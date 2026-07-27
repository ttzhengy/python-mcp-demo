"""考勤查询 MCP 工具。

薄封装层：参数解析 → 调用 service → 日志 → 格式化返回。
使用 @log_tool + @require_auth 装饰器剥离日志和认证逻辑。
"""

from __future__ import annotations

from fastmcp import FastMCP

from python_mcp_demo.attendance.service import AttendanceService
from python_mcp_demo.core.auth import AuthMiddleware
from python_mcp_demo.core.tool_decorators import log_tool, require_auth


def register_tools(
    server: FastMCP,
    attendance_service: AttendanceService,
    auth_middleware: AuthMiddleware,
) -> None:
    """注册考勤查询相关工具。

    Args:
        server: FastMCP 服务器实例。
        attendance_service: 考勤业务服务。
        auth_middleware: 认证中间件。
    """
    _require_auth = require_auth(auth_middleware)

    @server.tool()
    @log_tool("query_attendance")
    @_require_auth
    async def query_attendance(
        user_token: str,
        user_id: str = "",
        date_from: str = "",
        date_to: str = "",
        status: str = "",
        limit: int = 10,
    ) -> dict:
        """查询考勤记录（如签到时间、签退时间、考勤状态等）。

        Args:
            user_token: 用户 JWT Token（由 @require_auth 校验后注入 user_id）。
            user_id: 用户标识（由 @require_auth 自动注入，无需手动传入）。
            date_from: 时间范围起（YYYY-MM-DD），可选。
            date_to: 时间范围止（YYYY-MM-DD），可选。
            status: 考勤状态（如"正常"、"迟到"、"早退"），可选。
            limit: 返回条数上限，默认 10。

        Returns:
            {"success": bool, "data": {"total": int, "returned": int, "items": [...]}, "error": str | None}
        """
        result = await attendance_service.query_records(
            token=user_token,
            date_from=date_from or None,
            date_to=date_to or None,
            status=status or None,
            limit=limit,
        )
        return result.to_dict() if not isinstance(result, dict) else result

    @server.tool()
    @log_tool("query_leave_records")
    @_require_auth
    async def query_leave_records(
        user_token: str,
        user_id: str = "",
        date_from: str = "",
        date_to: str = "",
        status: str = "",
        limit: int = 10,
    ) -> dict:
        """查询请假记录（历史请假申请及审批状态）。

        Args:
            user_token: 用户 JWT Token（由 @require_auth 校验后注入 user_id）。
            user_id: 用户标识（由 @require_auth 自动注入，无需手动传入）。
            date_from: 时间范围起（YYYY-MM-DD），可选。
            date_to: 时间范围止（YYYY-MM-DD），可选。
            status: 请假状态（如"已审批"、"待审批"、"已驳回"），可选。
            limit: 返回条数上限，默认 10。

        Returns:
            {"success": bool, "data": {"total": int, "returned": int, "items": [...]}, "error": str | None}
        """
        result = await attendance_service.query_leave(
            token=user_token,
            date_from=date_from or None,
            date_to=date_to or None,
            status=status or None,
            limit=limit,
        )
        return result.to_dict() if not isinstance(result, dict) else result
