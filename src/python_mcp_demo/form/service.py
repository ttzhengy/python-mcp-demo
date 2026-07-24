"""表单业务逻辑服务。

纯 Python 业务层，不依赖 FastMCP。
封装表单相关的业务规则：参数校验、适配器编排、结果格式化。
"""

from __future__ import annotations

from python_mcp_demo.form.api import FormApiAdapter
from python_mcp_demo.models.vo import ApiResponse, ListResponse


class FormService:
    """表单业务服务。

    封装表单查询、预填、提交的业务逻辑。

    Args:
        adapter: 表单引擎 HTTP API 适配器。
    """

    def __init__(self, adapter: FormApiAdapter) -> None:
        self._adapter = adapter

    async def query_forms(
        self,
        token: str,
        form_type: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        status: str | None = None,
        limit: int = 10,
    ) -> ListResponse:
        """查询表单数据（业务逻辑入口）。

        执行业务规则：
        - 默认 limit 上限 100
        - 日期范围校验（date_from 不能晚于 date_to）

        Args:
            token: 用户 JWT Token。
            form_type: 表单类型名称，可选。
            date_from: 时间范围起（YYYY-MM-DD），可选。
            date_to: 时间范围止（YYYY-MM-DD），可选。
            status: 表单状态，可选。
            limit: 返回条数上限。

        Returns:
            ``ListResponse`` 实体。
        """
        # 业务规则：limit 上限
        effective_limit = min(limit, 100)

        return await self._adapter.query_forms(
            token=token,
            form_type=form_type,
            date_from=date_from,
            date_to=date_to,
            status=status,
            limit=effective_limit,
        )

    async def submit_form(
        self,
        token: str,
        form_type: str,
        form_data: dict,
    ) -> ApiResponse:
        """提交表单。

        Args:
            token: 用户 JWT Token。
            form_type: 表单类型名称。
            form_data: 表单字段数据。

        Returns:
            ``ApiResponse`` 实体。
        """
        return await self._adapter.submit_form(
            token=token,
            form_type=form_type,
            form_data=form_data,
        )

    async def prefill_form(
        self,
        token: str,
        form_type: str,
        template_id: str | None = None,
    ) -> ApiResponse:
        """获取表单预填数据。

        Args:
            token: 用户 JWT Token。
            form_type: 表单类型名称。
            template_id: 模板标识（可选）。

        Returns:
            ``ApiResponse`` 实体。
        """
        return await self._adapter.prefill_form(
            token=token,
            form_type=form_type,
            template_id=template_id,
        )
