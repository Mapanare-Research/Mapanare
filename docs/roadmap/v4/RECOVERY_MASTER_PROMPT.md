# Recovery Master Prompt — Execute v4.27.0 → v4.31.0

> **Read this BEFORE reading any individual v4.27.0+ PLAN.md.** This prompt
> supersedes `MASTER_PROMPT.md` (which covers v4.22.0–v4.26.0). The v4.x
> evolution arc is over. v4.27.0 is the start of a recovery arc.

> Each version has its own PLAN.md and PROMPT.md.
> Execute one at a time. Rebuild + golden + stage2 after every .mn change.
> Run full lint (black + ruff + mypy) before every commit.
> Read CLAUDE.md for project context.
> Read `.reviews/v4.26.0/README.md` before starting.

---

## Why this exists (the honest accounting)

A 7-reviewer panel ran on v4.26.0 and returned the largest single-cycle
review regression in project history:

| Metric | v3.47.0 (release gate) | v4.26.0 |
|--------|------------------------|---------|
| Aggregate score | 9.79/10 | ~8.2/10 |
| Verdict | 7/7 unanimous PASS | 4 NEEDS WORK + 3 PASS WITH NOTES |
| CRITICAL findings | 0 | 10 |
| Carry-forward resolution | ~64% | ~10% |

Seven independent reviewers, working in parallel without communication,
converged on the same headline finding:

> The v4.18.0–v4.26.0 arc has been shipping parseable syntax without
> semantic enforcement or runtime wiring.

Six hollow features in eight versions:

1. `const` keyword — parser alias for `ModuleLetDef`, no semantics
2. `@gpu` / `@cuda` / `@vulkan` — `raise NotImplementedError` at `lower.py:986`
3. `await` — `return self._lower_expr(expr.expr)` (identity)
4. v4.25.0 FFI — DCE drops non-main-reachable, runtime not -fPIC, ctypes wrapper has no argtypes/restype, `.replace()` sledgehammer strips linkage
5. v4.5.0 MIR verifier — defined, never called
6. v4.17.0 fixed-point bootstrap — `verify_fixed_point.sh:104 EXIT=0` unconditional

Plus process collapse:

- CHANGELOG advertises tests that don't exist on disk
- Two v4.0.0 hard-blockers (matmul) byte-identical to v3.47.0 — 27 versions overdue
- `main.ll` version string `mapanare 4.7.1` — 19 versions stale
- `extern "Python" fn` silently xfailed (79 tests) since v4.2.0

Read the full report at `.reviews/v4.26.0/README.md` before starting.
Re-read it whenever you feel tempted to scope-creep.

---

## The Recovery Arc

Five versions. Each has explicit no-new-features exit criteria. Each
version's PLAN.md has a "what this version explicitly does NOT do"
section to prevent scope creep.

| # | Version | Theme | Closes | Estimated |
|---|---------|-------|--------|-----------|
| 1 | **v4.27.0** | Honesty Recovery | All 8 CRITICAL items + CHANGELOG honesty | 1–2 days |
| 2 | **v4.28.0** | Concurrency + v3.47.0 carry-forwards | 5 concurrency races + 4 v3.47.0 carry-forwards + version string regression | 1 day |
| 3 | **v4.29.0** | Build infrastructure + test honesty | 2 orphaned runtime files + 117 silent xfails + fixed-point teeth + CI hollow-feature gate | 1 day |
| 4 | **v4.30.0** | Codegen + emitter carry-forwards | `await` decision + agent dispatch + optimizer correctness + 6 7-cycle emitter items | 1–2 days |
| 5 | **v4.31.0** | Documentation truth + process | SPEC sync (26 versions) + dead code + CHANGELOG honesty CI + **next 7-reviewer panel** | 1 day |

Total estimated work: **5–8 days of focused execution**, ending with an
external 7-reviewer panel re-run.

**The recovery arc terminates externally.** The lead does not declare it
done. The panel does. If the v4.31.0 panel returns aggregate < 9.0 or any
NEEDS WORK verdict, v4.32.0 inherits the outstanding items and the arc
continues.

---

## Anti-rush rules (these are stricter than the v4.22.0–v4.26.0 prompt)

