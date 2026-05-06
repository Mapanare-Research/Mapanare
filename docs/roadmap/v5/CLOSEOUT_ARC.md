# v5.x Arc — Closeout + Feature Parity + Re-Panel (target 9.7+)

> Three closeout releases clearing MEDIUM carry-forwards, then four
> feature-parity releases closing all Sh.* gaps and driving goldens to
> 66/66, then a final polish + re-panel. Features first, panel last —
> one panel instead of two.

---

## Roadmap Table

| Release | Theme | Items | Expected Lift | Effort |
|---------|-------|-------|---------------|--------|
| **v5.3.1** | Quick-win closeout | Lint fix, Bo.15/16/17/14r, Stream-C, An.9r | +0.15–0.25 | **30 min** |
| **v5.3.2** | Restore fixed-point | In.1-stage2 (extend `clone_instr_for_inline` to 30+ instruction kinds) | +0.15–0.20 | **1–2 hrs** |
| **v5.3.3** | SPEC + docs polish | SPEC-pkg section, SPEC header bump, signal demo | +0.02–0.05 | **1–2 hrs** |
| **v5.4.0** | **Own.1 Phase 2 — drop-glue** | Move instruction, EmitState slots, 4 drop-glue helpers, Sh.2 (11 goldens) | 54→65/66 | **3–5 sessions** |
| **v5.5.0** | **Sh.4 — self-hosted async** | `block_on`/`await` + coroutine lowering | closes 5 async goldens | **2–3 sessions** |
| **v5.6.0** | **Sh.6 — self-hosted tensor** | `Tensor`/`Float` types + nested-array literal parser | closes 5 tensor goldens | **3–4 sessions** |
| **v5.7.0** | **Sh.7 + or-pattern — 66/66** | Closure-typed params + bootstrap or-pattern fix | 65→**66/66** | **1–2 sessions** |
| **v5.7.1** | SPEC + docs polish (pre-panel) | SPEC refresh, README 66/66, PARITY_GAPS audit, known_issues cleanup | +0.05–0.10 | **1–2 hrs** |
| **v5.8.0** | **RE-PANEL** | Measurement + 7 reviewers | Target: **9.7+** | **1 session** |

---

## Per-Reviewer Recovery Path (full arc → v5.8.0 panel)

| Reviewer | v5.3.0 | What closes (v5.3.1–v5.7.1) | Expected v5.8.0 |
|----------|--------|-------------|-----------------|
| **Rattler** (9.3) | In.1-stage2, goldens ceiling | v5.3.2: cloner fix; v5.4.0–v5.7.0: 66/66 goldens | **9.7–9.8** |
| **Viper** (9.7) | Own.1 Phase 2 (28 panels) | v5.4.0: drop-glue + Move tracking | **9.8–9.9** |
| **Anaconda** (8.9) | Lint RED, stream tests, goldens | v5.3.1: lint + stream; v5.4.0–v5.7.0: full test coverage | **9.5–9.7** |
| **Cobra** (8.8) | Fixed-point, self-hosted parity | v5.3.2: fixed-point; v5.4.0–v5.7.0: all Sh.* closed | **9.5–9.7** |
| **Coral** (9.4) | SPEC-pkg, demo gap, tensor/async | v5.3.3+v5.7.1: SPEC polish; v5.5.0+v5.6.0: async+tensor | **9.6–9.8** |
| **Boa** (9.4) | Bo.15/16/17/14r, 66/66 badge | v5.3.1: docs; v5.7.1: full refresh | **9.6–9.7** |
| **Mamba** (9.6) | Stream-C, async parity | v5.3.1: stream fix; v5.5.0: async parity | **9.7–9.8** |
| **Aggregate** | **9.30** | — | **9.65–9.75** |

---

## MEDIUM Items Closure Schedule

| ID | Release | Reviewer(s) | Description |
|----|---------|-------------|-------------|
| Lint-v5.2.0 | v5.3.1 | Anaconda | `black . && ruff check --fix .` |
| Bo.15 | v5.3.1 | Boa | README fixed-point claim accuracy |
| Bo.16 | v5.3.1 | Boa | known_issues.md: remove "no pkg mgr" |
| Stream-C | v5.3.1 | Mamba | Fix test init + audit Ge.1r fallback |
| In.1-stage2 | v5.3.2 | Rattler, Cobra, Anaconda | Extend `clone_instr_for_inline` to all 30+ instruction kinds |

