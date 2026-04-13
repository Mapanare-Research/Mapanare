# v4.56.0 Measurements — Arc 5 Panel

| Metric | Value |
|---|---|
| VERSION | 4.55.0 |
| main.ll lines | 191,027 |
| semantic.mn lines | 2,070 |
| Golden tests | 55 (48 pass stage1, 7 fail: 6 tensor/parse + 1 const scope) |
| Self-hosted regression tests | 20 (11 wiring + 8 cascade + 1 deletion gate) |
| Const tests | 13 (6 parser + 7 semantic) |
| Pytest pass (semantic+parser+llvm+self_hosted) | 1,111 |
| Carry-forward A-items closed this arc | 3 (A7, A8, A9) |
| Carry-forward A-items still open | 0 (A1-A5 deferred v5.x) |
| v4.26.0 const CRITICAL | CLOSED Path A |
| New lines of .mn (semantic.mn) | +96 |
| New lines of main.ll | +1,286 |
