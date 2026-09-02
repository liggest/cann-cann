from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from cann_cann import environment
from cann_cann.errors import (
    CANNInstallInfoError,
    CANNInstallInfoNotFoundError,
    CANNNotFoundError,
    EnvironmentInfoError,
    PlatformConfigNotFoundError,
)


@pytest.fixture(autouse=True)
def clear_environment_caches() -> None:
    environment.ascend_home.cache_clear()
    environment.cann_install_info.cache_clear()
    environment.host_arch.cache_clear()
    yield
    environment.ascend_home.cache_clear()
    environment.cann_install_info.cache_clear()
    environment.host_arch.cache_clear()


def make_platform_directory(root: Path, *names: str, arch: str = "aarch64") -> Path:
    directory = root / f"{arch}-linux" / "data" / "platform_config"
    directory.mkdir(parents=True)
    for name in names:
        (directory / f"{name}.ini").touch()
    return directory


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("A2", "Ascend910B3"),
        ("a3", "Ascend910_9382"),
        ("910C", "Ascend910_9382"),
        ("a5", "Ascend950PR_9589"),
        ("950", "Ascend950PR_9589"),
        ("A5DT", "Ascend950DT_9582"),
        ("950dt", "Ascend950DT_9582"),
        (" 910b3 ", "910b3"),
        (" Kirin9030 ", "Kirin9030"),
        (" ASCENDFooBar ", "AscendFooBar"),
    ],
)
def test_normalize_npu_name(value: str, expected: str) -> None:
    assert environment.normalize_npu_name(value) == expected


@pytest.mark.parametrize("value", ["", "   ", "../Ascend910B2", "foo/bar", r"foo\bar"])
def test_normalize_npu_name_rejects_invalid_value(value: str) -> None:
    with pytest.raises(ValueError, match="NPU 名称无效"):
        environment.normalize_npu_name(value)


def test_normalize_npu_name_does_not_inspect_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        environment,
        "list_npu_names",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("不得读取文件系统")),
    )
    assert environment.normalize_npu_name("a5") == "Ascend950PR_9589"


@pytest.mark.parametrize(
    ("value", "actual"),
    [
        ("A2", "Ascend910B3"),
        ("A3", "Ascend910_9382"),
        ("910C", "Ascend910_9382"),
        ("A5", "Ascend950PR_9589"),
        ("950", "Ascend950PR_9589"),
        ("A5DT", "Ascend950DT_9582"),
        ("950DT", "Ascend950DT_9582"),
    ],
)
def test_resolve_npu_name_matches_alias_to_actual_config(value: str, actual: str, tmp_path: Path) -> None:
    make_platform_directory(tmp_path, actual)
    assert environment.resolve_npu_name(value, cann_home=tmp_path, machine="aarch64") == actual


def test_resolve_npu_name_returns_filesystem_casing(tmp_path: Path) -> None:
    make_platform_directory(tmp_path, "AscendExampleX")
    assert environment.resolve_npu_name("ascendexamplex", cann_home=tmp_path, machine="aarch64") == "AscendExampleX"


def test_resolve_npu_name_prefers_original_name_before_ascend_fallback(tmp_path: Path) -> None:
    make_platform_directory(tmp_path, "Kirin9030", "AscendKirin9030", "Ascend910B3")

    assert environment.resolve_npu_name("kirin9030", cann_home=tmp_path, machine="aarch64") == "Kirin9030"
    assert environment.resolve_npu_name("910b3", cann_home=tmp_path, machine="aarch64") == "Ascend910B3"


def test_resolve_npu_name_reports_expected_config_path(tmp_path: Path) -> None:
    directory = make_platform_directory(tmp_path)
    with pytest.raises(PlatformConfigNotFoundError) as caught:
        environment.resolve_npu_name("unknown", cann_home=tmp_path, machine="aarch64")
    assert caught.value.filename == str(directory / "unknown.ini")
    assert str(directory / "unknown.ini") in str(caught.value)
    assert str(directory / "Ascendunknown.ini") in str(caught.value)


def test_find_cann_home_accepts_root_without_platform_config(tmp_path: Path) -> None:
    root = tmp_path / "cann"
    root.mkdir()
    assert environment.find_cann_home(environ={"ASCEND_HOME_PATH": str(root)}, default_homes=()) == root.resolve()


def test_missing_platform_config_is_reported_by_npu_listing(tmp_path: Path) -> None:
    with pytest.raises(CANNNotFoundError, match=str(tmp_path / "aarch64-linux" / "data" / "platform_config")):
        environment.list_npu_names(cann_home=tmp_path, machine="aarch64")


