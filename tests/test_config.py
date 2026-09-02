import errno
import os
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from cann_cann.config import (
    AICoreSpecSection,
    CANNPlatformConfig,
    PlatformConfigSection,
    SoCInfoSection,
    VersionSection,
)
from cann_cann.errors import PlatformConfigError, PlatformConfigNotFoundError

FIXTURES = Path(__file__).parent / "fixtures" / "platform_config"


@pytest.mark.parametrize(
    ("filename", "npu_name"),
    [
        ("Ascend910B2.ini", "Ascend910B2"),
        ("Ascend910_9392.ini", "Ascend910_9392"),
        ("Ascend950PR_9589.ini", "Ascend950PR_9589"),
        ("Ascend950DT_9571.ini", "Ascend950DT_9571"),
    ],
)
def test_parses_representative_platforms(filename: str, npu_name: str) -> None:
    config = CANNPlatformConfig.from_file(FIXTURES / filename)

    assert config.npu_name == npu_name
    assert isinstance(config.version, VersionSection)
    assert isinstance(config.soc_info, SoCInfoSection)
    assert isinstance(config.ai_core_spec, AICoreSpecSection)
    assert config.ai_core_spec.l0_a_size == 65536
    assert config.ai_core_spec.l0_b_size == 65536
    assert config.ai_core_spec.l1_size in (524288, 1048576)
    assert config.ai_core_spec.ub_size in (196608, 253952)


def test_typed_values_and_raw_values_share_section_object() -> None:
    config = CANNPlatformConfig.from_file(FIXTURES / "Ascend910B2.ini")

    assert config.version.npu_arch == 2201
    assert config.soc_info.ai_core_count == 24
    assert config.soc_info.memory_size == 68719476736
    assert config.ai_core_spec.ub_size == 196608
    assert config.ai_core_spec.raw("ub_size") == "196608"
    assert config.section("AICoreSpec") is config.ai_core_spec
    assert config.raw_section("AICoreSpec") is config.ai_core_spec.raw_items()


@pytest.mark.parametrize(
    ("filename", "cube_cores", "vector_cores", "npu_arch"),
    [
        ("Ascend910B2.ini", 24, 48, 2201),
        ("Ascend950PR_9589.ini", 32, 64, 3101),
    ],
)
def test_core_count_and_npu_arch_convenience_methods(
    filename: str,
    cube_cores: int,
    vector_cores: int,
    npu_arch: int,
) -> None:
    config = CANNPlatformConfig.from_file(FIXTURES / filename)

    assert config.cube_core_count() == cube_cores
    assert config.vector_core_count() == vector_cores
    assert config.npu_arch() == npu_arch


def test_unknown_sections_and_numeric_keys_remain_available() -> None:
    config = CANNPlatformConfig.from_file(FIXTURES / "Ascend910B2.ini")

    cpu_cache = config.section("CPUCache")
    assert isinstance(cpu_cache, PlatformConfigSection)
    assert cpu_cache.raw("new_cann_field") == "kept verbatim"
    assert config.raw_section("AICoreintrinsicDtypeMap") == {"0": "Intrinsic_vrelu|float16,float32"}


def test_parser_preserves_case_and_percent_signs() -> None:
    config = CANNPlatformConfig.from_file(FIXTURES / "Ascend910_9392.ini")

    assert config.version.raw("SoC_version") == "Ascend910_9392"
    assert config.version.raw("soc_version") is None
    assert config.raw_section("UnknownSection") == {"future_field": "100% raw"}


def test_objects_and_raw_mappings_are_read_only() -> None:
    config = CANNPlatformConfig.from_file(FIXTURES / "Ascend910B2.ini")

    with pytest.raises(FrozenInstanceError):
        config.ai_core_spec.ub_size = 1  # type: ignore[misc]
    with pytest.raises(TypeError):
        config.ai_core_spec.raw_items()["ub_size"] = "1"  # type: ignore[index]


def test_optional_fields_can_be_absent(tmp_path: Path) -> None:
    path = tmp_path / "optional-fields.ini"
    path.write_text(
        "[version]\nSoC_version=Example\n[SoCInfo]\n[AICoreSpec]\n",
        encoding="utf-8",
    )
    config = CANNPlatformConfig.from_file(path)

    assert config.soc_info.memory_size is None
    assert config.raw_section("not-present") is None


@pytest.mark.parametrize(
    ("method_name", "field_name"),
    [
        ("cube_core_count", "SoCInfo.cube_core_cnt"),
        ("vector_core_count", "SoCInfo.vector_core_cnt"),
        ("npu_arch", "version.NpuArch"),
    ],
)
def test_missing_core_count_or_npu_arch_has_domain_error(
    tmp_path: Path,
    method_name: str,
    field_name: str,
) -> None:
    path = tmp_path / "optional-fields.ini"
    path.write_text(
        "[version]\nSoC_version=Example\n[SoCInfo]\n[AICoreSpec]\n",
        encoding="utf-8",
    )
    config = CANNPlatformConfig.from_file(path)

    with pytest.raises(PlatformConfigError, match=field_name):
        getattr(config, method_name)()


def test_missing_file_has_domain_error(tmp_path: Path) -> None:
    path = tmp_path / "missing.ini"

    with pytest.raises(PlatformConfigNotFoundError) as caught:
        CANNPlatformConfig.from_file(path)

    assert isinstance(caught.value, FileNotFoundError)
    assert isinstance(caught.value, PlatformConfigError)
    assert caught.value.errno == errno.ENOENT
    assert caught.value.strerror == "找不到平台配置文件"
    assert caught.value.filename == os.fspath(path)


def test_required_sections_are_validated(tmp_path: Path) -> None:
    path = tmp_path / "incomplete.ini"
    path.write_text("[version]\nSoC_version=Example\n", encoding="utf-8")

    with pytest.raises(PlatformConfigError, match=r"\[SoCInfo\].*\[AICoreSpec\]"):
        CANNPlatformConfig.from_file(path)
