# 架构说明文档

## 项目概述

`python-mcp-demo` 是一个基于 [FastMCP](https://github.com/jlowin/fastmcp) 构建的 AI 办公助手 MCP 服务器，采用 **5 层模块化架构**（v0.4.0）。

### 端到端链路

```
用户提问 → Dify Agent → MCP 协议 (SSE) → FastMCP 
→ tools (参数解析) → services (业务逻辑) 
→ adapters (HTTP 调用) → Java 后端
```

---

## 5 层分层架构

```
┌─────────────────────────────────────────────┐
│                  tools/                      │
│   FastMCP @server.tool() 定义（薄封装层）      │
│   参数解析 → 调用 service → 格式化返回         │
│   ┌──────────────────────────────────────┐   │
│   │ demo.py / form_query.py /            │   │
│   │ form_submit.py / attendance_query.py │   │
│   │ attendance_submit.py                 │   │
│   └──────────────────────────────────────┘   │
├─────────────────────────────────────────────┤
│                services/                     │
│   纯 Python 业务逻辑（不依赖 FastMCP）         │
│   封装业务规则：参数校验、适配器编排             │
│   ┌──────────────────────────────────────┐   │
│   │ form_service.py / attendance_service │   │
│   └──────────────────────────────────────┘   │
├─────────────────────────────────────────────┤
│                adapters/                     │
│   HTTP API 适配器（继承 BaseHttpClient）       │
│   封装对 Java 后端服务的 HTTP 调用             │
│   ┌──────────────────────────────────────┐   │
│   │ form_api.py / attendance_api.py       │   │
│   └──────────────────────────────────────┘   │
├─────────────────────────────────────────────┤
│                 core/                        │
│   跨模块基础设施                              │
│   ┌──────────────────────────────────────┐   │
│   │ http_client.py  BaseHttpClient 基类   │   │
│   └──────────────────────────────────────┘   │
├─────────────────────────────────────────────┤
│                models/                       │
│   Pydantic 数据模型                          │
│   ┌──────────────────────────────────────┐   │
│   │ form.py / attendance.py              │   │
│   └──────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

---

## 模块职责

### 1. `tools/` — 工具层

FastMCP `@server.tool()` 定义的薄封装层。每个工具函数只做三件事：

1. **参数解析** — 从函数参数中提取业务数据
2. **调用 service** — 将业务参数传给下层服务
3. **格式化返回** — 将 service 的返回格式化为 MCP 响应

**目录：**

| 文件 | 注册的工具 | 依赖 |
|------|-----------|------|
| `demo.py` | hello, fetch_url, add, calculate, random_number, current_time, echo, count_words | config, exceptions |
| `form_query.py` | query_forms | FormService, AuthMiddleware |
| `form_submit.py` | submit_form, prefill_form | FormService, AuthMiddleware |
| `attendance_query.py` | query_attendance, query_leave_records | AttendanceService, AuthMiddleware |
| `attendance_submit.py` | clock_in, clock_out, leave_apply | AttendanceService, AuthMiddleware |

### 2. `services/` — 业务服务层

纯 Python 业务逻辑，**不依赖 FastMCP**。封装业务规则：

- `FormService` — 表单查询、提交、预填的业务逻辑（limit 上限、日期范围校验）
- `AttendanceService` — 考勤签到、签退、请假申请、记录查询的业务逻辑

### 3. `adapters/` — 适配器层

HTTP API 客户端，继承 `BaseHttpClient`，封装对 Java 后端服务的 HTTP 调用。

- `FormApiAdapter` — 表单引擎（form_engine）HTTP API
- `AttendanceApiAdapter` — 考勤服务 HTTP API

### 4. `core/` — 基础设施层

- `http_client.py` — `BaseHttpClient` 基类，提供统一的：
  - 超时控制（连接超时 + 读超时）
  - 指数退避重试（tenacity，仅 5xx 状态码）
  - 4xx 直接返回（不重试）
  - X-AI-Agent 审计标记
  - 响应解析（`_parse_list_response` / `_parse_simple_response`）

### 5. `models/` — 数据模型层

Pydantic `BaseModel` 定义，用于请求/响应的类型约束和验证。

- `form.py` — `FormQueryRequest`, `FormQueryResponse`, `FormSubmitRequest`, `FormPrefillRequest`
- `attendance.py` — `ClockInRequest`, `ClockOutRequest`, `LeaveApplyRequest`, `AttendanceQueryRequest`

---

## 模块间调用关系

```
main.py:create_server()
  │
  ├── tools/demo.py:register_tools(server)
  │     └── 直接返回，不依赖 service/adapter
  │
  ├── tools/form_query.py:register_tools(server, form_service, auth_middleware)
  │     └── form_service.query_forms()
  │           └── FormApiAdapter.query_forms()  ← BaseHttpClient._do_request()
  │
  ├── tools/form_submit.py:register_tools(server, form_service, auth_middleware)
  │     └── form_service.submit_form() / form_service.prefill_form()
  │           └── FormApiAdapter.submit_form() / .prefill_form()
  │
  ├── tools/attendance_query.py:register_tools(server, attendance_service, auth_middleware)
  │     └── attendance_service.query_records() / .query_leave()
  │           └── AttendanceApiAdapter.query_records() / .query_leave()
  │
  └── tools/attendance_submit.py:register_tools(server, attendance_service, auth_middleware)
        └── attendance_service.clock_in() / .clock_out() / .leave_apply()
              └── AttendanceApiAdapter.clock_in() / .clock_out() / .leave_apply()
```

### 认证中间件调用

每个业务工具在调用 service 前，先调用 `auth_middleware.verify_token()` 前置校验 JWT Token 有效性：

```
tools/form_query.py
  → auth_middleware.verify_token(user_token)  ← 前置校验
  → form_service.query_forms(...)              ← 业务逻辑
```

### 响应格式统一

所有 HTTP API 适配器返回统一格式：

```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```

- **列表类响应**（query_forms / query_attendance）：data 包含 `{total, returned, items}`
- **操作类响应**（clock_in / submit_form）：data 为直接结果对象

---

## 项目目录树

```
python-mcp-demo/
├── src/python_mcp_demo/         # 源码包
│   ├── __init__.py              # 导出 create_server, mcp, tools
│   ├── __main__.py              # CLI 入口: python -m python_mcp_demo
│   ├── server.py                # 向后兼容封装（57 行精简版）
│   ├── main.py                  # FastAPI + FastMCP 入口
│   ├── config.py                # 配置管理（pydantic-settings, MCP_ 前缀）
│   ├── auth.py                  # Token 前置校验中间件
│   ├── exceptions.py            # 自定义异常体系
│   ├── logging_.py              # loguru 结构化日志
│   ├── urls.py                  # API URL 集中管理
│   ├── core/
│   │   └── http_client.py       # BaseHttpClient 基类
│   ├── models/
│   │   ├── form.py              # 表单数据模型
│   │   └── attendance.py        # 考勤数据模型
│   ├── services/
│   │   ├── form_service.py      # 表单业务逻辑
│   │   └── attendance_service.py # 考勤业务逻辑
│   ├── adapters/
│   │   ├── form_api.py          # 表单引擎 HTTP API 适配器
│   │   └── attendance_api.py    # 考勤服务 HTTP API 适配器
│   └── tools/
│       ├── demo.py              # 8 个基础 demo 工具
│       ├── form_query.py        # 表单查询工具
│       ├── form_submit.py       # 表单提交工具
│       ├── attendance_query.py  # 考勤查询工具
│       └── attendance_submit.py # 考勤操作工具
├── tests/
│   └── test_demo.py             # Demo 工具 pytest 测试
├── docs/
│   ├── api.md                   # API 接口文档
│   ├── architecture.md          # 本文档
│   └── attendance-module-guide.md  # 考勤模块使用指南
├── pyproject.toml               # 项目元数据与构建配置
├── .env.example                 # 环境变量配置模板
└── README.md                    # 项目总览与快速开始
```

---

## URL 集中管理

所有后端 API 路径集中定义在 `urls.py` 的 `APIUrls` 类中，避免路径字符串散落在各适配器中：

```python
class APIUrls:
    # 表单服务
    FORM_QUERY: str = "/api/forms/query"
    FORM_PREFILL: str = "/api/forms/prefill"
    FORM_SUBMIT: str = "/api/forms/submit"

    # 考勤服务
    ATTENDANCE_QUERY: str = "/api/attendance/query"
    CLOCK_IN: str = "/api/attendance/clock-in"
    CLOCK_OUT: str = "/api/attendance/clock-out"
    LEAVE_APPLY: str = "/api/attendance/leave/apply"
    LEAVE_QUERY: str = "/api/attendance/leave/query"
```

---

## 配置说明

所有配置项通过环境变量或 `.env` 文件设置，以 `MCP_` 为前缀。

详见 `config.py` 中的 `Settings` 类的完整字段列表。

---

## 架构决策

### ADR-001：使用 FastMCP 而非底层 SDK

选择 FastMCP 作为 MCP 服务器框架，理由：
- 装饰器风格的 tool 定义（`@server.tool()`），开发效率高
- 内置 SSE 和 stdio 双传输模式
- 活跃的社区维护

### ADR-002：Token 前置校验 + 透传

- 用户身份通过 JWT Token 透传到 Java 后端
- MCP 层仅做 Token 有效性前置校验（过期提前拦截）
- HTTP Header 添加 `X-AI-Agent: dify-workflow/v1` 审计标记

### ADR-003：存量零改造

Java 后端不做任何变更，MCP 层以标准 HTTP 客户端身份调用后端 API。

### ADR-004：5 层模块化分层

将原有平铺结构重构为五层，职责分离：
- **tools** — MCP 协议耦合层
- **services** — 纯业务逻辑
- **adapters** — 外部系统适配
- **core** — 基础设施复用
- **models** — 数据模型共享
