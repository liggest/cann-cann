# cann-cann 新特性实现待办

目标：在保持现有 Python API 和 CLI 兼容的基础上，改善 NPU 型号输入、查询项帮助和
无参数调用体验，并补充核心数量、CANN 版本及主机环境信息查询。

## 1. NPU 名称规范化与常用别名

- [x] 实现公开的纯字符串函数 `normalize_npu_name(name)`：去除首尾空白、以大小写不敏感
  方式展开固定别名、规范已有的 `Ascend` 前缀，但不猜测普通名称的前缀；该函数不访问
  文件系统或 CANN 环境。
- [x] 实现公开的环境解析函数 `resolve_npu_name(name)`：先调用 `normalize_npu_name()`，再在
  当前安装的标准配置名称中做大小写不敏感匹配，并返回配置文件使用的实际名称。
- [x] `platform_config()` 及所有接受 `npu_name` 参数的 Python API 和 CLI 统一调用
  `resolve_npu_name()`，避免在各入口重复实现别名和配置匹配逻辑。
- [x] 支持以下常用别名，并将其解析为标准配置名称：
  - `A2` → `Ascend910B3`
  - `A3` → `Ascend910_9382`
  - `910C` → `Ascend910_9382`
  - `A5` → `Ascend950PR_9589`
  - `950` → `Ascend950PR_9589`
  - `A5DT` → `Ascend950DT_9582`
  - `950DT` → `Ascend950DT_9582`
- [x] `resolve_npu_name()` 对普通输入先匹配原名，再尝试补全 `Ascend` 前缀；例如将
  `910B3` 解析为 `Ascend910B3`，同时保持 `Kirin9030` 等无前缀标准名称可用，匹配规则
  同样大小写不敏感。
- [x] `normalize_npu_name()` 对已经带有 `Ascend` 前缀的输入不重复添加前缀，并将前缀
  规范为 `Ascend`；未知型号的后缀不擅自改写字符大小写。
- [x] `resolve_npu_name()` 以当前安装中实际存在的配置文件名作为最终标准名称，保证在
  大小写敏感的文件系统上能够正确加载；无法匹配时沿用平台配置文件不存在的领域异常语义。
- [x] 保持自动探测和枚举语义不变：`npu_name()` 返回 ACL 探测结果，
  `all_npu_names()` 只列出当前 CANN 安装中实际存在的标准配置名称，不额外列出别名。
- [x] 保持配置缓存按解析后的标准名称命中，使同一型号的别名、无前缀名称和标准名称
  返回同一个 `CANNPlatformConfig` 对象。
- [x] 将 `normalize_npu_name()` 和 `resolve_npu_name()` 加入包的公开导出并补充类型标注；
  分别测试其不依赖环境和依赖已安装配置的边界。

## 2. CANN 根目录与功能目录发现解耦

- [x] 调整 `find_cann_home()`，只负责按既有环境变量和默认路径优先级寻找确实存在的 CANN
  根目录，不再要求候选目录包含 `data/platform_config`。
- [x] 环境变量指向不存在的目录时继续检查下一个候选；一旦选中存在的根目录，各具体功能
  再独立验证所需文件，避免因缺少某一组件而误选另一套安装。
- [x] 保留 `platform_config_directory()` 作为路径构造函数，并在平台配置查询入口单独验证
  目录存在；错误中明确指出缺失的平台配置目录。
- [x] CANN 安装信息查询单独验证 `{arch}-linux` 下的安装信息文件，不依赖平台配置目录。
- [x] `ascend_home()` 只依赖根目录发现；`cann_version()` 只依赖根目录、主机架构及安装
  信息文件；NPU 配置查询才依赖平台配置目录。
- [x] 更新环境发现测试，分别覆盖“根目录存在但缺少平台配置”“安装信息存在但缺少平台
  配置”和“平台配置存在但缺少安装信息”，验证各接口互不产生无关依赖。

## 3. CLI NPU 参数与查询别名

