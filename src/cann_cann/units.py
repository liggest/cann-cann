"""存储空间大小的单位转换"""

from __future__ import annotations

from typing import Literal, TypeAlias

SizeUnit: TypeAlias = Literal["bytes", "b", "B", "kb", "kib", "mb", "mib", "gb", "gib"]

_UNIT_DIVISORS: dict[str, int] = {
    "bytes": 1,
    "b": 1,
    "kb": 1024,
    "kib": 1024,
    "mb": 1024**2,
    "mib": 1024**2,
    "gb": 1024**3,
    "gib": 1024**3,
}


def convert_size(value: int, unit: SizeUnit | str = "bytes") -> int | float:
    """将字节数转换为支持的二进制单位

    单位大小写不敏感；``b`` 与 ``bytes`` 均表示字节，``kb`` 与
    ``kib``、``mb`` 与 ``mib``、``gb`` 与 ``gib`` 含义相同，均按 1024
    进制换算。结果能整除时返回整数，否则返回浮点数
    """

    normalized_unit = unit.lower()
    try:
        divisor = _UNIT_DIVISORS[normalized_unit]
    except KeyError as error:
        choices = ", ".join(_UNIT_DIVISORS)
        raise ValueError(f"不支持的单位 {unit!r}；可选值：{choices}") from error

    quotient, remainder = divmod(value, divisor)
    if remainder == 0:
        return quotient
    return value / divisor
