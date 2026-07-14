"""AI 办公助手 POC — FastMCP 服务器入口。

暴露 query_forms MCP Tool，供 Dify Agent 工作流调用。

目标链路：Dify Agent → MCP 协议 (SSE) → FastMCP → HTTP API → Java 后端

架构约束：
  - 存量零改造：Java 后端不做任何变更
  - 用户身份代理：透传用户 JWT，MCP 层仅做 token 前置校验
  - Cookie 隔离：cookie 不进入 Dify / LLM
  - 审计标记：HTTP Header 添加 X-AI-Agent
"""

from __future__ import annotations

import time
import uuid

from fastmcp import FastMCP

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


#: CLI 入口使用的服务器单例
mcp = create_server()

if __name__ == "__main__":
    logger.info(
        "🚀 AI 办公助手 POC 服务器启动: {name} @ {host}:{port}",
        name=settings.server_name,
        host=settings.host,
        port=settings.port,
    )
    mcp.run(transport="sse", host=settings.host, port=settings.port)