**5 MEDIUM → 0 MEDIUM in 2 releases.**

---

## LOW Items Status

| ID | Disposition | Release |
|----|-------------|---------|
| Bo.17 | Close | v5.3.1 |
| Bo.14r | Close | v5.3.1 |
| An.9r | Close | v5.3.1 |
| SPEC-pkg | Close | v5.3.3 |
| Demo gap (signals) | Close | v5.3.3 |
| Li.1 | Defer to v5.x | — |
| Own.1 P2 | Close | **v5.4.0** (self-hosted drop-glue) |
| Sh.2 | Close | **v5.4.0** (closes with Own.1 P2) |
| Sh.4 | Close | **v5.5.0** (self-hosted async) |
| Sh.5 | Defer to v5.x feature track | — |
| Sh.6 | Close | **v5.6.0** (self-hosted tensor) |
| Sh.7 | Close | **v5.7.0** (with or-pattern fix — 66/66) |
| Gr.1 | Defer | — |

---

## Feature-parity arc: v5.4.0–v5.7.0 goldens-to-66

The v5.3.x closeout clears MEDIUM carry-forwards. The v5.4.0–v5.7.0
arc targets the **native goldens ceiling** — currently stuck at 54/66
since v5.0.4. Then v5.7.1 polishes and v5.8.0 re-panels with
everything closed.

| Release | Theme | Closes | Goldens |
|---------|-------|--------|---------|
| **v5.4.0** | Own.1 Phase 2 — self-hosted drop-glue | Sh.2 (11 tests) | 54 → 65 |
| **v5.5.0** | Self-hosted async | Sh.4 (5 tests) | (already in 65) |
| **v5.6.0** | Self-hosted tensor | Sh.6 (5 tests) | (already in 65) |
| **v5.7.0** | Closure-typed + or-pattern fix | Sh.7 + B (2 tests) | 65 → **66/66** |
| **v5.7.1** | SPEC + docs polish | (pre-panel refresh) | 66/66 |
| **v5.8.0** | **RE-PANEL** | All items closed | Target: **9.7+** |

Note on accounting: the 12-test gap at v5.3.2 includes overlaps
across Sh.2/Sh.4/Sh.6/Sh.7/B buckets from the v4.126.0 triage. A
fresh triage pass at v5.4.0 Phase 0 re-anchors the trajectory. See
each release's PLAN.md for details.

---

## What NOT to do

- **Do not add features** in v5.3.1–v5.3.3. This is a closeout arc.
- **Do not touch the package registry.** v5.2.0 shipped; improvements
  go to v5.4+ feature track.
- **Do not attempt Li.1 (LICM).** The fixpoint + preheader design is
  a multi-session project, not a quick fix.
- **Do not attempt Own.1 P2.** Move semantics are a v5.x/v6.0 scope.

---

## Success Criteria

The arc succeeds when:
1. All 5 MEDIUM items are closed
2. `black --check . && ruff check .` returns 0
3. `bash scripts/verify_fixed_point.sh --keep` reaches stage2.ll
   that passes `llvm-as` (NEAR or better)
4. `python3 -m pytest tests/native/test_c_hardening.py` → 0 failures
5. README does not make factual claims contradicted by measurements
6. v5.4.0 re-panel aggregate >= 9.5

---

## v5.6.x docket sequence (memory-safety closeout, post-arc)

Issued during the v5.6.x bug-closeout arc (after the v5.4.0–v5.7.0
feature arc was scoped). Tracked here for completeness:

| Release | Docket | Status |
|---|---|---|
| v5.6.5 | Ve.1 (parser overflow) | CLOSED |
| v5.6.6 | Rt.04 (multi-level alias) | RESCOPED → v6.0 |
| v5.6.7 | Ve.2 (lowerer empty-list) | PARTIAL (11/18) |
| v5.6.8 | Ve.3 (stage2 OOM) | INVESTIGATION |
| v5.6.9 | Ve.3 | CLOSED; Ve.4 OPENED |
| v5.6.10 | Ve.2 + struct_byte_size + culebra | PARTIAL; Lk.1 OPENED |
| v5.6.11 | Ve.4 | CLOSED |
| v5.6.12 | Lk.1 + Ve.2 residuals | CLOSED |
| **v5.6.13** | **Layer 1 cleanup → struct lets** | **OPTIONAL — SHIPPED** |

