"""MCP server implementation for python-mcp-demo."""

import httpx

try:
    from fastmcp import FastMCP
except ImportError:
    FastMCP = None  # Will be installed as dependency


def create_server(name: str = "python-mcp-demo") -> "FastMCP":
    """Create and configure a FastMCP server instance.

    Args:
        name: The name of the MCP server.

    Returns:
        A configured FastMCP server instance.
    """
    if FastMCP is None:
        raise ImportError("fastmcp is not installed. Run: uv add fastmcp")

    server = FastMCP(name)

    @server.tool()
    async def hello(name: str = "World") -> str:
        """Say hello to someone.

        Args:
            name: The name to greet.

        Returns:
            A greeting message.
        """
        return f"Hello, {name}! Welcome to MCP."

    @server.tool()
    async def fetch_url(url: str) -> dict:
        """Fetch the content of a URL.

        Args:
            url: The URL to fetch.

        Returns:
            A dict with status code and content preview.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10)
            return {
                "status": response.status_code,
                "content_preview": response.text[:500],
                "content_length": len(response.text),
            }

    @server.tool()
    async def add(a: float, b: float) -> float:
        """Add two numbers together.

        Args:
            a: First number.
            b: Second number.

        Returns:
            The sum of a and b.
        """
        return a + b

    return server


# Lazily initialized singleton
mcp = create_server()

if __name__ == "__main__":
    mcp.run()
