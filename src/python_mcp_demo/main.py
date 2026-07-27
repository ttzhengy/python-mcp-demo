"""AI 办公助手 — FastAPI + FastMCP 服务器入口（重构 v0.4.0）。

将 FastMCP 挂载到 FastAPI 上，整个服务以 ``/obot`` 为上下文根。

架构层级::

    ┌─────────────────────────────────────────┐
    │  tools/          FastMCP @server.tool()  │
    │  services/       纯业务逻辑              │
    │  adapters/       HTTP API 适配器         │
    │  core/           跨模块基础设施          │
    └─────────────────────────────────────────┘

用法::

    python -m python_mcp_demo
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.routing import Mount

from python_mcp_demo.attendance.api import AttendanceApiAdapter
from python_mcp_demo.attendance.router import OrgIdRouter
from python_mcp_demo.attendance.service import AttendanceService
from python_mcp_demo.core.auth import AuthMiddleware
from python_mcp_demo.config import settings
from python_mcp_demo.form.api import FormApiAdapter
from python_mcp_demo.form.service import FormService
from python_mcp_demo.core.log import log_json, logger, setup_logging

# 初始化日志
setup_logging(log_level=settings.log_level, json_format=settings.log_json)

# ── 全局组件 ──────────────────────────────────────────────
auth_middleware = AuthMiddleware(auth_url=settings.backend_auth_url)

form_adapter = FormApiAdapter(
    base_url=settings.backend_base_url,
    timeout=settings.request_timeout,
    connect_timeout=settings.connect_timeout,
    max_retries=settings.max_retries,
)

# 考勤模块：初始化 OrgId 路由器
attendance_org_router = OrgIdRouter(
    mapping=settings.get_attendance_org_mapping(),
    default_url=settings.backend_base_url,
)
attendance_adapter = AttendanceApiAdapter(
    base_url=settings.backend_base_url,
    org_router=attendance_org_router,
    timeout=settings.request_timeout,
    connect_timeout=settings.connect_timeout,
    max_retries=settings.max_retries,
)

form_service = FormService(adapter=form_adapter)
attendance_service = AttendanceService(adapter=attendance_adapter)


# ═══════════════════════════════════════════════════════════════════
# MCP 服务器工厂
# ═══════════════════════════════════════════════════════════════════


def create_server(name: str | None = None) -> FastMCP:
    """创建完整的 MCP 服务器，注册所有业务模块的 tools。

    注册的工具：
      - **demo 工具**: hello, fetch_url, add, calculate, random_number,
        current_time, echo, count_words
      - **表单工具**: query_forms, submit_form, prefill_form
      - **考勤工具**: clock_in, clock_out, leave_apply,
        query_attendance, query_leave_records

    Args:
        name: 可选的服务器名称。默认从配置加载。

    Returns:
        配置好的 FastMCP 实例。
    """
    server = FastMCP(name or settings.server_name)

    # ── 注册各业务模块的 tools ──
    from python_mcp_demo.tools import demo
    from python_mcp_demo.attendance import query as attendance_query
    from python_mcp_demo.attendance import submit as attendance_submit
    from python_mcp_demo.form import query as form_query
    from python_mcp_demo.form import submit as form_submit

    demo.register_tools(server)
    form_query.register_tools(server, form_service, auth_middleware)
    form_submit.register_tools(server, form_service, auth_middleware)
    attendance_query.register_tools(server, attendance_service, auth_middleware)
    attendance_submit.register_tools(server, attendance_service, auth_middleware)

    return server


# ═══════════════════════════════════════════════════════════════════
# 应用工厂
# ═══════════════════════════════════════════════════════════════════


def create_app(name: str | None = None) -> Starlette:
    """创建并配置整个应用。

    架构::

        ┌────────────────────────────────────────┐
        │  Starlette (外层)                       │
        │  Mount("/obot", app=inner_fastapi)      │
        │  ┌────────────────────────────────┐     │
        │  │  FastAPI (内层)                 │     │
        │  │  GET /health                   │     │
        │  │  GET /docs                     │     │
        │  │  mount("/mcp", mcp_sse_app)    │     │
        │  │  ┌───────────────────────┐     │     │
        │  │  │  FastMCP SSE ASGI     │     │     │
        │  │  │  /sse, /messages      │     │     │
        │  │  └───────────────────────┘     │     │
        │  └────────────────────────────────┘     │
        └────────────────────────────────────────┘

    对外路径::

        /obot/health          ← FastAPI 健康探针
        /obot/docs            ← OpenAPI 文档页
        /obot/openapi.json    ← OpenAPI Schema
        /obot/mcp/sse         ← MCP SSE 协议流
        /obot/mcp/messages    ← MCP 消息投递

    Args:
        name: 可选的服务器名称。默认从配置加载。

    Returns:
        配置好的 ``Starlette`` 实例，可直接用于 uvicorn。
    """
    # ── 1. 内层 FastAPI 应用（所有路由以 / 注册） ──
    inner = FastAPI(
        title=name or settings.server_name,
        version="0.5.0",
    )

    @inner.get("/health")
    async def health():
        """健康检查（K8s / 负载均衡探针）。"""
        return {"status": "healthy", "server": inner.title}

    # ── 2. 创建 MCP 服务器并挂载到内层 FastAPI ──
    mcp_server = create_server(name)
    mcp_asgi = mcp_server.http_app(transport="sse")
    inner.mount("/mcp", mcp_asgi, name="mcp")

    # ── 3. 外层 ASGI 应用，将内层挂载到 /obot 上下文根 ──
    @asynccontextmanager
    async def _lifespan(_app: Starlette):
        logger.info(
            "🚀 AI 办公助手启动: {name} @ /obot (v0.5.0)",
            name=inner.title,
        )
        yield
        logger.info("⏹️  服务器关闭")

    app = Starlette(
        routes=[Mount("/obot", app=inner)],
        lifespan=_lifespan,
    )

    return app


#: Uvicorn 使用的应用单例
app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "python_mcp_demo.main:app",
        host=settings.host,
        port=settings.port,
    )
