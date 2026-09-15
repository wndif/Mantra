"""Layout of the single Verilog project being mutated.

Mantra2 operates on one project at a time, so the project is described by
command-line arguments instead of a checked-in manifest file.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectLayout:
    """A project root plus the RTL files that take part in mutation."""

    root: Path
    sources: tuple[Path, ...]
    testbench: Path | None
    output_filename: str

    def relative(self, path: Path) -> str:
        """Return ``path`` relative to the project root, when possible."""
        try:
            return path.resolve().relative_to(self.root.resolve()).as_posix()
        except ValueError:
            return path.resolve().as_posix()

    def companion_sources(self, source: Path) -> list[Path]:
        """The RTL files that must be shipped next to a mutant of ``source``."""
        return [item for item in self.sources if item != source]

    def simulation_sources(self, rtl: list[Path]) -> list[Path]:
        """RTL files plus the testbench, in compilation order."""
        files = list(rtl)
        if self.testbench is not None and self.testbench not in files:
            files.append(self.testbench)
        return files


def build_layout(
    sources: list[Path],
    *,
    root: Path | None,
    testbench: Path | None,
    output_filename: str,
) -> ProjectLayout:
    """Resolve CLI arguments into a validated :class:`ProjectLayout`."""
    if not sources:
        raise ValueError("at least one --source is required")

    resolved = [Path(source).resolve() for source in sources]
    missing = [str(path) for path in resolved if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing source files:\n  " + "\n  ".join(missing))

    if root is None:
        parents = [path.parent for path in resolved]
        root = parents[0]
        for parent in parents[1:]:
            while root != parent and root not in parent.parents:
                root = root.parent
        if testbench is not None:
            testbench_parent = Path(testbench).resolve().parent
            while root != testbench_parent and root not in testbench_parent.parents:
                root = root.parent
    else:
        root = Path(root).resolve()

    for path in resolved:
        try:
            path.relative_to(root)
        except ValueError as error:
            raise ValueError(
                f"source file {path} escapes the project root {root}; "
                "pass --root explicitly"
            ) from error

    resolved_testbench = None
    if testbench is not None:
        resolved_testbench = Path(testbench).resolve()
        if not resolved_testbench.is_file():
            raise FileNotFoundError(f"missing testbench: {resolved_testbench}")

    return ProjectLayout(
        root=root,
        sources=tuple(resolved),
        testbench=resolved_testbench,
        output_filename=output_filename,
    )
