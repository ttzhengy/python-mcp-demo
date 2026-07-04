"""python-mcp-demo: A production-ready MCP (Model Context Protocol) server library built with FastMCP."""

__version__ = "0.2.0"

from .server import create_server, mcp

__all__ = [
    "create_server",
    "mcp",
]