- [x] 为 `--npu-name` 增加 `-n` 和 `--soc` 两个等价选项，三者共用同一参数值和校验逻辑。
- [x] 支持在 query 前后使用 NPU 参数，例如 `ccann -n A5 UB` 和
  `ccann UB --soc A5`。
- [x] `-n` 只是 `--npu-name` 的参数简写，不改变 query 规则；`ccann -n A5` 不作为
  `npu-name` 查询的简写。
- [x] 为 CLI query 增加 `soc`，作为 `npu-name` 的别名。
- [x] 为 CLI query 增加 `all-socs`，作为 `all-npu-names` 的别名。
- [x] `npu-name`/`soc` 和 `all-npu-names`/`all-socs` 仍不得与 `-n`、`--npu-name`
  或 `--soc` 同时使用，并提供包含实际选项名的清晰错误信息。

## 4. bytes 单位别名

- [x] 为大小单位 `bytes` 增加大小写不敏感的 `b` 别名，Python API 的 `unit="b"` 和
  CLI 的 `--unit b` 均按字节返回。
- [x] 更新公开 `SizeUnit` 类型和单位转换映射；保留 `bytes` 作为默认单位及标准展示名称。
- [x] 不新增单独的 `--b` 快捷选项，避免与现有 `--kb`、`--mb` 等选项形成含义不清的
  单字母参数。

## 5. Cube、Vector 与 NPU 架构配置项

- [x] 在 `CANNPlatformConfig` 上实现 `cube_core_count()`，读取
  `SoCInfo.cube_core_cnt`；字段不存在时给出与 `ai_core_count()` 一致的配置错误。
- [x] 在 `CANNPlatformConfig` 上实现 `vector_core_count()`，读取
  `SoCInfo.vector_core_cnt`；字段不存在时给出与 `ai_core_count()` 一致的配置错误。
- [x] 增加模块级 `cube_core_count(npu_name=None)` 和
  `vector_core_count(npu_name=None)`，仅负责加载配置并转发对象方法。
- [x] 将两个新函数加入包的公开导出和类型化接口。
- [x] 在 `CANNPlatformConfig` 上实现 `npu_arch()`，读取已经类型化的
  `VersionSection.npu_arch`；字段不存在时给出一致的配置错误。
- [x] 增加模块级 `npu_arch(npu_name=None)` 并加入公开导出，模块级函数只负责加载配置并
  转发对象方法。
- [x] CLI 增加 `cube-cores` 查询及 `c-cores` 别名。
- [x] CLI 增加 `vector-cores` 查询及 `v-cores` 别名。
- [x] CLI 增加 `npu-arch` 查询；核心数量和 NPU 架构查询均拒绝所有单位选项。

## 6. 聚合 cores 查询

- [x] 将 `cores` 从 `ai_core_count()` 的别名改为独立的聚合查询；保留
  `ai-core-count`、`ai_core_count` 和 `ai-cores` 对单个 AI Core 数量的既有查询能力。
- [x] `cores` 使用同一次平台配置加载依次查询 AI Core、Cube Core 和 Vector Core 数量，
  避免重复解析配置或重复探测 NPU。
- [x] `cores` 严格按以下标签及顺序逐行输出：

  ```text
  ai-cores: xx
  cube-cores: xx
  vector-cores: xx
  ```

- [x] 为 CLI 结果建立能够表达多行带标签结果的内部结构或专用输出路径，不把聚合格式
  拼接逻辑放入公开 Python API。
- [x] `cores` 拒绝所有单位选项；某个核数字段缺失时仍输出全部三行，并将该项显示为小写
  `none`，例如 `vector-cores: none`，使输出键和行数保持稳定。
- [x] Python 配置对象上的三个单项查询仍返回 `int`，字段缺失时仍抛出配置错误；聚合查询
  内部直接读取三个类型化字段，将缺失值保留为 Python `None`，只在 CLI 文本输出时格式化
  为 `none`。

