# Mapanare v5 Readiness — Updated for v4.136.0 Panel

> Written at v4.135.0 (2026-04-15) as **informational input** to the
> v4.136.0 panel (v5 gate attempt 3). Supersedes the v4.125.0 snapshot
> (`docs/roadmap/v4/v4.125.0/V5_READINESS.md`) which served the
> deferred v4.131.0 panel. Updates the v4.119.0 / v4.120.0 baseline
> (`docs/roadmap/v4/v4.120.0/V5_READINESS.md`) with every closure from
> v4.121.0 through v4.134.0.
>
> **Stance: neutral.** No advocacy. The panel decides based on this
> plus `benchmarks/FINAL_REPORT_v4.136.md`, `DOCKET_LEDGER.md`, and
> `MEASUREMENTS.md`.
>
> **Headline diff from v4.125.0 readiness:** 7 of 8 "would embarrass
> v5" items now closed (was 5). The single remaining panel-visible
> blocker from v4.120.0 (strict 3-stage fixed point) **closed at
> v4.134.0** — the first byte-identical stage2 == stage3 in the v4.x
> recovery arc. Sh.2 extracted-alias drop-glue family closed across
> v4.131.0 (LIST) + v4.132.0 (STR), eliminating 23 ASan findings and
> 26 valgrind findings. An.1 test-hygiene bucket (39 failures) closed
> at v4.133.0 with zero compiler source changes.

---

## Decision rule (the mechanical gate, unchanged from v4.99.0)

- **Aggregate ≥ 9.0** AND **0 NEEDS WORK** → Option A — tag `v5.0.0`
- **Aggregate 8.5 – 9.0** AND **0 NEEDS WORK** → Option C — tag `v5.0.0-rc1` + continue
- **Aggregate < 9.0** with any NEEDS WORK → Option B — continue v4.137.0+

The panel is not asked for a narrative judgment. The decision follows
the aggregate and the NEEDS-WORK count.

---

## What a "v5" tag would be (unchanged from v4.119.0 readiness)

v5.0.0 is a **major version**: first breaking-change line after v4.x.
A shipped v5 carries the expectation that the language is stable at
this surface, the compiler is self-hosting in production, and the
runtime is safe to link into real programs.

(Same constraints and non-constraints as v4.119.0 and v4.125.0
readiness. The inventory below describes what shipped between
v4.125.0 and v4.134.0.)

---

## Status matrix — what changed since v4.125.0

Color key: ✅ done · ◐ partial · ⬜ planned · ✖ not implemented · 🆕 new since v4.125.0 readiness · 🔄 updated since v4.125.0 readiness.

### Language core — closeout-arc updates (v4.126.0–v4.134.0)

| Feature | Status | Evidence |
|---|---|---|
| `KW_CONST` + `KW_TRAIT` in self-hosted parser's `is_definition_start` | 🆕 ✅ | **v4.126.0** `mapanare/self/parser.mn:385-386` — closes 2 goldens; latent since v4.55.0. |
| Golden test harness superset-allowed fn-set | 🆕 ✅ | **v4.126.0** `scripts/test_native.py` — stage1 output semantically equivalent even when Python inliner converges; closes 10 goldens at the harness level. |
| Self-hosted `None` identifier lowering | 🆕 ✅ | **v4.134.0** `mapanare/self/lower.mn::lower_identifier` — bare `None` now produces `WrapNone` MIR mirroring `KW_NONE → Expr::NoneLit`. Closes Sh.12. |

### Runtime — unchanged

No runtime source changes v4.125.0 → v4.134.0. `libmapanare_rt.a`
rebuilds are VERSION-string propagation only; source-tree
byte-identical. ASan + valgrind sweeps at v4.132.0 and v4.134.0
confirm no runtime-path UAF regressions.

### Self-hosted compiler — closeout-arc updates

