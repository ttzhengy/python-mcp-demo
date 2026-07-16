# API 接口文档

## 工具接口定义

本文档定义 `python-mcp-demo` 所有 MCP 工具的接口规范，包括输入参数、输出格式和错误码。

---

## Demo 层工具（server.py）

8 个内置示例工具，基于 FastMCP 框架实现。

### 1. hello — 问候

| 项目 | 说明 |
|------|------|
| **工具名** | `hello` |
| **功能** | 向指定名称返回问候消息 |
| **MCP 调用** | `server.call_tool("hello", {"name": "World"})` |

**输入参数：**

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `name` | `str` | 否 | `"World"` | 要问候的名称 |

**输出格式：**

```text
Hello, {name}! Welcome to MCP.
```

**错误：** 无特定错误。

---

### 2. fetch_url — URL 抓取

| 项目 | 说明 |
|------|------|
| **工具名** | `fetch_url` |
| **功能** | 发起 HTTP GET 请求，返回状态码、内容预览及长度 |
| **MCP 调用** | `server.call_tool("fetch_url", {"url": "https://example.com"})` |

**输入参数：**

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `url` | `str` | 是 | — | 以 `http://` 或 `https://` 开头的 URL |

**输出格式：**

```json
{
  "status": 200,
  "content_preview": "...",
  "content_length": 1256
}
```

**错误码：**

| 错误码 | 触发条件 | 错误消息 |
|--------|----------|----------|
| `MCPToolError` | URL 不以 http/https 开头 | `无效的 URL: 必须以 http:// 或 https:// 开头` |
| `MCPToolError` | HTTP 4xx/5xx | `HTTP {status}: {reason}` |
| `MCPToolError` | 网络不可达 | `请求失败: {details}` |

---

### 3. add — 加法

| 项目 | 说明 |
|------|------|
| **工具名** | `add` |
| **功能** | 返回两个数的算术和 |
| **MCP 调用** | `server.call_tool("add", {"a": 3, "b": 4})` |

**输入参数：**

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `a` | `float` | 是 | — | 第一个加数 |
| `b` | `float` | 是 | — | 第二个加数 |

**输出：** `float` — 两数之和。

**错误：** 无特定错误。

---

### 4. calculate — 安全数学计算

| 项目 | 说明 |
|------|------|
| **工具名** | `calculate` |
| **功能** | 安全计算数学表达式（AST 解析，非 `eval()`） |
| **MCP 调用** | `server.call_tool("calculate", {"expression": "2 + 3 * 4"})` |

**输入参数：**

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `expression` | `str` | 是 | — | 数学表达式字符串 |

**支持运算符/函数：**

| 类别 | 内容 |
|------|------|
| 算术运算符 | `+`, `-`, `*`, `/`, `**`, `%`, `//`, `()`, 一元正负号 |
| 数学函数 | `sqrt`, `sin`, `cos`, `tan`, `log`, `log10`, `exp`, `abs`, `ceil`, `floor`, `round`, `degrees`, `radians`, `isinf`, `isnan` |
| 聚合函数 | `max`, `min` |
| 数学常量 | `pi`, `e`, `tau` |

**输出：** `float` — 计算结果。

**错误码：**

| 错误码 | 触发条件 | 错误消息示例 |
|--------|----------|-------------|
| `MathExpressionError` | 空表达式 | `表达式不能为空` |
| `MathExpressionError` | 语法错误 | `表达式语法错误: ...` |
| `MathExpressionError` | 不支持的函数 | `不支持的函数: invalid_func` |
| `MathExpressionError` | 除零 | `除零错误` |
| `MathExpressionError` | 结果为无穷/NaN | `结果为无穷或非数字 (NaN)` |

---

### 5. random_number — 随机数

| 项目 | 说明 |
|------|------|
| **工具名** | `random_number` |
| **功能** | 在 `[min, max]` 范围内生成均匀分布的随机浮点数 |
| **MCP 调用** | `server.call_tool("random_number", {"min": 0.0, "max": 10.0})` |

**输入参数：**

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `min` | `float` | 是 | — | 下限（包含） |
| `max` | `float` | 是 | — | 上限（包含） |

**输出：** `float` — 指定范围内的随机值。

**错误码：**

| 错误码 | 触发条件 | 错误消息 |
|--------|----------|----------|
| `MCPToolError` | `min > max` | `最小值 ({min}) 不能大于最大值 ({max})` |

---

### 6. current_time — 当前时间

| 项目 | 说明 |
|------|------|
| **工具名** | `current_time` |
| **功能** | 获取指定 IANA 时区的当前日期和时间 |
| **MCP 调用** | `server.call_tool("current_time", {"timezone": "Asia/Shanghai"})` |

**输入参数：**

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `timezone` | `str` | 否 | `"UTC"` | IANA 时区名（如 `"Asia/Shanghai"`、`"US/Eastern"`） |

**输出格式：**

```text
YYYY-MM-DD HH:MM:SS
```

**错误码：**

| 错误码 | 触发条件 | 错误消息 |
|--------|----------|----------|
| `MCPToolError` | 时区不可识别 | `未知时区: {name}` |

---

### 7. echo — 回显

| 项目 | 说明 |
|------|------|
| **工具名** | `echo` |
| **功能** | 将消息重复指定次数并返回列表 |
| **MCP 调用** | `server.call_tool("echo", {"message": "你好", "times": 3})` |

