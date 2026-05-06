# CLAUDE.md

Guidance for Claude Code working in this repository.

## Project Overview

Mapanare is an AI-native compiled language with first-class agents,
signals, streams, and tensors. Compiles to LLVM IR (primary) and C
(fallback via gcc). WebAssembly backend for browser/server targets.
Self-hosted compiler is 38,000+ lines of `.mn` across 10 modules in
`mapanare/self/`. The compiler compiles itself —
`bash scripts/build_from_seed.sh` builds from source with no Python.

**Current version:** see `VERSION` file.

## Current Version & Roadmap

Most recent releases. Full history at
`docs/roadmap/ROADMAP.md` and
`docs/roadmap/v5/v5.X.Y/SESSION_REPORT.md` per release:

- **v5.47.5** (ready, not tagged) — **Cp.\* — end-of-v5 closeout
  panel.** Panel-only release. **Zero compiler edits. Zero
  runtime edits. Zero `mapanare/self/*.mn` source edits.**
  Strict 3-stage fixed point preserved by construction at
  v5.47.0's **244,654 lines / 0 diff** (50-release strict
  streak from v5.7.1 baseline). Goldens **103/103**. Decides
  three things at the structural pause before v6.0: (1) has v5
  delivered? (2) is v6.0 ready to start? (3) what carries
  forward?
  **Aggregate panel score: 9.76 / 10. Decision: Option A.**
  7-reviewer panel (Rattler 9.85 PASS / Viper 9.85 PASS /
  Anaconda 9.75 PASS / Cobra 9.75 PASS / Coral 9.65 PASS WITH
  NOTES / Boa 9.65 PASS WITH NOTES / Mamba 9.85 PASS) reviewed
  v5.31.0 → v5.47.0 (17 substantive releases plus v5.39.1–v5.39.7
  sub-releases). Spread 0.20 (well below 0.5 follow-up trigger).
  **0 HIGH / 6 dedup MEDIUM / 31 LOW** — all MEDIUMs are either
  v6.0 PLAN inputs (PRE_PHASE_AUDIT promotion, tensor surface
  unification, distributed supervision orchestration, registry
  package signing, STRICT carve-out, perf baseline) or v5.47.x
  patch candidates (CARRY_FORWARD.md drift, localized README
  staleness). Second consecutive Option A under the v5-gate
  framework; second consecutive panel above the v5.7.1 / v5.8.0
  9.66 ceiling (+0.04 vs v5.28.0 RE-PANEL's 9.72 across +9
  releases of scope).
  **v6.0 green-lit** conditional on 9 v6.0 PLAN inputs being
  explicit (borrow checker / multi-level alias analysis; hard
  removal of `{}`; STRICT 3-stage fixed-point gate carve-out;
  tensor surface unification; distributed-supervision
  orchestration; registry-side package signing; `_specialize_fn`
  body-walk fix; PRE_PHASE_AUDIT.md mandatory at every v6.x
  release; convergent-recommendation pattern explicit).
  **v5.47.x patches recommended pre-v6.0:** v5.47.1 (already
  named: Cl.2 agent stdlib ergonomic refactor + Cl.3 fs.mn
  walk_dir IR codegen); v5.47.2 (proposed: 5 docs/process
  polish items — CARRY_FORWARD.md refresh, KNOWN_FAILURES.md
  ledger, localized README refresh, docs/stdlib/INDEX.md,
  manifesto.md As.\*+Da.\* section).
  **Cadence-gap acknowledgment.** v5.47.5 closes 19 minor
  versions late on purpose. Per project memory + v5.28.0
  directive: panels run at the end of an arc, not in the
  middle. v5.45.0's original panel slot was deferred so
  v5.45.0 (tensor closeout) + v5.46.0 (lowerer-bug closeout)
  + v5.47.0 (pre-panel hygiene) could close three long-
  standing debts before the panel audited ecosystem readiness
  for v6.0. `check_cadence.py` is informational REMINDER per
  v5.33.2 Cd.\* exactly to support this shape; reviewers did
  not dock for the gap.
  **v5 series state:** Foundation arc CLOSED. Stdlib gap-close
  arc CLOSED. Manifesto arc CLOSED. Tensor closeout arc CLOSED.
  Package-system runway CLOSED. v5.43.0 lowerer-bug closeout
  CLOSED at v5.46.0. Pre-panel hygiene cleanup CLOSED at
  v5.47.0. Mb.\* arc CLOSED (since v5.29.0). Pv.\* arc CLOSED
  (since v5.32.0/v5.33.0). Js.4 arc CLOSED (v5.39.7).
  Terseness arc CLOSED (since v5.27.0).
  Source delta: 8 panel deliverable files
  (`PRE_PANEL_AUDIT.md` + 7 `<reviewer>/findings.md` +
  `V5_DECISION.md` + `V5_TO_V6_CARRY.md` + `V5_RETRO.md` +
  `README.md`); v5 closeout summary paragraph replacing
  v5.31.0–v5.45.0 explicit ledger entries (Cp.6 prune); final
  paragraph appended to `docs/roadmap/v5/CLOSEOUT_ARC.md`
  (Cp.7); CHANGELOG `### Added` entry for Cp.1..Cp.8 panel
  deliverables; SPEC.md header re-sync to v5.47.5 cut with
  closeout-panel sync block; this CLAUDE.md release-notes
  entry; mechanical bump_version.py edits. **v6.0 PLAN
  drafting begins** at `docs/roadmap/v6/PLAN.md` per
  V5_TO_V6_CARRY.md inputs. See
  `.reviews/v5.47.5/{PRE_PANEL_AUDIT.md, V5_DECISION.md,
  V5_TO_V6_CARRY.md, V5_RETRO.md, README.md, <reviewer>/findings.md}`
  and `docs/roadmap/v5/v5.47.5/{PLAN.md, PROMPT.md,
  SESSION_REPORT.md}`.

