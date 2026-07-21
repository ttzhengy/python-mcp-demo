# 考勤模块（Attendance Module）指南

## 概述

考勤模块是 `python-mcp-demo` 的四层业务模块之一，基于 **models → services → tools → adapters** 架构。

本模块提供以下 MCP 工具：

| 工具名称 | 操作类型 | 说明 |
|---------|---------|------|
| `clock_in` | 签到 | 上班签到打卡 |
| `clock_out` | 签退 | 下班签退打卡 |
| `leave_apply` | 请假 | 提交请假申请 |
| `query_attendance` | 查询 | 查询考勤记录 |
| `query_leave_records` | 查询 | 查询请假记录 |

---

## 模块结构

```
src/python_mcp_demo/
├── models/attendance.py          # 数据模型（Pydantic）
├── services/attendance_service.py # 业务逻辑层
├── tools/attendance_query.py      # 查询类 MCP 工具
├── tools/attendance_submit.py     # 操作类 MCP 工具
└── adapters/attendance_api.py     # HTTP API 适配器
```

### 四层职责

| 层级 | 职责 | 依赖 |
|------|------|------|
| **adapters/** | HTTP 通信、重试、超时、响应解析 | `core/http_client.py`、`urls.py` |
| **services/** | 纯业务逻辑、参数校验、适配器编排 | adapters |
| **tools/** | FastMCP `@server.tool()` 薄封装 | services、auth 中间件 |
| **models/** | Pydantic 请求/响应数据结构 | 无 |

**约束：**
- services 层 **不依赖** FastMCP（纯 Python）
- tools 层 **不做** 业务逻辑（仅参数校验 + 调用 service + 格式化）
- adapters 层 **只做** HTTP 通信（不含业务逻辑）
- URL 路径从 `urls.py` 的 `APIUrls` 类引用

---

## 新增考勤操作类型的步骤

如需新增考勤操作（如加班申请 `overtime_apply`、调休申请 `compensatory_leave`），按以下步骤操作：

### 第一步：在 `urls.py` 添加 API 路径

```python
# src/python_mcp_demo/urls.py
class APIUrls:
    # ... 已有路径 ...

    # 新增
    OVERTIME_APPLY = "/api/attendance/overtime/apply"
```

### 第二步：在 `models/attendance.py` 添加数据模型（如需要）

```python
class OvertimeApplyRequest(BaseModel):
    """加班申请请求。"""
    date: str = Field(description="加班日期（YYYY-MM-DD）")
    hours: float = Field(description="加班小时数")
    reason: str = Field(description="加班原因")
```

### 第三步：在 `adapters/attendance_api.py` 添加 API 方法

```python
async def overtime_apply(self, token: str, date: str, hours: float, reason: str) -> dict:
    """加班申请。"""
    try:
        result = await self._do_request(
            method="POST",
            path=APIUrls.OVERTIME_APPLY,
            json_data={"date": date, "hours": hours, "reason": reason},
            token=token,
        )
        return self._parse_simple_response(result)
    except httpx.TimeoutException:
        logger.warning("加班申请超时")
        return {"success": False, "data": None, "error": "加班申请超时，请稍后重试"}
    except httpx.RequestError as exc:
        logger.error("考勤服务不可达: {error}", error=str(exc))
        return {"success": False, "data": None, "error": "考勤服务暂时不可用"}
```

### 第四步：在 `services/attendance_service.py` 添加业务方法

```python
async def overtime_apply(self, token: str, date: str, hours: float, reason: str) -> dict:
    """加班申请。"""
    # 业务规则：加班小时数不能超过 12
    if hours > 12:
        return {"success": False, "data": None, "error": "单日加班不能超过 12 小时"}
    return await self._adapter.overtime_apply(
        token=token, date=date, hours=hours, reason=reason
    )
```

### 第五步：在 `tools/` 中添加 MCP 工具

可选方案：

**方案 A**：追加到已有工具模块（操作类工具追加到 `attendance_submit.py`）：

```python
# 在 tools/attendance_submit.py 的 register_tools 函数内

@server.tool()
async def overtime_apply(
    user_token: str,
    date: str,
    hours: float,
    reason: str,
) -> dict:
    """申请加班。

    Args:
        user_token: 用户 JWT Token。
        date: 加班日期（YYYY-MM-DD）。
        hours: 加班小时数。
        reason: 加班原因。

    Returns:
        {"success": bool, "data": dict | None, "error": str | None}
    """
    # 参数校验 → token 校验 → 调用 service → 日志 → 返回
    ...
```

**方案 B**：创建新工具模块（如 `tools/overtime.py`），保持模块单一职责。

### 第六步：在 `main.py` 注册新工具

如果创建了新工具模块，需在 `main.py` 的 `create_server()` 中注册：

```python
from python_mcp_demo.tools import overtime  # 新模块

# 在 create_server() 内
overtime.register_tools(server, attendance_service, auth_middleware)
```

---

## 如何复用

### 在另一个 MCP 服务器中复用考勤模块

```python
from python_mcp_demo.adapters.attendance_api import AttendanceApiAdapter
from python_mcp_demo.services.attendance_service import AttendanceService

# 创建适配器
adapter = AttendanceApiAdapter(
    base_url="http://your-backend:8080",
    timeout=20,
)
# 创建服务
attendance_service = AttendanceService(adapter=adapter)

# 直接调用业务逻辑
result = await attendance_service.clock_in(token="user-jwt-token")
result = await attendance_service.leave_apply(
    token="user-jwt-token",
    leave_type="年假",
    date_from="2026-07-01",
    date_to="2026-07-03",
    reason="个人年假",
)
```

### 使用 BaseHttpClient 开发新适配器

```python
from python_mcp_demo.core.http_client import BaseHttpClient

class MyApiAdapter(BaseHttpClient):
    async def my_operation(self, token: str) -> dict:
        try:
            response = await self._do_request(
                method="GET", path="/api/my/endpoint", token=token,
            )
            return self._parse_simple_response(response)
        except httpx.TimeoutException:
            return {"success": False, "data": None, "error": "超时"}
```

---

## API 使用示例

### 签到

```
工具: clock_in
参数: {"user_token": "eyJhbG..."}
返回: {"success": true, "data": {"record_id": "A-2026-001", "time": "09:00:00"}, "error": null}
```

### 签退

```
工具: clock_out
参数: {"user_token": "eyJhbG..."}
返回: {"success": true, "data": {"record_id": "A-2026-001", "time": "18:00:00"}, "error": null}
```

### 请假

```
工具: leave_apply
参数: {
  "user_token": "eyJhbG...",
  "leave_type": "年假",
  "date_from": "2026-07-15",
  "date_to": "2026-07-17",
  "reason": "年度休假"
}
返回: {"success": true, "data": {"leave_id": "L-2026-001", "status": "待审批"}, "error": null}
```

### 查询考勤记录

```
工具: query_attendance
参数: {
  "user_token": "eyJhbG...",
  "date_from": "2026-07-01",
  "date_to": "2026-07-31",
  "limit": 10
}
返回: {"success": true, "data": {"total": 22, "returned": 10, "items": [...]}, "error": null}
```

### 查询请假记录

```
工具: query_leave_records
参数: {"user_token": "eyJhbG...", "status": "已审批"}
返回: {"success": true, "data": {"total": 3, "returned": 3, "items": [...]}, "error": null}
```
