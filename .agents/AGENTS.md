# cann-cann 开发约定

## 项目定位

- `cann-cann` 取“看看”之意，是读取当前 CANN 安装中 NPU 平台配置的轻量工具库
- 面向 Linux 环境，同时提供 Python API 与 `cann-cann` / `ccann` CLI，支持 Python >= 3.10
- 当前范围只读取静态平台配置，不负责设备监控、温度功耗、卡号管理等 `npu-smi` 能力
- 保持零运行时依赖；开发工具使用 uv、pytest、Ruff 和 pre-commit，构建后端使用 uv_build

## 开发前先了解

- `src/cann_cann/config.py`：只读配置模型与 INI 解析
- `src/cann_cann/environment.py`：CANN 路径、架构及 ACL 探测
- `src/cann_cann/__init__.py`：公开 API、惰性版本属性与默认配置缓存
- `src/cann_cann/cli.py`：CLI 参数解析，只调用公开 Python API
- `src/cann_cann/units.py`：存储空间大小单位转换
- `src/cann_cann/errors.py`：精简的公开异常层级
- `tests/fixtures/platform_config/`：从真实 CANN 配置精简出的测试数据
- `tests/smoke_test.py`：验证 wheel 和源码包可以独立安装并读取版本
- `.github/workflows/ci.yml`：pre-commit 与 Python 3.10～3.14 测试
- `.github/workflows/release.yml`：GitHub Release 与 PyPI Trusted Publishing
- 开始任务前阅读 `.agents/todo/` 中相关文档；新增待办按可独立验收的结果拆分，不堆实现步骤

## 必须遵守

- 面向用户的 README、docstring、CLI 帮助和错误信息使用简明、自然的中文
- Python 标识符及 NPU、CANN、ACL、AI Core、UB、L0A、Section 等术语保持英文；独立中文文案末尾通常不加句号
- 公共型号参数统一叫 `npu_name`；不要用易与设备编号、神经网络模型混淆的名称
- 顶层使用 `npu_name()`、`all_npu_names()`；实现层可使用 `detect_`、`list_` 等动作名称
- 显式传入 `npu_name` 时不得导入或调用 ACL；只有自动探测时才延迟导入 ACL，并缓存成功结果
- `CANNPlatformConfig` 和 Section 保持只读；类型化属性与内部 Section 注册表必须引用同一对象
- 新版 CANN 的未知 Section、字段和数字键必须保留原始字符串，不要因暂未支持而丢弃
- 大小属性保存 INI 原始字节值，单位转换只放在便利方法或顶层函数中
- 参数错误使用标准 `ValueError`；CANN 环境或平台配置错误使用 `CannCannError` 子类
- 修改公开 API 或 CLI 时同步 `__all__`、帮助文本、测试及对应层级的用户文档；只有核心用法变化时才扩充 README

## 用户文档

- `README.md` 只展示项目定位、安装方式和少量核心用法，并链接到 `docs/usage.md`；不要在 README 中堆完整查询表、别名、单位和错误规则
- `docs/usage.md` 按首次使用者的任务顺序组织：准备环境并安装、查询当前 NPU 型号、查询指定型号，再介绍 CLI、Python API、简称、单位和错误处理
- 先给用户可以直接运行的核心示例，再补充必要说明；不要要求用户在开始使用前先理解 ACL、配置目录、名称解析或查询分派等实现机制
- 命令、函数调用与示例结果放在一起；Shell 和 Python 示例优先用紧随调用的 `# 结果` 展示预期输出，使示例容易阅读和复制
- 一项概念只在第一次需要时解释，说明紧邻相关示例；精确映射或完整查询列表使用表格，不在多个章节重复同一概念
- 使用用户视角的名称，统一称“当前 NPU 型号”和“CANN 包”；不要为了显得完整而突出内部辅助函数或较少使用的公开接口，使用指南不是 API 符号索引
- 使用前统一说明需要安装 CANN 并加载 CANN 环境变量；显式指定 `npu_name` 虽然不调用 ACL，仍需要通过 `ASCEND_HOME_PATH` 定位 CANN 包中的配置文件
- 安装示例使用简洁的 `pip install cann-cann`；没有具体环境需求时，不改写为更长的等价命令
- 用户文档中的标题、段落、提示、列表项和表格说明在行尾结句时不加句号；避免把多个完整句子硬拼成长句
- 重点描述当前可用行为；项目尚未形成真实兼容负担时，不为假设中的旧版本用户增加迁移说明
- 简称、单位、输出协议和错误处理等参考信息放在核心用法之后；只保留会影响用户选择或结果理解的边界说明

## 不要做

- 不要硬编码 NPU 型号白名单，也不要让测试依赖本机真实 NPU 或 CANN 安装
- 不要把 INI 简单拍平成一个字典；同名字段可能属于不同 Section
- 不要在顶层便利函数中增加 `cann_home`；高级用法通过配置类处理，确有需求再讨论全局配置接口
- 不要为单一抛出位置创建大量异常类，也不要为很小的改动堆砌待办项
- 不要为了 CLI 方便复制查询逻辑，或引入非必要的运行时依赖
- 未经明确要求，不做兼容别名、全局可变状态、设备监控和大范围重构

## 版本与发布

- `pyproject.toml` 是版本号的唯一来源；使用 `uv version` 更新版本并同步提交 `uv.lock`
- `cann_cann.__version__` 惰性读取已安装包元数据，不要在源码中重复硬编码版本号
- GitHub Release 标签必须为 `v<项目版本>`；PyPI 已发布版本不能覆盖，发布新内容前必须递增版本
- `.github/workflows/release.yml` 和 GitHub `pypi` environment 已与 PyPI Trusted Publisher 绑定，不要随意改名
- 发布使用 OIDC，不要在仓库或 environment 中添加 PyPI 用户名、密码或长期 Token

## 测试与交付

- 测试使用精简 fixture 和假的 `acl` 模块；新增型号差异时优先补 fixture
- CANN/ACL 在容器入口中可能较慢，真实探测至少等待 30 秒；沙箱无法访问驱动时申请单次外部执行权限
- 完成代码修改后运行：

```bash
uv run ruff format .
uv run ruff check .
uv run pytest
uv build --no-sources
```

- 涉及打包或发布时，额外使用 `tests/smoke_test.py` 对 wheel 和源码包做隔离安装验证
- 只有验证通过后才勾选待办；提交 Git 或推送远端必须由用户明确要求
