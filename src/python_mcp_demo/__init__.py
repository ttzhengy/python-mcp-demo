"""python-mcp-demo: 基于 FastMCP 的生产级 MCP 服务器库。"""

__version__ = "0.3.0"

from .server import create_server, mcp

__all__ = [
    "create_server",
    "mcp",
]
