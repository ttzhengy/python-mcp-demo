"""loguru 结构化日志配置。

输出 JSON 格式的结构化日志到 stdout，以及日志文件轮转。
每条日志包含：
  - timestamp, level, trace_id, tool_name, user_id
  - duration_ms, status_code, message
  - 敏感字段（user_token）脱敏：仅保留前 N 字符
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from loguru import logger


def _normalize_log_level(level: str) -> str:
    """将常见日志级别别名规范化为 loguru 可识别的标准名称。

    loguru 不识别 ``WARN``，只认 ``WARNING``；类似地 ``FATAL`` → ``CRITICAL``。

    Args:
        level: 原始日志级别字符串（大小写不限）。

    Returns:
        规范化后的大写级别名称。
    """
    aliases = {"WARN": "WARNING", "FATAL": "CRITICAL", "TRACE": "DEBUG"}
    normalized = aliases.get(level.upper(), level.upper())
    return normalized


def setup_logging(log_level: str = "INFO", json_format: bool = True) -> None:
    """配置 loguru 日志输出。

    Args:
        log_level: 日志级别（DEBUG / INFO / WARNING / ERROR），接受 WARN 等别名。
        json_format: True = JSON 结构化输出；False = 人类可读格式。
    """
    log_level = _normalize_log_level(log_level)
    # 移除默认的 stderr handler
    logger.remove()

    if json_format:
        # JSON 结构化日志 → stdout（K8s 环境由容器运行时采集）
        logger.add(
            sys.stdout,
            format="{message}",
            level=log_level.upper(),
        )
    else:
        # 人类可读的开发日志
        logger.add(
            sys.stdout,
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                "<level>{level: <7}</level> | "
                "<cyan>{extra[trace_id]: <12}</cyan> | "
                "{message}"
            ),
            level=log_level.upper(),
        )

    # 文件日志输出：logs/python-mcp-demo.log，自动轮转（10MB/5 备份）
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    logger.add(
        sink=str(log_dir / "python-mcp-demo.log"),
        format="{message}" if json_format else (
            "{time:YYYY-MM-DD HH:mm:ss} | {level: <7} | {message}"
        ),
        level=log_level.upper(),
        rotation="10 MB",
        retention=5,
        encoding="utf-8",
    )


def mask_token(token: str, prefix_len: int = 8) -> str:
    """对用户 Token 进行脱敏处理。

    仅保留前 ``prefix_len`` 个字符，其余替换为 ``*``。
    空字符串或短于 prefix_len 的 Token 原样返回。

    Args:
        token: 原始 JWT Token。
        prefix_len: 保留的前缀字符数。

    Returns:
        脱敏后的 Token 字符串。
    """
    if not token:
        return ""
    if len(token) <= prefix_len:
        return token
    return token[:prefix_len] + "*" * (len(token) - prefix_len)


def log_json(
    level: str,
    trace_id: str,
    tool_name: str,
    duration_ms: int,
    status: str,
    *,
    user_token: str | None = None,
    user_id: str | None = None,
    error: str | None = None,
    extra: dict | None = None,
) -> None:
    """输出一条结构化 JSON 日志。

    该函数统一所有 JSON 日志的字段结构和序列化格式。
    日志记录器使用 ``logger.bind(json=True)`` 以确保 JSON 行
    与人类可读输出（如果启用）互不干扰。

    Args:
        level: 日志级别。
        trace_id: 请求链路追踪 ID。
        tool_name: 工具名称。
        duration_ms: 执行耗时（毫秒）。
        status: 状态（success / error / auth_failed 等）。
        user_token: 原始用户 Token（将被自动脱敏）。
        user_id: 用户标识（可选）。
        error: 错误消息（可选）。
        extra: 额外字段（可选）。
    """
    record = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.") +
                     f"{datetime.now(timezone.utc).microsecond // 1000:03d}Z",
        "level": level.upper(),
        "trace_id": trace_id,
        "tool_name": tool_name,
        "duration_ms": duration_ms,
        "status": status,
    }

    if user_token is not None:
        record["user_token"] = mask_token(user_token)
    if user_id is not None:
        record["user_id"] = user_id
    if error is not None:
        record["error"] = error
    if extra:
        record.update(extra)

    record["message"] = f"Tool {tool_name} {status} in {duration_ms}ms"

    # 使用绑定的 json=True 标志输出 JSON 行
    logger.bind(json=True).log(level.upper(), json.dumps(record, ensure_ascii=False))
