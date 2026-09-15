"""Compare reference and mutant simulation outputs.
"""

from __future__ import annotations

import csv
from pathlib import Path


def compare_csv_outputs(
    golden: Path,
    observed: Path,
    *,
    output: Path | None = None,
    index_column: str = "time",
) -> list[dict[str, str]]:
    """Return a per-row discrepancy vector using Mantra's common-prefix rule."""
    with golden.open(newline="", encoding="utf-8") as handle:
        golden_rows = list(csv.DictReader(handle))
    with observed.open(newline="", encoding="utf-8") as handle:
        observed_rows = list(csv.DictReader(handle))
    if not golden_rows or not observed_rows:
        raise ValueError("simulation output is empty")
    if index_column not in golden_rows[0] or index_column not in observed_rows[0]:
        raise ValueError(f"both outputs must contain an {index_column!r} column")

    common_columns = [
        column
        for column in golden_rows[0]
        if column != index_column and column in observed_rows[0]
    ]
    if not common_columns:
        raise ValueError("simulation outputs have no comparable value columns")

    result: list[dict[str, str]] = []
    for golden_row, observed_row in zip(golden_rows, observed_rows):
        error = golden_row[index_column] != observed_row[index_column] or any(
            golden_row[column] != observed_row[column] for column in common_columns
        )
        result.append(
            {index_column: golden_row[index_column], "error": str(int(error))}
        )

    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=[index_column, "error"])
            writer.writeheader()
            writer.writerows(result)
    return result
