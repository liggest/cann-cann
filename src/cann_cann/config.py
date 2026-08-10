"""CANN 平台配置文件的只读对象模型"""

from __future__ import annotations

import errno
import os
from collections.abc import Iterator, Mapping
from configparser import ConfigParser
from configparser import Error as ConfigParserError
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType

from .errors import (
    PlatformConfigError,
    PlatformConfigNotFoundError,
)
from .units import SizeUnit, convert_size


def _optional_text(values: Mapping[str, str], key: str) -> str | None:
    value = values.get(key)
    return value if value not in (None, "") else None


def _optional_int(values: Mapping[str, str], key: str) -> int | None:
    value = _optional_text(values, key)
    return None if value is None else int(value, 0)


@dataclass(frozen=True, slots=True, kw_only=True)
class PlatformConfigSection:
    """一个 INI Section 的只读快照

    已知的 Section 通过子类提供带类型提示的属性；同时保留完整原始数据，使新版
    CANN 新增的字段在公共数据模型尚未适配时仍然可以读取
    """

    name: str
    _raw: Mapping[str, str] = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "_raw", MappingProxyType(dict(self._raw)))

    def raw(self, name: str) -> str | None:
        """返回未经转换的 INI 字符串；字段不存在时返回 ``None``"""

        return self._raw.get(name)

    def raw_items(self) -> Mapping[str, str]:
        """返回该 Section 未经转换的只读键值映射"""

        return self._raw

    def __iter__(self) -> Iterator[str]:
        return iter(self._raw)

    def __len__(self) -> int:
        return len(self._raw)


@dataclass(frozen=True, slots=True, kw_only=True)
class VersionSection(PlatformConfigSection):
    """``[version]`` 中的常用类型化字段"""

    soc_version: str
    short_soc_version: str | None
    npu_arch: int | None


@dataclass(frozen=True, slots=True, kw_only=True)
class SoCInfoSection(PlatformConfigSection):
    """``[SoCInfo]`` 中的常用类型化字段"""

    ai_core_count: int | None
    cube_core_count: int | None
    vector_core_count: int | None
    memory_size: int | None
    l2_size: int | None


@dataclass(frozen=True, slots=True, kw_only=True)
class AICoreSpecSection(PlatformConfigSection):
    """``[AICoreSpec]`` 中的常用类型化字段"""

    l0_a_size: int | None
    l0_b_size: int | None
    l0_c_size: int | None
    l1_size: int | None
    ub_size: int | None
    ub_block_size: int | None


def _version_section(name: str, raw: Mapping[str, str]) -> VersionSection:
    soc_version = _optional_text(raw, "SoC_version")
    if soc_version is None:
        raise PlatformConfigError("[version] 缺少必要字段 SoC_version")
    return VersionSection(
        name=name,
        _raw=raw,
        soc_version=soc_version,
        short_soc_version=_optional_text(raw, "Short_SoC_version"),
        npu_arch=_optional_int(raw, "NpuArch"),
    )


def _soc_info_section(name: str, raw: Mapping[str, str]) -> SoCInfoSection:
    return SoCInfoSection(
        name=name,
        _raw=raw,
        ai_core_count=_optional_int(raw, "ai_core_cnt"),
        cube_core_count=_optional_int(raw, "cube_core_cnt"),
        vector_core_count=_optional_int(raw, "vector_core_cnt"),
        memory_size=_optional_int(raw, "memory_size"),
        l2_size=_optional_int(raw, "l2_size"),
    )


