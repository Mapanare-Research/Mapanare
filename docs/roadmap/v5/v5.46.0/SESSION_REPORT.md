# v5.46.0 — SESSION REPORT

**Status:** ready, not tagged.
**Headline:** Lf.\* — v5.43.0 lowerer-bug closeout; ergonomic
`Result<T, E>` API unblocked.
**Strict 3-stage fixed point:** preserved by construction at
v5.45.0's 243,749 lines / 0 diff (49-release strict streak from
v5.7.1; **zero `mapanare/self/*.mn` source touches**).
**Goldens:** 102/102 (99 existing + 3 new for Lf.\*).

---

## Outcome

v5.46.0 closes Lf.1, Lf.2, Lf.3 — the three v5.x lowerer bugs
that the v5.43.0 SESSION_REPORT documented and worked around with
the flat `(ok: Bool, value, err_kind: Int, err_msg: String)`
tuple shape. After v5.46.0, the v5.43.0 distributed-agent surface
in `stdlib/agent/` *can* be refactored back to ergonomic
`Result<T, NetworkError>` shape — that ergonomic refactor is
v5.46.x scope, not v5.46.0. v5.46.0 ships the codegen fixes that
unblock the refactor.

**Lf.4 (variant-name collision)** was decided as a Phase 0 split
to v5.46.x per LOC measurement (≥50 LOC fix exceeds PLAN's
≤30 LOC bundle threshold). The Lf.4 fix needs multimap-of-
variants infrastructure across `mapanare/semantic.py` +
`mapanare/lower.py`; structurally separate work.

---

## Phase 0 — load-bearing finding

**Phase 0 audit re-diagnosis turned the release scope upside
down.** The PLAN budgeted ~12-16h across Phases 1+2+3+4 (Lf.1
fix + Lf.2 fix + Lf.3 fix + self-host mirror); Phase 0 IR-level
diagnosis showed:

1. **All three bugs share one root cause** — the Python
   bootstrap lowerer's `Ok`/`Err` constructor wrap-shape
   default in `mapanare/lower.py:2398-2429`. When the enclosing
   function returns `Result<T, E>` with non-trivial `T`, the
   `Err(...)` literal lowered with `Result<Int, E>` shape
   (32 bytes) and was stored into the function's `__sret__`
   slot sized for the real `Result<T, E>` (e.g. 88 bytes for
   `Result<NodeHandle, NetworkError>`). Trailing bytes stayed
   zero; consumer reads NetworkError at the big-layout offset
   and got tag=0 = BadUrl regardless of which variant was
   constructed.
2. **The bug exists ONLY in the Python bootstrap.** The self-
   host mirror (`mapanare/self/lower.mn:2259-2306`) **already
   had the v5.26.1 Eu.2 fix** consulting `current_fn.return_type`
   — Eu.2 was applied to the self-host but never backported to
   Python. `mapanare/self/mnc-stage1` produces correct output
   for all three repros at v5.45.0 HEAD:
   ```
   $ stage1 emit-llvm /tmp/diag_lf1_real.mn ...; ./exe
   kind=3                # ✓ correct (Python prints kind=1)
   $ stage1 emit-llvm /tmp/diag_lf2_complex.mn ...; ./exe
   kind=3                # ✓ correct (Python rejects at IR validation)
   $ stage1 emit-llvm /tmp/diag_lf3_min.mn ...; ./exe
   got NoKey             # ✓ correct (Python silently no-fires)
   ```
3. **Lf.5 self-host mirror is a no-op gate.** PLAN budgeted
   ~4h; actual work is zero `.mn` edits. STRICT 3-stage fixed
   point preserved trivially.

The release collapsed from 4 distinct fix phases to **one
~30-LOC edit** in `mapanare/lower.py` plus test corpus.

PRE_PHASE_AUDIT.md captures the IR-level diagnoses, the self-
host audit (no Result<NonTrivialOk, NonTrivialErr> usage in
`mapanare/self/`; 5 large matches but none nested under Err
destructure with mismatched Result wrap shape), and the Lf.4
bundle/split decision rationale.

---

## Phase 1+2+3 — single fix

### `mapanare/lower.py:2398-2453` (Ok + Err branches)

Ok branch: when the enclosing fn returns `Result<T, E>`, default
Err side to `E` instead of `String`.

