# v5.47.0 — Cl.\* — pre-panel hygiene cleanup

**Status:** PLANNING
**Type:** Hygiene release. **Drains every closeable LOW-tier
carry before the v5.47.5 closeout panel sees the docket.**
Substantive Lf.4 fix in `mapanare/semantic.py` /
`mapanare/lower.py`; ergonomic stdlib refactor of v5.43.0
distributed-agent APIs from flat tuple to `Result<T,
NetworkError>` (now unblocked by v5.46.0); two small stdlib
bug fixes if cheap.
**Breaking:** No, in the surface sense. The agent stdlib
refactor changes public function signatures in `stdlib/agent/`
from flat-tuple shape `(ok: Bool, value, err_kind: Int,
err_msg: String)` back to ergonomic `Result<T, NetworkError>`.
This is a stdlib API surface change — flagged in CHANGELOG
`### Changed` (potentially breaking-ish for any caller that
adopted the v5.43.0 flat-tuple shape; in practice the surface
shipped as a workaround that was always intended to revert).
**Prerequisite:** v5.46.0 shipped (Lf.\* — three lowerer bugs
closed; the agent refactor is structurally unblocked because
`Result<NodeHandle, NetworkError>` destructure now works).
**Estimated effort:** 1–2 sessions. Smaller than v5.46.0; the
work is structurally well-understood (Lf.4 was scoped at Phase
0; the agent refactor is the "remove the workaround" follow-on).

---

## Why this exists

The v5.28.0 RE-PANEL precedent is load-bearing here. That
panel scored 9.72 (the +0.31 recovery) specifically because
Phase 2 H.\* hygiene closures landed *ahead of panel cut* —
25/25 docket items closed before the panel saw the docket.
Reviewers can't dock for items that no longer exist.

Going straight from v5.46.0 to the closeout panel means the
panel sees:

1. **Lf.4 split** — explicitly named in v5.46.0 SESSION_REPORT
   as v5.46.x scope. One release later it's still open.
2. **Flat-tuple → `Result<T, NetworkError>` ergonomic refactor**
   — explicitly named in the v5.46.0 SESSION_REPORT carry-
   forward as v5.46.x. The v5.46.0 PROMPT itself called the
   flat-tuple shape "documented as ugly" and committed v5.46.x
   to the refactor. One release later it's still open.
3. **`stdlib/fs.mn::walk_dir` IR codegen issue** — v5.40.0
   carry, never picked up.
4. **`stdlib/net/websocket.mn` `str(byte)` decimal-stringification**
   — v5.43.0 carry, never picked up.

These are LOW carries; no individual one threatens v6.0
readiness. But four LOW carries on a closeout-panel docket is
~8 reviewer-comments waiting to happen. v5.47.0 closes them
before the panel runs.

The split — v5.47.0 hygiene + v5.47.5 panel — mirrors the
v5.28.0 precedent exactly. The cost is one extra release;
the benefit is a clean docket and (per the v5.28.0 +0.31
recovery shape) a higher panel score that reflects actual
state, not paperwork.

---

## Goals

1. **Cl.0** — Phase 0 audit: confirm each Cl.\* item is
   actually still open at v5.47.0 HEAD; verify the v5.46.0
   Lf.\* fix didn't accidentally close any of them; localize
   each fix site; size the diff per item.
2. **Cl.1** — **Lf.4 — variant-name collision.** Match-pattern
   resolution keys on `(subject_type, variant_name)` instead
   of just `variant_name`. Lock with regression test.
3. **Cl.2** — **Agent stdlib ergonomic refactor.** Convert
   `stdlib/agent/url.mn` + `stdlib/agent/remote.mn` +
   `stdlib/agent/node.mn` + `stdlib/agent/supervision.mn` from
   flat tuple `(ok, value, err_kind, err_msg)` to ergonomic
   `Result<T, NetworkError>`. The v5.46.0 Lf.\* fix unblocked
   this; v5.47.0 picks it up.
4. **Cl.3** — **`stdlib/fs.mn::walk_dir` IR codegen** (carry
   from v5.40.0). Match-on `Result<List<String>, FsError>`
   produces `extractvalue ptr ... 0` then `zext ptr to i64`
   which clang rejects. Phase 0 confirms whether the v5.46.0
   Lf.\* fix coincidentally closed this; if not, fix.
