"""考勤服务 HTTP API 适配器。

封装对考勤后端服务的 HTTP 调用。
遵循与 FormApiAdapter 相同的设计模式。
"""

from __future__ import annotations

import httpx

from python_mcp_demo.core.http_client import BaseHttpClient
from python_mcp_demo.logging_ import logger
from python_mcp_demo.urls import APIUrls


class AttendanceApiAdapter(BaseHttpClient):
    """考勤服务 HTTP API 客户端。

    支持签到、签退、请假申请和考勤记录查询。
    """

    async def clock_in(self, token: str) -> dict:
        """上班签到。

        Args:
            token: 用户 JWT Token。

        Returns:
            包含 success、data 和 error 字段的字典。
        """
        try:
            result = await self._do_request(
                method="POST",
                path=APIUrls.CLOCK_IN,
                token=token,
            )
            return self._parse_simple_response(result)
        except httpx.TimeoutException:
            logger.warning("签到请求超时")
            return {"success": False, "data": None, "error": "签到超时，请稍后重试"}
        except httpx.RequestError as exc:
            logger.error("考勤服务不可达: {error}", error=str(exc))
            return {"success": False, "data": None, "error": "考勤服务暂时不可用，请稍后重试"}

    async def clock_out(self, token: str) -> dict:
        """下班签退。

        Args:
            token: 用户 JWT Token。

        Returns:
            包含 success、data 和 error 字段的字典。
        """
        try:
            result = await self._do_request(
                method="POST",
                path=APIUrls.CLOCK_OUT,
                token=token,
            )
            return self._parse_simple_response(result)
        except httpx.TimeoutException:
            logger.warning("签退请求超时")
            return {"success": False, "data": None, "error": "签退超时，请稍后重试"}
        except httpx.RequestError as exc:
            logger.error("考勤服务不可达: {error}", error=str(exc))
            return {"success": False, "data": None, "error": "考勤服务暂时不可用，请稍后重试"}

    async def leave_apply(
        self,
        token: str,
        leave_type: str,
        date_from: str,
        date_to: str,
        reason: str,
    ) -> dict:
        """请假申请。

        Args:
            token: 用户 JWT Token。
            leave_type: 请假类型（年假/事假/病假等）。
            date_from: 开始日期（YYYY-MM-DD）。
            date_to: 结束日期（YYYY-MM-DD）。
            reason: 请假原因。

        Returns:
            包含 success、data 和 error 字段的字典。
        """
        try:
            result = await self._do_request(
                method="POST",
                path=APIUrls.LEAVE_APPLY,
                json_data={
                    "leave_type": leave_type,
                    "date_from": date_from,
                    "date_to": date_to,
                    "reason": reason,
                },
                token=token,
            )
            return self._parse_simple_response(result)
        except httpx.TimeoutException:
            logger.warning("请假申请超时")
            return {"success": False, "data": None, "error": "请假申请超时，请稍后重试"}
        except httpx.RequestError as exc:
            logger.error("考勤服务不可达: {error}", error=str(exc))
            return {"success": False, "data": None, "error": "考勤服务暂时不可用，请稍后重试"}

    async def query_records(
        self,
        token: str,
        date_from: str | None = None,
        date_to: str | None = None,
        status: str | None = None,
        limit: int = 10,
    ) -> dict:
        """查询考勤记录。

        Args:
            token: 用户 JWT Token。
            date_from: 时间范围起（YYYY-MM-DD），可选。
            date_to: 时间范围止（YYYY-MM-DD），可选。
            status: 考勤状态，可选。
            limit: 返回条数上限，默认 10。

        Returns:
            包含 success、data 和 error 字段的字典。
        """
        params: dict[str, str | int] = {"limit": limit}
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        if status:
            params["status"] = status

        try:
            result = await self._do_request(
                method="GET",
                path=APIUrls.ATTENDANCE_QUERY,
                params=params,
                token=token,
            )
            return self._parse_list_response(result)
        except httpx.TimeoutException:
            logger.warning("考勤查询超时")
            return {"success": False, "data": None, "error": "查询超时，请稍后重试"}
        except httpx.RequestError as exc:
            logger.error("考勤服务不可达: {error}", error=str(exc))
            return {"success": False, "data": None, "error": "考勤服务暂时不可用，请稍后重试"}

    async def query_leave(
        self,
        token: str,
        date_from: str | None = None,
        date_to: str | None = None,
        status: str | None = None,
        limit: int = 10,
    ) -> dict:
        """查询请假记录。

        Args:
            token: 用户 JWT Token。
            date_from: 时间范围起（YYYY-MM-DD），可选。
            date_to: 时间范围止（YYYY-MM-DD），可选。
            status: 请假状态（如"已审批"），可选。
            limit: 返回条数上限，默认 10。

        Returns:
            包含 success、data 和 error 字段的字典。
        """
        params: dict[str, str | int] = {"limit": limit}
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        if status:
            params["status"] = status

        try:
            result = await self._do_request(
                method="GET",
                path=APIUrls.LEAVE_QUERY,
                params=params,
                token=token,
            )
            return self._parse_list_response(result)
        except httpx.TimeoutException:
            logger.warning("请假记录查询超时")
            return {"success": False, "data": None, "error": "查询超时，请稍后重试"}
        except httpx.RequestError as exc:
            logger.error("考勤服务不可达: {error}", error=str(exc))
            return {"success": False, "data": None, "error": "考勤服务暂时不可用，请稍后重试"}
