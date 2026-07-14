"""python-mcp-demo MCP 服务器实现。

提供基于 FastMCP 的服务器，内置 8 个实用工具：
``hello``, ``fetch_url``, ``add``, ``calculate``, ``random_number``,
``current_time``, ``echo``, ``count_words``。
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

from python_mcp_demo.config import settings as mcp_settings
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
# 安全数学表达式计算器 —— 基于 AST 解析替代 eval()
# ---------------------------------------------------------------------------

# AST 运算符节点 → Python 运算符函数映射
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

# 允许在表达式中使用的函数名 → 可调用对象
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
    """使用 AST 解析安全地计算数学表达式。

    支持基础算术运算（``+``, ``-``, ``*``, ``/``, ``**``,
    ``%``, ``//``）、括号、一元正负号以及一组精选的数学函数
    （``sqrt``, ``sin``, ``cos``, ``log``, ``floor``, …）。

    该实现**绝不会**调用 Python 的 ``eval()``——它把表达式解析
    为 AST 后遍历语法树，拒绝任何未明确允许的节点类型。

    Args:
        expression: 数学表达式字符串，例如 ``"2 + 3 * 4"``。

    Returns:
        计算结果（``float``）。

    Raises:
        MathExpressionError: 表达式包含无效语法、不支持的运算符、
            不允许的函数，或产生无穷/NaN 结果。
    """
    if not expression or not expression.strip():
        raise MathExpressionError("表达式不能为空")

    try:
        tree = ast.parse(expression.strip(), mode="eval")
    except SyntaxError as exc:
        raise MathExpressionError(f"表达式语法错误: {exc}") from exc

    def _eval(node: ast.AST) -> float:
        """递归计算 AST 节点并返回 float。"""
        if isinstance(node, ast.Expression):
            return _eval(node.body)

        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return float(node.value)
            raise MathExpressionError(
                f"不支持的常量类型: {type(node.value).__name__}"
            )

        if isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in _SAFE_OPERATORS:
                raise MathExpressionError(
                    f"不支持的一元运算符: {op_type.__name__}"
                )
            return _SAFE_OPERATORS[op_type](_eval(node.operand))

        if isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in _SAFE_OPERATORS:
                raise MathExpressionError(
                    f"不支持的二元运算符: {op_type.__name__}"
                )
            return _SAFE_OPERATORS[op_type](_eval(node.left), _eval(node.right))

        if isinstance(node, ast.Name):
            # 裸名称只允许用于已知常量（如 pi, e, tau）
            if node.id not in _SAFE_FUNCTIONS:
                raise MathExpressionError(f"不支持的名称: {node.id}")
            value = _SAFE_FUNCTIONS[node.id]
            if callable(value):
                raise MathExpressionError(
                    f"{node.id} 是函数而非常量——请用 () 调用"
                )
            return float(value)

        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise MathExpressionError("只允许简单的函数名")
            func_name = node.func.id
            if func_name not in _SAFE_FUNCTIONS:
                raise MathExpressionError(f"不支持的函数: {func_name}")
            args = [_eval(a) for a in node.args]
            kwargs = {kw.arg: _eval(kw.value) for kw in node.keywords if kw.arg}
            return _SAFE_FUNCTIONS[func_name](*args, **kwargs)

        raise MathExpressionError(f"不支持的语法元素: {type(node).__name__}")

    try:
        result = _eval(tree)
    except MathExpressionError:
        raise
    except ZeroDivisionError as exc:
        raise MathExpressionError("除零错误") from exc
    except Exception as exc:
        raise MathExpressionError(f"计算错误: {exc}") from exc

    if isinstance(result, float) and (math.isinf(result) or math.isnan(result)):
        raise MathExpressionError("结果为无穷或非数字 (NaN)")

    return float(result)


# ---------------------------------------------------------------------------
# 服务器工厂
# ---------------------------------------------------------------------------


def create_server(name: str | None = None) -> FastMCP:
    """创建并配置一个包含所有内置工具的 FastMCP 服务器实例。

    Args:
        name: 可选的服务器名称。未指定时依次回退到环境变量
            ``MCP_SERVER_NAME`` 或默认值 ``"python-mcp-demo"``。

    Returns:
        一个配置好的 ``FastMCP`` 实例。

    Raises:
        ImportError: 如果 ``fastmcp`` 未安装。
    """
    if FastMCP is None:
        raise ImportError(
            "fastmcp 未安装。请运行: uv add fastmcp"
        )

    server = FastMCP(name or mcp_settings.server_name)

    logger.info(
        "正在创建 MCP 服务器 '%s' (日志级别=%s, 超时=%ds)",
        name or mcp_settings.server_name,
        mcp_settings.log_level,
        mcp_settings.request_timeout,
    )

    # ═══════════════════════════════════════════════════════════════
    # 工具: hello — 问候
    # ═══════════════════════════════════════════════════════════════
    @server.tool()
    async def hello(name: str = "World") -> str:
        """向某人打招呼。

        Args:
            name: 要问候的名字。默认为 ``"World"``。

        Returns:
            友好的问候消息。
        """
        logger.debug("hello 被调用, name=%r", name)
        return f"Hello, {name}! Welcome to MCP."

    # ═══════════════════════════════════════════════════════════════
    # 工具: fetch_url — 抓取 URL
    # ═══════════════════════════════════════════════════════════════
    @server.tool()
    async def fetch_url(url: str) -> dict[str, Any]:
        """从指定 URL 获取内容。

        发起 HTTP GET 请求，返回状态码、内容预览及总内容长度。

        Args:
            url: 要抓取的 URL。必须以 ``http://`` 或 ``https://`` 开头。

        Returns:
            包含 ``status`` (int)、``content_preview`` (str) 和
            ``content_length`` (int) 的字典。

        Raises:
            MCPToolError: URL 无效、无法访问或返回 HTTP 错误状态。
        """
        if not url.startswith(("http://", "https://")):
            raise MCPToolError("无效的 URL: 必须以 http:// 或 https:// 开头")

        logger.info("正在抓取 URL: %s", url)
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(mcp_settings.request_timeout),
                follow_redirects=True,
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                text = response.text
                logger.debug(
                    "从 %s 获取了 %d 字节 (状态码=%d)",
                    url,
                    len(text),
                    response.status_code,
                )
                return {
                    "status": response.status_code,
                    "content_preview": text[: mcp_settings.max_fetch_size],
                    "content_length": len(text),
                }
        except httpx.HTTPStatusError as exc:
            logger.warning("抓取 %s 时 HTTP 错误: %s", url, exc)
            raise MCPToolError(
                f"HTTP {exc.response.status_code}: {exc.response.reason_phrase}"
            ) from exc
        except httpx.RequestError as exc:
            logger.warning("请求 %s 失败: %s", url, exc)
            raise MCPToolError(f"请求失败: {exc}") from exc

    # ═══════════════════════════════════════════════════════════════
    # 工具: add — 加法
    # ═══════════════════════════════════════════════════════════════
    @server.tool()
    async def add(a: float, b: float) -> float:
        """将两个数相加。

        Args:
            a: 第一个加数。
            b: 第二个加数。

        Returns:
            ``a`` 与 ``b`` 的算术和。
        """
        logger.debug("add 被调用, a=%r, b=%r", a, b)
        return a + b

    # ═══════════════════════════════════════════════════════════════
    # 工具: calculate — 数学计算
    # ═══════════════════════════════════════════════════════════════
    @server.tool()
    async def calculate(expression: str) -> float:
        """安全地计算数学表达式。

        使用基于 AST 的解析（而非 ``eval()``）以确保安全。
        支持基础算术运算（``+``, ``-``, ``*``, ``/``）、括号
        以及常见数学函数（``sqrt``, ``sin``, ``cos``, ``log``,
        ``floor`` 等）。

        Args:
            expression: 数学表达式字符串，例如 ``"2 + 3 * 4"``
                或 ``"sqrt(16) * pi"``。

        Returns:
            计算结果（``float``）。

        Raises:
            MathExpressionError: 表达式无效、包含不允许的语法或
                触发除零错误。
        """
        logger.debug("calculate 被调用, expression=%r", expression)
        return _safe_eval(expression)

    # ═══════════════════════════════════════════════════════════════
    # 工具: random_number — 随机数
    # ═══════════════════════════════════════════════════════════════
    @server.tool()
    async def random_number(min: float, max: float) -> float:
        """在指定范围内生成一个随机浮点数。

        使用 ``random.uniform`` 生成在 ``[min, max]`` 区间内
        均匀分布的随机值。

        Args:
            min: 下限（包含）。
            max: 上限（包含）。

        Returns:
            指定范围内的随机 ``float``。

        Raises:
            MCPToolError: 如果 ``min`` 大于 ``max``。
        """
        if min > max:
            raise MCPToolError(
                f"最小值 ({min}) 不能大于最大值 ({max})"
            )
        result = random.uniform(min, max)
        logger.debug("random_number(min=%r, max=%r) = %r", min, max, result)
        return result

    # ═══════════════════════════════════════════════════════════════
    # 工具: current_time — 当前时间
    # ═══════════════════════════════════════════════════════════════
    @server.tool()
    async def current_time(timezone: str = "UTC") -> str:
        """获取指定 IANA 时区的当前日期和时间。

        Args:
            timezone: IANA 时区名称，例如 ``"Asia/Shanghai"``、
                ``"US/Eastern"`` 或 ``"Europe/London"``。
                默认为 ``"UTC"``。

        Returns:
            ``YYYY-MM-DD HH:MM:SS`` 格式的时区时间字符串。

        Raises:
            MCPToolError: 时区名称不可识别。
        """
        if timezone not in available_timezones():
            raise MCPToolError(
                f"未知时区: {timezone}。"
                f"请使用有效的 IANA 时区，例如 'Asia/Shanghai' 或 "
                f"'US/Eastern'。"
            )
        tz = ZoneInfo(timezone)
        now = datetime.now(tz)
        result = now.strftime("%Y-%m-%d %H:%M:%S")
        logger.debug("current_time(%r) = %s", timezone, result)
        return result

    # ═══════════════════════════════════════════════════════════════
    # 工具: echo — 回显
    # ═══════════════════════════════════════════════════════════════
    @server.tool()
    async def echo(message: str, times: int = 1) -> list[str]:
        """重复回显消息。

        Args:
            message: 要回显的消息。
            times: 重复次数。必须在 ``1`` 到 ``100``（含）之间。
                默认为 ``1``。

        Returns:
            包含 ``message`` 重复 ``times`` 次的列表。

        Raises:
            MCPToolError: 如果 ``times`` 超出允许范围。
        """
        if times < 1 or times > 100:
            raise MCPToolError(
                f"重复次数 ({times}) 必须在 1 到 100 之间"
            )
        logger.debug("echo 被调用, message=%r, times=%d", message, times)
        return [message] * times

    # ═══════════════════════════════════════════════════════════════
    # 工具: count_words — 文本统计
    # ═══════════════════════════════════════════════════════════════
    @server.tool()
    async def count_words(text: str) -> dict[str, Any]:
        """分析文本并返回词频统计。

        计算字符数、词数、行数以及频率最高的前 10 个词
        （不区分大小写，去除标点）。

        Args:
            text: 要分析的输入文本。

        Returns:
            包含 ``char_count`` (int)、``word_count`` (int)、
            ``line_count`` (int) 和 ``top_words``
            (dict[str, int]) 的字典，其中 ``top_words`` 将每个词
            映射到其出现频率。
        """
        logger.debug("count_words 被调用, 输入 %d 个字符", len(text))

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

        # 去除标点并统一大小写以进行词频分析
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


#: CLI 使用的单例实例（``python -m python_mcp_demo``）。
mcp = create_server()

if __name__ == "__main__":
    mcp.run()