5. **Cl.4** — **`stdlib/net/websocket.mn` `str(byte)`
   decimal-stringification** (carry from v5.43.0). The
   websocket frame-header path uses `str(byte)` decimal-
   stringification where it should use `__mn_str_chr` (now
   that v5.43.0 Da.0 extended the latter to cover bytes
   0..255). Cosmetic but a latent footgun on any future
   pure-Mapanare binary protocol.
6. **Cl.5** — **Self-host mirror gate.** Cl.1 lives in
   `mapanare/semantic.py` + `mapanare/lower.py` + their
   self-host mirrors at `mapanare/self/semantic.mn` +
   `mapanare/self/lower.mn`. STRICT 3-stage fixed point
   preserved by stage1 rebuild after each mirror edit.
   Cl.2 / Cl.3 / Cl.4 don't touch the self-host (stdlib /
   agent stdlib edits only) — STRICT preserved by
   construction for those.
7. **Cl.6** — **Test corpus.** Cl.1 regression in
   `tests/llvm/test_lowerer_fixes.py` (extend the v5.46.0
   harness with Lf.4 cases) + at least one new golden
   (`103_variant_name_collision.mn`). Cl.2 regression locks
   the new agent API surface — pytest harness in
   `tests/stdlib/test_distributed_agents.py` (which already
   exists from v5.43.0; updates to assert the new
   `Result<T, NetworkError>` return shape). Cl.3 / Cl.4
   regression in their respective module test files.
8. **Cl.7** — **Closeout artifacts.** CHANGELOG `### Fixed`
   per item; CLAUDE.md release-notes entry; SPEC.md sync;
   carry-forward delta.

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Cl.0** | HIGH (gate) | **Phase 0 audit.** For each Cl.\* item: confirm still-open at v5.47.0 HEAD via repro; localize fix site; estimate LOC. Output: `docs/roadmap/v5/v5.47.0/PRE_PHASE_AUDIT.md`. Surface any deviation from PLAN before any code edits land. Critical Cl.1 LOC measurement: ≤ 60 LOC = bundle; > 60 LOC = re-split (the v5.46.0 PLAN's ≤30 LOC bundle threshold doesn't apply because v5.47.0 is itself the bundling release). | 3h |
| **Cl.1** | HIGH | **Lf.4 — variant-name collision.** Multimap of `variant_name → list[(enum_name, return_type, arity)]` built during semantic checker registration. Constructor expression resolution consults the binding's declared type when present (e.g. `pon n: NetworkError = TransportLost("...")`); falls back to single-match path when context is absent. Match-pattern resolution keys on `(subject_type, variant_name)`. Mirror in `mapanare/self/semantic.mn` + `mapanare/self/lower.mn`. Estimated 50-80 LOC across the two files; falsifiability locked with `/tmp/diag_lf4.mn` repro from v5.46.0 PRE_PHASE_AUDIT. | 5h |
| **Cl.2** | HIGH | **Agent stdlib ergonomic refactor.** Convert all v5.43.0 functions returning the flat-tuple workaround back to `Result<T, NetworkError>`. Affected files: `stdlib/agent/url.mn`, `stdlib/agent/remote.mn`, `stdlib/agent/node.mn`, `stdlib/agent/supervision.mn`. `parse_agent_url`, `node_listen`, `node_connect`, `remote_agent_connect`, `remote_agent_send`, etc. The `UrlParseResult` flat-tuple intermediate type goes away (or stays internal-only). Existing `test_distributed_agents.py` updates to assert the new shape. Zero compiler edits — purely stdlib. | 4h |
| **Cl.3** | MEDIUM | **`stdlib/fs.mn::walk_dir` IR codegen.** v5.40.0 SESSION_REPORT documented this; v5.46.0 Lf.\* may have closed it as a side-effect (the failure mode `extractvalue ptr ... 0` then `zext ptr to i64` is the same wrong-IR-shape class as Lf.1). Phase 0 verifies. If still open, fix in `mapanare/lower.py` `_lower_match` for `Result<NonTrivialOk, E>` patterns. If v5.46.0 closed it, document and skip. | 2h (+ 0h if v5.46.0 closed it) |
| **Cl.4** | LOW | **`stdlib/net/websocket.mn` `str(byte)` cleanup.** Replace decimal-stringification calls with `__mn_str_chr` (v5.43.0 Da.0 extended this to bytes 0..255 with byte 0x00 preservation). Cosmetic; behavior identical for ASCII bytes; correct for high bytes. Pure stdlib; zero compiler edits. | 1h |
| **Cl.5** | HIGH (gate) | **Self-host mirror.** Cl.1 requires mirror in `mapanare/self/semantic.mn` + `mapanare/self/lower.mn`. Cl.2 / Cl.3 / Cl.4 don't touch self-host. Stage1 rebuild after each Cl.1 mirror edit; STRICT 3-stage fixed point preserved at v5.46.0's 243,749 lines / 0 diff (50-release strict streak target). | 3h |
| **Cl.6** | HIGH (gate) | **Test corpus.** New golden `103_variant_name_collision.mn` (~50 LOC); extend `tests/llvm/test_lowerer_fixes.py` with `test_lf4_variant_name_collision` parametrized over enum-pair shapes (NetworkError + ExitReason from v5.43.0 supervision; minimum 2 enums, possibly 3 for the multi-collision case). Update `tests/stdlib/test_distributed_agents.py` to assert the new `Result<T, NetworkError>` return shape (not the flat tuple). New golden brings count 102 → 103. | 3h |
| **Cl.7** | HIGH (gate) | **Closeout artifacts.** Bump VERSION to 5.47.0; CHANGELOG `### Fixed` per Cl.\* item (4 entries: Lf.4, agent refactor, fs.mn walk_dir if still applicable, websocket str(byte)); CLAUDE.md release-notes; SPEC.md header re-synced from "v5.46.0 cut" to "v5.47.0 cut" with new sync block; SESSION_REPORT.md; PR_BODY.md if requested. | 1h |

