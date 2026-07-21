"""表单数据模型。

定义表单查询、预填、提交相关的请求/响应 Pydantic 模型。
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class FormQueryRequest(BaseModel):
    """表单查询请求参数。

    Attributes:
        form_type: 表单类型名称（如"请假申请"），可选。
        date_from: 时间范围起（YYYY-MM-DD），可选。
        date_to: 时间范围止（YYYY-MM-DD），可选。
        status: 表单状态（如"已审批"、"待审批"），可选。
        limit: 返回条数上限，默认 10。
    """

    form_type: str | None = Field(default=None, description="表单类型名称，如'请假申请'")
    date_from: str | None = Field(default=None, description="时间范围起（YYYY-MM-DD）")
    date_to: str | None = Field(default=None, description="时间范围止（YYYY-MM-DD）")
    status: str | None = Field(default=None, description="表单状态，如'已审批'")
    limit: int = Field(default=10, ge=1, le=100, description="返回条数上限")


class FormQueryResponseData(BaseModel):
    """表单查询响应数据。"""

    total: int = Field(description="符合条件的总记录数")
    returned: int = Field(description="实际返回的记录数")
    items: list[dict] = Field(default_factory=list, description="表单记录列表")


class FormQueryResponse(BaseModel):
    """表单查询统一响应。"""

    success: bool = Field(description="是否成功")
    data: FormQueryResponseData | None = Field(default=None, description="查询结果数据")
    error: str | None = Field(default=None, description="失败时的错误消息")


class FormSubmitRequest(BaseModel):
    """表单提交请求。"""

    form_type: str = Field(description="表单类型名称")
    form_data: dict = Field(default_factory=dict, description="表单字段数据")


class FormPrefillRequest(BaseModel):
    """表单预填请求。"""

    form_type: str = Field(description="表单类型名称")
    template_id: str | None = Field(default=None, description="模板标识")
