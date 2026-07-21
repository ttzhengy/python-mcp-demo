"""考勤数据模型。

定义签到、签退、请假相关的请求/响应 Pydantic 模型。
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ClockInRequest(BaseModel):
    """上班签到请求。"""

    user_id: str = Field(description="用户标识")


class ClockOutRequest(BaseModel):
    """下班签退请求。"""

    user_id: str = Field(description="用户标识")


class LeaveApplyRequest(BaseModel):
    """请假申请请求。

    Attributes:
        leave_type: 请假类型（年假、事假、病假、婚假、产假等）。
        date_from: 开始日期（YYYY-MM-DD）。
        date_to: 结束日期（YYYY-MM-DD）。
        reason: 请假原因。
        duration_days: 请假天数（自动计算，可选覆盖）。
    """

    leave_type: str = Field(description="请假类型: 年假/事假/病假/婚假/产假")
    date_from: str = Field(description="开始日期（YYYY-MM-DD）")
    date_to: str = Field(description="结束日期（YYYY-MM-DD）")
    reason: str = Field(description="请假原因")
    duration_days: float | None = Field(default=None, description="请假天数，自动计算时留空")


class AttendanceQueryRequest(BaseModel):
    """考勤记录查询请求。"""

    date_from: str | None = Field(default=None, description="时间范围起（YYYY-MM-DD）")
    date_to: str | None = Field(default=None, description="时间范围止（YYYY-MM-DD）")
    status: str | None = Field(default=None, description="考勤状态筛选")
    limit: int = Field(default=10, ge=1, le=100, description="返回条数上限")


class AttendanceQueryResponseData(BaseModel):
    """考勤查询响应数据。"""

    total: int = Field(description="符合条件的总记录数")
    returned: int = Field(description="实际返回的记录数")
    items: list[dict] = Field(default_factory=list, description="考勤记录列表")


class AttendanceOperationResponse(BaseModel):
    """考勤操作（签到/签退/请假）的统一响应。"""

    success: bool = Field(description="是否成功")
    data: dict | None = Field(default=None, description="操作结果数据")
    error: str | None = Field(default=None, description="失败时的错误消息")
