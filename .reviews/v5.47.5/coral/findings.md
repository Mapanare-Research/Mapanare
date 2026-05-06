# Coral — v5.47.5 Closeout Panel Findings

**Reviewer axis:** UX + docs + ergonomics
**Arc reviewed:** v5.31.0 → v5.47.0 (17 releases)
**Audit reference:** `.reviews/v5.47.5/PRE_PANEL_AUDIT.md`
**Prior-panel score:** 9.70 (v5.28.0 RE-PANEL)

---

## Summary

The arc shipped **eight new user-facing stdlib cookbooks**:
date/time (v5.34.0), sqlite (v5.35.0), JSON (v5.36.0), HTTP
(v5.37.0), regex (v5.38.0), crypto (v5.39.0), AI (v5.40.0),
agent (v5.42.0). Plus extended `docs/SPEC.md` headers tracked
across every release via `check_doc_freshness.py`. Plus
`docs/manifesto.md` updated at v5.40.0 with the "first manifesto
item shipped at the syntax level" section.

**Ergonomic discipline** in the stdlib was substantively honest.
When v5.x couldn't deliver the natural API shape, the workaround
was documented at the source-preamble level + cookbook level,
not hidden:
- v5.43.0 Da.\* flat-tuple shape (instead of `Result<T,
  NetworkError>`) explicitly documented; v5.46.0 closes the
  underlying lowerer bugs; v5.47.0 splits the ergonomic refactor
  to v5.47.1 (Cl.2)
- v5.42.0 As.\* strategy-library shape (instead of supervisor-
  agent) documented as a workaround pattern
- v5.40.0 Ai.\* function-syntax fall-back (instead of `ask`
  keyword) documented; gated on `_specialize_fn` body-walk
- v5.34.0 Dt.\* free-function arithmetic (instead of operator
  overloads) documented; gated on `impl Add for Dur`

The pattern across these is: **ship the surface, document
the ergonomic deferral, schedule the upgrade**. This is the
right discipline.

---

## Per-category grades

### Stdlib cookbook density

**Grade: EXCEEDS**

8 new cookbooks across the arc, each ~250-370 LOC and
each with: quick reference + type/API table + 4-7
recipes + "what's not here yet" forward-link + migration
note from prior surface (where applicable). The
`docs/stdlib/json.md` (v5.36.0) explicitly documents
the strictness change as `### Changed` + Js.4.B status.
The `docs/stdlib/agent.md` (v5.42.0 + v5.43.0 extension)
is the deepest cookbook in the project.

### SPEC sync discipline

**Grade: EXCEEDS**

`check_doc_freshness.py` GREEN at HEAD. The v5.33.1 Hd.\*
hotfix closed a 3-minor SPEC-header lag; from v5.33.1 onward
the gate has held. Every release in the arc bumps the SPEC
header + appends a sync block summarizing what shipped.
The v5.45.0 sync block calling out the 6 new runtime
exports was the first SPEC-scoped runtime additions block
since v5.21.0.

### CHANGELOG framing honesty

**Grade: EXCEEDS**

`### Changed` (potentially breaking-ish) discipline applied
correctly across the arc:
- v5.36.0 Js.1 RFC 8259 strict mode
- v5.39.6 Map<K,V> non-String K compile-time error
- v5.43.0 Da.\* RemoteExitReason rename
- v5.45.0 Ts.\* mutable-view semantic swap

`check_changelog_honesty.py` GREEN at HEAD.

### Banner UX (v5.31.0)

**Grade: EXCEEDS**

The publish-run-#50 anti-pattern (`[dev mode]` banner
firing on release installs) was a real UX bug; v5.31.0
Bn.\* closed it correctly. The `MAPANARE_RELEASE=1` env
var + `_is_release_install()` heuristic + argv-peek skip
for metadata commands is the right composition. Honest-
default policy: "when in doubt, don't fire" is correct.

### Localized README state

**Grade: NEEDS WORK** *(LOW-severity)*

Per the v5.28.0 H.4 cross-reference + project memory: the
es/pt/zh-CN READMEs are tracked as a separate bookkeeping
cycle, not per-release work. v5.47.5 panel cut HEAD has
**localized READMEs frozen at the v5.28.0 hygiene-pass
state** (95/95 goldens, 241k lines, 23-release streak,
v5.23-v5.27 arc summary) — 19 minor versions stale on
front-page narrative.

