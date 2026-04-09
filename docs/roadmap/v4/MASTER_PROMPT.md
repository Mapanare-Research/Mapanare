# Master Prompt — Execute Roadmap v4.22.0 → v4.25.0

> Make it real. v4.14–v4.17 fixed bugs and achieved bootstrap. v4.18–v4.20
> added syntax but skipped the hard parts. v4.21 cleaned up the mess.
> Now finish what was promised: dead block elimination, type-safe MIR,
> async runtime wiring, and FFI that actually calls compiled libraries.
> Each version has its own PLAN.md and PROMPT.md.
> Execute one at a time. Rebuild + golden + stage2 after every .mn change.
> Run full lint (black + ruff + mypy) before every commit.
> Read CLAUDE.md for project context.

---

## The Debt (honest accounting)

v4.14.0-v4.17.0 were solid — real bug fixes, real features, verified:

| Version | What Was Done | Quality |
|---------|---------------|---------|
| v4.14.0 | Runtime NULL check, cross-module push type fix | SOLID — fixed real crash |
| v4.15.0 | Module-level let across both pipelines | SOLID — caused 6 test regressions (fixed in v4.21) |
| v4.16.0 | Constant propagation pass | PARTIAL — dead block elim deferred |
| v4.17.0 | Fixed-point bootstrap (0.062% diff) | SOLID — compiler compiles itself |

v4.18.0-v4.20.0 were rushed — syntax only, no runtime:

| Version | What Was Claimed | What Was Actually Done |
|---------|-----------------|----------------------|
| v4.18.0 | Tensor shapes + @gpu auto-kernels | `const` keyword (synonym for module-level let). No shape checking. No auto-kernel extraction. |
| v4.19.0 | Reactive async with backpressure | `async`/`await` as grammar keywords only. No MIR lowering. No cooperative scheduling. No ring buffer integration. |
| v4.20.0 | FFI bindings for Python/TS/Go | `bind.py` generates text files. Generated Python CAN'T actually call compiled code. No shared library build. No end-to-end test. |

v4.21.0 fixed lint, tests, and added CI — but the features are still hollow.

**What this arc must deliver:**
1. Dead block elimination that works (v4.22.0)
2. Type-safe MIR — no more string comparisons (v4.23.0)
3. async/await that actually runs (v4.24.0)
4. FFI bindings that actually call compiled code + tensor shapes that actually check (v4.25.0)

---

## Current State (as of v4.21.0)

**Self-hosted compiler:** 15,000+ lines across 12 modules in `mapanare/self/`:
`ast.mn` · `lexer.mn` · `parser.mn` · `semantic.mn` · `mir.mn` ·
`lower_state.mn` · `lower.mn` · `mir_opt.mn` · `emit_llvm_ir.mn` ·
`emit_llvm.mn` · `main.mn`

**What works:**
- 45/45 golden tests (all language features + const + async keyword)
- 11/11 stage2 modules valid (including main.mn)
- Near fixed-point: stage2→stage3 with 0.062% diff (69 lines / 111K)
- Module-level `let` and `const` across both pipelines
- Constant propagation in mir_opt.mn
- `mapanare bind --lang python|ts|go` generates text output
- `async`/`await` keywords parse in grammar and self-hosted lexer
- CI: black/ruff/mypy clean, GCC -Werror clean, WASM emission validated

**What's broken or hollow:**
- Dead block elimination disabled — BFS in `collect_targets` misses block references
  from while/for loop patterns emitted by self-hosted lowerer
- MIRType.kind is still String — 111+ comparison sites use `TK_INT()` string functions
- `async fn` does nothing at runtime — no stream creation, no task spawn
- `await expr` does nothing at runtime — no stream consumption
- `mapanare bind --lang python` generates ctypes wrapper but no .so is compiled
- Tensor shapes not checked at compile time (TypeInfo.tensor_shape exists but unused)
- 4 pre-existing test failures (unrelated to our changes)

**Culebra status:**
- 42 `break-inside-nested-control` findings — ALL false positives (return-in-for, not dropped break)
- 0 real CRITICAL findings in `mapanare/self/main.ll`
- C runtime clean: `culebra scan runtime/native/mapanare_core.c` — no critical

---

## Instructions

You are executing Mapanare from v4.22.0 through v4.25.0. This is the
"make it real" arc — every feature must have a working end-to-end test.

**Anti-rush rules (these exist because the last arc was rushed):**

