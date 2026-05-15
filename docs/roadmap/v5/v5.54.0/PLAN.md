# v5.54.0 — Cl.2 + Cl.3 + Cl.4-residual — agent stdlib ergonomic refactor + walk_dir IR codegen + websocket str(byte) sweep

**Status:** PLANNING
**Type:** Stdlib closeout release. Drains the three LOW carries that
v5.47.0 named for v5.47.1 but split / partially-shipped, plus the
v5.43.0 distributed-agent API ergonomic refactor that v5.46.0 Lf.\*
structurally unblocked. **Cl.2** is the load-bearing item (~400 LOC
across stdlib public API + ~50 callers + 4 pytest shape changes);
**Cl.3** and **Cl.4-residual** are mechanical bundles.
**Breaking:** **YES for stdlib users** — Cl.2 changes the public
signature of `stdlib/agent/{url,remote,node,supervision}.mn` from
flat tuple `(ok, value, err_kind, err_msg)` to ergonomic
`Result<T, NetworkError>`. Bundled in v5.54.0 explicitly because
v6.0's hard `{}` removal is the bigger Mapanare-language break;
piggybacking the stdlib break in the same release window keeps the
churn cost amortized. Existing callers that destructure the tuple
will not compile against v5.54.0 stdlib until they refactor.
**Prerequisite:** v5.53.0 ships (Sf.\* + Te.3.F closed). v5.46.0
Lf.\* lowerer fixes shipped (closed the wrap-shape default bug
that forced v5.43.0 into the flat-tuple workaround in the first
place).
**Estimated effort:** 2 sessions. Cl.2 alone is 1.5 sessions per
v5.47.0 Phase 0's sizing (~400 LOC + ~50 callers + tests). Cl.3 +
Cl.4-residual fit in the second session's tail.

---

## Why this exists

**Cl.2 — agent stdlib ergonomic refactor.** v5.43.0 Da.\* shipped
distributed-agent APIs with a flat-tuple Result workaround because
v5.43.0-era lowerer bugs (Lf.1 + Lf.2 + Lf.3, closed in v5.46.0)
prevented `Result<T, NetworkError>` from compiling correctly when
`NetworkError` was a non-trivial enum. v5.43.0 SESSION_REPORT
explicitly noted the workaround as temporary; v5.46.0 closed the
lowerer bugs; v5.47.0 Phase 0 confirmed the refactor is
structurally unblocked but sized it at ~400 LOC and split it to a
dedicated release. v5.54.0 ships that release.

The refactor surface from v5.47.0 SESSION_REPORT.md:

| File | Public functions | Internal callers |
|---|---:|---:|
| `stdlib/agent/url.mn` | 2 | ~12 |
| `stdlib/agent/remote.mn` | 4 | ~18 |
| `stdlib/agent/node.mn` | 3 | ~10 |
| `stdlib/agent/supervision.mn` | 3 | ~10 |
| **Total** | **~12** | **~50** |

Plus `tests/stdlib/test_distributed_agents.py` 4-case shape change.

**Cl.3 — `stdlib/fs.mn::walk_dir` IR codegen.** v5.40.0 SESSION_REPORT
opened this as a new LOW: `walk_dir` returns
`Result<List<String>, FsError>` but the destructure site emits
`extractvalue ptr ... 0` then `zext ptr to i64`, which clang rejects.
v5.47.0 Phase 0 verified the bug is "wrong-IR-shape class different
from Lf.1" — receiver-side Result aggregate at the destructure site,
not the constructor-side wrap-shape default that v5.46.0 fixed.
Distinct fix-site, same enum-layout discipline.

**Cl.4-residual — `stdlib/net/websocket.mn` `str(byte)` cleanup.**
v5.47.0 Cl.4 swept 11 `str(byte)` sites in `read_frame` /
`build_send_frame` / chunked-send. v5.47.0 SESSION_REPORT noted
"Cl.4 sites enumerated" suggesting some sites may have remained;
this release does the final sweep and verifies zero residuals.
Mechanical 0-1 hour bundle.

---

## Items in scope

