# 部署配置指南

## 环境变量配置（MCP_ 前缀）

所有配置项通过以 `MCP_` 为前缀的环境变量注入，优先级：环境变量 > `.env` 文件 > 默认值。

### 部署环境字段（通过 K8s Deployment env: 注入）

| 环境变量 | 默认值 | 说明 |
|---|---|---|
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

## 环境推荐配置

### 本地开发环境

```yaml
MCP_BACKEND_BASE_URL: "http://localhost:8080"
MCP_BACKEND_AUTH_URL: "http://localhost:8080/api/auth/verify"
MCP_HOST: "0.0.0.0"
MCP_PORT: 8000
MCP_LOG_LEVEL: "DEBUG"
MCP_LOG_JSON: false    # 人类可读日志，方便查看
```

### 测试环境

```yaml
MCP_BACKEND_BASE_URL: "http://test-backend:8080"
MCP_BACKEND_AUTH_URL: "http://test-backend:8080/api/auth/verify"
MCP_HOST: "0.0.0.0"
MCP_PORT: 8000
MCP_LOG_LEVEL: "INFO"
MCP_LOG_JSON: true     # JSON 日志，便于采集
```

### 生产环境

```yaml
MCP_BACKEND_BASE_URL: "http://prod-backend:8080"
MCP_BACKEND_AUTH_URL: "http://prod-backend:8080/api/auth/verify"
MCP_HOST: "0.0.0.0"
MCP_PORT: 8000
MCP_LOG_LEVEL: "WARN"  # 生产环境减少 INFO 日志量
MCP_LOG_JSON: true     # JSON 日志输出到 stdout，由容器运行时采集
```

---

## K8s Deployment YAML 参考

以下为 Deployment 的 `env:` 段落配置示例，**完整 YAML 由用户根据实际集群环境创建**。

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
            # ── 部署环境（按环境修改） ──
            - name: MCP_BACKEND_BASE_URL
              value: "http://backend-service:8080"
            - name: MCP_BACKEND_AUTH_URL
              value: "http://backend-service:8080/api/auth/verify"
            - name: MCP_HOST
              value: "0.0.0.0"
            - name: MCP_PORT
              value: "8000"
            - name: MCP_LOG_LEVEL
              value: "INFO"
            - name: MCP_LOG_JSON
              value: "true"
            # ── 运行策略（可选覆盖） ──
            - name: MCP_REQUEST_TIMEOUT
              value: "20"
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

1. **敏感信息**：`MCP_BACKEND_AUTH_URL` 中不应包含凭据，认证通过 JWT Token 传递
2. **日志安全**：`log_json=true` 时，`user_token` 字段自动脱敏（仅保留前 N 字符）
3. **资源规划**：建议每个 Pod 分配 256Mi~512Mi 内存，cpu 200m~500m
4. **健康检查**：使用 `/obot/health` 端点（返回 `{"status": "healthy"}`）
5. **扩缩容**：服务无状态，可水平扩展，建议 HPA 基于 CPU 使用率自动扩缩