Err branch: when the enclosing fn returns `Result<T, E>`, default
Ok side to `T` instead of `Int`.

Mirrors the self-host's existing v5.26.1 Eu.2 logic. Pre-fix
diagnostic recorded in PRE_PHASE_AUDIT.md:

```llvm
; pre-fix IR for `da Err(NoKey("..."))` in fn returning Result<NodeHandle, NetworkError>:
%we.21 = insertvalue {i1, {i64, {i64, ptr}}} undef, i1 0, 0
%we.22 = insertvalue {i1, {i64, {i64, ptr}}} %we.21, {i64, ptr} %l.20, 1, 1
store {i1, {i64, {i64, ptr}}} %we.22, ptr %t7.a.23      ; SMALL 32-byte shape
%l.24 = load {i1, {i64, {i64, ptr}}}, ptr %t7.a.23
store {i1, {{ptr, i64}, {i64, ptr}}} zeroinitializer, ptr %rc.25
store {i1, {i64, {i64, ptr}}} %l.24, ptr %rc.25         ; THE BUG: 32-byte store into 40-byte alloca
```

Post-fix, `%t7.a.23` is allocated with the real Result<T, E>
shape from the function's return type, not the legacy
`Result<Int, ...>` default. The store and load widths agree.

Falsifiability per case:
- `test_lf1_complex_result_destructure` — pre-fix prints
  `["k=1", "k=1"]` (BadUrl); post-fix prints `["k=3", "k=5"]`.
- `test_lf2_match_rewrap_propagation` — pre-fix fails at clang
  link with `'%ok.NN' defined with type 'i64' but expected
  '{ ... }'`; post-fix prints `["k=2"]`.
- `test_lf3_nested_15arm_match` — pre-fix prints `[]` (silent
  no-fire); post-fix prints `["k=3", "k=12", "k=15"]`.

Round-trip locked: `git stash` the lower.py edit, re-run pytest,
2 of 3 fail (Lf.1 case 100 doesn't fail because the helpers in
that golden got inlined by the MIR optimizer; the inlining
sidesteps the cross-call sret bug). Reverting also broke Lf.2
and Lf.3 with the recorded signatures.

`tests/llvm/test_lowerer_fixes.py` documents the falsifiability
protocol in module docstring + per-test docstring.

---

## Phase 4 — self-host mirror

**No-op.** Self-host already has the v5.26.1 Eu.2 fix at
`mapanare/self/lower.mn:2259-2306`. STRICT 3-stage fixed point
preserved by construction at v5.45.0's 243,749 lines / 0 diff.

Verified post-bump:
- `python3 scripts/build_stage1.py` rebuilt stage1 successfully.
- `bash scripts/verify_fixed_point.sh` STRICT GREEN.
- `python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1`
  → 102/102 (99 existing + 3 new) GREEN.

---

## Phase 5 — test corpus

### Goldens (3 new)

| File | Lines | Bug locked |
|---|---|---|
| `tests/golden/100_result_complex_destructure.mn` | 80 | Lf.1 |
| `tests/golden/101_match_rewrap_propagation.mn` | 70 | Lf.2 |
| `tests/golden/102_nested_15arm_match.mn` | 80 | Lf.3 |

Goldens 99/99 → 102/102. The harness
`scripts/test_native.py --stage1 mapanare/self/mnc-stage1`
verifies stage1 emit + clang link + binary execution returns 0.

### Pytest harness

`tests/llvm/test_lowerer_fixes.py` — 5 cases:
- `test_lf1_complex_result_destructure` — output assertion
  `["k=3", "k=5"]`.
- `test_lf2_match_rewrap_propagation` — output assertion
  `["k=2"]`.
- `test_lf3_nested_15arm_match` — output assertion
  `["k=3", "k=12", "k=15"]`.
- `test_lf1_regression_trivial_ok_unchanged[Int]` — regression
  for `Result<Int, NE>` callers (must still print `k=2`).
- `test_lf1_regression_trivial_ok_unchanged[String]` — regression
  for `Result<String, NE>` callers (must still print `k=2`).

5/5 GREEN at HEAD.

The harness uses `python3 -m mapanare emit-llvm` (Python
bootstrap) explicitly — the bug never existed in the self-host
stage1, so going through stage1 would be a useless test.