- **v5.47.0** (ready, not tagged) — **Cl.\* — pre-panel hygiene
  cleanup; v5.47.5 closeout panel runway begins.** Drains every
  closeable LOW-tier carry before the v5.47.5 closeout panel sees
  the docket. Mirrors the v5.28.0 hygiene-before-panel precedent
  (the +0.31 panel recovery there came from H.\* hygiene closures
  landing ahead of panel cut). **Cl.1 (Lf.4) — variant-name
  collision** closed across both Python bootstrap
  (`mapanare/semantic.py` `_variant_alternatives` multimap +
  `_check_let` annotation-as-`_expected_type` context;
  `_check_call` and Identifier-resolution disambiguation when the
  name has multiple alternatives) AND self-host stage1
  (`mapanare/self/semantic.mn` `expected_type` field on `SemState`
  + `scope_has_variant_for_enum` post-inference helper walking
  `Scope.symbols` which appends rather than replaces;
  `mapanare/self/lower.mn` `expected_enum_name` field on
  `LowerState` + `enum_has_variant` lookup; `lower_let` sets the
  hint when type_ann is TK_ENUM; `lower_call_by_name` enum-variant
  branch prefers the hint over `enum_name_for_variant`'s
  first-match result when the hinted enum has the variant). Phase
  0 audit verified self-host stage1 had the bug too (different
  from v5.46.0 where self-host already had Eu.2 fix); Cl.5 mirror
  is non-trivial (~80 LOC across 4 files). **Cl.4 —
  `stdlib/net/websocket.mn` `str(byte)` decimal-stringification
  cleanup** — 11 sites in `read_frame` / `build_send_frame` /
  chunked-send replaced with `__mn_str_chr` (v5.43.0 Da.0 C
  runtime export). **Two Phase-0-driven scope splits
  (load-bearing for honest release framing):** (1) **Cl.2 —
  agent stdlib ergonomic refactor SPLIT to v5.47.1** — the
  v5.43.0 distributed-agent flat-tuple shape across
  `stdlib/agent/{url,remote,node,supervision}.mn` is structurally
  unblocked by Cl.1 but the refactor is ~400 LOC across
  public-API surfaces + ~50 internal callers + test updates;
  warrants dedicated focus; (2) **Cl.3 — fs.mn walk_dir IR
  codegen SPLIT to v5.47.1** — Phase 0 verified the v5.40.0 carry
  is still open (clang rejects `extractvalue ptr ... 0` then
  `zext ptr to i64`); receiver-side wrong-shape Result aggregate
  bug, different fix-site from v5.46.0's constructor-side
  wrap-shape default. **STRICT 3-stage fixed point preserved at
  244,654 lines / 0 diff** (50-release strict streak from v5.7.1;
  +889 lines vs v5.46.0). Goldens **103/103** (102 + new
  `103_variant_name_collision.mn`). Falsifiability locked per
  layer in `tests/llvm/test_lowerer_fixes.py` (8/8 GREEN;
  +3 new Lf.4 cases). Source delta: ~80 LOC compiler + ~30 LOC
  stdlib + ~85 LOC golden + ~80 LOC test extension + closeout
  artifacts. Aggregate state entering v5.47.5: **0 HIGH** /
  **2 MEDIUM** (Cl.2 + Cl.3 splits to v5.47.1; macOS
  notarization carry from v5.33.0 Nu.2) / ~6 LOW. **Tensor
  closeout arc CLOSED at v5.45.0. Manifesto arc CLOSED at
  v5.43.0. Package-system runway CLOSED at v5.44.0. v5.43.0
  lowerer-bug closeout CLOSED at v5.46.0. Pre-panel hygiene
  cleanup CLOSED at v5.47.0** (with two scope splits to v5.47.1).
  v5.47.5 panel reviews a clean docket. See
  `docs/roadmap/v5/v5.47.0/{PLAN.md, PROMPT.md, PRE_PHASE_AUDIT.md,
  SESSION_REPORT.md}`.

