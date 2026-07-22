"""通用 API 响应实体类（Value Object 模式）。

提供类型约束的响应结构，替代原始 dict 操作。
所有实体类支持 ``.to_dict()`` 方法转换为普通 dict，与 FastMCP 序列化兼容。

用法::

    # 解析 HTTP 响应 → 实体类
    resp: ApiResponse = parser.parse_list_response(http_response)
    if resp.success:
        items = resp.data.items  # IDE 类型提示可用
    else:
        log.error(resp.error)
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Any


@dataclass
class ApiResponse:
    """通用 API 响应实体。

    Attributes:
        success: 请求是否成功。
        data: 响应数据（可为任意类型，子类可限定）。
        error: 错误消息（成功时为 ``None``）。
    """

    success: bool
    data: Any = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """将实体转换为普通 dict，与 FastMCP / JSON 序列化兼容。

        Returns:
            ``{"success": bool, "data": ..., "error": str | None}``
        """
        return {
            "success": self.success,
            "data": self._encode_data(self.data),
            "error": self.error,
        }

    @staticmethod
    def _encode_data(data: Any) -> Any:
        """递归将实体类编码为 dict。"""
        if isinstance(data, (ApiResponse, ListData)):
            return data.to_dict()
        if isinstance(data, list):
            return [
                item.to_dict() if isinstance(item, ApiResponse) else item
                for item in data
            ]
        if isinstance(data, dict):
            return {
                k: v.to_dict() if isinstance(v, ApiResponse) else v
                for k, v in data.items()
            }
        return data


@dataclass
class ListData:
    """列表响应数据。

    Attributes:
        total: 总记录数。
        returned: 本次返回的记录数。
        items: 数据项列表。
    """

    total: int = 0
    returned: int = 0
    items: list = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """将实体转换为普通 dict。"""
        return {
            "total": self.total,
            "returned": self.returned,
            "items": self.items,
        }


@dataclass
class ListResponse(ApiResponse):
    """列表类 API 响应（继承自 ``ApiResponse``）。

    ``data`` 字段的类型收窄为 ``ListData | None``。
    """

    data: ListData | None = None


def error_response(
    message: str,
    *,
    success: bool = False,
) -> ApiResponse:
    """快速创建错误响应实体。

    Args:
        message: 错误描述。
        success: 是否标记为成功（默认 ``False``）。

    Returns:
        配置好的 ``ApiResponse`` 实例。
    """
    return ApiResponse(success=success, error=message)


def list_response(
    items: list,
    total: int | None = None,
) -> ListResponse:
    """快速创建列表响应实体。

    Args:
        items: 数据项列表。
        total: 总记录数（默认使用 ``len(items)``）。

    Returns:
        配置好的 ``ListResponse`` 实例。
    """
    returned = len(items)
    if total is None:
        total = returned
    return ListResponse(
        success=True,
        data=ListData(total=total, returned=returned, items=items),
    )


def simple_response(data: Any = None) -> ApiResponse:
    """快速创建单对象响应实体。

    Args:
        data: 响应数据对象。

    Returns:
        配置好的 ``ApiResponse`` 实例。
    """
    return ApiResponse(success=True, data=data)