1. **Do NOT commit until verification passes.** Run the proof command for
   each exit criterion. If it fails, fix it. Do not mark as DONE with
   failures outstanding.
2. **Do NOT defer core features.** If the PLAN says "dead block elimination
   enabled," it must be enabled and passing. Not "deferred because of X."
3. **Do NOT add syntax without runtime.** If async/await is in the plan,
   the golden test must show actual async behavior, not just keyword parsing.
4. **Run lint before EVERY commit.** `black --check . && ruff check . && mypy mapanare/`
   If it fails, fix it before committing. Do not commit lint violations.
5. **Run golden + stage2 after EVERY .mn change.** No exceptions.
6. **Record measurements.** IR size before/after, pass counts, diff counts.
   Put numbers in commit messages.
7. **If something can't be done, say why in the SESSION_REPORT.** Don't
   silently skip. Explain the blocker and what would unblock it.

**For each version N:**

1. Read `docs/roadmap/v4/vN/PLAN.md` — full task breakdown and exit criteria
2. Read `docs/roadmap/v4/vN/PROMPT.md` — context, key files, specific rules
3. Execute all phases in the plan, following its priority order
4. Run verification after EVERY change (not just at the end)
5. Run full lint: `black --check . && ruff check . && mypy mapanare/`
6. Run `/bump-version` to bump to version N
7. Commit with message: `vN: <theme> — <one-line summary with numbers>`
8. Update `docs/roadmap/v4/vN/PLAN.md` status to DONE
9. Write `docs/roadmap/v4/vN/SESSION_REPORT.md`
10. Move to version N+1

**Execution order (strict — each depends on the previous):**

| # | Version | Theme | What It Does | Proof Command |
|---|---------|-------|--------------|---------------|
| 1 | v4.22.0 | Dead Block Elim | Fix BFS, enable pass, measure IR reduction | `culebra scan main.ll --id break-inside-nested-control` + IR line count drops |
| 2 | v4.23.0 | MIRType Enum | TypeKind enum replaces all string comparisons | `grep 'TK_.*()' mapanare/self/*.mn` → 0 matches |
| 3 | v4.24.0 | async/await Wired | async fn creates stream, await consumes | Golden test runs via lli and prints async result |
| 4 | v4.25.0 | FFI E2E + Shapes | `mapanare bind` compiles .so, Python calls it | `python3 -c "from math_lib import add; assert add(3,4)==7"` |

**Dependencies:**

```
v4.21.0 (quality gate) ── 45/45 golden, 11/11 stage2, CI clean
    │
    ▼
v4.22.0 (dead block elim) ── fix BFS collect_targets
    │                          enable pass in optimize_mir
    │                          PHI cleanup for removed blocks
    │                          PROOF: IR line count decreases
    │                          UNLOCKS: smaller binaries, faster compilation
    ▼
v4.23.0 (MIRType enum) ── TypeKind enum in mir.mn
    │                       MIRType.kind: String → TypeKind
    │                       111+ comparison sites updated
    │                       TK_*() functions deleted
    │                       PROOF: grep 'TK_.*()' → 0
    │                       UNLOCKS: exhaustive match on types, no typo bugs
    ▼
v4.24.0 (async/await wired) ── async fn → create SPSC ring buffer + spawn task
    │                            await → call stream_next with cooperative yield
    │                            PROOF: golden test prints async result via lli
    │                            UNLOCKS: real concurrent programs
    ▼
v4.25.0 (FFI E2E + shapes) ── bind.py compiles .mn → .so
                                 Python ctypes wrapper calls the .so
                                 Tensor shape mismatch → compile-time error
                                 PROOF: Python import + assert, shape error test
                                 UNLOCKS: ecosystem interop
```

---

## Per-version verification tools

| Tool | Command | When to use |
|------|---------|-------------|
| Build stage1 | `python3 scripts/build_stage1.py` | After every .mn change |
| Golden tests | `python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1` | After every build |
| Stage2 | `python3 scripts/ir_doctor.py stage2 --timeout 60` | After emitter changes |
| Lint | `black --check . && ruff check . && mypy mapanare/` | Before every commit |
| Culebra scan | `culebra scan mapanare/self/main.ll` | After emitter changes |
| Culebra C scan | `culebra scan runtime/native/mapanare_core.c` | After C runtime changes |
| GCC check | `gcc -c -fsyntax-only -Wall -Wextra -Werror runtime/native/mapanare_core.c -I runtime/native` | After C runtime changes |
| Fixed-point | `bash scripts/verify_fixed_point.sh` | After any compiler change |
| Python tests | `python3 -m pytest tests/parser tests/semantic tests/llvm tests/diagnostics -q --tb=no` | After Python code changes |
| Valgrind | `valgrind --num-callers=20 ./mapanare/self/mnc-stage1 tests/golden/06_struct.mn` | After memory-related changes |

