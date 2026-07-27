"""认证中间件 — Token 前置校验。

在业务操作前调用后端认证 API 验证 JWT Token 有效性。
MCP 层不做权限判断，仅做 token 有效性预检（过期 token 提前拦截）。

安全约束（来自 ADR-002）：
  - Cookie 隔离：cookie 不传入 Dify / LLM，仅传递 JWT
  - Token 前置校验：MCP 层调用后端认证 API 验证 token 有效性
  - X-AI-Agent：HTTP Header 添加 AI 代理审计标记
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from python_mcp_demo.core.log import logger


@dataclass
class TokenVerificationResult:
    """Token 校验结果。

    Attributes:
        valid: Token 是否有效。
        user_id: 校验通过时的用户标识。
        error: 校验失败时的错误消息。
    """
    valid: bool
    user_id: str = ""
    error: str = ""


class AuthMiddleware:
    """Token 前置校验中间件。

    封装对后端认证 API 的调用，用于在执行业务操作前
    验证用户 JWT Token 的有效性。

    Args:
        auth_url: 后端认证 API 的完整 URL。
        timeout: HTTP 请求超时（秒）。
    """

    def __init__(self, auth_url: str, timeout: int = 10) -> None:
        self._auth_url = auth_url
        self._timeout = timeout

    async def verify_token(self, token: str) -> TokenVerificationResult:
        """调用后端认证 API 验证 Token 有效性。

        Args:
            token: 用户 JWT Token。

        Returns:
            TokenVerificationResult: 包含 valid、user_id 和 error 字段。
        """
        if not token or not token.strip():
            return TokenVerificationResult(valid=False, error="Token 不能为空")

        if not self._auth_url:
            # 开发/测试模式：跳过真实校验
            logger.warning("后端认证 URL 未配置，跳过 Token 校验")
            return TokenVerificationResult(valid=True, user_id="dev_user")

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    self._auth_url,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "X-AI-Agent": "dify-workflow/v1",
                        "Content-Type": "application/json",
                    },
                    json={"token": token},
                )

                if response.status_code == 200:
                    data = response.json()
                    return TokenVerificationResult(
                        valid=True,
                        user_id=data.get("user_id", ""),
                    )

                if response.status_code == 401:
                    return TokenVerificationResult(
                        valid=False,
                        error="登录已过期，请刷新页面后重试",
                    )

                if response.status_code == 403:
                    return TokenVerificationResult(
                        valid=False,
                        error="权限不足，无法执行此操作",
                    )

                logger.warning(
                    "认证服务返回意外状态码: {status}",
                    status=response.status_code,
                )
                return TokenVerificationResult(
                    valid=False,
                    error=f"认证服务异常，请稍后重试 ({response.status_code})",
                )

        except httpx.TimeoutException:
            logger.error("认证服务请求超时")
            return TokenVerificationResult(
                valid=False,
                error="认证服务暂时不可用，请稍后重试",
            )
        except httpx.RequestError as exc:
            logger.error("认证服务不可达: {error}", error=str(exc))
            return TokenVerificationResult(
                valid=False,
                error="认证服务暂时不可用，请稍后重试",
            )
