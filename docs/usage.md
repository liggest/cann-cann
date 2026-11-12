# cann-cann 使用指南

cann-cann 是一个轻量的命令行工具兼 Python 库，支持用一行代码快速查看当前环境上的 NPU 型号、硬件参数、CANN 版本、操作系统信息等

## 快速开始

### 1. 准备环境并安装

cann-cann 支持在安装了 CANN 和 Python >= 3.10 的环境上运行，使用前需要加载 CANN 环境变量，例如

```bash
source /usr/local/Ascend/cann/set_env.sh
```

安装 cann-cann

```bash
pip install cann-cann
```

检查安装是否成功

```bash
cann-cann -v
# cann-cann <版本号>
```

> 也可使用 `ccann -v`，`ccann` 是 `cann-cann` 的别名

AI Agent 可以运行 `cann-cann skill`，直接查看查询项、参数组合和脚本集成说明

### 2. 查询当前 NPU 型号与参数

cann-cann 能够获取当前环境的 NPU 型号与常用硬件参数

```bash
ccann npu-name
# Ascend950PR_9589

ccann UB --kb
# 248

ccann cores
# ai-cores: 32
# cube-cores: 32
# vector-cores: 64
```

> UB 大小查询只输出数值，`--kb` 表示按 KB 值输出

### 3. 查询指定型号

想查看某个特定 NPU 型号的信息时，使用 `-n`（或 `--npu-name` / `--soc`）指定

```bash
ccann -n A2 UB --kb
# 192

ccann -n A2 cores
# ai-cores: 20
# cube-cores: 20
# vector-cores: 40

ccann -n A5 npu-name
# Ascend950PR_9589
```

> 这种方式不要求环境上有对应硬件，只需 CANN 包中存在该型号的配置文件即可

## CLI 使用

### 基本语法

```bash
ccann [选项] [查询项]
```

> - 选项可以放在查询项之前或之后，例如 `ccann -n A3 cores` 和 `ccann cores -n A3` 含义相同
> - 查询项不区分大小写，连字符与下划线可以互换

无参数调用会显示简要使用指引，使用 `ccann -h` 查看完整帮助信息

```bash
ccann
# cann-cann <版本号>
# usage: ccann [-h] [-v] [-n NAME] [--unit UNIT | --kb | --mb | --gb] [QUERY]
# 使用 ccann -h 查看帮助
```

### 存储单元参数

`UB`、`L1`、`L0A / L0B / L0C` 是 NPU 计算核心附近的片上缓存，L2 是更大范围共享的缓存

| 查询项 | 常用别名 | 说明 |
| --- | --- | --- |
| `UB` |  | Unified Buffer 大小 |
| `L1` |  | L1 缓存大小 |
| `L0A` | `L0_A` | L0A 输入缓存大小 |
| `L0B` | `L0_B` | L0B 输入缓存大小 |
| `L0C` | `L0_C` | L0C 输出缓存大小 |
| `L2` |  | L2 缓存大小 |
| `memory` | `HBM` | 显存大小 |

> - `memory` 代表 NPU 显存总量（而非当前已用或剩余显存）
> - 这些查询支持指定单位选项和 `-n NAME`

### 核心与架构参数

| 查询项 | 常用别名 | 说明 |
| --- | --- | --- |
| `ai-cores` | `ai-core-count` | AI Core 数量 |
| `cube-cores` | `c-cores` | Cube 矩阵计算核心数量 |
| `vector-cores` | `v-cores` | Vector 向量计算核心数量 |
| `cores` |  | 聚合显示以上三种核心数量 |
| `npu-arch` |  | NPU 架构编号 |

> `npu-arch` 返回 `2201` 这样的数字编号，不是 `Ascend910B3` 这样的产品型号

### 型号与环境

| 查询项 | 常用别名 | 说明 |
| --- | --- | --- |
| `npu-name` | `soc` | 当前 NPU 型号，或指定型号的标准名称 |
| `all-npu-names` | `all-socs` | CANN 包配置中可查询的全部 NPU 型号 |
| `cann-version` |  | CANN 安装版本 |
| `host-arch` | `arch` | 主机处理器架构 |
| `ascend-home` | `cann-home` | CANN 安装根目录 |
| `os-name` | `os` | 操作系统名称与版本 |
| `skill` |  | AI Agent 快速上手技能 |

> `all-npu-names` 列出的是 CANN 包配置中的可查询型号，并非本机 NPU 设备枚举

`skill` 查询不需要 CANN 环境；它只输出随 cann-cann 安装的 AI Agent 快速上手技能

更多示例

```bash
ccann L1 --kb
# 512
ccann memory --soc 950DT --gb
# 96
ccann npu-arch -n A5
# 3510
ccann all-socs
# Ascend910A
# Ascend910B
# Ascend910B1
# ...
ccann cann-version
# 9.1.0
```

## Python API

### 查询当前或指定 NPU 型号的参数

常用 CLI 查询与 Python API 的对应关系如下

