"""考勤服务 HTTP API 适配器。

封装对考勤后端服务的 HTTP 调用。
基于 ``BaseHttpClient._call_api`` 统一处理异常和日志。
Business 方法返回类型约束的 VO 实体类（``ApiResponse`` / ``ListResponse``）。
"""

from __future__ import annotations

from typing import cast

from python_mcp_demo.core.http_client import BaseHttpClient
from python_mcp_demo.models.vo import ApiResponse, ListResponse
from python_mcp_demo.urls import APIUrls


class AttendanceApiAdapter(BaseHttpClient):
    """考勤服务 HTTP API 客户端。

    支持签到、签退、请假申请和考勤记录查询。
    每个业务方法通过 ``_call_api`` 统一处理 HTTP 通信和错误日志。
    """

    async def clock_in(self, token: str) -> ApiResponse:
        """上班签到。

        Args:
            token: 用户 JWT Token。

        Returns:
            ``ApiResponse`` 实体。
        """
        return await self._call_api(
            method="POST",
            path=APIUrls.CLOCK_IN,
            parse_func=self._parse_simple_response,
            token=token,
            action_name="签到",
            service_name="考勤服务",
        )

    async def clock_out(self, token: str) -> ApiResponse:
        """下班签退。

        Args:
            token: 用户 JWT Token。

        Returns:
            ``ApiResponse`` 实体。
        """
        return await self._call_api(
            method="POST",
            path=APIUrls.CLOCK_OUT,
            parse_func=self._parse_simple_response,
            token=token,
            action_name="签退",
            service_name="考勤服务",
        )

    async def leave_apply(
        self,
        token: str,
        leave_type: str,
        date_from: str,
        date_to: str,
        reason: str,
    ) -> ApiResponse:
        """请假申请。

        Args:
            token: 用户 JWT Token。
            leave_type: 请假类型（年假/事假/病假等）。
            date_from: 开始日期（YYYY-MM-DD）。
            date_to: 结束日期（YYYY-MM-DD）。
            reason: 请假原因。

        Returns:
            ``ApiResponse`` 实体。
        """
        return await self._call_api(
            method="POST",
            path=APIUrls.LEAVE_APPLY,
            parse_func=self._parse_simple_response,
            json_data={
                "leave_type": leave_type,
                "date_from": date_from,
                "date_to": date_to,
                "reason": reason,
            },
            token=token,
            action_name="请假申请",
            service_name="考勤服务",
        )

    async def query_records(
        self,
        token: str,
        date_from: str | None = None,
        date_to: str | None = None,
        status: str | None = None,
        limit: int = 10,
    ) -> ListResponse:
        """查询考勤记录。

        Args:
            token: 用户 JWT Token。
            date_from: 时间范围起（YYYY-MM-DD），可选。
            date_to: 时间范围止（YYYY-MM-DD），可选。
            status: 考勤状态，可选。
            limit: 返回条数上限，默认 10。

        Returns:
            ``ListResponse`` 实体。
        """
        params: dict[str, str | int] = {"limit": limit}
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        if status:
            params["status"] = status

        return cast(ListResponse, await self._call_api(
            method="GET",
            path=APIUrls.ATTENDANCE_QUERY,
            parse_func=self._parse_list_response,
            params=params,
            token=token,
            action_name="考勤查询",
            service_name="考勤服务",
        ))

    async def query_leave(
        self,
        token: str,
        date_from: str | None = None,
        date_to: str | None = None,
        status: str | None = None,
        limit: int = 10,
    ) -> ListResponse:
        """查询请假记录。

        Args:
            token: 用户 JWT Token。
            date_from: 时间范围起（YYYY-MM-DD），可选。
            date_to: 时间范围止（YYYY-MM-DD），可选。
            status: 请假状态（如"已审批"），可选。
            limit: 返回条数上限，默认 10。

        Returns:
            ``ListResponse`` 实体。
        """
        params: dict[str, str | int] = {"limit": limit}
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        if status:
            params["status"] = status

        return cast(ListResponse, await self._call_api(
            method="GET",
            path=APIUrls.LEAVE_QUERY,
            parse_func=self._parse_list_response,
            params=params,
            token=token,
            action_name="请假记录查询",
            service_name="考勤服务",
        ))
