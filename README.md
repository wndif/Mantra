# Mantra2

Mutation testing for a single Verilog project. Its 19 mutation operators are
extracted from the real distribution of Verilog bugs: a large-scale empirical
study of 300+ open-source projects in which bug-fix commits were AST-diffed into
update / insert / delete / move patterns, reported in X. Meng et al., "Rtl
design flaws revisited: a data-driven study of systematic bug patterns in Verilog
code," The Journal of Supercomputing, vol. 81, no. 14, p. 1321, 2025,
doi: 10.1007/s11227-025-07811-9.

Mantra2 is an improvement on Mantra, the original prototype it is based on: J.
Wu et al., "Mantra: Mutation Testing of Hardware Design Code Based on Real Bugs,"
2023 60th ACM/IEEE Design Automation Conference (DAC), San Francisco, CA, USA,
2023, pp. 1-6, doi: 10.1109/DAC56929.2023.10247962.

Point it at one RTL file (or a handful of files from one project) and it will
inject realistic, bug-shaped faults into the Verilog AST, then optionally
simulate each mutant against your testbench to separate the ones that actually
change behaviour from the equivalent ones.

```bash
mantra2 mutate --source rtl/counter.v --root rtl --out mutants
```

## What it does

1. **Parse** the RTL with PyVerilog 1.2.1.
2. **Find mutation points** by matching parent/child AST class-name sequences
   declared in `src/mantra2/configs/mutation_patterns.yaml` (for example
   `Always → NonblockingSubstitution`).
3. **Rewrite** the AST with one operator and regenerate Verilog source.
4. **Record** every mutant in `mutants.csv` (operator, node id, source line,
   files to compile).
5. **Optionally simulate** each mutant with Icarus Verilog or Synopsys VCS and
   label it `observable`, `equivalent`, or `error`.

Steps 1–4 produce mutants. Step 5 additionally needs a testbench.

> **Icarus Verilog is required even for steps 1–4.** PyVerilog shells out to
> `iverilog -E` as its preprocessor, so parsing fails without it. Install
> Icarus Verilog first, whether or not you plan to simulate.

## Install

The recommended way to run Mantra2 is **inside Docker** — the image bundles
Python, the patched PyVerilog 1.2.1, and Icarus Verilog, so there is nothing to
install on your machine and no patch step to forget.

### Docker (recommended)

```bash
# Build the image once
docker build -t mantra2:local .

# Mount your project dir at /data and run any sub-command.
# "examples" is included in the repo, so you can try it without your own RTL:
docker run --rm -v "$PWD/examples:/data" mantra2:local \
    mutate --source counter.v --root /data --out /data/mantra

docker run --rm -v "$PWD/examples:/data" mantra2:local \
    evaluate --source counter.v --root /data \
    --testbench counter_tb.v --manifest /data/mantra/mutants.csv \
    --backend iverilog --work-dir /data/work
```

Mutants and CSVs are written back into the mounted directory, so they land on
your host instead of inside the container. The same image works on Linux,
macOS, and Windows (Docker Desktop). Synopsys VCS cannot be bundled — mount your
own licence and toolchain (`--backend vcs`) if you need it.

### Local install (virtual environment)

If you prefer to run on the host, use a virtual environment. Mantra2 patches
PyVerilog, so keep the patch step inside that environment.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[mutation,test]"

mantra2 setup-pyverilog --yes      # one-off, per environment
```

`setup-pyverilog` replaces four files inside the installed `pyverilog` package
(`codegen.py`, `ast.py`, `parser.py`, `ast_classes.txt`). Without it, code
generation does not match the behaviour the operators were written against.

### Simulators

**Icarus Verilog** (`iverilog` + `vvp`) is a hard requirement: PyVerilog uses
`iverilog -E` to preprocess sources, so even `mantra2 mutate` fails without it.

```bash
# Debian/Ubuntu
sudo apt-get install iverilog
# macOS
brew install icarus-verilog
# Windows
choco install iverilog
```

**Synopsys VCS** is opt-in via `--backend vcs` and additionally needs Verdi PLI
files (`novas.tab`, `pli.a`), located through `MANTRA2_VERDI_PLI` or
`VERDI_HOME`.

### Testbench format

`evaluate` classifies a mutant by comparing its simulation dump with the golden
run's dump. The testbench must therefore **write sampled signals to a CSV file**
(default name `output.txt`, override with `--output`) that has a `time` column
plus one column per signal you want compared:

```verilog
output_file = $fopen("output.txt", "w");
$fwrite(output_file, "time,value\n");
repeat (8) begin
    #10;
    $fwrite(output_file, "%0t,%0d\n", $time, value);
