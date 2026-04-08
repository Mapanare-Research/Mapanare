# v0.6.0 Summary — "Compiler Infrastructure"

**Released:** March 2026
**Test count:** 2,500+
**Theme:** MIR pipeline, self-hosted semantic checker, bootstrap freeze

---

## What shipped

- **MIR core:** typed SSA-based intermediate representation (`mir.py`, `mir_builder.py`) with ~35 instruction types, basic blocks, explicit terminators, pretty-printer, verifier
- **AST → MIR lowering:** `lower.py` (1,397 lines) — all AST constructs lower to flat three-address MIR with phi nodes at control flow merges
- **MIR optimizer:** `mir_opt.py` with passes: constant folding, constant propagation, DCE, dead function elimination, agent inlining, stream fusion, unreachable block elimination, branch simplification, copy propagation; O0–O3 levels
- **MIR → Python emitter:** `emit_python_mir.py` — reconstructs structured Python from MIR basic blocks
- **MIR → LLVM emitter:** `emit_llvm_mir.py` — 1:1 MIR block → LLVM block mapping with phi nodes
- **MIR is default pipeline:** `--no-mir` flag to opt out; `emit-mir` CLI command for debugging
- **Self-hosted progress:** multi-module compilation (`build-multi`), `new Name { field: value }` struct literal syntax, complete enum lowering, string interpolation in self-hosted lexer/parser
- **Bootstrap frozen:** `bootstrap/` snapshot of Python compiler at v0.6.0 (22 files), `bootstrap/Makefile` for three-stage verification

## What didn't ship

- Phase 6 (Bootstrap Freeze & Validation) tasks 1–9 were partially deferred — completed in v0.7.0 Phase 1
- Self-hosted `lower.mn` deferred to v0.7.0
- Three-stage bootstrap verification deferred to v0.7.0

## Key metrics

| Metric | Value |
|--------|-------|
| Tests | 2,500+ |
| MIR lowering tests | 71 |
| MIR optimizer tests | 61 |
| MIR instruction types | ~35 |
| `lower.py` LOC | 1,397 |
| Phases completed | 5/6 (Phase 6 partial) |
