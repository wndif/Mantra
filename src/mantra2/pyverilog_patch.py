"""Application of the bundled PyVerilog compatibility files.

Mantra2 rewrites PyVerilog's AST and relies on code generation behaviour that
stock PyVerilog 1.2.1 does not provide.  The four bundled files replace their
counterparts inside the installed ``pyverilog`` package.

Because this overwrites files in the active environment, run it inside a
virtual environment.  It is a no-op to run twice.
"""

from __future__ import annotations

import shutil
from pathlib import Path

PATCH_DIR = Path(__file__).resolve().parent / "vendor" / "pyverilog_patch"

TARGETS = {
    "codegen.py": ("ast_code_generator", "codegen.py"),
    "ast.py": ("vparser", "ast.py"),
    "parser.py": ("vparser", "parser.py"),
    "ast_classes.txt": ("vparser", "ast_classes.txt"),
}


def patch_dir() -> Path:
    """Directory holding the bundled replacement files."""
    if not PATCH_DIR.is_dir():
        raise FileNotFoundError(f"bundled PyVerilog patch not found at {PATCH_DIR}")
    return PATCH_DIR


def installed_pyverilog_root() -> Path:
    """Root of the ``pyverilog`` package in the active environment."""
    try:
        import pyverilog
    except ImportError as error:
        raise RuntimeError("Install pyverilog==1.2.1 before applying the patch") from error
    return Path(pyverilog.__file__).resolve().parent


def check_patch_state() -> list[tuple[str, Path, bool]]:
    """Report, per file, whether the installed copy already matches ours."""
    root = installed_pyverilog_root()
    source = patch_dir()
    state = []
    for name, parts in TARGETS.items():
        destination = root.joinpath(*parts)
        identical = destination.is_file() and destination.read_bytes() == (
            source / name
        ).read_bytes()
        state.append((name, destination, identical))
    return state


def apply_patch(*, confirm: bool = False) -> list[Path]:
    """Copy the bundled files over the installed PyVerilog files."""
    if not confirm:
        raise SystemExit(
            "Refusing to modify the active environment without confirmation.\n"
            "Re-run with --yes, preferably inside a dedicated virtual environment."
        )
    root = installed_pyverilog_root()
    source = patch_dir()
    written = []
    for name, parts in TARGETS.items():
        destination = root.joinpath(*parts)
        if not destination.parent.is_dir():
            raise FileNotFoundError(
                f"unexpected PyVerilog layout, missing {destination.parent}"
            )
        shutil.copy2(source / name, destination)
        written.append(destination)
    return written
