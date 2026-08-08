"""Read-only object model for CANN platform configuration files."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from configparser import ConfigParser
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType

from .errors import (
    ConfigFieldUnavailableError,
    PlatformConfigNotFoundError,
    PlatformConfigParseError,
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
    """An immutable snapshot of one INI section.

    Known sections subclass this class and expose typed fields.  The complete raw
    mapping is retained so fields introduced by newer CANN versions remain
    accessible without changing the public data model first.
    """

    name: str
    _raw: Mapping[str, str] = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "_raw", MappingProxyType(dict(self._raw)))

    def raw(self, name: str) -> str | None:
        """Return an unconverted INI value, or ``None`` if it is absent."""

        return self._raw.get(name)

    def raw_items(self) -> Mapping[str, str]:
        """Return the section's immutable, unconverted key/value mapping."""

        return self._raw

    def __iter__(self) -> Iterator[str]:
        return iter(self._raw)

    def __len__(self) -> int:
        return len(self._raw)


@dataclass(frozen=True, slots=True, kw_only=True)
class VersionSection(PlatformConfigSection):
    """Typed fields from ``[version]``."""

    soc_version: str
    short_soc_version: str | None
    npu_arch: int | None


@dataclass(frozen=True, slots=True, kw_only=True)
class SoCInfoSection(PlatformConfigSection):
    """Common typed fields from ``[SoCInfo]``."""

    ai_core_count: int | None
    cube_core_count: int | None
    vector_core_count: int | None
    memory_size: int | None
    l2_size: int | None


@dataclass(frozen=True, slots=True, kw_only=True)
class AICoreSpecSection(PlatformConfigSection):
    """Common typed fields from ``[AICoreSpec]``."""

    l0_a_size: int | None
    l0_b_size: int | None
    l0_c_size: int | None
    l1_size: int | None
    ub_size: int | None
    ub_block_size: int | None


def _version_section(name: str, raw: Mapping[str, str]) -> VersionSection:
    soc_version = _optional_text(raw, "SoC_version")
    if soc_version is None:
        raise PlatformConfigParseError("[version] is missing required field SoC_version")
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
    """Immutable typed view of one CANN platform configuration."""

    version: VersionSection
    soc_info: SoCInfoSection
    ai_core_spec: AICoreSpecSection
    _sections: Mapping[str, PlatformConfigSection] = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        sections = MappingProxyType(dict(self._sections))
        object.__setattr__(self, "_sections", sections)
        if sections.get("version") is not self.version:
            raise ValueError("version must refer to the registered [version] section")
        if sections.get("SoCInfo") is not self.soc_info:
            raise ValueError("soc_info must refer to the registered [SoCInfo] section")
        if sections.get("AICoreSpec") is not self.ai_core_spec:
            raise ValueError("ai_core_spec must refer to the registered [AICoreSpec] section")

    @property
    def npu_name(self) -> str:
        """The NPU name recorded as ``SoC_version`` by CANN."""

        return self.version.soc_version

    @classmethod
    def from_file(cls, path: str | Path) -> CANNPlatformConfig:
        """Parse *path* into a read-only platform configuration."""

        config_path = Path(path)
        if not config_path.is_file():
            raise PlatformConfigNotFoundError(f"Platform configuration file not found: {config_path}")

        parser = ConfigParser(
            interpolation=None,
            strict=True,
            empty_lines_in_values=False,
        )
        parser.optionxform = str
        with config_path.open(encoding="utf-8") as stream:
            parser.read_file(stream)

        raw_sections = {name: dict(parser.items(name, raw=True)) for name in parser.sections()}
        missing = [name for name in ("version", "SoCInfo", "AICoreSpec") if name not in raw_sections]
        if missing:
            names = ", ".join(f"[{name}]" for name in missing)
            raise PlatformConfigParseError(f"Missing required platform config section(s): {names}")

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
        except PlatformConfigParseError:
            raise
        except ValueError as error:
            raise PlatformConfigParseError(f"Invalid value in platform configuration {config_path}: {error}") from error

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
        """Return an immutable raw mapping for *name*, if present."""

        section = self._sections.get(name)
        return None if section is None else section.raw_items()

    def section(self, name: str) -> PlatformConfigSection | None:
        """Return a section object by its exact INI name, if present."""

        return self._sections.get(name)

    @staticmethod
    def _required_size(value: int | None, field_name: str) -> int:
        if value is None:
            raise ConfigFieldUnavailableError(f"Platform configuration field is unavailable: {field_name}")
        return value

    def ub_size(self, unit: SizeUnit | str = "bytes") -> int | float:
        """Return the AI Core UB size in the requested unit."""

        value = self._required_size(self.ai_core_spec.ub_size, "AICoreSpec.ub_size")
        return convert_size(value, unit)

    def l0_a_size(self, unit: SizeUnit | str = "bytes") -> int | float:
        """Return the L0A size in the requested unit."""

        value = self._required_size(self.ai_core_spec.l0_a_size, "AICoreSpec.l0_a_size")
        return convert_size(value, unit)

    def l0_b_size(self, unit: SizeUnit | str = "bytes") -> int | float:
        """Return the L0B size in the requested unit."""

        value = self._required_size(self.ai_core_spec.l0_b_size, "AICoreSpec.l0_b_size")
        return convert_size(value, unit)

    def l0_c_size(self, unit: SizeUnit | str = "bytes") -> int | float:
        """Return the L0C size in the requested unit."""

        value = self._required_size(self.ai_core_spec.l0_c_size, "AICoreSpec.l0_c_size")
        return convert_size(value, unit)

    def l1_size(self, unit: SizeUnit | str = "bytes") -> int | float:
        """Return the L1 size in the requested unit."""

        value = self._required_size(self.ai_core_spec.l1_size, "AICoreSpec.l1_size")
        return convert_size(value, unit)

    def l2_size(self, unit: SizeUnit | str = "bytes") -> int | float:
        """Return the L2 size in the requested unit."""

        value = self._required_size(self.soc_info.l2_size, "SoCInfo.l2_size")
        return convert_size(value, unit)

    def ai_core_count(self) -> int:
        """Return the AI Core count."""

        return self._required_size(self.soc_info.ai_core_count, "SoCInfo.ai_core_cnt")