- **v5.46.0** (ready, not tagged) — **Lf.\* — v5.43.0 lowerer-bug
  closeout; ergonomic `Result<T, E>` API unblocked.** Closes the
  three v5.x lowerer bugs (Lf.1 + Lf.2 + Lf.3) that v5.43.0
  SESSION_REPORT documented and worked around with the flat
  `(ok: Bool, value, err_kind: Int, err_msg: String)` tuple.
  After v5.46.0, the v5.43.0 distributed-agent APIs *can* be
  refactored back to ergonomic `Result<T, NetworkError>` shape
  — that ergonomic refactor is v5.46.x scope, not v5.46.0.
  v5.46.0 ships the codegen fixes that unblock the refactor.
  **Phase 0 audit (load-bearing finding):** all three bugs
  share **one** root cause and that root cause exists **only
  in the Python bootstrap lowerer** (`mapanare/lower.py`). The
  self-host mirror (`mapanare/self/lower.mn`) **already had
  the fix** — v5.26.1 Eu.2 introduced
  `current_fn.return_type` consultation on the self-host side
  at lines 2259-2306; the same fix was never backported to
  the Python bootstrap. Self-host `mapanare/self/mnc-stage1`
  produced correct output for all three repros at v5.45.0
  HEAD (Lf.1 `kind=3` ✓, Lf.2 `kind=3` ✓, Lf.3 `got NoKey` ✓);
  Python bootstrap printed wrong values, failed at IR
  validation, or silently no-fired the inner match. v5.46.0
  backports the self-host's logic into the Python `Ok`/`Err`
  constructor lowering branches at
  `mapanare/lower.py:2398-2453` — **single ~30-LOC edit
  closes all three bugs**.
  **Strict 3-stage fixed point preserved by construction at
  v5.45.0's 243,749 lines / 0 diff** (49-release strict
  streak from the v5.7.1 baseline; **zero
  `mapanare/self/*.mn` source touches** because the self-host
  already had the fix). Goldens **102/102** (99 existing + 3
  new: `100_result_complex_destructure`,
  `101_match_rewrap_propagation`, `102_nested_15arm_match`).
  Plus `tests/llvm/test_lowerer_fixes.py` (5 cases — Lf.1 +
  Lf.2 + Lf.3 + 2 trivial-Ok regression cases) with
  falsifiability protocol documented in module docstring.
  **PROMPT/PLAN deviations surfaced at Phase 0** (load-bearing,
  documented in `PRE_PHASE_AUDIT.md`): (1) Lf.5 self-host
  mirror is a **no-op gate** — PLAN budgeted ~4h, actual
  work is zero `.mn` edits; STRICT preserved trivially.
  (2) **Lf.1 + Lf.2 + Lf.3 share one root cause** — PLAN
  hypothesized Lf.1 + Lf.2 may share with Lf.3 independent;
  IR diagnosis confirms one common cause (the Python
  Ok/Err constructor wrap-shape default). One fix, three
  regressions. (3) **Lf.4 splits to v5.46.x** — Phase 0 LOC
  measurement put the variant-name disambiguation fix at
  ≥50 LOC (multimap-of-variants infrastructure across
  `mapanare/semantic.py` + `mapanare/lower.py`); exceeds
  PLAN's ≤30 LOC bundle threshold. (4) Pre-existing test
  bookkeeping: `tests/llvm/test_llvm_link_all.py::test_golden_corpus_count`
  asserted 95 (pre-v5.34.0 number); v5.46.0 bumps to 102
  and extends the glob from `[0-9][0-9]_*.mn` to also match
  3-digit prefixes. (5) Pre-existing failures —
  `test_run_hello` (gcc.exe env issue),
  `test_reshape_size_mismatch_aborts`,
  `test_link_and_run[98_*/99_*]` — all fail at v5.45.0
  baseline pre-v5.46.0 changes; not regressions from this
  release.
  **Lf.0 — Phase 0 audit.** Reconstructed all 4 v5.43.0
  `/tmp/diag_*.mn` repros at v5.45.0 HEAD; captured IR-level
  diff per bug; localized fix sites; verified self-host
  produces correct output for all three; decided Lf.4
  bundle/split. Audited `mapanare/self/*.mn` for affected
  patterns (no `Err`/`Ok` returns in self-host, no
  Result<NonTrivialOk, NonTrivialErr> usage, max match arms
  in self-host = 12 in `lower.mn` chained_cmp + 184/241 in
  `mnc_all.mn` chained_cmp tables but none nested under
  Err destructure with mismatched Result wrap shape). Output:
  `docs/roadmap/v5/v5.46.0/PRE_PHASE_AUDIT.md`.
  **Lf.1 + Lf.2 + Lf.3 — single fix at `mapanare/lower.py`.**
  In the `Ok` and `Err` constructor lowering branches, when
  the enclosing function returns `Result<T, E>`, default the
  unfilled side of the wrapper to `T` (for Err's Ok-default)
  / `E` (for Ok's Err-default) instead of the legacy `Int` /
  `String` defaults. Mirrors the v5.26.1 Eu.2 fix that the
  self-host already had. Pre-fix the small 32-byte `Result<Int,
  E>` wrapper was stored into the function's larger `__sret__`
  slot; bytes past 32 stayed zero; consumer reads NetworkError
  at the big-layout offset (e.g. 72 for `Result<NodeHandle,
  NetworkError>`) and got tag=0 = BadUrl regardless of which
  variant was actually constructed (Lf.1); rewrap chains
  inherited the wrong shape and IR validation failed (Lf.2);
  nested 15-arm match fired none of the arms because the
  corrupt tag matched no case (Lf.3 — the 15-arm threshold
  reported at v5.43.0 was a red herring). Falsifiability
  locked per fix in `tests/llvm/test_lowerer_fixes.py`
  module docstring + per-test docstring; revert the fix and
  the corresponding pytest case fails with the recorded
  signature.
  **Lf.5 — self-host mirror.** No-op gate. Self-host already
  has the v5.26.1 Eu.2 fix; STRICT 3-stage fixed point
  preserved by construction.
  **Lf.6 — broader sweep.** Audited 237 non-trivial-Ok
  Result-returning functions across `stdlib/`, `examples/`,
  `tests/`. The v5.43.0 `stdlib/agent/` distributed-agent
  surface uses the flat-tuple workaround (per the v5.43.0
  SESSION_REPORT) — the only Result-returning function that
  could have been silently corrupting is
  `stdlib/agent/remote_proto.mn::validate_key`
  (`Result<String, NetworkError>`), but its sole caller is
  internal and exercised through pytest; verified post-fix.
  Existing `tests/stdlib/` regression suite (1043 cases) all
  GREEN — most stdlib Result-returning callers don't trigger
  the bug because their Ok/Err sizes match the inferred
  defaults (e.g., `Result<String, JsonError>` has 16-byte
  ok/err so the small-shape default coincidentally matched).
  No production caller relied on the wrong output.
  **Source delta:** ~30 LOC `mapanare/lower.py` (Ok + Err
  branches) + ~50 LOC `tests/golden/100_*.mn` + ~70 LOC
  `tests/golden/101_*.mn` + ~80 LOC `tests/golden/102_*.mn`
  + ~190 LOC `tests/llvm/test_lowerer_fixes.py` + ~5 LOC
  `tests/llvm/test_llvm_link_all.py` (count + glob) + ~370
  LOC PRE_PHASE_AUDIT.md + SESSION_REPORT.md + ~120 LOC
  CHANGELOG `### Fixed` (3 entries with potentially-
  behavior-changing annotations) + ~25 LOC SPEC sync + this
  CLAUDE.md release-notes entry + mechanical
  bump_version.py edits.
  Aggregate state entering v5.47.0 (closeout panel):
  **0 HIGH** (Lf.\* arc CLOSED) / **2 MEDIUM** (macOS
  notarization carry from v5.33.0 Nu.2; Ai.1
  `_specialize_fn` body-walk fix gating Ai.1+Ai.2 keyword
  sugar, carry from v5.40.0) / ~7 LOW (Lf.4 variant-name
  collision split to v5.46.x; ergonomic refactor of
  v5.43.0 distributed-agent APIs from flat tuple to
  `Result<T, NetworkError>` v5.46.x; fs.mn `walk_dir` IR
  codegen carry from v5.40.0; websocket.mn `str(byte)`
  decimal-stringification carry from v5.43.0; carries
  from v5.45.0). **Tensor closeout arc CLOSED at v5.45.0.
  Manifesto arc CLOSED at v5.43.0. Package-system runway
  CLOSED at v5.44.0. v5.43.0 lowerer-bug closeout CLOSED at
  v5.46.0.** v5.47.0 closeout panel green-lights v6.0 (or
  doesn't). See
  `docs/roadmap/v5/v5.46.0/{PLAN.md, PROMPT.md,
  PRE_PHASE_AUDIT.md, SESSION_REPORT.md}`.

- **v5.31.0 → v5.45.0 — closeout summary** (pruned at v5.47.5
  Cp.6; full release notes preserved in
  `docs/roadmap/v5/<release>/SESSION_REPORT.md` per release).
  Six structural sub-arcs shipped across these 15 releases:
  **Foundation arc** (v5.31.0 Bn.\* banner hotfix; v5.32.0 Nw.\*
  Windows native `mnc.exe`; v5.33.0 Nu.\* Linux x86_64 + macOS
  arm64 native `mnc`; v5.33.1 Hd.\* SPEC header re-sync;
  v5.33.2 Cd.\* cadence gate demoted to informational); **Stdlib
  gap-close arc** (v5.34.0 Dt.\* date/time — first-class types
  + 6 new C exports; v5.35.0 Sq.\* first-class sqlite3 driver +
  Tn.1 closure via Sq.0; v5.36.0 Js.\* JSON RFC 8259 strictness
  + typed serde + 2 emitter-bug fixes; v5.37.0 Ht.\* HTTP App /
  router / middleware / streaming encoders; v5.38.0 Re.\* regex
  Regex-first API + Captures + named groups; v5.39.0 Cr.\*
  crypto baseline — hashing additions + streaming digest +
  HMAC-SHA512 + Cr.0 emitter shortcut bypass fix); **Js.4
  staged closure** (v5.39.1 → v5.39.7 — typed-serde round-trip
  closure across all TypeKind branches in 7 sub-releases);
  **Manifesto arc** (v5.40.0 Ai.\* `ask` runtime adapter;
  v5.41.0 Ts.1 tensor.reshape on LLVM; v5.42.0 As.\* agent
  supervision trees + 4 new C runtime exports; v5.43.0 Da.\*
  distributed agents v0 — TCP/TLS wire format v1, HMAC-SHA256
  signed, 100MB DoS guard, 1000-iteration network fuzz);
  **Tensor closeout** (v5.45.0 Ts.2 + Ts.3 — mutable views,
  stepped slices, `mapanare_tensor_t` 40→64 byte append-only
  extension); **Package-system runway** (v5.44.0 Ps.\*
  package-aware imports + lockfile/install/publish wired into
  resolver; v5.44.1 Ps.11+Ps.12 scripts parity + gitignore
  template).
  Every release in the arc shipped with PRE_PHASE_AUDIT.md
  catching PROMPT/PLAN-vs-HEAD-state mismatches before
  implementation began (10+ load-bearing surfaces across the
  arc). STRICT 3-stage fixed-point preserved at every release
  (50-release strict streak from the v5.7.1 baseline at
  v5.47.0 HEAD: 244,654 lines / 0 diff). Goldens trajectory
  95 → 96 (v5.41.0) → 99 (v5.45.0) → 102 (v5.46.0) → 103
  (v5.47.0). Six new stdlib cookbooks shipped under
  `docs/stdlib/` (time, sql, json, http, regex, crypto, ai,
  agent — 8 total). For per-release details see
  `docs/roadmap/v5/v5.31.0/SESSION_REPORT.md` through
  `docs/roadmap/v5/v5.45.0/SESSION_REPORT.md` and CHANGELOG
  entries `## [5.31.0]` through `## [5.45.0]`.

> Older release notes elided. See `docs/roadmap/ROADMAP.md` for the
> full ledger and `docs/roadmap/v5/v5.X.Y/SESSION_REPORT.md` for any
> specific release.

### Planned / in-progress

- **v5.12.0** — **Mc.6 / Wk.* — Windows SDK split.** Default
  Windows installs move to `mapanare-${V}-win-x64-sdk.zip`, which
  bundles one curated LLVM-MinGW/UCRT x86_64 SDK under `sdk/` so
  clean-machine `mnc run` / `mnc build` keep working. The opt-in
  `mapanare-${V}-win-x64-minimal.zip` is app-only and requires a
  user/system compiler. `MAPANARE_NO_BUNDLED_TOOLCHAIN=1` and legacy
  `MAPANARE_NO_BUNDLED_LLVM=1` select minimal. `toolchain/` must not
  appear in v5.12.0 Windows release ZIPs. See
  `docs/roadmap/v5/v5.12.0/WINDOWS_TOOLCHAIN_AUDIT.md`.

**Terseness arc — v5.13–v5.21 (shipped).** All terseness arc
releases (v5.13.0 → v5.21.0, plus the Sh.\* self-host rewrite at
v5.17.0 → v5.17.2) have shipped. See per-release SESSION_REPORTs
under `docs/roadmap/v5/v5.13.0/` through `docs/roadmap/v5/v5.21.0/`
for details, or `CHANGELOG.md` for summaries. The terseness thesis
is now visible in real code: cumulative source shrink of −13.8%
across `mapanare/self/` from v5.13.0 baseline.

- **v5.19.0** — **Te.3 + Dk.* — closeout.** Soft-deprecate
  `{}` (still parses, emits warning); hard removal scheduled
  for v6.0. Ship `mapanare/builder` + `mapanare/runtime`
  Docker images. See `docs/roadmap/v5/v5.19.0/PLAN.md`.
- **v6.0** — Borrow checker / multi-level alias analysis. Hard
  removal of `{}` (Te.3 from v5.19.0 was soft deprecation only).
  Closes Rt.04 (multi-level drop-glue alias analysis, rescoped
  v5.6.6 — struct→list→string depth-2). The only remaining
  v5.6.x v6.0 carry now that v5.6.12 closed Lk.1 at the
  source via destination passing.

See `docs/roadmap/v5/CLOSEOUT_ARC.md` and
`docs/roadmap/v5/PARITY_GAPS.md`.

## Pre-Push Validation (MANDATORY)

Run the full validation suite before any commit/push. Mirrors CI.
Writes results to `error.log`.

```powershell
.\dev.ps1                  # Full validate: black + ruff + mypy + gcc + pytest + WAT
.\dev.ps1 validate -Watch  # Validate then watch
.\dev.ps1 test             # pytest only
.\dev.ps1 lint             # Linters only
.\dev.ps1 fmt              # Auto-format
.\dev.ps1 e2e              # End-to-end tests
.\dev.ps1 bench            # Benchmarks
```

The validate step includes **WAT emission** for `examples/wasm/*.mn`
— catches WASM CI failures locally. `pytest` alone is NOT sufficient.

Quick partial checks:

```bash
python -m mapanare emit-wasm examples/wasm/hello.mn -o /dev/null
black --check . && ruff check . && mypy mapanare/ runtime/
pytest tests/semantic/test_types.py -v
pytest tests/parser/ -v
```

## Commands

```bash
make install          # pip install -e ".[dev]"
make build            # pip install -e .
make test             # pytest tests/ -v  (add -n auto for parallel)
make lint             # ruff + black + mypy
make fmt              # black + ruff --fix
make benchmark        # python -m benchmarks.run_all
make clean            # Remove caches + egg-info
```

### Core workflows

```bash
# Golden test harness (WSL for stage1)
python scripts/test_native.py --stage1 mapanare/self/mnc-stage1

# Full rebuild cycle (WSL)
bash scripts/rebuild.sh              # concat + build + goldens

# Self-hosted fixed-point (WSL)
python scripts/build_stage1.py
bash scripts/verify_fixed_point.sh --keep
```

### Debug tooling

Full command reference: **`docs/guides/tools_reference.md`**.

- `python scripts/ir_doctor.py <cmd>` — per-function IR diagnostics,
  baselines, valgrind mapping, stage2 pipeline
- `python scripts/mir_trace.py <file.mn> <fn>` — trace type inference
  in the Python lowerer
- `culebra <cmd>` — 49+ templates for IR + C diagnostics (Rust binary,
  WSL)

## Testing the Native Compiler

Golden corpus at `tests/golden/*.mn` (66 programs). Reference IR at
`tests/golden/*.ref.ll`.

Workflow:
1. Edit `mapanare/self/*.mn` or `mapanare/emit_llvm_text.py`
2. `python scripts/build_stage1.py`
3. `python scripts/test_native.py --stage1 mapanare/self/mnc-stage1 -v`
4. Harness compares mnc-stage1 output against Python bootstrap —
   shows which functions are missing or different.

Every run updates `tests/golden/BENCHMARKS.md`. Commit to track
regressions.

**Current baseline (v5.7.1):** **66/66 — preserved.** Sh.7
(closure-typed parameters) and B (or-pattern + identifier `None`
resolution) both closed in v5.7.0; v5.7.1 is a docs/polish release
with no compiler edits. The closure arc is closed; every test in
the corpus that defines "self-hosting" now passes through
`mnc-stage1`.

## Code Style

- **Black** (line length 100), **Ruff** (E, F, W, I), **MyPy** strict
- Target Python 3.11+ (bootstrap compiler)
- Dataclasses for AST nodes; type hints throughout

## Compiler Pipeline

```
.mn source
  → Lark LALR parser → AST (dataclasses)
  → Semantic checker
  → MIR lowering
  → MIR optimizer (O0–O3)
  → Emitter:
      ├→ emit_llvm_text.py  → LLVM IR (text)
      ├→ emit_c.py          → C source
      └→ emit_wasm.py       → WebAssembly (WAT/WASM)
```

Key modules in `mapanare/`:

| File | Role |
|---|---|
| `cli.py` | Entry point — command dispatch |
| `parser.py` | Lark transformer: parse tree → AST |
| `ast_nodes.py` | AST node definitions |
| `semantic.py` | Two-pass type checker + scope resolver |
| `mir.py` / `mir_builder.py` | MIR data + builder |
| `lower.py` | AST → MIR lowering |
| `mir_opt.py` | MIR optimizer passes |
| `emit_llvm_text.py` | LLVM IR generation |
| `emit_c.py` | C source generation |
| `emit_wasm.py` | WebAssembly (WAT) generation |
| `wasm_linker.py` | wasm-ld multi-module linking |
| `types.py` | **Single source of truth** for type system |
| `mapanare.lark` | LALR grammar, 13-level precedence |
| `tracing.py` | OpenTelemetry-compatible tracing |
| `diagnostics.py` | Rust-style structured error output |

## Runtime System

**Python runtime** (`runtime/`): `agent.py`, `signal.py`, `stream.py`,
`result.py`, `deploy.py`. **Legacy — being replaced by native .mn
stdlib.**

**Native C runtime** (`runtime/native/`): arena memory (no GC),
lock-free SPSC ring buffers, thread pool with work-stealing, coop
scheduler (mobile), agent lifecycle, TCP sockets, TLS (OpenSSL via
dlopen), file I/O, event loop (epoll/select), string interning,
memory profiling. Used by the LLVM backend.

## LLVM Backend Status

**Working:** functions, structs, enums, pattern matching, control
flow, type inference, generics, Result/Option, print, builtins, lists,
maps (Robin Hood), agents, signals (full reactivity), streams,
closures (env struct capture), traits, module imports, pipes,
multi-agent pipe definitions, string methods, GPU kernel dispatch.

Tensor surface complete as of v5.45.0 (Ts.\* — closeout arc CLOSED):
reshape (aliasing), view (aliasing), stepped slice (copy). Strided /
non-contiguous tensors reserved for v6.0+ (would force ABI change on
`mapanare_tensor_t` for transpose / permute / reverse step).

New LLVM features target `emit_llvm_text.py` (sole LLVM emitter).

## Type System (`mapanare/types.py`)

Single source of truth:
- `TypeKind` enum (25 kinds: INT, FLOAT, BOOL, STRING, LIST, MAP,
  OPTION, RESULT, SIGNAL, STREAM, AGENT, TENSOR, FN, etc.)
- `BUILTIN_FUNCTIONS`: print, println (deprecated), len, str, int,
  float, Some, Ok, Err, signal, stream
- `BUILTIN_CALL_MAP`: Mapanare → Python name mapping for emitters
- `PYTHON_TYPE_MAP`: Type → Python type mapping

## Self-Hosted Compiler (`mapanare/self/`)

10 modules, ~14,000 lines of Mapanare. Mirrors the Python bootstrap:

| Module | ~LOC | Role |
|---|---:|---|
| `ast.mn` | 781 | AST node definitions |
| `lexer.mn` | 575 | Tokenizer |
| `parser.mn` | 2,249 | Recursive descent parser |
| `semantic.mn` | 1,729 | Type checker + scope resolver |
| `mir.mn` | 791 | MIR data structures |
| `lower_state.mn` | 587 | Lowerer state |
| `lower.mn` | 3,602 | AST → MIR lowering |
| `emit_llvm_ir.mn` | 258 | LLVM type constants + IR builders |
| `emit_llvm.mn` | 3,206 | MIR → LLVM IR emitter |
| `main.mn` | 537 | Compiler driver |

**Patterns:** constructor functions (`let r: T = first_field; return
r`), state-threading, no struct literal syntax in grammar yet.

**Fixed-point:** NEAR (stage2.ll == stage3.ll except VERSION
placeholder). Strict hit at v4.134.0; currently NEAR per v5.3.2.

## Key Conventions

- Grammar: `mapanare/mapanare.lark` (bootstrap copy at `bootstrap/`)
- Emitters detect used features (agents/signals/streams) and import
  only as needed
- Builtins dispatched via `BUILTIN_CALL_MAP` in both emitters
- Self-hosted sources: `mapanare/self/*.mn`
- Language spec: `docs/SPEC.md` | Manifesto: `docs/manifesto.md` |
  RFCs: `docs/rfcs/`
- Roadmap: `docs/roadmap/ROADMAP.md` | Era READMEs:
  `docs/roadmap/v0/` → `docs/roadmap/v5/`
- Version: `VERSION` file
- Bootstrap frozen at v0.6.0 in `bootstrap/`

## Native-First Philosophy (v0.8.0+)

- **Stdlib in .mn:** new stdlib modules are `.mn`, compiled via LLVM.
  No more Python `.py` stdlib files.
- **C runtime as foundation:** OS primitives (sockets, TLS, file I/O)
  in C. Everything above (HTTP, JSON, routing) in Mapanare.
- **Test on LLVM:** every test runs on the LLVM backend.
- **Python entrypoint is bootstrap-only on release installs (v5.32.0+).**
  Windows SDK ZIPs ship a real native `mnc.exe` (built from
  `mapanare/self/` via the stage1 → stage2 self-compile cycle).
  **v5.33.0 extends this to Linux x86_64 and macOS arm64 release
  tarballs** — both ship `dist/mapanare/mnc` (native ELF / Mach-O)
  alongside the existing PyInstaller `mapanare` binary. The native
  `mnc` is invoked directly; no Python interpreter starts on
  `mnc --version`, `mnc run`, or `mnc build`. Linux aarch64 + macOS
  x86_64 tarballs are deferred to v5.34.0+ (no native runner /
  cross-compile infrastructure yet). The Python `mapanare`/`mnc`
  console-script remains for clean clones, pip-installs without
  the SDK, and the `bash scripts/build_from_seed.sh` bootstrap
  path. `mapanare/__main__.py` detects a sibling `bin/mnc[.exe]`
  and `os.execv`s to it; `MAPANARE_FORCE_PYTHON=1` opts out for
  dev/debug.

## GPU / WASM / Mobile (v2.0.0)

- **GPU** — CUDA + Vulkan via dlopen; `@gpu`/`@cuda`/`@vulkan`
  annotations; PTX/SPIR-V codegen; `stdlib/gpu/`.
- **WASM** — `mapanare/emit_wasm.py` → WAT, `wasm_linker.py` for
  wasm-ld. Targets: `wasm32-unknown-unknown`, `wasm32-wasi`.
- **Mobile** — `aarch64-apple-ios`, `aarch64-linux-android`,
  `x86_64-linux-android`. Coop scheduler + smaller defaults (4 KB
  arenas, 256-slot rings, 4 K string intern cap).

## Ecosystem Packages

- **Dato** (`github.com/Mapanare-Research/dato`) — DataFrame package
  (pandas+numpy replacement), in .mn
- `net/crawl`, `security/scan`, `security/fuzz` — agents-based
- AI/LLM drivers: `stdlib/ai/` (LLM, embeddings, RAG)

## CI

GitHub Actions on push/PR to `dev`:
- **ci** — black → ruff → mypy → pytest. Matrix: Python 3.11/3.12
- **native** — C runtime: gcc, ASan, TSan
- **wasm** — WAT emit → wat2wasm → wasmtime WASI examples
- **android** — NDK cross-compile: ARM64 + x86_64 `.o` + ELF verify

5,400+ tests across the full pipeline.

## Skills (slash commands)

| Skill | Description |
|---|---|
| `/golden` | 15/15 golden suite through mnc-stage1 + llvm-as |
| `/stage2` | Compile self-hosted modules + validate stage2 IR |
| `/rebuild` | concat + build mnc-stage1 + run goldens |
| `/ir-audit` | LLVM IR pathology audit with baselines |
| `/valgrind-map` | Valgrind + auto-map offsets to struct fields |
| `/bump-version` | Bump VERSION, README, CHANGELOG, localized docs |
| `/code-review` | 7-reviewer panel review |
| `/create-pr` | PR title + description from commits |
| `/simplify` | Review + fix changed code |
| `/autoresearch` | Autonomous experiment loop |
| `/culebra-scan` | Culebra v2.4.0 — 49+ templates (ABI / IR / Binary / Bootstrap / C). Workflow guide: `docs/guides/culebra.md` |

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **Mapanare** (32756 symbols, 68346 relationships, 300 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## When Debugging

1. `gitnexus_query({query: "<error or symptom>"})` — find execution flows related to the issue
2. `gitnexus_context({name: "<suspect function>"})` — see all callers, callees, and process participation
3. `READ gitnexus://repo/Mapanare/process/{processName}` — trace the full execution flow step by step
4. For regressions: `gitnexus_detect_changes({scope: "compare", base_ref: "main"})` — see what your branch changed

## When Refactoring

- **Renaming**: MUST use `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` first. Review the preview — graph edits are safe, text_search edits need manual review. Then run with `dry_run: false`.
- **Extracting/Splitting**: MUST run `gitnexus_context({name: "target"})` to see all incoming/outgoing refs, then `gitnexus_impact({target: "target", direction: "upstream"})` to find all external callers before moving code.
- After any refactor: run `gitnexus_detect_changes({scope: "all"})` to verify only expected files changed.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Tools Quick Reference

| Tool | When to use | Command |
|------|-------------|---------|
| `query` | Find code by concept | `gitnexus_query({query: "auth validation"})` |
| `context` | 360-degree view of one symbol | `gitnexus_context({name: "validateUser"})` |
| `impact` | Blast radius before editing | `gitnexus_impact({target: "X", direction: "upstream"})` |
| `detect_changes` | Pre-commit scope check | `gitnexus_detect_changes({scope: "staged"})` |
| `rename` | Safe multi-file rename | `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` |
| `cypher` | Custom graph queries | `gitnexus_cypher({query: "MATCH ..."})` |

## Impact Risk Levels

| Depth | Meaning | Action |
|-------|---------|--------|
| d=1 | WILL BREAK — direct callers/importers | MUST update these |
| d=2 | LIKELY AFFECTED — indirect deps | Should test |
| d=3 | MAY NEED TESTING — transitive | Test if critical path |

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/Mapanare/context` | Codebase overview, check index freshness |
| `gitnexus://repo/Mapanare/clusters` | All functional areas |
| `gitnexus://repo/Mapanare/processes` | All execution flows |
| `gitnexus://repo/Mapanare/process/{name}` | Step-by-step execution trace |

## Self-Check Before Finishing

Before completing any code modification task, verify:
1. `gitnexus_impact` was run for all modified symbols
2. No HIGH/CRITICAL risk warnings were ignored
3. `gitnexus_detect_changes()` confirms changes match expected scope
4. All d=1 (WILL BREAK) dependents were updated

## Keeping the Index Fresh

After committing code changes, the GitNexus index becomes stale. Re-run analyze to update it:

```bash
npx gitnexus analyze
```

If the index previously included embeddings, preserve them by adding `--embeddings`:

```bash
npx gitnexus analyze --embeddings
```

To check whether embeddings exist, inspect `.gitnexus/meta.json` — the `stats.embeddings` field shows the count (0 means no embeddings). **Running analyze without `--embeddings` will delete any previously generated embeddings.**

> Claude Code users: A PostToolUse hook handles this automatically after `git commit` and `git merge`.

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
