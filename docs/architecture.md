# 架构说明文档

## 项目概述

`python-mcp-demo` 是一个基于 [FastMCP](https://github.com/jlowin/fastmcp) 构建的 AI 办公助手 MCP 服务器，采用 **按业务领域分包** 的模块化架构（v0.4.1）。

### 端到端链路

```
用户提问 → Dify Agent → MCP 协议 (SSE) → FastMCP 
→ tools (薄封装，装饰器驱动) → service (业务逻辑) 
→ api adapter (HTTP 调用) → Java 后端
```

---

## 业务领域分包架构

```
┌─────────────────────────────────────────────┐
│              attendance/                    │
│   考勤业务领域                               │
│   ┌─────────────────────────────────────┐   │
│   │ models.py   — 考勤数据模型          │   │
│   │ service.py  — 考勤业务逻辑          │   │
│   │ query.py    — 考勤查询 MCP 工具     │   │
│   │ submit.py   — 考勤操作 MCP 工具     │   │
│   │ api.py      — 考勤 HTTP API 适配器  │   │
│   └─────────────────────────────────────┘   │
├─────────────────────────────────────────────┤
│                form/                         │
│   表单业务领域                               │
│   ┌─────────────────────────────────────┐   │
│   │ models.py   — 表单数据模型          │   │
│   │ service.py  — 表单业务逻辑          │   │
│   │ query.py    — 表单查询 MCP 工具     │   │
│   │ submit.py   — 表单提交 MCP 工具     │   │
│   │ api.py      — 表单 HTTP API 适配器  │   │
│   └─────────────────────────────────────┘   │
├─────────────────────────────────────────────┤
│                core/                         │
│   跨域基础设施                               │
│   ┌─────────────────────────────────────┐   │
│   │ http_client.py      BaseHttpClient  │   │
│   │ logging_helper.py   ToolLogger      │   │
│   │ tool_decorators.py  @log_tool       │   │
│   │                     @require_auth   │   │
│   └─────────────────────────────────────┘   │
├─────────────────────────────────────────────┤
│              models/ + tools/                │
│   通用 VO 实体 + Demo 工具集                 │
│   ┌─────────────────────────────────────┐   │
│   │ models/vo.py  ApiResponse 等        │   │
│   │ tools/demo.py  8 个基础 demo 工具   │   │
│   └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

---

## 装饰器驱动模式（v0.4.1 新增）

工具函数使用 ``@log_tool`` 和 ``@require_auth`` 装饰器剥离日志和认证逻辑：

```python
@server.tool()               # FastMCP 注册（最外层）
@log_tool("query_forms")     # 自动 trace_id、耗时计算、结构化日志
@require_auth(auth_middleware)  # Token 校验，注入 user_id（最内层）
async def query_forms(user_token: str, user_id: str = "", ...) -> dict:
    result = await form_service.query_forms(...)
    return result.to_dict()
```

**设计要点**：
- ``@server.tool()`` **必须放在最外层** — FastMCP 直接调用内部函数，外部装饰器不会触发
- ``@require_auth`` **最内层** — 最先执行，校验 Token 后注入 ``user_id``
- ``@log_tool`` **中间层** — 自动生成 trace_id、计算耗时、根据返回值的 ``success`` 字段输出结构化日志
- 异常会被 ``@log_tool`` 捕获并记录日志后重新抛出

**代码量缩减**：每个工具函数体从 ~20 行缩减至 3-8 行。

---

## 模块职责

### `attendance/` + `form/` — 业务领域包

每个业务领域包内按职责拆分文件：

| 文件 | 职责 | 依赖 |
|------|------|------|
| `models.py` | Pydantic 数据模型 | 无 |
| `service.py` | 纯业务逻辑（不依赖 FastMCP） | `api.py` |
| `query.py` | 查询类 MCP 工具（@log_tool + @require_auth） | `service.py`, `AuthMiddleware` |
| `submit.py` | 操作类 MCP 工具（@log_tool + @require_auth） | `service.py`, `AuthMiddleware` |
| `api.py` | HTTP API 适配器（继承 BaseHttpClient） | `core/http_client.py`, `models/vo.py` |

**考勤领域工具**：clock_in, clock_out, leave_apply, query_attendance, query_leave_records  
**表单领域工具**：query_forms, submit_form, prefill_form

### `core/` — 基础设施层

- `http_client.py` — `BaseHttpClient` 基类，统一超时/重试/错误处理/响应解析
- `logging_helper.py` — `ToolLogger` 上下文管理器（向后兼容，新代码推荐用装饰器）
- `tool_decorators.py` — `@log_tool` 和 `@require_auth` 装饰器

### `models/` — 通用 VO 实体

- `vo.py` — `ApiResponse`, `ListResponse`, `ListData` 等跨领域通用响应实体

### `tools/` — Demo 工具集

- `demo.py` — 8 个基础示例工具（hello, fetch_url, add, calculate, random_number, current_time, echo, count_words）

---

## 模块间调用关系

```
main.py:create_server()
  │
  ├── tools/demo.py:register_tools(server)
  │     └── 直接返回，不依赖 service/adapter
  │
  ├── form/query.py:register_tools(server, form_service, auth_middleware)
  │     └── form_service.query_forms()
  │           └── FormApiAdapter.query_forms()  ← BaseHttpClient._do_request()
  │
  ├── form/submit.py:register_tools(server, form_service, auth_middleware)
  │     └── form_service.submit_form() / form_service.prefill_form()
  │           └── FormApiAdapter.submit_form() / .prefill_form()
  │
  ├── attendance/query.py:register_tools(server, attendance_service, auth_middleware)
  │     └── attendance_service.query_records() / .query_leave()
  │           └── AttendanceApiAdapter.query_records() / .query_leave()
  │
  └── attendance/submit.py:register_tools(server, attendance_service, auth_middleware)
        └── attendance_service.clock_in() / .clock_out() / .leave_apply()
              └── AttendanceApiAdapter.clock_in() / .clock_out() / .leave_apply()
```

### 认证装饰器调用链

```
@require_auth(auth_middleware)
  → auth_middleware.verify_token(user_token)  ← 前置校验
  → 注入 user_id 到 kwargs
  → 调用原函数
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
├── src/python_mcp_demo/            # 源码包
│   ├── __init__.py                 # 导出 create_server
│   ├── __main__.py                 # CLI 入口
│   ├── main.py                     # FastAPI + FastMCP 入口（装配根，全部工具）
│   ├── config.py                   # 多环境配置（MCP_ENV）
│   ├── auth.py                     # Token 前置校验中间件
│   ├── exceptions.py               # 自定义异常
│   ├── logging_.py                 # loguru 结构化日志
│   ├── urls.py                     # API URL 集中管理
│   ├── attendance/                 # 考勤业务领域
│   │   ├── __init__.py
│   │   ├── models.py               # 考勤数据模型
│   │   ├── service.py              # 考勤业务逻辑
│   │   ├── query.py                # 考勤查询工具
│   │   ├── submit.py               # 考勤操作工具
│   │   └── api.py                  # 考勤 HTTP API 适配器
│   ├── form/                       # 表单业务领域
│   │   ├── __init__.py
│   │   ├── models.py               # 表单数据模型
│   │   ├── service.py              # 表单业务逻辑
│   │   ├── query.py                # 表单查询工具
│   │   ├── submit.py               # 表单提交工具
│   │   └── api.py                  # 表单 HTTP API 适配器
│   ├── core/                       # 跨域基础设施
│   │   ├── http_client.py          # BaseHttpClient 基类
│   │   ├── logging_helper.py       # ToolLogger 上下文管理器
│   │   └── tool_decorators.py      # @log_tool + @require_auth
│   ├── models/                     # 通用 VO 实体
│   │   └── vo.py                   # ApiResponse, ListResponse, ListData
│   └── tools/                      # Demo 工具集
│       └── demo.py                 # 8 个基础 demo 工具
├── tests/
│   └── test_demo.py                # Demo 工具 pytest 测试
├── docs/
│   ├── api.md                      # API 接口文档
│   ├── architecture.md             # 本文档
│   ├── deployment.md               # 部署配置指南（含多环境 .env）
│   └── attendance-module-guide.md  # 考勤模块使用指南
├── .env.example                    # 环境变量模板
├── .env.dev / .env.test / .env.prod  # 多环境配置文件
├── pyproject.toml                  # 项目元数据与构建配置
└── README.md                       # 项目总览与快速开始
```

---

## URL 集中管理

所有后端 API 路径集中定义在 `urls.py` 的 `APIUrls` 类中：

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

详见 [部署配置指南](deployment.md)。支持通过 `MCP_ENV` 切换多环境 .env 文件：

```bash
MCP_ENV=dev   # → .env.dev（DEBUG 日志，localhost 后端）
MCP_ENV=test  # → .env.test（JSON 日志，测试后端）
MCP_ENV=prod  # → .env.prod（JSON 日志，生产后端）
```

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

### ADR-004：业务领域分包 + 装饰器驱动

v0.4.1 将原有 5 层分层架构（models/services/tools/adapters/core）重构为：
- **按业务领域分包** — 每个领域包（attendance/form）自包含全部层级
- **装饰器剥离横切关注点** — `@log_tool` 处理日志、`@require_auth` 处理认证，工具函数体缩减至 3-8 行
- **core/ 保留跨域基础设施** — http_client、tool_decorators 等跨领域复用

### ADR-005：多环境 .env 文件

v0.4.1 引入 `MCP_ENV` 环境变量，根据环境加载对应的 `.env.{env}` 文件。K8s 部署只需设置 `MCP_ENV=prod`。
