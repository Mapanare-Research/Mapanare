# Master Prompt — Execute Roadmap v4.14.0 → v4.20.0

> Ditch Python. Ship features. The foundation is done — now build on it.
> v4.8.0-v4.13.0 fixed workarounds, enabled semantic checking, added string
> pooling, named constants, and a self-hosted optimizer.
> v4.14.0-v4.17.0 finishes compiler maturity → Python independence.
> v4.18.0-v4.20.0 ships real language features.
> Each version has its own PLAN.md and PROMPT.md.
> Execute one at a time. Rebuild + golden + stage2 after every .mn change.
> Read CLAUDE.md for project context.

---

## The Ultimate Destination (keep in context)

We are building an AI-native compiled systems language. The Python bootstrap
was necessary to get here, but the self-hosted compiler is 15,000+ lines of
Mapanare and produces working native binaries. Now we cut the cord:

- **v4.14.0-v4.17.0:** Fix remaining compiler bugs, complete the optimizer,
  achieve fixed-point bootstrap (compiler compiles itself with identical output)
- **v4.18.0-v4.20.0:** Tensor shapes, `@gpu` auto-kernels, reactive async,
  auto-generated FFI bindings
- **v5.0+:** Distributed agent routing, JIT hot-module replacement

---

## What v4.8.0-v4.13.0 Accomplished (foundation arc)

| Version | What Was Done |
|---------|---------------|
| v4.8.0 | 8 workaround sites removed, PHI root cause fixed in lower.py |
| v4.9.0 | Semantic checker enabled as blocking (misdiagnosed "memory bug" was false positives) |
| v4.10.0 | skip_struct_ret removed, str(true)/str(-128..127) pooled, ptr-field-aware drop glue |
| v4.11.0 | 81 `.kind == "..."` → TK_*() named constants, zero raw string comparisons |
| v4.12.0 | mir_opt.mn created with constant folding, wired into compile() pipeline |
| v4.13.0 | Foundation gate verified, REFACTOR_SUMMARY.md written |

## What v4.8.0-v4.13.0 Left Open (honest accounting)

| Item | Why | Fixed In |
|------|-----|----------|
| break-inside-nested-control (3 CRITICAL) | Python lowerer drops break in nested if/for | v4.14.0 |
| main.mn stage2 crash (10/11) | Drop glue escape analysis can't follow heap ptrs | v4.14.0 |
| Dead block elimination disabled | Emitter references unreachable blocks by label | v4.16.0 |
| Module-level let not supported | No LetDef AST variant, no parser support | v4.15.0 |
| MIRType still String (not enum) | Blocked by module-level let | v4.15.0 |
| Constant/copy propagation missing | Only constant folding implemented | v4.16.0 |
| Fixed-point not achieved | Cross-module type resolution gaps | v4.17.0 |

---

## Instructions

You are executing Mapanare from v4.14.0 through v4.20.0. Two phases:

**Phase A (v4.14.0-v4.17.0): Compiler maturity → Python independence**
- Fix remaining bugs, complete optimizer, achieve self-compilation
- After v4.17.0: Python bootstrap is optional, not required

**Phase B (v4.18.0-v4.20.0): Language features**
- New syntax, new type system features, new backends
- Each version adds user-facing capability

**For each version N:**

1. Read `docs/roadmap/v4/vN/PLAN.md` — full task breakdown and exit criteria
2. Read `docs/roadmap/v4/vN/PROMPT.md` — context and rules for that version
3. Execute all phases in the plan, following its priority order
4. Run verification after EVERY change (not just at the end)
5. Run `/bump-version` to bump to version N
6. Commit with message: `vN: <theme> — <one-line summary>`
7. Update `docs/roadmap/v4/vN/PLAN.md` status to DONE
8. Write `docs/roadmap/v4/vN/SESSION_REPORT.md`
9. Move to version N+1

**Execution order (strict — each depends on the previous):**

