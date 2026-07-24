"""考勤业务逻辑服务。

纯 Python 业务层，不依赖 FastMCP。
封装考勤相关的业务规则：签到、签退、请假、记录查询。
"""

from __future__ import annotations

from python_mcp_demo.attendance.api import AttendanceApiAdapter
from python_mcp_demo.models.vo import ApiResponse, ListResponse


class AttendanceService:
    """考勤业务服务。

    封装考勤操作（签到、签退、请假、查询）的业务逻辑。

    Args:
        adapter: 考勤服务 HTTP API 适配器。
    """

    def __init__(self, adapter: AttendanceApiAdapter) -> None:
        self._adapter = adapter

    async def clock_in(self, token: str) -> ApiResponse:
        """上班签到。

        Args:
            token: 用户 JWT Token。

        Returns:
            ``ApiResponse`` 实体。
        """
        return await self._adapter.clock_in(token=token)

    async def clock_out(self, token: str) -> ApiResponse:
        """下班签退。

        Args:
            token: 用户 JWT Token。

        Returns:
            ``ApiResponse`` 实体。
        """
        return await self._adapter.clock_out(token=token)

    async def leave_apply(
        self,
        token: str,
        leave_type: str,
        date_from: str,
        date_to: str,
        reason: str,
    ) -> ApiResponse:
        """请假申请。

        Args:
            token: 用户 JWT Token。
            leave_type: 请假类型。
            date_from: 开始日期（YYYY-MM-DD）。
            date_to: 结束日期（YYYY-MM-DD）。
            reason: 请假原因。

        Returns:
            ``ApiResponse`` 实体。
        """
        return await self._adapter.leave_apply(
            token=token,
            leave_type=leave_type,
            date_from=date_from,
            date_to=date_to,
            reason=reason,
        )

    async def query_records(
        self,
        token: str,
        date_from: str | None = None,
        date_to: str | None = None,
        status: str | None = None,
        limit: int = 10,
    ) -> ListResponse:
        """查询考勤记录。

        Args:
            token: 用户 JWT Token。
            date_from: 时间范围起（YYYY-MM-DD），可选。
            date_to: 时间范围止（YYYY-MM-DD），可选。
            status: 考勤状态，可选。
            limit: 返回条数上限，默认 10。

        Returns:
            ``ListResponse`` 实体。
        """
        effective_limit = min(limit, 100)
        return await self._adapter.query_records(
            token=token,
            date_from=date_from,
            date_to=date_to,
            status=status,
            limit=effective_limit,
        )

    async def query_leave(
        self,
        token: str,
        date_from: str | None = None,
        date_to: str | None = None,
        status: str | None = None,
        limit: int = 10,
    ) -> ListResponse:
        """查询请假记录。

        Args:
            token: 用户 JWT Token。
            date_from: 时间范围起（YYYY-MM-DD），可选。
            date_to: 时间范围止（YYYY-MM-DD），可选。
            status: 请假状态，可选。
            limit: 返回条数上限，默认 10。

        Returns:
            ``ListResponse`` 实体。
        """
        effective_limit = min(limit, 100)
        return await self._adapter.query_leave(
            token=token,
            date_from=date_from,
            date_to=date_to,
            status=status,
            limit=effective_limit,
        )