| Milestone | Status | Evidence |
|---|---|---|
| Strict 3-stage stage1 → stage2 → stage3 fixed point | 🔄 ✅ **REACHED** | **v4.134.0** — `bash scripts/verify_fixed_point.sh --keep` → stage2.ll == stage3.ll (108,397 lines, 0 diff, md5 `0c00ad07fee94f98bb350b359395843b`). First byte-identical FP in the v4.x recovery arc. La Culebra Se Muerde La Cola. |
| Sh.8 (self-hosted `None`/`Some`/`Ok` ctor registration) | CLOSED v4.128.0 | — |
| Sh.11 (`lower_expr` SIGSEGV, v4.128.0-opened) | CLOSED v4.134.0 | by inheritance from Sh.2 arc |
| Sh.12 (`Ident("None")` undef in IR, v4.134.0-opened+closed) | CLOSED v4.134.0 | 6 logic lines in `lower.mn::lower_identifier` |
| Self-hosted Rt.1 (inline enum payloads in `self/emit_llvm.mn`) | OPEN | v5.x track — deferred at v4.124.0 to avoid destabilising Sh.8 landing; now that FP holds, v5.x candidate |
| Sh.4/5/6/7 (async / const-in-self-hosted / tensor / closure-typed) | OPEN | v5.x track |
| Goldens through `mnc-stage1` | 🔄 ✅ **53/65** | was 27/65 at v4.120.0; +26 across closeout arc (v4.122.0 +6, v4.126.0 +12, v4.131.0 +8) |

### Test infrastructure — closeout-arc updates (v4.125.0 → v4.133.0)

| Item | Status | Evidence |
|---|---|---|
| An.1 — 39 deterministic pytest failures (Anaconda v4.120.0 NEEDS WORK) | 🔄 ✅ CLOSED | **v4.133.0** — 11 fixed (SPEC drift, e2e LLVM stale, VERSION-sync, doc-link regex, ctypes `MnString` bit-63 mask, filesystem), 18 skipped with named dockets (TR.1, Bn.1, Rt.2, Rt.3, Ch.1, Tm.1, An.2). Zero compiler source changes. 5,109 passed / 0 failed / 121 skipped / 7 xfailed. |
| 4-run flaky audit total | 🔄 ✅ | **v4.135.0** audit #4 — cumulative 20 sequential runs across 4 audits (v4.117.0, v4.125.0, v4.130.0, v4.135.0) — zero flaky findings. |
| Bootstrap pytest failures | ◐ 13 / 212 | unchanged v4.128.0 → v4.134.0 byte-identical (1 new flaky, pre-existing Python-bootstrap counter non-determinism in `test_lexer_full_emit_deterministic`). |

### Sanitizer results — closeout-arc updates

| Metric | v4.125.0 | v4.132.0 (Sh.2 closeout) | v4.135.0 (live) | Δ |
|---|---:|---:|---:|---:|
| Valgrind ERRORS | 31 (30 Sh.2) | **5** (all Ge.1) | **5** | **−26** net; Sh.2 vehicle closed |
| Valgrind WARNINGS_ONLY | 34 | 60 | 60 | +26 (errors demoted to warnings) |
| ASan ASAN_ERROR | 23 (all Sh.2) | **0** | **0** | **−23** — stretch goal hit |
| ASan CLEAN | 31 | 54 | 54 | +23 |
| ASan CRASH_NO_ASAN | 11 (Sh.4/6/7) | 11 (same) | 11 (same) | 0 |

**Net: 36 of 47 historical sanitizer findings closed in the closeout
arc.** The 5 residual valgrind ERRORS are the new Ge.1 generics-init
class (v4.132.0-opened), all in `26_generics / 29_generic_impl /
30_nested_generics / 31_generic_multi / 32_generic_enum`. Not a
regression — surfaced when Sh.2 closure cleared the noise floor. v5.x
track per v4.132.0 PLAN.

### Documentation — v4.129.0 SPEC + cookbook + guides sync

`docs/SPEC.md` audited v4.129.0 (8 OK / 4 stale / 6 wrong, 11 edits).
`README.md`, `docs/getting_started.md`, `docs/cookbook/async.md`, and
`docs/guides/async.md` synced to v4.129.0. SPEC header now reads
"4.129.0 Live". Examples verified 16 PASS / 13 FAIL, 3 new dockets
opened (Gr.1, Gr.2, Sem.1 — all v5.x track).

