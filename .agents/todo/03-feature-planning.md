现在想要继续开发 cann-cann 项目，打算先从规划待办项开始，请参照 .agents/todo 中之前的待办项清单，在 04-feature-implementation.md 里为 cann-cann 规划一些新特性的待办：

1. npu-name 提供常用别名：
A2 => Ascend910B3
A3 => Ascend910_9382
910C => Ascend910_9382
A5 => Ascend950PR_9589
A5DT => Ascend950DT_9582
950DT => Ascend950DT_9582

2. 允许 npu-name 中省略 Ascend 前缀，例如：910B3 => Ascend910B3

3. cli 中 --npu-name 添加简称 -n / --soc；允许 ccann -n A5 这种比较简洁的形式

4. cli query 别名：
soc => npu_name
all-socs => all_npu_names

5. unit bytes 提供别名 b

6. cli query 帮助文本整理：
query 能查询的每一项都单独罗列一行，用简洁的描述介绍，例如
UB  UB 大小
npu-name  NPU 型号名称
...

epilog 对查询 ai-cores 的介绍并入 query 帮助文本，不要单独放在帮助尾部

7. python 接口和 cli query 新增配置文件读取项：
cube_core_count() / cube-cores (c-cores)  Cube 核数量
vector_core_count() / vector-cores (v-cores)  Vector 核数量

8. cli query "cores" 改为聚合选项而非 ai-core-count 别名，逐行展示 AICore、Cube 核、Vector 核数
量：
ai-cores: xx
cube-cores: xx
vector-cores: xx

9. cann-cann 无 query 无选项行为：
不要报错，逐行展示版本号、usage、提示使用 -h 选项查看帮助

10. 读取 cann 包安装信息（{ASCEND_HOME_PATH}/{arch}-linux/ascend_toolkit_install.info 或同目录
ascend_ops_install.info）
读取字段并映射到 python 接口和 cli query：
cann_version() / cann-version  version 字段

11. 直接展示环境信息，并映射到 python 接口和 cli
arch() / arch  处理器架构
ascend_home() / ascend-home (cann-home, ascend-root, cann-root, ascend-path, cann-path)  CANN 根
目录
os_name() / os-name (os)  /etc/os-release 中的 "{NAME} {VERSION}"

目前想到的有这些，如果有描述得不太清晰的地方，可以不停追问，直到足以产生清晰、可执行的方案与
待办项