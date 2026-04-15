# v4.131.0 Execution Prompt — Panel: v5 Gate Attempt (Target >= 9.0)

> Read with `PLAN.md` + `POST_RECOVERY_MASTER_PROMPT.md`. Panel
> release. Seven reviewers grade the closeout arc (v4.121.0-v4.130.0).
> v5 gate. The mechanical rule applies. 131 releases deep.

---

## Why v4.131.0 exists

The v4.120.0 panel returned 8.21/10 with one NEEDS WORK (Anaconda
7.6 on CI/testing). The 11-release closeout arc that followed
addressed every finding:

- **v4.121.0**: DWARF warning + trait fix (make test fully green)
- **v4.122.0**: Qs.1 List<Int> indexing fix (real user-visible bug)
- **v4.123.0**: Dead-code sweep (optimizer.py + TBAA deleted)
- **v4.124.0**: Rt.1 unboxed enum payloads (perf improvement)
- **v4.125.0**: Benchmark refresh + flaky audit + docs
- **v4.126.0**: Golden test push (target 40/64+ native)
- **v4.127.0**: GitNexus codebase audit (dead code, ABI, SPEC cross-ref)
- **v4.128.0**: Self-hosted fixed-point refinement
- **v4.129.0**: Documentation + SPEC sync
- **v4.130.0**: Pre-panel prep + third flaky audit + sanitizer reports

The evidence is assembled. The pre-panel audit (v4.130.0) fact-checked
every claim. The MEASUREMENTS.md draft has every metric. Now the 7
reviewers render judgment.

Target: aggregate >= 9.0 with 0 NEEDS WORK for Option A (tag v5.0.0).
Previous score: 8.21. Gap to close: 0.79 points across 7 reviewers.

---

## Read before starting

1. PLAN.md
2. `v4.130.0/SESSION_REPORT.md`
3. `docs/roadmap/v4/v4.130.0/FLAKY_AUDIT_3.md` — third flaky audit
4. `docs/roadmap/v4/v4.130.0/VALGRIND_REPORT.md` — sanitizer results
5. `docs/roadmap/v4/v4.130.0/ASAN_REPORT.md` — sanitizer results
6. `.reviews/v4.131.0/PRE_PANEL_AUDIT.md` — fact-checked claims
7. `docs/roadmap/v4/v4.131.0/MEASUREMENTS.md` — draft metrics (finalize in Phase 2)
8. `docs/roadmap/v4/v4.126.0/GOLDEN_TRIAGE.md` — golden test failure analysis
9. `docs/roadmap/v4/v4.127.0/GITNEXUS_AUDIT.md` — structural findings from graph audit
10. `docs/roadmap/v4/v4.128.0/FIXEDPOINT_BASELINE.md` — fixed-point metrics
11. `docs/roadmap/v4/v4.129.0/SPEC_AUDIT.md` — documentation audit
12. `.reviews/v4.120.0/README.md` — previous panel result (8.21/10)
13. Every SESSION_REPORT.md from v4.121.0 through v4.130.0

---

## GitNexus (code graph — use during panel preparation + execution)

The repo is indexed by GitNexus (23K+ nodes, 56K+ edges). Use it
during pre-panel sweep and panel execution to verify claims, trace
regressions, and answer reviewer questions in real time.

```bash
# Pre-panel sweep: verify no regressions
gitnexus impact emit_llvm_text.py        # what depends on the emitter?
gitnexus impact __mn_enum_unbox          # blast radius of enum unboxing
gitnexus query "list indexing argument"  # verify Qs.1 fix is wired

# During panel: answer reviewer questions
gitnexus context MnString                # Mamba asks about runtime layout
gitnexus context emit_enum_match         # Rattler asks about IR codegen
gitnexus query "async scheduler spawn"   # Viper asks about concurrency
gitnexus query "SPEC documentation"      # Coral asks about spec compliance

# Verify dead-code claims
gitnexus query "optimizer legacy"        # should return nothing (deleted)
gitnexus query "TBAA metadata"           # should return nothing (deleted)

# Verify GitNexus audit findings (v4.127.0)
gitnexus query "unreachable functions"   # cross-check dead code report
gitnexus query "circular dependency"     # cross-check community analysis

# Full status
gitnexus status                          # check freshness before panel
gitnexus analyze                         # re-index if stale
```

**Panel workflow:** Before spawning reviewers, run `gitnexus status`
to ensure the index matches HEAD. During reviewer execution, use
`gitnexus context` and `gitnexus query` to ground reviewer questions
in actual code rather than stale assumptions.

---

## Decisions to make before starting

### Decision 1: Panel format

- **Individual then aggregate**: each reviewer writes independently, then scores are combined
- **Discussion format**: reviewers see each other's drafts and can revise

**Default: individual then aggregate.** Independent reviews are more honest. No groupthink. Same format as v4.120.0.

### Decision 2: What if a regression is found during pre-panel sweep?

- **Fix it, then panel**: delay the panel until the regression is resolved
- **Panel with known regression**: document it, let the panel factor it in

**Default: fix it, then panel.** Do not run the panel on broken code.

### Decision 3: How to handle Option C (release candidate)

If the aggregate is >= 8.5 but < 9.0 with 0 NEEDS WORK:

- **Tag v5.0.0-rc1**: signal that v5 is imminent but not final
- **Continue v4.132.0+**: treat it as Option B

