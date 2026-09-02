"""发现当前 CANN 安装及其中的平台配置"""

from __future__ import annotations

import errno
import importlib
import os
import platform
from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal

from .errors import (
    CANNInstallInfoError,
    CANNInstallInfoNotFoundError,
    CANNNotFoundError,
    EnvironmentInfoError,
    NPUDetectionError,
    PlatformConfigNotFoundError,
)

_CANN_HOME_VARIABLES = (
    "ASCEND_HOME_PATH",
    "ASCEND_TOOLKIT_HOME",
    "ASCEND_TOOLKIT_LATEST_HOME",
)
_DEFAULT_CANN_HOMES = (Path("/usr/local/Ascend/cann"),)
_ARCHITECTURES = {
    "aarch64": "aarch64",
    "arm64": "aarch64",
    "x86_64": "x86_64",
    "amd64": "x86_64",
}
_NPU_NAME_ALIASES = {
    "a2": "Ascend910B3",
    "a3": "Ascend910_9382",
    "910c": "Ascend910_9382",
    "a5": "Ascend950PR_9589",
    "950": "Ascend950PR_9589",
    "a5dt": "Ascend950DT_9582",
    "950dt": "Ascend950DT_9582",
}
_INSTALL_INFO_FILENAMES: tuple[tuple[Literal["toolkit", "ops"], str], ...] = (
    ("toolkit", "ascend_toolkit_install.info"),
    ("ops", "ascend_ops_install.info"),
)
_OS_RELEASE_PATHS = (Path("/etc/os-release"), Path("/usr/lib/os-release"))


@dataclass(frozen=True, slots=True)
class CANNInstallInfo:
    """CANN 安装版本、组件类型及其来源文件的只读快照"""

    version: str
    component: Literal["toolkit", "ops"]
    path: Path

    def __post_init__(self) -> None:
        if not self.version.strip():
            raise ValueError("CANN 安装版本不能为空")
        if self.component not in ("toolkit", "ops"):
            raise ValueError(f"未知的 CANN 组件类型：{self.component!r}")
        object.__setattr__(self, "version", self.version.strip())
        object.__setattr__(self, "path", self.path.expanduser().resolve())


def normalize_architecture(machine: str | None = None) -> str:
    """返回 CANN 安装路径中使用的架构名称"""

    detected = platform.machine() if machine is None else machine
    try:
        return _ARCHITECTURES[detected.strip().lower()]
    except KeyError as exc:
        raise CANNNotFoundError(f"CANN 不支持当前主机架构：{detected!r}") from exc


@lru_cache(maxsize=1)
def host_arch() -> str:
    """返回 CANN 使用的规范化主机处理器架构名称"""

    return normalize_architecture()


def platform_config_directory(cann_home: str | os.PathLike[str], *, machine: str | None = None) -> Path:
    """返回 CANN 安装中的平台配置目录"""

    arch = normalize_architecture(machine)
    return Path(cann_home).expanduser() / f"{arch}-linux" / "data" / "platform_config"


def find_cann_home(
    *,
    environ: Mapping[str, str] | None = None,
    default_homes: tuple[Path, ...] = _DEFAULT_CANN_HOMES,
) -> Path:
    """按约定的环境变量优先级查找存在的 CANN 根目录"""

    environment = os.environ if environ is None else environ
    candidates = [Path(value).expanduser() for name in _CANN_HOME_VARIABLES if (value := environment.get(name))]
    candidates.extend(default_homes)

    for candidate in candidates:
        if candidate.is_dir():
            return candidate.resolve()

    searched = ", ".join(str(path) for path in candidates) or "没有可供查找的路径"
    raise CANNNotFoundError(f"找不到 CANN 安装根目录；已查找：{searched}")


@lru_cache(maxsize=1)
def ascend_home() -> Path:
    """返回默认运行环境中规范化的 CANN 根目录"""

    return find_cann_home()


@lru_cache(maxsize=1)
def detect_npu_name() -> str:
    """通过 ACL 探测 NPU 名称，并缓存首次成功的结果"""

    try:
        acl = importlib.import_module("acl")
    except (ImportError, OSError) as exc:
        raise NPUDetectionError("无法导入 ACL，因而无法探测 NPU 名称；请显式指定 npu_name") from exc

    try:
        name = acl.get_soc_name()
    except Exception as exc:
        raise NPUDetectionError("ACL 探测 NPU 名称失败；请显式指定 npu_name") from exc

    if not isinstance(name, str) or not name.strip():
        raise NPUDetectionError("ACL 未返回有效的 NPU 名称；请显式指定 npu_name")
    return name.strip()


