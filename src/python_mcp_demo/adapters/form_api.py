"""表单引擎 HTTP API 适配器。

封装对 Java 表单引擎后端服务的 HTTP 调用。
从原有的 form_engine.py 提取并基于 BaseHttpClient 重构。
"""

from __future__ import annotations

import httpx

from python_mcp_demo.core.http_client import BaseHttpClient
from python_mcp_demo.logging_ import logger
from python_mcp_demo.urls import APIUrls


class FormApiAdapter(BaseHttpClient):
    """表单引擎 HTTP API 客户端。

    每个业务方法对应一个后端 API 端点。
    继承 BaseHttpClient 的统一超时、重试和错误处理。
    """

    async def query_forms(
        self,
        token: str,
        form_type: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        status: str | None = None,
        limit: int = 10,
    ) -> dict:
        """查询表单数据。

        Args:
            token: 用户 JWT Token。
            form_type: 表单类型名称（如"请假申请"），可选。
            date_from: 时间范围起（YYYY-MM-DD），可选。
            date_to: 时间范围止（YYYY-MM-DD），可选。
            status: 表单状态（如"已审批"），可选。
            limit: 返回条数上限，默认 10。

        Returns:
            包含 success、data 和 error 字段的字典。
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

        try:
            result = await self._do_request(
                method="GET",
                path=APIUrls.FORM_QUERY,
                params=params,
                token=token,
            )
            return self._parse_list_response(result)
        except httpx.TimeoutException:
            logger.warning("表单引擎查询超时")
            return {"success": False, "data": None, "error": "查询超时，请稍后重试"}
        except httpx.RequestError as exc:
            logger.error("表单引擎不可达: {error}", error=str(exc))
            return {"success": False, "data": None, "error": "后端服务暂时不可用，请稍后重试"}

    async def submit_form(
        self,
        token: str,
        form_type: str,
        form_data: dict,
    ) -> dict:
        """提交表单数据。

        Args:
            token: 用户 JWT Token。
            form_type: 表单类型名称。
            form_data: 表单字段数据。

        Returns:
            包含 success、data 和 error 字段的字典。
        """
        try:
            result = await self._do_request(
                method="POST",
                path=APIUrls.FORM_SUBMIT,
                json_data={"form_type": form_type, "form_data": form_data},
                token=token,
            )
            return self._parse_simple_response(result)
        except httpx.TimeoutException:
            logger.warning("表单提交超时")
            return {"success": False, "data": None, "error": "提交超时，请稍后重试"}
        except httpx.RequestError as exc:
            logger.error("表单引擎不可达: {error}", error=str(exc))
            return {"success": False, "data": None, "error": "后端服务暂时不可用，请稍后重试"}

    async def prefill_form(
        self,
        token: str,
        form_type: str,
        template_id: str | None = None,
    ) -> dict:
        """获取表单预填数据。

        Args:
            token: 用户 JWT Token。
            form_type: 表单类型名称。
            template_id: 模板标识（可选）。

        Returns:
            包含 success、data 和 error 字段的字典。
        """
        params: dict[str, str] = {"form_type": form_type}
        if template_id:
            params["template_id"] = template_id

        try:
            result = await self._do_request(
                method="GET",
                path=APIUrls.FORM_PREFILL,
                params=params,
                token=token,
            )
            return self._parse_simple_response(result)
        except httpx.TimeoutException:
            logger.warning("表单预填查询超时")
            return {"success": False, "data": None, "error": "查询超时，请稍后重试"}
        except httpx.RequestError as exc:
            logger.error("表单引擎不可达: {error}", error=str(exc))
            return {"success": False, "data": None, "error": "后端服务暂时不可用，请稍后重试"}