### Cl.2 — agent stdlib ergonomic refactor

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Cl.2.0** | HIGH (gate) | Phase 0 audit. Re-enumerate the 4-file public-API surface at HEAD (the v5.47.0 count of 12 functions may have drifted across v5.48–v5.52). Snapshot the existing flat-tuple signatures verbatim. Decide migration boundary: do all 4 files migrate atomically, or per-file with cross-file callers held on a v5.43.0-shaped adapter shim during the transition? Output: `PRE_PHASE_AUDIT.md` with per-function before/after signature table + caller-count delta. | 2h |
| **Cl.2.1** | HIGH | `stdlib/agent/url.mn` migration. 2 public functions → `Result<T, NetworkError>` shape. Internal callers updated. Falsifiability anchor: existing `tests/stdlib/` cases pass against the new shape. | 1.5h |
| **Cl.2.2** | HIGH | `stdlib/agent/remote.mn` migration. 4 public functions. Largest surface (`remote_call`, `remote_send`, `remote_recv`, `remote_close` or similar — Phase 0 confirms). | 3h |
| **Cl.2.3** | HIGH | `stdlib/agent/node.mn` migration. 3 public functions. | 1.5h |
| **Cl.2.4** | HIGH | `stdlib/agent/supervision.mn` migration. 3 public functions. | 1.5h |
| **Cl.2.5** | HIGH | `tests/stdlib/test_distributed_agents.py` migration. 4 case shape changes per v5.47.0 Phase 0 enumeration. Plus new pytest cases asserting the `Result<T, NetworkError>` shape compiles + round-trips. | 1h |
| **Cl.2.6** | MEDIUM | `docs/stdlib/agent.md` cookbook refresh. v5.43.0 cookbook used flat-tuple examples; v5.54.0 cookbook uses `match result { Ok(v) => ..., Err(e) => ... }` examples. | 0.5h |
| **Cl.2.7** | HIGH (gate) | Cross-cluster regression sweep. After all 4 files + tests + docs land, run full stdlib test suite + goldens + STRICT. The refactor is BREAKING for stdlib consumers; v5.54.0 is the explicit break point. | 1h |

### Cl.3 — `stdlib/fs.mn::walk_dir` IR codegen

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Cl.3.0** | MEDIUM (gate) | Phase 0 audit. Reproduce the IR generation; capture the exact `extractvalue ptr ... 0` + `zext ptr to i64` sequence. Localize: is the bug in `mapanare/lower.py`'s destructure handling of Result aggregate receivers, or in `walk_dir`'s specific IR emission? If lowerer-only, self-host needs mirror (v5.46.0 Lf.\* precedent). | 1h |
| **Cl.3.1** | MEDIUM | Apply the fix at the localized site. ≤ 30 LOC predicted. | 1h |
| **Cl.3.2** | MEDIUM | Self-host mirror if needed. | 0-0.5h |
| **Cl.3.3** | MEDIUM | Falsifiability test in `tests/stdlib/test_fs.py::TestWalkDir`. Run `walk_dir` against a synthesized temp tree; assert it returns `Ok(List<String>)` with expected entries. | 0.5h |

### Cl.4-residual — websocket str(byte) sweep

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Cl.4r.0** | LOW (gate) | Phase 0 audit. `grep -nP "str\(byte\)|str\(\w+_byte\)" stdlib/net/websocket.mn` to enumerate residual sites. v5.47.0 Cl.4 hit 11 sites; verify count at HEAD. | 0.25h |
| **Cl.4r.1** | LOW | Mechanical sweep: replace each residual `str(byte)` with `__mn_str_chr(byte)` per v5.43.0 Da.0 precedent. | 0.5h |
| **Cl.4r.2** | LOW | Verify via `tests/stdlib/test_websocket.py` (existing). | 0.25h |

---

## Phase plan

- **Phase 0** — Cl.2.0 + Cl.3.0 + Cl.4r.0 in parallel. Three audits
  in one combined `PRE_PHASE_AUDIT.md` (or split per docket).
  Critical: Cl.2 sizing gate. If Phase 0 finds Cl.2 > 600 LOC
  (the v5.47.0 estimate was 400; drift may have pushed it higher),
  split per-file: ship `stdlib/agent/url.mn` in v5.54.0, defer the
  other 3 files to v5.54.1.
- **Phase 1** — Cl.2.1 (url.mn). Smallest surface; canary for the
  migration pattern.
- **Phase 2** — Cl.2.2 (remote.mn). Largest surface.
- **Phase 3** — Cl.2.3 + Cl.2.4 (node.mn + supervision.mn). Bundled.
- **Phase 4** — Cl.2.5 (tests) + Cl.2.6 (docs).
- **Phase 5** — Cl.2.7 (regression sweep).
- **Phase 6** — Cl.3.\* (walk_dir IR fix). Independent of Cl.2;
  can interleave if Cl.2 is blocked on review.
- **Phase 7** — Cl.4r.\* (websocket sweep).
- **Phase 8** — Closeout (VERSION 5.53.0 → 5.54.0; CHANGELOG
  `### Changed` for Cl.2 with **BREAKING** annotation; `### Fixed`
  for Cl.3 + Cl.4r; SESSION_REPORT.md; CLAUDE.md; SPEC.md re-sync).