| # | Version | Theme | What It Does | Proof |
|---|---------|-------|--------------|-------|
| 1 | v4.14.0 | Break Fix + 11/11 | Fix 3 Culebra CRITICAL, fix main.mn stage2 crash | 0 Culebra CRITICAL, 11/11 stage2 |
| 2 | v4.15.0 | Module-Level Let + Enum | LetDef AST, parser support, MIRType → TypeKind enum | `grep 'TK_.*()' emit_llvm.mn` → 0 |
| 3 | v4.16.0 | Optimizer Complete | Dead block elim + const/copy propagation | Measurable IR size reduction |
| 4 | v4.17.0 | Fixed-Point Bootstrap | Compiler compiles itself identically | `verify_fixed_point.sh` passes |
| 5 | v4.18.0 | Tensors + @gpu | Compile-time shapes, auto-kernel extraction | GPU golden test runs |
| 6 | v4.19.0 | Reactive Async | async/await + Streams | Async golden test runs |
| 7 | v4.20.0 | FFI Bindings | Python/TS/Go binding generation | `mapanare bind` produces working bindings |

**Dependencies:**

```
v4.13.0 (foundation complete) ── 40/40 golden, 10/11 stage2
    │
    ▼
v4.14.0 (break fix) ── fix 3 break-inside-nested-control CRITICAL
    │                    fix main.mn drop glue crash → 11/11 stage2
    │                    UNLOCKS: clean Culebra scan
    ▼
v4.15.0 (module-level let) ── LetDef AST + parser + lowerer + emitter
    │                          MIRType.kind: String → TypeKind enum
    │                          UNLOCKS: proper compile-time constants
    ▼
v4.16.0 (optimizer complete) ── dead block elim (fix emitter label refs)
    │                            constant propagation, copy propagation
    │                            UNLOCKS: smaller IR, faster compilation
    ▼
v4.17.0 (fixed-point) ── cross-module type resolution fixes
    │                     3-stage self-compilation verification
    │                     stage2.ll == stage3.ll (identical IR output)
    │                     MILESTONE: Python bootstrap is OPTIONAL
    ▼
v4.18.0 (tensors + GPU) ── const keyword, Tensor<Float, [3,3]>
    │                        @gpu extracts to PTX/SPIR-V automatically
    │                        FIRST NEW LANGUAGE FEATURE since v4.2.0
    ▼
v4.19.0 (reactive async) ── async/await keywords
    │                         Streams as async primitive
    │                         Backpressure via ring buffers
    ▼
v4.20.0 (FFI bindings) ── mapanare bind --lang python|ts|go
                            Auto-generated from .mn function signatures
                            ENABLES: ecosystem interop
```

---

## Rules

- Do NOT skip versions or reorder them
- Do NOT start version N+1 until version N is committed and verified
- For v4.14.0-v4.17.0: focus on compiler quality, not new syntax
- For v4.18.0-v4.20.0: new features allowed, but foundation must not regress
- Make decisions autonomously — do not ask for confirmation on implementation choices
- Commit at each milestone within a version (not just at the end)
- **YOU ARE IN WSL** — run rebuild + golden + stage2 after EVERY .mn change

### Per-version verification tools

| Tool | Command | When to use |
|------|---------|-------------|
| Build stage1 | `python3 scripts/build_stage1.py` | After every .mn change |
| Golden tests | `python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1` | After every build |
| Stage2 | `python3 scripts/ir_doctor.py stage2 --timeout 30` | After emitter changes |
| Valgrind | `valgrind --num-callers=20 /tmp/mnc-O0 tests/golden/06_struct.mn` | After memory-related changes |
| Culebra scan | `culebra scan mapanare/self/main.ll` | After emitter changes |
| Culebra C scan | `culebra scan runtime/native/mapanare_core.c` | After C runtime changes |
| Python tests | `python3 -m pytest tests/parser tests/semantic tests/llvm -q --tb=no` | After Python code changes |
| GCC check | `gcc -c -fsyntax-only -Wall runtime/native/mapanare_core.c -I runtime/native` | After C runtime changes |
| Fixed-point | `bash scripts/verify_fixed_point.sh` | v4.17.0+ only |

---

## What must be true after each version

