# python-mcp-demo Makefile
#
# 常用开发任务。需要 uv（https://docs.astral.sh/uv/）。

.PHONY: install test test-coverage run clean lint format

install:                          ## 安装项目依赖
	uv sync

test:                             ## 运行测试（详细输出）
	uv run pytest -v

test-coverage:                    ## 运行测试并生成覆盖率报告
	uv run pytest -v --cov=python_mcp_demo --cov-report=term-missing

run:                              ## 启动 MCP 服务器
	uv run python -m python_mcp_demo

lint:                             ## 使用 ruff 检查代码
	uv run ruff check src/ tests/

format:                           ## 使用 ruff 格式化代码
	uv run ruff format src/ tests/

clean:                            ## 清理构建和缓存文件
	rm -rf .venv/ .pytest_cache/ __pycache__/
	rm -rf src/*.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
