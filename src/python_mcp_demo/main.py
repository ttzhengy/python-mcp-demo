"""AI 办公助手 POC — FastAPI + FastMCP 服务器入口。

将 FastMCP 挂载到 FastAPI 上，整个服务以 ``/obot`` 为上下文根。

用法::

    python -m python_mcp_demo

暴露接口::

  /obot/health         健康探针
  /obot/docs           FastAPI OpenAPI 文档
  /obot/openapi.json   OpenAPI Schema
  /obot/mcp/sse        MCP SSE 协议流端点
  /obot/mcp/messages   MCP 消息投递端点
"""

from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.routing import Mount

from python_mcp_demo.auth import AuthMiddleware
from python_mcp_demo.config import settings
from python_mcp_demo.form_engine import FormEngineAdapter
from python_mcp_demo.logging_ import log_json, logger, setup_logging

# 初始化日志
setup_logging(log_level=settings.log_level, json_format=settings.log_json)

# 全局组件
auth_middleware = AuthMiddleware(
    auth_url=settings.backend_auth_url,
)
form_engine = FormEngineAdapter(
    base_url=settings.backend_base_url,
    timeout=settings.request_timeout,
    connect_timeout=settings.connect_timeout,
    max_retries=settings.max_retries,
)


# ═══════════════════════════════════════════════════════════════════
# MCP 服务器工厂
# ═══════════════════════════════════════════════════════════════════


def create_server(name: str | None = None) -> FastMCP:
    """创建 POC FastMCP 服务器，包含 query_forms 工具。

    Args:
        name: 可选的服务器名称。默认从配置加载。

    Returns:
        配置好的 FastMCP 实例。
    """
    server = FastMCP(name or settings.server_name)

    # ═══════════════════════════════════════════════════════════
    # 工具: query_forms — 表单查询
    # ═══════════════════════════════════════════════════════════
    @server.tool()
    async def query_forms(
        user_token: str,
        form_type: str = "",
        date_from: str = "",
        date_to: str = "",
        status: str = "",
        limit: int = 10,
    ) -> dict:
        """查询表单数据（如请假申请、报销单等）。

        端到端链路：
          用户提问 → Dify 意图识别 → 调用 query_forms →
          verify_token 前置校验 → 表单引擎 HTTP API → 返回结果

        Args:
            user_token: 用户 JWT Token，从 Dify session variable 透传。
            form_type: 表单类型名称（如"请假申请"），可选。
            date_from: 时间范围起（YYYY-MM-DD），可选。
            date_to: 时间范围止（YYYY-MM-DD），可选。
            status: 表单状态（如"已审批"、"待审批"），可选。
            limit: 返回条数上限，默认 10。

        Returns:
            {
                "success": true/false,
                "data": {
                    "total": int,       # 符合条件的总记录数
                    "returned": int,    # 实际返回的记录数
                    "items": [...]      # 表单记录列表
                },
                "error": str | null     # 失败时的错误消息
            }
        """
        trace_id = uuid.uuid4().hex[:12]
        tool_name = "query_forms"
        start_time = time.time()

        # ── 1. 参数校验 ──
        if not user_token or not user_token.strip():
            elapsed = int((time.time() - start_time) * 1000)
            log_json("WARN", trace_id, tool_name, elapsed, "error",
                     error="Token 为空")
            return {
                "success": False,
                "data": None,
                "error": "缺少用户认证信息，请重新登录后重试",
            }

        # ── 2. Token 前置校验 ──
        verify_result = await auth_middleware.verify_token(user_token)
        if not verify_result.valid:
            elapsed = int((time.time() - start_time) * 1000)
            log_json("WARN", trace_id, tool_name, elapsed, "auth_failed",
                     user_token=user_token,
                     error=verify_result.error)
            return {
                "success": False,
                "data": None,
                "error": verify_result.error,
            }

        # ── 3. 业务查询 ──
        result = await form_engine.query_forms(
            token=user_token,
            form_type=form_type or None,
            date_from=date_from or None,
            date_to=date_to or None,
            status=status or None,
            limit=limit,
        )

        # ── 4. 日志输出（结构化 JSON） ──
        elapsed = int((time.time() - start_time) * 1000)
        log_level = "INFO" if result["success"] else "ERROR"
        log_status = "success" if result["success"] else "error"
        log_json(log_level, trace_id, tool_name, elapsed, log_status,
                 user_token=user_token,
                 user_id=verify_result.user_id,
                 error=result.get("error"),
                 extra={
                     "returned": result.get("data", {}).get("returned", 0)
                     if result.get("data") else 0,
                 })

        return result

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
        version="0.3.0",
    )

    @inner.get("/health")
    async def health():
        """健康检查（K8s / 负载均衡探针）。

        Returns:
            {"status": "healthy", "server": "服务器名称"}
        """
        return {"status": "healthy", "server": inner.title}

    # ── 2. 创建 MCP 服务器并挂载到内层 FastAPI ──
    mcp_server = create_server(name)
    mcp_asgi = mcp_server.http_app(transport="sse")
    inner.mount("/mcp", mcp_asgi, name="mcp")

    # ── 3. 外层 ASGI 应用，将内层挂载到 /obot 上下文根 ──
    @asynccontextmanager
    async def _lifespan(_app: Starlette):
        logger.info(
            "🚀 AI 办公助手 POC 启动: {name} @ /obot",
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