## 7. CANN 安装信息与版本

- [x] 实现 CANN 安装信息文件发现：在已发现的 CANN 根目录下查找
  `{arch}-linux/ascend_toolkit_install.info`，不存在时回退到同目录的
  `ascend_ops_install.info`。
- [x] 两个文件同时存在时始终优先读取 `ascend_toolkit_install.info`。
- [x] 实现安装信息解析，只读取 `version` 字段；允许常见的 `key=value` 格式、字段两侧
  空白及带引号的值，同时不向调用方暴露可变解析结果。
- [x] 实现公开、只读的 `CANNInstallInfo` 数据对象，至少保存 `version: str`、组件类型
  （`toolkit` 或 `ops`）及安装信息文件的规范化 `path: Path`。
- [x] 实现模块级 `cann_install_info()` 返回 `CANNInstallInfo`；`cann_version()` 只负责返回
  `cann_install_info().version`。
- [x] 回退只由文件是否存在决定：toolkit 文件存在但不可读、无法解析或缺少 `version` 时
  直接报告该文件错误，不再静默读取 ops 文件。
- [x] 对两个安装信息文件均不存在、文件不可读、内容无法解析或缺少非空 `version` 字段
  的情况给出明确的 `CannCannError` 子类异常，并包含所检查的文件路径。
- [x] 实现模块级 `cann_version()`，返回安装信息中的 CANN `version`；不要与
  `cann_cann.__version__`（本 Python 包版本）混淆。
- [x] 对默认运行时上下文中的 CANN 根目录、架构和 CANN 版本结果进行缓存，并确保测试
  可以可靠清理缓存。
- [x] CLI 增加 `cann-version` 查询；该查询不接受 NPU 名称或单位选项。

## 8. 主机与 CANN 环境信息

- [x] 实现模块级 `host_arch()`，返回现有架构规范化逻辑得到的 `aarch64` 或 `x86_64`；
  不依赖 ACL、CANN 根目录或平台配置加载。
- [x] 实现模块级 `ascend_home()`，以 `Path` 返回现有 CANN 根目录发现逻辑得到的规范化
  绝对路径；CLI 将其直接格式化为路径字符串。
- [x] 实现模块级 `os_name()`，使用标准库 `platform.freedesktop_os_release()` 读取
  `NAME` 和 `VERSION`，返回 `"{NAME} {VERSION}"`；正确处理引号和转义，且拼接结果
  不含多余空格。
- [x] 沿用标准库行为，优先读取 `/etc/os-release`，不存在时回退到
  `/usr/lib/os-release`；两个文件都不存在或无法读取时转换为带明确路径说明的环境领域异常。
- [x] `os_name()` 在 `VERSION` 不存在或为空时只返回 `NAME`；文件不存在、不可读或
  `NAME` 缺失时给出明确的环境领域异常。
- [x] 将 `host_arch()`、`ascend_home()` 和 `os_name()` 加入包的公开导出。
- [x] CLI 增加 `arch` 查询并映射到 `host_arch()`；帮助中明确其含义为主机处理器架构，
  与读取平台配置的 `npu-arch` 区分。
- [x] CLI 增加 `ascend-home` 查询，以及 `cann-home`、`ascend-root`、`cann-root`、
  `ascend-path` 和 `cann-path` 别名。
- [x] CLI 增加 `os-name` 查询及 `os` 别名。
- [x] 上述环境查询均不接受 NPU 名称或单位选项，并通过公开 Python API 获取结果。

## 9. CLI 查询注册表、分派与参数校验

- [x] 建立只读的内部 `QuerySpec` 数据对象，集中记录标准名称、别名、简短说明、查询类别
  和对应的公开 API 名称；查询类别至少区分大小、配置单值、聚合及全局环境信息。
- [x] 使用一份 `QuerySpec` 列表生成“规范化 query/别名 → QuerySpec”的查找表和帮助文本，
  确保新增别名时不会出现“能够执行但帮助未列出”或相反的情况。
