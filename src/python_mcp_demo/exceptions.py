"""python-mcp-demo 自定义异常。"""

class MCPToolError(Exception):
    """工具执行时遇到可恢复错误时抛出。"""

class MathExpressionError(MCPToolError):
    """非法的或不安全的数学表达式时抛出。"""