The previous prompt's anti-rush rules were ignored in v4.26.0 itself. The
panel cited that explicitly. These are stricter:

1. **No new features. None.** If a task is not in the active version's
   PLAN.md exit criteria, it goes to the next recovery version. Do not
   slip "while I'm in here" improvements. The 8-version regression died
   from "while I'm in here."
2. **Every CHANGELOG entry must point at a real test file.** Before
   committing, run `git ls-files tests/ | grep <claimed_test>` for every
   test mentioned in your draft entry. If the file doesn't exist, the
   feature isn't done.
3. **Every claimed-as-working feature must have a green pytest.** Not "the
   parser accepts it." Not "the lowerer doesn't crash." A pytest that
   exercises the runtime behavior the CHANGELOG describes.
4. **`raise NotImplementedError` is a bug, not a feature.** If you write
   one, you have not shipped the feature. Either implement it or delete
   the syntax that gets you to the raise site. v4.29.0 adds a CI gate that
   enforces this.
5. **`.replace()` over LLVM IR text is forbidden.** Every textual
   transformation of generated IR is a future "why is this broken" review
   item. v4.27.0 deletes the `define internal` `.replace()` hack. Do not
   add new ones.
6. **CHANGELOG honesty test.** Before tagging, every entry under the new
   version must be checkable with one of: `git ls-files`, `pytest`, or
   `grep` over the source. If you cannot mechanically verify a claim,
   strike it. v4.31.0 adds a CI script that enforces this.
7. **Pick the cheap path.** For decisions like `const` Path A vs Path B,
   `@gpu` Path A vs Path B, `await` Path A vs Path B: whichever path
   reaches CI-green soonest is the correct path. The panel said both
   paths are acceptable. The cowardly path is shipping nothing and leaving
   the CHANGELOG broken.
8. **Run `.\dev.ps1` before every commit.** Not "after I'm done with this
   batch." Every commit. The panel found regressions in tests that were
   currently failing locally — that means commits were going in without
   running validation.
9. **TSan before tagging.** v4.28.0 introduces TSan stress tests for the
   new races. v4.30.0 must run them. Concurrency fixes that pass under
   normal pytest can still race under load.
10. **A test that is skipped is a test that does not exist.** Do not add
    `@pytest.mark.skip` or `pytest.mark.xfail` without a comment naming
    the version that will un-skip it. v4.29.0 adds a CI gate.
11. **Boring fixes count.** v4.30.0's six 7-cycle emitter carry-forwards
    are boring. They are also the longest-running debt in the project. Do
    them. Do not defer again.
12. **The recovery arc terminates externally.** v4.31.0 ships when the
    next 7-reviewer panel gives ≥9.0 aggregate with zero NEEDS WORK
    verdicts. The lead does not self-certify completion.

---

## Execution order (strict)

```
v4.26.0 (shipped, panel verdict NEEDS WORK)
   │
   ▼
v4.27.0  Honesty Recovery (8 CRITICAL items)
   │     PROOF: pytest tests/bind/ -v passes round-trip Int/Float/String/Struct
   │     PROOF: MIRVerifier called in compile() (instrumented)
   │     PROOF: const is real (Path A) OR absent (Path B)
   │     PROOF: @gpu real OR absent
   │     PROOF: CHANGELOG entries map to existing files
   │     PROOF: zero `raise NotImplementedError` in source
   │     UNLOCKS: every subsequent recovery release builds on honest baseline
   ▼
v4.28.0  Concurrency + v3.47.0 carry-forwards
   │     PROOF: TSan-clean stress tests for signal/agent/registry
   │     PROOF: matmul shape NULL check + dim validation regression test
   │     PROOF: `mnc --version` prints VERSION file contents
   │     PROOF: test_version_string passes (was failing locally)
   │     UNLOCKS: thread-safe runtime, paid-down v3.47.0 debt
   ▼
v4.29.0  Build infrastructure + test honesty
   │     PROOF: orphaned db.c + html.c built and smoke-tested
   │     PROOF: ~80 fewer xfails in pytest -v
   │     PROOF: CI fails red on deliberate fixed-point regression
   │     PROOF: NotImplementedError CI gate active
   │     UNLOCKS: PR-time detection of future hollow features
   ▼
v4.30.0  Codegen + emitter carry-forwards
   │     PROOF: zero i64* / void()* in emit_llvm_text.py
   │     PROOF: nsw flags on int arithmetic
   │     PROOF: agent spawn/send/receive golden test passes
   │     PROOF: optimizer non-convergence raises ICE
   │     PROOF: await real OR absent
   │     UNLOCKS: clean IR, drained carry-forward queue
   ▼
v4.31.0  Documentation truth + process hardening
   │     PROOF: every code block in docs/SPEC.md parses
   │     PROOF: scripts/check_changelog_honesty.py passes (in CI)
   │     PROOF: scripts/check_no_hollow_features.py passes (in CI)
   │     PROOF: 7-reviewer panel re-run on v4.31.0 returns ≥9.0 + 0 NEEDS WORK
   │     UNLOCKS: recovery arc terminates externally; resume normal feature work
   ▼
v4.32.0+ Normal feature work resumes — only after v4.31.0 panel certifies
```

