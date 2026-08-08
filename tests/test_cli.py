from __future__ import annotations

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


def test_detect_npu_name(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        cann_cann,
        "detect_npu_name",
        lambda: "Ascend910_9392",
        raising=False,
    )

    assert main(["npu-name"]) == 0
    assert capsys.readouterr().out == "Ascend910_9392\n"


def test_list_npu_names_prints_one_per_line(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        cann_cann,
        "list_npu_names",
        lambda: ["Ascend910B2", "Ascend950PR_9589"],
        raising=False,
    )

    assert main(["LIST-NPU-NAMES"]) == 0
    assert capsys.readouterr().out == "Ascend910B2\nAscend950PR_9589\n"


def test_count_query_rejects_size_unit(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cann_cann, "ai_core_count", lambda **_: 24, raising=False)

    assert main(["AI_CORE_COUNT", "--kb"]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "size units can only be used with size queries" in captured.err


def test_library_error_is_friendly(monkeypatch, capsys) -> None:
    def fail(*, npu_name, unit):
        raise CannCannError("CANN platform configuration was not found")

    monkeypatch.setattr(cann_cann, "l1_size", fail, raising=False)

    assert main(["L1"]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "error: CANN platform configuration was not found\n"
