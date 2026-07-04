"""Configuration for python-mcp-demo."""

import os
from dataclasses import dataclass, field

@dataclass
class MCPConfig:
    server_name: str = "python-mcp-demo"
    request_timeout: int = 30
    log_level: str = "INFO"
    max_fetch_size: int = 500

def load_config() -> MCPConfig:
    return MCPConfig(
        server_name=os.getenv("MCP_SERVER_NAME", "python-mcp-demo"),
        request_timeout=int(os.getenv("MCP_REQUEST_TIMEOUT", "30")),
        log_level=os.getenv("MCP_LOG_LEVEL", "INFO").upper(),
        max_fetch_size=int(os.getenv("MCP_MAX_FETCH_SIZE", "500")),
    )
