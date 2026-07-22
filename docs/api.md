# API 接口文档

本文档定义 `python-mcp-demo` 所有 MCP 工具的接口规范，包括输入参数、输出格式和错误码。

**工具总数：15 个**

| 类别 | 工具 | 来源文件 |
|------|------|---------|
| Demo | 8 个 | `tools/demo.py` |
| 表单 | 3 个 | `tools/form_query.py`, `tools/form_submit.py` |
| 考勤 | 5 个 | `tools/attendance_query.py`, `tools/attendance_submit.py` |

---

## Demo 工具（tools/demo.py）

8 个基础示例工具，开箱即用。

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

| 异常 | 触发条件 | 错误消息 |
|------|----------|----------|
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

| 异常 | 触发条件 | 错误消息示例 |
|------|----------|-------------|
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

| 异常 | 触发条件 | 错误消息 |
|------|----------|----------|
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

| 异常 | 触发条件 | 错误消息 |
|------|----------|----------|
| `MCPToolError` | 时区不可识别 | `未知时区: {name}。请使用有效的 IANA 时区，例如 'Asia/Shanghai'。` |

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

| 异常 | 触发条件 | 错误消息 |
|------|----------|----------|
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

## 表单工具（tools/form_query.py + tools/form_submit.py）

### 9. query_forms — 表单查询

| 项目 | 说明 |
|------|------|
| **工具名** | `query_forms` |
| **功能** | 查询表单数据（请假申请、报销单等），经 Token 校验 → 后端 HTTP API |
| **MCP 调用** | `server.call_tool("query_forms", {...})` |
| **来源** | `tools/form_query.py` |

**输入参数：**

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `user_token` | `str` | 是 | — | 用户 JWT Token（从 Dify session variable 透传） |
| `form_type` | `str` | 否 | `""` | 表单类型名称（如 "请假申请"） |
| `date_from` | `str` | 否 | `""` | 时间范围起（YYYY-MM-DD） |
| `date_to` | `str` | 否 | `""` | 时间范围止（YYYY-MM-DD） |
| `status` | `str` | 否 | `""` | 表单状态（如 "已审批"、"待审批"） |
| `limit` | `int` | 否 | `10` | 返回条数上限（最大 100） |

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

### 10. submit_form — 表单提交

| 项目 | 说明 |
|------|------|
| **工具名** | `submit_form` |
| **功能** | 提交表单数据（如请假申请、报销单等） |
| **MCP 调用** | `server.call_tool("submit_form", {...})` |
| **来源** | `tools/form_submit.py` |

**输入参数：**

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `user_token` | `str` | 是 | — | 用户 JWT Token |
| `form_type` | `str` | 是 | — | 表单类型名称（如 "请假申请"） |
| `form_data` | `dict` | 是 | — | 表单字段数据（JSON 对象） |

**输出格式：**

```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```

**错误场景：** 与 query_forms 相同的认证/网络错误场景。

---

### 11. prefill_form — 表单预填

| 项目 | 说明 |
|------|------|
| **工具名** | `prefill_form` |
| **功能** | 获取表单预填数据（根据模板自动填充表单字段） |
| **MCP 调用** | `server.call_tool("prefill_form", {...})` |
| **来源** | `tools/form_submit.py` |

**输入参数：**

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `user_token` | `str` | 是 | — | 用户 JWT Token |
| `form_type` | `str` | 是 | — | 表单类型名称（如 "请假申请"） |
| `template_id` | `str` | 否 | `""` | 模板标识 |

**输出格式：**

```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```

---

## 考勤工具（tools/attendance_query.py + tools/attendance_submit.py）

### 12. clock_in — 上班签到

| 项目 | 说明 |
|------|------|
| **工具名** | `clock_in` |
| **功能** | 记录当前时间作为上班打卡时间 |
| **MCP 调用** | `server.call_tool("clock_in", {"user_token": "..."})` |
| **来源** | `tools/attendance_submit.py` |

**输入参数：**

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `user_token` | `str` | 是 | — | 用户 JWT Token |

**输出格式：**

```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```

---

### 13. clock_out — 下班签退

| 项目 | 说明 |
|------|------|
| **工具名** | `clock_out` |
| **功能** | 记录当前时间作为下班打卡时间 |
| **MCP 调用** | `server.call_tool("clock_out", {"user_token": "..."})` |
| **来源** | `tools/attendance_submit.py` |

**输入参数：**

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `user_token` | `str` | 是 | — | 用户 JWT Token |

**输出格式：**

```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```

---

### 14. leave_apply — 请假申请

| 项目 | 说明 |
|------|------|
| **工具名** | `leave_apply` |
| **功能** | 提交请假申请 |
| **MCP 调用** | `server.call_tool("leave_apply", {...})` |
| **来源** | `tools/attendance_submit.py` |

