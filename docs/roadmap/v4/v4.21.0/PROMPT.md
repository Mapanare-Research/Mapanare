# v4.21.0 — Quality Gate + CI/CD — Continuation Prompt

> Fix regressions. Add CI. Make everything honest.
> You are in WSL. Run full validation after every change.

---

## Context

v4.14.0-v4.20.0 shipped 7 versions. v4.14.0-v4.17.0 were solid (real bug
fixes, real features, verified). v4.18.0-v4.20.0 were surface-level (syntax
keywords only, no runtime wiring). This version makes the CI catch any
future regressions and ensures all existing tests still pass.

## Commands

```bash
python3 -m pytest tests/ -q --tb=short
python3 -m mapanare emit-wasm examples/wasm/hello.mn -o /dev/null
gcc -c -fsyntax-only -Wall -Wextra -Werror runtime/native/mapanare_core.c -I runtime/native
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1
python3 scripts/ir_doctor.py stage2
bash scripts/verify_fixed_point.sh
```

## Rules

- Fix test regressions FIRST, then CI, then docs
- Do not change any .mn compiler code — only tests, CI, and docs
- Record pass counts before and after
