"""MCP server implementation for python-mcp-demo.

Provides a FastMCP-based server with 8 utility tools:
``hello``, ``fetch_url``, ``add``, ``calculate``, ``random_number``,
``current_time``, ``echo``, and ``count_words``.
"""

from __future__ import annotations

import ast
import logging
import math
import operator
import random
from collections import Counter
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo, available_timezones

import httpx

from python_mcp_demo.config import load_config
from python_mcp_demo.exceptions import (
    MathExpressionError,
    MCPToolError,
)

try:
    from fastmcp import FastMCP
except ImportError:  # pragma: no cover
    FastMCP = None  # type: ignore[assignment]


logger = logging.getLogger("python_mcp_demo")


# ---------------------------------------------------------------------------
# Safe math expression evaluator — replaces eval() with AST-based evaluation
# ---------------------------------------------------------------------------

# Mapping of AST operator nodes → Python operator functions
_SAFE_OPERATORS: dict[type[ast.operator], Any] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

# Allowed function names → callables for use in expressions
_SAFE_FUNCTIONS: dict[str, Any] = {
    "abs": abs,
    "ceil": math.ceil,
    "cos": math.cos,
    "degrees": math.degrees,
    "e": math.e,
    "exp": math.exp,
    "floor": math.floor,
    "isinf": math.isinf,
    "isnan": math.isnan,
    "log": math.log,
    "log10": math.log10,
    "max": max,
    "min": min,
    "pi": math.pi,
    "radians": math.radians,
    "round": round,
    "sin": math.sin,
    "sqrt": math.sqrt,
    "tan": math.tan,
    "tau": math.tau,
}


def _safe_eval(expression: str) -> float:
    """Evaluate a mathematical expression safely using AST parsing.

    Supports basic arithmetic (``+``, ``-``, ``*``, ``/``, ``**``,
    ``%``, ``//``), parentheses, unary negation/positive, and a curated
    set of math functions (``sqrt``, ``sin``, ``cos``, ``log``,
    ``floor``, …).

    The implementation **never** calls Python's ``eval()`` — it parses
    the expression into an AST and walks the tree, rejecting any node
    type that isn't explicitly allowed.

    Args:
        expression: A mathematical expression string, e.g. ``"2 + 3 * 4"``.

    Returns:
        The computed result as a ``float``.

    Raises:
        MathExpressionError: If the expression contains invalid syntax,
            unsupported operators, disallowed functions, or produces
            an infinite / NaN result.
    """
    if not expression or not expression.strip():
        raise MathExpressionError("Expression must not be empty")

    try:
        tree = ast.parse(expression.strip(), mode="eval")
    except SyntaxError as exc:
        raise MathExpressionError(f"Invalid expression syntax: {exc}") from exc

    def _eval(node: ast.AST) -> float:
        """Recursively evaluate an AST node to a float."""
        if isinstance(node, ast.Expression):
            return _eval(node.body)

        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return float(node.value)
            raise MathExpressionError(
                f"Unsupported constant type: {type(node.value).__name__}"
            )

        if isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in _SAFE_OPERATORS:
                raise MathExpressionError(
                    f"Unsupported unary operator: {op_type.__name__}"
                )
            return _SAFE_OPERATORS[op_type](_eval(node.operand))

        if isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in _SAFE_OPERATORS:
                raise MathExpressionError(
                    f"Unsupported binary operator: {op_type.__name__}"
                )
            return _SAFE_OPERATORS[op_type](_eval(node.left), _eval(node.right))

        if isinstance(node, ast.Name):
            # Bare names are only allowed for named constants (e.g. pi, e, tau)
            if node.id not in _SAFE_FUNCTIONS:
                raise MathExpressionError(f"Unsupported name: {node.id}")
            value = _SAFE_FUNCTIONS[node.id]
            if callable(value):
                raise MathExpressionError(
                    f"{node.id} is a function, not a constant — call it with ()"
                )
            return float(value)

        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise MathExpressionError("Only simple function names are allowed")
            func_name = node.func.id
            if func_name not in _SAFE_FUNCTIONS:
                raise MathExpressionError(f"Unsupported function: {func_name}")
            args = [_eval(a) for a in node.args]
            kwargs = {kw.arg: _eval(kw.value) for kw in node.keywords if kw.arg}
            return _SAFE_FUNCTIONS[func_name](*args, **kwargs)

        raise MathExpressionError(f"Unsupported syntax element: {type(node).__name__}")

    try:
        result = _eval(tree)
    except MathExpressionError:
        raise
    except ZeroDivisionError as exc:
        raise MathExpressionError("Division by zero") from exc
    except Exception as exc:
        raise MathExpressionError(f"Evaluation error: {exc}") from exc

    if isinstance(result, float) and (math.isinf(result) or math.isnan(result)):
        raise MathExpressionError("Result is infinite or not a number (NaN)")

    return float(result)


