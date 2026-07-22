"""表单查询工具 — FastMCP tool 定义。

薄封装层：参数解析 → 调用 service → 日志 → 格式化返回。
"""

from __future__ import annotations

from fastmcp import FastMCP

from python_mcp_demo.auth import AuthMiddleware
from python_mcp_demo.core.logging_helper import ToolLogger
from python_mcp_demo.services.form_service import FormService


def register_tools(
    server: FastMCP,
    form_service: FormService,
    auth_middleware: AuthMiddleware,
) -> None:
    """注册表单查询相关工具。

    Args:
        server: FastMCP 服务器实例。
        form_service: 表单业务服务。
        auth_middleware: 认证中间件。
    """

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
            {"success": bool, "data": {"total": int, "returned": int, "items": [...]}, "error": str | None}
        """
        async with ToolLogger("query_forms", user_token=user_token) as log_ctx:
            # ── 1. 参数校验 ──
            if not user_token or not user_token.strip():
                log_ctx.set_error("Token 为空")
                return {"success": False, "data": None, "error": "缺少用户认证信息，请重新登录后重试"}

            # ── 2. Token 前置校验 ──
            verify_result = await auth_middleware.verify_token(user_token)
            if not verify_result.valid:
                log_ctx.set_error(verify_result.error)
                return {"success": False, "data": None, "error": verify_result.error}
            log_ctx.set_user_id(verify_result.user_id)

            # ── 3. 业务查询 ──
            result = await form_service.query_forms(
                token=user_token,
                form_type=form_type or None,
                date_from=date_from or None,
                date_to=date_to or None,
                status=status or None,
                limit=limit,
            )
            log_ctx.set_result(result)
            return result.to_dict() if not isinstance(result, dict) else result
