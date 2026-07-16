# 贡献指南

## 环境搭建

### 前置要求

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)（推荐）或 pip

### 安装步骤

```bash
# 克隆仓库
git clone https://github.com/ttzhengy/python-mcp-demo.git
cd python-mcp-demo

# 安装依赖
uv sync

# 可选：安装开发依赖（含测试工具）
uv sync --group dev

# 设置环境变量（可选）
cp .env.example .env
# 编辑 .env 按需调整配置
```

### 验证安装

```bash
# 运行测试
uv run pytest -v

# 启动服务器
uv run python -m python_mcp_demo
```

---

## 开发工作流

### 1. 编写代码

- 所有代码在 `src/python_mcp_demo/` 目录下
- Demo 工具编辑 `server.py`，POC 工具编辑 `main.py`
- 业务适配器新建独立模块（参考 `form_engine.py`）
- 遵循 [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html) 的 docstring 格式

### 2. 运行测试

```bash
# 运行所有测试
uv run pytest -v

# 带覆盖率报告
uv run pytest -v --cov=python_mcp_demo --cov-report=term-missing

# 特定测试文件
uv run pytest -v tests/test_demo.py

# 按测试名称筛选
uv run pytest -v -k "test_calculate"

# POC 验收验证
uv run python test_poc.py
```

### 3. 代码检查

```bash
# 静态检查
uv run ruff check src/ tests/

# 自动格式化
uv run ruff format src/ tests/

# 或者使用 Makefile
make lint
make format
```

### 4. 提交规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式：

```
<type>(<scope>): <简短描述>

<详细说明（可选）>

<footer（可选）>
```

**类型：**

| 类型 | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `docs` | 文档更新 |
| `refactor` | 代码重构 |
| `test` | 测试相关 |
| `chore` | 构建/工具链变更 |
| `style` | 代码格式（不影响功能） |
| `perf` | 性能优化 |

**示例：**

```
feat(server): 添加 JPEG 图片处理工具

支持将图片调整为指定尺寸，返回 Base64 编码结果。

Closes #12
```

```
docs(api): 补充 query_forms 错误码说明
```

```
fix(auth): 修复空 Token 时未校验的问题
```

### 5. 提交流程

```bash
# 查看变更
git status
git diff

# 暂存并提交
git add <文件>
git commit -m "type(scope): 描述"

# 推送到远程
git push origin <branch>
```

---

## 添加新工具指南

详见 [`docs/architecture.md`](docs/architecture.md) 的「扩展方式：如何添加新工具」章节。

---

## 代码规范

### 命名约定

| 元素 | 规范 | 示例 |
|------|------|------|
| 模块/包 | 小写下划线 | `form_engine.py` |
| 类 | 大驼峰 | `AuthMiddleware` |
| 函数/方法 | 小写下划线 | `verify_token()` |
| 变量 | 小写下划线 | `user_token` |
| 常量 | 大写加下划线 | `_SAFE_OPERATORS` |
| 私有属性/方法 | 下划线前缀 | `self._auth_url` |

### 类型注解

所有函数参数和返回值必须添加类型注解：

```python
def calculate_total(items: list[float], discount: float = 0.0) -> float:
    ...
```

### Docstring

使用 Google-style docstring 格式：

```python
def my_function(param1: str, param2: int = 0) -> bool:
    """一句话功能描述。

    详细说明（可选），可以跨多行。

    Args:
        param1: 参数说明。
        param2: 参数说明，含默认值。

    Returns:
        返回值说明。

    Raises:
        ValueError: 出错条件说明。
    """
```

### 工具方法约束

- 工具方法名：小写下划线
- 输入参数：使用类型注解
- 返回值：Demo 工具使用基本类型，POC 工具使用 `dict`（含 `success`/`data`/`error`）
- 异常：继承 `MCPToolError` 的自定义异常

### 日志规范

- 使用 `logger` 记录操作日志（`server.py` 用标准 logging，POC 用 loguru）
- POC 工具执行日志使用 `log_json()` 函数输出结构化 JSON
- 敏感信息（Token）脱敏后打印

---

## 发布流程

```bash
# 1. 更新版本号
#    pyproject.toml 中的 version 字段
#    src/python_mcp_demo/__init__.py 中的 __version__

# 2. 确保所有测试通过
uv run pytest -v --cov=python_mcp_demo

# 3. 构建
uv build

# 4. 发布到 PyPI
uv publish
```

---

## 目录结构规范

```
src/python_mcp_demo/
├── __init__.py      # 导出公共 API，版本声明
├── __main__.py      # CLI 入口
├── server.py        # Demo 工具（8 个内置）
├── main.py          # POC 主入口
├── config.py        # 配置管理
├── auth.py          # 认证中间件
├── exceptions.py    # 异常定义
├── logging_.py      # 日志工具
└── form_engine.py   # 业务适配器示例

tests/
├── test_demo.py     # Demo 层测试
└── ...              # 其他测试

docs/
├── api.md           # API 文档
└── architecture.md  # 架构说明
```
