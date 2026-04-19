# Perf Arc — v4.144.0 → v4.154.0

> **The Go-parity arc.** 11 releases. 1 goal: close the Rust gap on
> compiled CPU workloads to ≤ 1.5× and the Go gap on async workloads to
> ≤ 1.2×, with the evidence pack and story needed for external
> attention (HN / RedMonk / "language of the year" year-end coverage).

**Status:** PLANNED
**Opens after:** `v5.0.0-rc1` at v4.136.0 shipped, v4.143.0 post-rc1 panel shipped with aggregate 8.86 / 0 NEEDS WORK. Zero MEDIUM on the ledger for the first time since v4.99.0.
**Closes at:** v4.154.0 perf panel. Expected outcome: aggregate ≥ 9.5, clean `v5.1.0` tag.
**Estimated calendar:** 4–6 weeks solo.

---

## Why this arc exists

The v4.x engineering arc is finished. 143 releases, 92 % docket closure,
zero CRITICAL / HIGH / MEDIUM on the ledger, 0 NEEDS WORK verdicts at
v4.143.0 panel. v5.0.0-rc1 is live. What's *not* finished is the
**narrative the numbers should support**:

- **Current claim:** "AI-native compiled language." Competitors:
  Mojo (AI for Python), Julia (scientific), Elixir (actors), Go
  (concurrency), Rust (safety). Crowded positioning, no clear wedge.
- **Actual position (post-Bn.1 measurements):** roughly on par with Go
  on compiled CPU work, 1.6× slower than Go on async, 1.1–3.5× slower
  than Rust depending on workload, 4–5× slower than C. Fundamentally
  in the same performance class as Go.
- **Defensible story:** *"As concurrent as Go, as memory-safe as Rust,
  as readable as Python — measured, reproducible, compiled."* This
  story is true at v4.143.0 for most workloads and can be made true
  for all of them by closing the remaining codegen gaps.

The perf arc delivers the evidence pack for this story and the
marketing-usable artifacts (benchmark charts, IR diffs, experiment
ledger, technical blog posts) that turn a well-engineered compiler
into a noticed one.

## The 11 releases at a glance

| Release | Theme | Target | Closes | Effort |
|---|---|---|---|---|
| **v4.144.0** | LOW polish + perf baseline + THE PANEL (attempt 4) | Clean `v5.0.0` tag if aggregate ≥ 9.0; `v5.0.0-rc2` otherwise | Cb.5-tests, Cb.6/7/9/10, Option-A gate | 1–2 days |
| **v4.145.0** | **E1** — `enum_match` codegen vs Rust | 3.4× → ≤ 2× of Rust | Perf finding #1 | 2–4 h |
| **v4.146.0** | **E2** — `fib_recursive` / pure CPU calling convention | ≤ 1.1× of Rust | ABI correctness | 1–2 h |
| **v4.147.0** | **E3** — parameter-level `noalias` (escape-analysis-driven) | Unlock LLVM auto-vectorization | Vectorization story | 2–3 days |
| **v4.148.0** | **E4** — `string_concat` vs Rust | 5–10× → ≤ 2× of Rust | String perf | 1–2 days |
| **v4.149.0** | **E5** — ABI.1 struct-return ABI | Close ABI.1 panel carry | ABI.1 | 3–5 days |
| **v4.150.0** | **E6** — async agent pipeline vs Go | 1.61× → ≤ 1.2× of Go | Go parity story | 3–5 days |
| **v4.151.0** | **E7** — allocation hot path (`List<Int>::push`) | List throughput +30–50 % | Allocator perf | 2–3 days |
| **v4.152.0** | **E8** — re-enable LICM + inlining in self-hosted path | stage2.ll shrinks; goldens unchanged | Self-hosted perf | 2–4 days |
| **v4.153.0** | Pre-perf-panel refresh (6th flaky audit, full benchmark re-run, MEASUREMENTS.md FINAL) | Evidence pack complete | — | 1 day |
| **v4.154.0** | **THE PERF PANEL** (7 reviewers, perf-focused) | Aggregate ≥ 9.5, tag `v5.1.0` | — | 1 day |

**Total:** ~3–6 weeks end-to-end, budget ~4 weeks for a full-time solo sprint, ~6–8 weeks for part-time.

## The experiment loop (apply to every E-release)

Every perf release — v4.145.0 through v4.152.0 — runs this exact
six-step loop. This is the discipline that distinguishes "I tried
things until it got faster" from "I systematically closed a codegen
gap with evidence."

1. **Measure** (baseline)
   - `benchmarks/cross_language/run_benchmarks.py --only <name> --runs 20`
   - Record median wall, CPU, peak RSS in `BASELINE.md` for the release.
2. **Diff IR at -O0 and -O3**
   - `mapanare emit-llvm file.mn -O3 -o mn.ll`
   - `rustc -O --emit=llvm-ir file.rs -o rust.ll`
   - Extract the hot function; line up side-by-side in `IR_DIFF.md`.
