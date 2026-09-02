from __future__ import annotations

import sys
from pathlib import Path
from shutil import copyfile
from types import SimpleNamespace

import pytest

import cann_cann
from cann_cann.cli import _parser, main
from cann_cann.errors import CannCannError


def _basic_guidance(command: str = "cann-cann") -> str:
    return f"{_parser(command).format_usage()}使用 {command} -h 查看帮助\n"


def _input_error(message: str, command: str = "cann-cann") -> str:
    return f"错误：{message}\n\n{_basic_guidance(command)}"


def test_size_query_is_case_insensitive_and_accepts_npu_option_before_or_after(monkeypatch, capsys) -> None:
    calls = []

    def fake_ub_size(*, npu_name, unit):
        calls.append((npu_name, unit))
        return 192

    monkeypatch.setattr(cann_cann, "ub_size", fake_ub_size, raising=False)

    assert main(["-n", "A5", "uB", "--kb"]) == 0
    assert capsys.readouterr().out == "192\n"
    assert main(["uB", "--soc", "A5DT", "--kb"]) == 0
    assert capsys.readouterr().out == "192\n"
    assert main(["uB", "--npu-name", "Ascend910_9392", "--kb"]) == 0
    assert capsys.readouterr().out == "192\n"
    assert calls == [("A5", "kb"), ("A5DT", "kb"), ("Ascend910_9392", "kb")]


def test_long_unit_option_is_case_insensitive(monkeypatch, capsys) -> None:
    units = []

    def fake_l0_a_size(*, npu_name, unit):
        assert npu_name is None
        units.append(unit)
        return 65536

    monkeypatch.setattr(cann_cann, "l0_a_size", fake_l0_a_size, raising=False)

    assert main(["L0A", "--unit", "B"]) == 0
    assert capsys.readouterr().out == "65536\n"
    assert main(["L0A", "--unit", "mIb"]) == 0
    assert capsys.readouterr().out == "65536\n"
    assert units == ["b", "mib"]


def test_memory_query_and_hbm_alias(monkeypatch, capsys) -> None:
    calls = []

    def fake_memory_size(*, npu_name, unit):
        calls.append((npu_name, unit))
        return 64

    monkeypatch.setattr(cann_cann, "memory_size", fake_memory_size, raising=False)

    assert main(["memory", "--npu-name", "Ascend910B2", "--gb"]) == 0
    assert capsys.readouterr().out == "64\n"
    assert main(["hBm", "--gib"]) == 0
    assert capsys.readouterr().out == "64\n"
    assert calls == [("Ascend910B2", "gb"), (None, "gb")]


@pytest.mark.parametrize(
    ("option", "unit"),
    [("--kb", "kb"), ("--kib", "kb"), ("--mb", "mb"), ("--mib", "mb"), ("--gb", "gb"), ("--gib", "gb")],
)
def test_short_unit_option_pairs_use_the_same_normalized_unit(monkeypatch, capsys, option, unit) -> None:
    calls = []

    def fake_ub_size(*, npu_name, unit):
        calls.append((npu_name, unit))
        return 1

    monkeypatch.setattr(cann_cann, "ub_size", fake_ub_size, raising=False)

    assert main(["UB", option]) == 0
    assert capsys.readouterr().out == "1\n"
    assert calls == [(None, unit)]


@pytest.mark.parametrize("query", ["npu-name", "soc"])
def test_npu_name_aliases(monkeypatch, capsys, query) -> None:
    monkeypatch.setattr(cann_cann, "npu_name", lambda: "Ascend910_9392", raising=False)

    assert main([query]) == 0
    captured = capsys.readouterr()
    assert captured.out == "Ascend910_9392\n"
    assert captured.err == ""


@pytest.mark.parametrize("query", ["ALL-NPU-NAMES", "all-socs"])
def test_all_npu_names_aliases_print_one_per_line(monkeypatch, capsys, query) -> None:
    monkeypatch.setattr(
        cann_cann,
        "all_npu_names",
        lambda: ["Ascend910B2", "Ascend950PR_9589"],
        raising=False,
    )

    assert main([query]) == 0
    captured = capsys.readouterr()
    assert captured.out == "Ascend910B2\nAscend950PR_9589\n"
    assert captured.err == ""


@pytest.mark.parametrize(
    ("query", "api_name", "result"),
    [
        ("ai-core-count", "ai_core_count", 24),
        ("AI_CORE_COUNT", "ai_core_count", 24),
        ("ai-cores", "ai_core_count", 24),
        ("cube-cores", "cube_core_count", 12),
        ("c-cores", "cube_core_count", 12),
        ("vector-cores", "vector_core_count", 8),
        ("v-cores", "vector_core_count", 8),
        ("npu-arch", "npu_arch", 2201),
    ],
)
def test_platform_value_queries(monkeypatch, capsys, query, api_name, result) -> None:
    calls = []

    def fake_query(*, npu_name):
        calls.append(npu_name)
        return result

    monkeypatch.setattr(cann_cann, api_name, fake_query, raising=False)

    assert main([query, "--soc", "A5"]) == 0
    captured = capsys.readouterr()
    assert captured.out == f"{result}\n"
    assert captured.err == ""
    assert calls == ["A5"]


