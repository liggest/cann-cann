# 仓库基础设施

## 1. 提交前检查

- [x] 配置 pre-commit，使 Ruff 在提交前依次自动修复静态检查问题并格式化代码，同时补充安装与手动检查说明

## 2. 持续集成

- [x] 配置 GitHub Actions：使用 uv 安装锁定的开发环境，运行一次全仓 pre-commit，并在 Python 3.10～3.14 上并行运行 pytest

## 3. 验证与收尾

- [x] 在本地运行 pre-commit、完整 pytest 和构建检查，确认配置文件有效后更新任务状态
