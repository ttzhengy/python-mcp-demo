"""工具装饰器 — 将日志和认证逻辑从工具函数体中剥离。

提供两个装饰器：

- ``@log_tool(tool_name)``  — 自动 trace_id、耗时计算、结构化日志
- ``@require_auth(auth_middleware)``  — Token 前置校验，注入 user_id

组合用法::

    @server.tool()
    @log_tool("query_forms")
    @require_auth(auth_middleware)
    async def query_forms(user_token: str, ...) -> dict:
        result = await service.query(...)
        return result.to_dict()

注意：``@server.tool()`` 必须放在最外层，因为 FastMCP 会直接调用内部函数，
外部装饰器不会被触发。
"""

from __future__ import annotations

import functools
import time
import uuid
from typing import Any, Callable

from python_mcp_demo.auth import AuthMiddleware
from python_mcp_demo.logging_ import log_json


def log_tool(tool_name: str):
    """工具日志装饰器 — 自动生成 trace_id、计算耗时、输出结构化日志。

    根据返回值的 ``success`` 字段自动判断成功/失败状态。
    异常会被捕获并记录日志后重新抛出。

    Args:
        tool_name: 工具名称（将填入日志的 ``tool_name`` 字段）。

    Returns:
        装饰器函数。

    Raises:
        原始异常：捕获后记录日志并重新抛出，不吞异常。
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            trace_id = uuid.uuid4().hex[:12]
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                elapsed_ms = int((time.time() - start) * 1000)

                # 判断状态
                if isinstance(result, dict):
                    status = "success" if result.get("success", True) else "error"
                    error_msg = result.get("error") if not result.get("success", True) else None
                else:
                    status = "success"
                    error_msg = None

                log_json(
                    "INFO" if status == "success" else "ERROR",
                    trace_id,
                    tool_name,
                    elapsed_ms,
                    status,
                    user_token=kwargs.get("user_token"),
                    user_id=kwargs.get("user_id"),
                    error=error_msg,
                )
                return result
            except Exception as exc:
                elapsed_ms = int((time.time() - start) * 1000)
                log_json(
                    "ERROR",
                    trace_id,
                    tool_name,
                    elapsed_ms,
                    "error",
                    user_token=kwargs.get("user_token"),
                    user_id=kwargs.get("user_id"),
                    error=str(exc),
                )
                raise

        return wrapper

    return decorator


def require_auth(auth_middleware: AuthMiddleware):
    """认证装饰器 — 自动校验 Token 并注入 user_id。

    从 kwargs 中提取 ``user_token``，调用认证中间件验证有效性。
    验证通过后将 ``user_id`` 注入 kwargs，验证失败则直接返回错误响应。

    Args:
        auth_middleware: 认证中间件实例。

    Returns:
        装饰器函数。
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            user_token = kwargs.get("user_token", "")

            # Token 为空检查
            if not user_token or not user_token.strip():
                return {
                    "success": False,
                    "data": None,
                    "error": "缺少用户认证信息，请重新登录后重试",
                }

            # Token 前置校验
            verify_result = await auth_middleware.verify_token(user_token)
            if not verify_result.valid:
                return {
                    "success": False,
                    "data": None,
                    "error": verify_result.error,
                }

            # 注入 user_id（保持 user_token 供 log_tool 使用）
            kwargs["user_id"] = verify_result.user_id

            return await func(*args, **kwargs)

        return wrapper

    return decorator
