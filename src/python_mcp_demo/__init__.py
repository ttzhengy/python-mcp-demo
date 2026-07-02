"""python-mcp-demo: A demonstration MCP (Model Context Protocol) server library."""

__version__ = "0.1.0"

from .server import create_server, mcp

__all__ = ["create_server", "mcp"]