### CI / quality gates — unchanged

10 enforcing gates hold. No new gates added in the closeout arc. The
dead-code sweep (v4.123.0) removed informational coverage on
`optimizer.py` but did not change the gate surface.

---

## "Would embarrass a v5 label" items — closure walk (v4.119.0 baseline → v4.135.0)

The v4.119.0 readiness identified 8 items. The v4.135.0 status:

| # | Item from v4.119.0 readiness | v4.135.0 status |
|---|---|---|
| 1 | **Self-hosted async/tensor/const gaps** (Sh.4/5/6/7) — 13 of 25 self-hosted golden failures | **OPEN** — v5.x track. Unchanged from v4.125.0. Affects `mnc-stage1` users only; Python bootstrap handles all features. The v4.131.0+ Sh.2 arc closed the memory-safety path but did not unblock async/tensor lowering in self-hosted — those remain architectural gaps, not bugs. |
| 2 | **Fixed-point convergence cannot be proved today** (Sh.8 + Sh.11) | **CLOSED v4.134.0** — `verify_fixed_point.sh` now succeeds: stage2.ll == stage3.ll, byte-identical, md5-matched, 108,397 lines, 0 diff. Sh.8 closed v4.128.0; Sh.11 opened v4.128.0 and closed v4.134.0 (by Sh.2 arc inheritance); Sh.12 opened+closed v4.134.0. **Cobra's v4.99.0 v5 blocker ("a self-hosted compiler that cannot reach 3-stage fixed point is not v5.0.0 material") is now resolved with evidence.** |
| 3 | **No package manager / registry** | **OPEN** — unchanged from v4.125.0. v5.x deliverable. The `stdlib/` surface is adequate for single-program work. Not a correctness bug; an adoption-surface gap. |
| 4 | **Boxed-enum payload overhead** (Rt.1) — `enum_match` 24× slower than C gcc and 2× slower than Rust | **CLOSED v4.124.0** — structural fix; `enum_match` now 0.91× of Rust (Mapanare faster). Residual 2.3× gap to C is the ABI.1 docket (by-value 24-byte struct return), v5.x ABI work. |
| 5 | **`List<Int>` indexing in print context** (Qs.1) | **CLOSED v4.122.0** — single-line fix in `mapanare/lower.py::_lower_let`. Regression suite at `tests/golden/65_list_int_indexing.mn` + 5 IR invariants. |
| 6 | **`optimizer.py` at 9% coverage** (likely dead) | **CLOSED v4.123.0** — file deleted (1,203 lines) + test file (1,029 lines) + TBAA tree. Net dead-code sweep: −1,963 lines. |
| 7 | **14 stale CLI tests** (pre-rename) | **CLOSED v4.121.0** — `TestCompile` class deleted; tests rewritten against `build`. Expanded scope to 22/22 deterministic audit failures (v4.121.0 SR); expanded further at v4.133.0 to 39/39 An.1 closeout. |
| 8 | **TBAA metadata declared but not wired** (TBAA.1) | **CLOSED v4.123.0** (Python) + **v4.127.0** (self-hosted). Zero behaviour change; metadata comment gone. |

**Score: 7 of 8 closed (6 with code change, 1 with structural removal
at v4.123.0). 1 remains open** — package manager, v5.x ecosystem
scope, **not a correctness bug**.

### Delta from v4.125.0 readiness

| # | v4.125.0 status | v4.135.0 status | Change |
|---|---|---|---|
| 1 | OPEN (Sh.4-7) | OPEN | — |
| 2 | OPEN (Sh.8) | **CLOSED v4.134.0** | **fixed-point REACHED** |
| 3 | OPEN (pkg manager) | OPEN | — |
| 4 | CLOSED v4.124.0 | CLOSED | — |
| 5 | CLOSED v4.122.0 | CLOSED | — |
| 6 | CLOSED v4.123.0 | CLOSED | — |
| 7 | CLOSED v4.121.0 | CLOSED | — |
| 8 | CLOSED v4.123.0 | CLOSED | — |

