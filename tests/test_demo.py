"""python-mcp-demo 测试。"""

import pytest
from fastmcp.exceptions import ToolError
from python_mcp_demo import create_server, __version__


def test_version():
    """验证包版本号。"""
    assert __version__ == "0.5.0"


@pytest.fixture
def server():
    """创建测试用服务器实例。"""
    return create_server("test-server")


def _text(result) -> str:
    """从 FastMCP ToolResult 中提取文本内容。"""
    if hasattr(result, 'content') and result.content:
        item = result.content[0]
        return item.text if hasattr(item, 'text') else str(item)
    return str(result)


@pytest.mark.asyncio
async def test_hello_tool(server):
    """测试 hello 工具返回问候语。"""
    result = await server.call_tool("hello", {"name": "MCP"})
    text = _text(result)
    assert "Hello, MCP!" in text


@pytest.mark.asyncio
async def test_hello_default(server):
    """测试 hello 工具使用默认名称。"""
    result = await server.call_tool("hello", {})
    text = _text(result)
    assert "Hello, World!" in text


@pytest.mark.asyncio
async def test_add_tool(server):
    """测试 add 工具返回正确和。"""
    result = await server.call_tool("add", {"a": 3.0, "b": 4.0})
    assert "7.0" in _text(result)


@pytest.mark.asyncio
async def test_add_negative(server):
    """测试 add 工具处理负数。"""
    result = await server.call_tool("add", {"a": -5.0, "b": 10.0})
    assert "5.0" in _text(result)


@pytest.mark.asyncio
async def test_calculate_simple(server):
    """测试 calculate 工具处理表达式。"""
    result = await server.call_tool("calculate", {"expression": "2 + 3 * 4"})
    assert "14.0" in _text(result)


@pytest.mark.asyncio
async def test_calculate_invalid(server):
    """除零应抛出 ToolError（包装 MathExpressionError）。"""
    with pytest.raises(ToolError) as exc_info:
        await server.call_tool("calculate", {"expression": "2/0"})
    assert "零" in str(exc_info.value)


@pytest.mark.asyncio
async def test_calculate_empty(server):
    """空表达式应抛出 ToolError。"""
    with pytest.raises(ToolError) as exc_info:
        await server.call_tool("calculate", {"expression": ""})
    assert "空" in str(exc_info.value)


@pytest.mark.asyncio
async def test_random_number(server):
    """测试 random_number 生成有效范围内的随机数。"""
    result = await server.call_tool("random_number", {"min": 0.0, "max": 10.0})
    val = float(_text(result))
    assert 0.0 <= val <= 10.0


@pytest.mark.asyncio
async def test_random_number_invalid(server):
    """最小值大于最大值时应抛出 ToolError。"""
    with pytest.raises(ToolError):
        await server.call_tool("random_number", {"min": 10.0, "max": 0.0})


@pytest.mark.asyncio
async def test_current_time_utc(server):
    """测试 current_time 返回 UTC 时间。"""
    result = await server.call_tool("current_time", {"timezone": "UTC"})
    text = _text(result)
    # 验证是日期时间格式
    assert len(text) == 19  # YYYY-MM-DD HH:MM:SS


@pytest.mark.asyncio
async def test_current_time_invalid(server):
    """无效时区应抛出 ToolError。"""
    with pytest.raises(ToolError):
        await server.call_tool("current_time", {"timezone": "Fake/Zone"})


@pytest.mark.asyncio
async def test_echo(server):
    """测试 echo 工具重复消息。"""
    result = await server.call_tool("echo", {"message": "hi", "times": 3})
    text = _text(result)
    assert text.count("hi") == 3


@pytest.mark.asyncio
async def test_echo_default(server):
    """测试 echo 默认重复一次。"""
    result = await server.call_tool("echo", {"message": "hello"})
    text = _text(result)
    assert "hello" in text


@pytest.mark.asyncio
async def test_echo_invalid_times(server):
    """超出范围的重复次数应抛出 ToolError。"""
    with pytest.raises(ToolError):
        await server.call_tool("echo", {"message": "x", "times": 101})


@pytest.mark.asyncio
async def test_count_words(server):
    """测试 count_words 统计文本。"""
    result = await server.call_tool("count_words", {
        "text": "hello world hello"
    })
    text = _text(result)
    assert "hello" in text


@pytest.mark.asyncio
async def test_count_words_empty(server):
    """空文本应正常处理而不报错。"""
    result = await server.call_tool("count_words", {"text": ""})
    text = _text(result)
    assert "word" in text.lower() or "char" in text.lower()