This is the v5.28.0 H.4 finding pattern recurring at v5.47.5
scale. **Recommend a v5.47.x localized-README refresh
patch** capturing 95/95 → 103/103 goldens, 241k → 244k
lines, 23 → 50 release streak, v5.31-v5.47.0 arc summary
(foundation + stdlib + manifesto + tensor + package
system).

This is **not a v6.0 PLAN input** — it's a one-shot
documentation refresh. v5.28.0 H.4 closed this for the
v5.13-v5.21 arc; v5.47.x can close for v5.31-v5.47.

### Cookbook discoverability

**Grade: MEETS**

8 new cookbooks under `docs/stdlib/` is the right shape
but there's no top-level index pointing at them. A user
landing in `docs/` doesn't have a "stdlib reference"
landing page. `README.md` mentions some but not all. **Low
severity** — the cookbooks are findable via grep; this
is a cosmetic ergonomic gap.

---

## Findings

### Co.0 — cookbook density is the v5 ergonomic story (LOW, positive)

The "stdlib gap-close arc" delivered. 8 new cookbooks +
the manifesto.md update shipping with v5.40.0's first
manifesto item is the highest cohesion in v5 docs.

### Co.1 — localized README staleness (MEDIUM, fresh)

Same shape as v5.28.0 H.4 (Bo.17r class). Three localized
READMEs (es/pt/zh-CN) are 19-minor-versions stale at HEAD.
**Recommend v5.47.x patch:** refresh native-compiler
subsections in each with v5.31-v5.47.0 arc summary +
50-release streak + 244k lines + 103/103 goldens.

### Co.2 — top-level stdlib index missing (LOW, fresh)

Eight new cookbooks under `docs/stdlib/`; no top-level
landing page. `README.md` mentions stdlib in passing but
no "stdlib reference" doc. **Recommend v5.47.x docs
addition:** `docs/stdlib/INDEX.md` listing all cookbooks
with a one-line description each.

### Co.3 — manifesto.md vs CLAUDE.md drift risk (LOW, fresh)

`docs/manifesto.md` updated at v5.40.0 with one section.
v5.42.0 As.\* + v5.43.0 Da.\* were equally manifesto-axis
work but did not update manifesto.md. **Recommend v5.47.x
patch:** manifesto.md gets a "v5 closed: agents are
cross-machine" section pointing at v5.42.0 + v5.43.0.

### Co.4 — ergonomic deferrals are honestly framed (LOW, positive)

Every ergonomic deferral in the arc (Ai.1+Ai.2 keyword,
Da.\* flat-tuple, As.\* strategy-library, Dt.5 operator
overloads) was documented at source-preamble + SESSION_REPORT
+ cookbook level. **No hidden ergonomic debt.** This is
the right discipline.

### Co.New1 — `docs/stdlib/INDEX.md` as v5.47.x patch (LOW, fresh)

(See Co.2)

### Co.New2 — Spanish/Portuguese/Chinese cookbook localization (LOW, fresh)

Cookbooks are English-only. Localized READMEs exist for
README only. **Recommend v6.0 process input:** decide
whether stdlib cookbooks should localize. For now, treat
as deferred (English is canonical; non-English speakers
read English docs in practice). **NOT a v5.47.x patch
candidate.**

---

## Carry-forward suggestions

For Cp.4 V5_TO_V6_CARRY.md:

- **(b) v5.47.x patch candidate:** Localized README
  refresh (Co.1) — one-shot, well-scoped
- **(b) v5.47.x patch candidate:** `docs/stdlib/INDEX.md`
  (Co.2 / Co.New1) — small, ergonomic
- **(b) v5.47.x patch candidate:** manifesto.md As.\*+Da.\*
  section (Co.3)
- **(c) retired:** Spanish/Portuguese/Chinese cookbook
  localization (Co.New2) — not v5.47.x scope; not v6.0
  scope; tracked as future-consideration

---

## Score

**9.65 / 10**

Down 0.05 from v5.28.0's 9.70 — entirely attributable to
the localized README staleness (Co.1) being a recurrence
of the v5.28.0 H.4 pattern that v5.47.5 didn't pre-close.
The 0.30 gap is honest cosmetic-ergonomic debt across
Co.1 + Co.2 + Co.3.

## Recommendation

**PASS WITH NOTES**

v5 ships clean from the docs/UX axis. The "with notes" is
the localized README refresh — v6.0 should not start until
v5.47.1 or v5.47.2 closes Co.1. This is small docs work
(~2-3 hours), not a release-blocker.