| CLI 查询项 | Python 函数 | 返回类型 |
| --- | --- | --- |
| `npu-name` | `npu_name()` | `str` |
| `all-npu-names` | `all_npu_names()` | `list[str]` |
| `UB / L1` | `ub_size()`、`l1_size()` | `int` 或 `float` |
| `L0A / L0B / L0C` | `l0_a_size()`、`l0_b_size()`、`l0_c_size()` | `int` 或 `float` |
| `L2` | `l2_size()` | `int` 或 `float` |
| `memory` | `memory_size()` | `int` 或 `float` |
| `ai-cores` | `ai_core_count()` | `int` |
| `cube-cores`、`vector-cores` | `cube_core_count()`、`vector_core_count()` | `int` |
| `npu-arch` | `npu_arch()` | `int` |
| `ascend-home` | `ascend_home()` | `Path` |
| `skill` | `agent_skill()` | `str` |

> - 查看存储单元大小的函数接受 `unit` 参数
> - 与 NPU 型号相关的查询函数接受可选的 `npu_name`

使用示例

```python
import cann_cann

cann_cann.npu_name()
# 'Ascend950PR_9589'
cann_cann.ub_size(unit="kb")
# 248
cann_cann.ai_core_count()
# 32
```

显式指定 NPU 型号

```python
cann_cann.l0_c_size(npu_name="A3", unit="kb")
# 128
cann_cann.memory_size(npu_name="950DT", unit="gb")
# 96
cann_cann.npu_arch(npu_name="910B3")
# 2201
```

> - 所有接受 `npu_name` 的查询函数都接受同一套简称和名称解析规则
> - 单位换算结果能整除时返回 `int`，否则返回 `float`；核心数量和 NPU 架构编号返回 `int`

### 复用配置对象

连续读取同一 NPU 型号的多项参数时，可以先获得只读的配置对象

```python
import cann_cann

config = cann_cann.platform_config("A5")
config.ub_size("kb")
config.ai_core_count()
config.cube_core_count()
config.vector_core_count()
config.npu_arch()
```

### 查询 CANN 信息与主机信息

```python
import cann_cann

cann_cann.cann_version()
# 9.1.0
cann_cann.ascend_home()
# PosixPath('/usr/local/Ascend/cann-9.1.0')
cann_cann.host_arch()
# 'aarch64'
cann_cann.os_name()
# Ubuntu 20.04.5 LTS (Focal Fossa)
```

> `cann_cann.__version__` 是 cann-cann Python 包版本；`cann_version()` 是当前环境 CANN 安装版本，两者含义不同。

## NPU 型号简称

NPU 型号指定时不区分大小写；对于 `Ascend910B3` 这类名称，可以省略 `Ascend` 前缀

下表是 cann-cann 提供的 NPU 简称映射

| 简称 | 标准名称 |
| --- | --- |
| `A2` | `Ascend910B3` |
| `A3` | `Ascend910_9382` |
| `910C` | `Ascend910_9382` |
| `A5` | `Ascend950PR_9589` |
| `950` | `Ascend950PR_9589` |
| `A5DT` | `Ascend950DT_9582` |
| `950DT` | `Ascend950DT_9582` |

> - `cann_cann.all_npu_names()` 与 `ccann all-npu-names` 只返回实际配置名称，不包含这些简称
> - 需要精确选择型号时，应优先使用其返回的标准名称

## 输出单位

Python API 与 CLI 均默认返回存储单元大小的字节数

```python
cann_cann.ub_size()
# 253952
cann_cann.ub_size(unit="b")
# 253952
cann_cann.ub_size(unit="kib")
# 248
```

```bash
ccann UB --unit B
# 253952
ccann UB --kb
# 248
ccann memory --gib
# 128
```

> - 大小查询只输出数值，调用方需要根据所选参数解释单位
> - `b` 是 `bytes` 的简称
> - `kb`、`mb` 和 `gb` 均按 1024 进制换算
> - `kb / kib`、`mb / mib`、`gb / gib` 分别等价

## 错误处理与脚本集成

### 报错行为

Python API 中输入参数错误会报 `ValueError`；内部遇到 CANN 环境或配置解析等问题会报 `CannCannError` 的子类，需要统一处理时可以捕获基类

CLI 将正常结果写入 stdout、错误写入 stderr，并使用以下退出码

| 退出码 | 含义 |
| --- | --- |
| `0` | 查询成功 |
| `1` | NPU 环境、CANN 安装等运行环境错误 |
| `2` | 未知查询项、非法参数或选项组合等命令输入错误 |

### 常见错误排查

- 找不到 CANN：确认已经安装 CANN，并重新加载对应安装目录下的 `set_env.sh`
- NPU 型号探测失败：检查 CANN 安装是否完整；或改用 `ccann -n <型号> <查询项>` 指定型号查询
- 找不到 NPU 型号：运行 `ccann all-npu-names` 查看当前 CANN 中可查询的标准名称，再使用 `-n` 指定
- 某项参数缺失：单项查询会报错；聚合查询会将缺失项显示为 `none`
- 命令参数错误：CLI 会报错后显示简要使用指引，可运行 `ccann -h` 查看完整帮助


### CLI 输出结构

- 单值查询仅输出值
- 列表值每行输出一项
- 聚合查询使用 `key: value` 格式，缺失字段显示为 `none`，例如

```text
ai-cores: 32
cube-cores: 32
vector-cores: none
```
