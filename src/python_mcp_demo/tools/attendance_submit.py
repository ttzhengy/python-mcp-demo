"""考勤操作工具 — FastMCP tool 定义。

薄封装层：参数解析 → 调用 service → 日志 → 格式化返回。
"""

from __future__ import annotations

from fastmcp import FastMCP

from python_mcp_demo.auth import AuthMiddleware
from python_mcp_demo.core.logging_helper import ToolLogger
from python_mcp_demo.services.attendance_service import AttendanceService


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

    @server.tool()
    async def clock_in(user_token: str) -> dict:
        """上班签到。

        记录当前时间作为上班打卡时间。

        Args:
            user_token: 用户 JWT Token。

        Returns:
            {"success": bool, "data": dict | None, "error": str | None}
        """
        async with ToolLogger("clock_in", user_token=user_token) as log_ctx:
            if not user_token or not user_token.strip():
                log_ctx.set_error("Token 为空")
                return {"success": False, "data": None, "error": "缺少用户认证信息，请重新登录后重试"}

            verify_result = await auth_middleware.verify_token(user_token)
            if not verify_result.valid:
                log_ctx.set_error(verify_result.error)
                return {"success": False, "data": None, "error": verify_result.error}
            log_ctx.set_user_id(verify_result.user_id)

            result = await attendance_service.clock_in(token=user_token)
            log_ctx.set_result(result)
            return result.to_dict() if not isinstance(result, dict) else result

    @server.tool()
    async def clock_out(user_token: str) -> dict:
        """下班签退。

        记录当前时间作为下班打卡时间。

        Args:
            user_token: 用户 JWT Token。

        Returns:
            {"success": bool, "data": dict | None, "error": str | None}
        """
        async with ToolLogger("clock_out", user_token=user_token) as log_ctx:
            if not user_token or not user_token.strip():
                log_ctx.set_error("Token 为空")
                return {"success": False, "data": None, "error": "缺少用户认证信息，请重新登录后重试"}

            verify_result = await auth_middleware.verify_token(user_token)
            if not verify_result.valid:
                log_ctx.set_error(verify_result.error)
                return {"success": False, "data": None, "error": verify_result.error}
            log_ctx.set_user_id(verify_result.user_id)

            result = await attendance_service.clock_out(token=user_token)
            log_ctx.set_result(result)
            return result.to_dict() if not isinstance(result, dict) else result

    @server.tool()
    async def leave_apply(
        user_token: str,
        leave_type: str,
        date_from: str,
        date_to: str,
        reason: str,
    ) -> dict:
        """申请请假。

        Args:
            user_token: 用户 JWT Token。
            leave_type: 请假类型（年假/事假/病假/婚假/产假）。
            date_from: 开始日期（YYYY-MM-DD）。
            date_to: 结束日期（YYYY-MM-DD）。
            reason: 请假原因。

        Returns:
            {"success": bool, "data": dict | None, "error": str | None}
        """
        async with ToolLogger("leave_apply", user_token=user_token) as log_ctx:
            # ── 参数校验 ──
            if not leave_type:
                log_ctx.set_error("请假类型不能为空")
                return {"success": False, "data": None, "error": "请假类型不能为空"}
            if not date_from:
                log_ctx.set_error("开始日期不能为空")
                return {"success": False, "data": None, "error": "开始日期不能为空"}
            if not date_to:
                log_ctx.set_error("结束日期不能为空")
                return {"success": False, "data": None, "error": "结束日期不能为空"}
            if not reason:
                log_ctx.set_error("请假原因不能为空")
                return {"success": False, "data": None, "error": "请假原因不能为空"}

            if not user_token or not user_token.strip():
                log_ctx.set_error("Token 为空")
                return {"success": False, "data": None, "error": "缺少用户认证信息，请重新登录后重试"}

            verify_result = await auth_middleware.verify_token(user_token)
            if not verify_result.valid:
                log_ctx.set_error(verify_result.error)
                return {"success": False, "data": None, "error": verify_result.error}
            log_ctx.set_user_id(verify_result.user_id)

            result = await attendance_service.leave_apply(
                token=user_token,
                leave_type=leave_type,
                date_from=date_from,
                date_to=date_to,
                reason=reason,
            )
            log_ctx.set_result(result)
            return result.to_dict() if not isinstance(result, dict) else result