If at any point a recovery release misses an exit criterion, **do not
skip ahead.** Open a v4.27.0.1 patch release; do not advance to v4.28.0
with an unmet criterion. The whole point of the arc is that scope
discipline is enforced.

---

## Per-version verification tools

| Tool | Command | When to use |
|------|---------|-------------|
| Build stage1 | `python3 scripts/build_stage1.py` | After every .mn change |
| Golden tests | `python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1` | After every build |
| Stage2 | `python3 scripts/ir_doctor.py stage2 --timeout 60` | After emitter changes |
| Lint | `black --check . && ruff check . && mypy mapanare/` | Before every commit |
| Culebra scan | `culebra scan mapanare/self/main.ll` | After emitter changes |
| TSan stress | (per v4.28.0 PLAN) | Before tagging v4.28.0 |
| Fixed-point | `bash scripts/verify_fixed_point.sh` | After any compiler change |
| Honesty checks | `python3 scripts/check_changelog_honesty.py` (after v4.31.0) | Before every commit that touches CHANGELOG |
| Hollow-feature gate | `python3 scripts/check_no_hollow_features.py` (after v4.31.0) | Before every commit that touches `lower.py` or grammar |
| Full validation | `.\dev.ps1` | Before every commit |

---

## What must be true after each version

| Check | v4.27 | v4.28 | v4.29 | v4.30 | v4.31 |
|-------|:-----:|:-----:|:-----:|:-----:|:-----:|
| 46/46+ golden | YES | YES | YES | YES | YES |
| 11/11 stage2 | YES | YES | YES | YES | YES |
| black/ruff/mypy clean | YES | YES | YES | YES | YES |
| GCC -Werror clean | YES | YES | YES | YES | YES |
| FFI argtypes/restype populated | **YES** | YES | YES | YES | YES |
| `libmapanare_rt.a` built `-fPIC` | **YES** | YES | YES | YES | YES |
| `MIRVerifier().verify()` called in compile() | **YES** | YES | YES | YES | YES |
| `const` real OR absent | **YES** | YES | YES | YES | YES |
| `@gpu` real OR absent | **YES** | YES | YES | YES | YES |
| `semantic.py SemanticError` deleted | **YES** | YES | YES | YES | YES |
| CHANGELOG entries map to real files | **YES** | YES | YES | YES | YES |
| Signal value mutation under lock | — | **YES** | YES | YES | YES |
| Agent inbox MPSC-safe | — | **YES** | YES | YES | YES |
| Type registry locked | — | **YES** | YES | YES | YES |
| matmul shape NULL check | — | **YES** | YES | YES | YES |
| matmul dim validation | — | **YES** | YES | YES | YES |
| `mnc --version` matches VERSION file | — | **YES** | YES | YES | YES |
| `test_version_string` passes | — | **YES** | YES | YES | YES |
| TSan-clean stress tests | — | **YES** | YES | YES | YES |
| `mapanare_db.c` linked | — | — | **YES** | YES | YES |
| `mapanare_html.c` linked | — | — | **YES** | YES | YES |
| `extern "Python"` real OR absent | — | — | **YES** | YES | YES |
| `verify_fixed_point.sh` returns non-zero on diff | — | — | **YES** | YES | YES |
| CI `fixed-point` job propagates exit code | — | — | **YES** | YES | YES |
| `raise NotImplementedError` CI gate active | — | — | **YES** | YES | YES |
| `await` real OR absent | — | — | — | **YES** | YES |
| Agent dispatch wired | — | — | — | **YES** | YES |
| Optimizer non-convergence raises ICE | — | — | — | **YES** | YES |
| Zero `i64*` typed pointers | — | — | — | **YES** | YES |
| Zero `void ()*` typed pointers | — | — | — | **YES** | YES |
| `nsw` flags on int arithmetic | — | — | — | **YES** | YES |
| Self-hosted DCE uses BFS + clean_phis | — | — | — | **YES** | YES |
| Every code block in `docs/SPEC.md` parses | — | — | — | — | **YES** |
| Spanish README synced | — | — | — | — | **YES** |
| User-Agent matches VERSION | — | — | — | — | **YES** |
| `__mn_list_oob_buf` deleted | — | — | — | — | **YES** |
| CHANGELOG honesty CI gate | — | — | — | — | **YES** |
| Docs-vs-code drift CI gate | — | — | — | — | **YES** |
| Hollow-feature CI gate | — | — | — | — | **YES** |
| **Next 7-reviewer panel ≥9.0 + 0 NEEDS WORK** | — | — | — | — | **YES** |

