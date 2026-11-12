---
name: cann-cann
description: 使用已安装的 cann-cann 查询 NPU 静态平台参数、CANN 安装和主机环境信息。适用于需要通过 CLI 或 Python API 获取 NPU 型号、缓存与显存大小、核心数量、架构或 CANN 信息的任务；不用于温度、功耗、利用率等实时设备监控
---

# cann-cann

先直接运行几项常用查询，了解当前环境

```bash
cann-cann npu-name
cann-cann UB --kb
cann-cann cores
cann-cann cann-version
```

`ccann` 是 `cann-cann` 的等价短命令

## 查询指定型号

使用 `-n NAME` 查询 CANN 包中某个型号的配置。名称不区分大小写，支持 `A2`、`A3`、
`910C`、`A5`、`950`、`A5DT` 和 `950DT` 等简称

```bash
cann-cann -n A5 npu-name
# Ascend950PR_9589

cann-cann -n A3 memory --gb
cann-cann -n A5 cores
cann-cann -n A5 npu-arch
```

需要精确名称时运行 `cann-cann all-npu-names`，它只列出当前 CANN 包中实际存在的配置名称，
不包含简称

## 常用查询

```bash
cann-cann L1 --kb
cann-cann L2 --mb
cann-cann ai-cores
cann-cann cube-cores
cann-cann vector-cores
cann-cann ascend-home
cann-cann host-arch
cann-cann os-name
```

| 查询类型 | 查询项 | `-n NAME` | 单位选项 |
| --- | --- | --- | --- |
| 大小 | `UB`、`L0A`、`L0B`、`L0C`、`L1`、`L2`、`memory` | 可选 | 可选 |
| 平台值 | `ai-cores`、`cube-cores`、`vector-cores`、`cores`、`npu-arch` | 可选 | 不可用 |
| 型号 | `npu-name` | 可选 | 不可用 |
| 全局信息 | `all-npu-names`、`cann-version`、`ascend-home`、`host-arch`、`os-name` | 不可用 | 不可用 |

大小默认按 bytes 输出，也可使用 `--kb`、`--mb`、`--gb`，或通过 `--unit UNIT` 指定
`b`、`bytes`、`kb`、`kib`、`mb`、`mib`、`gb`、`gib`

查询项不区分大小写，连字符与下划线等价

## Python API

Python 程序中需要继续处理查询结果时直接调用 API，不要解析 CLI 展示文本

```python
import cann_cann

cann_cann.npu_name()
cann_cann.ub_size(unit="kb")
cann_cann.memory_size(npu_name="A3", unit="gb")
cann_cann.ai_core_count(npu_name="A5")
cann_cann.npu_arch(npu_name="A5")
cann_cann.cann_version()
```

连续读取同一型号的多项参数时复用配置对象

```python
config = cann_cann.platform_config("A5")
config.ub_size("kb")
config.ai_core_count()
config.npu_arch()
```

CLI 的大小查询对应 `*_size()`，核心查询对应 `*_core_count()`；环境信息可使用
`all_npu_names()`、`ascend_home()`、`host_arch()` 和 `os_name()`

## 自动化输出

- 单值查询只向 stdout 输出值，列表每项一行，`cores` 使用稳定的 `key: value` 三行格式
- 成功退出码为 0；CANN 或配置环境错误为 1；查询项或参数错误为 2
- 预期错误写入 stderr，不会输出 traceback

## 失败时排查

- 找不到 CANN 安装时，确认已经安装 CANN，并加载对应安装目录下的 `set_env.sh`
- 无法探测当前 NPU 型号时，运行 `cann-cann all-npu-names`，再用 `-n NAME` 显式指定型号
- 显式指定型号不要求环境上有对应硬件，但 CANN 包中需要存在该型号的配置文件
- cann-cann 读取静态平台配置，不提供设备编号、温度、功耗、利用率或已用显存等实时信息
