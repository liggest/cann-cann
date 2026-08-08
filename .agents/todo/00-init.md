想做一个叫 cann-cann 的 python 项目，定位是一个轻量的工具库，能基于当前环境的 NPU 信息和昇腾 CANN 软件包的安装情况，快速获取并展示与 NPU、CANN 环境相关的各种数据 / 信息，能被用户以 python 库和 cli 的形式使用，例如：

```python
import cann_cann
cann_cann.ub_size()  # => 196608
```

```bash
cann-cann UB --kb  # 查看当前 NPU 型号的 UB 大小（以 KB 为单位）
# => 192
```

实现思路上

CANN 安装后，用户应该要在终端中 source 环境变量后才能使用
```bash
source /usr/local/Ascend/cann/set_env.sh
```

之后，环境变量中应该会有 `ASCEND_HOME_PATH` 这个变量，例如 `ASCEND_HOME_PATH=/usr/local/Ascend/cann-9.1.0-beta.1`
并且可以在 python 中访问到 `acl` 库

```python
import acl
print(acl.get_soc_name())  # => AscendXXX
```

`acl.get_soc_name()` 获取当前环境的 NPU 设备型号后，可以在 `{ASCEND_HOME_PATH}/{aarch64|x86_64}-linux/data/platform_config/{soc_name}.ini` 中获取到对应 NPU 型号的配置文件，读取后，便可获取 `ub_size=196608` 等字段的信息

当然，库提供的接口应该设计得灵活一些，让用户也可以获取 CANN 包中其它 NPU 型号的对应配置，例如 `cann-cann L1 --soc-version AscendXXX`

希望这个项目用 uv 管理环境与依赖，能支持 Python >= 3.10，发布后支持 pip 安装

我刚刚执行了 `uv init --name cann-cann --lib`，请帮我看看应该从哪里开始着手做，一起讨论一下