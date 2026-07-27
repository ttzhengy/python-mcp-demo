"""考勤操作 MCP 工具。

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
    """注册考勤操作相关工具（签到、签退、请假）。

    Args:
        server: FastMCP 服务器实例。
        attendance_service: 考勤业务服务。
        auth_middleware: 认证中间件。
    """
    _require_auth = require_auth(auth_middleware)

    @server.tool()
    @log_tool("clock_in")
    @_require_auth
    async def clock_in(
        user_token: str,
        user_id: str = "",
    ) -> dict:
        """上班签到。

        记录当前时间作为上班打卡时间。

        Args:
            user_token: 用户 JWT Token（由 @require_auth 校验后注入 user_id）。
            user_id: 用户标识（由 @require_auth 自动注入，无需手动传入）。

        Returns:
            {"success": bool, "data": dict | None, "error": str | None}
        """
        result = await attendance_service.clock_in(token=user_token)
        return result.to_dict() if not isinstance(result, dict) else result

    @server.tool()
    @log_tool("clock_out")
    @_require_auth
    async def clock_out(
        user_token: str,
        user_id: str = "",
    ) -> dict:
        """下班签退。

        记录当前时间作为下班打卡时间。

        Args:
            user_token: 用户 JWT Token（由 @require_auth 校验后注入 user_id）。
            user_id: 用户标识（由 @require_auth 自动注入，无需手动传入）。

        Returns:
            {"success": bool, "data": dict | None, "error": str | None}
        """
        result = await attendance_service.clock_out(token=user_token)
        return result.to_dict() if not isinstance(result, dict) else result

    @server.tool()
    @log_tool("leave_apply")
    @_require_auth
    async def leave_apply(
        user_token: str,
        leave_type: str,
        date_from: str,
        date_to: str,
        reason: str,
        user_id: str = "",
    ) -> dict:
        """申请请假。

        Args:
            user_token: 用户 JWT Token（由 @require_auth 校验后注入 user_id）。
            user_id: 用户标识（由 @require_auth 自动注入，无需手动传入）。
            leave_type: 请假类型（年假/事假/病假/婚假/产假）。
            date_from: 开始日期（YYYY-MM-DD）。
            date_to: 结束日期（YYYY-MM-DD）。
            reason: 请假原因。

        Returns:
            {"success": bool, "data": dict | None, "error": str | None}
        """
        # ── 业务参数校验 ──
        if not leave_type:
            return {"success": False, "data": None, "error": "请假类型不能为空"}
        if not date_from:
            return {"success": False, "data": None, "error": "开始日期不能为空"}
        if not date_to:
            return {"success": False, "data": None, "error": "结束日期不能为空"}
        if not reason:
            return {"success": False, "data": None, "error": "请假原因不能为空"}

        result = await attendance_service.leave_apply(
            token=user_token,
            leave_type=leave_type,
            date_from=date_from,
            date_to=date_to,
            reason=reason,
        )
        return result.to_dict() if not isinstance(result, dict) else result
