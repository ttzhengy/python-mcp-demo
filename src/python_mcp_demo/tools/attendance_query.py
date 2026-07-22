"""考勤查询工具 — FastMCP tool 定义。

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
    """注册考勤查询相关工具。

    Args:
        server: FastMCP 服务器实例。
        attendance_service: 考勤业务服务。
        auth_middleware: 认证中间件。
    """

    @server.tool()
    async def query_attendance(
        user_token: str,
        date_from: str = "",
        date_to: str = "",
        status: str = "",
        limit: int = 10,
    ) -> dict:
        """查询考勤记录（如签到时间、签退时间、考勤状态等）。

        Args:
            user_token: 用户 JWT Token。
            date_from: 时间范围起（YYYY-MM-DD），可选。
            date_to: 时间范围止（YYYY-MM-DD），可选。
            status: 考勤状态（如"正常"、"迟到"、"早退"），可选。
            limit: 返回条数上限，默认 10。

        Returns:
            {"success": bool, "data": {"total": int, "returned": int, "items": [...]}, "error": str | None}
        """
        async with ToolLogger("query_attendance", user_token=user_token) as log_ctx:
            if not user_token or not user_token.strip():
                log_ctx.set_error("Token 为空")
                return {"success": False, "data": None, "error": "缺少用户认证信息，请重新登录后重试"}

            verify_result = await auth_middleware.verify_token(user_token)
            if not verify_result.valid:
                log_ctx.set_error(verify_result.error)
                return {"success": False, "data": None, "error": verify_result.error}
            log_ctx.set_user_id(verify_result.user_id)

            result = await attendance_service.query_records(
                token=user_token,
                date_from=date_from or None,
                date_to=date_to or None,
                status=status or None,
                limit=limit,
            )
            log_ctx.set_result(result)
            return result.to_dict() if not isinstance(result, dict) else result

    @server.tool()
    async def query_leave_records(
        user_token: str,
        date_from: str = "",
        date_to: str = "",
        status: str = "",
        limit: int = 10,
    ) -> dict:
        """查询请假记录（历史请假申请及审批状态）。

        Args:
            user_token: 用户 JWT Token。
            date_from: 时间范围起（YYYY-MM-DD），可选。
            date_to: 时间范围止（YYYY-MM-DD），可选。
            status: 请假状态（如"已审批"、"待审批"、"已驳回"），可选。
            limit: 返回条数上限，默认 10。

        Returns:
            {"success": bool, "data": {"total": int, "returned": int, "items": [...]}, "error": str | None}
        """
        async with ToolLogger("query_leave_records", user_token=user_token) as log_ctx:
            if not user_token or not user_token.strip():
                log_ctx.set_error("Token 为空")
                return {"success": False, "data": None, "error": "缺少用户认证信息，请重新登录后重试"}

            verify_result = await auth_middleware.verify_token(user_token)
            if not verify_result.valid:
                log_ctx.set_error(verify_result.error)
                return {"success": False, "data": None, "error": verify_result.error}
            log_ctx.set_user_id(verify_result.user_id)

            result = await attendance_service.query_leave(
                token=user_token,
                date_from=date_from or None,
                date_to=date_to or None,
                status=status or None,
                limit=limit,
            )
            log_ctx.set_result(result)
            return result.to_dict() if not isinstance(result, dict) else result
