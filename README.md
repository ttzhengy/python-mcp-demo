# python-mcp-demo

基于 [FastMCP](https://github.com/jlowin/fastmcp) 构建的 AI 办公助手 MCP 服务器，采用按业务领域分包的模块化架构。

[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](https://opensource.org/licenses/MIT)

## 架构概览

```
attendance/     考勤业务领域（models/service/query/submit/api）
form/           表单业务领域（models/service/query/submit/api）
tools/          Demo 工具集（8 个基础 MCP 工具）
core/           跨模块基础设施（http_client, logging_helper, tool_decorators）
models/         通用 VO 实体（ApiResponse, ListResponse, ListData）
```

每个业务领域包内包含该领域的全部层级：数据模型 → 业务逻辑 → MCP 工具 → HTTP API 适配器。

工具函数使用 ``@log_tool`` 和 ``@require_auth`` 装饰器剥离日志和认证逻辑，每函数体缩减至 3-8 行。

## 业务模块

| 模块 | 工具 | 说明 |
|------|------|------|
| **Demo** | hello, fetch_url, add, calculate, random_number, current_time, echo, count_words | 基础示例工具 |
| **表单** | query_forms, submit_form, prefill_form | 表单查询/提交/预填 |
| **考勤** | clock_in, clock_out, leave_apply, query_attendance, query_leave_records | 考勤签到/签退/请假/查询 |

## 安装

```bash
# 使用 uv（推荐）
uv add python-mcp-demo

# 或使用 pip
pip install python-mcp-demo
```

## 快速启动

### 开发模式（stdio 传输）

```bash
# 默认加载 .env.dev 配置
python -m python_mcp_demo

# 指定环境
MCP_ENV=test python -m python_mcp_demo
```

### 生产模式（SSE 传输）

```python
from python_mcp_demo import create_server

server = create_server("my-server")
server.run(transport="sse", host="0.0.0.0", port=8000)
```

### FastAPI + SSE 模式

启动完整的 FastAPI 应用，在 `/obot` 上下文根上挂载 MCP SSE 端点：

```bash
uv run python -m python_mcp_demo
# → http://0.0.0.0:8000/obot/health
# → http://0.0.0.0:8000/obot/mcp/sse
```

### MCP 客户端（Python SDK）

```python
from python_mcp_demo import create_server

server = create_server()
result = await server.call_tool("hello", {"name": "FastMCP"})
print(result)  # Hello, FastMCP! Welcome to MCP.
```

## Demo 工具速览

| 工具 | 功能 | 示例 |
|------|------|------|
| `hello` | 问候 | `{"name": "World"}` → `"Hello, World! Welcome to MCP."` |
| `fetch_url` | 抓取 URL 内容 | `{"url": "https://example.com"}` → `{status, content_preview, content_length}` |
| `add` | 两数相加 | `{"a": 3, "b": 4}` → `7.0` |
| `calculate` | 安全数学表达式（AST 解析） | `{"expression": "sqrt(16) * pi"}` → `12.566...` |
| `random_number` | 随机浮点数 | `{"min": 0, "max": 10}` → `5.342...` |
| `current_time` | IANA 时区当前时间 | `{"timezone": "Asia/Shanghai"}` → `"2026-07-22 13:00:00"` |
| `echo` | 消息回显 | `{"message": "你好", "times": 3}` → `["你好", "你好", "你好"]` |
| `count_words` | 文本词频统计 | `{"text": "hello world hello"}` → `{char_count, word_count, line_count, top_words}` |

## 环境配置

### 多环境支持

通过 `MCP_ENV` 环境变量切换配置环境：

```bash
MCP_ENV=dev   # 开发环境 → 加载 .env.dev（DEBUG 日志，localhost 后端）
MCP_ENV=test  # 测试环境 → 加载 .env.test（JSON 日志，测试后端）
MCP_ENV=prod  # 生产环境 → 加载 .env.prod（JSON 日志，生产后端）
```

K8s 部署只需设置 `MCP_ENV=prod`，其余配置从 `.env.prod` 读取。

**优先级**：环境变量 > `.env.{MCP_ENV}` 文件 > 默认值

### 配置项一览

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `MCP_ENV` | `dev` | 环境标识（dev/test/prod） |
| `MCP_SERVER_NAME` | `ai-office-mcp` | FastMCP 服务器名称 |
| `MCP_HOST` | `0.0.0.0` | 监听地址 |
| `MCP_PORT` | `8000` | 监听端口 |
| `MCP_LOG_LEVEL` | `INFO` | 日志级别 |
| `MCP_LOG_JSON` | `true` | JSON 结构化日志开关 |
| `MCP_REQUEST_TIMEOUT` | `20` | HTTP 读超时（秒） |
| `MCP_CONNECT_TIMEOUT` | `5` | HTTP 连接超时（秒） |
| `MCP_MAX_RETRIES` | `3` | 5xx 错误最大重试次数 |
| `MCP_BACKEND_BASE_URL` | `http://localhost:8080` | Java 后端基础 URL |
| `MCP_BACKEND_AUTH_URL` | `http://localhost:8080/api/auth/verify` | 认证 API URL |
| `MCP_MAX_FETCH_SIZE` | `5000` | fetch_url 内容预览最大字节数 |

## 开发

```bash
# 安装依赖
uv sync

# 运行测试
uv run pytest -v

# 带覆盖率
uv run pytest -v --cov=python_mcp_demo --cov-report=term-missing

# 代码检查
uv run ruff check src/ tests/

# 启动服务器（开发模式）
MCP_ENV=dev uv run python -m python_mcp_demo
```

## 项目结构

```
src/python_mcp_demo/
├── __init__.py              # 导出 create_server, mcp
├── __main__.py              # CLI 入口
├── server.py                # 向后兼容封装
├── main.py                  # FastAPI + FastMCP 入口（装配根）
├── config.py                # 多环境配置（MCP_ENV）
├── auth.py                  # 认证中间件（TokenVerificationResult）
├── exceptions.py            # 自定义异常（MCPToolError, MathExpressionError）
├── logging_.py              # loguru 结构化日志（log_json）
├── urls.py                  # API URL 集中管理
├── attendance/              # 考勤业务领域
│   ├── __init__.py
│   ├── models.py            # 考勤数据模型（Pydantic）
│   ├── service.py           # 考勤业务逻辑（纯 Python）
│   ├── query.py             # 查询类 MCP 工具
│   ├── submit.py            # 操作类 MCP 工具
│   └── api.py               # 考勤 HTTP API 适配器
├── form/                    # 表单业务领域
│   ├── __init__.py
│   ├── models.py            # 表单数据模型（Pydantic）
│   ├── service.py           # 表单业务逻辑（纯 Python）
│   ├── query.py             # 查询类 MCP 工具
│   ├── submit.py            # 提交类 MCP 工具
│   └── api.py               # 表单引擎 HTTP API 适配器
├── core/                    # 跨域基础设施
│   ├── http_client.py       # BaseHttpClient 基类（超时/重试/错误处理）
│   ├── logging_helper.py    # ToolLogger 上下文管理器（向后兼容）
│   └── tool_decorators.py   # @log_tool + @require_auth 装饰器
├── models/                  # 通用 VO 实体
│   └── vo.py                # ApiResponse, ListResponse, ListData
└── tools/                   # Demo 工具集
    └── demo.py              # 8 个基础 demo 工具
```

## 文档

- [架构说明](docs/architecture.md) — 业务领域分包架构、模块职责、调用关系
- [API 文档](docs/api.md) — 所有工具的接口定义、参数、输出格式
- [考勤模块指南](docs/attendance-module-guide.md) — 考勤模块使用指南
- [部署配置指南](docs/deployment.md) — K8s 部署、多环境配置、日志说明

## 许可证

MIT