- [x] 注册表只描述查询，不实现平台配置或环境读取；`_run()` 根据查询类别统一执行参数
  校验，再调用注册表指定的公开 Python API。`cores` 等特殊聚合项使用明确的专用分支。
- [x] 保持 query 对大小写不敏感，并继续将连字符和下划线视为等价写法。
- [x] 按查询类别统一校验参数：大小查询可接受 NPU 和单位，核心数及 `npu-arch` 等平台
  配置单值查询只接受 NPU，NPU 枚举、版本及环境查询不接受 NPU 或单位。
- [x] 未知 query 继续输出简洁错误并返回退出码 2；错误中保留用户原始输入。
- [x] 确保新增逻辑不复制 Python API 中的平台配置、环境发现或安装信息解析实现。

## 10. CLI 输出协议、退出码、帮助与无参数行为

- [x] 固定文本输出协议：单值查询只向 stdout 输出值；列表每项一行；聚合查询稳定使用
  小写 kebab-case 的 `key: value`；缺失聚合值输出 `none`；成功时 stderr 为空。
- [x] 所有预期错误只向 stderr 输出一行 `错误：<信息>`，stdout 为空且默认不显示 traceback。
- [x] 区分退出码：成功为 0，CANN 环境、ACL、安装信息或平台配置等领域错误为 1，未知
  query、非法选项组合、非法名称或单位等命令行输入错误为 2；argparse 自身错误保持 2。

- [x] 将 `query` 改为可选位置参数，以便程序自行处理无 query 的情况。
- [x] `cann-cann` 或 `ccann` 在既没有 query 也没有其他选项时返回退出码 0，并逐行输出：
  当前调用命令及 cann-cann 包版本、简短 usage、使用当前命令 `-h` 查看帮助的提示。
- [x] 无 query 但带有 `-n`、`--soc`、`--npu-name` 或单位选项时视为参数错误，说明必须
  提供 query 并返回退出码 2；不得静默忽略选项。
- [x] 无参数输出和 `-h` 帮助均使用实际调用名，保证 `cann-cann` 与 `ccann` 显示各自名称。
- [x] 整理 `query` 帮助文本，每种标准查询单独一行，并在同一行列出别名和简洁中文说明。
- [x] 帮助完整列出 `UB`、`L0A`、`L0B`、`L0C`、`L1`、`L2`、`memory`、
  `ai-cores`、`cube-cores`、`vector-cores`、`cores`、`npu-arch`、`npu-name`、
  `all-npu-names`、`cann-version`、`arch`、`ascend-home` 和 `os-name`；每行同时展示
  对应别名，固定别名不得只存在于代码或 README 中。
- [x] 将原 epilog 中关于 `ai-cores` 的说明并入 query 列表，移除独立 epilog。
- [x] 在选项帮助中说明 NPU 常用别名、可省略 `Ascend` 前缀以及 `-n`/`--soc` 的含义；
  内容过长时用简短示例配合 `docs/usage.md` 详细说明。

## 11. 自动化测试

- [x] 分别测试 `normalize_npu_name()` 的纯字符串规则和 `resolve_npu_name()` 的已安装配置
  匹配，确认前者完全不访问环境或文件系统。
- [x] 测试每个固定 NPU 别名、大小写变体、首尾空白、无 `Ascend` 前缀和完整标准名称。
- [x] 测试别名只解析到实际标准配置，未知名称保持明确的配置不存在错误，路径分隔符等非法
  输入仍被拒绝。