3. **Form hypothesis**
   - One sentence: "Rust does X that we don't. Closing X would save
     approximately Y %." File as `HYPOTHESIS.md`.
4. **Patch**
   - Smallest possible change in `mapanare/emit_llvm_text.py`,
     `mir_opt.py`, or `lower.py`. Keep scope to the hypothesis.
5. **Re-measure**
   - Same command as step 1. Record in `RESULTS.md`.
   - **5 % rule:** keep the patch only if median improves ≥ 5 % on
     target AND no other benchmark regresses > 2 %.
6. **Record**
   - Append to `docs/roadmap/v4/PERF_EXPERIMENTS.md` (running arc ledger):
     experiment ID, hypothesis, result (win / dead end / partial),
     lines changed, benchmark delta.
   - **Dead ends are data.** Document them. A failed experiment
     rules out a hypothesis and narrows the search space.

## Quality gates (every release, no exceptions)

Every perf release must pass all of these before tagging. A perf patch
that regresses any of them is rolled back, no exceptions.

| Gate | Requirement | Where it lives |
|---|---|---|
| `ruff check .` | 0 errors | CI + `make lint` |
| `black --check .` | 0 reformats | CI + `make lint` |
| `mypy mapanare/ runtime/` | 0 errors across 52 files | CI + `make lint` |
| `check_docs_drift` | clean (142+ blocks) | CI |
| `check_silent_skips` | clean | CI |
| `check_struct_registry` | clean (23 / 23 / 89+) | CI (Reg.1) |
| `check_no_hollow_features` | clean | CI |
| `check_changelog_honesty` | clean | CI |
| Non-bootstrap pytest | ≥ 5,160 passed / 0 failed | local + CI |
| Bootstrap pytest | 212 / 13 byte-identical | local |
| Native goldens (`mnc-stage1`) | 54 / 66 (or higher) | local |
| Valgrind ERRORS | 0 | local |
| ASan ASAN_ERROR | 0 | local |
| Fixed-point | stage2.ll ≈ stage3.ll within `DIFF_THRESHOLD=100` | local |
| **Benchmark 5 % rule** | Target benchmark improves ≥ 5 %, no other regresses > 2 % | local |
| **IR diff recorded** | `docs/roadmap/v4/v4.XYZ.0/IR_DIFF.md` exists | release dir |
| **Experiment entry recorded** | One line in `PERF_EXPERIMENTS.md` | arc ledger |

## What this arc does NOT do

- **Does not open new language features.** No new syntax, no new
  primitives, no new SPEC sections. The v4.143.0 language surface is
  frozen for the arc.
- **Does not touch the WASM or mobile backends.** Those are separate
  tracks.
- **Does not add benchmarks.** The existing 6 cross-language + 5 async
  are the fixed corpus. Adding benchmarks mid-arc corrupts the trend
  graph.
- **Does not do discretionary v5 tags.** v5.0.0 is gated by v4.144.0
  panel; v5.1.0 is gated by v4.154.0 panel. The mechanical rule applies
  at both gates.
- **Does not touch the panel format.** v4.154.0 uses the same 7-reviewer
  format as every prior panel, just with a perf-focused prompt.

## The marketing payload (what this arc produces beyond the code)

1. **Benchmark trend graph** — Mapanare median wall vs Rust/Go/C per
   release across the arc. The canonical HN chart.
2. **IR before/after gallery** — One 20-line IR diff per experiment,
   annotated. 8 diffs total. Developer catnip.
3. **`PERF_EXPERIMENTS.md` ledger** — Wins and dead ends, both named.
   The credibility artifact. Honest about what didn't work.
4. **One blog post per major experiment** — 500–800 words each.
   - "How Mapanare closed a 3× Rust gap on enum dispatch" (E1)
   - "Parameter-level noalias in a new LLVM-backed language" (E3)
   - "Matching Go scheduler throughput in under 200 logic lines" (E6)
   - "Revisiting four 'dead' MIR passes and what we learned" (E8)
5. **`docs/PERF.md`** — Landing page for the perf story. Replaces the
   "Benchmarks" section of the README with something dense, honest, and
   reproducible.
6. **`v5.1.0` tag** — Clean tag with perf-panel aggregate ≥ 9.5. Tweetable.

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Experiment regresses a non-target benchmark > 2 % | medium | medium | 5 % rule auto-triggers rollback. Patch is discarded; hypothesis re-examined. |
| LICM / inlining re-enable reintroduces Ge.1-class silent divergence | medium | high | Reg.1 gate catches struct-field drift. Run the full sanitizer sweep on every stage2.ll change. Cross-check stage2 vs stage3 md5. |
| Perf patch breaks self-hosted fixed point (line count creeps past 100) | medium | medium | `verify_fixed_point.sh --keep` runs on every release. If `DIFF_THRESHOLD=100` is exceeded, patch is held pending investigation. |
| A reviewer flags "pre-mature optimization, we lost architectural clarity" at v4.154.0 panel | low | high | Document each experiment's hypothesis + evidence. Dead ends are as valuable as wins. Keep diffs small (< 50 LOC per experiment). |
| Go gap doesn't actually close (scheduler architecture is a deep difference) | medium | high | If E6 hits dead-end, document honestly and pivot: ship the 1.4× Go story instead of the 1.2× goal. Honesty beats hitting an arbitrary number. |
| Arc duration creeps past 8 weeks | medium | low | Ship what's done. A partial perf arc at v4.150.0 that closed E1/E2/E4 is still story-worthy. Don't force v4.154.0 to wait for stragglers. |

