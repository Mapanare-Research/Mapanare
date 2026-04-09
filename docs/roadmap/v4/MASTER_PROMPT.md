# Master Prompt — Execute Foundation Roadmap v4.8.0 → v4.13.0

> Fix the foundation. No shortcuts. No new features until v4.13.0 is complete.
> The v4.0.0 production release shipped. v4.2.0-v4.7.1 made structural fixes.
> v4.8.0-v4.13.0 finishes the deep work the earlier versions deferred.
> Each version has its own PLAN.md and PROMPT.md with full instructions.
> Execute one at a time. Rebuild + golden + stage2 after every .mn change.
> Read CLAUDE.md for project context.

---

## The Ultimate Destination (keep in context)

We are building an AI-native compiled systems language. Everything we fix
now is to prepare the architecture for:

- **v4.14.0+:** Compile-time tensor shapes, `@gpu` auto-kernel extraction to
  PTX/SPIR-V, reactive async (async/await tied to Mapanare Streams)
- **v5.0+:** Distributed actor-model routing for `@Agent`, auto-generated
  Python/TS/Go FFI bindings, JIT hot-module replacement

None of that works if the compiler has workarounds, the semantic checker
corrupts memory, or struct-returning functions leak. Fix the core first.

---

## What v4.2.0-v4.7.1 Accomplished

| Version | What Was Done |
|---------|---------------|
| v4.2.0 | Deleted 3 emitters + emit_c.mn (~13,000 lines). Single pipeline. |
| v4.3.0 | Stream user_data free, __mn_intern_destroy at exit. |
| v4.4.0 | Atomic counters, signal free under lock. |
| v4.5.0 | TypeKind.UNRESOLVED/ERROR, type system framework. |
| v4.6.0 | hardcoded_field_index deleted (159 lines). |
| v4.7.0 | Unified fixpoint optimizer (O1+O2 merged). |
| v4.7.1 | WSL rebuild verified: 40/40 golden, 11/11 stage2. |

## What v4.2.0-v4.7.1 Deferred (honest accounting)

| Item | Why Deferred | Fixed In |
|------|-------------|----------|
| substr workaround (4 sites) | Needs root cause investigation | v4.8.0 |
| PHI zeroinit workaround (2 sites) | Needs root cause investigation | v4.8.0 |
| ABI mismatch workaround (2 sites) | Needs root cause investigation | v4.8.0 |
| semantic.mn memory corruption | ast__expr_ident_name reads freed data | v4.9.0 |
| skip_struct_ret still active | Blocked by semantic.mn fix | v4.10.0 |
| String pooling (str(true) allocs) | Blocked by skip_struct_ret removal | v4.10.0 |
| MIRType string→enum | Module-level let breaks stage2 IR | v4.11.0 |
| Self-hosted optimizer passes | No constant folding/propagation/DCE | v4.12.0 |

---

## Instructions

You are executing the Mapanare foundation hardening from v4.8.0 through v4.13.0.
There are 6 versions, each building on the previous one. You are FORBIDDEN from
implementing new language features until v4.13.0 is complete.

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

| # | Version | Theme | What It Fixes | Proof |
|---|---------|-------|---------------|-------|
| 1 | v4.8.0 | Workaround Fixes | substr (4), PHI zeroinit (2), ABI mismatch (2) | `grep "avoid.*substr\|avoid.*PHI\|avoid.*ABI" emit_llvm.mn` → 0 |
| 2 | v4.9.0 | Semantic Safety | ast__expr_ident_name invalid reads | Valgrind clean, check() enabled |
| 3 | v4.10.0 | Drop Glue Complete | skip_struct_ret leak, string alloc waste | Valgrind: 0 "definitely lost", str(true) = constant |
| 4 | v4.11.0 | Global Constants | Module-level let breaks stage2, MIRType strings | `grep '.kind == "' emit_llvm.mn` → 0 |
| 5 | v4.12.0 | Self-Hosted Optimizer | No MIR optimization in self-hosted | mir_opt.mn exists, IR size reduced |
| 6 | v4.13.0 | Foundation Gate | Final verification | Culebra clean, valgrind clean, ALL exit criteria met |

After all 6: the foundation is truly complete. v4.14.0 opens the door to features.

**Dependencies:**

```
v4.7.1 (verified) ── 40/40 golden, 11/11 stage2, Culebra baseline established
    │
    ▼
v4.8.0 (workarounds) ── fix substr/PHI/ABI root causes in emit_llvm.mn
    │                    8 workaround sites across 3 root causes
    │                    EACH needs: investigate → fix → remove workaround → rebuild
    ▼
v4.9.0 (semantic safety) ── fix ast__expr_ident_name memory corruption
    │                        UNLOCKS: check() in compile(), proper error detection
    │                        ROOT CAUSE: AST accessor functions read freed memory
    ▼
v4.10.0 (drop glue complete) ── remove skip_struct_ret, add string pooling
    │                            UNLOCKS: zero memory leaks in struct-returning fns
    │                            FIXES: str(true) allocates every call
    │                            REQUIRES: semantic.mn is memory-safe (v4.9.0)
    ▼
v4.11.0 (global constants) ── add module-level let support to self-hosted lowerer
    │                          UNLOCKS: MIRType string→enum migration
    │                          ROOT CAUSE: lowerer can't emit global constant init
    ▼
v4.12.0 (self-hosted optimizer) ── new mir_opt.mn module
    │                               3 passes: constant fold, propagate, dead block
    │                               WIRED into compile() pipeline
    ▼
v4.13.0 (foundation gate) ── Culebra clean, valgrind clean, everything verified
    │                         FINAL CHECK: all exit criteria from v4.8.0-v4.12.0 met
    │                         WRITES: REFACTOR_SUMMARY.md for v4.2.0-v4.13.0 arc
    ▼
v4.14.0+ (evolution) ── NEW FEATURES ALLOWED
                         tensor shapes, @gpu auto-kernels, reactive async, FFI bindings
```