- [x] 测试别名、无前缀名称和标准名称共享同一个配置缓存对象，且显式名称仍不触发 ACL。
- [x] 测试 `all_npu_names()` 只返回实际配置文件名，不包含固定别名。
- [x] 测试 `-n`、`--npu-name`、`--soc` 在 query 前后的等价行为及互斥/重复传参错误。
- [x] 测试 `soc`、`all-socs`、`c-cores`、`v-cores` 和全部环境查询别名。
- [x] 测试 Python API 和 CLI 对 `b`/`B` 单位的支持，以及非法单位错误。
- [x] 测试 Cube 和 Vector 核数量的对象方法、模块级函数、CLI 输出及缺失字段错误。
- [x] 测试 `npu_arch()` 的对象方法、模块级函数、CLI 输出、型号别名及缺失字段错误。
- [x] 测试 `cores` 的三行标签、顺序、数值、单位参数错误，并验证任意字段缺失时对应行
  输出 `none`、其他行仍正常输出。
- [x] 为两类安装信息文件准备最小 fixture，测试 toolkit 优先、ops 回退、空白与引号、缺失
  文件、不可读文件、缺少/空 `version` 和畸形内容。
- [x] 测试 `CANNInstallInfo` 的只读性、组件类型和来源路径，验证 `cann_install_info()`、
  `cann_version()` 与包 `__version__` 相互独立，且 CLI 输出 CANN 安装版本。
- [x] 测试 `host_arch()` 的两种标准架构、已支持别名和不支持架构错误。
- [x] 测试 `ascend_home()` 的环境变量优先级、标准目录回退、规范化返回值和找不到安装错误。
- [x] 替换 `platform.freedesktop_os_release()` 的返回值或异常，测试 `os_name()` 的正常值、
  缺少 VERSION、缺少 NAME 及两个标准路径均不可读时的错误转换；引号、转义和路径回退
  由标准库负责，不重复测试标准库实现，也不依赖测试主机的真实发行版。
- [x] 测试两个 CLI 入口的无参数输出、退出码、实际命令名，以及无 query 但带选项时的错误。
- [x] 对帮助文本做结构断言，确认每个标准 query 各占一行、别名与说明齐全且不再出现旧 epilog。
- [x] 分别断言成功、领域错误和命令行输入错误的 stdout、stderr 及退出码，锁定 CLI 协议。

## 12. 文档与兼容性

- [x] 精简 README，使其一目了然地展示项目定位、安装方式、最常用的 Python/CLI 示例和
  指向详细指南的链接；不要在 README 罗列全部别名、查询项和异常规则。
- [x] 新增 `docs/usage.md` 详细使用指南，集中说明 NPU 别名与名称解析、完整 CLI 查询表、
  Python API、单位、聚合输出、环境发现、安装信息来源和错误码。
- [x] README 中仅用少量代表性示例展示 `-n`/`--soc`、NPU 简称及新增聚合查询，其余内容
  链接到 `docs/usage.md`。
- [x] 说明 `npu_name()`、`cann_version()`、`cann_cann.__version__`、`host_arch()`、
  `npu_arch()`、`ascend_home()` 和 `os_name()` 分别表示设备、CANN 安装、Python 包、
  主机架构、NPU 架构及主机环境信息；详细概念说明放入使用指南。
- [x] 记录 `cores` 从 `ai_core_count()` 别名变为聚合输出的 CLI 行为变更，并推荐需要单值的
  脚本改用 `ai-cores`。
- [x] 检查既有公开 API、CLI 查询名及输出保持兼容；除明确变更的 `cores` 外，不移除已有别名。
- [x] 同步所有新增公共 API 的中文 docstring、类型标注、`__all__` 和用户可见错误信息。

## 13. 验证与收尾

- [x] 运行 Ruff format 和 lint。
- [x] 运行完整 pytest 测试套件。
- [x] 构建 wheel 和 sdist，并检查新增模块、类型信息及文档均正确进入发布包。
- [x] 在干净环境安装 wheel，冒烟验证 Python 新接口、`cann-cann --help`、`ccann` 无参数
  输出及不依赖真实 ACL 的显式 NPU 查询。
- [x] 根据实际完成情况更新本文件中的勾选状态。

## 14. CLI 版本、usage 与错误指引微调