---

## Phase plan

- **Phase 0** — Pre-flight; v5.46.0 HEAD clean (post-`commit`).
  Reproduce each Cl.\* item; verify still-open. Decide whether
  Cl.3 was closed by Lf.\*. Write PRE_PHASE_AUDIT.md.
- **Phase 1** — Cl.1 Lf.4 fix (semantic checker + lowerer).
  This is the biggest item; do it first while context is
  fresh.
- **Phase 2** — Cl.2 agent stdlib refactor. Pure stdlib; can
  parallelize with Phase 1 review if desired.
- **Phase 3** — Cl.3 (if still applicable) + Cl.4. Both
  small.
- **Phase 4** — Cl.5 self-host mirror. Stage1 rebuild after
  each Cl.1 mirror edit per the v5.45.0 / v5.46.0 ordering.
- **Phase 5** — Cl.6 test corpus.
- **Phase 6** — Cl.7 closeout (bump + verify + STRICT check).

---

## Out of scope

- **macOS notarization** (carry from v5.33.0 Nu.2). Needs paid
  Apple Developer cert + signing infrastructure. v6.0+ when
  paid distribution makes it worthwhile.
- **Ai.1 `_specialize_fn` body-walk for generic stdlib calling
  generic intrinsics** (carry from v5.40.0). Structural
  compiler work; v6.0 PLAN input.
- **Borrow checker.** v6.0 thesis. Not v5.47.0 scope.
- **Hard removal of `{}`.** v6.0. Soft deprecation since
  v5.19.0 holds.
- **The closeout panel itself.** v5.47.5.

---

## Risk

1. **Cl.1 LOC overshoots.** v5.46.0 Phase 0 estimated ≥ 50 LOC
   for Lf.4. If v5.47.0 Phase 0 finds it's actually 100+ LOC
   across semantic.py + lower.py + their self-host mirrors,
   Cl.1 could split further. Mitigation: explicit Phase 0
   sizing decision; if > 100 LOC, defer Cl.1 to v5.47.1 and
   ship v5.47.0 with Cl.2 + Cl.4 only.
