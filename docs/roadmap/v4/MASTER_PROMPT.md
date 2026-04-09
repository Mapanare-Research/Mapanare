# Master Prompt — Execute Refactor Roadmap v4.2.0 → v4.7.0

> Fix the foundation. Then evolve.
> The v4.0.0 production release shipped. An architectural audit found 21 issues.
> We are executing a 6-version refactor sequence to fix them.
> NO NEW LANGUAGE FEATURES UNTIL v4.7.0 IS COMPLETE.
> Each version has its own PLAN.md and PROMPT.md with full instructions.
> Execute one at a time, verify, commit, then move to next.
> Read CLAUDE.md for project context.

---

## The Ultimate Destination (keep in context)

We are building an AI-native compiled systems language. Everything we refactor
now is to prepare the architecture for:

- **v4.8.0+:** Compile-time tensor shapes, `@gpu` auto-kernel extraction to
  PTX/SPIR-V, reactive async (async/await tied to Mapanare Streams)
- **v5.0+:** Distributed actor-model routing for `@Agent`, auto-generated
  Python/TS/Go FFI bindings, JIT hot-module replacement

None of that works if the compiler leaks memory, races on signals, or silently
accepts wrong types. Fix the core first.

---

## Instructions

You are executing the Mapanare architectural refactor from v4.2.0 through v4.7.0.
There are 6 versions, each building on the previous one. You are FORBIDDEN from
implementing new language features until v4.7.0 is complete.

**For each version N:**

1. Read `docs/roadmap/v4/vN/PLAN.md` — it has the full task breakdown and exit criteria
2. Read `docs/roadmap/v4/vN/PROMPT.md` — it has the context and rules for that version
3. Execute all phases in the plan, following its priority order
4. Run the verification/exit criteria from the plan
5. Run `/bump-version` to bump to version N
6. Commit with message: `vN: <theme> — <one-line summary>`
7. Update `docs/roadmap/v4/vN/PLAN.md` status to DONE
8. Move to version N+1

**Execution order (strict — each depends on the previous):**

| # | Version | Theme | What It Fixes | Proof |
|---|---------|-------|---------------|-------|
| 1 | v4.2.0 | Clean House | 3 dead emitters, ~8,500 lines, `_coerce_arg` | Only `emit_llvm_text.py` remains, no `--no-mir` flag |
| 2 | v4.3.0 | Drop Glue | `skip_struct_ret` leak, string/map/stream/agent leaks | Valgrind: zero "definitely lost" on struct-return test |
| 3 | v4.4.0 | Thread Safety | Signal race, racy counters, COW corruption, agent lifecycle | TSan clean on multi-agent program |
| 4 | v4.5.0 | Type System | UNKNOWN passes everything, self-hosted skips semantic | Misspelled function → compile error (not silent success) |
| 5 | v4.6.0 | Self-Hosted Quality | Hardcoded tables, string kinds, workarounds, typed ptrs | Zero workaround comments, MIRType uses enum |
| 6 | v4.7.0 | Optimizer | O1/O2 gap, no self-hosted optimization, string alloc | Benchmarks show improvement, unified fixpoint |

After all 6: the refactor is complete. v4.8.0 opens the door to new features.

**Dependencies:**

