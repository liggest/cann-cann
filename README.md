# cann-cann

`cann-cann` is a small community-maintained Python library and command-line tool
for reading the NPU platform configuration shipped with an installed CANN
toolkit.

> The project is under initial v0.1 development. The documented API may still
> change before the first release.

## Requirements

- Python 3.10 or newer
- An installed CANN toolkit
- A sourced CANN environment when detecting the local NPU name

The library discovers CANN primarily through `ASCEND_HOME_PATH`. Reading a
configuration for an explicitly named NPU does not require ACL device
detection.

An NPU name such as `Ascend910_9392` identifies a hardware platform
configuration; it is not a device index, a neural-network model, or the CANN
software version. CANN calls the same value a SoC version internally, while
the public cann-cann API consistently calls it `npu_name`.

## Installation

During development, clone the repository and use uv:

```console
uv sync --dev
```

After a release, the package can be installed from its wheel or package index.

## Python API

For a quick query, use the module-level convenience functions:

```python
import cann_cann

cann_cann.detect_npu_name()
cann_cann.list_npu_names()

cann_cann.ub_size()
cann_cann.ub_size(unit="kb")
cann_cann.l0_a_size(npu_name="Ascend910_9392", unit="kb")
```

To inspect several values from one configuration, obtain the cached platform
configuration object:

```python
config = cann_cann.platform_config(npu_name="Ascend910_9392")

config.ai_core_spec.ub_size  # raw platform value in bytes
config.ai_core_spec.l0_a_size
config.soc_info.ai_core_count

config.ub_size(unit="kb")  # convenience conversion
config.l2_size(unit="mb")
```

Typed properties cover the most useful fields. Unrecognized fields and
sections remain available as their original INI strings:

```python
config.ai_core_spec.raw("new_cann_field")
config.raw_section("UnknownSection")
```

## Command line

Detect the NPU name reported by ACL or list the names represented by the
installed CANN platform configurations:

```console
cann-cann npu-name
cann-cann list-npu-names
```

Query common memory sizes and counts:

```console
cann-cann UB
cann-cann UB --kb
cann-cann L0A --unit kib
cann-cann L2 --mb --npu-name Ascend910_9392
cann-cann AI_CORE_COUNT
```

Query names are case-insensitive. v0.1 supports `UB`, `L0A`, `L0B`, `L0C`,
`L1`, `L2`, and `AI_CORE_COUNT`.

The initial test matrix focuses on Ascend 910B, Ascend 910 93-series, Ascend
950PR, and Ascend 950DT configurations. There is no hard-coded NPU allowlist:
other configurations with compatible fields can be loaded as well.

## Units

Platform configuration values are stored in bytes and are returned unchanged
by typed section properties. Convenience functions and methods default to
`unit="bytes"`.

For compatibility with common accelerator tooling, `kb` and `kib` both mean
1024 bytes; `mb` and `mib` both mean 1024² bytes. The CLI shortcuts `--kb`,
`--kib`, `--mb`, and `--mib` select the corresponding unit.

## Errors

The Python API raises `CannCannError` subclasses when CANN cannot be found, an
NPU name cannot be detected, or a platform configuration cannot be used.
Applications can normally catch this one base class; callers that need a
fallback may catch `NPUDetectionError` or `PlatformConfigNotFoundError` more
specifically. Invalid arguments, such as an unsupported unit, raise the
standard `ValueError`. The CLI prints expected errors concisely and exits
non-zero. If local detection is unavailable, pass an explicit NPU name:

```console
cann-cann UB --npu-name Ascend910_9392
```

## Development

```console
uv run ruff format --check .
uv run ruff check .
uv run pytest
uv build
```
