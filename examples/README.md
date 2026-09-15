# Example project

`counter.v` is a 4-bit counter, `counter_tb.v` its testbench. The testbench
writes `output.txt` (a `time,value` CSV) and dumps a value every 10ns for four
cycles, which is exactly what `mantra2 evaluate` compares against.

## Mutate

```bash
mantra2 mutate --source examples/counter.v --root examples --out examples/mantra
```

## Evaluate

```bash
mantra2 evaluate \
  --source examples/counter.v \
  --root examples \
  --testbench examples/counter_tb.v \
  --manifest examples/mantra/mutants.csv \
  --backend iverilog \
  --work-dir work
```

## What to expect

`counter.v` is deliberately tiny, so it exercises only part of the operator
set:

- fires: `ExprUpdate` / `ExprInsert` / `ExprDelete` (the `value + 4'd1` adder),
  `NSubUpdate` / `NSubDelete` / `NSubInsert` / `AssignN2B` (the always block),
  `EdgeFlip` / `EdgeInsert` / `EdgeDelete` (the sensitivity list),
  `IOFlip1` / `IOFlip2` (the ports)
- stays silent: the `Pointer*` and `Partselect*` families, because the design
  has no bit-selects or part-selects

Mutants that change the counter's value are reported as `observable`; those
that leave it untouched (for example an equivalent expression rewrite) come out
as `equivalent`.
