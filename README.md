# python-mcp-demo

基于 [FastMCP](https://github.com/jlowin/fastmcp) 构建的生产级 MCP（Model Context Protocol）服务器库。

[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](https://opensource.org/licenses/MIT)

## 功能特性

- **8 个内置工具** — hello, fetch_url, add, calculate, random_number, current_time, echo, count_words
- **安全表达式求值** — 基于 AST 的 `calculate` 工具（不使用 `eval()`）
- **异步优先** — 基于 `httpx` 实现快速 HTTP 请求
- **类型安全** — 完整的类型注解
- **结构化日志** — 通过环境变量可配置
- **自定义异常** — 分层的异常体系，支持健壮的错误处理
- **环境配置** — 支持 `.env` 文件加载运行时设置

## 安装

```bash
pip install python-mcp-demo
```

或使用 uv：

```bash
uv add python-mcp-demo
```

## 快速开始

### 启动服务器

```bash
python -m python_mcp_demo
```

### 使用 MCP 客户端

```python
from python_mcp_demo import create_server

server = create_server("my-server")

# 调用 hello
result = await server.call_tool("hello", {"name": "FastMCP"})
print(result)  # Hello, FastMCP! Welcome to MCP.

# 计算表达式
result = await server.call_tool("calculate", {"expression": "sqrt(16) * pi"})
print(result)  # 12.566370614359172
```

## 可用工具

### hello — 问候

```python
await server.call_tool("hello", {"name": "World"})
# → "Hello, World! Welcome to MCP."
```

### fetch_url — 抓取 URL

```python
await server.call_tool("fetch_url", {"url": "https://example.com"})
# → {"status": 200, "content_preview": "...", "content_length": 1256}
```

### add — 加法

```python
await server.call_tool("add", {"a": 3, "b": 4})
# → 7.0
```

### calculate — 安全数学计算

```python
await server.call_tool("calculate", {"expression": "2 + 3 * 4"})
# → 14.0

await server.call_tool("calculate", {"expression": "sqrt(144) + sin(pi/2)"})
# → 13.0
```

支持：`+`, `-`, `*`, `/`, `**`, `%`, `//`, `()`, `sqrt`, `sin`, `cos`, `log`, `floor`, `ceil`, `abs`, `round`, `pi`, `e` 等。

### random_number — 随机数

```python
await server.call_tool("random_number", {"min": 0.0, "max": 10.0})
# → 5.3421...
```

### current_time — 当前时间

```python
await server.call_tool("current_time", {"timezone": "Asia/Shanghai"})
# → "2026-07-04 13:00:00"
```

### echo — 回显

```python
await server.call_tool("echo", {"message": "你好", "times": 3})
# → ["你好", "你好", "你好"]
```

### count_words — 文本统计

```python
await server.call_tool("count_words", {"text": "hello world hello"})
# → {"char_count": 17, "word_count": 3, "line_count": 1, "top_words": {"hello": 2, "world": 1}}
```

## 配置

通过环境变量配置（参见 `.env.example`）：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `MCP_SERVER_NAME` | `python-mcp-demo` | MCP 服务器名称 |
| `MCP_LOG_LEVEL` | `INFO` | 日志级别 |
| `MCP_REQUEST_TIMEOUT` | `30` | HTTP 请求超时（秒） |
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

## 许可证

MIT