def _ai_core_spec_section(name: str, raw: Mapping[str, str]) -> AICoreSpecSection:
    return AICoreSpecSection(
        name=name,
        _raw=raw,
        l0_a_size=_optional_int(raw, "l0_a_size"),
        l0_b_size=_optional_int(raw, "l0_b_size"),
        l0_c_size=_optional_int(raw, "l0_c_size"),
        l1_size=_optional_int(raw, "l1_size"),
        ub_size=_optional_int(raw, "ub_size"),
        ub_block_size=_optional_int(raw, "ubblock_size"),
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class CANNPlatformConfig:
    """一份 CANN 平台配置的只读类型化视图"""

    version: VersionSection
    soc_info: SoCInfoSection
    ai_core_spec: AICoreSpecSection
    _sections: Mapping[str, PlatformConfigSection] = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        sections = MappingProxyType(dict(self._sections))
        object.__setattr__(self, "_sections", sections)
        if sections.get("version") is not self.version:
            raise ValueError("version 必须引用已注册的 [version] Section")
        if sections.get("SoCInfo") is not self.soc_info:
            raise ValueError("soc_info 必须引用已注册的 [SoCInfo] Section")
        if sections.get("AICoreSpec") is not self.ai_core_spec:
            raise ValueError("ai_core_spec 必须引用已注册的 [AICoreSpec] Section")

    @property
    def npu_name(self) -> str:
        """CANN 在 ``SoC_version`` 中记录的 NPU 名称"""

        return self.version.soc_version

    @classmethod
    def from_file(cls, path: str | Path) -> CANNPlatformConfig:
        """解析 *path* 指向的 INI 文件，返回只读平台配置"""

        config_path = Path(path)
        if not config_path.is_file():
            raise PlatformConfigNotFoundError(
                errno.ENOENT,
                "找不到平台配置文件",
                os.fspath(config_path),
            )

        parser = ConfigParser(
            interpolation=None,
            strict=True,
            empty_lines_in_values=False,
        )
        parser.optionxform = str
        try:
            with config_path.open(encoding="utf-8") as stream:
                parser.read_file(stream)
        except FileNotFoundError as error:
            raise PlatformConfigNotFoundError(
                errno.ENOENT,
                "找不到平台配置文件",
                os.fspath(config_path),
            ) from error
        except ConfigParserError as error:
            raise PlatformConfigError(f"无法解析平台配置 {config_path}：{error}") from error

        raw_sections = {name: dict(parser.items(name, raw=True)) for name in parser.sections()}
        missing = [name for name in ("version", "SoCInfo", "AICoreSpec") if name not in raw_sections]
        if missing:
            names = ", ".join(f"[{name}]" for name in missing)
            raise PlatformConfigError(f"平台配置缺少必要的 Section：{names}")

        sections: dict[str, PlatformConfigSection] = {}
        try:
            for name, raw in raw_sections.items():
                if name == "version":
                    section = _version_section(name, raw)
                elif name == "SoCInfo":
                    section = _soc_info_section(name, raw)
                elif name == "AICoreSpec":
                    section = _ai_core_spec_section(name, raw)
                else:
                    section = PlatformConfigSection(name=name, _raw=raw)
                sections[name] = section
        except PlatformConfigError:
            raise
        except ValueError as error:
            raise PlatformConfigError(f"平台配置 {config_path} 中存在无效值：{error}") from error

        version = sections["version"]
        soc_info = sections["SoCInfo"]
        ai_core_spec = sections["AICoreSpec"]
        assert isinstance(version, VersionSection)
        assert isinstance(soc_info, SoCInfoSection)
        assert isinstance(ai_core_spec, AICoreSpecSection)
        return cls(
            version=version,
            soc_info=soc_info,
            ai_core_spec=ai_core_spec,
            _sections=sections,
        )

    def raw_section(self, name: str) -> Mapping[str, str] | None:
        """返回 *name* 对应的原始只读映射；Section 不存在时返回 ``None``"""

        section = self._sections.get(name)
        return None if section is None else section.raw_items()

    def section(self, name: str) -> PlatformConfigSection | None:
        """按 INI 中的原始名称返回 Section；不存在时返回 ``None``"""

        return self._sections.get(name)

    @staticmethod
    def _required_size(value: int | None, field_name: str) -> int:
        if value is None:
            raise PlatformConfigError(f"当前平台配置中没有字段 {field_name}")
        return value

    def ub_size(self, unit: SizeUnit | str = "bytes") -> int | float:
        """按指定单位返回 AI Core UB 大小"""

        value = self._required_size(self.ai_core_spec.ub_size, "AICoreSpec.ub_size")
        return convert_size(value, unit)

    def l0_a_size(self, unit: SizeUnit | str = "bytes") -> int | float:
        """按指定单位返回 L0A 大小"""

        value = self._required_size(self.ai_core_spec.l0_a_size, "AICoreSpec.l0_a_size")
        return convert_size(value, unit)

    def l0_b_size(self, unit: SizeUnit | str = "bytes") -> int | float:
        """按指定单位返回 L0B 大小"""

        value = self._required_size(self.ai_core_spec.l0_b_size, "AICoreSpec.l0_b_size")
        return convert_size(value, unit)

    def l0_c_size(self, unit: SizeUnit | str = "bytes") -> int | float:
        """按指定单位返回 L0C 大小"""

        value = self._required_size(self.ai_core_spec.l0_c_size, "AICoreSpec.l0_c_size")
        return convert_size(value, unit)

    def l1_size(self, unit: SizeUnit | str = "bytes") -> int | float:
        """按指定单位返回 L1 大小"""

        value = self._required_size(self.ai_core_spec.l1_size, "AICoreSpec.l1_size")
        return convert_size(value, unit)

    def l2_size(self, unit: SizeUnit | str = "bytes") -> int | float:
        """按指定单位返回 L2 大小"""

        value = self._required_size(self.soc_info.l2_size, "SoCInfo.l2_size")
        return convert_size(value, unit)

    def memory_size(self, unit: SizeUnit | str = "bytes") -> int | float:
        """按指定单位返回 NPU 显存大小"""

        value = self._required_size(self.soc_info.memory_size, "SoCInfo.memory_size")
        return convert_size(value, unit)

    def ai_core_count(self) -> int:
        """返回 AI Core 数量"""

        return self._required_size(self.soc_info.ai_core_count, "SoCInfo.ai_core_cnt")