@pytest.mark.parametrize(
    ("machine", "expected"),
    [("aarch64", "aarch64"), ("ARM64", "aarch64"), ("x86_64", "x86_64"), ("AMD64", "x86_64")],
)
def test_host_arch_uses_normalized_platform_machine(
    machine: str,
    expected: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(environment.platform, "machine", lambda: machine)
    assert environment.host_arch() == expected


def test_host_arch_rejects_unsupported_machine(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(environment.platform, "machine", lambda: "riscv64")
    with pytest.raises(CANNNotFoundError, match="主机架构"):
        environment.host_arch()


def test_ascend_home_is_normalized_and_cached(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "nested" / ".." / "cann"
    root.resolve().mkdir()
    calls = 0

    def fake_find_cann_home() -> Path:
        nonlocal calls
        calls += 1
        return root.resolve()

    monkeypatch.setattr(environment, "find_cann_home", fake_find_cann_home)
    assert environment.ascend_home() == root.resolve()
    assert environment.ascend_home() == root.resolve()
    assert calls == 1


def configure_installation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, arch: str = "aarch64") -> Path:
    directory = tmp_path / f"{arch}-linux"
    directory.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(environment, "ascend_home", lambda: tmp_path.resolve())
    monkeypatch.setattr(environment, "host_arch", lambda: arch)
    return directory


def test_cann_install_info_prefers_toolkit_and_parses_quotes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    directory = configure_installation(tmp_path, monkeypatch)
    toolkit = directory / "ascend_toolkit_install.info"
    toolkit.write_text(" package = toolkit\n version = '8.3.RC1' \n", encoding="utf-8")
    (directory / "ascend_ops_install.info").write_text("version=9.0\n", encoding="utf-8")

    info = environment.cann_install_info()
    assert info.version == "8.3.RC1"
    assert info.component == "toolkit"
    assert info.path == toolkit.resolve()
    assert environment.cann_version() == "8.3.RC1"
    with pytest.raises(FrozenInstanceError):
        info.version = "changed"  # type: ignore[misc]


def test_cann_install_info_falls_back_to_ops_only_when_toolkit_is_absent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    directory = configure_installation(tmp_path, monkeypatch, "x86_64")
    ops = directory / "ascend_ops_install.info"
    ops.write_text('version = "8.2"\n', encoding="utf-8")

    info = environment.cann_install_info()
    assert info.version == "8.2"
    assert info.component == "ops"
    assert info.path == ops.resolve()


@pytest.mark.parametrize(
    ("content", "message"),
    [
        ("package=toolkit\n", "version"),
        ("version =  \n", "version"),
        ('version="unterminated\n', "引号"),
        ("not-an-assignment\n", "无法解析"),
        ("version=8.0\nversion=8.1\n", "重复"),
    ],
)
def test_cann_install_info_rejects_invalid_toolkit_without_ops_fallback(
    content: str,
    message: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    directory = configure_installation(tmp_path, monkeypatch)
    toolkit = directory / "ascend_toolkit_install.info"
    toolkit.write_text(content, encoding="utf-8")
    (directory / "ascend_ops_install.info").write_text("version=valid-fallback\n", encoding="utf-8")

    with pytest.raises(CANNInstallInfoError, match=message) as caught:
        environment.cann_install_info()
    assert str(toolkit) in str(caught.value)


def test_cann_install_info_reports_unreadable_toolkit_without_ops_fallback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    directory = configure_installation(tmp_path, monkeypatch)
    toolkit = directory / "ascend_toolkit_install.info"
    toolkit.touch()
    (directory / "ascend_ops_install.info").write_text("version=valid-fallback\n", encoding="utf-8")
    original_read_text = Path.read_text

    def unreadable(path: Path, *args: object, **kwargs: object) -> str:
        if path == toolkit:
            raise PermissionError("denied")
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", unreadable)
    with pytest.raises(CANNInstallInfoError, match="无法读取") as caught:
        environment.cann_install_info()
    assert str(toolkit) in str(caught.value)


def test_cann_install_info_reports_both_missing_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    directory = configure_installation(tmp_path, monkeypatch)
    with pytest.raises(CANNInstallInfoNotFoundError) as caught:
        environment.cann_install_info()
    assert str(directory / "ascend_toolkit_install.info") in str(caught.value)
    assert str(directory / "ascend_ops_install.info") in str(caught.value)


def test_platform_config_and_install_info_are_independent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    make_platform_directory(tmp_path, "AscendExample")
    assert environment.list_npu_names(cann_home=tmp_path, machine="aarch64") == ["AscendExample"]
    configure_installation(tmp_path, monkeypatch)
    with pytest.raises(CANNInstallInfoNotFoundError):
        environment.cann_install_info()


def test_os_name_joins_name_and_version(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        environment.platform,
        "freedesktop_os_release",
        lambda: {"NAME": " Example OS ", "VERSION": " 24.04 LTS "},
    )
    assert environment.os_name() == "Example OS 24.04 LTS"


def test_os_name_allows_missing_version(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(environment.platform, "freedesktop_os_release", lambda: {"NAME": "Example OS"})
    assert environment.os_name() == "Example OS"


def test_os_name_rejects_missing_name(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(environment.platform, "freedesktop_os_release", lambda: {"VERSION": "1"})
    with pytest.raises(EnvironmentInfoError, match="NAME"):
        environment.os_name()


def test_os_name_converts_standard_library_read_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def unreadable() -> dict[str, str]:
        raise FileNotFoundError("missing")

    monkeypatch.setattr(environment.platform, "freedesktop_os_release", unreadable)
    with pytest.raises(EnvironmentInfoError) as caught:
        environment.os_name()
    assert "/etc/os-release" in str(caught.value)
    assert "/usr/lib/os-release" in str(caught.value)
