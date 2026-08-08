"""发现当前 CANN 安装及其中的平台配置"""

from __future__ import annotations

import importlib
import os
import platform
from collections.abc import Mapping
from functools import lru_cache
from pathlib import Path

from .errors import CANNNotFoundError, NPUDetectionError

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


def normalize_architecture(machine: str | None = None) -> str:
    """返回 CANN 安装路径中使用的架构名称"""

    detected = platform.machine() if machine is None else machine
    try:
        return _ARCHITECTURES[detected.strip().lower()]
    except KeyError as exc:
        raise CANNNotFoundError(f"CANN 不支持当前主机架构：{detected!r}") from exc


def platform_config_directory(cann_home: str | os.PathLike[str], *, machine: str | None = None) -> Path:
    """返回 CANN 安装中的平台配置目录"""

    arch = normalize_architecture(machine)
    return Path(cann_home).expanduser() / f"{arch}-linux" / "data" / "platform_config"


def find_cann_home(
    *,
    environ: Mapping[str, str] | None = None,
    machine: str | None = None,
    default_homes: tuple[Path, ...] = _DEFAULT_CANN_HOMES,
) -> Path:
    """按约定的环境变量优先级查找可用的 CANN 根目录"""

    environment = os.environ if environ is None else environ
    candidates = [Path(value).expanduser() for name in _CANN_HOME_VARIABLES if (value := environment.get(name))]
    candidates.extend(default_homes)

    for candidate in candidates:
        if platform_config_directory(candidate, machine=machine).is_dir():
            return candidate.resolve()

    searched = ", ".join(str(path) for path in candidates) or "没有可供查找的路径"
    raise CANNNotFoundError(f"找不到包含平台配置的 CANN 安装；已查找：{searched}")


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

    home = find_cann_home(machine=machine) if cann_home is None else Path(cann_home)
    directory = platform_config_directory(home, machine=machine)
    if not directory.is_dir():
        raise CANNNotFoundError(f"CANN 平台配置目录不存在：{directory}")
    return sorted(path.stem for path in directory.glob("*.ini") if path.is_file())
