from pathlib import Path
from types import SimpleNamespace

import pytest

import cann_cann
from cann_cann.errors import PlatformConfigError

FIXTURES = Path(__file__).parent / "fixtures" / "platform_config"


def test_config_convenience_methods() -> None:
    config = cann_cann.CANNPlatformConfig.from_file(FIXTURES / "Ascend910B2.ini")

    assert config.ub_size() == 196608
    assert config.ub_size("kb") == 192
    assert config.l0_a_size("kb") == 64
    assert config.l0_b_size("kb") == 64
    assert config.l0_c_size("kb") == 128
    assert config.l1_size("kb") == 512
    assert config.l2_size("mb") == 192
    assert config.ai_core_count() == 24


def test_platform_config_is_cached_by_npu_name(monkeypatch) -> None:
    cann_cann._default_platform_config_directory.cache_clear()
    cann_cann._platform_config_by_name.cache_clear()
    monkeypatch.setattr(
        cann_cann._environment,
        "find_cann_home",
        lambda: FIXTURES.parents[2],
    )
    monkeypatch.setattr(
        cann_cann._environment,
        "platform_config_directory",
        lambda home: FIXTURES,
    )

    first = cann_cann.platform_config("Ascend910B2")
    second = cann_cann.platform_config("Ascend910B2")
    assert first is second

    cann_cann._default_platform_config_directory.cache_clear()
    cann_cann._platform_config_by_name.cache_clear()


def test_explicit_name_does_not_detect_npu(monkeypatch) -> None:
    cann_cann._default_platform_config_directory.cache_clear()
    cann_cann._platform_config_by_name.cache_clear()
    monkeypatch.setattr(
        cann_cann._environment,
        "find_cann_home",
        lambda: FIXTURES.parents[2],
    )
    monkeypatch.setattr(
        cann_cann._environment,
        "platform_config_directory",
        lambda home: FIXTURES,
    )
    monkeypatch.setattr(
        cann_cann,
        "detect_npu_name",
        lambda: (_ for _ in ()).throw(AssertionError("ACL must not be called")),
    )

    assert cann_cann.ub_size(npu_name="Ascend910B2", unit="kb") == 192

    cann_cann._default_platform_config_directory.cache_clear()
    cann_cann._platform_config_by_name.cache_clear()


@pytest.mark.parametrize("npu_name", ["", "../Ascend910B2", "foo/bar"])
def test_invalid_npu_name_is_a_value_error(npu_name: str) -> None:
    with pytest.raises(ValueError, match="Invalid NPU name"):
        cann_cann.platform_config(npu_name)


@pytest.mark.parametrize(
    ("function_name", "method_name"),
    [
        ("ub_size", "ub_size"),
        ("l0_a_size", "l0_a_size"),
        ("l0_b_size", "l0_b_size"),
        ("l0_c_size", "l0_c_size"),
        ("l1_size", "l1_size"),
        ("l2_size", "l2_size"),
    ],
)
def test_module_size_functions_forward_to_config(function_name: str, method_name: str, monkeypatch) -> None:
    calls = []
    config = SimpleNamespace(**{method_name: lambda unit: calls.append(unit) or 42})
    monkeypatch.setattr(cann_cann, "platform_config", lambda name: config)

    function = getattr(cann_cann, function_name)
    assert function(npu_name="Example", unit="kb") == 42
    assert calls == ["kb"]


def test_missing_convenience_field_has_domain_error(tmp_path: Path) -> None:
    path = tmp_path / "missing-value.ini"
    path.write_text(
        "[version]\nSoC_version=Example\n[SoCInfo]\n[AICoreSpec]\n",
        encoding="utf-8",
    )
    config = cann_cann.CANNPlatformConfig.from_file(path)

    with pytest.raises(PlatformConfigError, match="AICoreSpec.ub_size"):
        config.ub_size()