# ---------------------------------------------------------------------------
# Server factory
# ---------------------------------------------------------------------------


def create_server(name: str | None = None) -> FastMCP:
    """Create and configure a FastMCP server instance with all built-in tools.

    Args:
        name: Optional server name. Falls back to the configured
            ``MCP_SERVER_NAME`` or ``"python-mcp-demo"``.

    Returns:
        A configured ``FastMCP`` instance.

    Raises:
        ImportError: If ``fastmcp`` is not installed.
    """
    if FastMCP is None:
        raise ImportError(
            "fastmcp is not installed. Run: uv add fastmcp"
        )

    config = load_config()
    server = FastMCP(name or config.server_name)

    logger.info(
        "Creating MCP server '%s' (log_level=%s, timeout=%ds)",
        name or config.server_name,
        config.log_level,
        config.request_timeout,
    )

    # ═══════════════════════════════════════════════════════════════
    # Tool: hello
    # ═══════════════════════════════════════════════════════════════
    @server.tool()
    async def hello(name: str = "World") -> str:
        """Say hello to someone.

        Args:
            name: The name to greet. Defaults to ``"World"``.

        Returns:
            A friendly greeting message.
        """
        logger.debug("hello called with name=%r", name)
        return f"Hello, {name}! Welcome to MCP."

    # ═══════════════════════════════════════════════════════════════
    # Tool: fetch_url
    # ═══════════════════════════════════════════════════════════════
    @server.tool()
    async def fetch_url(url: str) -> dict[str, Any]:
        """Fetch content from a URL.

        Makes an HTTP GET request and returns the status code, a
        content preview, and the total content length.

        Args:
            url: The URL to fetch. Must start with ``http://`` or
                ``https://``.

        Returns:
            A dictionary with keys ``status`` (int),
            ``content_preview`` (str), and ``content_length`` (int).

        Raises:
            MCPToolError: If the URL is invalid, unreachable, or
                returns an HTTP error status.
        """
        if not url.startswith(("http://", "https://")):
            raise MCPToolError("Invalid URL: must start with http:// or https://")

        logger.info("Fetching URL: %s", url)
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(config.request_timeout),
                follow_redirects=True,
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                text = response.text
                logger.debug(
                    "Fetched %d bytes from %s (status=%d)",
                    len(text),
                    url,
                    response.status_code,
                )
                return {
                    "status": response.status_code,
                    "content_preview": text[: config.max_fetch_size],
                    "content_length": len(text),
                }
        except httpx.HTTPStatusError as exc:
            logger.warning("HTTP error fetching %s: %s", url, exc)
            raise MCPToolError(
                f"HTTP {exc.response.status_code}: {exc.response.reason_phrase}"
            ) from exc
        except httpx.RequestError as exc:
            logger.warning("Request failed for %s: %s", url, exc)
            raise MCPToolError(f"Request failed: {exc}") from exc

    # ═══════════════════════════════════════════════════════════════
    # Tool: add
    # ═══════════════════════════════════════════════════════════════
    @server.tool()
    async def add(a: float, b: float) -> float:
        """Add two numbers together.

        Args:
            a: First addend.
            b: Second addend.

        Returns:
            The arithmetic sum of ``a`` and ``b``.
        """
        logger.debug("add called with a=%r, b=%r", a, b)
        return a + b

    # ═══════════════════════════════════════════════════════════════
    # Tool: calculate
    # ═══════════════════════════════════════════════════════════════
    @server.tool()
    async def calculate(expression: str) -> float:
        """Safely evaluate a mathematical expression.

        Uses AST-based parsing (not ``eval()``) for security.
        Supports basic arithmetic (``+``, ``-``, ``*``, ``/``),
        parentheses, and common math functions (``sqrt``, ``sin``,
        ``cos``, ``log``, ``floor``, etc.).

        Args:
            expression: A mathematical expression string, e.g.
                ``"2 + 3 * 4"`` or ``"sqrt(16) * pi"``.

        Returns:
            The computed result as a ``float``.

        Raises:
            MathExpressionError: If the expression is invalid,
                contains disallowed syntax, or triggers division by
                zero.
        """
        logger.debug("calculate called with expression=%r", expression)
        return _safe_eval(expression)

    # ═══════════════════════════════════════════════════════════════
    # Tool: random_number
    # ═══════════════════════════════════════════════════════════════
    @server.tool()
    async def random_number(min: float, max: float) -> float:
        """Generate a random floating-point number in a given range.

        Uses ``random.uniform`` to produce a uniformly-distributed
        value in ``[min, max]``.

        Args:
            min: The lower bound (inclusive).
            max: The upper bound (inclusive).

        Returns:
            A random ``float`` in the requested range.

        Raises:
            MCPToolError: If ``min`` is greater than ``max``.
        """
        if min > max:
            raise MCPToolError(
                f"min ({min}) must not be greater than max ({max})"
            )
        result = random.uniform(min, max)
        logger.debug("random_number(min=%r, max=%r) = %r", min, max, result)
        return result

    # ═══════════════════════════════════════════════════════════════
    # Tool: current_time
    # ═══════════════════════════════════════════════════════════════
    @server.tool()
    async def current_time(timezone: str = "UTC") -> str:
        """Get the current date and time for a given IANA timezone.

        Args:
            timezone: An IANA timezone name such as
                ``"Asia/Shanghai"``, ``"US/Eastern"``, or
                ``"Europe/London"``. Defaults to ``"UTC"``.

        Returns:
            A string in ``YYYY-MM-DD HH:MM:SS`` format for the
            specified timezone.

        Raises:
            MCPToolError: If the timezone name is not recognised.
        """
        if timezone not in available_timezones():
            raise MCPToolError(
                f"Unknown timezone: {timezone}. "
                f"Use a valid IANA timezone like 'Asia/Shanghai' or "
                f"'US/Eastern'."
            )
        tz = ZoneInfo(timezone)
        now = datetime.now(tz)
        result = now.strftime("%Y-%m-%d %H:%M:%S")
        logger.debug("current_time(%r) = %s", timezone, result)
        return result

    # ═══════════════════════════════════════════════════════════════
    # Tool: echo
    # ═══════════════════════════════════════════════════════════════
    @server.tool()
    async def echo(message: str, times: int = 1) -> list[str]:
        """Echo a message repeatedly.

        Args:
            message: The message to echo.
            times: Number of repetitions. Must be between ``1`` and
                ``100`` (inclusive). Defaults to ``1``.

        Returns:
            A list containing ``message`` repeated ``times`` times.

        Raises:
            MCPToolError: If ``times`` is outside the allowed range.
        """
        if times < 1 or times > 100:
            raise MCPToolError(
                f"times ({times}) must be between 1 and 100"
            )
        logger.debug("echo called with message=%r, times=%d", message, times)
        return [message] * times

    # ═══════════════════════════════════════════════════════════════
    # Tool: count_words
    # ═══════════════════════════════════════════════════════════════
    @server.tool()
    async def count_words(text: str) -> dict[str, Any]:
        """Analyse text and return word statistics.

        Computes character count, word count, line count, and the
        top 10 most frequent words (case-insensitive,
        punctuation-stripped).

        Args:
            text: The input text to analyse.

        Returns:
            A dictionary with keys ``char_count`` (int),
            ``word_count`` (int), ``line_count`` (int), and
            ``top_words`` (dict[str, int] mapping each word to its
            frequency).
        """
        logger.debug("count_words called with %d characters", len(text))

        char_count: int = len(text)
        line_count: int = text.count("\n") + 1 if text else 0

        if not text.strip():
            return {
                "char_count": char_count,
                "word_count": 0,
                "line_count": line_count,
                "top_words": {},
            }

        words: list[str] = text.split()
        word_count: int = len(words)

        # Clean punctuation and normalise case for frequency analysis
        cleaned = [
            w.strip(".,!?;:()[]{}'\"“”'…-").lower()
            for w in words
        ]
        cleaned = [w for w in cleaned if w]

        top_words: dict[str, int] = {}
        if cleaned:
            counter = Counter(cleaned)
            top_words = dict(counter.most_common(10))

        return {
            "char_count": char_count,
            "word_count": word_count,
            "line_count": line_count,
            "top_words": top_words,
        }

    return server


#: Singleton instance for CLI invocation (``python -m python_mcp_demo``).
mcp = create_server()

if __name__ == "__main__":
    mcp.run()
