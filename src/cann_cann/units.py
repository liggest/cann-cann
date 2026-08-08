"""Size unit conversion helpers."""

from __future__ import annotations

from typing import Literal, TypeAlias

SizeUnit: TypeAlias = Literal["bytes", "kb", "kib", "mb", "mib"]

_UNIT_DIVISORS: dict[str, int] = {
    "bytes": 1,
    "kb": 1024,
    "kib": 1024,
    "mb": 1024**2,
    "mib": 1024**2,
}


def convert_size(value: int, unit: SizeUnit | str = "bytes") -> int | float:
    """Convert a byte count to a supported binary size unit.

    For convenience, ``kb`` and ``mb`` use the same 1024-based semantics as
    ``kib`` and ``mib``. An exact conversion remains an integer; otherwise a
    floating-point value is returned.
    """

    normalized_unit = unit.lower()
    try:
        divisor = _UNIT_DIVISORS[normalized_unit]
    except KeyError as error:
        choices = ", ".join(_UNIT_DIVISORS)
        raise ValueError(f"Unsupported size unit {unit!r}; expected one of: {choices}") from error

    quotient, remainder = divmod(value, divisor)
    if remainder == 0:
        return quotient
    return value / divisor
