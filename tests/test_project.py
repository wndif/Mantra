"""Tests for project-layout resolution from command-line arguments."""

from pathlib import Path

import pytest

from mantra2.project import build_layout


def _write(path: Path, content: str = "module m; endmodule\n") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_root_defaults_to_common_parent(tmp_path: Path):
    top = _write(tmp_path / "rtl" / "top.v")
    other = _write(tmp_path / "rtl" / "other.v")
    layout = build_layout([top, other], root=None, testbench=None, output_filename="o.txt")
    assert layout.root == tmp_path / "rtl"
    assert set(layout.sources) == {top, other}


def test_explicit_root_is_honoured(tmp_path: Path):
    top = _write(tmp_path / "rtl" / "top.v")
    layout = build_layout(
        [top], root=tmp_path, testbench=None, output_filename="o.txt"
    )
    assert layout.root == tmp_path
    assert layout.relative(top) == "rtl/top.v"


def test_source_outside_root_is_rejected(tmp_path: Path):
    top = _write(tmp_path / "rtl" / "top.v")
    outside = _write(tmp_path / "elsewhere" / "far.v")
    with pytest.raises(ValueError, match="escapes the project root"):
        build_layout(
            [top, outside],
            root=tmp_path / "rtl",
            testbench=None,
            output_filename="o.txt",
        )


def test_missing_source_is_reported(tmp_path: Path):
    with pytest.raises(FileNotFoundError, match="missing source files"):
        build_layout(
            [tmp_path / "nope.v"], root=None, testbench=None, output_filename="o.txt"
        )


def test_missing_testbench_is_reported(tmp_path: Path):
    top = _write(tmp_path / "top.v")
    with pytest.raises(FileNotFoundError, match="missing testbench"):
        build_layout(
            [top],
            root=tmp_path,
            testbench=tmp_path / "tb.v",
            output_filename="o.txt",
        )


def test_simulation_sources_append_the_testbench(tmp_path: Path):
    top = _write(tmp_path / "top.v")
    bench = _write(tmp_path / "tb.v")
    layout = build_layout(
        [top], root=tmp_path, testbench=bench, output_filename="output.txt"
    )
    assert layout.simulation_sources([top]) == [top, bench]
    assert layout.output_filename == "output.txt"


def test_no_sources_is_rejected():
    with pytest.raises(ValueError, match="at least one --source"):
        build_layout([], root=None, testbench=None, output_filename="o.txt")
