"""Simulation backends used to classify mutants.

Icarus Verilog is the default backend: it is open source and available
everywhere.  Synopsys VCS is kept as an opt-in backend for users who need the
exact reference toolchain used by Mantra.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


def run_iverilog(
    sources: list[Path],
    *,
    output: Path,
    top: str | None = None,
    timeout: int = 120,
    cwd: Path | None = None,
    include_dirs: list[Path] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Compile and run Verilog sources with Icarus Verilog."""
    compiler = shutil.which("iverilog")
    runtime = shutil.which("vvp")
    if not compiler or not runtime:
        raise RuntimeError("Icarus Verilog (iverilog and vvp) is required")
    output.parent.mkdir(parents=True, exist_ok=True)
    compile_command = [compiler, "-g2012", "-o", str(output)]
    for include_dir in include_dirs or []:
        compile_command.extend(["-I", str(include_dir)])
    if top:
        compile_command.extend(["-s", top])
    compile_command.extend(str(source) for source in sources)
    subprocess.run(compile_command, check=True, text=True, timeout=timeout, cwd=cwd)
    return subprocess.run(
        [runtime, str(output)],
        check=True,
        text=True,
        capture_output=True,
        timeout=timeout,
        cwd=cwd,
    )


def vcs_command(
    sources: list[Path],
    *,
    coverage: bool = True,
    include_dirs: list[Path] | None = None,
    verdi_pli_dir: Path | None = None,
) -> list[str]:
    """Return the Mantra-compatible VCS compile command."""
    command = ["vcs"]
    for include_dir in include_dirs or []:
        command.append(f"+incdir+{include_dir}")
    command.extend(str(source) for source in sources)
    command.extend(
        [
            "-timescale=1ns/100ps",
            "-fsdb",
            "-full64",
            "+vc",
            "+v2k",
            "-LDFLAGS",
            "-Wl,--no-as-needed",
            "-sverilog",
        ]
    )
    if verdi_pli_dir is not None:
        command.extend(
            [
                "-P",
                str(verdi_pli_dir / "novas.tab"),
                str(verdi_pli_dir / "pli.a"),
            ]
        )
    if coverage:
        command.extend(["-cm", "line+cond+fsm+branch+tgl"])
    return command


def resolve_verdi_pli_dir() -> Path:
    """Locate the Verdi PLI directory required by the reference workflow."""
    candidates: list[Path] = []
    for variable in ("MANTRA2_VERDI_PLI", "VERIBUGBENCH_VERDI_PLI"):
        explicit = os.environ.get(variable)
        if explicit:
            candidates.append(Path(explicit))
    verdi_home = os.environ.get("VERDI_HOME")
    if verdi_home:
        candidates.append(Path(verdi_home) / "share" / "PLI" / "VCS" / "LINUX64")
    candidates.extend(
        Path(entry)
        for entry in os.environ.get("LD_LIBRARY_PATH", "").split(os.pathsep)
        if entry
    )
    for candidate in candidates:
        if (candidate / "novas.tab").is_file() and (candidate / "pli.a").is_file():
            return candidate
    raise RuntimeError(
        "The VCS backend requires Verdi PLI files novas.tab and pli.a. "
        "Set MANTRA2_VERDI_PLI, VERDI_HOME, or LD_LIBRARY_PATH."
    )


def run_vcs(
    sources: list[Path],
    *,
    cwd: Path,
    timeout: int = 300,
    coverage: bool = False,
    include_dirs: list[Path] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Compile and execute sources with Synopsys VCS."""
    compiler = shutil.which("vcs")
    if not compiler:
        raise RuntimeError("Synopsys VCS is required for the VCS backend")
    verdi_pli_dir = resolve_verdi_pli_dir()
    cwd.mkdir(parents=True, exist_ok=True)
    command = vcs_command(
        sources,
        coverage=coverage,
        include_dirs=include_dirs,
        verdi_pli_dir=verdi_pli_dir,
    )
    command[0] = compiler
    if coverage:
        command.extend(["-cm_dir", str(cwd / "cov_test.vdb")])
    subprocess.run(command, cwd=cwd, check=True, text=True, timeout=timeout)
    simv = cwd / ("simv.exe" if (cwd / "simv.exe").exists() else "simv")
    return subprocess.run(
        [str(simv)],
        cwd=cwd,
        check=True,
        text=True,
        capture_output=True,
        timeout=timeout,
    )
