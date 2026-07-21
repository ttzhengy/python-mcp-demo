"""python-mcp-demo: 基于 FastMCP 的生产级 MCP 服务器库。

架构分层::

    tools/          FastMCP @server.tool() 定义
    services/       纯业务逻辑（不依赖 FastMCP）
    adapters/       HTTP API 适配器
    core/           跨模块基础设施
    models/         数据模型
"""

__version__ = "0.4.0"

from . import tools
from .server import create_server, mcp

__all__ = [
    "create_server",
    "mcp",
    "tools",
]
