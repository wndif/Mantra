# PyVerilog compatibility patch

These files are the PyVerilog modifications used by Mantra. They are retained
for exact artifact reproduction. Prefer applying them in an isolated virtual
environment; do not overwrite a system Python installation.

The following files replace their counterparts in PyVerilog 1.2.1:

    codegen.py -> pyverilog/ast_code_generator/codegen.py
    ast.py -> pyverilog/vparser/ast.py
    parser.py -> pyverilog/vparser/parser.py
    ast_classes.txt -> pyverilog/vparser/ast_classes.txt