Every v5.6.x docket is now resolved or appropriately deferred to
v6.0 (Rt.04 only). The v5.6.x closeout arc is genuinely complete
with no v6.0 deferrals from v5.6.x itself — the only v6.0 carry
is Rt.04 from v5.6.6, which has its own scoping rationale
(multi-level alias analysis is a borrow-checker concern).

v5.6.13 ships an optional Layer 1 cleanup: extends v5.6.12's
destination-passing pattern from List let-bindings to Struct
let-bindings (eliminates the `.si` scratch alloca in
`emit_struct_init` / `emit_struct_init_from_values`). Enum +
Map skipped after empirical analysis confirmed no
`.si`-equivalent scratch pattern exists for those types.
240 `.si` sites → 0; 93 net struct allocas saved; stage2.ll
+0.20% (the new lower_struct_new_into helper's source code
slightly outweighs the alloca savings). No behavioral change;
preventive cleanup only.

After v5.6.13 ships, the trajectory rejoins the original arc:
v5.7.0 (Sh.7 + B → 66/66), v5.7.1 (docs polish), v5.8.0
(RE-PANEL).

---

## v5.19.x docket sequence (terseness arc closeout + Docker)

Issued during the v5.13–v5.21 terseness arc closeout. Tracked
here for completeness:

| Release | Docket | Status |
|---|---|---|
| v5.19.0 | Te.3 (brace deprecation + fmt auto-migration) | CLOSED |
| **v5.19.1** | **Dk.1–Dk.7 (Docker images + `mnc init --docker`)** | **CLOSED** |

The v5.19.0 PLAN originally bundled Te.3 + Dk.* into a single
release; mid-execution scope split (commit 6adfee7) moved Dk.*
to a dedicated v5.19.1 patch so the deprecation could ship clean.

### v5.19.1 deferred follow-ups (open carry to v5.20.0+)

Both surfaced from `v5.19.1/DESIGN_AMENDMENT.md` items A2 + A3 —
clean compiler-side fixes that retire Docker-side workarounds:

- **Builder-image diet.** Patch
  `mapanare/self/main.mn::link_with_runtime` to drive `lld`
  directly (current path: `gcc obj rt.a -o exe -no-pie -rdynamic
  -lm -lpthread`). Unblocks shipping `mapanare-builder` with only
  `llvm-18` (no `clang` / `libclang-cpp` — saves ~99 MB),
  targeting **~450 MB** builder image. Out of scope for v5.19.1
  because the prompt forbade compiler edits. Retires the `gcc →
  clang` symlink shim (A2).
- **`MAPANARE_RUNTIME_LIB_PATH` env-var override.** First-class
  compiler support for an explicit runtime-archive path,
  replacing the in-image `mnc` wrapper script that symlinks
  `runtime/native/libmapanare_rt.a` into CWD before exec'ing the
  real binary. Retires A3.

Both items are small, additive, and don't conflict with
v5.20.0's Te.5 (struct ergonomics) — they can ship in parallel
as a v5.20.x patch or alongside Te.5.

---

## v5 closed at v5.47.5

Aggregate panel score: **9.76 / 10**. Decision: **Option A**
(v5 ships clean; v6.0 green-lit). Per-reviewer: Rattler 9.85
PASS, Viper 9.85 PASS, Anaconda 9.75 PASS, Cobra 9.75 PASS,
Coral 9.65 PASS WITH NOTES, Boa 9.65 PASS WITH NOTES, Mamba
9.85 PASS. Spread 0.20 (well below 0.5 follow-up trigger).
Second consecutive Option A under the v5-gate framework;
second consecutive panel above the v5.7.1 / v5.8.0 9.66
ceiling. v5.47.5 covers v5.31.0 → v5.47.0 (17 substantive
releases plus v5.39.1 → v5.39.7 sub-releases) — the longest
single-panel scope in project history.

**v5 series state at panel cut:**

- ✅ **Foundation arc CLOSED** (banner + 3 prebuilt binary
  releases — v5.31.0 Bn.\*, v5.32.0 Nw.\*, v5.33.0 Nu.\*,
  v5.33.1 Hd.\*, v5.33.2 Cd.\*)
