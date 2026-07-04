"""Custom exceptions for python-mcp-demo."""

class MCPToolError(Exception):
    """Raised when a tool encounters a recoverable error."""

class MathExpressionError(MCPToolError):
    """Raised for invalid or unsafe math expressions."""