2. **Cl.2 surfaces NEW v5.x bugs.** Removing the flat-tuple
   workaround means user code paths exercise `Result<T,
   NetworkError>` destructure shapes that v5.46.0 fixed.
   If any of those shapes hit a *different* lowerer bug,
   v5.47.0 surfaces it. Mitigation: Phase 0 includes a quick
   sweep of the v5.43.0 `stdlib/agent/` callers; flag any
   suspicious patterns; if a new bug surfaces, scope decision
   between fix-in-v5.47.0 vs split-to-v5.47.1.
3. **STRICT preservation.** Cl.1 mirror touches
   `mapanare/self/semantic.mn` + `mapanare/self/lower.mn` —
   the highest-risk paths for STRICT divergence (the v5.45.0
   tensor work broke the streak; v5.46.0 had no self-host
   touches and trivially preserved). Mitigation: stage1
   rebuild after each mirror edit; halt if STRICT diverges;
   investigate before continuing.
4. **Cl.3 false-positive close.** v5.46.0 Lf.\* fix touched
   `mapanare/lower.py` Ok/Err branches; it's plausible but
   not certain that fs.mn `walk_dir` works now. Phase 0 must
   verify with the actual v5.40.0 repro, not guess.
5. **Panel score erosion.** If v5.47.0 ships and the panel
   still scores < 9.5, the split was wasted. Mitigation: the
   v5.28.0 +0.31 recovery shape is the precedent; the
   structural argument for hygiene-before-panel is sound;
   trust the precedent.

---

## Success criteria

- ✅ Lf.4 closed: `/tmp/diag_lf4.mn` (or successor) compiles
  and prints `n=1\nx=1` (or whatever the post-fix correct
  output is).
- ✅ Agent stdlib API surface: every public `pub fn` in
  `stdlib/agent/{url,remote,node,supervision}.mn` returning
  the v5.43.0 flat-tuple shape now returns `Result<T,
  NetworkError>`. Existing `test_distributed_agents.py`
  GREEN against the new shape.
- ✅ Cl.3 closed (if applicable) or documented closed.
- ✅ Cl.4 closed: `stdlib/net/websocket.mn` no longer uses
  `str(byte)` decimal-stringification on byte values.
- ✅ Self-host mirror landed; STRICT 3-stage fixed point
  preserved.
- ✅ Goldens 102/102 → 103/103 (Cl.6 adds one).
- ✅ `tests/llvm/test_lowerer_fixes.py` extended with Lf.4
  cases; falsifiability per case documented.
- ✅ CHANGELOG `### Fixed` per item; check_changelog_honesty
  GREEN.
- ✅ CLAUDE.md release-notes entry; check_doc_freshness
  GREEN.
- ✅ SPEC.md header re-synced.
- ✅ `make ci-gates` GREEN; `make lint` clean.

---

## Carry-forward delta

**Closes:**
- Lf.4 variant-name collision (split from v5.46.0).
- Flat-tuple → `Result<T, NetworkError>` ergonomic refactor in
  `stdlib/agent/` (commitment from v5.46.0 SESSION_REPORT).
- `stdlib/fs.mn::walk_dir` IR codegen (carry from v5.40.0; if
  Phase 0 confirms still-open).
- `stdlib/net/websocket.mn` `str(byte)` decimal-stringification
  (carry from v5.43.0).

**Inherits to v5.47.5 panel:**
- Whatever Cp.4 carry-forward ledger surfaces; expected count
  is much smaller after v5.47.0 hygiene drains the LOW tier.

**Inherits to v6.0:**
- macOS notarization (paid infrastructure dependency).
- Ai.1 `_specialize_fn` body-walk (structural compiler work).
- Borrow checker (the v6.0 thesis).
- Hard removal of `{}` (carry from v5.19.0).
- Multi-level alias analysis.

**Aggregate state entering v5.47.5:**
- Tensor closeout arc CLOSED (v5.45.0).
- Manifesto arc CLOSED (v5.43.0).
- Package-system runway CLOSED (v5.44.0).
- v5.43.0 lowerer-bug closeout CLOSED at v5.46.0.
- Pre-panel hygiene cleanup CLOSED at v5.47.0.
- 0 HIGH carries; ≤ 2 MEDIUM carries (the two structural items
  legitimately deferrable to v6.0); ≤ 4 LOW carries.
- v5.47.5 panel reviews a clean docket.
