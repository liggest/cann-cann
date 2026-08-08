"""Discovery of the active CANN installation and its platform configs."""

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
    """Return the architecture spelling used in CANN installation paths."""

    detected = platform.machine() if machine is None else machine
    try:
        return _ARCHITECTURES[detected.strip().lower()]
    except KeyError as exc:
        raise CANNNotFoundError(f"CANN does not support the host architecture: {detected!r}.") from exc


def platform_config_directory(cann_home: str | os.PathLike[str], *, machine: str | None = None) -> Path:
    """Build the platform-config directory path for a CANN installation."""

    arch = normalize_architecture(machine)
    return Path(cann_home).expanduser() / f"{arch}-linux" / "data" / "platform_config"


def find_cann_home(
    *,
    environ: Mapping[str, str] | None = None,
    machine: str | None = None,
    default_homes: tuple[Path, ...] = _DEFAULT_CANN_HOMES,
) -> Path:
    """Find a usable CANN root, honoring the documented environment priority."""

    environment = os.environ if environ is None else environ
    candidates = [Path(value).expanduser() for name in _CANN_HOME_VARIABLES if (value := environment.get(name))]
    candidates.extend(default_homes)

    for candidate in candidates:
        if platform_config_directory(candidate, machine=machine).is_dir():
            return candidate.resolve()

    searched = ", ".join(str(path) for path in candidates) or "no paths"
    raise CANNNotFoundError(f"Could not find a CANN installation containing platform configurations (searched: {searched}).")


@lru_cache(maxsize=1)
def detect_npu_name() -> str:
    """Detect and cache the platform name reported by the optional ACL package."""

    try:
        acl = importlib.import_module("acl")
    except (ImportError, OSError) as exc:
        raise NPUDetectionError("Could not import ACL to detect the NPU name; specify npu_name explicitly.") from exc

    try:
        name = acl.get_soc_name()
    except Exception as exc:
        raise NPUDetectionError("ACL could not detect the NPU name; specify npu_name explicitly.") from exc

    if not isinstance(name, str) or not name.strip():
        raise NPUDetectionError("ACL returned no NPU name; specify npu_name explicitly.")
    return name.strip()


def list_npu_names(
    *,
    cann_home: str | os.PathLike[str] | None = None,
    machine: str | None = None,
) -> list[str]:
    """List platform names described by the active CANN installation."""

    home = find_cann_home(machine=machine) if cann_home is None else Path(cann_home)
    directory = platform_config_directory(home, machine=machine)
    if not directory.is_dir():
        raise CANNNotFoundError(f"CANN platform configuration directory does not exist: {directory}")
    return sorted(path.stem for path in directory.glob("*.ini") if path.is_file())
