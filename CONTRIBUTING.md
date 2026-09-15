# Contributing to Mantra2

Thanks for helping out.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[mutation,test]"
mantra2 setup-pyverilog --yes
pytest
```

Both `pytest` and any manual run depend on the PyVerilog patch, because the
operators were written against that code-generation behaviour.

## Ground rules

- **Mutation behaviour is the contract.** Instance identifiers
  (`<stem>_<schema>_<nodeid>_<line>`) and the output layout are stable API: a
  mutant must keep the same name across runs and machines. If you change either,
  say so loudly in the PR.
- **Do not reintroduce the population-based operators.** The inherited
  delete/insert/replace operators and the fault-localisation bookkeeping were
  deliberately removed: nothing on the generation path reaches them, and the
  schemas only ever call `replace_with_node`.
- **Keep the dependency surface small.** PyYAML is the only hard dependency;
  PyVerilog stays behind the `mutation` extra so that the metadata tooling can
  be used without it.

## Adding an operator

1. Add `YourOperator.py` under `src/mantra2/mutation/implementations/`,
   subclassing `MantraOperator` and implementing `mutate()`.
2. Export it from that package's `__init__.py`.
3. Add a schema entry to `src/mantra2/configs/mutation_patterns.yaml` with the
   parent/child class-name pattern that identifies legal mutation points.
4. Register the operator family in `src/mantra2/configs/operators.yaml`.
5. Add a test that runs the schema against `examples/counter.v` or a fixture
   that exercises the relevant AST shape.

## Style

- Python 3.10+, type hints on public functions.
- No formatter is enforced; match the surrounding code.

## Provenance

The bundled PyVerilog patch is distributed under the Apache License 2.0. Update
`THIRD_PARTY_NOTICES.md` when you vendor new third-party code.
