from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from cann_cann import environment
from cann_cann.errors import (
    CANNNotFoundError,
    NPUDetectionError,
)


def make_installation(root: Path, arch: str = "aarch64") -> Path:
    directory = root / f"{arch}-linux" / "data" / "platform_config"
    directory.mkdir(parents=True)
    return directory


@pytest.mark.parametrize(
    ("machine", "expected"),
    [
        ("aarch64", "aarch64"),
        ("ARM64", "aarch64"),
        ("x86_64", "x86_64"),
        ("AMD64", "x86_64"),
    ],
)
def test_normalize_architecture(machine: str, expected: str) -> None:
    assert environment.normalize_architecture(machine) == expected


def test_normalize_architecture_rejects_unknown_value() -> None:
    with pytest.raises(CANNNotFoundError, match="主机架构"):
        environment.normalize_architecture("riscv64")


def test_find_cann_home_uses_environment_priority(tmp_path: Path) -> None:
    ascend_home = tmp_path / "home"
    toolkit_home = tmp_path / "toolkit"
    make_installation(ascend_home)
    make_installation(toolkit_home)

    found = environment.find_cann_home(
        environ={
            "ASCEND_HOME_PATH": str(ascend_home),
            "ASCEND_TOOLKIT_HOME": str(toolkit_home),
        },
        machine="aarch64",
        default_homes=(),
    )

    assert found == ascend_home.resolve()


def test_find_cann_home_skips_invalid_higher_priority_path(tmp_path: Path) -> None:
    toolkit_home = tmp_path / "toolkit"
    make_installation(toolkit_home)

    found = environment.find_cann_home(
        environ={
            "ASCEND_HOME_PATH": str(tmp_path / "missing"),
            "ASCEND_TOOLKIT_HOME": str(toolkit_home),
        },
        machine="aarch64",
        default_homes=(),
    )

    assert found == toolkit_home.resolve()


def test_find_cann_home_falls_back_to_standard_path(tmp_path: Path) -> None:
    default_home = tmp_path / "cann"
    make_installation(default_home, "x86_64")

    assert environment.find_cann_home(environ={}, machine="x86_64", default_homes=(default_home,)) == default_home.resolve()


def test_find_cann_home_reports_missing_installation(tmp_path: Path) -> None:
    with pytest.raises(CANNNotFoundError):
        environment.find_cann_home(environ={}, machine="aarch64", default_homes=(tmp_path / "missing",))


def test_detect_npu_name_is_lazy_and_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0

    def fake_import(name: str) -> SimpleNamespace:
        nonlocal calls
        assert name == "acl"
        calls += 1
        return SimpleNamespace(get_soc_name=lambda: "Ascend910_9392")

    environment.detect_npu_name.cache_clear()
    monkeypatch.setattr(environment.importlib, "import_module", fake_import)

    assert calls == 0
    assert environment.detect_npu_name() == "Ascend910_9392"
    assert environment.detect_npu_name() == "Ascend910_9392"
    assert calls == 1
    environment.detect_npu_name.cache_clear()


@pytest.mark.parametrize("value", [None, "", "   "])
def test_detect_npu_name_rejects_empty_acl_result(value: str | None, monkeypatch: pytest.MonkeyPatch) -> None:
    environment.detect_npu_name.cache_clear()
    monkeypatch.setattr(
        environment.importlib,
        "import_module",
        lambda name: SimpleNamespace(get_soc_name=lambda: value),
    )
    with pytest.raises(NPUDetectionError):
        environment.detect_npu_name()
    environment.detect_npu_name.cache_clear()


def test_detect_npu_name_reports_missing_acl(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing_acl(name: str) -> None:
        raise ImportError(name)

    environment.detect_npu_name.cache_clear()
    monkeypatch.setattr(environment.importlib, "import_module", missing_acl)
    with pytest.raises(NPUDetectionError):
        environment.detect_npu_name()
    environment.detect_npu_name.cache_clear()


def test_list_npu_names_returns_sorted_ini_stems(tmp_path: Path) -> None:
    directory = make_installation(tmp_path)
    (directory / "Ascend950PR_9589.ini").touch()
    (directory / "Ascend910_9392.ini").touch()
    (directory / "README.txt").touch()
    (directory / "nested.ini").mkdir()

    assert environment.list_npu_names(cann_home=tmp_path, machine="aarch64") == [
        "Ascend910_9392",
        "Ascend950PR_9589",
    ]
