# 部署配置指南

## 多环境 .env 文件机制（v0.4.1+）

通过 `MCP_ENV` 环境变量切换配置环境，无需在 K8s YAML 中逐项配置：

```bash
MCP_ENV=dev   # 开发环境 → 加载 .env.dev
MCP_ENV=test  # 测试环境 → 加载 .env.test
MCP_ENV=prod  # 生产环境 → 加载 .env.prod
```

**配置优先级**：环境变量 > `.env.{MCP_ENV}` 文件 > 默认值

K8s 部署时只需设置一个环境变量 `MCP_ENV=prod`，其余配置从 `.env.prod` 读取。

### 各环境差异

| 配置项 | dev | test | prod |
|--------|-----|------|------|
| 日志级别 | DEBUG | INFO | WARN |
| 日志格式 | 人类可读 | JSON | JSON |
| 后端 URL | localhost:8080 | test-backend:8080 | prod-backend:8080 |
| 请求超时 | 20s | 20s | 30s |
| 连接超时 | 5s | 5s | 10s |

### 环境文件示例

**`.env.dev`** — 开发配置（DEBUG 日志，localhost 后端，人类可读日志）
```ini
MCP_ENV=dev
MCP_LOG_LEVEL=DEBUG
MCP_LOG_JSON=false
MCP_BACKEND_BASE_URL=http://localhost:8080
```

**`.env.test`** — 测试配置（INFO 日志，测试后端，JSON 日志）
```ini
MCP_ENV=test
MCP_LOG_LEVEL=INFO
MCP_LOG_JSON=true
MCP_BACKEND_BASE_URL=http://test-backend:8080
```

**`.env.prod`** — 生产配置（WARN 日志，生产后端，严格超时）
```ini
MCP_ENV=prod
MCP_LOG_LEVEL=WARN
MCP_LOG_JSON=true
MCP_BACKEND_BASE_URL=http://prod-backend:8080
MCP_REQUEST_TIMEOUT=30
MCP_CONNECT_TIMEOUT=10
```

---

## 环境变量配置（MCP_ 前缀）

所有配置项通过以 `MCP_` 为前缀的环境变量注入。

### 部署环境字段（通过 K8s Deployment env: 注入）

| 环境变量 | 默认值 | 说明 |
|---|---|---|
| `MCP_ENV` | `dev` | 环境标识，加载对应 .env 文件 |
| `MCP_BACKEND_BASE_URL` | `http://localhost:8080` | 后端 API 基础地址（各环境不同） |
| `MCP_BACKEND_AUTH_URL` | `http://localhost:8080/api/auth/verify` | 认证服务 URL |
| `MCP_HOST` | `0.0.0.0` | 监听地址 |
| `MCP_PORT` | `8000` | 监听端口 |
| `MCP_LOG_LEVEL` | `INFO` | 日志级别 |
| `MCP_LOG_JSON` | `true` | 是否 JSON 结构化日志 |

### 运行策略字段（极少变更，代码内定）

| 环境变量 | 默认值 | 说明 |
|---|---|---|
| `MCP_REQUEST_TIMEOUT` | `20` | HTTP 请求读超时（秒） |
| `MCP_CONNECT_TIMEOUT` | `5` | HTTP 连接超时（秒） |
| `MCP_MAX_RETRIES` | `3` | 5xx 最大重试次数 |
| `MCP_RETRY_MIN_DELAY` | `1.0` | 重试最小间隔（秒） |
| `MCP_RETRY_MAX_DELAY` | `8.0` | 重试最大间隔（秒） |
| `MCP_TOKEN_MASK_PREFIX_LEN` | `8` | Token 脱敏保留前缀长度 |

---

## K8s Deployment YAML 参考

使用多环境 .env 机制后，Deployment 只需设置 `MCP_ENV`：

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-office-mcp
spec:
  replicas: 2
  selector:
    matchLabels:
      app: ai-office-mcp
  template:
    metadata:
      labels:
        app: ai-office-mcp
    spec:
      containers:
        - name: mcp-server
          image: registry.example.com/ai-office-mcp:latest
          ports:
            - containerPort: 8000
          env:
            # 只需设置环境标识，其余配置从 .env.prod 读取
            - name: MCP_ENV
              value: "prod"
            # 可选覆盖：环境变量优先级高于 .env.prod
            - name: MCP_LOG_LEVEL
              value: "INFO"
          livenessProbe:
            httpGet:
              path: /obot/health
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 30
          resources:
            requests:
              cpu: "200m"
              memory: "256Mi"
            limits:
              cpu: "500m"
              memory: "512Mi"
```

### 覆盖特定配置

如需在 K8s 中覆盖 .env.prod 中的某项配置（如使用不同的后端 URL），只需在 env: 中添加对应环境变量：

```yaml
env:
  - name: MCP_ENV
    value: "prod"
  - name: MCP_BACKEND_BASE_URL
    value: "http://custom-backend:8080"  # 覆盖 .env.prod 中的值
```

---

## JSON 日志 vs 人类可读日志

| 场景 | `MCP_LOG_JSON` | 说明 |
|---|---|---|
| **K8s 生产/测试** | `true` | JSON 行输出到 stdout，由容器运行时（如 fluentd、Filebeat）采集到 ELK/Loki |
| **本地开发** | `false` | 彩色人类可读格式，每行包含时间、级别、trace_id 和消息，方便终端查看 |

### JSON 日志示例（log_json=true）

```json
{"timestamp":"2026-07-23T10:30:00.123Z","level":"INFO","trace_id":"a1b2c3d4e5f6","tool_name":"query_forms","duration_ms":150,"status":"success","user_token":"a1b2c3d4*","user_id":"u_12345","returned":5,"message":"Tool query_forms success in 150ms"}
```

### 人类可读日志示例（log_json=false）

```
2026-07-23 10:30:00 | INFO    | a1b2c3d4e5f6 | Tool query_forms success in 150ms
```

---

## 注意事项

1. **敏感信息**：`.env.*` 文件中的 `MCP_BACKEND_AUTH_URL` 不应包含凭据，认证通过 JWT Token 传递
2. **日志安全**：`log_json=true` 时，`user_token` 字段自动脱敏（仅保留前 N 字符）
3. **资源规划**：建议每个 Pod 分配 256Mi~512Mi 内存，cpu 200m~500m
4. **健康检查**：使用 `/obot/health` 端点（返回 `{"status": "healthy"}`）
5. **扩缩容**：服务无状态，可水平扩展，建议 HPA 基于 CPU 使用率自动扩缩
6. **环境隔离**：各环境的 .env 文件已提交到 Git，敏感凭证应通过 K8s Secrets 注入
