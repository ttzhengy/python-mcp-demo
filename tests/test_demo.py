"""Tests for python-mcp-demo."""

import pytest
from fastmcp.exceptions import ToolError
from python_mcp_demo import create_server, __version__


def test_version():
    assert __version__ == "0.2.0"


@pytest.fixture
def server():
    return create_server("test-server")


def _text(result) -> str:
    """Extract text from a FastMCP ToolResult."""
    if hasattr(result, 'content') and result.content:
        item = result.content[0]
        return item.text if hasattr(item, 'text') else str(item)
    return str(result)


@pytest.mark.asyncio
async def test_hello_tool(server):
    result = await server.call_tool("hello", {"name": "MCP"})
    text = _text(result)
    assert "Hello, MCP!" in text


@pytest.mark.asyncio
async def test_hello_default(server):
    result = await server.call_tool("hello", {})
    text = _text(result)
    assert "Hello, World!" in text


@pytest.mark.asyncio
async def test_add_tool(server):
    result = await server.call_tool("add", {"a": 3.0, "b": 4.0})
    assert "7.0" in _text(result)


@pytest.mark.asyncio
async def test_add_negative(server):
    result = await server.call_tool("add", {"a": -5.0, "b": 10.0})
    assert "5.0" in _text(result)


@pytest.mark.asyncio
async def test_calculate_simple(server):
    result = await server.call_tool("calculate", {"expression": "2 + 3 * 4"})
    assert "14.0" in _text(result)


@pytest.mark.asyncio
async def test_calculate_invalid(server):
    """Division by zero should raise a ToolError (wrapping MathExpressionError)."""
    with pytest.raises(ToolError) as exc_info:
        await server.call_tool("calculate", {"expression": "2/0"})
    assert "zero" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_calculate_empty(server):
    with pytest.raises(ToolError) as exc_info:
        await server.call_tool("calculate", {"expression": ""})
    assert "empty" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_random_number(server):
    result = await server.call_tool("random_number", {"min": 0.0, "max": 10.0})
    val = float(_text(result))
    assert 0.0 <= val <= 10.0


@pytest.mark.asyncio
async def test_random_number_invalid(server):
    with pytest.raises(ToolError):
        await server.call_tool("random_number", {"min": 10.0, "max": 0.0})


@pytest.mark.asyncio
async def test_current_time_utc(server):
    result = await server.call_tool("current_time", {"timezone": "UTC"})
    text = _text(result)
    # Just verify it's a datetime string
    assert len(text) == 19  # YYYY-MM-DD HH:MM:SS


@pytest.mark.asyncio
async def test_current_time_invalid(server):
    with pytest.raises(ToolError):
        await server.call_tool("current_time", {"timezone": "Fake/Zone"})


@pytest.mark.asyncio
async def test_echo(server):
    result = await server.call_tool("echo", {"message": "hi", "times": 3})
    text = _text(result)
    assert text.count("hi") == 3


@pytest.mark.asyncio
async def test_echo_default(server):
    result = await server.call_tool("echo", {"message": "hello"})
    text = _text(result)
    assert "hello" in text


@pytest.mark.asyncio
async def test_echo_invalid_times(server):
    with pytest.raises(ToolError):
        await server.call_tool("echo", {"message": "x", "times": 101})


@pytest.mark.asyncio
async def test_count_words(server):
    result = await server.call_tool("count_words", {
        "text": "hello world hello"
    })
    text = _text(result)
    assert "hello" in text


@pytest.mark.asyncio
async def test_count_words_empty(server):
    result = await server.call_tool("count_words", {"text": ""})
    text = _text(result)
    # Should handle empty text without error
    assert "word" in text.lower() or "char" in text.lower()
