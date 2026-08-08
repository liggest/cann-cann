from __future__ import annotations

import sys

import cann_cann
from cann_cann.cli import main
from cann_cann.errors import CannCannError


def test_size_query_is_case_insensitive(monkeypatch, capsys) -> None:
    calls = []

    def fake_ub_size(*, npu_name, unit):
        calls.append((npu_name, unit))
        return 192

    monkeypatch.setattr(cann_cann, "ub_size", fake_ub_size, raising=False)

    assert main(["uB", "--npu-name", "Ascend910_9392", "--kb"]) == 0
    assert capsys.readouterr().out == "192\n"
    assert calls == [("Ascend910_9392", "kb")]


def test_long_unit_option(monkeypatch, capsys) -> None:
    def fake_l0_a_size(*, npu_name, unit):
        assert npu_name is None
        assert unit == "mib"
        return 0.0625

    monkeypatch.setattr(cann_cann, "l0_a_size", fake_l0_a_size, raising=False)

    assert main(["L0A", "--unit", "mib"]) == 0
    assert capsys.readouterr().out == "0.0625\n"


def test_npu_name(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        cann_cann,
        "npu_name",
        lambda: "Ascend910_9392",
        raising=False,
    )

    assert main(["npu-name"]) == 0
    assert capsys.readouterr().out == "Ascend910_9392\n"


def test_all_npu_names_prints_one_per_line(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        cann_cann,
        "all_npu_names",
        lambda: ["Ascend910B2", "Ascend950PR_9589"],
        raising=False,
    )

    assert main(["ALL-NPU-NAMES"]) == 0
    assert capsys.readouterr().out == "Ascend910B2\nAscend950PR_9589\n"


def test_count_query_rejects_size_unit(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cann_cann, "ai_core_count", lambda **_: 24, raising=False)

    assert main(["AI_CORE_COUNT", "--kb"]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "单位选项只能用于查询存储空间大小" in captured.err


def test_ai_core_count_aliases(monkeypatch, capsys) -> None:
    calls = []

    def fake_ai_core_count(*, npu_name):
        calls.append(npu_name)
        return 24

    monkeypatch.setattr(cann_cann, "ai_core_count", fake_ai_core_count, raising=False)

    assert main(["cores", "--npu-name", "Ascend910_9392"]) == 0
    assert capsys.readouterr().out == "24\n"
    assert main(["ai-cores"]) == 0
    assert capsys.readouterr().out == "24\n"
    assert calls == ["Ascend910_9392", None]


def test_help_explains_ai_core_count_aliases(capsys) -> None:
    try:
        main(["--help"])
    except SystemExit as error:
        assert error.code == 0

    output = capsys.readouterr().out
    assert "AI_CORE_COUNT" in output
    assert "cores" in output
    assert "ai-cores" in output
    assert "--kib" in output and "同 --kb" in output
    assert "--mib" in output and "同 --mb" in output


def test_short_command_help_uses_invoked_name(monkeypatch, capsys) -> None:
    monkeypatch.setattr(sys, "argv", ["/usr/local/bin/ccann", "--help"])

    try:
        main()
    except SystemExit as error:
        assert error.code == 0

    assert capsys.readouterr().out.startswith("usage: ccann ")


def test_library_error_is_friendly(monkeypatch, capsys) -> None:
    def fail(*, npu_name, unit):
        raise CannCannError("找不到 CANN 平台配置")

    monkeypatch.setattr(cann_cann, "l1_size", fail, raising=False)

    assert main(["L1"]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "错误：找不到 CANN 平台配置\n"
