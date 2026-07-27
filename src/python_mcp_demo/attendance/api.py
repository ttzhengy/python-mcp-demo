"""考勤服务 HTTP API 适配器。

封装对考勤后端服务的 HTTP 调用。
基于 ``BaseHttpClient._call_api`` 统一处理异常和日志。
Business 方法返回类型约束的 VO 实体类（``ApiResponse`` / ``ListResponse``）。

支持 OrgId 动态路由：每个业务方法接收 ``org_id`` 参数，
通过 ``OrgIdRouter`` 解析对应的 baseurl 发起请求。
"""

from __future__ import annotations

from typing import cast

from python_mcp_demo.attendance.router import OrgIdRouter
from python_mcp_demo.core.http_client import BaseHttpClient
from python_mcp_demo.models.vo import ApiResponse, ListResponse
from python_mcp_demo.urls import APIUrls


class AttendanceApiAdapter(BaseHttpClient):
    """考勤服务 HTTP API 客户端。

    支持签到、签退、请假申请和考勤记录查询。
    每个业务方法通过 ``_call_api`` 统一处理 HTTP 通信和错误日志。
    支持 OrgId 动态路由（通过 ``org_id`` 参数选择对应的后端 baseurl）。

    Args:
        base_url: 默认后端服务基础 URL（当 org_id 未匹配到映射时使用）。
        org_router: OrgId → BaseURL 路由器。
        timeout: HTTP 读超时（秒）。
        connect_timeout: 连接超时（秒）。
        max_retries: 5xx 错误最大重试次数。
    """

    def __init__(
        self,
        base_url: str,
        org_router: OrgIdRouter,
        timeout: int = 20,
        connect_timeout: int = 5,
        max_retries: int = 3,
    ) -> None:
        """初始化考勤 API 适配器。

        Args:
            base_url: 默认后端服务基础 URL。
            org_router: OrgId → BaseURL 路由器。
            timeout: HTTP 读超时（秒）。
            connect_timeout: 连接超时（秒）。
            max_retries: 5xx 错误最大重试次数。
        """
        super().__init__(
            base_url=base_url,
            timeout=timeout,
            connect_timeout=connect_timeout,
            max_retries=max_retries,
        )
        self._org_router = org_router

    async def clock_in(self, token: str, org_id: str | None = None) -> ApiResponse:
        """上班签到。

        Args:
            token: 用户 JWT Token。
            org_id: 组织 ID（用于路由到对应的后端 baseurl）。

        Returns:
            ``ApiResponse`` 实体。
        """
        base_url_override = self._org_router.resolve(org_id)
        return await self._call_api(
            method="POST",
            path=APIUrls.CLOCK_IN,
            parse_func=self._parse_simple_response,
            token=token,
            action_name="签到",
            service_name="考勤服务",
            base_url_override=base_url_override,
        )

    async def clock_out(self, token: str, org_id: str | None = None) -> ApiResponse:
        """下班签退。

        Args:
            token: 用户 JWT Token。
            org_id: 组织 ID（用于路由到对应的后端 baseurl）。

        Returns:
            ``ApiResponse`` 实体。
        """
        base_url_override = self._org_router.resolve(org_id)
        return await self._call_api(
            method="POST",
            path=APIUrls.CLOCK_OUT,
            parse_func=self._parse_simple_response,
            token=token,
            action_name="签退",
            service_name="考勤服务",
            base_url_override=base_url_override,
        )

    async def leave_apply(
        self,
        token: str,
        leave_type: str,
        date_from: str,
        date_to: str,
        reason: str,
        org_id: str | None = None,
    ) -> ApiResponse:
        """请假申请。

        Args:
            token: 用户 JWT Token。
            leave_type: 请假类型（年假/事假/病假等）。
            date_from: 开始日期（YYYY-MM-DD）。
            date_to: 结束日期（YYYY-MM-DD）。
            reason: 请假原因。
            org_id: 组织 ID（用于路由到对应的后端 baseurl）。

        Returns:
            ``ApiResponse`` 实体。
        """
        base_url_override = self._org_router.resolve(org_id)
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
            base_url_override=base_url_override,
        )

    async def query_records(
        self,
        token: str,
        date_from: str | None = None,
        date_to: str | None = None,
        status: str | None = None,
        limit: int = 10,
        org_id: str | None = None,
    ) -> ListResponse:
        """查询考勤记录。

        Args:
            token: 用户 JWT Token。
            date_from: 时间范围起（YYYY-MM-DD），可选。
            date_to: 时间范围止（YYYY-MM-DD），可选。
            status: 考勤状态，可选。
            limit: 返回条数上限，默认 10。
            org_id: 组织 ID（用于路由到对应的后端 baseurl）。

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

        base_url_override = self._org_router.resolve(org_id)
        return cast(ListResponse, await self._call_api(
            method="GET",
            path=APIUrls.ATTENDANCE_QUERY,
            parse_func=self._parse_list_response,
            params=params,
            token=token,
            action_name="考勤查询",
            service_name="考勤服务",
            base_url_override=base_url_override,
        ))

    async def query_leave(
        self,
        token: str,
        date_from: str | None = None,
        date_to: str | None = None,
        status: str | None = None,
        limit: int = 10,
        org_id: str | None = None,
    ) -> ListResponse:
        """查询请假记录。

        Args:
            token: 用户 JWT Token。
            date_from: 时间范围起（YYYY-MM-DD），可选。
            date_to: 时间范围止（YYYY-MM-DD），可选。
            status: 请假状态（如"已审批"），可选。
            limit: 返回条数上限，默认 10。
            org_id: 组织 ID（用于路由到对应的后端 baseurl）。

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

        base_url_override = self._org_router.resolve(org_id)
        return cast(ListResponse, await self._call_api(
            method="GET",
            path=APIUrls.LEAVE_QUERY,
            parse_func=self._parse_list_response,
            params=params,
            token=token,
            action_name="请假记录查询",
            service_name="考勤服务",
            base_url_override=base_url_override,
        ))
