# python-mcp-demo

A **production-ready** MCP (Model Context Protocol) server library built with [FastMCP](https://github.com/jlowin/fastmcp).

[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](https://opensource.org/licenses/MIT)

## Features

- **8 built-in tools** — hello, fetch_url, add, calculate, random_number, current_time, echo, count_words
- **Safe expression evaluation** — AST-based `calculate` tool (no `eval()`)
- **Async-first** — Powered by `httpx` for fast HTTP requests
- **Type-safe** — Full type hints and dataclass return types
- **Structured logging** — Configurable via environment variables
- **Custom exceptions** — Granular error hierarchy for robust error handling
- **Env configuration** — `.env` file support for runtime settings

## Installation

```bash
pip install python-mcp-demo
```

Or with uv:

```bash
uv add python-mcp-demo
```

## Quick Start

### Run the MCP server

```bash
python -m python_mcp_demo
```

### Use in your code

```python
from python_mcp_demo import create_server

server = create_server("my-server")

@server.tool()
async def my_tool(query: str) -> str:
    """Custom tool implementation."""
    return f"You searched for: {query}"

server.run()
```

## Available Tools

| Tool | Description | Parameters | Returns |
|------|-------------|------------|---------|
| `hello` | Greet someone | `name` (str, default: "World") | `str` |
| `fetch_url` | Fetch content from a URL | `url` (str) | `dict` (status, content_preview, content_length) |
| `add` | Add two numbers | `a` (float), `b` (float) | `float` |
| `calculate` | Safely evaluate a math expression | `expression` (str) | `float` |
| `random_number` | Generate a random float | `min` (float, default: 0.0), `max` (float, default: 100.0) | `float` |
| `current_time` | Get current time in a timezone | `timezone` (str, default: "UTC") | `str` (ISO-8601) |
| `echo` | Echo a message N times | `message` (str), `times` (int, default: 1) | `list[str]` |
| `count_words` | Analyse text statistics | `text` (str) | `WordCountResult` dataclass |

### Tool details

#### `hello`

```python
result = await server.call_tool("hello", {"name": "Alice"})
# → "Hello, Alice! Welcome to MCP."

result = await server.call_tool("hello", {})
# → "Hello, World! Welcome to MCP."
```

#### `fetch_url`

```python
result = await server.call_tool("fetch_url", {"url": "https://example.com"})
# → {"status": 200, "content_preview": "<html>...", "content_length": 1256}
```

#### `add`

```python
result = await server.call_tool("add", {"a": 3.5, "b": 2.5})
# → 6.0
```

#### `calculate`

Safe expression evaluator using AST parsing (not `eval()`).

```python
result = await server.call_tool("calculate", {"expression": "2 + 3 * 4"})
# → 14.0

result = await server.call_tool("calculate", {"expression": "sqrt(16) * pi"})
# → 12.566370614359172

result = await server.call_tool("calculate", {"expression": "sin(pi/2)"})
# → 1.0
```

**Supported functions:** `abs`, `ceil`, `cos`, `degrees`, `exp`, `floor`,
`isinf`, `isnan`, `log`, `log10`, `max`, `min`, `radians`, `round`, `sin`,
`sqrt`, `tan`

**Constants:** `e`, `pi`, `tau`

#### `random_number`

```python
result = await server.call_tool("random_number", {"min": 1.0, "max": 10.0})
# → 4.7238456921... (random)
```

#### `current_time`

```python
result = await server.call_tool("current_time", {"timezone": "Asia/Shanghai"})
# → "2026-07-04T20:30:00+08:00"

result = await server.call_tool("current_time", {"timezone": "US/Eastern"})
# → "2026-07-04T08:30:00-04:00"
```

#### `echo`

```python
result = await server.call_tool("echo", {"message": "hi", "times": 3})
# → ["hi", "hi", "hi"]
```

#### `count_words`

```python
result = await server.call_tool("count_words", {"text": "hello world hello"})
# → WordCountResult(word_count=3, char_count=18, line_count=1, top_words=[("hello", 2), ("world", 1)])
```

## Configuration

Settings are read from environment variables and can be overridden
via a `.env` file:

```bash
# Copy the example and edit
cp .env.example .env
```

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_SERVER_NAME` | `python-mcp-demo` | Name exposed by the MCP server |
| `MCP_LOG_LEVEL` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`) |
| `MCP_REQUEST_TIMEOUT` | `30` | HTTP request timeout in seconds |
| `MCP_MAX_FETCH_SIZE` | `5000` | Max characters in content preview |

## Exception Hierarchy

```
MCPDemoError
├── ConfigurationError    — Configuration loading failures
├── MCPToolError          — User-level tool errors (invalid input, etc.)
│   ├── MathExpressionError — Invalid/unsafe math expressions
│   └── FetchError        — URL fetch failures
```

## Development

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)

### Setup

```bash
# Clone the repo
git clone https://github.com/ttzhengy/python-mcp-demo.git
cd python-mcp-demo

# Create virtual environment and install dependencies
uv sync

# Run tests
uv run pytest -v

# Run the server
uv run python -m python_mcp_demo
```

### Makefile commands

```bash
make install        # Install dependencies
make test           # Run tests
make test-coverage  # Run tests with coverage report
make run            # Start the MCP server
make lint           # Lint with ruff
make format         # Format with ruff
make clean          # Remove build artifacts
```

## Project Structure

```
python-mcp-demo/
├── pyproject.toml
├── .env.example
├── Makefile
├── README.md
├── src/
│   └── python_mcp_demo/
│       ├── __init__.py      # Package exports
│       ├── __main__.py      # CLI entry point
│       ├── config.py        # Environment configuration
│       ├── exceptions.py    # Custom exception hierarchy
│       ├── models.py        # Dataclass return types
│       └── server.py        # FastMCP server + all tools
└── tests/
    └── test_demo.py         # Comprehensive test suite
```

## Requirements

- Python >= 3.12
- fastmcp >= 0.6.0
- httpx >= 0.28.0

## License

MIT
