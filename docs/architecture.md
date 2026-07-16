# 架构说明文档

## 项目概述

`python-mcp-demo` 是一个基于 [FastMCP](https://github.com/jlowin/fastmcp) 构建的生产级 MCP（Model Context Protocol）服务器库。

项目分为两个功能层次：

| 层次 | 目录 | 说明 |
|------|------|------|
| **Demo 层** | `server.py` | 8 个内置示例工具，开箱即用，适合学习 MCP 协议 |
| **POC 层** | `main.py` + 业务模块 | AI 办公助手 POC，连接 Dify 工作流与 Java 后端 |

---

## 项目结构

```
python-mcp-demo/
├── src/python_mcp_demo/        # 源码包
│   ├── __init__.py              # 包入口，导出 create_server / mcp
│   ├── __main__.py              # CLI 入口: python -m python_mcp_demo
│   ├── server.py                # 8 个内置 demo 工具（hello / fetch_url / add / calculate / ...）
│   ├── main.py                  # POC 主入口（query_forms 工具）
│   ├── config.py                # 配置管理（pydantic-settings, MCP_ 前缀）
│   ├── auth.py                  # Token 前置校验中间件
│   ├── form_engine.py           # 表单引擎 HTTP API 适配器
│   ├── logging_.py              # loguru 结构化日志
│   └── exceptions.py            # 自定义异常体系
├── tests/
│   ├── test_demo.py             # 8 个 demo 工具的 pytest 测试
│   └── ...                      # POC 相关测试
├── test_poc.py                  # POC 验证脚本（7 项验收清单）
├── docs/                        # 文档目录
│   ├── api.md                   # API 接口文档
│   └── architecture.md          # 本文档
├── Makefile                     # 常用开发命令
├── pyproject.toml               # 项目元数据与构建配置
├── .env.example                 # 环境变量配置模板
└── README.md                    # 项目总览与快速开始
```

---

## 模块职责

### 1. `server.py` — Demo 服务器（8 个内置工具）

提供基于 FastMCP 的参考实现。包含以下独立工具：

- **hello** — 问候
- **fetch_url** — URL 内容抓取
- **add** — 算术加法
- **calculate** — 安全数学表达式求值（AST 解析，非 `eval()`）
- **random_number** — 随机数生成
- **current_time** — 当前时间（IANA 时区）
- **echo** — 消息回显
- **count_words** — 文本统计分析

核心安全设计：`calculate` 工具使用 AST 解析替代 `eval()`，白名单模式只允许预设运算符和函数。

### 2. `main.py` — POC 服务器入口

AI 办公助手 POC 的服务器入口，暴露 `query_forms` MCP Tool。

目标链路：

```
Dify Agent → MCP 协议 (SSE) → FastMCP → HTTP API → Java 后端
```

### 3. `config.py` — 配置管理

基于 `pydantic-settings`，所有配置项以 `MCP_` 为环境变量前缀。

配置优先级：环境变量 > `.env` 文件 > 默认值

### 4. `auth.py` — Token 认证中间件

- 在前置阶段调用后端认证 API 验证 JWT Token 有效性
- 支持开发模式跳过校验（`auth_url` 为空时自动放行）
- 使用 `AuthMiddleware` 类封装

### 5. `form_engine.py` — 表单引擎适配器

- 封装对 Java 后端的 HTTP 调用
- 支持指数退避重试（tenacity，仅 5xx 错误）
- 统一响应格式 `{success, data, error}`

### 6. `logging_.py` — 结构化日志

- 基于 loguru 实现 JSON 结构化日志输出
- 自动脱敏用户 Token（保留前 N 字符）
- 统一日志字段格式：`timestamp, level, trace_id, tool_name, duration_ms, status`

### 7. `exceptions.py` — 异常体系

```
Exception
└── MCPToolError          # 可恢复的工具执行错误
    └── MathExpressionError  # 不合法或不安全的数学表达式
```

---

## 扩展方式：如何添加新工具

### 在 Demo 层添加工具

编辑 `server.py`，在 `create_server()` 函数内使用 `@server.tool()` 装饰器：

```python
@server.tool()
async def my_tool(param1: str, param2: int = 0) -> str:
    \"\"\"工具功能描述。

    Args:
        param1: 参数说明。
        param2: 参数说明，含默认值。

    Returns:
        返回结果描述。

    Raises:
        MCPToolError: 出错时抛出。
    \"\"\"
    # 业务逻辑
    return "result"
```

约束：
- 使用类型注解标注输入参数类型
- 写完整的 Google-style docstring
- 自定义异常继承 `MCPToolError`

### 在 POC 层添加工具

编辑 `main.py`，在 `create_server()` 函数内添加：

```python
@server.tool()
async def my_business_tool(
    user_token: str,
    # ... 业务参数
) -> dict:
    \"\"\"...\"\"\"
    trace_id = uuid.uuid4().hex[:12]
    tool_name = "my_business_tool"
    start_time = time.time()

    # 1. 参数校验
    if not user_token:
        return error_response("缺少用户认证信息")

    # 2. Token 前置校验
    verify_result = await auth_middleware.verify_token(user_token)
    if not verify_result.valid:
        return error_response(verify_result.error)

    # 3. 业务逻辑（调用后端 API）
    result = await ...  # 业务调用

    # 4. 审计日志
    log_json("INFO", trace_id, tool_name, elapsed, "success", ...)

    return result
```

### 添加后端 API 适配器

创建新的适配器模块，参考 `form_engine.py` 的模式：
- 继承统一的超时/重试机制
- 使用 `_build_headers()` 添加审计 Header
- 返回统一格式 `{success, data, error}`

---

## 配置说明

所有配置项通过环境变量或 `.env` 文件设置，以 `MCP_` 为前缀。

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `MCP_SERVER_NAME` | `ai-office-mcp` | FastMCP 服务器名称 |
| `MCP_HOST` | `0.0.0.0` | 监听地址 |
| `MCP_PORT` | `8000` | 监听端口 |
| `MCP_LOG_LEVEL` | `INFO` | 日志级别 |
| `MCP_LOG_JSON` | `true` | JSON 结构化日志开关 |
| `MCP_REQUEST_TIMEOUT` | `20` | HTTP 读超时（秒） |
| `MCP_CONNECT_TIMEOUT` | `5` | HTTP 连接超时（秒） |
| `MCP_MAX_RETRIES` | `3` | 5xx 错误最大重试次数 |
| `MCP_RETRY_MIN_DELAY` | `1.0` | 重试初始间隔（秒） |
| `MCP_RETRY_MAX_DELAY` | `8.0` | 重试最大间隔（秒） |
| `MCP_BACKEND_BASE_URL` | `http://localhost:8080` | Java 后端基础 URL |
| `MCP_BACKEND_AUTH_URL` | `http://localhost:8080/api/auth/verify` | 认证 API URL |
| `MCP_TOKEN_MASK_PREFIX_LEN` | `8` | Token 脱敏保留前缀长度 |
| `MCP_MAX_FETCH_SIZE` | `5000` | fetch_url 内容预览最大字节数 |

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
- Cookie 不进入 Dify/LLM 环境
- HTTP Header 添加 `X-AI-Agent: dify-workflow/v1` 审计标记

### ADR-003：存量零改造

Java 后端不做任何变更，MCP 层以标准 HTTP 客户端身份调用后端 API。

---
