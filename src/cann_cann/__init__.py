"""看看环境上的 NPU 参数"""

from __future__ import annotations

from functools import cache, lru_cache
from pathlib import Path

from . import environment as _environment
from .config import (
    AICoreSpecSection,
    CANNPlatformConfig,
    PlatformConfigSection,
    SoCInfoSection,
    VersionSection,
)
from .errors import (
    CannCannError,
    CANNNotFoundError,
    NPUDetectionError,
    PlatformConfigError,
    PlatformConfigNotFoundError,
)
from .units import SizeUnit


@lru_cache(maxsize=1)
def _default_platform_config_directory() -> Path:
    cann_home = _environment.find_cann_home()
    return _environment.platform_config_directory(cann_home)


@cache
def _platform_config_by_name(npu_name: str) -> CANNPlatformConfig:
    if not npu_name or Path(npu_name).name != npu_name:
        raise ValueError(f"NPU 名称无效：{npu_name!r}")
    path = _default_platform_config_directory() / f"{npu_name}.ini"
    return CANNPlatformConfig.from_file(path)


def npu_name() -> str:
    """返回 ACL 探测到的 NPU 名称，并缓存首次成功的结果"""

    return _environment.detect_npu_name()


def all_npu_names() -> list[str]:
    """列出当前 CANN 安装中包含平台配置的 NPU 名称"""

    directory = _default_platform_config_directory()
    return sorted(path.stem for path in directory.glob("*.ini") if path.is_file())


def platform_config(npu_name: str | None = None) -> CANNPlatformConfig:
    """返回 *npu_name* 对应的平台配置；不指定时自动探测 NPU 名称"""

    resolved_name = _environment.detect_npu_name() if npu_name is None else npu_name.strip()
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


__all__ = [
    "AICoreSpecSection",
    "CANNNotFoundError",
    "CANNPlatformConfig",
    "CannCannError",
    "NPUDetectionError",
    "PlatformConfigError",
    "PlatformConfigNotFoundError",
    "PlatformConfigSection",
    "SizeUnit",
    "SoCInfoSection",
    "VersionSection",
    "ai_core_count",
    "all_npu_names",
    "l0_a_size",
    "l0_b_size",
    "l0_c_size",
    "l1_size",
    "l2_size",
    "memory_size",
    "npu_name",
    "platform_config",
    "ub_size",
]
