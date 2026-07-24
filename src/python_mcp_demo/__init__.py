"""python-mcp-demo: 基于 FastMCP 的生产级 MCP 服务器库。

架构分层::

    attendance/    考勤业务领域（models, service, query, submit, api）
    form/          表单业务领域（models, service, query, submit, api）
    tools/         Demo 工具集
    core/          跨模块基础设施（http_client, logging_helper）
    models/        通用 VO 实体
"""
__version__ = "0.4.0"

from .server import create_server, mcp

__all__ = [
    "create_server",
    "mcp",
]
