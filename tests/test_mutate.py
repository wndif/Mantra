"""End-to-end tests for mutant generation."""

import shutil
from pathlib import Path

import pytest

from mantra2.mutate import generate_mutants, read_manifest, write_manifest
from mantra2.project import build_layout

pytest.importorskip("pyverilog", reason="PyVerilog is required for mutation")

if shutil.which("iverilog") is None:
    pytest.skip(
        "Icarus Verilog is required: PyVerilog preprocesses sources with "
        "'iverilog -E', so even mutation needs it",
        allow_module_level=True,
    )

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"
COUNTER = EXAMPLES / "counter.v"

SCHEMAS = ["NSubUpdate", "NSubDelete", "ExprUpdate", "EdgeFlip", "IOFlip1"]


def _layout() -> "object":
    return build_layout(
        [COUNTER], root=COUNTER.parent, testbench=None, output_filename="output.txt"
    )


def test_counter_example_is_present():
    assert COUNTER.is_file(), "the bundled counter example is missing"


def test_generate_mutants_writes_each_instance_directory(tmp_path: Path):
    layout = _layout()
    out_dir = tmp_path / "mantra"
    records = generate_mutants(
        layout,
        out_dir=out_dir,
        operators=SCHEMAS,
        per_operator=2,
        seed=0,
    )
    generated = [record for record in records if record.status == "generated"]
    assert generated, "no mutant was generated for the counter example"

    for record in generated:
        mutant = layout.root / record.mutant_path
        assert mutant.is_file(), record.instance_id
        assert mutant.read_text(encoding="utf-8").strip()

        origin = mutant.with_name(f"{mutant.stem}_origin{mutant.suffix}")
        assert origin.is_file(), f"{record.instance_id} has no canonical original"

        assert record.line >= 1
        assert record.node_id >= 0
        assert record.mutant_path in record.files


def test_generate_mutants_is_deterministic_for_a_seed(tmp_path: Path):
    layout = _layout()
    first = generate_mutants(
        layout,
        out_dir=tmp_path / "a",
        operators=SCHEMAS,
        per_operator=2,
        seed=7,
    )
    second = generate_mutants(
        layout,
        out_dir=tmp_path / "b",
        operators=SCHEMAS,
        per_operator=2,
        seed=7,
    )
    assert [item.instance_id for item in first] == [
        item.instance_id for item in second
    ]


def test_per_operator_limits_the_number_of_mutants(tmp_path: Path):
    layout = _layout()
    few = generate_mutants(
        layout, out_dir=tmp_path / "few", operators=["NSubUpdate"], per_operator=1
    )
    many = generate_mutants(
        layout, out_dir=tmp_path / "many", operators=["NSubUpdate"], per_operator=3
    )
    assert len(few) <= len(many)


def test_manifest_round_trip(tmp_path: Path):
    layout = _layout()
    records = generate_mutants(
        layout, out_dir=tmp_path / "mantra", operators=SCHEMAS, per_operator=1
    )
    path = write_manifest(records, tmp_path / "mantra" / "mutants.csv")
    rows = read_manifest(path)
    generated = [item for item in records if item.status == "generated"]
    assert len(rows) == len(generated)
    assert rows[0]["files"], "the manifest must list the files to compile"


def test_unknown_schema_is_rejected(tmp_path: Path):
    with pytest.raises(ValueError, match="unknown mutation schemas"):
        generate_mutants(
            _layout(), out_dir=tmp_path / "mantra", operators=["Nope"], per_operator=1
        )
