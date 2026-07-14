"""表单引擎 HTTP API 适配器。

封装对 Java 表单引擎后端服务的 HTTP 调用。
遵循架构约束：
  - 存量零改造：Java 后端不做任何变更，MCP 层作为外部调用方
  - 用户身份代理：透传用户 JWT Token 到后端
  - HTTP Header 添加 X-AI-Agent 审计标记
"""

from __future__ import annotations

import time

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from python_mcp_demo.logging_ import logger


class FormEngineAdapter:
    """表单引擎 HTTP API 客户端。

    每个方法对应一个后端 API 端点。支持：
    - 统一超时控制
    - 指数退避重试（仅 5xx 错误）
    - 4xx 客户端错误直接返回（不重试）
    - 网络错误直接返回
    - X-AI-Agent 审计标记

    Args:
        base_url: 后端服务基础 URL。
        timeout: HTTP 读超时（秒）。
        connect_timeout: HTTP 连接超时（秒）。
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

    def _build_headers(self, token: str) -> dict[str, str]:
        """构建 HTTP 请求头。

        Args:
            token: 用户 JWT Token。

        Returns:
            包含 Authorization、X-AI-Agent 和 Content-Type 的请求头。
        """
        return {
            "Authorization": f"Bearer {token}",
            "X-AI-Agent": "dify-workflow/v1",
            "Content-Type": "application/json",
        }

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

        调用后端表单引擎 API，返回查询结果或友好的错误消息。

        Args:
            token: 用户 JWT Token。
            form_type: 表单类型名称（如"请假申请"），可选。
            date_from: 时间范围起（YYYY-MM-DD），可选。
            date_to: 时间范围止（YYYY-MM-DD），可选。
            status: 表单状态（如"已审批"），可选。
            limit: 返回条数上限，默认 10。

        Returns:
            包含 success、data 和 error 字段的字典。
            成功时 data 包含 total、returned、items。
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
                path="/api/forms",
                params=params,
                token=token,
            )
            return self._parse_response(result)

        except httpx.TimeoutException:
            logger.warning("表单引擎查询超时")
            return {
                "success": False,
                "data": None,
                "error": "查询超时，请稍后重试",
            }
        except httpx.RequestError as exc:
            logger.error("表单引擎不可达: {error}", error=str(exc))
            return {
                "success": False,
                "data": None,
                "error": "后端服务暂时不可用，请稍后重试",
            }

    # ── 内部方法 ──────────────────────────────────────────

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
        token: str | None = None,
    ) -> httpx.Response:
        """执行 HTTP 请求（含重试逻辑）。

        仅在遇到 5xx 状态码时重试，最多重试 3 次，
        使用指数退避（1s / 2s / 4s）。

        Args:
            method: HTTP 方法（GET / POST）。
            path: API 路径（如 /api/forms）。
            params: URL 查询参数。
            token: 用户 JWT Token。

        Returns:
            httpx.Response 对象。

        Raises:
            httpx.HTTPStatusError: 4xx/5xx 状态码（5xx 会自动重试）。
            httpx.TimeoutException: 请求超时。
            httpx.RequestError: 网络错误。
        """
        headers = self._build_headers(token) if token else {}

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(
                self._timeout,
                connect=self._connect_timeout,
            ),
        ) as client:
            response = await client.request(
                method=method,
                url=f"{self._base_url}{path}",
                params=params,
                headers=headers,
            )

            # 4xx 不重试，直接返回
            if 400 <= response.status_code < 500:
                return response

            # 5xx 抛出异常触发 tenacity 重试
            response.raise_for_status()
            return response

    def _parse_response(self, response: httpx.Response) -> dict:
        """解析后端 API 响应为统一格式。

        Args:
            response: httpx.Response 对象。

        Returns:
            统一格式的响应字典。
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
                return {
                    "success": False,
                    "data": None,
                    "error": "后端返回数据格式异常",
                }

        if response.status_code == 401:
            return {
                "success": False,
                "data": None,
                "error": "登录已过期，请刷新页面后重试",
            }

        if response.status_code == 403:
            return {
                "success": False,
                "data": None,
                "error": "权限不足，无法查询表单数据",
            }

        # 4xx 其他错误
        if 400 <= response.status_code < 500:
            return {
                "success": False,
                "data": None,
                "error": f"请求参数错误 ({response.status_code})",
            }

        # 5xx（重试后仍然失败）
        return {
            "success": False,
            "data": None,
            "error": f"后端服务异常，请稍后重试 ({response.status_code})",
        }
