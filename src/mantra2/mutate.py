"""Mutation of a single Verilog project.

Instance identifiers follow the stable ``<stem>_<schema>_<nodeid>_<line>`` form
so mutant names do not drift between runs.  The pipeline: parse with PyVerilog,
collect mutation points that match a parent/child class-name pattern, rewrite
the AST with one operator, and emit the mutant next to a canonical copy of the
original source.
"""

from __future__ import annotations

import copy
import csv
import random
import shutil
import tempfile
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .operators import (
    DEFAULT_CATALOG,
    DEFAULT_PATTERNS,
    load_catalog,
    load_patterns,
    resolve_operator_class,
    schema_to_operator,
    select_schemas,
)
from .project import ProjectLayout

CSV_FIELDS = [
    "instance_id",
    "operator",
    "schema",
    "source_file",
    "node_id",
    "line",
    "mutant_path",
    "files",
    "status",
]


@dataclass(frozen=True)
class MutantRecord:
    """One generated mutant and the metadata needed to simulate it."""

    instance_id: str
    operator: str
    schema: str
    source_file: str
    node_id: int
    line: int
    mutant_path: str
    files: list[str]
    status: str = "generated"
    note: str = ""

    def as_row(self) -> dict[str, str]:
        return {
            "instance_id": self.instance_id,
            "operator": self.operator,
            "schema": self.schema,
            "source_file": self.source_file,
            "node_id": str(self.node_id),
            "line": str(self.line),
            "mutant_path": self.mutant_path,
            "files": ";".join(self.files),
            "status": self.status,
        }


def _import_pyverilog():
    try:
        import pyverilog.vparser.ast as vast
        from pyverilog.ast_code_generator.codegen import ASTCodeGenerator
        from pyverilog.vparser.parser import parse
    except ImportError as error:
        raise RuntimeError(
            "PyVerilog is required for mutation. Install Mantra2 with the "
            "'mutation' extra (pip install 'mantra2[mutation]') and run "
            "'mantra2 setup-pyverilog'."
        ) from error
    return vast, ASTCodeGenerator, parse


def _require_iverilog() -> None:
    """PyVerilog preprocesses every source with ``iverilog -E``."""
    if shutil.which("iverilog") is None:
        raise RuntimeError(
            "Icarus Verilog ('iverilog') was not found on PATH. PyVerilog uses "
            "'iverilog -E' to preprocess Verilog sources, so it is required "
            "even to generate mutants. Install it and re-run: "
            "Debian/Ubuntu 'apt-get install iverilog', "
            "macOS 'brew install icarus-verilog', "
            "Windows 'choco install iverilog'."
        )


def _pattern_matches(
    pattern: list[dict[str, str]], path: list[Any], vast: Any
) -> bool:
    """True when the node path ends with the pattern's class-name sequence."""
    if not path or not isinstance(path[-1], getattr(vast, pattern[-1]["class_name"])):
        return False
    position = 0
    for node in path:
        if isinstance(node, getattr(vast, pattern[position]["class_name"])):
            position += 1
            if position == len(pattern):
                return True
    return False


def _collect_nodes(
    ast: Any, patterns: dict[str, Any], vast: Any
) -> tuple[dict[str, list[int]], dict[int, int]]:
    """Collect candidate node ids per schema, and each node's source line."""
    found: dict[str, list[int]] = defaultdict(list)
    lines: dict[int, int] = {}

    def visit(node: Any, path: list[Any]) -> None:
        if node is None:
            return
        for child in node.children():
            next_path = [*path, child]
            lines[child.nodeid] = child.lineno
            for name, definition in patterns.items():
                if _pattern_matches(definition["pattern"], next_path, vast):
                    found[name].append(child.nodeid)
            visit(child, next_path)

    visit(ast, [])
    return dict(found), lines


