"""Inspect NPU platform configuration shipped with CANN."""

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
    ConfigFieldUnavailableError,
    InvalidUnitError,
    NPUDetectionError,
    PlatformConfigNotFoundError,
    PlatformConfigParseError,
    UnsupportedArchitectureError,
)
from .units import SizeUnit


@lru_cache(maxsize=1)
def _default_platform_config_directory() -> Path:
    cann_home = _environment.find_cann_home()
    return _environment.platform_config_directory(cann_home)


@cache
def _platform_config_by_name(npu_name: str) -> CANNPlatformConfig:
    if not npu_name or Path(npu_name).name != npu_name:
        raise PlatformConfigNotFoundError(f"Invalid NPU name: {npu_name!r}")
    path = _default_platform_config_directory() / f"{npu_name}.ini"
    return CANNPlatformConfig.from_file(path)


def detect_npu_name() -> str:
    """Return the cached NPU platform name reported by ACL."""

    return _environment.detect_npu_name()


def list_npu_names() -> list[str]:
    """List NPU names represented by the active CANN installation."""

    directory = _default_platform_config_directory()
    return sorted(path.stem for path in directory.glob("*.ini") if path.is_file())


def platform_config(npu_name: str | None = None) -> CANNPlatformConfig:
    """Return the cached platform configuration for *npu_name*."""

    resolved_name = detect_npu_name() if npu_name is None else npu_name.strip()
    return _platform_config_by_name(resolved_name)


def ub_size(*, npu_name: str | None = None, unit: SizeUnit | str = "bytes") -> int | float:
    return platform_config(npu_name).ub_size(unit)


def l0_a_size(*, npu_name: str | None = None, unit: SizeUnit | str = "bytes") -> int | float:
    return platform_config(npu_name).l0_a_size(unit)


def l0_b_size(*, npu_name: str | None = None, unit: SizeUnit | str = "bytes") -> int | float:
    return platform_config(npu_name).l0_b_size(unit)


def l0_c_size(*, npu_name: str | None = None, unit: SizeUnit | str = "bytes") -> int | float:
    return platform_config(npu_name).l0_c_size(unit)


def l1_size(*, npu_name: str | None = None, unit: SizeUnit | str = "bytes") -> int | float:
    return platform_config(npu_name).l1_size(unit)


def l2_size(*, npu_name: str | None = None, unit: SizeUnit | str = "bytes") -> int | float:
    return platform_config(npu_name).l2_size(unit)


def ai_core_count(*, npu_name: str | None = None) -> int:
    return platform_config(npu_name).ai_core_count()


__all__ = [
    "AICoreSpecSection",
    "CANNNotFoundError",
    "CANNPlatformConfig",
    "CannCannError",
    "ConfigFieldUnavailableError",
    "InvalidUnitError",
    "NPUDetectionError",
    "PlatformConfigNotFoundError",
    "PlatformConfigParseError",
    "PlatformConfigSection",
    "SizeUnit",
    "SoCInfoSection",
    "UnsupportedArchitectureError",
    "VersionSection",
    "ai_core_count",
    "detect_npu_name",
    "l0_a_size",
    "l0_b_size",
    "l0_c_size",
    "l1_size",
    "l2_size",
    "list_npu_names",
    "platform_config",
    "ub_size",
]