**Default: tag v5.0.0-rc1.** A release candidate is honest. It says "almost" without claiming "done."

### Decision 4: Comparison with v4.120.0

The panel should explicitly compare scores against v4.120.0 for each reviewer:

- **Delta required**: each reviewer must state whether their score went up, down, or stayed the same
- **Independent scoring**: each reviewer scores on absolute merit, no reference to prior scores

**Default: delta required.** The closeout arc exists because of the v4.120.0 findings. Each reviewer should state whether their domain improved.

---

## Culebra discipline

```bash
culebra scan mapanare/self/main.ll
culebra baseline diff mapanare/self/main.ll
culebra journal add "v4.131.0: panel — v5 gate attempt 3" --action milestone --tags "v4.131.0,panel,v5-gate"
```

**Wrap every build** with `culebra wrap -- <build command>`.
**End every session** with `culebra baseline diff` + `culebra journal add`.

---

## Commit checkpoints

| Phase | Commit message |
|---|---|
| 1 | `v4.131.0 phase 1: pre-panel sweep (tests, sanitizers, fixed-point, CI)` |
| 2 | `v4.131.0 phase 2: MEASUREMENTS.md finalized` |
| 3 | `v4.131.0 phase 3: panel run (7 reviewers, aggregate N.NN/10)` |
| 4 | `v4.131.0 phase 4: V5_DECISION.md (Option A/B/C)` |
| 5 | `v4.131.0 phase 5: version tag + updates (if v5)` OR `v4.131.0 phase 5: v4.132.0 plan (if not v5)` |
| Final | `v4.131.0: panel — v5 gate (attempt 3) — [RESULT]` |

---

## Ready-to-start checklist

- [ ] On `dev` branch, clean working tree
- [ ] `make test` passes
- [ ] v4.130.0 SESSION_REPORT.md committed
- [ ] FLAKY_AUDIT_3.md committed (from v4.130.0)
- [ ] VALGRIND_REPORT.md committed (from v4.130.0)
- [ ] ASAN_REPORT.md committed (from v4.130.0)
- [ ] PRE_PANEL_AUDIT.md committed (from v4.130.0)
- [ ] MEASUREMENTS.md draft committed (from v4.130.0)
- [ ] GITNEXUS_AUDIT.md committed (from v4.127.0)
- [ ] All CI jobs green

## Ready-to-ship checklist

- [ ] All 13 exit criteria from PLAN.md verified
- [ ] Pre-panel sweep: all tests pass, sanitizers clean
- [ ] MEASUREMENTS.md finalized with all metrics
- [ ] Panel executed: 7 individual reviews completed
- [ ] Aggregate score computed and recorded
- [ ] v5 decision documented in V5_DECISION.md
- [ ] If v5: VERSION updated, tag created, README updated, CHANGELOG entry
- [ ] If not v5: v4.132.0+ plan documented
- [ ] Golden count documented (both pipelines)
- [ ] Fixed-point status documented
- [ ] Sanitizer results documented
- [ ] All v4.120.0 carry-forward items addressed
- [ ] ROADMAP.md updated
- [ ] `make test` passes
- [ ] `make lint` passes
- [ ] Culebra baseline saved
- [ ] CHANGELOG.md updated
- [ ] SESSION_REPORT.md written

- [ ] Roadmap status updated (PLAN.md Status->DONE, v4/README.md row, ROADMAP.md row, CLAUDE.md current version) -- see POST_RECOVERY_MASTER_PROMPT.md "Roadmap status update"

---

## Final commit (MANDATORY -- do not end the session without this)

```bash
# 1. Stage everything
git add -A
git status  # review -- no secrets, no binaries

# 2. Commit with the version tag
git commit -m "v4.131.0: panel — v5 gate (attempt 3) — [RESULT]"

# 3. Archive Culebra journal + baseline
cp .culebra-journal.jsonl  docs/roadmap/v4/v4.131.0/culebra-journal.jsonl
cp .culebra-baseline.json  docs/roadmap/v4/v4.131.0/culebra-baseline.json
culebra journal add "v4.131.0 shipped — [RESULT]" --action milestone --tags v4.131.0

# 4. Bump VERSION (depends on panel outcome)
# If Option A: echo "5.0.0" > VERSION
# If Option B: echo "4.132.0" > VERSION
# If Option C: echo "5.0.0-rc1" > VERSION
git add VERSION docs/roadmap/v4/v4.131.0/culebra-journal.jsonl docs/roadmap/v4/v4.131.0/culebra-baseline.json
git commit -m "Bump VERSION to [NEXT]"
```

**Do not end the session without committing.** Uncommitted work is lost work.

---

## After v4.131.0

The cadence works. Whatever the panel decides, we keep shipping.

If **v5.0.0**: the v5 era begins. New roadmap, new arcs, new panel cadence. Full suspension async, tensor advanced ops, and cross-module compilation are the v5 feature targets. The v4.x line closes at 131 releases.

If **v5.0.0-rc1**: one more release (v4.132.0 or v5.0.0) to close the remaining items. The release candidate signals confidence.

If **v4.132.0+**: the recovery continues. The gaps the panel identified become the next phase. The cadence is the cadence. Every release has a PLAN.md, a PROMPT.md, a SESSION_REPORT.md. Every claim is verifiable. The process that built 131 releases can build 132.
