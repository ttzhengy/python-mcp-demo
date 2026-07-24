"""表单引擎 HTTP API 适配器。

封装对 Java 表单引擎后端服务的 HTTP 调用。
基于 ``BaseHttpClient._call_api`` 统一处理异常和日志。
每个业务方法返回类型约束的 VO 实体类（``ApiResponse`` / ``ListResponse``）。
"""

from __future__ import annotations

from typing import cast

from python_mcp_demo.core.http_client import BaseHttpClient
from python_mcp_demo.models.vo import ApiResponse, ListResponse
from python_mcp_demo.urls import APIUrls


class FormApiAdapter(BaseHttpClient):
    """表单引擎 HTTP API 客户端。

    每个业务方法对应一个后端 API 端点。
    继承 BaseHttpClient 的统一超时、重试和错误处理，
    通过 ``_call_api`` 消除重复的 try/except 日志代码。
    """

    async def query_forms(
        self,
        token: str,
        form_type: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        status: str | None = None,
        limit: int = 10,
    ) -> ListResponse:
        """查询表单数据。

        Args:
            token: 用户 JWT Token。
            form_type: 表单类型名称（如"请假申请"），可选。
            date_from: 时间范围起（YYYY-MM-DD），可选。
            date_to: 时间范围止（YYYY-MM-DD），可选。
            status: 表单状态（如"已审批"），可选。
            limit: 返回条数上限，默认 10。

        Returns:
            ``ListResponse`` 实体。
        """
        params: dict[str, str | int] = {"limit": limit}
        if form_type:
            params["form_type"] = form_type
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        if status:
            params["status"] = status

        return cast(ListResponse, await self._call_api(
            method="GET",
            path=APIUrls.FORM_QUERY,
            parse_func=self._parse_list_response,
            params=params,
            token=token,
            action_name="表单查询",
            service_name="表单引擎",
        ))

    async def submit_form(
        self,
        token: str,
        form_type: str,
        form_data: dict,
    ) -> ApiResponse:
        """提交表单数据。

        Args:
            token: 用户 JWT Token。
            form_type: 表单类型名称。
            form_data: 表单字段数据。

        Returns:
            ``ApiResponse`` 实体。
        """
        return await self._call_api(
            method="POST",
            path=APIUrls.FORM_SUBMIT,
            parse_func=self._parse_simple_response,
            json_data={"form_type": form_type, "form_data": form_data},
            token=token,
            action_name="表单提交",
            service_name="表单引擎",
        )

    async def prefill_form(
        self,
        token: str,
        form_type: str,
        template_id: str | None = None,
    ) -> ApiResponse:
        """获取表单预填数据。

        Args:
            token: 用户 JWT Token。
            form_type: 表单类型名称。
            template_id: 模板标识（可选）。

        Returns:
            ``ApiResponse`` 实体。
        """
        params: dict[str, str] = {"form_type": form_type}
        if template_id:
            params["template_id"] = template_id

        return await self._call_api(
            method="GET",
            path=APIUrls.FORM_PREFILL,
            parse_func=self._parse_simple_response,
            params=params,
            token=token,
            action_name="表单预填查询",
            service_name="表单引擎",
        )
