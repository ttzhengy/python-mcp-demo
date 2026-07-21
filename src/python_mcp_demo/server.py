"""python-mcp-demo MCP 服务器实现（向后兼容封装）。

提供基于 FastMCP 的独立服务器，包含 8 个实用 demo 工具：
``hello``, ``fetch_url``, ``add``, ``calculate``, ``random_number``,
``current_time``, ``echo``, ``count_words``。

该模块为向后兼容保留。新代码详见 ``tools/demo.py``。
"""

from __future__ import annotations

import logging

from python_mcp_demo.config import settings as mcp_settings

try:
    from fastmcp import FastMCP
except ImportError:  # pragma: no cover
    FastMCP = None  # type: ignore[assignment]

logger = logging.getLogger("python_mcp_demo")


def create_server(name: str | None = None) -> FastMCP:
    """创建并配置一个包含 demo 工具的 FastMCP 服务器实例。

    向后兼容函数。注册全部 8 个内置 demo 工具。

    Args:
        name: 可选的服务器名称。

    Returns:
        配置好的 ``FastMCP`` 实例。
    """
    if FastMCP is None:
        raise ImportError("fastmcp 未安装。请运行: uv add fastmcp")

    server = FastMCP(name or mcp_settings.server_name)

    logger.info(
        "正在创建 MCP 服务器 '%s' (日志级别=%s, 超时=%ds)",
        name or mcp_settings.server_name,
        mcp_settings.log_level,
        mcp_settings.request_timeout,
    )

    from python_mcp_demo.tools.demo import register_tools
    register_tools(server)

    return server


#: CLI 使用的单例实例（``python -m python_mcp_demo``）。
mcp = create_server()

if __name__ == "__main__":
    mcp.run()
