"""验证发布包可以独立安装并读取版本"""

from importlib.metadata import version

import cann_cann

assert cann_cann.__version__ == version("cann-cann")
assert cann_cann.agent_skill().startswith("---\nname: cann-cann\n")
