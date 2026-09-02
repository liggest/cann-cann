"""cann-cann 命令行入口"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from types import MappingProxyType
from typing import TextIO, TypeAlias

from .errors import CannCannError


class _QueryKind(Enum):
    SIZE = auto()
    PLATFORM_VALUE = auto()
    AGGREGATE = auto()
    NPU_NAME = auto()
    GLOBAL = auto()


@dataclass(frozen=True, slots=True)
class QuerySpec:
    """CLI 查询项的只读元数据"""

    name: str
    aliases: tuple[str, ...]
    description: str
    kind: _QueryKind
    api_name: str | None = None


_QUERY_SPECS = (
    QuerySpec("UB", (), "AI Core UB 大小", _QueryKind.SIZE, "ub_size"),
    QuerySpec("L0A", ("l0_a",), "AI Core L0A 大小", _QueryKind.SIZE, "l0_a_size"),
    QuerySpec("L0B", ("l0_b",), "AI Core L0B 大小", _QueryKind.SIZE, "l0_b_size"),
    QuerySpec("L0C", ("l0_c",), "AI Core L0C 大小", _QueryKind.SIZE, "l0_c_size"),
    QuerySpec("L1", (), "AI Core L1 大小", _QueryKind.SIZE, "l1_size"),
    QuerySpec("L2", (), "NPU L2 大小", _QueryKind.SIZE, "l2_size"),
    QuerySpec("memory", ("hbm",), "NPU 显存大小", _QueryKind.SIZE, "memory_size"),
    QuerySpec(
        "ai-cores",
        ("ai-core-count", "ai_core_count"),
        "AI Core 数量",
        _QueryKind.PLATFORM_VALUE,
        "ai_core_count",
    ),
    QuerySpec(
        "cube-cores",
        ("c-cores",),
        "Cube Core 数量",
        _QueryKind.PLATFORM_VALUE,
        "cube_core_count",
    ),
    QuerySpec(
        "vector-cores",
        ("v-cores",),
        "Vector Core 数量",
        _QueryKind.PLATFORM_VALUE,
        "vector_core_count",
    ),
    QuerySpec("cores", (), "AI、Cube 和 Vector Core 数量", _QueryKind.AGGREGATE),
    QuerySpec("npu-arch", (), "NPU 架构编号", _QueryKind.PLATFORM_VALUE, "npu_arch"),
    QuerySpec(
        "npu-name",
        ("soc",),
        "当前 NPU 型号，或指定型号的标准名称",
        _QueryKind.NPU_NAME,
        "npu_name",
    ),
    QuerySpec(
        "all-npu-names",
        ("all-socs",),
        "当前安装中的 NPU 配置名称",
        _QueryKind.GLOBAL,
        "all_npu_names",
    ),
    QuerySpec("cann-version", (), "CANN 安装版本", _QueryKind.GLOBAL, "cann_version"),
    QuerySpec("host-arch", ("arch",), "主机处理器架构", _QueryKind.GLOBAL, "host_arch"),
    QuerySpec(
        "ascend-home",
        ("cann-home", "ascend-root", "cann-root", "ascend-path", "cann-path"),
        "CANN 安装根目录",
        _QueryKind.GLOBAL,
        "ascend_home",
    ),
    QuerySpec("os-name", ("os",), "主机操作系统名称", _QueryKind.GLOBAL, "os_name"),
)


def _normalize_query(query: str) -> str:
    return query.casefold().replace("-", "_")


def _build_query_lookup() -> MappingProxyType[str, QuerySpec]:
    lookup: dict[str, QuerySpec] = {}
    for spec in _QUERY_SPECS:
        for name in (spec.name, *spec.aliases):
            normalized = _normalize_query(name)
            previous = lookup.setdefault(normalized, spec)
            if previous is not spec:
                raise RuntimeError(f"CLI 查询别名重复：{name}")
    return MappingProxyType(lookup)


_QUERY_LOOKUP = _build_query_lookup()


@dataclass(frozen=True, slots=True)
class _AggregateResult:
    values: tuple[tuple[str, int | None], ...]


_CLIResult: TypeAlias = str | Path | list[str] | int | float | _AggregateResult


def _version_text() -> str:
    import cann_cann

    return f"cann-cann {cann_cann.__version__}"


def _print_basic_guidance(parser: argparse.ArgumentParser, stream: TextIO) -> None:
    parser.print_usage(file=stream)
    print(f"使用 {parser.prog} -h 查看帮助", file=stream)


def _print_input_error(parser: argparse.ArgumentParser, message: str) -> None:
    print(f"错误：{message}", file=sys.stderr)
    print(file=sys.stderr)
    _print_basic_guidance(parser, sys.stderr)


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
        print(_version_text())
        parser.exit()


class _NPUNameAction(argparse.Action):
    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: str,
        option_string: str | None = None,
    ) -> None:
        previous = getattr(namespace, "npu_name_option", None)
        if previous is not None:
            raise argparse.ArgumentError(self, f"{previous} 和 {option_string} 不能同时使用")
        setattr(namespace, self.dest, values)
        namespace.npu_name_option = option_string


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        _print_input_error(self, message)
        self.exit(2)


def _query_help() -> str:
    lines = []
    for spec in _QUERY_SPECS:
        aliases = f" （别名：{', '.join(spec.aliases)}）" if spec.aliases else ""
        lines.append(f"  {spec.name}{aliases}：{spec.description}")
    return "可用的查询项：\n" + "\n".join(lines)


def _parser(prog: str = "cann-cann") -> argparse.ArgumentParser:
    parser = _ArgumentParser(
        prog=prog,
        description="看看环境上的 NPU 参数\n\n" + _query_help(),
        formatter_class=argparse.RawTextHelpFormatter,
        add_help=False,
    )
    parser._positionals.title = "位置参数"
    parser._optionals.title = "选项"
    parser.add_argument("-h", "--help", action="help", help="显示帮助信息并退出")
    parser.add_argument("-v", "--version", action=_VersionAction, help="显示版本信息并退出")
    parser.add_argument("query", nargs="?", metavar="QUERY", help="要执行的查询项")
    parser.set_defaults(npu_name_option=None)
    parser.add_argument(
        "-n",
        "--npu-name",
        "--soc",
        action=_NPUNameAction,
        metavar="NAME",
        help="读取指定 NPU 的配置；支持 A2/A3/A5/950 等别名，可省略 Ascend 前缀",
    )
    units = parser.add_mutually_exclusive_group()
    units.add_argument(
        "--unit",
        type=str.lower,
        choices=("b", "bytes", "kb", "kib", "mb", "mib", "gb", "gib"),
        metavar="UNIT",
        help="存储空间大小的输出单位（默认：bytes）",
    )
    units.add_argument("--kb", "--kib", action="store_const", const="kb", dest="short_unit", help="以 kb 输出")
    units.add_argument("--mb", "--mib", action="store_const", const="mb", dest="short_unit", help="以 mb 输出")
    units.add_argument("--gb", "--gib", action="store_const", const="gb", dest="short_unit", help="以 gb 输出")
    return parser


def _unit_was_supplied(args: argparse.Namespace) -> bool:
    return args.unit is not None or args.short_unit is not None


def _reject_unit(args: argparse.Namespace) -> None:
    if _unit_was_supplied(args):
        raise ValueError("单位选项只能用于查询存储空间大小")


def _reject_npu_name(args: argparse.Namespace, query: str) -> None:
    if args.npu_name is not None:
        option = args.npu_name_option or "--npu-name"
        raise ValueError(f"查询 {query} 时不能使用 {option}")


def _run_cores(npu_name: str | None) -> _AggregateResult:
    import cann_cann

    config = cann_cann.platform_config(npu_name)
    soc_info = config.soc_info
    return _AggregateResult(
        (
            ("ai-cores", soc_info.ai_core_count),
            ("cube-cores", soc_info.cube_core_count),
            ("vector-cores", soc_info.vector_core_count),
        )
    )


def _run(args: argparse.Namespace) -> _CLIResult:
    # 运行时导入，确保 CLI 始终通过公开 Python API 完成查询
    import cann_cann

    spec = _QUERY_LOOKUP.get(_normalize_query(args.query))
    if spec is None:
        raise ValueError(f"未知的查询项：{args.query}")

    if spec.kind is _QueryKind.SIZE:
        function = getattr(cann_cann, spec.api_name)
        unit = args.unit or args.short_unit or "bytes"
        return function(npu_name=args.npu_name, unit=unit)

    _reject_unit(args)
    if spec.kind is _QueryKind.PLATFORM_VALUE:
        function = getattr(cann_cann, spec.api_name)
        return function(npu_name=args.npu_name)
    if spec.kind is _QueryKind.AGGREGATE:
        return _run_cores(args.npu_name)
    if spec.kind is _QueryKind.NPU_NAME:
        if args.npu_name is not None:
            return cann_cann.resolve_npu_name(args.npu_name)
        return cann_cann.npu_name()

    _reject_npu_name(args, spec.name)
    function = getattr(cann_cann, spec.api_name)
    return function()


def _print_result(result: _CLIResult) -> None:
    if isinstance(result, list):
        for item in result:
            print(item)
        return
    if isinstance(result, _AggregateResult):
        for key, value in result.values:
            print(f"{key}: {'none' if value is None else value}")
        return
    print(result)


def main(argv: Sequence[str] | None = None) -> int:
    """运行命令行程序并返回退出码"""

    prog = Path(sys.argv[0]).name if argv is None else "cann-cann"
    parser = _parser(prog)
    args = parser.parse_args(argv)
    if args.query is None:
        if args.npu_name is not None or _unit_was_supplied(args):
            _print_input_error(parser, "使用 NPU 名称或单位选项时必须提供 query")
            return 2
        print(_version_text())
        _print_basic_guidance(parser, sys.stdout)
        return 0

    try:
        _print_result(_run(args))
    except CannCannError as error:
        print(f"错误：{error}", file=sys.stderr)
        return 1
    except ValueError as error:
        _print_input_error(parser, str(error))
        return 2
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
