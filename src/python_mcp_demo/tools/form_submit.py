"""表单提交工具 — FastMCP tool 定义。

薄封装层：参数解析 → 调用 service → 格式化返回。
"""

from __future__ import annotations

import time
import uuid

from fastmcp import FastMCP

from python_mcp_demo.auth import AuthMiddleware
from python_mcp_demo.logging_ import log_json
from python_mcp_demo.services.form_service import FormService


def register_tools(
    server: FastMCP,
    form_service: FormService,
    auth_middleware: AuthMiddleware,
) -> None:
    """注册表单提交相关工具。

    Args:
        server: FastMCP 服务器实例。
        form_service: 表单业务服务。
        auth_middleware: 认证中间件。
    """

    @server.tool()
    async def submit_form(
        user_token: str,
        form_type: str,
        form_data: dict,
    ) -> dict:
        """提交表单数据（如请假申请、报销单等）。

        Args:
            user_token: 用户 JWT Token。
            form_type: 表单类型名称（如"请假申请"）。
            form_data: 表单字段数据（JSON 对象）。

        Returns:
            {"success": bool, "data": dict | None, "error": str | None}
        """
        trace_id = uuid.uuid4().hex[:12]
        tool_name = "submit_form"
        start_time = time.time()

        if not user_token or not user_token.strip():
            elapsed = int((time.time() - start_time) * 1000)
            log_json("WARN", trace_id, tool_name, elapsed, "error", error="Token 为空")
            return {"success": False, "data": None, "error": "缺少用户认证信息，请重新登录后重试"}

        verify_result = await auth_middleware.verify_token(user_token)
        if not verify_result.valid:
            elapsed = int((time.time() - start_time) * 1000)
            log_json("WARN", trace_id, tool_name, elapsed, "auth_failed",
                     user_token=user_token, error=verify_result.error)
            return {"success": False, "data": None, "error": verify_result.error}

        result = await form_service.submit_form(
            token=user_token,
            form_type=form_type,
            form_data=form_data,
        )

        elapsed = int((time.time() - start_time) * 1000)
        log_level = "INFO" if result["success"] else "ERROR"
        log_status = "success" if result["success"] else "error"
        log_json(log_level, trace_id, tool_name, elapsed, log_status,
                 user_token=user_token, user_id=verify_result.user_id,
                 error=result.get("error"))

        return result

    @server.tool()
    async def prefill_form(
        user_token: str,
        form_type: str,
        template_id: str = "",
    ) -> dict:
        """获取表单预填数据（根据模板自动填充表单字段）。

        Args:
            user_token: 用户 JWT Token。
            form_type: 表单类型名称（如"请假申请"）。
            template_id: 模板标识（可选）。

        Returns:
            {"success": bool, "data": dict | None, "error": str | None}
        """
        trace_id = uuid.uuid4().hex[:12]
        tool_name = "prefill_form"
        start_time = time.time()

        if not user_token or not user_token.strip():
            elapsed = int((time.time() - start_time) * 1000)
            log_json("WARN", trace_id, tool_name, elapsed, "error", error="Token 为空")
            return {"success": False, "data": None, "error": "缺少用户认证信息，请重新登录后重试"}

        verify_result = await auth_middleware.verify_token(user_token)
        if not verify_result.valid:
            elapsed = int((time.time() - start_time) * 1000)
            log_json("WARN", trace_id, tool_name, elapsed, "auth_failed",
                     user_token=user_token, error=verify_result.error)
            return {"success": False, "data": None, "error": verify_result.error}

        result = await form_service.prefill_form(
            token=user_token,
            form_type=form_type,
            template_id=template_id or None,
        )

        elapsed = int((time.time() - start_time) * 1000)
        log_level = "INFO" if result["success"] else "ERROR"
        log_status = "success" if result["success"] else "error"
        log_json(log_level, trace_id, tool_name, elapsed, log_status,
                 user_token=user_token, user_id=verify_result.user_id,
                 error=result.get("error"))

        return result