在既有 CLI 协议基础上统一产品名称并改善基础使用提示。本章只调整展示和命令输入错误；
领域错误的语义及退出码保持不变。

### 14.1 统一版本与基础指引

- [x] 提取统一的版本文本函数，固定返回 `cann-cann <package-version>`，只从
  `cann_cann.__version__` 读取版本号。
- [x] `cann-cann --version` 与 `ccann --version` 均只输出统一版本文本，不再根据入口名
  显示为两个不同程序。
- [x] 将 `_print_no_query()` 重构为可复用的基础指引输出函数，接收 parser 和输出流，依次
  输出 `parser.format_usage()` 与使用实际入口名查看 `-h` 的提示；基础指引本身不含版本号。
- [x] 无参数成功调用先输出统一版本文本，再将基础指引写入 stdout，保持 stderr 为空并
  返回 0；版本行固定为 `cann-cann`，usage 与 `-h` 提示仍使用实际调用的入口名。
- [x] `_VersionAction` 只复用统一版本文本，不额外输出 usage 或帮助提示。

无参数调用 `ccann` 的预期结构：

```text
cann-cann <package-version>
usage: ccann ...
使用 ccann -h 查看帮助
```

### 14.2 恢复 argparse 自动生成 usage

- [x] 移除 `_parser()` 中手写的 `usage="%(prog)s QUERY [选项]"`，由 argparse 根据位置
  参数、选项和互斥组自动生成 usage，避免新增选项后遗漏同步。
- [x] 保持 query 为可选位置参数，使自动 usage 使用 `[QUERY]`，与无参数行为一致。
- [x] 为 `--unit` 设置 `metavar="UNIT"`，避免 usage 展开全部 choices。
- [x] 自动 usage 至少展示 `-h`、`-v`、`-n NAME`、`--unit UNIT`、`--kb`、`--mb`、
  `--gb` 和 `[QUERY]`；参数别名和较少使用的单位无需在 usage 中重复展开。
- [x] `parser.format_usage()`、完整 `-h` 帮助和错误后的基础指引共用同一个 parser，不在
  其他函数中维护第二份 usage 文本。

预期形式近似如下，具体换行由 argparse formatter 决定：

```text
usage: ccann [-h] [-v] [-n NAME]
             [--unit UNIT | --kb | --mb | --gb] [QUERY]
```

### 14.3 合并单位快捷选项

- [x] 将 `--kb`/`--kib`、`--mb`/`--mib`、`--gb`/`--gib` 分别注册为三个 argparse
  action，每对选项设置相同的规范化单位值。
- [x] 完整帮助中每对快捷项只占一行，例如 `--kb, --kib  以 kb 输出`；采用 argparse
  默认别名分隔样式，不为斜杠样式引入专用 formatter。
- [x] 删除三条“同 --*b”帮助文案，并保持六个参数的既有行为。
- [x] `--unit` 继续接受完整单位集合及大小写输入；CLI 只显示简洁说明，完整单位语义保留在
  `docs/usage.md`。

### 14.4 为命令输入错误追加基础指引

- [x] 建立统一的命令输入错误输出函数：先向 stderr 输出一行 `错误：<信息>`，空一行后
  输出基础指引；stdout 保持为空，退出码保持 2。
- [x] `main()` 捕获的 `ValueError` 使用统一错误输出，包括未知 query、非法参数语义、
  不允许的选项组合，以及无 query 但带查询选项等情况。
- [x] `_ArgumentParser.error()` 产生的 argparse 错误也使用同一结构，包括非法 choice、
  缺少选项值、重复 NPU 选项和无法识别的参数。
- [x] CANN、ACL、平台配置和安装信息等领域错误仍只输出错误并返回 1，不追加基础指引，
  避免把环境故障误导成命令写法问题。
- [x] `-h`、`--version` 和正常查询的成功输出不受错误指引逻辑影响。

使用 `ccann unknown` 时，stderr 的预期结构：

