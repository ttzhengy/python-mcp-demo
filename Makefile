# python-mcp-demo Makefile
#
# Common development tasks. Requires uv (https://docs.astral.sh/uv/).

.PHONY: install test test-coverage run clean lint format

install:                          ## Install project dependencies
	uv sync

test:                             ## Run tests with verbose output
	uv run pytest -v

test-coverage:                    ## Run tests with coverage report
	uv run pytest -v --cov=python_mcp_demo --cov-report=term-missing

run:                              ## Start the MCP server
	uv run python -m python_mcp_demo

lint:                             ## Lint source code with ruff
	uv run ruff check src/ tests/

format:                           ## Format source code with ruff
	uv run ruff format src/ tests/

clean:                            ## Remove build artifacts and caches
	rm -rf .venv/
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	rm -rf *.egg-info/
	rm -rf dist/
	rm -rf build/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
