"""Command-line interface for :mod:`cann_cann`."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

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
    "ub": "ub_size",
}
_COUNT_QUERIES = {"ai_core_count": "ai_core_count"}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cann-cann",
        description="Inspect NPU platform configuration shipped with CANN.",
    )
    parser.add_argument(
        "query",
        help=("query to run: npu-name, list-npu-names, UB, L0A, L0B, L0C, L1, L2, or AI_CORE_COUNT"),
    )
    parser.add_argument(
        "--npu-name",
        metavar="NAME",
        help="read configuration for this NPU name instead of detecting it",
    )
    units = parser.add_mutually_exclusive_group()
    units.add_argument(
        "--unit",
        choices=("bytes", "kb", "kib", "mb", "mib"),
        help="output unit for size queries (default: bytes)",
    )
    units.add_argument("--kb", action="store_const", const="kb", dest="short_unit")
    units.add_argument("--kib", action="store_const", const="kib", dest="short_unit")
    units.add_argument("--mb", action="store_const", const="mb", dest="short_unit")
    units.add_argument("--mib", action="store_const", const="mib", dest="short_unit")
    return parser


def _run(args: argparse.Namespace) -> object:
    # Import at execution time so importing the CLI itself never initializes ACL.
    import cann_cann

    query = args.query.lower().replace("-", "_")
    unit = args.unit or args.short_unit or "bytes"

    if query == "npu_name":
        if args.npu_name is not None:
            raise ValueError("--npu-name cannot be used with the npu-name query")
        return cann_cann.detect_npu_name()
    if query == "list_npu_names":
        if args.npu_name is not None:
            raise ValueError("--npu-name cannot be used with the list-npu-names query")
        return cann_cann.list_npu_names()
    if query in _SIZE_QUERIES:
        function = getattr(cann_cann, _SIZE_QUERIES[query])
        return function(npu_name=args.npu_name, unit=unit)
    if query in _COUNT_QUERIES:
        if args.unit is not None or args.short_unit is not None:
            raise ValueError("size units can only be used with size queries")
        function = getattr(cann_cann, _COUNT_QUERIES[query])
        return function(npu_name=args.npu_name)

    raise ValueError(f"unknown query: {args.query}")


def _print_result(result: object) -> None:
    if isinstance(result, (list, tuple)):
        for item in result:
            print(item)
        return
    print(result)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the ``cann-cann`` command and return its process exit code."""
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        _print_result(_run(args))
    except (CannCannError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
