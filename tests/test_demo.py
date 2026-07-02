"""Tests for python-mcp-demo."""

import pytest
from python_mcp_demo import create_server, __version__


def test_version():
    """Verify the package has a version string."""
    assert __version__ == "0.1.0"


@pytest.fixture
def server():
    """Create a test server instance."""
    return create_server("test-server")


@pytest.mark.asyncio
async def test_hello_tool(server):
    """Test the hello tool returns a greeting."""
    result = await server.call_tool("hello", {"name": "MCP"})
    assert "Hello, MCP!" in str(result.content)


@pytest.mark.asyncio
async def test_hello_default(server):
    """Test the hello tool with default name."""
    result = await server.call_tool("hello", {})
    assert "Hello, World!" in str(result.content)


@pytest.mark.asyncio
async def test_add_tool(server):
    """Test the add tool returns correct sum."""
    result = await server.call_tool("add", {"a": 3.0, "b": 4.0})
    assert "7.0" in str(result.content)


@pytest.mark.asyncio
async def test_add_negative(server):
    """Test the add tool with negative numbers."""
    result = await server.call_tool("add", {"a": -5.0, "b": 10.0})
    assert "5.0" in str(result.content)
