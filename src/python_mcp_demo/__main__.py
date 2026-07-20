"""python-mcp-demo CLI 入口点。

用法::

    python -m python_mcp_demo

启动 FastAPI 服务器，将 MCP 应用挂载到 ``/obot`` 上下文根，\
并暴露 ``/health`` 健康探针。
"""

from __future__ import annotations

from python_mcp_demo.config import settings
from python_mcp_demo.main import app

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
    )