def test_platform_value_query_rejects_size_unit(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cann_cann, "ai_core_count", lambda **_: 24, raising=False)

    assert main(["AI_CORE_COUNT", "--kb"]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == _input_error("单位选项只能用于查询存储空间大小")


def test_cores_loads_config_once_and_prints_stable_aggregate(monkeypatch, capsys) -> None:
    calls = []
    config = SimpleNamespace(
        soc_info=SimpleNamespace(
            ai_core_count=24,
            cube_core_count=12,
            vector_core_count=8,
        )
    )

    def fake_platform_config(npu_name):
        calls.append(npu_name)
        return config

    monkeypatch.setattr(cann_cann, "platform_config", fake_platform_config)

    assert main(["cores", "-n", "A5"]) == 0
    captured = capsys.readouterr()
    assert captured.out == "ai-cores: 24\ncube-cores: 12\nvector-cores: 8\n"
    assert captured.err == ""
    assert calls == ["A5"]


def test_cores_prints_none_for_each_missing_typed_field(monkeypatch, capsys) -> None:
    config = SimpleNamespace(
        soc_info=SimpleNamespace(
            ai_core_count=24,
            cube_core_count=None,
            vector_core_count=None,
        )
    )
    monkeypatch.setattr(cann_cann, "platform_config", lambda _: config)

    assert main(["cores"]) == 0
    captured = capsys.readouterr()
    assert captured.out == "ai-cores: 24\ncube-cores: none\nvector-cores: none\n"
    assert captured.err == ""


def test_cores_rejects_unit(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cann_cann, "platform_config", lambda _: None)

    assert main(["cores", "--unit", "bytes"]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == _input_error("单位选项只能用于查询存储空间大小")


@pytest.mark.parametrize(
    ("query", "api_name", "result"),
    [
        ("cann-version", "cann_version", "8.3.RC1"),
        ("arch", "host_arch", "aarch64"),
        ("ascend-home", "ascend_home", Path("/opt/Ascend/cann")),
        ("cann-home", "ascend_home", Path("/opt/Ascend/cann")),
        ("ascend-root", "ascend_home", Path("/opt/Ascend/cann")),
        ("cann-root", "ascend_home", Path("/opt/Ascend/cann")),
        ("ascend-path", "ascend_home", Path("/opt/Ascend/cann")),
        ("cann-path", "ascend_home", Path("/opt/Ascend/cann")),
        ("os-name", "os_name", "Ubuntu 24.04 LTS"),
        ("os", "os_name", "Ubuntu 24.04 LTS"),
    ],
)
def test_global_queries_and_aliases(monkeypatch, capsys, query, api_name, result) -> None:
    monkeypatch.setattr(cann_cann, api_name, lambda: result, raising=False)

    assert main([query]) == 0
    captured = capsys.readouterr()
    assert captured.out == f"{result}\n"
    assert captured.err == ""


@pytest.mark.parametrize("option", ["-n", "--npu-name", "--soc"])
def test_global_query_rejects_npu_option_with_actual_option_name(monkeypatch, capsys, option) -> None:
    monkeypatch.setattr(cann_cann, "npu_name", lambda: "unused")

    assert main(["npu-name", option, "A5"]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == _input_error(f"查询 npu-name 时不能使用 {option}")


def test_global_query_rejects_unit(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cann_cann, "host_arch", lambda: "unused", raising=False)

    assert main(["arch", "--kb"]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == _input_error("单位选项只能用于查询存储空间大小")


def test_repeated_npu_options_are_argparse_error(capsys) -> None:
    with pytest.raises(SystemExit) as error:
        main(["UB", "-n", "A5", "--soc", "A3"])

    assert error.value.code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == _input_error("argument -n/--npu-name/--soc: -n 和 --soc 不能同时使用")


def test_argparse_error_appends_basic_guidance(capsys) -> None:
    with pytest.raises(SystemExit) as error:
        main(["UB", "--unit", "invalid"])

    assert error.value.code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == _input_error("argument --unit: invalid choice: 'invalid' (choose from b, bytes, kb, kib, mb, mib, gb, gib)")


@pytest.mark.parametrize("command", ["cann-cann", "ccann"])
def test_unknown_query_appends_guidance_for_invoked_name(monkeypatch, capsys, command) -> None:
    monkeypatch.setattr(sys, "argv", [f"/usr/local/bin/{command}", "not-a-query"])

    assert main() == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == _input_error("未知的查询项：not-a-query", command)


def test_help_lists_each_query_and_its_aliases_on_one_line(capsys) -> None:
    with pytest.raises(SystemExit) as error:
        main(["--help"])
    assert error.value.code == 0

    output = capsys.readouterr().out
    query_lines = output.split("可用的查询项：\n", maxsplit=1)[1].split("\n\n", maxsplit=1)[0].splitlines()
    assert len(query_lines) == 18
    for query in (
        "UB",
        "L0A",
        "L0B",
        "L0C",
        "L1",
        "L2",
        "memory",
        "ai-cores",
        "cube-cores",
        "vector-cores",
        "cores",
        "npu-arch",
        "npu-name",
        "all-npu-names",
        "cann-version",
        "arch",
        "ascend-home",
        "os-name",
    ):
        assert sum(line.startswith(f"  {query}") for line in query_lines) == 1
    assert any("ai-core-count" in line and "AI Core 数量" in line for line in query_lines)
    assert any("soc" in line and "npu-name" in line for line in query_lines)
    assert any("all-socs" in line and "all-npu-names" in line for line in query_lines)
    assert any("c-cores" in line and "cube-cores" in line for line in query_lines)
    assert any("v-cores" in line and "vector-cores" in line for line in query_lines)
    assert any("cann-path" in line and "ascend-home" in line for line in query_lines)
    assert "--kb, --kib           以 kb 输出" in output
    assert "--mb, --mib           以 mb 输出" in output
    assert "--gb, --gib           以 gb 输出" in output
    assert "同 --" not in output
    assert "epilog" not in output


@pytest.mark.parametrize("command", ["cann-cann", "ccann"])
@pytest.mark.parametrize("option", ["-v", "--version"])
def test_version_options_always_use_product_name(monkeypatch, capsys, command, option) -> None:
    monkeypatch.setattr(sys, "argv", [f"/usr/local/bin/{command}", option])

    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 0
    captured = capsys.readouterr()
    assert captured.out == f"cann-cann {cann_cann.__version__}\n"
    assert captured.err == ""


def test_help_uses_invoked_name(monkeypatch, capsys) -> None:
    monkeypatch.setattr(sys, "argv", ["/usr/local/bin/ccann", "--help"])

    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 0
    assert capsys.readouterr().out.startswith("usage: ccann ")


def test_automatic_usage_exposes_important_options() -> None:
    usage = _parser("ccann").format_usage()

    for option in ("[-h]", "[-v]", "[-n NAME]", "--unit UNIT", "--kb", "--mb", "--gb", "[QUERY]"):
        assert option in usage
    assert "{b,bytes,kb,kib,mb,mib,gb,gib}" not in usage
    assert "QUERY [选项]" not in usage


@pytest.mark.parametrize("command", ["cann-cann", "ccann"])
def test_no_arguments_print_version_usage_and_help_hint(monkeypatch, capsys, command) -> None:
    monkeypatch.setattr(sys, "argv", [f"/usr/local/bin/{command}"])

    assert main() == 0
    captured = capsys.readouterr()
    assert captured.out == f"cann-cann {cann_cann.__version__}\n{_basic_guidance(command)}"
    assert captured.err == ""


@pytest.mark.parametrize("options", [["-n", "A5"], ["--soc", "A5"], ["--unit", "mb"], ["--kb"]])
def test_options_without_query_are_input_error(capsys, options) -> None:
    assert main(options) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == _input_error("使用 NPU 名称或单位选项时必须提供 query")


def test_library_error_is_friendly_and_returns_one(monkeypatch, capsys) -> None:
    def fail(*, npu_name, unit):
        raise CannCannError("找不到 CANN 平台配置")

    monkeypatch.setattr(cann_cann, "l1_size", fail, raising=False)

    assert main(["L1"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "错误：找不到 CANN 平台配置\n"


def test_cli_integrates_alias_config_and_install_info(tmp_path: Path, monkeypatch, capsys) -> None:
    arch_directory = tmp_path / "aarch64-linux"
    config_directory = arch_directory / "data" / "platform_config"
    config_directory.mkdir(parents=True)
    fixture = Path(__file__).parent / "fixtures" / "platform_config" / "Ascend950PR_9589.ini"
    copyfile(fixture, config_directory / fixture.name)
    copyfile(fixture, config_directory / "Kirin9030.ini")
    (arch_directory / "ascend_toolkit_install.info").write_text("version=8.3.RC1\n", encoding="utf-8")
    monkeypatch.setenv("ASCEND_HOME_PATH", str(tmp_path))
    monkeypatch.setattr(cann_cann._environment.platform, "machine", lambda: "aarch64")

    caches = (
        cann_cann._default_platform_config_directory,
        cann_cann._platform_config_by_name,
        cann_cann._environment.ascend_home,
        cann_cann._environment.host_arch,
        cann_cann._environment.cann_install_info,
    )
    for cached in caches:
        cached.cache_clear()
    try:
        assert main(["-n", "A5", "cores"]) == 0
        captured = capsys.readouterr()
        assert captured.out == "ai-cores: 32\ncube-cores: 32\nvector-cores: 64\n"
        assert captured.err == ""

        assert main(["-n", "Kirin9030", "UB"]) == 0
        captured = capsys.readouterr()
        assert captured.out == "253952\n"
        assert captured.err == ""

        assert main(["cann-version"]) == 0
        captured = capsys.readouterr()
        assert captured.out == "8.3.RC1\n"
        assert captured.err == ""
    finally:
        for cached in caches:
            cached.cache_clear()