- ✅ **Stdlib gap-close arc CLOSED** (date/time, sqlite,
  JSON, HTTP, regex, crypto — v5.34.0 → v5.39.0; Js.4 staged
  closure across v5.39.1 → v5.39.7)
- ✅ **Manifesto arc CLOSED** (`ask`, supervision,
  distributed agents — v5.40.0 Ai.\*, v5.42.0 As.\*, v5.43.0
  Da.\*)
- ✅ **Tensor closeout arc CLOSED** (Ts.1 reshape v5.41.0;
  Ts.2 mutable views + Ts.3 stepped slices v5.45.0)
- ✅ **Package-system runway CLOSED** (v5.44.0 Ps.\*,
  v5.44.1 Ps.11+Ps.12 — installed packages compile as normal
  dependencies)
- ✅ **v5.43.0 lowerer-bug closeout CLOSED at v5.46.0** (Lf.1
  + Lf.2 + Lf.3 — single ~30 LOC fix at
  `mapanare/lower.py:2398-2453` closed three symptoms via
  one root cause)
- ✅ **Pre-panel hygiene cleanup CLOSED at v5.47.0** (Cl.1
  variant-name collision; Cl.4 websocket.mn `str(byte)`
  cleanup; Cl.2 + Cl.3 honest splits to v5.47.1)
- ✅ Mb.\* arc CLOSED (since v5.29.0)
- ✅ Pv.\* arc CLOSED (since v5.32.0/v5.33.0)
- ✅ Js.4.\* arc CLOSED (v5.39.7)
- ✅ Terseness arc CLOSED (since v5.27.0)

**v5 totals:**
- Strict 3-stage fixed-point: **50-release strict streak**
  from v5.7.1 baseline (244,654 lines / 0 diff at v5.47.0
  HEAD)
- Goldens: 95 → 103 across the arc (8 net-new, every one
  falsifiability-locked)
- Stdlib cookbooks: 8 new under `docs/stdlib/` (time, sql,
  json, http, regex, crypto, ai, agent)
- Runtime exports: 30+ new `__mn_*` symbols across
  `mapanare_time.c`, `mapanare_db.c`, `mapanare_io.c`,
  `mapanare_node.c`, `mapanare_runtime.c` extensions

**v6.0 PLAN drafting begins** at `docs/roadmap/v6/PLAN.md`
per `.reviews/v5.47.5/V5_TO_V6_CARRY.md` inputs. The 9-item
v6.0 PLAN input list (borrow checker / multi-level alias
analysis; hard removal of `{}`; STRICT 3-stage fixed-point
gate carve-out; tensor surface unification; distributed-
supervision orchestration; registry-side package signing;
`_specialize_fn` body-walk fix; PRE_PHASE_AUDIT.md mandatory;
convergent-recommendation pattern explicit) is the load-
bearing v6.0 docket. Recommended v6.0 sub-release split
per the v5.43.0 sizing lesson: v6.0.0 (Bc.1.0 inference) /
v6.0.1 (Bc.2.0 enforcement + perf baseline) / v6.0.2
(Bc.3.0 hard `{}` removal + tensor unification).

**v5.47.x patches recommended pre-v6.0:** v5.47.1 (already
named — Cl.2 agent stdlib ergonomic refactor; Cl.3 fs.mn
walk_dir IR codegen); v5.47.2 (proposed — `.reviews/CARRY_FORWARD.md`
refresh, `tests/KNOWN_FAILURES.md` ledger, localized README
refresh, `docs/stdlib/INDEX.md`, manifesto.md As.\*+Da.\*
section). These are docs/process polish, not load-bearing
for v6.0 correctness.

**Cadence-gap closure.** v5.47.5 closes 19 minor versions
late on purpose. Per project memory + v5.28.0 directive:
panels run at the end of an arc, not in the middle.
`check_cadence.py` is informational REMINDER per v5.33.2
Cd.\* exactly to support this shape.

See `.reviews/v5.47.5/{PRE_PANEL_AUDIT.md, V5_DECISION.md,
V5_TO_V6_CARRY.md, V5_RETRO.md, README.md,
<reviewer>/findings.md}` for the full panel docket.
