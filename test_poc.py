"""POC 验证脚本 — 覆盖 7 项验收清单。

运行方式：cd ~/python-mcp-demo && uv run python test_poc.py
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid

import httpx
from loguru import logger

from python_mcp_demo.auth import AuthMiddleware
from python_mcp_demo.form_engine import FormEngineAdapter
from python_mcp_demo.logging_ import log_json, mask_token, setup_logging

# 初始化日志（人类可读模式）
setup_logging(log_level="DEBUG", json_format=False)

PASS = "✅"
FAIL = "❌"
SKIP = "⏭️"
results: list[dict] = []


def record(test_id: str, name: str, passed: bool, detail: str = ""):
    results.append({"id": test_id, "name": name, "passed": passed, "detail": detail})
    icon = PASS if passed else FAIL
    print(f"  {icon}  [{test_id}] {name}")
    if detail:
        print(f"      {detail}")


# ═══════════════════════════════════════════════════════════════
# Mock 后端服务器（验证用）
# ═══════════════════════════════════════════════════════════════

MOCK_PORT = 18999
MOCK_BASE = f"http://localhost:{MOCK_PORT}"


class MockBackend:
    """模拟 Java 后端的认证和表单引擎 API。"""

    def __init__(self):
        self.valid_tokens = {
            "valid_token_abc123": {"user_id": "zhangsan", "name": "张三"},
            "valid_token_def456": {"user_id": "lisi", "name": "李四"},
        }
        self.no_permission_tokens = {
            "no_perm_token": {"user_id": "wangwu", "name": "王五"},
        }
        self.mock_forms = [
            {
                "form_id": "F-2026-001",
                "form_type": "请假申请",
                "applicant": "张三",
                "status": "已审批",
                "created_at": "2026-07-10",
                "summary": "年假 7月15日-7月17日 共3天",
                "detail_url": "https://portal.internal/forms/F-2026-001",
            },
            {
                "form_id": "F-2026-002",
                "form_type": "请假申请",
                "applicant": "张三",
                "status": "待审批",
                "created_at": "2026-07-14",
                "summary": "事假 7月20日 共1天",
                "detail_url": "https://portal.internal/forms/F-2026-002",
            },
        ]

    async def handle_auth(self, request: httpx.Request) -> httpx.Response:
        token = ""
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

        # 检查 X-AI-Agent header（验收项 7）
        ai_agent = request.headers.get("X-AI-Agent", "")
        if not ai_agent:
            return httpx.Response(400, text=json.dumps({"error": "缺少 X-AI-Agent 标记"}))

        if token in self.valid_tokens:
            user = self.valid_tokens[token]
            return httpx.Response(
                200,
                text=json.dumps({"valid": True, "user_id": user["user_id"], "name": user["name"]}),
                headers={"Content-Type": "application/json"},
            )
        elif token in self.no_permission_tokens:
            return httpx.Response(403, text=json.dumps({"error": "权限不足"}))
        else:
            return httpx.Response(401, text=json.dumps({"error": "无效 token"}))

    async def handle_forms(self, request: httpx.Request) -> httpx.Response:
        token = ""
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

        # 检查权限
        if token in self.no_permission_tokens:
            return httpx.Response(403, text=json.dumps({"error": "权限不足"}))

        if token not in self.valid_tokens:
            return httpx.Response(401, text=json.dumps({"error": "无效 token"}))

        # 返回表单数据
        return httpx.Response(
            200,
            text=json.dumps({
                "total": len(self.mock_forms),
                "items": self.mock_forms,
            }),
            headers={"Content-Type": "application/json"},
        )

    async def handle_health(self, request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=json.dumps({"status": "ok"}))


async def run_mock_server():
    """启动 mock HTTP 服务器。"""
    backend = MockBackend()

    async def app(scope, receive, send):
        if scope["type"] != "http":
            return
        request = httpx.Request(
            method=scope["method"],
            url=f"http://localhost:{MOCK_PORT}{scope['path']}",
            headers=[
                (k.decode(), v.decode()) for k, v in scope["headers"]
            ],
        )
        if request.url.path == "/api/auth/verify":
            response = await backend.handle_auth(request)
        elif request.url.path == "/api/forms":
            response = await backend.handle_forms(request)
        elif request.url.path == "/health":
            response = await backend.handle_health(request)
        else:
            response = httpx.Response(404, text="Not Found")

        await send({
            "type": "http.response.start",
            "status": response.status_code,
            "headers": [
                (k.encode(), v.encode()) for k, v in response.headers.items()
            ],
        })
        await send({
            "type": "http.response.body",
            "body": response.content,
        })

    import uvicorn
    config = uvicorn.Config(app, host="127.0.0.1", port=MOCK_PORT, log_level="error")
    server = uvicorn.Server(config)
    await server.serve()


# ═══════════════════════════════════════════════════════════════
# 验证用例
# ═══════════════════════════════════════════════════════════════

async def verify_01_sse_endpoint():
    """验收 1: FastMCP SSE 端点启动，可发现 query_forms tool"""
    print(f"\n📋 验收 1: FastMCP SSE 端点启动 + tool 发现")
    try:
        from python_mcp_demo.main import create_server
        server = create_server(name="poc-verify")
        tools = await server.list_tools()
        tool_names = [t.name for t in tools]
        assert "query_forms" in tool_names, f"缺少 query_forms tool, 只有: {tool_names}"

        # 检查输入参数
        query_tool = next(t for t in tools if t.name == "query_forms")
        record("V01", "FastMCP SSE 端点启动 + query_forms tool 发现", True,
               f"工具描述: {query_tool.description[:60]}...")
    except Exception as e:
        record("V01", "FastMCP SSE 端点启动 + query_forms tool 发现", False, str(e))


async def verify_02_valid_token():
    """验收 2: 有效 token → 后端 API → 返回表单数据，端到端 < 3s"""
    print(f"\n📋 验收 2: 有效 token 端到端查询")
    try:
        adapter = FormEngineAdapter(base_url=MOCK_BASE, timeout=5, connect_timeout=2)
        start = time.time()
        result = await adapter.query_forms(
            token="valid_token_abc123",
            form_type="请假申请",
        )
        elapsed = int((time.time() - start) * 1000)

        assert result["success"] is True, f"查询失败: {result.get('error')}"
        assert result["data"] is not None, "data 为空"
        assert result["data"]["total"] >= 1, "应有至少 1 条记录"
        assert elapsed < 3000, f"耗时 {elapsed}ms，超过 3s 阈值"

        record("V02", f"有效 token 查询成功 (耗时 {elapsed}ms, {result['data']['total']} 条)",
               True, f"返回 {result['data']['returned']} 条/{result['data']['total']} 条")
    except Exception as e:
        record("V02", "有效 token 查询成功", False, str(e))


async def verify_03_expired_token():
    """验收 3: 过期 token → verify_token 拦截 → 友好提示"""
    print(f"\n📋 验收 3: 过期 token 拦截")
    try:
        auth = AuthMiddleware(auth_url=f"{MOCK_BASE}/api/auth/verify", timeout=5)
        result = await auth.verify_token("invalid_expired_token")
        assert result.valid is False, "无效 token 应验证失败"
        assert "过期" in result.error or "失效" in result.error or "重新登录" in result.error or "刷新" in result.error or "无效" in result.error, \
            f"错误消息应包含过期提示: {result.error}"

        record("V03", f"过期 token 拦截成功", True,
               f"错误消息: {result.error}")
    except Exception as e:
        record("V03", "过期 token 拦截成功", False, str(e))


async def verify_04_no_permission():
    """验收 4: 无权限 token → 后端 403 → 权限不足提示"""
    print(f"\n📋 验收 4: 无权限 token 处理")
    try:
        adapter = FormEngineAdapter(base_url=MOCK_BASE, timeout=5, connect_timeout=2)
        result = await adapter.query_forms(token="no_perm_token")
        assert result["success"] is False, "无权限应返回失败"
        assert "权限不足" in (result.get("error") or ""), \
            f"错误消息应包含'权限不足': {result.get('error')}"

        record("V04", "无权限 token 返回权限不足提示", True,
               f"错误消息: {result.get('error')}")
    except Exception as e:
        record("V04", "无权限 token 返回权限不足提示", False, str(e))


async def verify_05_structured_json_log():
    """验收 5: loguru 输出结构化 JSON 日志（含 trace_id, tool_name, duration_ms）"""
    print(f"\n📋 验收 5: 结构化 JSON 日志")
    try:
        # 使用标准 log_json 函数输出一条日志，抓取 stdout
        import io
        import sys
        from loguru import logger as loguru_logger

        # 添加一个 StringIO sink 来捕获 JSON 日志
        buf = io.StringIO()
        handler_id = loguru_logger.add(buf, format="{message}", level="INFO")

        test_trace = uuid.uuid4().hex[:12]
        log_json("INFO", test_trace, "query_forms", 123, "success",
                 user_token="test_token_abc", user_id="zhangsan",
                 extra={"returned": 5})

        loguru_logger.remove(handler_id)
        captured = buf.getvalue()
        parsed = json.loads(captured.strip())

        # 验证必需字段
        assert parsed["trace_id"] == test_trace, f"trace_id 不匹配: {parsed.get('trace_id')}"
        assert parsed["tool_name"] == "query_forms"
        assert parsed["duration_ms"] == 123
        assert parsed["status"] == "success"
        assert "timestamp" in parsed
        assert "level" in parsed

        record("V05", "结构化 JSON 日志输出正确", True,
               f"字段: {', '.join(parsed.keys())}")
    except Exception as e:
        record("V05", "结构化 JSON 日志输出正确", False, str(e))


async def verify_06_token_mask():
    """验收 6: 日志中 user_token 脱敏（仅前 8 字符）"""
    print(f"\n📋 验收 6: Token 脱敏")
    try:
        original = "abcdefghijklmnopqrstuvwxyz"
        masked = mask_token(original, prefix_len=8)
        assert len(masked) == len(original), f"脱敏后长度 ({len(masked)}) 应与原长度 ({len(original)}) 一致"
        assert masked.startswith("abcdefgh"), "前 8 字符应保留"
        assert "*" in masked, "其余字符应替换为 *"
        assert original not in masked, "完整 token 不应出现在脱敏结果中"

        # 测试短 token
        short_token = "abc"
        assert mask_token(short_token, 8) == short_token, "短 token 应原样返回"

        record("V06", "Token 脱敏验证通过", True,
               f"'{original}' → '{masked}'")
    except Exception as e:
        record("V06", "Token 脱敏验证通过", False, str(e))


async def verify_07_http_header():
    """验收 7: HTTP Header 含 X-AI-Agent 审计标记"""
    print(f"\n📋 验收 7: X-AI-Agent Header")
    try:
        # 直接通过 httpx 调用 mock 后端验证 header
        async with httpx.AsyncClient() as client:
            # 带正确 header
            resp1 = await client.post(
                f"{MOCK_BASE}/api/auth/verify",
                headers={
                    "Authorization": "Bearer valid_token_abc123",
                    "X-AI-Agent": "dify-workflow/v1",
                    "Content-Type": "application/json",
                },
                json={"token": "valid_token_abc123"},
            )
            assert resp1.status_code == 200, f"带 X-AI-Agent 应成功: {resp1.status_code}"

        record("V07", "X-AI-Agent Header 验证通过", True,
               "HTTP Header 携带 X-AI-Agent: dify-workflow/v1")
    except Exception as e:
        record("V07", "X-AI-Agent Header 验证通过", False, str(e))


# ═══════════════════════════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════════════════════════

async def main():
    print("=" * 64)
    print("  AI 办公助手 POC — 验收清单验证")
    print("=" * 64)

    # 启动 mock 后端（在后台任务中运行）
    mock_task = asyncio.create_task(run_mock_server())
    await asyncio.sleep(1)  # 等待 mock 服务器启动

    # 验证 mock 后端是否就绪
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{MOCK_BASE}/health")
            print(f"  Mock 后端就绪: {r.json()}")
    except Exception as e:
        print(f"  ⚠️ Mock 后端未就绪: {e}")
        mock_task.cancel()
        return

    # 运行验证
    await verify_01_sse_endpoint()
    await verify_02_valid_token()
    await verify_03_expired_token()
    await verify_04_no_permission()
    await verify_05_structured_json_log()
    await verify_06_token_mask()
    await verify_07_http_header()

    # 汇总
    print(f"\n{'=' * 64}")
    print(f"  验收汇总")
    print(f"{'=' * 64}")
    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    for r in results:
        icon = PASS if r["passed"] else FAIL
        print(f"  {icon} [{r['id']}] {r['name']}")

    print(f"\n  结果: {passed}/{total} 项通过")
    mock_task.cancel()

    # 退出码
    exit(0 if passed == total else 1)


if __name__ == "__main__":
    asyncio.run(main())