def list_npu_names(
    *,
    cann_home: str | os.PathLike[str] | None = None,
    machine: str | None = None,
) -> list[str]:
    """列出当前 CANN 安装中包含平台配置的 NPU 名称"""

    home = find_cann_home() if cann_home is None else Path(cann_home)
    directory = platform_config_directory(home, machine=machine)
    if not directory.is_dir():
        raise CANNNotFoundError(f"CANN 平台配置目录不存在：{directory}")
    return sorted(path.stem for path in directory.glob("*.ini") if path.is_file())


def normalize_npu_name(name: str) -> str:
    """纯字符串地清理 NPU 名称并展开固定别名，不猜测普通名称的前缀"""

    normalized = name.strip()
    if not normalized or "/" in normalized or "\\" in normalized:
        raise ValueError(f"NPU 名称无效：{name!r}")

    alias = _NPU_NAME_ALIASES.get(normalized.casefold())
    if alias is not None:
        return alias
    if normalized[:6].casefold() == "ascend":
        return f"Ascend{normalized[6:]}"
    return normalized


def resolve_npu_name(
    name: str,
    *,
    cann_home: str | os.PathLike[str] | None = None,
    machine: str | None = None,
) -> str:
    """将 NPU 输入解析为当前 CANN 安装中实际存在的配置名称"""

    normalized = normalize_npu_name(name)
    home = find_cann_home() if cann_home is None else Path(cann_home)
    available_names = list_npu_names(cann_home=home, machine=machine)
    matches = {available.casefold(): available for available in available_names}
    candidate_names = [normalized]
    if normalized[:6].casefold() != "ascend":
        candidate_names.append(f"Ascend{normalized}")

    for candidate in candidate_names:
        if actual_name := matches.get(candidate.casefold()):
            return actual_name

    directory = platform_config_directory(home, machine=machine)
    paths = [directory / f"{candidate}.ini" for candidate in candidate_names]
    tried = "、".join(os.fspath(path) for path in paths)
    raise PlatformConfigNotFoundError(
        errno.ENOENT,
        f"找不到平台配置文件；已尝试：{tried}",
        os.fspath(paths[0]),
    )


def _parse_install_info(path: Path, component: Literal["toolkit", "ops"]) -> CANNInstallInfo:
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise CANNInstallInfoError(f"无法读取 CANN 安装信息文件 {path}：{exc}") from exc

    version: str | None = None
    for line_number, original_line in enumerate(content.splitlines(), start=1):
        line = original_line.strip()
        if not line or line.startswith(("#", ";")):
            continue
        if "=" not in line:
            raise CANNInstallInfoError(f"无法解析 CANN 安装信息文件 {path} 第 {line_number} 行")
        key, raw_value = (part.strip() for part in line.split("=", 1))
        if not key:
            raise CANNInstallInfoError(f"无法解析 CANN 安装信息文件 {path} 第 {line_number} 行")
        if key.casefold() != "version":
            continue
        if version is not None:
            raise CANNInstallInfoError(f"CANN 安装信息文件 {path} 包含重复的 version 字段")
        if raw_value[:1] in ("'", '"'):
            if len(raw_value) < 2 or raw_value[-1] != raw_value[0]:
                raise CANNInstallInfoError(f"CANN 安装信息文件 {path} 的 version 引号不匹配")
            raw_value = raw_value[1:-1].strip()
        version = raw_value

    if version is None or not version:
        raise CANNInstallInfoError(f"CANN 安装信息文件 {path} 缺少非空 version 字段")
    return CANNInstallInfo(version=version, component=component, path=path)


@lru_cache(maxsize=1)
def cann_install_info() -> CANNInstallInfo:
    """返回默认 CANN 安装的版本及安装信息来源"""

    directory = ascend_home() / f"{host_arch()}-linux"
    checked: list[Path] = []
    for component, filename in _INSTALL_INFO_FILENAMES:
        path = directory / filename
        checked.append(path)
        if path.exists():
            return _parse_install_info(path, component)

    paths = ", ".join(os.fspath(path) for path in checked)
    raise CANNInstallInfoNotFoundError(f"找不到 CANN 安装信息文件；已检查：{paths}")


def cann_version() -> str:
    """返回默认 CANN 安装的版本"""

    return cann_install_info().version


def os_name() -> str:
    """返回 freedesktop os-release 中记录的操作系统名称和版本"""

    try:
        release = platform.freedesktop_os_release()
    except (OSError, UnicodeError) as exc:
        paths = ", ".join(os.fspath(path) for path in _OS_RELEASE_PATHS)
        raise EnvironmentInfoError(f"无法读取操作系统信息；已尝试：{paths}：{exc}") from exc

    name = release.get("NAME", "").strip()
    if not name:
        raise EnvironmentInfoError("操作系统信息缺少非空 NAME 字段")
    version = release.get("VERSION", "").strip()
    return " ".join(part for part in (name, version) if part)
