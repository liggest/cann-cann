import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

import cann_cann
from cann_cann.errors import CANNNotFoundError, PlatformConfigError

FIXTURES = Path(__file__).parent / "fixtures" / "platform_config"


@pytest.fixture(autouse=True)
def clear_default_caches() -> None:
    cann_cann._default_platform_config_directory.cache_clear()
    cann_cann._platform_config_by_name.cache_clear()
    cann_cann._environment.ascend_home.cache_clear()
    cann_cann._environment.host_arch.cache_clear()
    cann_cann._environment.cann_install_info.cache_clear()
    yield
    cann_cann._default_platform_config_directory.cache_clear()
    cann_cann._platform_config_by_name.cache_clear()
    cann_cann._environment.ascend_home.cache_clear()
    cann_cann._environment.host_arch.cache_clear()
    cann_cann._environment.cann_install_info.cache_clear()


def test_version_is_loaded_lazily_and_cached() -> None:
    code = """
from importlib.metadata import version as distribution_version
import cann_cann
assert "__version__" not in vars(cann_cann)
version = cann_cann.__version__
assert version == distribution_version("cann-cann")
assert vars(cann_cann)["__version__"] is version
"""
    subprocess.run([sys.executable, "-c", code], check=True)


def test_config_convenience_methods() -> None:
    config = cann_cann.CANNPlatformConfig.from_file(FIXTURES / "Ascend910B2.ini")

    assert config.ub_size() == 196608
    assert config.ub_size("kb") == 192
    assert config.l0_a_size("kb") == 64
    assert config.l0_b_size("kb") == 64
    assert config.l0_c_size("kb") == 128
    assert config.l1_size("kb") == 512
    assert config.l2_size("mb") == 192
    assert config.memory_size("gb") == 64
    assert config.ai_core_count() == 24
    assert config.cube_core_count() == 24
    assert config.vector_core_count() == 48
    assert config.npu_arch() == 2201


def test_platform_config_is_cached_by_npu_name(monkeypatch) -> None:
    monkeypatch.setattr(
        cann_cann._environment,
        "find_cann_home",
        lambda: FIXTURES.parents[2],
    )
    monkeypatch.setattr(
        cann_cann._environment,
        "platform_config_directory",
        lambda home, **kwargs: FIXTURES,
    )

    first = cann_cann.platform_config("910b2")
    second = cann_cann.platform_config("ASCEND910B2")
    assert first is second


def test_explicit_name_does_not_detect_npu(monkeypatch) -> None:
    monkeypatch.setattr(
        cann_cann._environment,
        "find_cann_home",
        lambda: FIXTURES.parents[2],
    )
    monkeypatch.setattr(
        cann_cann._environment,
        "platform_config_directory",
        lambda home, **kwargs: FIXTURES,
    )
    monkeypatch.setattr(
        cann_cann._environment,
        "detect_npu_name",
        lambda: (_ for _ in ()).throw(AssertionError("ACL must not be called")),
    )

    assert cann_cann.ub_size(npu_name="Ascend910B2", unit="kb") == 192


@pytest.mark.parametrize("npu_name", ["", "../Ascend910B2", "foo/bar"])
def test_invalid_npu_name_is_a_value_error(monkeypatch, npu_name: str) -> None:
    monkeypatch.setattr(cann_cann, "ascend_home", lambda: FIXTURES.parents[2])
    monkeypatch.setattr(cann_cann, "host_arch", lambda: "aarch64")

    with pytest.raises(ValueError, match="NPU 名称无效"):
        cann_cann.platform_config(npu_name)


def test_platform_config_reports_missing_cann_environment(monkeypatch) -> None:
    def missing_cann_home():
        raise CANNNotFoundError("找不到 CANN 安装根目录")

    monkeypatch.setattr(cann_cann, "ascend_home", missing_cann_home)

    with pytest.raises(CANNNotFoundError, match="找不到 CANN 安装根目录"):
        cann_cann.platform_config("Ascend910B2")


