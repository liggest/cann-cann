# cann-cann 初版实现待办

目标：完成一个可安装、可作为 Python 库及 CLI 使用的 v0.1.0。首版重点验证
Ascend 910B、Ascend 910 93 系列、Ascend 950PR 和 Ascend 950DT 的平台配置；
解析器不设置型号白名单，其他具有兼容配置结构的 NPU 也应可以使用。

## 1. 工程基础

- [x] 完善 `pyproject.toml` 中的项目描述、Python 版本、CLI 入口和开发依赖。
- [x] 使用 pytest 作为测试框架。
- [x] 使用 Ruff 负责 format 和 lint，并配置 Python 3.10 目标版本。
- [x] 建立 `tests/` 目录及公共 fixture。
- [x] 确保 `uv run pytest`、`uv run ruff check .`、`uv run ruff format --check .` 可执行。
- [x] 确保 `uv build` 能生成 wheel 和 sdist。

## 2. 平台配置数据模型与 INI 解析

- [x] 实现只读的 `PlatformConfigSection` 基类，完整保留一个 INI Section 的原始键值。
- [x] 实现 `raw(name)` 和 `raw_items()`，返回未经转换的原始字符串数据。
- [x] 实现带 IDE 类型提示的 `VersionSection`。
- [x] 实现带 IDE 类型提示的 `SoCInfoSection`。
- [x] 实现带 IDE 类型提示的 `AICoreSpecSection`。
- [x] 将暂未类型化的 Section 保存为通用 `PlatformConfigSection`。
- [x] 暂不专门解释 intrinsic dtype map 中的数字键，但必须完整保留原始数据。
- [x] 实现只读的 `CANNPlatformConfig`，已知 Section 属性和内部 Section 注册表引用同一对象。
- [x] 实现 `CANNPlatformConfig.from_file(path)`。
- [x] 实现 `raw_section(name)`，使未知或尚未类型化的 Section 仍然可读。
- [x] 使用标准库 `configparser`，关闭 interpolation，并保留原始键名大小写。
- [x] 对缺少必要 Section、必要字段、非法整数等情况给出项目自己的明确异常。

## 3. CANN 环境与 NPU 名称发现

- [x] 实现 CANN 根目录发现，依次考虑 `ASCEND_HOME_PATH`、`ASCEND_TOOLKIT_HOME`、`ASCEND_TOOLKIT_LATEST_HOME` 和标准安装路径。
- [x] 验证候选目录确实包含当前架构对应的 `data/platform_config`。
- [x] 将主机架构规范化为 `aarch64` 或 `x86_64`。
- [x] 实现 `detect_npu_name()`，延迟导入 `acl` 并调用 `acl.get_soc_name()`。
- [x] 缓存首次成功探测到的 NPU 名称。
- [x] 正确处理 ACL 不存在、返回空值或调用失败的情况。
- [x] 实现 `list_npu_names()`，列出当前 CANN 安装中可读取的配置名称。
- [x] 显式提供 `npu_name` 时不得导入或调用 ACL。

## 4. 配置加载与缓存

- [x] 实现 `platform_config(npu_name=None)`。
- [x] 不传 `npu_name` 时使用缓存的自动探测结果。
- [x] 按规范化后的 NPU 名称缓存 `CANNPlatformConfig` 对象。
- [x] 同一进程内重复查询同一 NPU 名称时返回同一个配置对象。
- [x] CANN 根目录和架构在默认运行时上下文中只解析一次。
- [x] `CANNPlatformConfig.from_file()` 不进入默认全局缓存。

## 5. 配置对象便利接口与单位转换

- [x] 实现统一的大小单位转换函数。
- [x] 默认单位为 bytes；支持 `kb`/`kib` 和 `mb`/`mib`，均采用 1024 进制。
- [x] 实现 `CANNPlatformConfig.ub_size(unit="bytes")`，读取 `AICoreSpec.ub_size`。
- [x] 实现 `CANNPlatformConfig.l0_a_size(unit="bytes")`。
- [x] 实现 `CANNPlatformConfig.l0_b_size(unit="bytes")`。
- [x] 实现 `CANNPlatformConfig.l0_c_size(unit="bytes")`。
- [x] 实现 `CANNPlatformConfig.l1_size(unit="bytes")`。
- [x] 实现 `CANNPlatformConfig.l2_size(unit="bytes")`。
- [x] 实现 `CANNPlatformConfig.ai_core_count()`。
- [x] 原始 Section 属性始终保持 INI 的基础值，不受便利方法的单位参数影响。

## 6. 模块级 Python API

- [x] 导出 `CANNPlatformConfig` 和需要公开的 Section 类型。
- [x] 实现模块级 `ub_size(npu_name=None, unit="bytes")`。
- [x] 实现模块级 `l0_a_size(npu_name=None, unit="bytes")`。
- [x] 实现模块级 `l0_b_size(npu_name=None, unit="bytes")`。
- [x] 实现模块级 `l0_c_size(npu_name=None, unit="bytes")`。
- [x] 实现模块级 `l1_size(npu_name=None, unit="bytes")`。
- [x] 实现模块级 `l2_size(npu_name=None, unit="bytes")`。
- [x] 实现模块级 `ai_core_count(npu_name=None)`。
- [x] 模块级便利函数只负责获取对应 `CANNPlatformConfig` 并转发调用。

