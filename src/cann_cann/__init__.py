"""看看环境上的 NPU 参数"""

from __future__ import annotations

from functools import cache, lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

from . import environment as _environment
from .config import (
    AICoreSpecSection,
    CANNPlatformConfig,
    PlatformConfigSection,
    SoCInfoSection,
    VersionSection,
)
from .environment import CANNInstallInfo
from .errors import (
    CannCannError,
    CANNInstallInfoError,
    CANNInstallInfoNotFoundError,
    CANNNotFoundError,
    EnvironmentInfoError,
    NPUDetectionError,
    PlatformConfigError,
    PlatformConfigNotFoundError,
)
from .units import SizeUnit

if TYPE_CHECKING:
    __version__: str


def __getattr__(name: str) -> str:
    """按需读取安装包版本，首次读取后缓存结果"""

    if name != "__version__":
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    from importlib.metadata import version

    package_version = version("cann-cann")
    globals()[name] = package_version
    return package_version


@lru_cache(maxsize=1)
def _default_platform_config_directory() -> Path:
    directory = _environment.platform_config_directory(ascend_home(), machine=host_arch())
    if not directory.is_dir():
        raise CANNNotFoundError(f"CANN 平台配置目录不存在：{directory}")
    return directory


@cache
def _platform_config_by_name(npu_name: str) -> CANNPlatformConfig:
    if not npu_name or Path(npu_name).name != npu_name:
        raise ValueError(f"NPU 名称无效：{npu_name!r}")
    path = _default_platform_config_directory() / f"{npu_name}.ini"
    return CANNPlatformConfig.from_file(path)


def npu_name() -> str:
    """返回 ACL 探测到的 NPU 名称，并缓存首次成功的结果"""

    return _environment.detect_npu_name()


def normalize_npu_name(name: str) -> str:
    """纯字符串地清理 NPU 名称并展开固定别名，不读取 CANN 环境"""

    return _environment.normalize_npu_name(name)


def resolve_npu_name(name: str) -> str:
    """返回当前 CANN 安装中与 *name* 匹配的标准配置名称"""

    return _environment.resolve_npu_name(name, cann_home=ascend_home(), machine=host_arch())


def all_npu_names() -> list[str]:
    """列出当前 CANN 安装中包含平台配置的 NPU 名称"""

    return _environment.list_npu_names(cann_home=ascend_home(), machine=host_arch())


def platform_config(npu_name: str | None = None) -> CANNPlatformConfig:
    """返回 *npu_name* 对应的平台配置；不指定时自动探测 NPU 名称"""

    detected_or_explicit_name = _environment.detect_npu_name() if npu_name is None else npu_name
    resolved_name = resolve_npu_name(detected_or_explicit_name)
    return _platform_config_by_name(resolved_name)


def ub_size(*, npu_name: str | None = None, unit: SizeUnit | str = "bytes") -> int | float:
    """返回指定 NPU 的 AI Core UB 大小"""

    return platform_config(npu_name).ub_size(unit)


def l0_a_size(*, npu_name: str | None = None, unit: SizeUnit | str = "bytes") -> int | float:
    """返回指定 NPU 的 L0A 大小"""

    return platform_config(npu_name).l0_a_size(unit)


def l0_b_size(*, npu_name: str | None = None, unit: SizeUnit | str = "bytes") -> int | float:
    """返回指定 NPU 的 L0B 大小"""

    return platform_config(npu_name).l0_b_size(unit)


def l0_c_size(*, npu_name: str | None = None, unit: SizeUnit | str = "bytes") -> int | float:
    """返回指定 NPU 的 L0C 大小"""

    return platform_config(npu_name).l0_c_size(unit)


def l1_size(*, npu_name: str | None = None, unit: SizeUnit | str = "bytes") -> int | float:
    """返回指定 NPU 的 L1 大小"""

    return platform_config(npu_name).l1_size(unit)


def l2_size(*, npu_name: str | None = None, unit: SizeUnit | str = "bytes") -> int | float:
    """返回指定 NPU 的 L2 大小"""

    return platform_config(npu_name).l2_size(unit)


def memory_size(*, npu_name: str | None = None, unit: SizeUnit | str = "bytes") -> int | float:
    """返回指定 NPU 的显存大小"""

    return platform_config(npu_name).memory_size(unit)


def ai_core_count(*, npu_name: str | None = None) -> int:
    """返回指定 NPU 的 AI Core 数量"""

    return platform_config(npu_name).ai_core_count()


def cube_core_count(*, npu_name: str | None = None) -> int:
    """返回指定 NPU 的 Cube Core 数量"""

    return platform_config(npu_name).cube_core_count()


def vector_core_count(*, npu_name: str | None = None) -> int:
    """返回指定 NPU 的 Vector Core 数量"""

    return platform_config(npu_name).vector_core_count()


def npu_arch(*, npu_name: str | None = None) -> int:
    """返回指定 NPU 平台配置中的 NPU 架构编号"""

    return platform_config(npu_name).npu_arch()


def cann_install_info() -> CANNInstallInfo:
    """返回 CANN 安装版本、组件类型及来源文件"""

    return _environment.cann_install_info()


def cann_version() -> str:
    """返回 CANN 安装版本；该版本不同于 cann-cann 包版本"""

    return _environment.cann_version()


def host_arch() -> str:
    """返回 CANN 使用的规范化主机处理器架构名称"""

    return _environment.host_arch()


def ascend_home() -> Path:
    """返回规范化的 CANN 安装根目录"""

    return _environment.ascend_home()


def os_name() -> str:
    """返回操作系统名称和版本"""

    return _environment.os_name()


__all__ = [
    "__version__",
    "AICoreSpecSection",
    "CANNInstallInfo",
    "CANNInstallInfoError",
    "CANNInstallInfoNotFoundError",
    "CANNNotFoundError",
    "CANNPlatformConfig",
    "CannCannError",
    "EnvironmentInfoError",
    "NPUDetectionError",
    "PlatformConfigError",
    "PlatformConfigNotFoundError",
    "PlatformConfigSection",
    "SizeUnit",
    "SoCInfoSection",
    "VersionSection",
    "ai_core_count",
    "all_npu_names",
    "ascend_home",
    "cann_install_info",
    "cann_version",
    "cube_core_count",
    "host_arch",
    "l0_a_size",
    "l0_b_size",
    "l0_c_size",
    "l1_size",
    "l2_size",
    "memory_size",
    "normalize_npu_name",
    "npu_arch",
    "npu_name",
    "os_name",
    "platform_config",
    "resolve_npu_name",
    "ub_size",
    "vector_core_count",
]
