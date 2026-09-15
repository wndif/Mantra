"""Command-line interface for Mantra2."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .evaluate import evaluate_candidates
from .mutate import generate_mutants, write_manifest
from .operators import (
    DEFAULT_CATALOG,
    DEFAULT_PATTERNS,
    load_catalog,
    load_patterns,
    schema_to_operator,
)
from .project import build_layout
from .pyverilog_patch import apply_patch, check_patch_state


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mantra2",
        description="Mutate a single Verilog project and classify the mutants.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    mutate = subparsers.add_parser(
        "mutate", help="inject Mantra-style faults into a Verilog project"
    )
    mutate.add_argument(
        "--source",
        action="append",
        required=True,
        metavar="FILE",
        help="RTL file to mutate (repeat for multi-file projects)",
    )
    mutate.add_argument(
        "--root",
        type=Path,
        help="project root used to resolve relative paths "
        "(default: common parent of the sources)",
    )
    mutate.add_argument(
        "--out",
        type=Path,
        default=Path("mantra"),
        help="output directory for mutants (default: mantra)",
    )
    mutate.add_argument(
        "--operator",
        action="append",
        metavar="SCHEMA",
        help="mutation schema to apply (repeatable; default: all schemas)",
    )
    mutate.add_argument(
        "--per-operator",
        type=int,
        default=1,
        help="mutation points per schema and source file (default: 1)",
    )
    mutate.add_argument(
        "--all-locations",
        action="store_true",
        help="mutate every matching location instead of sampling",
    )
    mutate.add_argument("--seed", type=int, default=0, help="random seed (default: 0)")
    mutate.add_argument(
        "--patterns",
        type=Path,
        default=DEFAULT_PATTERNS,
        help="mutation-patterns YAML file",
    )
    mutate.add_argument(
        "--catalog", type=Path, default=DEFAULT_CATALOG, help="operator catalog YAML"
    )
    mutate.add_argument(
        "--manifest",
        type=Path,
        help="mutant metadata CSV (default: <out>/mutants.csv)",
    )

    evaluate = subparsers.add_parser(
        "evaluate", help="simulate mutants and mark them observable or equivalent"
    )
    evaluate.add_argument("--source", action="append", required=True, metavar="FILE")
    evaluate.add_argument("--root", type=Path)
    evaluate.add_argument("--testbench", required=True, metavar="FILE")
    evaluate.add_argument(
        "--manifest",
        type=Path,
        help="mutant metadata CSV (default: mantra/mutants.csv)",
    )
    evaluate.add_argument(
        "--backend",
        choices=("iverilog", "vcs"),
        default="iverilog",
        help="simulator backend (default: iverilog)",
    )
    evaluate.add_argument("--work-dir", type=Path, default=Path("work"))
    evaluate.add_argument("--top", help="top module for Icarus Verilog")
    evaluate.add_argument("--timeout", type=int, default=300)
    evaluate.add_argument("--limit", type=int, help="evaluate only the first N mutants")
    evaluate.add_argument("--output-filename", default="output.txt")

    setup = subparsers.add_parser(
        "setup-pyverilog", help="patch the installed PyVerilog 1.2.1"
    )
    setup.add_argument(
        "--yes",
        action="store_true",
        help="confirm replacement inside the active environment",
    )

    listing = subparsers.add_parser(
        "list-operators", help="list available mutation schemas"
    )
    listing.add_argument("--patterns", type=Path, default=DEFAULT_PATTERNS)
    listing.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)

    return parser


def _cmd_mutate(args) -> int:
    project = build_layout(
        [Path(item) for item in args.source],
        root=args.root,
        testbench=None,
        output_filename="output.txt",
    )
    out_dir = args.out
    if not out_dir.is_absolute():
        out_dir = project.root / out_dir
    manifest = args.manifest or (out_dir / "mutants.csv")

    records = generate_mutants(
        project,
        out_dir=out_dir,
        patterns_path=args.patterns,
        catalog_path=args.catalog,
        operators=args.operator,
        per_operator=None if args.all_locations else args.per_operator,
        seed=args.seed,
    )
    write_manifest(records, manifest)

    generated = [item for item in records if item.status == "generated"]
    failed = [item for item in records if item.status != "generated"]
    print(
        json.dumps(
            {
                "generated": len(generated),
                "failed": len(failed),
                "out_dir": str(out_dir),
                "manifest": str(manifest),
            },
            indent=2,
        )
    )
    return 0


def _cmd_evaluate(args) -> int:
    project = build_layout(
        [Path(item) for item in args.source],
        root=args.root,
        testbench=Path(args.testbench),
        output_filename=args.output_filename,
    )
    manifest = args.manifest or (project.root / "mantra" / "mutants.csv")
    if not manifest.is_file():
        raise FileNotFoundError(
            f"{manifest} not found; run 'mantra2 mutate --manifest {manifest}' first"
        )
    output = evaluate_candidates(
        project,
        manifest_path=manifest,
        work_root=args.work_dir.resolve(),
        backend=args.backend,
        top=args.top,
        timeout=args.timeout,
        limit=args.limit,
    )
    print(output)
    return 0


def _cmd_setup_pyverilog(args) -> int:
    if not args.yes:
        for name, destination, identical in check_patch_state():
            state = "up to date" if identical else "needs patch"
            print(f"{state}: {name} -> {destination}")
        print("\nRe-run with --yes inside a dedicated virtual environment to apply.")
        return 0
    for destination in apply_patch(confirm=True):
        print(f"patched {destination}")
    return 0


def _cmd_list_operators(args) -> int:
    patterns = load_patterns(args.patterns)
    catalog = load_catalog(args.catalog)
    to_operator = schema_to_operator(catalog)
    families = (catalog.get("operators") or {}).get
    rows = []
    for schema in sorted(patterns):
        definition = patterns[schema]
        operator = to_operator.get(schema, schema)
        rows.append(
            {
                "schema": schema,
                "operator": operator,
                "family": (families(operator) or {}).get("family", ""),
                "class": definition.get("OPClass"),
                "module": definition.get("module", ""),
            }
        )
    print(json.dumps(rows, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    handlers = {
        "mutate": _cmd_mutate,
        "evaluate": _cmd_evaluate,
        "setup-pyverilog": _cmd_setup_pyverilog,
        "list-operators": _cmd_list_operators,
    }
    handler = handlers.get(args.command)
    if handler is None:
        print(f"error: unknown command: {args.command}", file=sys.stderr)
        return 2
    try:
        return handler(args)
    except (RuntimeError, ValueError, FileNotFoundError) as error:
        # Expected failures: missing iverilog, unknown schema, absent files.
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