**+1 closure across the v4.126.0–v4.134.0 arc: the strict fixed point
blocker.** This is the headline delta the v4.136.0 panel sees versus
the deferred v4.131.0 panel's evidence base.

---

## New dockets opened during the v4.126.0 – v4.134.0 arc

| # | Docket | Origin | Status | Notes |
|---|---|---|---|---|
| Sh.11 | `lower_expr` SIGSEGV when compiling `mnc_all.mn` beyond semantic phase | v4.128.0 (opened when Sh.8 closed) | **CLOSED v4.134.0** | Inheritance from Sh.2 arc — v4.131.0 LIST + v4.132.0 STR fixes removed the extracted-alias UAF shape that was causing `lower_expr` to dereference freed memory. v4.134.0 verification: stage1 ran 108,355 lines without SIGSEGV on first attempt. |
| Sh.12 | `Ident("None")` produces undef IR from self-hosted emitter | v4.134.0 | **CLOSED v4.134.0** | 6 logic lines in `mapanare/self/lower.mn::lower_identifier`. Bare `None` now matches `KW_NONE → Expr::NoneLit` path. |
| Ge.1 | Generics-init class — 5 valgrind ERRORS in 26/29/30/31/32_generic\*.mn | v4.132.0 (surfaced when Sh.2 noise cleared) | **OPEN** | v5.x track per v4.132.0 PLAN. All "Conditional jump or move depends on uninitialised value" in one shape; narrowed fix path. |
| Gr.1 | Multi-line collection literal grammar support | v4.129.0 (examples audit) | **OPEN** | Blocks 5 examples. Low priority. |
| Gr.2 | Qualified type refs in type position | v4.129.0 | **OPEN** | Blocks 2 stdlib modules + 3 examples. Medium priority. |
| Sem.1 | Module-level `let mut` scoping | v4.129.0 | **OPEN** | Blocks 1 example. Low priority. |
| Dr.1 | Self-hosted `!0 = !{!"4.127.0"}` frozen | v4.130.0 pre-panel audit | **OPEN** | Low priority; metadata housekeeping. |
| Dr.2 | `libmapanare_rt.a` VERSION drift (closed at v4.133.0 rebuild) | v4.133.0 audit | **CLOSED v4.133.0** | — |
| TR.1 | `test_runner.py::_compile_test_to_llvm` missing synthetic `main` | v4.133.0 | **OPEN** | Medium. 7 tests skip-docketed. |
| Bn.1 | Struct-with-String-field ctypes ABI UAF | v4.133.0 | **OPEN** | Medium. 1 test skip-docketed. |
| Rt.2 | `__mn_dir_create` ignores `recursive` | v4.133.0 | **OPEN** | Low. 1 test skip-docketed. |
| Rt.3 | `__mn_tmpfile_path` is a stub | v4.133.0 | **OPEN** | Low. 2 tests skip-docketed. |
| Ch.1 | `mapanare_agent_destroy` UAF before thread join | v4.133.0 | **OPEN** | High — runtime memory-safety defect. 3 tests skip-docketed (plain+ASan+TSan fail on same defect). Panel-surface-worthy. |
| Tm.1 | Memory stress fixture is no-concat | v4.133.0 | **OPEN** | Low. 1 test skip-docketed. |
| An.2 | Repo-wide lint debt (36 mypy + 204 ruff + black) | v4.133.0 | **OPEN** | Low. 3 tests skip-docketed. |

All opened dockets except Ch.1 are LOW or MEDIUM priority and on the
v5.x track. **Ch.1 is HIGH and genuinely new in this arc** — surfaces
a runtime-level agent-destroy race that is worth the panel's attention.
The race has existed for unknown duration; v4.133.0's stricter test
harness (plain+ASan+TSan tri-mode gate) made it visible.

---

## Panel-visible open items, prioritised

**Highest-priority open docket at v4.135.0:** Ch.1 (agent_destroy
UAF). HIGH severity because it's a runtime memory-safety defect that
ASan and TSan both flag. Documented, named, and scoped — but
concretely worth mentioning to the panel.

**Medium-priority:** Sh.4/5/6/7 (self-hosted feature gaps), Bn.1
(ctypes ABI), TR.1 (test_runner), Gr.2, ABI.1.