```text
错误：未知的查询项：unknown

usage: ccann ...
使用 ccann -h 查看帮助
```

### 14.5 测试、文档与验收

- [x] 测试两个入口的 `-v`/`--version` 均只输出 `cann-cann <package-version>`。
- [x] 测试无参数输出的统一产品名、实际入口 usage 和实际入口 `-h` 提示。
- [x] 测试自动 usage 包含重要选项、常用单位快捷项和 `[QUERY]`，且不再使用旧的手写文本。
- [x] 测试帮助将三对单位快捷项各合并为一行，六个参数均正确设置对应单位。
- [x] 分别覆盖 argparse 错误和 `main()` 中的退出码 2 错误，断言 stdout 为空，stderr
  包含错误行、空行和基础指引，并覆盖两个实际入口名。
- [x] 保留领域错误返回 1 且不追加基础指引的回归测试。
- [x] 更新 `docs/usage.md` 中的版本、无参数、usage、单位快捷项和错误输出说明；README
  只在现有核心示例受影响时做最小调整。
- [x] 运行 Ruff format、Ruff lint、完整 pytest 和全仓 pre-commit。
- [x] 构建 wheel 与 sdist，并在隔离安装的 wheel 中验证两个入口的版本、无参数、帮助和
  退出码 2 错误指引。
- [x] 由主 Agent 检视实现及验证结果后，再统一更新本章状态。

## 15. CLI 主机架构名称与显式 NPU 型号查询微调

本章只调整 CLI 查询名称及 `npu-name` 与显式型号选项组合时的语义；Python API、型号
解析规则、自动探测行为和其他查询的参数约束保持不变

### 15.1 将 `host-arch` 设为主查询名

- [x] 将主机处理器架构的 CLI 标准查询名由 `arch` 改为 `host-arch`，继续调用公开的
  `host_arch()`，返回值与退出码不变
- [x] 保留 `arch` 作为 `host-arch` 的兼容别名；大小写不敏感及连字符、下划线等价规则
  继续由统一查询注册表提供
- [x] 完整帮助以 `host-arch` 为主名称，并在同一行将 `arch` 显示为别名，使 CLI 与
  Python API 的命名主次一致

### 15.2 允许显式型号与 `npu-name` 查询组合

- [x] 不带型号选项执行 `npu-name` 或 `soc` 时保持现有行为，继续调用 `npu_name()` 并通过
  ACL 返回当前环境的 NPU 型号
- [x] 带 `-n NAME`、`--npu-name NAME` 或 `--soc NAME` 执行 `npu-name` 或 `soc` 时，调用
  公开的 `resolve_npu_name(NAME)`，输出当前 CANN 包配置中实际存在的标准名称，不调用 ACL
- [x] 显式输入可以使用固定简称、大小写变体、无 `Ascend` 前缀或标准名称，并完全复用
  `resolve_npu_name()` 的既有解析与错误语义，不在 CLI 中复制名称匹配逻辑
- [x] 只为 `npu-name` 查询及其 `soc` 别名放开型号选项；`all-npu-names`、`cann-version`、
  `host-arch` 等其他全局查询仍拒绝型号选项，所有非大小查询仍拒绝单位选项
- [x] 重复使用多个型号选项的 argparse 错误规则保持不变；未知或当前 CANN 包中不存在的
  显式型号继续作为领域错误返回退出码 1

### 15.3 测试、文档与验收

- [x] 测试 `host-arch` 与 `arch` 输出一致且都只调用 `host_arch()`；帮助文本以
  `host-arch` 为主名称并展示 `arch` 别名
- [x] 测试 `npu-name` 和 `soc` 在不带型号选项时仍调用 `npu_name()`，且不调用
  `resolve_npu_name()`
- [x] 覆盖三种型号选项、query 前后位置、固定简称和标准名称，确认显式 `npu-name` 查询只
  调用 `resolve_npu_name()` 并输出其标准名称，不调用 `npu_name()`
