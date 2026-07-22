"""AI 办公助手 — 配置管理（基于 pydantic-settings）。

配置优先级：环境变量 > .env 文件 > 默认值
所有环境变量以 MCP_ 为前缀。

配置分组说明：

  **部署环境相关**（通过 K8s Deployment env: 注入，各环境不同）
  - ``MCP_BACKEND_BASE_URL``：后端 API 基础地址
  - ``MCP_BACKEND_AUTH_URL``：认证服务 URL
  - ``MCP_HOST``：监听地址
  - ``MCP_PORT``：监听端口
  - ``MCP_LOG_LEVEL``：日志级别
  - ``MCP_LOG_JSON``：是否 JSON 结构化日志

  **运行策略相关**（代码内定，极少变更）
  - ``MCP_REQUEST_TIMEOUT``：请求读超时
  - ``MCP_CONNECT_TIMEOUT``：连接超时
  - ``MCP_MAX_RETRIES``：最大重试次数
  - ``MCP_RETRY_MIN_DELAY``：重试最小间隔
  - ``MCP_RETRY_MAX_DELAY``：重试最大间隔
  - ``MCP_TOKEN_MASK_PREFIX_LEN``：Token 脱敏前缀长度
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """AI 办公助手全局配置。

    从环境变量（MCP_ 前缀）或 .env 文件加载。

    按部署时注入 vs 代码内定分组，详见模块文档字符串。
    """

    # ═══════════════════════════════════════════════════════════════╗
    #  部署环境相关（各环境不同，通过 K8s Deployment env: 注入）    ║
    # ╚══════════════════════════════════════════════════════════════╝

    server_name: str = "ai-office-mcp"
    """FastMCP 服务器名称，供 Dify 识别。"""

    host: str = "0.0.0.0"
    """监听地址。"""

    port: int = 8000
    """监听端口。"""

    backend_base_url: str = "http://localhost:8080"
    """Java 后端服务基础 URL（开发/测试/生产环境不同）。"""

    backend_auth_url: str = "http://localhost:8080/api/auth/verify"
    """认证服务 API URL（用于 verify_token 前置校验）。"""

    log_level: str = "INFO"
    """日志级别：DEBUG | INFO | WARNING | ERROR | CRITICAL。"""

    log_json: bool = True
    """是否输出 JSON 结构化日志 vs 人类可读格式（K8s 用 JSON，本地开发用 readable）。"""

    # ═══════════════════════════════════════════════════════════════╗
    #  运行策略相关（代码内定，极少变更，一般不通过环境变量覆盖）   ║
    # ╚══════════════════════════════════════════════════════════════╝

    request_timeout: int = 20
    """HTTP 请求读超时（秒）。"""

    connect_timeout: int = 5
    """HTTP 连接超时（秒）。"""

    max_retries: int = 3
    """后端 5xx 错误时的最大重试次数。"""

    retry_min_delay: float = 1.0
    """重试最小间隔（秒，指数退避起始值）。"""

    retry_max_delay: float = 8.0
    """重试最大间隔（秒）。"""

    token_mask_prefix_len: int = 8
    """Token 脱敏时保留的前缀字符数。"""

    # ── 兼容字段（来自原有 server.py 的 fetch demo） ──
    max_fetch_size: int = 5000
    """fetch_url 工具内容预览的最大字节数（兼容旧版 demo）。"""

    model_config = SettingsConfigDict(
        env_prefix="MCP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


#: 全局单例设置实例
settings = Settings()


def load_settings() -> Settings:
    """返回全局 Settings 单例。

    在模块初始化时自动加载环境变量和 .env 文件。
    """
    return settings