## 7. CLI

- [x] 使用标准库 argparse 实现 `cann-cann` 命令，不增加运行时依赖。
- [x] 实现 `cann-cann npu-name`。
- [x] 实现 `cann-cann list-npu-names`。
- [x] 实现大小查询 `UB`、`L0A`、`L0B`、`L0C`、`L1` 和 `L2`，查询名称大小写不敏感。
- [x] 实现 `AI_CORE_COUNT` 查询。
- [x] 支持 `--npu-name` 和 `--unit`。
- [x] 支持 `--kb`、`--kib`、`--mb`、`--mib` 快捷选项。
- [x] CLI 捕获项目异常并输出简洁、可操作的错误信息，不默认显示 traceback。
- [x] CLI 实现调用公开 Python API，不复制配置查询逻辑。
- [x] 暂不实现任意 INI 字段查询、JSON/YAML 输出以及 `--soc` 等兼容别名。

## 8. 测试数据与自动化测试

- [x] 从真实配置精简出 Ascend 910B fixture。
- [x] 从真实配置精简出 `Ascend910_9392` fixture。
- [x] 从真实配置精简出 Ascend 950PR fixture。
- [x] 从真实配置精简出 Ascend 950DT fixture。
- [x] fixture 保留代表性的未知 Section 或数字键，验证原始数据不会丢失。
- [x] 测试类型化 Section 属性、可选字段和缺失字段错误。
- [x] 测试 `raw()`、`raw_items()` 和 `raw_section()`。
- [x] 测试 CANN 根目录和架构发现，不依赖本机真实安装。
- [x] 使用假的 `acl` 模块测试成功、缺失、空返回值和异常情况。
- [x] 测试显式 `npu_name` 不触发 ACL。
- [x] 测试当前 NPU 名称缓存和配置对象缓存。
- [x] 测试所有大小单位转换和非法单位。
- [x] 测试模块级函数与配置对象方法结果一致。
- [x] 测试全部 CLI 命令、参数和错误退出码。

## 9. 文档与发布检查

- [x] 完善 README 中的项目定位、安装方式和 CANN 环境前提。
- [x] 添加 Python 快速开始、指定 `npu_name` 和配置对象高级用法。
- [x] 添加 CLI 示例和单位语义说明。
- [x] 说明 NPU 名称、设备实例、SoC version 和 CANN version 的概念边界。
- [x] 说明首版重点测试的 NPU 系列及未设置硬编码型号白名单。
- [x] 在干净环境中安装构建出的 wheel，验证 `import cann_cann` 和 `cann-cann --help`。

## 10. 统一收尾

- [x] 检查并统一公共 API 命名、类型标注、docstring 和错误信息。
- [x] 检查并解决并行开发产生的集成问题。
- [x] 运行 Ruff format 和 lint。
- [x] 运行完整 pytest 测试套件。
- [x] 构建并检查 wheel 与 sdist。
- [x] 根据实际完成情况更新本文件中的勾选状态。

# cann-cann 初版实现微调

初版完成后，将讨论中确认但不影响整体架构的改进记录在这里，逐项实现和验证。

## 11. 简化异常设计

- [x] 精简公开异常层级，使普通用户只需理解 `CannCannError`，需要恢复时再捕获少量环境或配置子类。
- [x] 统一异常语义：调用参数和对象构造错误使用 `ValueError`，CANN 环境及平台配置错误使用领域异常。
- [x] 让平台配置文件缺失同时兼容 `PlatformConfigError` 和 `FileNotFoundError`，并携带标准文件异常信息。
- [x] 同步公共导出、README 和测试，并通过 Ruff、完整 pytest 及构建检查。

## 12. 中文易用性与 CLI 微调

- [x] 将 README、公共 API docstring、CLI 帮助和用户可见错误信息调整为简明、自然、通顺的中文；保留代码标识符和 NPU、CANN、ACL、AI Core、UB、L0A 等通用技术术语，避免生硬直译和不必要的技术黑话。
- [x] 为 CLI 的 `AI_CORE_COUNT` 查询增加 `cores` 和 `ai-cores` 别名，明确这些别名均表示 `ai_core_cnt`，并补充帮助文本与测试。
- [x] 使用 Python 3.10 兼容的内部联合类型规范 CLI 查询结果及输出函数，完成 Ruff、pytest 和构建验证。
- [x] 将顶层 NPU 名称接口统一为 `npu_name()` 和 `all_npu_names()`，CLI 同步使用 `npu-name` 和 `all-npu-names`，避免仅靠单复数区分不同语义。
- [x] 增加 `ccann` 作为 `cann-cann` 的简短命令别名，使帮助信息显示实际调用的命令名，并同步 README、测试和构建配置。

## 13. 显存大小查询

- [x] 从 `[SoCInfo]` 的 `memory_size` 提供 `CANNPlatformConfig.memory_size()` 和顶层 `cann_cann.memory_size()`，保持原始属性以字节表示并复用配置缓存与领域异常。
- [x] CLI 增加 `memory` 查询及 `HBM` 别名，大小单位增加 `gb`/`gib` 与 `--gb`/`--gib`，保持既有 1024 进制和大小写不敏感规则。
- [x] 同步中文 README、CLI 帮助和测试，覆盖字段缺失、单位换算、两个 CLI 名称与模块级转发，并通过 Ruff、pytest 和构建检查。