end
$finish;
```

Two rules:

- **Do not abort on a mismatch.** A self-checking bench that calls `$fatal`
  when the output is wrong makes Icarus Verilog exit non-zero, which Mantra2
  records as `error` instead of comparing the dump. Let the bench finish
  cleanly so the comparison can run.
- **The golden run must pass.** `evaluate` first simulates the original RTL;
  if that fails to compile or run, every mutant is reported as `error`.

### Status meanings

`observable` — the mutant's dump differs from the golden dump (the fault is
detected). `equivalent` — the dump is identical (the fault is invisible to this
testbench). `error` — the mutant did not compile or run.

## Quick start

The repository ships a runnable example. The commands below assume a local
install (see [Install](#install)); for the Docker equivalents, prefix each with
`docker run --rm -v "$PWD/examples:/data" mantra2:local ` and use `/data` as the
paths.

```bash
# 1. Mutate (needs iverilog for preprocessing, but no testbench)
mantra2 mutate --source examples/counter.v --root examples --out examples/mantra

# 2. Keep only the mutants that change behaviour
mantra2 evaluate \
  --source examples/counter.v \
  --root examples \
  --testbench examples/counter_tb.v \
  --manifest examples/mantra/mutants.csv \
  --backend iverilog \
  --work-dir work
```

Step 2 writes `work/candidate_results.csv` with one row per mutant:

```csv
instance_id,operator,schema,source_file,node_id,line,status,failing_rows,error
counter_ExprUpdate_37_10,ExprUpdate,ExprUpdate,counter.v,37,10,observable,4,
```

`status` is `observable` when the mutant's output diverges from the golden
reference, `equivalent` when it does not, and `error` when compilation or
simulation failed.

## Output layout

Instance identifiers are stable and follow the
`<stem>_<operator>_<nodeid>_<line>` convention, so a mutant keeps the same name
across runs and across machines:

```
mantra/
├── mutants.csv
├── counter_ExprUpdate_37_10/
│   ├── counter_ExprUpdate_37_10.v          # the mutant
│   └── counter_ExprUpdate_37_10_origin.v   # canonical original, for diffing
└── counter_NSubUpdate_24_7/
    ├── counter_NSubUpdate_24_7.v
    └── counter_NSubUpdate_24_7_origin.v
```

The `_origin.v` file is the original source round-tripped through PyVerilog.
Diff it against the mutant to see exactly what the operator changed, without
code-generation noise getting in the way.

## Operators

19 operators, realised by 22 executable schemas. Each operator is a
`(node type, repair action)` pair taken from the real bug distribution:
`ExprUpdate` is "an expression bug whose fix updates the node", `NSubDelete` is
"a non-blocking-assignment bug whose fix deletes it", and so on. Everything is
declared in `src/mantra2/configs/mutation_patterns.yaml` and `src/mantra2/configs/operators.yaml`.

| Family | Operators |
| --- | --- |
| Expression | `ExprUpdate`, `ExprInsert`, `ExprDelete` |
| Bit-vector and access | `PartselectUpdate`, `PartselectInsert`, `PartselectDelete`, `PointerUpdate`, `PointerInsert`, `PointerDelete` |
| Assignment | `NSubUpdate`, `NSubInsert`, `NSubDelete`, `NSubMove`, `AssignN2B`, `AssignB2N` |
| Timing | `EdgeFlip`, `EdgeInsert`, `EdgeDelete` |
| Port | `IOFlip` |

`NSubInsert` and `IOFlip` each have more than one schema (`NSubInsert`,
`NSubInsert_IF`, `NSubInsert_Case`; `IOFlip1`, `IOFlip2`).

```bash
mantra2 list-operators          # schemas, families, and operator classes
```

Not every operator fires on every design: `PointerUpdate` needs a bit-select,
`PartselectDelete` needs a part-select, and so on. When a schema finds no
matching node it simply produces nothing.

### Adding your own operator

You do not have to modify the package. Subclass `MantraOperator`, implement
`mutate()`, and point a schema at it:

```python
# my_operators.py
import pyverilog.vparser.ast as vast

from mantra2.mutation import MantraOperator


class ForceZero(MantraOperator):
    def mutate(self):
        self.replace_with_node(self.ast, self.old_nodeid, vast.IntConst("0"))
        return self.ast
```

```yaml
# my_patterns.yaml
patterns:
  ForceZero:
    OPClass: ForceZero
    module: my_operators            # importable dotted path
    pattern:
      - class_name: NonblockingSubstitution
