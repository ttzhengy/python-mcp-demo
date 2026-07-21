"""统一外部 API URL 管理。

所有后端 API 路径集中定义在此处，避免路径字符串散落在各适配器中。
基础 URL（base_url）从 config.py 的 settings.backend_base_url 读取。

用法::

    from python_mcp_demo.urls import APIUrls

    url = f"{base_url}{APIUrls.FORM_QUERY}"
"""


class APIUrls:
    """外部 API 路径常量。

    所有路径均为相对路径（以 ``/`` 开头），使用方拼接 ``base_url``。
    """

    # ── 表单服务 ──────────────────────────────────────────
    FORM_QUERY: str = "/api/forms/query"
    """表单查询。"""

    FORM_PREFILL: str = "/api/forms/prefill"
    """表单预填。"""

    FORM_SUBMIT: str = "/api/forms/submit"
    """表单提交。"""

    # ── 考勤服务 ──────────────────────────────────────────
    ATTENDANCE_QUERY: str = "/api/attendance/query"
    """考勤记录查询。"""

    CLOCK_IN: str = "/api/attendance/clock-in"
    """上班签到。"""

    CLOCK_OUT: str = "/api/attendance/clock-out"
    """下班签退。"""

    LEAVE_APPLY: str = "/api/attendance/leave/apply"
    """请假申请。"""

    LEAVE_QUERY: str = "/api/attendance/leave/query"
    """请假记录查询。"""