STRICT 3-stage fixed point preserved at every phase. Goldens
103/103. The line count is expected to shift by ~−200 lines net
(Cl.2 removes flat-tuple plumbing; Cl.3 + Cl.4r are nearly
line-neutral); v5.54.0 baseline preserves at the new value.

---

## Out of scope

- **`stdlib/agent/url.mn` URL parsing refactor.** Cl.2 only
  changes the Result shape; URL-parse internals stay.
- **Distributed-agent wire protocol changes.** v5.43.0 Da.\*
  shipped wire format v1 with HMAC-SHA256 + 100MB DoS guard;
  v5.54.0 keeps the wire format unchanged.
- **`stdlib/fs.mn` broader refactor.** Cl.3 fixes the specific
  walk_dir IR codegen bug; other fs.mn functions stay.
- **`stdlib/net/websocket.mn` framing refactor.** Cl.4r is the
  str(byte) cleanup only; the v5.43.0 framing implementation
  stays.
- **Adapter shim for v5.43.0-shaped callers.** Cl.2 is an explicit
  break; no shim. External consumers refactor at v5.54.0 boundary.
  v5.43.0-shaped stdlib remains git-tagged at v5.43.0 if needed.
- **Borrow checker.** v6.0 thesis.
- **macOS notarization (Nu.2) + Ai.1 `_specialize_fn`.** v5.55.0
  scope.

---

## Risk

1. **Cl.2 LOC overrun.** v5.47.0 Phase 0 estimated ~400 LOC; if
   the surface drifted across v5.48–v5.52, the count could be
   higher. Mitigation: Phase 0 sizing gate; if > 600 LOC, split
   per-file across v5.54.0 + v5.54.1.
2. **Breaking change downstream churn.** External Mapanare projects
   using v5.43.0 distributed-agent APIs break at v5.54.0. The
   v5.x → v6.0 migration document (`docs/roadmap/v6/MIGRATION.md`,
   if it exists) needs a Cl.2 entry. Mitigation: CHANGELOG entry
   names the break explicitly with migration recipe; v5.54.0
   release notes link to the recipe.
3. **Cl.3 root cause wider than predicted.** If the bug is in
   `mapanare/lower.py`'s destructure helper (not in `walk_dir`-
   specific code), other Result-receiving callers may share the
   bug. Mitigation: Phase 0 surface enumeration; if > 5 callers
   affected, split Cl.3 to a dedicated release (v5.54.1) with
   broader sweep.
4. **STRICT divergence at Cl.2.7 sweep.** The stdlib refactor
   doesn't touch `mapanare/self/*.mn` so STRICT preserves by
   construction. But `mnc_all.mn` includes self-host that calls
   `stdlib/agent/` indirectly? Verify in Phase 0; if yes, the
   self-host migration is part of Cl.2 scope, not free.

---

## Success criteria

1. **Cl.2.** `stdlib/agent/{url,remote,node,supervision}.mn`
   public APIs all return `Result<T, NetworkError>` (no flat
   tuples). 12 public function signatures changed. ~50 internal
   callers updated. 4 pytest shape changes in
   `tests/stdlib/test_distributed_agents.py` (plus new positive
   cases for `Ok` and `Err` round-trip).
2. **Cl.3.** `stdlib/fs.mn::walk_dir` compiles + executes via
   stage1 against a synthesized temp tree; returns
   `Ok(List<String>)` with expected entries; `Err` path tested
   via permission-denied or non-existent path.
3. **Cl.4r.** `grep -c "str(byte)" stdlib/net/websocket.mn`
   returns 0 (was 11 at v5.47.0; v5.47.0 Cl.4 closed some — verify
   Phase 0 count).
4. **Stdlib regression.** `pytest tests/stdlib/` GREEN.
5. **Goldens.** 103/103 on Linux + Windows.
6. **STRICT.** 3-stage fixed point preserved at the new
   v5.54.0 baseline.
7. **CHANGELOG `### Changed`** entry for Cl.2 names BREAKING +
   migration recipe.
8. **Aggregate state entering v5.55.0:** **0 HIGH** / **2 MEDIUM**
   (Ai.1 `_specialize_fn`; Nu.2 macOS notarization) / **~2 LOW**
   (Lf.4 variant-name collision; any Cl.3 residual surface
   surfaced by Phase 0).

---

## Carry-forward to v5.55.0

- **Ai.1 `_specialize_fn` body-walk fix** (MEDIUM) — Windows-doable.
- **Nu.2 macOS notarization** (MEDIUM) — needs Mac access + Apple
  Developer cert.
- **Lf.4 variant-name collision** (LOW) — non-blocking; defer-to-v6.0
  candidate.