def generate_mutants(
    project: ProjectLayout,
    *,
    out_dir: Path,
    patterns_path: Path = DEFAULT_PATTERNS,
    catalog_path: Path = DEFAULT_CATALOG,
    operators: list[str] | None = None,
    per_operator: int | None = 1,
    seed: int = 0,
) -> list[MutantRecord]:
    """Generate mutants for every requested schema of every source file."""
    vast, ASTCodeGenerator, parse = _import_pyverilog()
    _require_iverilog()

    if per_operator is not None and per_operator < 1:
        raise ValueError("--per-operator must be positive")

    random.seed(seed)
    pattern_data = load_patterns(patterns_path)
    catalog = load_catalog(catalog_path)
    to_operator = schema_to_operator(catalog)
    selected = select_schemas(pattern_data, operators)

    out_dir = Path(out_dir)
    if not out_dir.is_absolute():
        out_dir = project.root / out_dir
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    records: list[MutantRecord] = []
    for source in project.sources:
        relatives = {item: project.relative(item) for item in project.sources}
        # PyVerilog derives its preprocessor scratch file name from
        # filelist[0].split("/")[-1], so paths must use forward slashes or
        # Windows paths leak into the file name and produce an invalid path.
        with tempfile.TemporaryDirectory(prefix="mantra2-pyverilog-") as parser_output:
            ast, _directives = parse(
                [source.resolve().as_posix()],
                preprocess_include=[
                    project.root.resolve().as_posix(),
                    source.parent.resolve().as_posix(),
                ],
                outputdir=parser_output,
                debug=False,
            )
        nodes, lines = _collect_nodes(
            ast, {name: pattern_data[name] for name in selected}, vast
        )

        for schema in selected:
            choices = list(dict.fromkeys(nodes.get(schema, [])))
            random.shuffle(choices)
            picked = choices if per_operator is None else choices[:per_operator]
            for node_id in picked:
                instance_id = f"{source.stem}_{schema}_{node_id}_{lines[node_id]}"
                if not _emit_mutant(
                    project,
                    ast,
                    source=source,
                    relatives=relatives,
                    schema=schema,
                    operator=to_operator.get(schema, schema),
                    node_id=node_id,
                    line=lines[node_id],
                    instance_id=instance_id,
                    out_dir=out_dir,
                    pattern_data=pattern_data,
                    ASTCodeGenerator=ASTCodeGenerator,
                    records=records,
                ):
                    continue

    return records


def _emit_mutant(
    project: ProjectLayout,
    ast: Any,
    *,
    source: Path,
    relatives: dict[Path, str],
    schema: str,
    operator: str,
    node_id: int,
    line: int,
    instance_id: str,
    out_dir: Path,
    pattern_data: dict[str, Any],
    ASTCodeGenerator: Any,
    records: list[MutantRecord],
) -> bool:
    """Write one mutant directory; return False when the operator declined."""
    source_relative = project.relative(source)
    try:
        operator_class = resolve_operator_class(pattern_data[schema], schema)
        mutated_ast = operator_class(copy.deepcopy(ast), node_id).mutate()
    except Exception as error:  # a schema may be inapplicable at this node
        records.append(
            MutantRecord(
                instance_id=instance_id,
                operator=operator,
                schema=schema,
                source_file=source_relative,
                node_id=node_id,
                line=line,
                mutant_path="",
                files=[],
                status="failed",
                note=str(error),
            )
        )
        return False

    if mutated_ast is None:
        records.append(
            MutantRecord(
                instance_id=instance_id,
                operator=operator,
                schema=schema,
                source_file=source_relative,
                node_id=node_id,
                line=line,
                mutant_path="",
                files=[],
                status="failed",
                note="operator returned no AST",
            )
        )
        return False

    candidate_dir = out_dir / instance_id
    candidate_dir.mkdir(parents=True, exist_ok=True)
    mutant_name = f"{instance_id}{source.suffix}"
    origin_name = f"{instance_id}_origin{source.suffix}"
    (candidate_dir / mutant_name).write_text(
        ASTCodeGenerator().visit(mutated_ast), encoding="utf-8"
    )
    (candidate_dir / origin_name).write_text(
        ASTCodeGenerator().visit(ast), encoding="utf-8"
    )

    mutant_relative = project.relative(candidate_dir / mutant_name)
    files = [mutant_relative]
    for companion in project.companion_sources(source):
        target = candidate_dir / relatives[companion]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(companion, target)
        files.append(project.relative(target))

    records.append(
        MutantRecord(
            instance_id=instance_id,
            operator=operator,
            schema=schema,
            source_file=source_relative,
            node_id=node_id,
            line=line,
            mutant_path=mutant_relative,
            files=files,
        )
    )
    return True


def write_manifest(records: list[MutantRecord], path: Path) -> Path:
    """Persist the mutant metadata table used by ``mantra2 evaluate``."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for record in records:
            writer.writerow(record.as_row())
    return path


def read_manifest(path: Path) -> list[dict[str, str]]:
    """Read back a mutant metadata table."""
    with Path(path).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        row["files"] = [item for item in row.get("files", "").split(";") if item]
    return [row for row in rows if row.get("status") == "generated"]
