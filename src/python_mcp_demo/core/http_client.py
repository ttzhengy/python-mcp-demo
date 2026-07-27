"""HTTP 客户端基类 — 统一超时、重试、错误处理和响应解析。

所有外部 HTTP API 适配器继承此基类，复用统一的：
  - 超时控制（连接超时 + 读超时）
  - 指数退避重试（仅 5xx 状态码）
  - 4xx 直接返回（不重试）
  - X-AI-Agent 审计标记
  - 响应解析为 VO 实体类
  - ``_call_api`` 统一异常处理和日志记录（适配器不再重复 try/except）
"""

from __future__ import annotations

from typing import Any, Callable

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from python_mcp_demo.core.log import logger
from python_mcp_demo.models.vo import ApiResponse, ListData, ListResponse


class BaseHttpClient:
    """HTTP API 客户端基类。

    封装统一的 HTTP 请求行为。子类只需定义业务方法
    （如 ``query_forms``），调用 ``_call_api`` 传入解析函数即可。

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
        base_url_override: str | None = None,
    ) -> httpx.Response:
        """执行 HTTP 请求（含重试逻辑 + 基础错误日志）。

        仅在遇到 5xx 状态码时重试，最多重试 3 次，使用指数退避。
        在异常传播前记录日志，供 ``_call_api`` 或调用方捕获。

        Args:
            method: HTTP 方法（GET / POST）。
            path: API 路径（如 ``/api/forms/query``）。
            params: URL 查询参数。
            json_data: JSON 请求体。
            token: 用户 JWT Token。
            base_url_override: 动态覆盖 base_url（用于多租户/多环境路由）。

        Returns:
            httpx.Response 对象。

        Raises:
            httpx.HTTPStatusError: 4xx/5xx 状态码（5xx 自动重试）。
            httpx.TimeoutException: 请求超时。
            httpx.RequestError: 网络错误。
        """
        headers = self._build_headers(token)
        actual_base_url = base_url_override or self._base_url
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(self._timeout, connect=self._connect_timeout),
            ) as client:
                response = await client.request(
                    method=method,
                    url=f"{actual_base_url}{path}",
                    params=params,
                    json=json_data,
                    headers=headers,
                )
                # 4xx 不重试，直接返回
                if 400 <= response.status_code < 500:
                    logger.warning(
                        "HTTP 4xx: {method} {path} → {status}",
                        method=method, path=path, status=response.status_code,
                    )
                    return response
                # 5xx 抛出异常触发 tenacity 重试
                response.raise_for_status()
                return response
        except httpx.TimeoutException:
            logger.warning("请求超时: {method} {path}", method=method, path=path)
            raise
        except httpx.RequestError as exc:
            logger.error(
                "服务不可达: {method} {path} — {error}",
                method=method, path=path, error=str(exc),
            )
            raise

    async def _call_api(
        self,
        method: str,
        path: str,
        parse_func: Callable[[httpx.Response], ApiResponse | ListResponse],
        *,
        params: dict | None = None,
        json_data: dict | None = None,
        token: str | None = None,
        action_name: str = "请求",
        service_name: str = "后端服务",
        base_url_override: str | None = None,
    ) -> ApiResponse | ListResponse:
        """统一的 API 调用入口 — 简化子类的 try/except 样板代码。

        包装 ``_do_request`` + 解析 + 异常转换为 VO 实体。
        子类业务方法只需一行调用即可完成整个 HTTP 交互。

        Args:
            method: HTTP 方法。
            path: API 路径。
            parse_func: 响应解析函数（``_parse_list_response`` 或 ``_parse_simple_response``）。
            params: URL 查询参数。
            json_data: JSON 请求体。
            token: 用户 JWT Token。
            action_name: 用于日志和错误消息的操作名称（如"签到"、"查询"）。
            service_name: 用于日志的后端服务名称（如"考勤服务"、"表单引擎"）。
            base_url_override: 动态覆盖 base_url（用于多租户/多环境路由）。

        Returns:
            ``ApiResponse`` 或 ``ListResponse`` 实体（请求失败时包含错误信息）。
        """
        try:
            response = await self._do_request(
                method=method,
                path=path,
                params=params,
                json_data=json_data,
                token=token,
                base_url_override=base_url_override,
            )
            return parse_func(response)
        except httpx.TimeoutException:
            logger.warning("{name}超时", name=action_name)
            return ApiResponse(
                success=False,
                error=f"{action_name}超时，请稍后重试",
            )
        except httpx.RequestError as exc:
            logger.error(
                "{service}不可达: {error}",
                service=service_name, error=str(exc),
            )
            return ApiResponse(
                success=False,
                error=f"{service_name}暂时不可用，请稍后重试",
            )

    def _parse_list_response(self, response: httpx.Response) -> ListResponse:
        """解析列表类 API 响应为 ``ListResponse`` 实体。

        Args:
            response: httpx.Response 对象。

        Returns:
            类型约束的 ``ListResponse`` 实体。
        """
        if response.status_code == 200:
            try:
                data = response.json()
                items = data.get("items", data.get("data", []))
                if isinstance(items, dict):
                    items = [items]
                total = data.get("total", len(items))
                return ListResponse(
                    success=True,
                    data=ListData(total=total, returned=len(items), items=items),
                )
            except (ValueError, TypeError) as exc:
                logger.error("解析后端响应失败: {error}", error=str(exc))
                return ListResponse(success=False, error="后端返回数据格式异常")

        if response.status_code == 401:
            return ListResponse(success=False, error="登录已过期，请刷新页面后重试")
        if response.status_code == 403:
            return ListResponse(success=False, error="权限不足，无法执行此操作")
        if 400 <= response.status_code < 500:
            return ListResponse(
                success=False,
                error=f"请求参数错误 ({response.status_code})",
            )

        # 5xx（重试后仍然失败）
        return ListResponse(
            success=False,
            error=f"后端服务异常，请稍后重试 ({response.status_code})",
        )

    def _parse_simple_response(self, response: httpx.Response) -> ApiResponse:
        """解析单对象操作类 API 响应为 ``ApiResponse`` 实体。

        适用于签到、签退、提交等操作。

        Args:
            response: httpx.Response 对象。

        Returns:
            类型约束的 ``ApiResponse`` 实体。
        """
        if response.status_code in (200, 201):
            try:
                data = response.json()
                return ApiResponse(success=True, data=data)
            except (ValueError, TypeError) as exc:
                logger.error("解析后端响应失败: {error}", error=str(exc))
                return ApiResponse(success=False, error="后端返回数据格式异常")

        if response.status_code == 401:
            return ApiResponse(success=False, error="登录已过期，请刷新页面后重试")
        if response.status_code == 403:
            return ApiResponse(success=False, error="权限不足，无法执行此操作")
        if response.status_code == 404:
            return ApiResponse(success=False, error="请求的资源不存在")
        if 400 <= response.status_code < 500:
            return ApiResponse(
                success=False,
                error=f"请求参数错误 ({response.status_code})",
            )

        return ApiResponse(
            success=False,
            error=f"后端服务异常，请稍后重试 ({response.status_code})",
        )