| Check | v4.14 | v4.15 | v4.16 | v4.17 | v4.18 | v4.19 | v4.20 |
|-------|:-----:|:-----:|:-----:|:-----:|:-----:|:-----:|:-----:|
| 40/40 golden | YES | YES | YES | YES | YES+ | YES+ | YES+ |
| 11/11 stage2 | YES | YES | YES | YES | YES | YES | YES |
| 0 Culebra CRITICAL | YES | YES | YES | YES | YES | YES | YES |
| break-inside-nested-control fixed | YES | YES | YES | YES | YES | YES | YES |
| Module-level let works | — | YES | YES | YES | YES | YES | YES |
| MIRType is enum | — | YES | YES | YES | YES | YES | YES |
| Dead block elim enabled | — | — | YES | YES | YES | YES | YES |
| IR size reduced (measured) | — | — | YES | YES | YES | YES | YES |
| Fixed-point passes | — | — | — | YES | YES | YES | YES |
| Python bootstrap optional | — | — | — | YES | YES | YES | YES |
| Tensor shapes compile | — | — | — | — | YES | YES | YES |
| @gpu auto-kernels work | — | — | — | — | YES | YES | YES |
| async/await compiles | — | — | — | — | — | YES | YES |
| `mapanare bind` works | — | — | — | — | — | — | YES |

---

## Current State (as of v4.13.0)

**Self-hosted compiler:** 15,000+ lines across 12 modules:
`ast.mn` (781) · `lexer.mn` (575) · `parser.mn` (2,249) · `semantic.mn` (1,900+) ·
`mir.mn` (791) · `lower_state.mn` (587) · `lower.mn` (3,602) · `emit_llvm_ir.mn` (258) ·
`mir_opt.mn` (~170) · `emit_llvm.mn` (3,200+) · `main.mn` (537)

**What works:**
- Full compilation pipeline: parse → check → lower → optimize → emit
- 40/40 golden tests (all language features: structs, enums, generics, closures, agents, GPU)
- 10/11 stage2 modules (main.mn drops to crash from modular compilation drop glue)
- Constant folding optimizer
- Semantic checker as blocking gate
- String pooling for bool + small int conversions
- Named type constants (TK_INT(), TK_FLOAT(), etc.)

**What's broken:**
- 3 break-inside-nested-control CRITICAL (Python lowerer bug)
- main.mn stage2 crash (drop glue escape analysis limitation)
- Dead block elimination disabled (emitter label references)
- No module-level let support (AST + parser gap)
- Fixed-point not achieved (cross-module resolution)

---

## Session Summary Protocol

**After completing each version (or at the end of each session if mid-version),
write a session summary to `docs/roadmap/v4/vN/SESSION_REPORT.md`:**

```markdown
# vN.N.N Session Report — <date>

## Completed
- [ list of completed tasks with file paths ]

## Still TODO
- [ list of remaining tasks ]

## Issues Found
- [ unexpected bugs, test failures, regressions ]
- [ Culebra findings that need investigation ]

## Decisions Made
- [ any judgment calls, tradeoffs, deferred items and why ]

## Next Session Should Start With
- [ exact state, what to pick up, any blockers ]
```

---

## Culebra Integration

Culebra v2.3.1+ is the quality gate for all versions.

### Known real findings (from v4.13.0 scan)

| Template | Finding | Status |
|----------|---------|--------|
| `break-inside-nested-control` | 3 sites in self-hosted code | Fix in v4.14.0 |

### Known false positives

| Template | Finding | Why False Positive |
|----------|---------|--------------------|
| `missing-typedef` | 9 sites in mapanare_core.c | Anonymous `typedef struct { } Name;` is valid C |
| `c-memcpy-size-mismatch` | 1 site (double→uint64_t) | Same size (8 bytes), correct type-punning pattern |
| `field-index-always-zero` | Golden struct test | Index 0 IS correct (accessing first field) |
| `undefined-named-type` | Golden struct test | Type IS defined at file top, regex doesn't look up |

---

## After v4.20.0

The language is complete for production use:
- **Self-compiling** — no Python dependency
- **GPU-accelerated** — tensor shapes + auto-kernel extraction
- **Async-native** — reactive streams with backpressure
- **Interoperable** — FFI bindings for Python/TS/Go

Plan v5.0.0:
- Distributed actor-model routing for `@Agent`
- JIT hot-module replacement
- Package registry (dato, net, security, ai packages)
- Language server protocol (LSP) for IDE support
