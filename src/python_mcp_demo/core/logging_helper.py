"""工具日志上下文管理器 — 统一 trace_id 生成、耗时计算和 JSON 日志输出。

替代 tools 层中每个工具函数重复的以下样板代码::

    trace_id = uuid.uuid4().hex[:12]
    tool_name = "xxx"
    start_time = time.time()
    # ... 业务逻辑 ...
    elapsed = int((time.time() - start_time) * 1000)
    log_json("INFO", trace_id, tool_name, elapsed, "success", ...)

用法::

    async with ToolLogger("query_forms", user_token=user_token) as logger:
        result = await service.query_forms(...)
        logger.set_result(result)
        return result
    # 退出上下文时自动计算耗时并输出 log_json
"""

from __future__ import annotations

import time
import uuid
from typing import Any

from python_mcp_demo.logging_ import log_json
from python_mcp_demo.models.vo import ApiResponse


class ToolLogger:
    """工具日志上下文管理器。

    自动生成 trace_id、计算耗时、根据结果状态输出统一 JSON 日志。
    不改变 FastMCP tool 函数的签名（因此可与 ``@server.tool()`` 装饰器共用）。

    Attributes:
        trace_id: 12 字符的请求追踪 ID。

    Args:
        tool_name: 工具名称（将填入 log_json 的 ``tool_name`` 字段）。
        user_token: 用户 JWT Token（日志中自动脱敏）。
        user_id: 用户标识（可选，可在认证后通过 ``set_user_id`` 设置）。
    """

    def __init__(
        self,
        tool_name: str,
        *,
        user_token: str | None = None,
        user_id: str | None = None,
    ) -> None:
        self._tool_name = tool_name
        self._user_token = user_token
        self._user_id = user_id
        self._trace_id: str = uuid.uuid4().hex[:12]
        self._start_time: float = 0.0
        self._result: dict | None = None
        self._error: str | None = None
        self._extra: dict[str, Any] | None = None

    # ── 异步上下文管理器协议 ──────────────────────────────────────

    async def __aenter__(self) -> ToolLogger:
        """记录开始时间并返回自身。"""
        self._start_time = time.time()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """退出时计算耗时并输出结构化日志。"""
        elapsed = int((time.time() - self._start_time) * 1000)

        if exc_type is not None:
            # 未捕获的异常
            log_json(
                "ERROR", self._trace_id, self._tool_name, elapsed, "error",
                user_token=self._user_token, user_id=self._user_id,
                error=str(exc_val),
            )
            return  # 不吞异常 —— 返回 None 等价于 False，异常继续传播

        # 从 set_error / set_result 推断状态
        if self._error:
            log_json(
                "ERROR", self._trace_id, self._tool_name, elapsed, "error",
                user_token=self._user_token, user_id=self._user_id,
                error=self._error, extra=self._extra,
            )
        elif self._result and not self._result.get("success", True):
            log_json(
                "ERROR", self._trace_id, self._tool_name, elapsed, "error",
                user_token=self._user_token, user_id=self._user_id,
                error=self._result.get("error"), extra=self._extra,
            )
        else:
            returned = (
                self._result.get("data", {}).get("returned", 0)
                if self._result and self._result.get("data")
                else None
            )
            merged_extra = dict(self._extra) if self._extra else {}
            if returned is not None:
                merged_extra["returned"] = returned
            log_json(
                "INFO", self._trace_id, self._tool_name, elapsed, "success",
                user_token=self._user_token, user_id=self._user_id,
                extra=merged_extra or None,
            )

    # ── 公共设置方法 ──────────────────────────────────────────────

    def set_result(self, result: dict | ApiResponse) -> None:
        """设置业务结果。

        Args:
            result: 工具函数返回的响应字典或 ``ApiResponse`` 实体
                （应包含 ``success`` 和可选的 ``data``、``error`` 键/属性）。
        """
        if isinstance(result, ApiResponse):
            self._result = result.to_dict()
        else:
            self._result = result

    def set_error(self, error: str) -> None:
        """设置错误消息（不依赖 result 字典结构）。

        Args:
            error: 错误描述字符串。
        """
        self._error = error

    def set_extra(self, extra: dict[str, Any]) -> None:
        """设置额外日志字段（会与自动字段合并）。

        Args:
            extra: 要附加到日志记录的键值对。
        """
        self._extra = extra

    def set_user_id(self, user_id: str) -> None:
        """设置用户标识（可在认证后补充）。

        Args:
            user_id: 用户标识。
        """
        self._user_id = user_id

    # ── 只读属性 ──────────────────────────────────────────────────

    @property
    def trace_id(self) -> str:
        """当前请求追踪 ID（12 字符十六进制字符串）。"""
        return self._trace_id
