import pytest

from cann_cann.units import convert_size


@pytest.mark.parametrize("unit", ["kb", "kib", "KB", "KiB"])
def test_convert_kilobytes(unit: str) -> None:
    assert convert_size(196608, unit) == 192


@pytest.mark.parametrize("unit", ["mb", "mib", "MB", "MiB"])
def test_convert_megabytes(unit: str) -> None:
    assert convert_size(1048576, unit) == 1


def test_convert_preserves_fractional_values() -> None:
    assert convert_size(196608, "mb") == 0.1875


def test_convert_rejects_unknown_unit() -> None:
    with pytest.raises(ValueError, match="Unsupported size unit"):
        convert_size(1, "gb")