```

```bash
mantra2 mutate --source rtl/top.v --patterns my_patterns.yaml
```

If you omit `module`, the class is looked up in
`mantra2.mutation.implementations`.

## CLI

### `mantra2 mutate`

| Option | Meaning |
| --- | --- |
| `--source FILE` | RTL file to mutate; repeat for multi-file projects (required) |
| `--root DIR` | project root for relative paths (default: common parent of sources) |
| `--out DIR` | output directory (default: `mantra`) |
| `--operator SCHEMA` | restrict to one or more schemas (default: all) |
| `--per-operator N` | mutation points per schema per file (default: `1`) |
| `--all-locations` | mutate every matching location instead of sampling |
| `--seed N` | random seed (default: `0`) |
| `--patterns FILE` | custom mutation-patterns YAML |
| `--manifest FILE` | where to write the metadata CSV (default: `<out>/mutants.csv`) |

### `mantra2 evaluate`

| Option | Meaning |
| --- | --- |
| `--source FILE` | original RTL files (required) |
| `--testbench FILE` | testbench used to compile and run (required) |
| `--root DIR` | project root |
| `--manifest FILE` | metadata CSV written by `mutate` |
| `--backend` | `iverilog` (default) or `vcs` |
| `--work-dir DIR` | simulation scratch directory (default: `work`) |
| `--top MODULE` | top module for Icarus Verilog |
| `--timeout N` | per-simulation timeout in seconds (default: `300`) |
| `--limit N` | evaluate only the first N mutants |

### `mantra2 setup-pyverilog`

Applies the bundled PyVerilog patch. Run it without `--yes` to see the current
state of each file.

## Relationship to Mantra 1.0

This repository used to hold the original Mantra prototype. Mantra2 keeps that
implementation but replaces its operator set, and the prototype itself is
preserved on the [Mantra1.0](../../releases/tag/Mantra1.0) tag. Two things are
worth keeping apart from that earlier version.

**The operator sets are different.** Mantra 1.0's 19 operators are organised by
semantic category:

| Category | Mantra operators |
| --- | --- |
| Data Mis-Access | `DMO`, `DMS`, `DMI`, `DIE` |
| Communication | `CMA`, `CGA`, `CRV`, `CMP`, `CDP` |
| Timing | `TAA`, `TMD`, `TRA` |
| Semantic | `SRC`, `SRI`, `SRE`, `SME`, `SRA`, `SRR`, `SRW` |

Mantra2 replaces them with operators extracted from the real distribution of
Verilog bugs, organised as `(node type, repair action)` pairs — see
[Operators](#operators). The two sets share no operator names.

**What Mantra2 adds.** The original Mantra prototype is a research demonstrator
that applies one operator to one file and prints the regenerated source. Mantra2
builds on the same implementation to turn the operators into an engine that can
be pointed at a real project:

- **CLI-driven input.** Mutate any RTL file by passing `--source`; there is no
  project manifest to author and nothing to register.
- **One project at a time.** Multi-file projects work by repeating `--source`,
  but there is deliberately no cross-project orchestration.
- **Open-source simulation backend.** `evaluate` defaults to Icarus Verilog, so
  mutant classification works without a commercial simulator. Synopsys VCS
  remains available through `--backend vcs`.
- **Configurable operator set.** Schemas are declared in YAML and may point at
  any importable class, so operators can be added without forking the package.
- **Metadata manifest.** Every mutant is recorded in `mutants.csv` with its
  operator, node id, source line, and file list, for downstream analysis.
- **Operator fixes.** `SensList.list` was corrected to `SensList.slist` in
  `EdgeInsert` and `EdgeDelete`, which previously raised `AttributeError` on
  every run; and Icarus Verilog is invoked with POSIX-style paths, so mutation
  also works on Windows.

Mantra2 is the current state of this repository; the prototype it replaced is
kept on the [Mantra1.0](../../releases/tag/Mantra1.0) tag.

## Development

```bash
pip install -e ".[mutation,test]"
mantra2 setup-pyverilog --yes
pytest
```

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Citation

If you use Mantra2 in academic work, please cite the paper the tool derives
from:

```bibtex
@inproceedings{wu2023mantra,
  author    = {Jiang Wu and Yan Lei and Zhuo Zhang and Xiankai Meng and
               Deheng Yang and Pan Li and Jiayu He and Xiaoguang Mao},
  title     = {Mantra: Mutation Testing of Hardware Design Code Based on Real Bugs},
  booktitle = {60th ACM/IEEE Design Automation Conference (DAC 2023)},
  address   = {San Francisco, CA, USA},
  pages     = {1--6},
  publisher = {IEEE},
  year      = {2023},
  doi       = {10.1109/DAC56929.2023.10247962}
}
```

J. Wu et al., "Mantra: Mutation Testing of Hardware Design Code Based on Real
Bugs," 2023 60th ACM/IEEE Design Automation Conference (DAC), San Francisco, CA,
USA, 2023, pp. 1-6, doi: 10.1109/DAC56929.2023.10247962.

## License

MIT — see [LICENSE](LICENSE). The bundled PyVerilog patch is derived from
PyVerilog 1.2.1 (Apache-2.0); third-party components are listed in
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