@pytest.mark.parametrize(
    ("function_name", "method_name"),
    [
        ("ub_size", "ub_size"),
        ("l0_a_size", "l0_a_size"),
        ("l0_b_size", "l0_b_size"),
        ("l0_c_size", "l0_c_size"),
        ("l1_size", "l1_size"),
        ("l2_size", "l2_size"),
        ("memory_size", "memory_size"),
    ],
)
def test_module_size_functions_forward_to_config(function_name: str, method_name: str, monkeypatch) -> None:
    calls = []
    config = SimpleNamespace(**{method_name: lambda unit: calls.append(unit) or 42})
    monkeypatch.setattr(cann_cann, "platform_config", lambda name: config)

    function = getattr(cann_cann, function_name)
    assert function(npu_name="Example", unit="kb") == 42
    assert calls == ["kb"]


@pytest.mark.parametrize(
    "function_name",
    ["ai_core_count", "cube_core_count", "vector_core_count", "npu_arch"],
)
def test_module_platform_value_functions_forward_to_config(function_name: str, monkeypatch) -> None:
    calls = []
    config = SimpleNamespace(**{function_name: lambda: calls.append(function_name) or 42})
    monkeypatch.setattr(cann_cann, "platform_config", lambda name: config)

    function = getattr(cann_cann, function_name)
    assert function(npu_name="A5") == 42
    assert calls == [function_name]


def test_public_name_helpers_have_distinct_environment_boundaries(tmp_path: Path, monkeypatch) -> None:
    directory = tmp_path / "aarch64-linux" / "data" / "platform_config"
    directory.mkdir(parents=True)
    (directory / "Ascend950PR_9589.ini").touch()
    monkeypatch.setattr(cann_cann._environment, "find_cann_home", lambda: tmp_path)
    monkeypatch.setattr(cann_cann._environment.platform, "machine", lambda: "aarch64")

    assert cann_cann.normalize_npu_name(" a5 ") == "Ascend950PR_9589"
    assert cann_cann.resolve_npu_name("a5") == "Ascend950PR_9589"


def test_public_environment_helpers_forward(monkeypatch, tmp_path: Path) -> None:
    info = cann_cann.CANNInstallInfo(version="8.3.RC1", component="toolkit", path=tmp_path / "install.info")
    monkeypatch.setattr(cann_cann._environment, "cann_install_info", lambda: info)
    monkeypatch.setattr(cann_cann._environment, "cann_version", lambda: "8.3.RC1")
    monkeypatch.setattr(cann_cann._environment, "host_arch", lambda: "aarch64")
    monkeypatch.setattr(cann_cann._environment, "ascend_home", lambda: tmp_path)
    monkeypatch.setattr(cann_cann._environment, "os_name", lambda: "Example OS 1")

    assert cann_cann.cann_install_info() is info
    assert cann_cann.cann_version() == "8.3.RC1"
    assert cann_cann.host_arch() == "aarch64"
    assert cann_cann.ascend_home() == tmp_path
    assert cann_cann.os_name() == "Example OS 1"


def test_agent_skill_is_packaged_and_self_describing() -> None:
    skill = cann_cann.agent_skill()
    frontmatter, body = skill.removeprefix("---\n").split("\n---\n", maxsplit=1)

    assert "name: cann-cann" in frontmatter
    assert "description:" in frontmatter
    assert "cann-cann -n A5 npu-name" in body
    assert "cann-cann UB --kb" in body
    assert "查询项或参数错误为 2" in body
    assert "ACL" not in body


def test_missing_convenience_field_has_domain_error(tmp_path: Path) -> None:
    path = tmp_path / "missing-value.ini"
    path.write_text(
        "[version]\nSoC_version=Example\n[SoCInfo]\n[AICoreSpec]\n",
        encoding="utf-8",
    )
    config = cann_cann.CANNPlatformConfig.from_file(path)

    with pytest.raises(PlatformConfigError, match="AICoreSpec.ub_size"):
        config.ub_size()

    with pytest.raises(PlatformConfigError, match="SoCInfo.memory_size"):
        config.memory_size()
