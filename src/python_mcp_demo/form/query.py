"""表单查询 MCP 工具。

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
    """注册表单查询相关工具。

    Args:
        server: FastMCP 服务器实例。
        form_service: 表单业务服务。
        auth_middleware: 认证中间件。
    """
    _require_auth = require_auth(auth_middleware)

    @server.tool()
    @log_tool("query_forms")
    @_require_auth
    async def query_forms(
        user_token: str,
        user_id: str = "",
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
            user_token: 用户 JWT Token（由 @require_auth 校验后注入 user_id）。
            user_id: 用户标识（由 @require_auth 自动注入，无需手动传入）。
            form_type: 表单类型名称（如"请假申请"），可选。
            date_from: 时间范围起（YYYY-MM-DD），可选。
            date_to: 时间范围止（YYYY-MM-DD），可选。
            status: 表单状态（如"已审批"、"待审批"），可选。
            limit: 返回条数上限，默认 10。

        Returns:
            {"success": bool, "data": {"total": int, "returned": int, "items": [...]}, "error": str | None}
        """
        result = await form_service.query_forms(
            token=user_token,
            form_type=form_type or None,
            date_from=date_from or None,
            date_to=date_to or None,
            status=status or None,
            limit=limit,
        )
        return result.to_dict() if not isinstance(result, dict) else result
