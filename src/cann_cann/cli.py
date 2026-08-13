"""cann-cann 命令行入口"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import TypeAlias

from .errors import CannCannError

_SIZE_QUERIES = {
    "l0_a": "l0_a_size",
    "l0a": "l0_a_size",
    "l0_b": "l0_b_size",
    "l0b": "l0_b_size",
    "l0_c": "l0_c_size",
    "l0c": "l0_c_size",
    "l1": "l1_size",
    "l2": "l2_size",
    "hbm": "memory_size",
    "memory": "memory_size",
    "ub": "ub_size",
}
_COUNT_QUERIES = {
    "ai_core_count": "ai_core_count",
    "ai_cores": "ai_core_count",
    "cores": "ai_core_count",
}
_CLIResult: TypeAlias = str | list[str] | int | float


class _VersionAction(argparse.Action):
    def __init__(self, option_strings: Sequence[str], dest: str, **kwargs) -> None:
        super().__init__(option_strings, dest, nargs=0, **kwargs)

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: object,
        option_string: str | None = None,
    ) -> None:
        import cann_cann

        print(f"{parser.prog} {cann_cann.__version__}")
        parser.exit()


def _parser(prog: str = "cann-cann") -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=prog,
        description="看看环境上的 NPU 参数",
        epilog="AI Core 数量可用 AI_CORE_COUNT、cores 或 ai-cores 查询",
        add_help=False,
    )
    parser._positionals.title = "位置参数"
    parser._optionals.title = "选项"
    parser.add_argument("-h", "--help", action="help", help="显示帮助信息并退出")
    parser.add_argument("-v", "--version", action=_VersionAction, help="显示版本信息并退出")
    parser.add_argument(
        "query",
        help="例如 UB、L1、memory、cores、npu-name 或 all-npu-names",
    )
    parser.add_argument(
        "--npu-name",
        metavar="NAME",
        help="读取指定 NPU 名称的配置，不再自动探测",
    )
    units = parser.add_mutually_exclusive_group()
    units.add_argument(
        "--unit",
        choices=("bytes", "kb", "kib", "mb", "mib", "gb", "gib"),
        help="存储空间大小的输出单位（默认：bytes）",
    )
    units.add_argument("--kb", action="store_const", const="kb", dest="short_unit", help="以 kb 输出")
    units.add_argument("--kib", action="store_const", const="kib", dest="short_unit", help="同 --kb")
    units.add_argument("--mb", action="store_const", const="mb", dest="short_unit", help="以 mb 输出")
    units.add_argument("--mib", action="store_const", const="mib", dest="short_unit", help="同 --mb")
    units.add_argument("--gb", action="store_const", const="gb", dest="short_unit", help="以 gb 输出")
    units.add_argument("--gib", action="store_const", const="gib", dest="short_unit", help="同 --gb")
    return parser


def _run(args: argparse.Namespace) -> _CLIResult:
    # 运行时导入，确保 CLI 始终通过公开 Python API 完成查询
    import cann_cann

    query = args.query.lower().replace("-", "_")
    unit = args.unit or args.short_unit or "bytes"

    if query == "npu_name":
        if args.npu_name is not None:
            raise ValueError("查询 npu-name 时不能使用 --npu-name")
        return cann_cann.npu_name()
    if query == "all_npu_names":
        if args.npu_name is not None:
            raise ValueError("查询 all-npu-names 时不能使用 --npu-name")
        return cann_cann.all_npu_names()
    if query in _SIZE_QUERIES:
        function = getattr(cann_cann, _SIZE_QUERIES[query])
        return function(npu_name=args.npu_name, unit=unit)
    if query in _COUNT_QUERIES:
        if args.unit is not None or args.short_unit is not None:
            raise ValueError("单位选项只能用于查询存储空间大小")
        function = getattr(cann_cann, _COUNT_QUERIES[query])
        return function(npu_name=args.npu_name)

    raise ValueError(f"未知的查询项：{args.query}")


def _print_result(result: _CLIResult) -> None:
    if isinstance(result, list):
        for item in result:
            print(item)
        return
    print(result)


def main(argv: Sequence[str] | None = None) -> int:
    """运行命令行程序并返回退出码"""
    prog = Path(sys.argv[0]).name if argv is None else "cann-cann"
    parser = _parser(prog)
    args = parser.parse_args(argv)
    try:
        _print_result(_run(args))
    except (CannCannError, ValueError) as error:
        print(f"错误：{error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