---

## Session Summary Protocol

Every recovery release must produce a `SESSION_REPORT.md` with this
template (it's a recovery release, not a normal one — be brutally honest):

```markdown
# vN.N.N Session Report — <date>

## Verdict
- [ Aggregate score from internal smoke check, target progression toward >=9 ]
- [ Are there any items from the v4.26.0 panel still open after this version? ]

## Completed
- [ list of completed tasks with file paths and line numbers ]

## Carry-forward closed
- [ items from .reviews/CARRY_FORWARD.md that are now closed ]

## Carry-forward still open
- [ items deferred to v4.32.0+ with reason ]

## Measurements
- [ IR line count before/after ]
- [ Golden test count ]
- [ Stage2 module count ]
- [ Skip/xfail count delta ]
- [ Binary size change ]
- [ Carry-forward queue size before/after ]

## Decisions Made
- [ For every Path A/Path B decision in the PLAN: which path was taken and why ]

## Verification Results
- [ output of each proof command from PLAN exit criteria ]
- [ lint results ]
- [ golden/stage2 results ]
- [ TSan results (if applicable) ]

## Next Session Should Start With
- [ Read RECOVERY_MASTER_PROMPT.md ]
- [ Read docs/roadmap/v4/v(N+1).0/PLAN.md ]
- [ Read docs/roadmap/v4/v(N+1).0/PROMPT.md ]
- [ Specific blockers or context for the next phase ]
```

---

## After v4.31.0

**Only if the panel certifies it.** The arc terminates externally.

If certified:

The recovery arc is complete. Aggregate score is back to ≥9.0. Carry-forward
queue is below 5 items, none older than 2 cycles. CHANGELOG honesty,
docs-drift, and hollow-feature gates are active in CI. The compiler core
is in the same shape it was at v4.26.0; the difference is that the docs
and the claims are now true.

Resume normal feature work at v4.32.0+. The growth-feature backlog from
the original ROADMAP.md still applies:

| Feature | Target |
|---------|--------|
| Distributed agent routing | v5.0.0 |
| JIT hot-module replacement | v5.x |
| LSP improvements | v5.x |
| `await` coroutine lowering | v5.0.0 (deferred from v4.30.0 if Path B taken) |
| `@gpu` auto-kernel extraction | v5.0.0 (deferred from v4.27.0 if Path B taken) |
| DWARF debug info | v4.32.0 if appetite, else v5.x |

If not certified:

v4.32.0 inherits the outstanding items. The arc continues. Do not
declare victory. Read `.reviews/v4.31.0/README.md` carefully and write a
v4.32.0 PLAN that closes the new items the panel surfaced.

The recovery arc is not measured in versions. It is measured in the
aggregate score the next panel returns.