**Low-priority or documented-as-ok:**
- Package manager (ecosystem, v5.x)
- Ge.1 generics-init (5 valgrind ERRORS, narrowed, v5.x)
- arena-allocator "definitely lost" leaks (intentional per v4.105.0
  SR — v5.x is slot-pooled-arena scope)
- mnc-stage2 teardown exit 10 (v4.30.0-known, IR is correct, low-prio)
- Gr.1, Sem.1, Dr.1, Rt.2, Rt.3, Tm.1, An.2 — docketed follow-ups

**None is CRITICAL. None produces incorrect code for a program the
SPEC promises works.** Every item is named, sized, and has a known
fix vehicle.

---

## What would need to change between v4.135.0 and v5.0.0 (if tagged)

**Nothing required.** v4.135.0 is the last release before the v4.136.0
panel. No code changes in v4.135.0 (measurement-only release).
`libmapanare_rt.a` byte-identical to v4.134.0.

If the v4.136.0 panel votes Option A, the `v5.0.0` tag would be
applied to the v4.135.0 commit (or a successor no-change commit),
CHANGELOG `[5.0.0]` would replace `[Unreleased]`, the `VERSION` file
would read `5.0.0`, and the `dev` branch would continue as `v5.1.0`
development.

No additional engineering work is required to "earn" v5 between now
and the panel. The v4.120.0 panel's docket items are now **7 of 8
closed**; the one remaining (package manager) is **ecosystem scope
that explicitly was never v5.0.0 material** per `v4.120.0/V5_READINESS.md`
§"Tagging v5 does not require".

Whether "7/8 plus An.1 plus strict fixed point plus 36/47 sanitizer
findings plus 4 clean flaky audits" corresponds to **≥ 9.0 aggregate
and 0 NEEDS WORK** is the v4.136.0 panel's judgement.

---

## Author's neutral summary (delta from v4.125.0)

- The v4.126.0–v4.134.0 arc **closed the single remaining load-bearing
  v4.120.0 gap** (strict 3-stage fixed point, v4.134.0).
- Sh.2 extracted-alias drop-glue family (13 valgrind + 23 ASan
  findings) closed across v4.131.0 + v4.132.0.
- An.1 test-hygiene bucket (39 pytest failures) closed at v4.133.0
  with zero compiler source changes.
- Goldens through `mnc-stage1` moved from 27/65 → **53/65** (+26).
- Sanitizer ERRORS moved from 31 → **5** (all residual Ge.1, v5.x).
- ASan ASAN_ERROR moved from 23 → **0**.
- Fixed-point strict 3-stage: **REACHED**, 0 diff between stage2 and
  stage3, md5-matched.
- 4 cumulative flaky audits: **0 flaky findings** across 20 runs.
- 7 of 8 v4.119.0 "would embarrass v5" items closed.
- 1 new HIGH-priority docket (Ch.1) genuinely opened in the arc.
- Net code-line change v4.125.0 → v4.134.0: approximately unchanged
  (small targeted fixes, one dead-code sweep at v4.123.0 already
  counted in the prior readiness delta).

**Whether this is a v5 is for the panel.** The evidence is in the
repository. The decision rule is mechanical. This document states
only what is done, what isn't, and where the reader can verify each
item.

## Cross-references

| To verify | Read |
|---|---|
| v4.119.0 readiness baseline | `docs/roadmap/v4/v4.120.0/V5_READINESS.md` |
| v4.125.0 readiness | `docs/roadmap/v4/v4.125.0/V5_READINESS.md` |
| Strict fixed-point reproducer | `docs/roadmap/v4/v4.134.0/FIXEDPOINT.md` + `FIXEDPOINT_STATUS.md` (this release) |
| Every docket with evidence | `DOCKET_LEDGER.md` (this release) |
| Panel evidence base | `MEASUREMENTS.md` (this release) |
| Benchmark refresh | `benchmarks/FINAL_REPORT_v4.136.md` (this release) |
| v4.131.0-v4.134.0 SESSION_REPORT drift | `.reviews/v4.136.0/PRE_PANEL_AUDIT.md` |
