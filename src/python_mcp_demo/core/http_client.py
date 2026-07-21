"""HTTP 客户端基类 — 统一超时、重试和错误处理。

所有外部 HTTP API 适配器继承此基类，复用统一的：
  - 超时控制（连接超时 + 读超时）
  - 指数退避重试（仅 5xx 状态码）
  - 4xx 直接返回（不重试）
  - X-AI-Agent 审计标记
  - 响应解析
"""

from __future__ import annotations

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from python_mcp_demo.logging_ import logger


class BaseHttpClient:
    """HTTP API 客户端基类。

    封装统一的 HTTP 请求行为。子类只需定义业务方法
    （如 ``query_forms``），调用 ``_do_request`` 和 ``_parse_response``。

    Args:
        base_url: 后端服务基础 URL。
        timeout: HTTP 读超时（秒）。
        connect_timeout: 连接超时（秒）。
        max_retries: 5xx 错误最大重试次数。
    """

    def __init__(
        self,
        base_url: str,
        timeout: int = 20,
        connect_timeout: int = 5,
        max_retries: int = 3,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._connect_timeout = connect_timeout
        self._max_retries = max_retries

    def _build_headers(self, token: str | None = None) -> dict[str, str]:
        """构建 HTTP 请求头。

        Args:
            token: 用户 JWT Token（可选）。

        Returns:
            包含 X-AI-Agent 和 Content-Type 的请求头。如有 token 则添加 Authorization。
        """
        headers: dict[str, str] = {
            "X-AI-Agent": "dify-workflow/v1",
            "Content-Type": "application/json",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    @retry(
        retry=retry_if_exception_type(httpx.HTTPStatusError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )
    async def _do_request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        json_data: dict | None = None,
        token: str | None = None,
    ) -> httpx.Response:
        """执行 HTTP 请求（含重试逻辑）。

        仅在遇到 5xx 状态码时重试，最多重试 3 次，使用指数退避。

        Args:
            method: HTTP 方法（GET / POST）。
            path: API 路径（如 ``/api/forms/query``）。
            params: URL 查询参数。
            json_data: JSON 请求体。
            token: 用户 JWT Token。

        Returns:
            httpx.Response 对象。

        Raises:
            httpx.HTTPStatusError: 4xx/5xx 状态码（5xx 自动重试）。
            httpx.TimeoutException: 请求超时。
            httpx.RequestError: 网络错误。
        """
        headers = self._build_headers(token)
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(self._timeout, connect=self._connect_timeout),
        ) as client:
            response = await client.request(
                method=method,
                url=f"{self._base_url}{path}",
                params=params,
                json=json_data,
                headers=headers,
            )
            # 4xx 不重试，直接返回
            if 400 <= response.status_code < 500:
                return response
            # 5xx 抛出异常触发 tenacity 重试
            response.raise_for_status()
            return response

    def _parse_list_response(self, response: httpx.Response) -> dict:
        """解析列表类 API 响应为统一格式。

        Args:
            response: httpx.Response 对象。

        Returns:
            统一格式的响应字典::

                {"success": bool, "data": {"total": int, "returned": int, "items": [...]}, "error": str | None}
        """
        if response.status_code == 200:
            try:
                data = response.json()
                items = data.get("items", data.get("data", []))
                if isinstance(items, dict):
                    items = [items]
                total = data.get("total", len(items))
                return {
                    "success": True,
                    "data": {
                        "total": total,
                        "returned": len(items),
                        "items": items,
                    },
                    "error": None,
                }
            except (ValueError, TypeError) as exc:
                logger.error("解析后端响应失败: {error}", error=str(exc))
                return {"success": False, "data": None, "error": "后端返回数据格式异常"}

        if response.status_code == 401:
            return {"success": False, "data": None, "error": "登录已过期，请刷新页面后重试"}
        if response.status_code == 403:
            return {"success": False, "data": None, "error": "权限不足，无法执行此操作"}
        if 400 <= response.status_code < 500:
            return {"success": False, "data": None, "error": f"请求参数错误 ({response.status_code})"}

        # 5xx（重试后仍然失败）
        return {"success": False, "data": None, "error": f"后端服务异常，请稍后重试 ({response.status_code})"}

    def _parse_simple_response(self, response: httpx.Response) -> dict:
        """解析单对象操作类 API 响应（如签到、签退、提交）。

        Args:
            response: httpx.Response 对象。

        Returns:
            统一格式的响应字典::

                {"success": bool, "data": dict | None, "error": str | None}
        """
        if response.status_code in (200, 201):
            try:
                data = response.json()
                return {"success": True, "data": data, "error": None}
            except (ValueError, TypeError) as exc:
                logger.error("解析后端响应失败: {error}", error=str(exc))
                return {"success": False, "data": None, "error": "后端返回数据格式异常"}

        if response.status_code == 401:
            return {"success": False, "data": None, "error": "登录已过期，请刷新页面后重试"}
        if response.status_code == 403:
            return {"success": False, "data": None, "error": "权限不足，无法执行此操作"}
        if response.status_code == 404:
            return {"success": False, "data": None, "error": "请求的资源不存在"}
        if 400 <= response.status_code < 500:
            return {"success": False, "data": None, "error": f"请求参数错误 ({response.status_code})"}

        return {"success": False, "data": None, "error": f"后端服务异常，请稍后重试 ({response.status_code})"}