---

## What must be true after each version

| Check | v4.22 | v4.23 | v4.24 | v4.25 |
|-------|:-----:|:-----:|:-----:|:-----:|
| 45/45+ golden | YES | YES | YES+ | YES+ |
| 11/11 stage2 | YES | YES | YES | YES |
| black/ruff/mypy clean | YES | YES | YES | YES |
| GCC -Werror clean | YES | YES | YES | YES |
| Dead block elim enabled | **YES** | YES | YES | YES |
| IR size reduction measured | **YES** | YES | YES | YES |
| TypeKind enum in mir.mn | — | **YES** | YES | YES |
| Zero TK_*() string functions | — | **YES** | YES | YES |
| async fn creates stream at runtime | — | — | **YES** | YES |
| await consumes stream cooperatively | — | — | **YES** | YES |
| Golden test shows async behavior | — | — | **YES** | YES |
| `mapanare bind` produces callable .so | — | — | — | **YES** |
| Python calls compiled function | — | — | — | **YES** |
| Tensor shape mismatch is compile error | — | — | — | **YES** |

---

## Culebra Integration

Culebra v2.3.1+ is the quality gate for all versions.

### Current scan results (v4.21.0)

| Template | Count | Status |
|----------|-------|--------|
| `break-inside-nested-control` | 42 | All false positives (return-in-for pattern) |
| Other CRITICAL | 0 | Clean |

### Commands to use after every emitter change

```bash
# Quick scan for regressions
culebra scan mapanare/self/main.ll --severity critical
culebra triage mapanare/self/main.ll --brief

# After dead block elimination changes
culebra scan mapanare/self/main.ll --id break-inside-nested-control

# After type system changes
culebra health mapanare/self/main.ll

# Full summary
culebra summary mapanare/self/main.ll

# Track progress
culebra baseline save mapanare/self/main.ll
culebra baseline diff mapanare/self/main.ll
```

### Known false positives (do not fix — waste of time)

| Template | Finding | Why False Positive |
|----------|---------|--------------------|
| `break-inside-nested-control` | 42 sites | Template flags `return` in for loops (produces `ret`) as dropped break |
| `missing-typedef` | 9 sites in mapanare_core.c | Anonymous `typedef struct { } Name;` is valid C |
| `field-index-always-zero` | Golden struct test | Index 0 IS correct (accessing first field) |

---

## Session Summary Protocol

**After completing each version (or at the end of each session if mid-version),
write a session summary to `docs/roadmap/v4/vN/SESSION_REPORT.md`:**

```markdown
# vN.N.N Session Report — <date>

## Completed
- [ list of completed tasks with file paths and line numbers ]

## Measurements
- [ IR line count before/after ]
- [ Golden test count ]
- [ Stage2 module count ]
- [ Binary size change ]

## Still TODO (if mid-version)
- [ list of remaining tasks with specific next steps ]

## Issues Found
- [ unexpected bugs, test failures, regressions ]
- [ Culebra findings that need investigation ]

## Decisions Made
- [ any judgment calls, tradeoffs — WITH JUSTIFICATION ]
- [ nothing deferred without explanation ]

## Verification Results
- [ output of each proof command ]
- [ lint results ]
- [ golden/stage2 results ]

## Next Session Should Start With
- [ exact state, what to pick up, any blockers ]
```

---

## After v4.25.0

The language features are real (not just syntax):
- **Dead block elimination** — optimizer produces smaller IR
- **Type-safe MIR** — enum-based type comparisons, no string bugs
- **async/await** — cooperative streams with backpressure via ring buffers
- **FFI** — compile .mn → .so, call from Python/TS/Go

Plan v5.0.0:
- Perfect fixed-point (0 diff lines)
- Distributed actor-model routing for `@Agent`
- JIT hot-module replacement
- Package registry with Dato, net, security, AI packages
- Language server protocol (LSP) for IDE support