- [x] 测试显式型号无法解析时返回退出码 1，单位选项、重复型号选项及其他全局查询的既有
  参数错误与基础指引保持不变
- [x] 更新 `docs/usage.md` 的 CLI 查询表与必要示例，说明 `host-arch`/`arch` 的主次以及
  `ccann -n A5 npu-name` 返回标准配置名称；README 仅在核心示例确有必要时调整
- [x] 运行 Ruff format、Ruff lint、完整 pytest、全仓 pre-commit，并构建 wheel 与 sdist
- [x] 子 Agent 完成实现后不得勾选本章待办；由主 Agent 检视代码、测试、文档及验证结果，
  确认符合本章方案后再统一标记完成

## 16. AI Agent 快速上手技能

为安装 cann-cann 后的 AI Agent 提供比 `-h` 更直接、可执行的快速上手说明，减少枚举查询项、
试探参数组合和定位包内文档的成本。本章只提供静态使用指导，不增加 CANN 或 NPU 探测行为

### 16.1 技能设计与打包

- [x] 在 `src/cann_cann/skills/cann-cann/SKILL.md` 保留唯一的技能源文件，使用准确的 YAML
  frontmatter 描述适用场景，并作为 `cann_cann` 包资源随 wheel 和 sdist 发布；不在
  `.agents/skills` 维护第二份副本
- [x] 技能保持自包含和易于快速读取，首先引导 Agent 直接尝试当前型号、大小、核心和 CANN 版本
  查询，再给出指定型号、架构及主机信息等代表性命令
- [x] 说明会影响 Agent 正确调用的规则：显式型号与简称、大小单位、适用 `-n` 的查询、稳定输出、
  退出码及 CLI/Python API 的选择；将环境准备移到失败排查，不暴露 ACL 等内部实现概念
- [x] 增加公开只读 API 读取内置技能文本，使用标准库资源接口定位安装包内文件，不依赖源码树路径，
  并同步公开导出、中文 docstring 和类型标注

### 16.2 `skill` 查询项

- [x] 在集中式查询注册表中增加全局查询项 `skill`，由 `cann-cann skill` 和 `ccann skill` 原样
  输出内置技能，成功时 stdout 只包含技能文本且退出码为 0
- [x] `skill` 不接受 NPU 名称或单位选项，复用全局查询的参数校验、错误输出和退出码，不建立专用
  分派分支，也不复制技能内容到 CLI 模块
- [x] 将 `skill` 纳入 `-h` 查询列表，并在 README 安装位置和 `docs/usage.md` 中用一句话提供
  AI Agent 快速上手入口，详细用法仍以技能本体和使用指南各自的目标读者为准

### 16.3 pip 安装完成提示

- [x] 核实 PEP 517、wheel 与 pip 是否提供由项目声明的标准安装后消息机制，要求同时适用于从
  PyPI wheel、wheel 缓存和 sdist 构建后的安装
- [x] 未发现同时适用于 PyPI wheel、wheel 缓存和 sdist 安装的标准安装后消息机制，因此未引入
  仅在部分安装路径生效的构建输出、传统 `setup.py` 安装钩子、`.pth` 启动副作用或定制 pip；
  已通过 PyPI/README 安装说明和 CLI 帮助暴露 `cann-cann skill` 作为安全替代

### 16.4 测试与验收

- [x] 测试公开 API 返回完整技能文本，frontmatter 的名称与描述有效，关键调用规则和命令存在
- [x] 测试 `skill` 查询通过公开 API 输出内容、拒绝 NPU 与单位选项，并验证帮助列表包含该查询
- [x] 构建 wheel 与 sdist，检查技能资源进入两类产物；在隔离环境安装 wheel 后运行
  `cann-cann skill`，确认无需源码树或真实 CANN 环境即可使用
- [x] 运行 Ruff format、Ruff lint、完整 pytest、全仓 pre-commit 和无源码构建检查，验证通过
