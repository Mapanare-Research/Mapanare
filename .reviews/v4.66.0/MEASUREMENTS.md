# v4.66.0 Measurements — Arc 7 Panel

## DWARF coverage

| Metric | v4.61.0 (arc start) | v4.65.0 (arc end) |
|--------|--------------------|--------------------|
| DICompileUnit per module | 0 | 1 |
| DISubprogram per function | 0 | 1 per function |
| DILocation on instructions | 0 | all source-origin |
| DILocalVariable for params | 0 | all params with arg: N |
| llvm.dbg.declare calls | 0 | after param allocas |
| DWARF tests | 0 | 34 |
| llvm-dwarfdump --verify | N/A | "No errors" |

## Line counts

| Component | v4.61.0 | v4.65.0 | Delta |
|-----------|---------|---------|-------|
| mapanare/emit_llvm_text.py | ~4,300 | ~4,450 | +~150 (DWARF methods) |
| DWARF test files | 0 | 4 files, ~400 lines | +400 |

## DWARF arc deliverables

| Release | Deliverable |
|---------|------------|
| v4.62.0 | DESIGN.md (8 sections) + infrastructure helpers + -g flag wired |
| v4.63.0 | DICompileUnit + DIFile + DISubprogram + basic types |
| v4.64.0 | DILocation on every instruction + line table |
| v4.65.0 | DILocalVariable + llvm.dbg.declare + composite type stubs |

## Carry-forward

| Item | Status |
|------|--------|
| A2 (DWARF debug info) | **CLOSED** — 6 cycles, first reported v0.7.0 |