### Bookkeeping

`tests/llvm/test_llvm_link_all.py`:
- `_all_goldens` glob extended to match 3-digit prefixes
  (`[0-9][0-9][0-9]_*.mn`); the corpus crossed 99 at v5.46.0.
- `test_golden_corpus_count` count bumped from 95 (pre-v5.34.0
  number) to 102.

---

## Phase 6 — broader Result<T, E> sweep

```bash
$ grep -rEn "fn .*-> Result<[A-Z][a-zA-Z]+\s*," stdlib/ examples/ tests/ | wc -l
237
```

237 non-trivial-Ok Result-returning functions across the codebase.
Most are in `stdlib/time.mn` (`Result<Date, String>`,
`Result<DateTime, String>`, etc.); existing
`tests/stdlib/test_time_dt.py` (and the v5.34.0 Dt.\* harness)
exercise these and all 1043 `tests/stdlib/` cases pass GREEN at
v5.46.0 HEAD — no regressions.

The v5.43.0 `stdlib/agent/` distributed-agent surface uses the
flat-tuple workaround per the v5.43.0 SESSION_REPORT. Only one
function uses the `Result<NonTrivialOk, NetworkError>` shape:
`stdlib/agent/remote_proto.mn::validate_key`
(`Result<String, NetworkError>`). String is 16 bytes; pre-fix
the small `Result<Int, NetworkError>` was 32 bytes and the
real `Result<String, NetworkError>` was 40 bytes. The 8-byte
diff causes the silent no-fire on nested 15-arm match (Lf.3),
which is one of v5.43.0's recorded repros. v5.46.0 closes this
properly.

The v5.43.0 ecosystem worked around the bug by avoiding
non-trivial-Ok Result entirely; no production code relied on
the wrong output. Per-bug `### Fixed` entry in CHANGELOG flags
"potentially behavior-changing" — semantic shift visible to any
caller that exercised the buggy paths.

---

## Phase 7 — closeout artifacts

- VERSION: `5.46.0`
- CHANGELOG: 3 `### Fixed` entries (Lf.1 + Lf.2 + Lf.3), each
  flagged "potentially behavior-changing"; check_changelog_honesty
  GREEN.
- CLAUDE.md: v5.46.0 release-notes entry with per-Lf detail +
  Phase 0 deviation log.
- docs/SPEC.md: header re-synced from "v5.45.0 cut" to "v5.46.0
  cut"; new sync block summarizing what v5.46.0 ships.
- check_doc_freshness: clean (3 README files updated from
  99/99 → 102/102: en, es, pt; zh-CN was already current per
  the v5.28.0 H.4 policy that localized README updates aren't
  per-release work).
- PRE_PHASE_AUDIT.md and SESSION_REPORT.md: this file +
  PRE_PHASE_AUDIT.

### Pre-existing failures (NOT caused by v5.46.0)

Verified at v5.45.0 baseline (via `git stash` + re-run):

- `tests/cli/test_cli.py::TestRun::test_run_hello` — gcc.exe
  WSL/Windows env issue; fails at v5.45.0 baseline.
- `tests/llvm/test_tensor_reshape.py::test_reshape_size_mismatch_aborts`
  — fails at v5.45.0 baseline; tensor closeout-arc bookkeeping.
