"""表单提交 MCP 工具。

薄封装层：参数解析 → 调用 service → 日志 → 格式化返回。
使用 @log_tool + @require_auth 装饰器剥离日志和认证逻辑。
"""

from __future__ import annotations

from fastmcp import FastMCP

from python_mcp_demo.auth import AuthMiddleware
from python_mcp_demo.core.tool_decorators import log_tool, require_auth
from python_mcp_demo.form.service import FormService


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
    _require_auth = require_auth(auth_middleware)

    @server.tool()
    @log_tool("submit_form")
    @_require_auth
    async def submit_form(
        user_token: str,
        form_type: str,
        form_data: dict,
        user_id: str = "",
    ) -> dict:
        """提交表单数据（如请假申请、报销单等）。

        Args:
            user_token: 用户 JWT Token（由 @require_auth 校验后注入 user_id）。
            user_id: 用户标识（由 @require_auth 自动注入，无需手动传入）。
            form_type: 表单类型名称（如"请假申请"）。
            form_data: 表单字段数据（JSON 对象）。

        Returns:
            {"success": bool, "data": dict | None, "error": str | None}
        """
        result = await form_service.submit_form(
            token=user_token,
            form_type=form_type,
            form_data=form_data,
        )
        return result.to_dict() if not isinstance(result, dict) else result

    @server.tool()
    @log_tool("prefill_form")
    @_require_auth
    async def prefill_form(
        user_token: str,
        form_type: str,
        template_id: str = "",
        user_id: str = "",
    ) -> dict:
        """获取表单预填数据（根据模板自动填充表单字段）。

        Args:
            user_token: 用户 JWT Token（由 @require_auth 校验后注入 user_id）。
            user_id: 用户标识（由 @require_auth 自动注入，无需手动传入）。
            form_type: 表单类型名称（如"请假申请"）。
            template_id: 模板标识（可选）。

        Returns:
            {"success": bool, "data": dict | None, "error": str | None}
        """
        result = await form_service.prefill_form(
            token=user_token,
            form_type=form_type,
            template_id=template_id or None,
        )
        return result.to_dict() if not isinstance(result, dict) else result
