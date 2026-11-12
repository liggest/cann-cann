<div align="center">

# cann-cann

[![PyPI version](https://img.shields.io/pypi/v/cann-cann.svg)](https://pypi.org/project/cann-cann/)

一行代码快速检查环境上的 NPU 与 CANN 参数

> 看看你的 UB 有多大😎
</div>

## 安装

```bash
pip install cann-cann
```

> 支持 Python >= 3.10；需要安装 CANN 并加载环境变量

AI Agent 安装后可运行 `cann-cann skill` 查看适合直接执行的快速上手说明

## 命令行

提供 `cann-cann` 与作为简称的 `ccann` 命令，使用任一命令均可

```bash
ccann npu-name               # Ascend950PR_XXXX
ccann UB --kb                # 248
ccann -n A3 memory --gb      # 64
ccann cann-version           # 9.1.0
ccann cores                  # AI、Cube、Vector 核数量
```

## Python 接口

```python
import cann_cann

cann_cann.npu_name()  # "Ascend950PR_XXXX"
cann_cann.ub_size(unit="kb")  # 248
cann_cann.memory_size(npu_name="A3", unit="gb")  # 64
cann_cann.cann_version()  # "9.1.0"
```

完整的查询列表、Python API、NPU 型号简称、单位和错误处理请参阅[使用指南](https://github.com/liggest/cann-cann/blob/main/docs/usage.md)

## 参与开发

参与开发时，先安装开发依赖并启用提交前检查

```bash
uv sync --dev
uv run pre-commit install
```

启用后，每次提交前都会使用 Ruff 自动检查并格式化 Python 代码。也可手动检查所有文件

```bash
uv run pre-commit run --all-files
```

完整检查、测试与构建

```bash
uv run ruff format --check .
uv run ruff check .
uv run pytest
uv build
```