**输入参数：**

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `user_token` | `str` | 是 | — | 用户 JWT Token |
| `leave_type` | `str` | 是 | — | 请假类型（年假/事假/病假/婚假/产假） |
| `date_from` | `str` | 是 | — | 开始日期（YYYY-MM-DD） |
| `date_to` | `str` | 是 | — | 结束日期（YYYY-MM-DD） |
| `reason` | `str` | 是 | — | 请假原因 |

**输出格式：**

```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```

**参数校验错误：**

| 场景 | `success` | `error` 消息 |
|------|-----------|-------------|
| leave_type 为空 | `false` | `请假类型不能为空` |
| date_from 为空 | `false` | `开始日期不能为空` |
| date_to 为空 | `false` | `结束日期不能为空` |
| reason 为空 | `false` | `请假原因不能为空` |

---

### 15. query_attendance — 考勤记录查询

| 项目 | 说明 |
|------|------|
| **工具名** | `query_attendance` |
| **功能** | 查询考勤记录（签到时间、签退时间、考勤状态等） |
| **MCP 调用** | `server.call_tool("query_attendance", {...})` |
| **来源** | `tools/attendance_query.py` |

**输入参数：**

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `user_token` | `str` | 是 | — | 用户 JWT Token |
| `date_from` | `str` | 否 | `""` | 时间范围起（YYYY-MM-DD） |
| `date_to` | `str` | 否 | `""` | 时间范围止（YYYY-MM-DD） |
| `status` | `str` | 否 | `""` | 考勤状态（如 "正常"、"迟到"、"早退"） |
| `limit` | `int` | 否 | `10` | 返回条数上限（最大 100） |

**成功输出格式：**

```json
{
  "success": true,
  "data": {
    "total": 10,
    "returned": 10,
    "items": [ ... ]
  },
  "error": null
}
```

---

### 16. query_leave_records — 请假记录查询

| 项目 | 说明 |
|------|------|
| **工具名** | `query_leave_records` |
| **功能** | 查询历史请假申请及审批状态 |
| **MCP 调用** | `server.call_tool("query_leave_records", {...})` |
| **来源** | `tools/attendance_query.py` |

**输入参数：**

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `user_token` | `str` | 是 | — | 用户 JWT Token |
| `date_from` | `str` | 否 | `""` | 时间范围起（YYYY-MM-DD） |
| `date_to` | `str` | 否 | `""` | 时间范围止（YYYY-MM-DD） |
| `status` | `str` | 否 | `""` | 请假状态（如 "已审批"、"待审批"、"已驳回"） |
| `limit` | `int` | 否 | `10` | 返回条数上限（最大 100） |

**成功输出格式：**

```json
{
  "success": true,
  "data": {
    "total": 5,
    "returned": 5,
    "items": [ ... ]
  },
  "error": null
}
```

---

## 错误码汇总

### Demo 层异常（抛异常模式）

| 异常类 | 父类 | 说明 |
|--------|------|------|
| `MCPToolError` | `Exception` | 可恢复的工具执行错误 |
| `MathExpressionError` | `MCPToolError` | 不合法或不安全的数学表达式 |

FastMCP 框架会将这些异常包装为 `ToolError` 返回给调用方。

### 业务层错误码（返回格式模式）

业务工具**不抛出异常**，而是通过 `{success, error}` 字段返回错误信息：

| 错误场景 | 错误消息 |
|----------|----------|
| Token 为空 | `缺少用户认证信息，请重新登录后重试` |
| Token 过期 | `登录已过期，请刷新页面后重试` |
| 权限不足 | `权限不足，无法执行此操作` |
| 认证服务超时/不可达 | `认证服务暂时不可用，请稍后重试` |
| 查询/提交超时 | `{操作}超时，请稍后重试` |
| 后端不可达 | `{服务}暂时不可用，请稍后重试` |
| 后端 4xx | `请求参数错误 ({status})` |
| 后端 5xx（重试后） | `后端服务异常，请稍后重试 ({status})` |
| 响应格式异常 | `后端返回数据格式异常` |
| 请假参数为空 | `{字段名}不能为空` |

---

## MCP 服务器启动与连接

### 启动方式

#### 开发模式（stdio 传输）

```bash
python -m python_mcp_demo
```

#### FastAPI + SSE 模式

```bash
python -m python_mcp_demo
# 默认监听 0.0.0.0:8000，/obot/mcp/sse 端点
```

### 连接方式

#### MCP 客户端（Python SDK）

```python
from python_mcp_demo import create_server

server = create_server()
result = await server.call_tool("hello", {"name": "World"})
```

#### 标准 MCP 客户端（JSON-RPC）

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

#### MCP 客户端配置（Claude Desktop / Dify）

```json
{
  "mcpServers": {
    "python-mcp-demo": {
      "url": "http://<host>:8000/obot/mcp/sse"
    }
  }
}
```
