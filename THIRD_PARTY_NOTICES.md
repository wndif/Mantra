# Third-party notices

The repository-level MIT license applies to the Mantra software in this
repository. It does not replace the licenses of third-party software bundled or
referenced here.

## PyVerilog

The files in `src/mantra2/vendor/pyverilog_patch/` are modifications of
PyVerilog 1.2.1 (`codegen.py`, `ast.py`, `parser.py`, `ast_classes.txt`). Their
source headers identify the original copyright holders. PyVerilog is
distributed under the Apache License 2.0. Consult the upstream PyVerilog
distribution for its complete license and notice files.

The patch is applied on request by:

    mantra2 setup-pyverilog --yes

It overwrites files inside the active Python environment, so run it inside a
dedicated virtual environment.

## Simulators

Mantra2 shells out to Icarus Verilog (`iverilog`, `vvp`) or Synopsys VCS.
Neither is bundled: they are separate products with their own license terms.
The VCS backend additionally requires Verdi PLI files (`novas.tab`, `pli.a`).

## RTL designs

Any Verilog design you mutate with Mantra2 remains subject to its own upstream
license. Mantra2 does not relicense your sources or the mutants derived from
them.
