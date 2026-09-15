"""Simulation-based classification of generated mutants.

Every mutant is compiled and run against the project testbench and its output
is compared with the golden reference output.  A mutant whose behaviour differs
is *observable*; one that never diverges is *equivalent* and can be discarded.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from .execution import run_iverilog, run_vcs
from .mutate import read_manifest
from .project import ProjectLayout
from .results import compare_csv_outputs

RESULT_FIELDS = [
    "instance_id",
    "operator",
    "schema",
    "source_file",
    "node_id",
    "line",
    "status",
    "failing_rows",
    "error",
]


@dataclass(frozen=True)
class EvaluationRow:
    instance_id: str
    operator: str
    schema: str
    source_file: str
    node_id: str
    line: str
    status: str
    failing_rows: str
    error: str = ""

    def as_row(self) -> dict[str, str]:
        return {
            "instance_id": self.instance_id,
            "operator": self.operator,
            "schema": self.schema,
            "source_file": self.source_file,
            "node_id": self.node_id,
            "line": self.line,
            "status": self.status,
            "failing_rows": self.failing_rows,
            "error": self.error,
        }


def run_simulation(
    project: ProjectLayout,
    rtl: list[Path],
    *,
    work_dir: Path,
    backend: str,
    top: str | None = None,
    timeout: int = 300,
) -> Path:
    """Compile and run ``rtl`` plus the testbench; return the output file."""
    if project.testbench is None:
        raise ValueError("--testbench is required to simulate a project")
    sources = project.simulation_sources(rtl)
    missing = [str(path) for path in sources if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing simulation sources:\n  " + "\n  ".join(missing))

    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    output = work_dir / project.output_filename
    if output.is_file():
        output.unlink()

    if backend == "iverilog":
        run_iverilog(
            sources,
            output=work_dir / "simv.out",
            top=top,
            timeout=timeout,
            cwd=work_dir,
            include_dirs=[project.root],
        )
    elif backend == "vcs":
        run_vcs(
            sources,
            cwd=work_dir,
            timeout=timeout,
            include_dirs=[project.root],
        )
    else:
        raise ValueError(f"unsupported simulator backend: {backend}")

    if not output.is_file():
        raise FileNotFoundError(
            f"simulation completed but did not create {project.output_filename!r} "
            f"in {work_dir}"
        )
    return output


def evaluate_candidates(
    project: ProjectLayout,
    *,
    manifest_path: Path,
    work_root: Path,
    backend: str,
    top: str | None = None,
    timeout: int = 300,
    limit: int | None = None,
) -> Path:
    """Run every generated mutant and write ``candidate_results.csv``."""
    work_root = Path(work_root)
    work_root.mkdir(parents=True, exist_ok=True)
    records = read_manifest(manifest_path)
    if limit is not None:
        records = records[:limit]
    if not records:
        raise ValueError(
            f"{manifest_path} contains no generated mutants; run 'mantra2 mutate' first"
        )

    golden = run_simulation(
        project,
        list(project.sources),
        work_dir=work_root / "reference",
        backend=backend,
        top=top,
        timeout=timeout,
    )

    rows: list[EvaluationRow] = []
    for record in records:
        rtl = [project.root / name for name in record["files"]]
        try:
            observed = run_simulation(
                project,
                rtl,
                work_dir=work_root / record["instance_id"],
                backend=backend,
                top=top,
                timeout=timeout,
            )
            differences = compare_csv_outputs(golden, observed)
            failing = sum(row["error"] == "1" for row in differences)
            rows.append(
                EvaluationRow(
                    instance_id=record["instance_id"],
                    operator=record.get("operator", ""),
                    schema=record.get("schema", ""),
                    source_file=record.get("source_file", ""),
                    node_id=record.get("node_id", ""),
                    line=record.get("line", ""),
                    status="observable" if failing else "equivalent",
                    failing_rows=str(failing),
                )
            )
        except Exception as error:  # keep a complete evaluation ledger
            rows.append(
                EvaluationRow(
                    instance_id=record["instance_id"],
                    operator=record.get("operator", ""),
                    schema=record.get("schema", ""),
                    source_file=record.get("source_file", ""),
                    node_id=record.get("node_id", ""),
                    line=record.get("line", ""),
                    status="error",
                    failing_rows="0",
                    error=str(error),
                )
            )

    output = work_root / "candidate_results.csv"
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=RESULT_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row.as_row())
    return output
