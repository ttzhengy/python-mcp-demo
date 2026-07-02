# python-mcp-demo

A demonstration MCP (Model Context Protocol) server library built with [FastMCP](https://github.com/jlowin/fastmcp).

## Features

- **Simple API** — Create an MCP server with just a few lines of code
- **Built-in tools** — `hello`, `fetch_url`, `add` — ready to use out of the box
- **Async-first** — Powered by `httpx` for fast HTTP requests
- **Type-safe** — Full type hints and Pydantic models

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

### Available tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `hello` | Say hello to someone | `name` (str, default: "World") |
| `fetch_url` | Fetch content from a URL | `url` (str) |
| `add` | Add two numbers | `a` (float), `b` (float) |

## Development

```bash
# Clone the repo
git clone https://github.com/ttzhengy/python-mcp-demo.git
cd python-mcp-demo

# Create virtual environment and install dependencies
uv sync

# Run tests
uv run pytest

# Run the server
uv run python -m python_mcp_demo
```

## Requirements

- Python >= 3.12
- fastmcp >= 0.6.0
- httpx >= 0.28.0

## License

MIT