```
v4.1.0 (ecosystem) ── package registry, version manager, installers
    │
    ▼
v4.2.0 (clean house) ── delete 3 emitters + emit_c.mn (~8,500 lines)
    │                    UNLOCKS: single emitter to fix drop glue in
    │                    REMOVES: _coerce_arg (36 call sites of raw memory reinterpret)
    │                    REMOVES: --no-mir, --emitter llvmlite flags
    ▼
v4.3.0 (drop glue) ── return-value escape analysis, free all temporaries
    │                  UNLOCKS: correct memory ownership for thread safety
    │                  FIXES: skip_struct_ret (every struct-returning fn leaked)
    │                  FIXES: map iterators, stream closures, agent struct, intern table
    ▼
v4.4.0 (thread safety) ── signal mutex, atomic counters, COW audit
    │                      UNLOCKS: safe concurrent agents
    │                      FIXES: signal free race, racy profiling counters
    │                      FIXES: agent arena lifecycle, message ownership, restart cleanup
    ▼
v4.5.0 (type system) ── UNKNOWN → UNRESOLVED/ERROR, wire self-hosted semantic
    │                    UNLOCKS: compiler catches errors at compile time
    │                    FIXES: ~85 silent UNKNOWN passthroughs in semantic.py
    │                    FIXES: self-hosted semantic analysis (1,900 lines) finally called
    │                    FIXES: self-hosted MIR verifier finally called
    ▼
v4.6.0 (self-hosted quality) ── field tables, MIRType enum, workaround fixes
    │                            UNLOCKS: maintainable self-hosted compiler
    │                            FIXES: ~160 lines hardcoded field index tables
    │                            FIXES: PHI zeroinitializer, substr off-by-one, ABI mismatch
    │                            FIXES: 2 typed pointers → opaque ptr
    ▼
v4.7.0 (optimizer) ── unified fixpoint, constant propagation, string pooling
    │                  UNLOCKS: better native code quality
    │                  FIXES: O1/O2 pass ordering gap
    │                  ADDS: self-hosted constant folding + propagation + dead block elimination
    │                  ADDS: string allocation pooling (str(true) = constant, small ints cached)
    ▼
v4.8.0+ (evolution) ── NEW FEATURES ALLOWED
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

### Per-version verification tools

| Tool | When to use |
|------|-------------|
| `.\dev.ps1 validate` | Before every commit |
| `/golden` | After every compiler change |
| `/rebuild` | After every emitter or self-hosted .mn change |
| `/stage2` | After emitter changes that affect IR output |
| `valgrind` | After every memory-related change (v4.3.0+) |
| TSan (`-fsanitize=thread`) | After every C runtime change (v4.4.0) |
| ASan (`-fsanitize=address`) | After every C runtime change (v4.3.0+) |
| Culebra `scan`/`triage` | After emitter changes that affect IR quality |
| Benchmarks | Before and after optimization changes (v4.7.0) |

---

## What must be true after each version

| Check | v4.2 | v4.3 | v4.4 | v4.5 | v4.6 | v4.7 |
|-------|:----:|:----:|:----:|:----:|:----:|:----:|
| `.\dev.ps1 validate` passes | YES | YES | YES | YES | YES | YES |
| 40/40 golden tests pass | YES | YES | YES | YES | YES | YES |
| Self-hosted rebuild works | YES | YES | YES | YES | YES | YES |
| Fixed point maintained (stage3 == stage4) | YES | YES | YES | YES | YES | YES |
| `emit_llvm.py` deleted | YES | YES | YES | YES | YES | YES |
| `emit_llvm_mir.py` deleted | YES | YES | YES | YES | YES | YES |
| `_coerce_arg` gone | YES | YES | YES | YES | YES | YES |
| `skip_struct_ret` removed | — | YES | YES | YES | YES | YES |
| Valgrind: zero "definitely lost" | — | YES | YES | YES | YES | YES |
| TSan clean on multi-agent program | — | — | YES | YES | YES | YES |
| Misspelled function → compile error | — | — | — | YES | YES | YES |
| Self-hosted calls semantic analysis | — | — | — | YES | YES | YES |
| `hardcoded_field_index` deleted | — | — | — | — | YES | YES |
| MIRType uses enum (not string) | — | — | — | — | YES | YES |
| Zero workaround comments in self-hosted | — | — | — | — | YES | YES |
| Unified O1/O2 fixpoint loop | — | — | — | — | — | YES |
| Self-hosted has constant folding | — | — | — | — | — | YES |
| `str(true)` returns constant (no alloc) | — | — | — | — | — | YES |

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

This ensures continuity across sessions and keeps an honest record of what
Culebra catches vs misses (so we can improve its templates).

---

## Culebra Integration

Culebra (v2.3.0, 64 templates) is integrated into the refactor prompts.
Four templates were specifically created for this roadmap:

| Template | Version | Detects |
|----------|---------|---------|
| `c/non-atomic-shared-global` | v4.4.0 | Plain `int64_t` globals that should be `_Atomic` |
| `c/free-without-lock` | v4.4.0 | `free()` on shared data without mutex |
| `ir/missing-drop-glue` | v4.3.0 | sret functions that allocate but never free |
| `ir/typed-pointer-legacy` | v4.6.0 | `i64*`, `void ()*` that should be opaque `ptr` |

**Important caveat:** Culebra templates use regex-based pattern matching. They
are helpful for catching known issues but:

- **False positives happen.** A template regex may be too broad. If a finding
  looks wrong, investigate before acting. Note it in the session report as a
  false positive so we can fix the template in the Culebra repo.
- **False negatives happen.** A template regex may miss a variant of the pattern.
  If you find an issue manually that Culebra should have caught, note it in the
  session report as a "new pattern discovered."
- **Template bugs are Culebra bugs, not Mapanare bugs.** If a scan produces
  nonsensical results, the template regex is likely off. Report it to the Culebra
  repo (`C:\Users\Juan\Documents\GitHub\Culebra`) — don't change Mapanare code
  to satisfy a broken template.
- **Culebra is a linter, not a verifier.** It catches patterns, not semantics.
  Always verify with valgrind/TSan/ASan for correctness — Culebra confirms the
  code looks right, the sanitizers confirm it runs right.

---

## After v4.7.0

The refactor is complete. The compiler is:
- **Correct** — drop glue works, types are checked, verifier runs
- **Safe** — thread-safe signals, atomic counters, COW audit done
- **Clean** — one emitter, no workarounds, no hardcoded tables
- **Fast** — unified optimizer, constant propagation, string pooling

Now plan v4.8.0: pick 1-2 features from the candidate list in
`docs/roadmap/v4/v4.8.0/PLAN.md` and build on the solid foundation.
