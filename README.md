# python-mcp-demo

基于 [FastMCP](https://github.com/jlowin/fastmcp) 构建的 AI 办公助手 MCP 服务器，采用 5 层模块化架构。

[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](https://opensource.org/licenses/MIT)

## 架构概览

```
tools/          FastMCP @server.tool() 定义（薄封装层）
services/      纯业务逻辑（不依赖 FastMCP）
adapters/      HTTP API 适配器（基于 BaseHttpClient）
core/          跨模块基础设施（http_client.py）
models/        Pydantic 数据模型
```

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
python -m python_mcp_demo
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

所有配置项通过环境变量或 `.env` 文件加载，以 `MCP_` 为前缀：

| 变量 | 默认值 | 说明 |
|------|--------|------|
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

# 启动服务器
uv run python -m python_mcp_demo
```

## 项目结构

```
src/python_mcp_demo/
├── __init__.py          # 导出 create_server, mcp, tools
├── __main__.py          # CLI 入口
├── server.py            # 向后兼容封装
├── main.py              # FastAPI + FastMCP 入口
├── config.py            # 配置管理
├── auth.py              # 认证中间件
├── exceptions.py        # 自定义异常
├── logging_.py          # loguru 结构化日志
├── urls.py              # API URL 集中管理
├── core/
│   └── http_client.py   # BaseHttpClient 基类
├── models/
│   ├── form.py          # 表单数据模型
│   └── attendance.py    # 考勤数据模型
├── services/
│   ├── form_service.py          # 表单业务逻辑
│   └── attendance_service.py    # 考勤业务逻辑
├── adapters/
│   ├── form_api.py       # 表单引擎 HTTP API
│   └── attendance_api.py # 考勤服务 HTTP API
└── tools/
    ├── demo.py                 # 8 个 demo 工具
    ├── form_query.py           # 表单查询工具
    ├── form_submit.py          # 表单提交工具
    ├── attendance_query.py     # 考勤查询工具
    └── attendance_submit.py    # 考勤操作工具
```

## 文档

- [架构说明](docs/architecture.md) — 5 层分层架构、模块职责、调用关系
- [API 文档](docs/api.md) — 所有工具的接口定义、参数、输出格式
- [考勤模块指南](docs/attendance-module-guide.md) — 考勤模块使用指南

## 许可证

MIT
