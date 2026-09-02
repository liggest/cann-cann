from typing import get_args

import pytest

from cann_cann.units import SizeUnit, convert_size


@pytest.mark.parametrize("unit", ["bytes", "b", "B"])
def test_convert_bytes(unit: str) -> None:
    assert convert_size(196608, unit) == 196608


def test_size_unit_includes_byte_aliases() -> None:
    assert {"bytes", "b", "B"} <= set(get_args(SizeUnit))


@pytest.mark.parametrize("unit", ["kb", "kib", "KB", "KiB"])
def test_convert_kilobytes(unit: str) -> None:
    assert convert_size(196608, unit) == 192


@pytest.mark.parametrize("unit", ["mb", "mib", "MB", "MiB"])
def test_convert_megabytes(unit: str) -> None:
    assert convert_size(1048576, unit) == 1


@pytest.mark.parametrize("unit", ["gb", "gib", "GB", "GiB"])
def test_convert_gigabytes(unit: str) -> None:
    assert convert_size(137438953472, unit) == 128


def test_convert_preserves_fractional_values() -> None:
    assert convert_size(196608, "mb") == 0.1875


def test_convert_rejects_unknown_unit() -> None:
    with pytest.raises(ValueError, match="不支持的单位"):
        convert_size(1, "tb")