---

## Rules

- Do NOT skip versions or reorder them
- Do NOT start version N+1 until version N is committed and verified
- Do NOT implement new language features — only fix/refactor/optimize
- If an exit criteria fails, fix it before moving on
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
| Culebra scan | `culebra scan /tmp/golden_output.ll` | After emitter changes |
| Culebra C scan | `culebra scan runtime/native/mapanare_core.c` | After C runtime changes |
| Python tests | `python3 -m pytest tests/parser tests/semantic tests/llvm -q --tb=no` | After Python code changes |
| GCC check | `gcc -c -fsyntax-only -Wall runtime/native/mapanare_core.c -I runtime/native` | After C runtime changes |

---

## What must be true after each version

| Check | v4.8 | v4.9 | v4.10 | v4.11 | v4.12 | v4.13 |
|-------|:----:|:----:|:-----:|:-----:|:-----:|:-----:|
| 40/40 golden | YES | YES | YES | YES | YES | YES |
| 11/11 stage2 | YES | YES | YES | YES | YES | YES |
| substr workarounds removed | YES | YES | YES | YES | YES | YES |
| PHI zeroinit workarounds removed | YES | YES | YES | YES | YES | YES |
| ABI mismatch workarounds removed | YES | YES | YES | YES | YES | YES |
| semantic.mn check() enabled | — | YES | YES | YES | YES | YES |
| Valgrind: no invalid reads in semantic | — | YES | YES | YES | YES | YES |
| skip_struct_ret removed | — | — | YES | YES | YES | YES |
| str(true) returns constant | — | — | YES | YES | YES | YES |
| Module-level let works in stage2 | — | — | — | YES | YES | YES |
| MIRType uses named constants | — | — | — | YES | YES | YES |
| Self-hosted optimizer exists | — | — | — | — | YES | YES |
| Culebra: 0 real CRITICAL | — | — | — | — | — | YES |
| Valgrind clean on golden tests | — | — | — | — | — | YES |

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

## Culebra Report
- Templates run: [ list ]
- True positives: [ findings that led to real fixes ]
- False positives: [ findings that were template regex issues — report to Culebra repo ]
- New patterns discovered: [ issues Culebra should detect but doesn't ]

## Decisions Made
- [ any judgment calls, tradeoffs, deferred items and why ]

## Next Session Should Start With
- [ exact state, what to pick up, any blockers ]
```

---

## Culebra Integration

Culebra v2.3.1 (59/59 templates) is the quality gate for the refactor.

### Known false positives (from v4.8.0 Phase 5 scan)

| Template | Finding | Why False Positive |
|----------|---------|--------------------|
| `missing-typedef` | 9 sites in mapanare_core.c | Anonymous `typedef struct { } Name;` is valid C |
| `c-memcpy-size-mismatch` | 1 site (double→uint64_t) | Same size (8 bytes), correct type-punning pattern |
| `c-non-atomic-shared-global` | 1 site | Local variable flagged as global |
| `field-index-always-zero` | Golden struct test | Index 0 IS correct (accessing first field) |
| `undefined-named-type` | Golden struct test | Type IS defined at file top, regex doesn't look up |

**Report these to Culebra repo when fixing templates in v4.13.0.**

### Templates to watch

| Template | What It Catches | Use In |
|----------|----------------|--------|
| `ir/missing-drop-glue` | sret functions without free | v4.10.0 |
| `c/free-without-lock` | free() on shared data | v4.4.0 (done) |
| `c/non-atomic-shared-global` | Plain int64_t globals | v4.4.0 (done) |
| `ir/typed-pointer-legacy` | i64*, void ()* | v4.11.0 |

---

## After v4.13.0

The foundation is truly complete. The compiler is:
- **Correct** — drop glue works for ALL functions, types are checked, semantic runs
- **Safe** — thread-safe signals, atomic counters, valgrind clean
- **Clean** — one emitter, zero workarounds, MIRType uses named constants
- **Fast** — unified optimizer in Python + self-hosted optimizer in .mn

Now plan v4.14.0: pick 1-2 features from the candidate list:
- Compile-time tensor shapes + `const` keyword
- `@gpu` auto-kernel extraction
- Reactive async (async/await + Streams)
- Auto-generated FFI bindings
- Distributed agent routing