- `tests/llvm/test_llvm_link_all.py::test_link_and_run[98_tensor_stepped_slice]`
  — fails at v5.45.0 baseline; pre-existing tensor stepped-slice
  test_llvm_link_all infra issue (separate from
  test_native.py's golden harness which passes 99/99 + 102/102).
- `tests/llvm/test_llvm_link_all.py::test_link_and_run[99_tensor_reshape_aliased]`
  — fails at v5.45.0 baseline; same root cause as 98.

Tracked as v5.47.0+ LOW (panel-decision input).

---

## Carry-forward delta

**Closes:**
- Lf.1 + Lf.2 + Lf.3 (the three v5.43.0 lowerer bugs tracked as
  MEDIUM since v5.43.0 ship).
- The v5.43.0 commitment: "v5.43.x picks up `Result<T, NetworkError>`
  ergonomics once the lowerer fixes land." v5.46.0 does the
  lowerer fixes; v5.46.x picks up the ergonomic refactor.

**Inherits to v5.46.x:**
- Ergonomic refactor of v5.43.0 distributed-agent APIs from flat
  tuple to `Result<T, NetworkError>` (now unblocked).
- Lf.4 variant-name collision (Phase 0 split decision; needs
  multimap-of-variants infrastructure).
- `stdlib/fs.mn::walk_dir` IR codegen carry from v5.40.0.
- websocket.mn `str(byte)` decimal-stringification carry from
  v5.43.0.

**Inherits to v5.47.0 closeout panel:**
- Aggregate state of all v5 carries; panel decides v6.0
  readiness.

**Aggregate state entering v5.47.0:**
- Tensor closeout arc CLOSED (v5.45.0).
- Manifesto arc CLOSED (v5.43.0).
- Package-system runway CLOSED (v5.44.0).
- v5.43.0 lowerer-bug closeout CLOSED (v5.46.0).
- macOS notarization MEDIUM carry (from v5.33.0 Nu.2).
- Ai.1 `_specialize_fn` body-walk MEDIUM carry (from v5.40.0).
- Strict 3-stage fixed point preserved at v5.45.0's 243,749
  lines / 0 diff.
- v5.47.0 panel green-lights v6.0 (or doesn't).

---

## Source delta

| Layer | LOC | Notes |
|---|---|---|
| `mapanare/lower.py` | ~30 | Ok + Err constructor branches; backport v5.26.1 Eu.2. |
| `mapanare/self/*.mn` | 0 | Already had the fix. STRICT preserved by construction. |
| `tests/golden/100_*.mn` | ~80 | Lf.1 regression. |
| `tests/golden/101_*.mn` | ~70 | Lf.2 regression. |
| `tests/golden/102_*.mn` | ~80 | Lf.3 regression. |
| `tests/llvm/test_lowerer_fixes.py` | ~190 | 5 cases + falsifiability protocol. |
| `tests/llvm/test_llvm_link_all.py` | ~10 | Glob extension + count bump. |
| `docs/roadmap/v5/v5.46.0/PRE_PHASE_AUDIT.md` | ~370 | Phase 0 IR-level diagnoses + self-host audit + Lf.4 split rationale. |
| `docs/roadmap/v5/v5.46.0/SESSION_REPORT.md` | this file | Closeout. |
| `CHANGELOG.md` | ~120 | 3 `### Fixed` entries. |
| `docs/SPEC.md` | ~25 | Header re-sync + new sync block. |
| `CLAUDE.md` | ~140 | Release-notes entry. |
| `README.md`, `docs/README.es.md`, `docs/README.pt.md` | 3 | Goldens 99/99 → 102/102 line updates. |
| **Total** | **~1,100 LOC** | Well under v5.43.0's ~2,500 LOC delta. |

---

## Lessons captured

1. **Phase 0 audit pays off again.** PRE_PHASE_AUDIT continued
   the v5.41.0 / v5.43.0 / v5.44.0 / v5.45.0 streak of catching
   structural premise errors before any code edits land. The
   "self-host already has the fix" finding inverted the release
   scope; PLAN budgeted ~16h, actual work was ~6h.
2. **The self-host vs Python bootstrap drift is real.** v5.26.1
   Eu.2 was applied to one side and not the other; v5.46.0
   discovers it 20 releases later. A future structural gate
   could detect such drift via diff'ing constructor lowering
   logic across both sides.
3. **MIR inliner masks bugs.** Initial Lf.1 golden 100 had
   small helpers that got inlined; the bug only manifests at
   cross-call sret boundaries. Real-world repros from v5.43.0
   (`fake_node_listen`, `validate_key`) had complex enough
   helpers to bypass inlining; the v5.46.0 golden 100 was
   updated with branching helpers + string interpolation to
   match.
4. **Pre-existing test bookkeeping accumulates.** 4 pre-existing
   test failures at v5.45.0 baseline; the bookkeeping needs
   periodic cleanup. v5.46.0 fixes one (`test_golden_corpus_count`
   95 → 102 + 3-digit glob extension); the others are tracked.

---

## Closeout

v5.46.0 ready, not tagged. Awaiting lead approval for `git tag
v5.46.0`. The v5.43.0 lowerer-bug closeout arc is structurally
CLOSED; the v5.47.0 closeout panel green-lights v6.0 (or
doesn't).