**输入参数：**

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `message` | `str` | 是 | — | 要回显的消息 |
| `times` | `int` | 否 | `1` | 重复次数（1~100） |

**输出：** `list[str]` — 包含消息重复 `times` 次的列表。

**错误码：**

| 错误码 | 触发条件 | 错误消息 |
|--------|----------|----------|
| `MCPToolError` | `times` 不在 1~100 范围 | `重复次数 ({times}) 必须在 1 到 100 之间` |

---

### 8. count_words — 文本统计

| 项目 | 说明 |
|------|------|
| **工具名** | `count_words` |
| **功能** | 分析文本的字符数、词数、行数及词频统计 |
| **MCP 调用** | `server.call_tool("count_words", {"text": "hello world hello"})` |

**输入参数：**

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `text` | `str` | 是 | — | 要分析的输入文本 |

**输出格式：**

```json
{
  "char_count": 17,
  "word_count": 3,
  "line_count": 1,
  "top_words": {
    "hello": 2,
    "world": 1
  }
}
```

> `top_words` 按频率降序返回前 10 个词，不区分大小写且去除标点。

**错误：** 无特定错误。空文本返回所有计数为 0。

---

## POC 层工具（main.py）

### query_forms — 表单查询

| 项目 | 说明 |
|------|------|
| **工具名** | `query_forms` |
| **功能** | 查询表单数据（请假申请、报销单等），端到端链路经 Token 校验 → 后端 HTTP API |
| **MCP 调用** | `server.call_tool("query_forms", {...})` |

**输入参数：**

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `user_token` | `str` | 是 | — | 用户 JWT Token（从 Dify session variable 透传） |
| `form_type` | `str` | 否 | `""` | 表单类型名称（如 "请假申请"） |
| `date_from` | `str` | 否 | `""` | 时间范围起（YYYY-MM-DD） |
| `date_to` | `str` | 否 | `""` | 时间范围止（YYYY-MM-DD） |
| `status` | `str` | 否 | `""` | 表单状态（如 "已审批"、"待审批"） |
| `limit` | `int` | 否 | `10` | 返回条数上限 |

**成功输出格式：**

```json
{
  "success": true,
  "data": {
    "total": 5,
    "returned": 5,
    "items": [
      {
        "form_id": "F-2026-001",
        "form_type": "请假申请",
        "applicant": "张三",
        "status": "已审批",
        "created_at": "2026-07-10",
        "summary": "年假 7月15日-7月17日 共3天",
        "detail_url": "https://portal.internal/forms/F-2026-001"
      }
    ]
  },
  "error": null
}
```

**失败输出格式：**

```json
{
  "success": false,
  "data": null,
  "error": "缺少用户认证信息，请重新登录后重试"
}
```

**错误码/场景：**

| 场景 | `success` | `error` 消息 |
|------|-----------|-------------|
| Token 为空 | `false` | `缺少用户认证信息，请重新登录后重试` |
| Token 已过期 | `false` | `登录已过期，请刷新页面后重试` |
| 权限不足 | `false` | `权限不足，无法执行此操作` |
| 后端认证超时 | `false` | `认证服务暂时不可用，请稍后重试` |
| 查询超时 | `false` | `查询超时，请稍后重试` |
| 后端不可达 | `false` | `后端服务暂时不可用，请稍后重试` |
| 后端 4xx/5xx | `false` | `后端服务异常，请稍后重试 ({status})` |
| 响应格式异常 | `false` | `后端返回数据格式异常` |

---

## MCP 服务器启动与连接

### 启动方式

#### Development 模式（stdio 传输）

```bash
python -m python_mcp_demo
```

通过 stdio 协议与本地 MCP 客户端通信。

#### Production 模式（SSE 传输）

```bash
python -m python_mcp_demo
# 默认监听 0.0.0.0:8000，通过 SSE 传输
```

或从代码启动：

```python
from python_mcp_demo import create_server

server = create_server("my-server")
server.run(transport="sse", host="0.0.0.0", port=8000)
```

### 连接方式

#### MCP 客户端（Python SDK）

```python
from python_mcp_demo import create_server

server = create_server()
result = await server.call_tool("hello", {"name": "World"})
```

#### 标准 MCP 客户端（任何语言）

通过 stdio 或 SSE 连接，发送 JSON-RPC 消息：

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "hello",
    "arguments": {"name": "World"}
  }
}
```

#### Claude Desktop / Dify 集成

在 MCP 客户端配置中添加 SSE 端点地址：

```json
{
  "mcpServers": {
    "python-mcp-demo": {
      "url": "http://<host>:8000/sse"
    }
  }
}
```

---

## 错误码汇总

### Demo 层异常

| 异常类 | 父类 | 说明 |
|--------|------|------|
| `MCPToolError` | `Exception` | 可恢复的工具执行错误 |
| `MathExpressionError` | `MCPToolError` | 不合法或不安全的数学表达式 |

FastMCP 框架会将这些异常包装为 `ToolError` 返回给调用方。

### POC 层错误码

POC 工具不抛出异常，而是通过 `{success, error}` 字段返回错误信息。
唯一输入校验异常是 Token 为空的场景，其余网络/业务错误均走正常返回路径。