## Carry-forward management across the arc

- Items closed in this arc land in `.reviews/CARRY_FORWARD.md` with
  per-release closure rows (same pattern as the v4.137.0–v4.143.0 arc).
- Items *opened* by mid-arc surprises go straight to the carry-forward
  queue with explicit severity + tracking release. Do not accumulate
  a docket-debt deferral tail.
- ABI.1 (24-byte struct return) is the main LOW panel-carried item
  closing in this arc (v4.149.0). Own.1 (move-semantics) stays deferred
  to v5.x refactor as-is; not in scope.

## Exit criteria for the arc (v4.154.0 perf panel)

| # | Check | Required |
|---|---|---|
| 1 | v4.144.0 panel cleared Option A (v5.0.0 tagged) OR Option C (rc2) with documented rationale | yes |
| 2 | E1–E8 complete: each has BASELINE.md + IR_DIFF.md + HYPOTHESIS.md + RESULTS.md + PERF_EXPERIMENTS.md entry | yes |
| 3 | Rust gap closed: geomean ≤ 1.5× of Rust across 6 cross-language benches | target; partial is still story-worthy |
| 4 | Go gap closed: async geomean ≤ 1.2× of Go | target |
| 5 | ABI.1 CLOSED in CARRY_FORWARD.md | yes |
| 6 | `docs/PERF.md` landing page shipped | yes |
| 7 | Benchmark trend graph shipped in `benchmarks/TREND_v4.144_v4.153.md` | yes |
| 8 | v4.154.0 panel aggregate ≥ 9.0; aggregate ≥ 9.5 fires `v5.1.0` tag | target |
| 9 | All quality gates (sanitizer, lint, fixed-point, goldens) green across every release in the arc | yes |
| 10 | PERF_EXPERIMENTS.md is the honest record (wins + dead ends) | yes |

## After the arc

- Arc-level closure document at `docs/roadmap/v4/v4.154.0/PERF_ARC_CLOSEOUT.md`
  summarizes the 10 experiments, final numbers, and where the compiler
  ended up vs where it started.
- Blog posts queued for publication (one per week post-arc, 4 posts
  total).
- `v5.1.0` tag carries the perf story; `v5.0.0` carries the v4.x
  engineering arc.
- Next arc opens based on whichever signal wins (adoption → ecosystem
  track, criticism → correctness track, or rest → polish track).

---

## Per-release plan + prompt files

- [v4.144.0/PLAN.md](v4.144.0/PLAN.md) — Panel + LOW polish
- [v4.144.0/PROMPT.md](v4.144.0/PROMPT.md)
- [v4.145.0/PLAN.md](v4.145.0/PLAN.md) — E1 `enum_match`
- [v4.145.0/PROMPT.md](v4.145.0/PROMPT.md)
- [v4.146.0/PLAN.md](v4.146.0/PLAN.md) — E2 `fib_recursive`
- [v4.146.0/PROMPT.md](v4.146.0/PROMPT.md)
- [v4.147.0/PLAN.md](v4.147.0/PLAN.md) — E3 `noalias` hot loops
- [v4.147.0/PROMPT.md](v4.147.0/PROMPT.md)
- [v4.148.0/PLAN.md](v4.148.0/PLAN.md) — E4 `string_concat`
- [v4.148.0/PROMPT.md](v4.148.0/PROMPT.md)
- [v4.149.0/PLAN.md](v4.149.0/PLAN.md) — E5 ABI.1 struct return
- [v4.149.0/PROMPT.md](v4.149.0/PROMPT.md)
- [v4.150.0/PLAN.md](v4.150.0/PLAN.md) — E6 async vs Go
- [v4.150.0/PROMPT.md](v4.150.0/PROMPT.md)
- [v4.151.0/PLAN.md](v4.151.0/PLAN.md) — E7 allocator
- [v4.151.0/PROMPT.md](v4.151.0/PROMPT.md)
- [v4.152.0/PLAN.md](v4.152.0/PLAN.md) — E8 LICM re-enable
- [v4.152.0/PROMPT.md](v4.152.0/PROMPT.md)
- [v4.153.0/PLAN.md](v4.153.0/PLAN.md) — Pre-panel refresh
- [v4.153.0/PROMPT.md](v4.153.0/PROMPT.md)
- [v4.154.0/PLAN.md](v4.154.0/PLAN.md) — THE PERF PANEL
- [v4.154.0/PROMPT.md](v4.154.0/PROMPT.md)
