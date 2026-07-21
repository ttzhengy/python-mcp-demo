"""考勤操作工具 — FastMCP tool 定义。

薄封装层：参数解析 → 调用 service → 格式化返回。
"""

from __future__ import annotations

import time
import uuid

from fastmcp import FastMCP

from python_mcp_demo.auth import AuthMiddleware
from python_mcp_demo.logging_ import log_json
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
        trace_id = uuid.uuid4().hex[:12]
        tool_name = "clock_in"
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

        result = await attendance_service.clock_in(token=user_token)

        elapsed = int((time.time() - start_time) * 1000)
        log_level = "INFO" if result["success"] else "ERROR"
        log_status = "success" if result["success"] else "error"
        log_json(log_level, trace_id, tool_name, elapsed, log_status,
                 user_token=user_token, user_id=verify_result.user_id,
                 error=result.get("error"))

        return result

    @server.tool()
    async def clock_out(user_token: str) -> dict:
        """下班签退。

        记录当前时间作为下班打卡时间。

        Args:
            user_token: 用户 JWT Token。

        Returns:
            {"success": bool, "data": dict | None, "error": str | None}
        """
        trace_id = uuid.uuid4().hex[:12]
        tool_name = "clock_out"
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

        result = await attendance_service.clock_out(token=user_token)

        elapsed = int((time.time() - start_time) * 1000)
        log_level = "INFO" if result["success"] else "ERROR"
        log_status = "success" if result["success"] else "error"
        log_json(log_level, trace_id, tool_name, elapsed, log_status,
                 user_token=user_token, user_id=verify_result.user_id,
                 error=result.get("error"))

        return result

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
        trace_id = uuid.uuid4().hex[:12]
        tool_name = "leave_apply"
        start_time = time.time()

        if not user_token or not user_token.strip():
            elapsed = int((time.time() - start_time) * 1000)
            log_json("WARN", trace_id, tool_name, elapsed, "error", error="Token 为空")
            return {"success": False, "data": None, "error": "缺少用户认证信息，请重新登录后重试"}

        # 参数校验
        if not leave_type:
            return {"success": False, "data": None, "error": "请假类型不能为空"}
        if not date_from:
            return {"success": False, "data": None, "error": "开始日期不能为空"}
        if not date_to:
            return {"success": False, "data": None, "error": "结束日期不能为空"}
        if not reason:
            return {"success": False, "data": None, "error": "请假原因不能为空"}

        verify_result = await auth_middleware.verify_token(user_token)
        if not verify_result.valid:
            elapsed = int((time.time() - start_time) * 1000)
            log_json("WARN", trace_id, tool_name, elapsed, "auth_failed",
                     user_token=user_token, error=verify_result.error)
            return {"success": False, "data": None, "error": verify_result.error}

        result = await attendance_service.leave_apply(
            token=user_token,
            leave_type=leave_type,
            date_from=date_from,
            date_to=date_to,
            reason=reason,
        )

        elapsed = int((time.time() - start_time) * 1000)
        log_level = "INFO" if result["success"] else "ERROR"
        log_status = "success" if result["success"] else "error"
        log_json(log_level, trace_id, tool_name, elapsed, log_status,
                 user_token=user_token, user_id=verify_result.user_id,
                 error=result.get("error"))

        return result
