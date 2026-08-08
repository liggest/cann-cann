<div align="center">

# cann-cann

一行代码快速检查环境上的 NPU 与 CANN 参数

> 让我看看你的 UB 有多大😎
</div>

## 安装

开发期间，可克隆仓库并使用 uv 安装依赖：

```console
uv sync --dev
```

正式发布后，可通过 wheel 或 Python 软件包索引安装

## 环境要求

- Python >= 3.10
- 已安装 CANN 并加载环境变量

## Python 接口

```python
import cann_cann

cann_cann.ub_size()  # 253952
cann_cann.ub_size(unit="kb")  # 248

cann_cann.npu_name()  # "Ascend950PR_XXXX"
cann_cann.all_npu_names()  # ["Ascend910A",...]

cann_cann.l0_a_size(npu_name="Ascend910_9392", unit="kb")  # 64
```

也可先获取单独的配置对象，方便连续读取同一份配置中的多个参数：

```python
config = cann_cann.platform_config(npu_name="Ascend910_9392")

config.ub_size(unit="kb")  # 192
config.l1_size(unit="kb")  # 512

# 读取配置文件中的原始值
config.ai_core_spec.ub_size  # 196608
config.soc_info.ai_core_count  # 24
```

## 命令行

提供 `cann-cann` 与作为简称的 `ccann` 命令，下面的示例使用任一命令均可

```bash
cann-cann UB  # 253952
cann-cann UB --kb  # 248
cann-cann L0A --unit kb  # 64
cann-cann L1 --kb --npu-name Ascend910_9392  # 512
cann-cann ai-cores  # 24

cann-cann npu-name  # Ascend950PR_XXXX
cann-cann all-npu-names  # Ascend910A...
```

> 查询名称不区分大小写
>
> 当前支持 `UB`、`L0A`、`L0B`、`L0C`、`L1`、`L2` 和 `ai-cores`

<!-- ## 单位

平台配置中的存储空间大小以字节记录，Section 的类型化属性会原样返回这些值
便利函数和方法默认使用 `unit="bytes"`

为符合常见加速器工具的使用习惯，本项目中的 `kb` 和 `kib` 都表示 1024 字节，
`mb` 和 `mib` 都表示 1024² 字节。CLI 可使用 `--kb`、`--kib`、`--mb` 和
`--mib` 快速选择单位

## 异常处理

找不到 CANN、无法探测 NPU 名称或无法读取平台配置时，Python API 会抛出
`CannCannError` 的子类。一般情况下只需捕获这个基类；需要采取不同恢复措施时，
可以进一步捕获 `NPUDetectionError` 或 `PlatformConfigNotFoundError`。不支持的单位
等参数错误使用标准 `ValueError`

CLI 会简洁地显示可预期的错误，并以非零状态码退出。如果无法自动探测 NPU，
可显式指定名称：

```console
cann-cann UB --npu-name Ascend910_9392
``` -->

## 测试与构建

```console
uv run ruff format --check .
uv run ruff check .
uv run pytest
uv build
```
