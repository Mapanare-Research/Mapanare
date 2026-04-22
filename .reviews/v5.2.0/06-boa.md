# Panel v5.2.0 — Boa (Documentation / DX)

**Score:** 9.4 / 10
**Grade:** EXCEEDS
**Delta vs v4.154.0:** +0.1

## Summary

Both MEDIUM carry-forwards from v4.154.0 are confirmed closed. Bo.12-table
(README benchmark table) and Bo.12-i18n (localized README sync) were
addressed in v5.0.6 and verified in this review. The retracted "1.12x Rust"
and "v4.125.0" table data are gone from every README. The localized READMEs
are synced with correct "168x" headline numbers and 5720+ test badges. The
new `docs/guides/packages.md` is well-structured, covers the full
publish/install/auth workflow, and is the kind of guide you want to exist
on day one of a package registry. Eleven SESSION_REPORTs across the arc
maintain the exemplary quality established in the perf arc.

That said, the arc introduced three new documentation correctness issues
that prevent me from going higher: the README claims "strict 3-stage fixed
point" when the fixed point is actually BROKEN (In.1-stage2); the
`known_issues.md` Ecosystem table still says "No package manager yet" when
v5.2.0 just shipped one; and the localized READMEs (zh-CN, pt) have version
badges at 5.0.6 while the English README and `docs/README.es.md` are at
5.2.0. These are not hard to fix, but they are factual contradictions
visible to users right now.

## What improved since v4.154.0

- **Bo.12-table CLOSED (v5.0.6).** The README benchmark table that showed
  stale v4.125.0 pre-correction Rust data is gone. The entire benchmarks
  section was redesigned into a clean geomean summary table at lines
  128-137. `grep 'v4.125.0' README.md` returns 0. The old contradictory
  "headline moment (v4.124.0)" paragraph is also gone. The prose and table
  now agree. Beautiful cleanup.

- **Bo.12-i18n CLOSED (v5.0.6).** All three localized READMEs were synced
  at v5.0.6. `grep '1.12' docs/README.es.md` returns 0. `grep '5160'
  docs/README.es.md` returns 0. The retracted benchmark claims that I
  flagged at v4.144.0 and again at v4.154.0 are finally gone from every
  language variant. The Spanish README was further bumped to 5.2.0 in
  the v5.2.0 release. Two-cycle MEDIUM resolved.

- **Package guide is excellent.** `docs/guides/packages.md` (189 lines)
  covers: quick start, `mapanare.toml` schema with a field table, semver
  constraint syntax table (6 rows, each with meaning + example), install
  from registry / from git / from lockfile, SHA-256 verification
  explanation, lockfile format with example JSON, authentication flow
  (GitHub OAuth + token persistence), publish workflow with bump options,
  what-gets-published/excluded lists, search CLI, project scaffolding,
  registry API endpoint table, and environment variable overrides. This is
  a complete, well-organized guide. It reads like a mature package manager's
  documentation, not an MVP afterthought. The only missing piece is a
  troubleshooting section (e.g., "what if SHA-256 fails", "what if the
  registry is down"), which is reasonable to defer.

- **README redesign.** The English README was substantially redesigned
  between v4.154.0 and v5.2.0. The old wall of benchmarks, roadmap tables,
  and architecture diagrams was replaced with a clean, modern README
  (178 lines vs ~450 previously). The new structure (Install / Hello World /
  Write Python Compile Native / Language Features / Benchmarks / Build from
  Source / Contributing / License) is exactly right for a front door. The
  Python-to-native table with 5 real scripts and measured speedups is
  compelling. The code sample shows agents, signals, streams, pattern
  matching, and AI stdlib in one block. This is the best README this
  project has ever had.

- **SESSION_REPORT quality holds.** All 11 SESSION_REPORTs in the arc
  are present and structured. v5.0.4 includes a sret count pre/post table.
  v5.0.6 includes verification commands for every closure. v5.1.0 shows
  the actual codegen diff (inline GEP vs opaque call). v5.1.4 narrates
  the lazy-thread design with numbered invariants and a race-safety
  argument. v5.2.0 documents the registry API endpoints, files changed,
  deferred items, and test results. The quality is consistently high.

- **Test count.** Tests badge at 5720+ (README line 28), matching the
  v5.0.6 SESSION_REPORT claim. MEASUREMENTS.md reports 5445 collected
  in pytest, so "5720+" likely includes parametrize expansion or a
  recent addition. The delta direction is correct (up from 5302+ at
  v4.154.0).

- **Bo.13 CLOSED (implicit).** The old roadmap table that was missing
  v4.144.0-v4.153.0 rows is gone entirely. The README redesign removed
  the roadmap table in favor of linking to `docs/roadmap/ROADMAP.md`.
  This is the correct fix — the README should not contain a 40-row
  version history table.

- **Bo.14 partially addressed.** `known_issues.md` footer was bumped
  from v4.143.0 to v4.155.0 (line 3 and line 53). `getting_started.md`
  still says v4.143.0 for the golden test count (line 188) and "5,160+"
  for test count (line 236), both stale but not wrong in direction.

## What concerns me

### Bo.15: README "strict 3-stage fixed point" is factually wrong (MEDIUM)

README line 134:

```
The self-hosted compiler compiles itself to a strict 3-stage fixed point.
```

MEASUREMENTS.md section 3 (the canonical evidence for this panel) says:

```
Status: BROKEN (regression from NEAR)
```

The fixed point regressed at v5.1.2 when the In.1 inliner was re-enabled.
`llvm-as` fails on stage2.ll with `use of undefined value '%_inl0_6_t4'`.
This is not "strict" — it is not even "near." The README is making a
factual claim that contradicts the project's own measurement evidence.

The claim was accurate at v4.134.0 (first strict fixed point) and
approximately accurate through v4.154.0 (NEAR, 4-line version-metadata
diff). But v5.1.2 broke it, and the README was not updated.

A user who reads "strict 3-stage fixed point" and then runs
`bash scripts/verify_fixed_point.sh` will get an `llvm-as` error.
That is the definition of a misleading claim.

**Fix:** Change to "The self-hosted compiler compiles itself (stage2
blocked by In.1-stage2 inliner regression; strict fixed point reached
at v4.134.0, recovery tracked)" — or, if the lead prefers brevity,
simply remove the fixed-point sentence until it is restored.

Estimated effort: **5 minutes.**

Filing as **Bo.15** (MEDIUM) — factual inaccuracy on the front door.

### Bo.16: known_issues.md says "No package manager yet" (MEDIUM)

`docs/known_issues.md` line 33:

```
| -- | No package manager yet | pin `mapanare.toml` deps by git SHA | v5.x ecosystem |
```

v5.2.0 just shipped a package registry MVP with `mapanare install`,
`mapanare publish`, SHA-256 verification, lockfile support, and 51 tests.
The known-issues page tells users the feature does not exist.

**Fix:** Either remove the row or replace it with "Package registry is
team-only for MVP; open publishing tracked for v5.3+" to accurately
reflect the current state.

Estimated effort: **2 minutes.**

Filing as **Bo.16** (MEDIUM) — user-visible factual contradiction.

### Bo.17: Localized README version badge drift (zh-CN, pt at 5.0.6) (LOW)

The v5.2.0 SESSION_REPORT says it bumped `README.md` and
`docs/README.es.md` version badges to 5.2.0. Verified:

| File | Version badge | Current? |
|---|---|---|
| `README.md` | 5.2.0 | Yes |
| `docs/README.es.md` | 5.2.0 | Yes |
| `docs/README.zh-CN.md` | **5.0.6** | No (12 releases behind) |
| `docs/README.pt.md` | **5.0.6** | No (12 releases behind) |

The Spanish README was bumped in the v5.2.0 release, but the Chinese
and Portuguese copies were not. This is the same partial-sync pattern
that created Bo.12-i18n — only some localized files are updated.

The test badges (5720+) and headline numbers (168x, etc.) are correct
across all four READMEs. Only the version badge is stale on zh-CN and pt.

**Fix:** `sed -i 's/5.0.6/5.2.0/g'` on the two files.

Estimated effort: **2 minutes.**

Filing as **Bo.17** (LOW) — cosmetic badge, no content error.

### Bo.14r: getting_started.md stale counts (LOW, residual)

`docs/guides/getting_started.md` line 188 still says "As of v4.143.0"
and line 236 still says "5,160+ tests." Both are now 12+ releases behind.
The 54/66 golden count is still accurate, and the 5,160+ is directionally
correct (the actual count is higher), so this is a staleness issue, not
a factual error.

**Fix:** Update "v4.143.0" to "v5.2.0" and "5,160+" to "5,720+".

Estimated effort: **2 minutes.**

Filing as **Bo.14r** (LOW) — residual of Bo.14 from v4.154.0.

### Lint regression is a DX process concern (observation, not filing)

MEASUREMENTS.md reports 4 files need `black` and 9 `ruff` errors in the
v5.2.0 registry code. The v5.2.0 SESSION_REPORT does not mention lint
status at all. This means registry code was committed without running
`make lint` — the pre-push validation step documented in CLAUDE.md.

I am not filing a docket for this because it is a one-time process skip,
not a documentation gap. But I note it because developer experience
includes process discipline: if the project documents "run `dev.ps1`
before ANY commit" and then ships a release that fails `black --check`,
that erodes trust in the documented workflow. The fix is mechanical
(`black` + `ruff --fix` on 4 files), but the lead should be aware that
CI will fail on this commit.

## Bo.* summary table (v4.154.0 -> v5.2.0)

| ID | v4.154.0 status | v5.2.0 status | Notes |
|---|---|---|---|
| Bo.1 | CLOSED | CLOSED | content accurate, footer bumped to v4.155.0 |
| Bo.2 | CLOSED | CLOSED | native-mode prereqs intact |
| Bo.3 | CLOSED | CLOSED | merge note intact |
| Bo.4 | CLOSED | CLOSED | Tests badge 5720+ (current) |
| Bo.5 | CLOSED | CLOSED | structural fix |
| Bo.6 | CLOSED | CLOSED | golden count 54/66 still accurate |
| Bo.7 | REGRESSED | **CLOSED** | localized READMEs synced at v5.0.6 |
| Bo.8 | CLOSED | CLOSED | SPEC header 4.143.0 (correct — no spec changes in arc) |
| Bo.9 | MOOT | MOOT | factual historical text |
| Bo.10 | CLOSED | CLOSED | footers updated |
| Bo.11 | CLOSED | **REGRESSED** | README says "strict" when fixed point is BROKEN (Bo.15) |
| Bo.12-table | OPEN (MEDIUM) | **CLOSED** | v5.0.6 — benchmark section redesigned |
| Bo.12-i18n | OPEN (MEDIUM) | **CLOSED** | v5.0.6 — all localized READMEs synced |
| Bo.13 | OPEN (LOW) | **CLOSED** | README redesign removed roadmap table entirely |
| Bo.14 | OPEN (LOW) | **PARTIALLY CLOSED** | known_issues footer bumped; getting_started stale (Bo.14r) |

**Two MEDIUM closures (Bo.12-table, Bo.12-i18n). One MEDIUM regression
(Bo.11 -> Bo.15). One new MEDIUM (Bo.16). One new LOW (Bo.17). One
residual LOW (Bo.14r).**

## Carry-forward (for v5.3.0+)

| ID | Severity | Scope | Effort |
|---|---|---|---|
| Bo.15 | MEDIUM | README claims "strict 3-stage fixed point" — actually BROKEN since v5.1.2 | 5 min |
| Bo.16 | MEDIUM | known_issues.md says "No package manager yet" — v5.2.0 shipped one | 2 min |
| Bo.17 | LOW | zh-CN and pt README version badges at 5.0.6 (should be 5.2.0) | 2 min |
| Bo.14r | LOW | getting_started.md says "v4.143.0" and "5,160+" — 12 releases stale | 2 min |

**Total estimated effort: 11 minutes.** Two MEDIUM, two LOW.

## Score rationale

| Driver | Delta |
|---|---|
| Bo.12-table CLOSED — two-cycle MEDIUM resolved, benchmark section redesigned beautifully | +0.15 |
| Bo.12-i18n CLOSED — localized READMEs synced, retracted claims gone from all languages | +0.15 |
| Bo.13 CLOSED — roadmap table removed via README redesign | +0.05 |
| Package guide: complete, well-organized, covers full workflow | +0.10 |
| README redesign: clean, modern, compelling front door | +0.10 |
| 11 SESSION_REPORTs, consistently high quality | +0.05 |
| Bo.15 NEW: README "strict 3-stage fixed point" is factually BROKEN | -0.20 |
| Bo.16 NEW: known_issues says "No package manager" when v5.2.0 shipped one | -0.15 |
| Bo.17 NEW: zh-CN/pt version badges at 5.0.6 (partial sync regression) | -0.05 |
| Bo.14r: getting_started.md still stale (residual) | -0.05 |
| Lint regression: registry code committed without black/ruff | -0.05 |
| **Net** | **+0.10** |

**9.3 -> 9.4. Grade: EXCEEDS.** Fourth consecutive EXCEEDS.

## Why not 9.5+

At v4.154.0 I said: "Clear Bo.12 and I am at 9.5+ for the next panel."
Bo.12 IS cleared, and the package guide and README redesign are genuinely
excellent work. But two new MEDIUM findings prevent me from delivering
on that promise.

Bo.15 is a factual inaccuracy on the README. The project says "strict
3-stage fixed point" — and the evidence document for this very panel says
"BROKEN." That is a front-door credibility issue. It was not a deliberate
misrepresentation; the In.1 inliner re-enable at v5.1.2 broke the fixed
point and the README was not updated. But the result is the same: a user
who reads the README and tries to verify the claim will fail.

Bo.16 is a content contradiction in the known-issues page. Shipping a
package registry and then leaving "No package manager yet" in the
known-issues table is the kind of oversight that makes users question
whether the docs are maintained.

Both are 5-minute fixes. But they exist today, and I grade what I see.

The +0.10 net delta reflects the genuine improvements (two two-cycle
MEDIUMs closed, a beautiful README redesign, an excellent package guide)
balanced against two new MEDIUMs that are smaller in scope but higher
in visibility than the ones they replaced.

## Reproducibility

```bash
# Bo.12-table CLOSED:
grep 'v4.125.0' README.md
# Expected: no output

# Bo.12-i18n CLOSED:
grep '1.12' docs/README.es.md
# Expected: no output
grep '5160' docs/README.es.md
# Expected: no output

# Bo.15 — README claims strict fixed point:
grep 'strict 3-stage fixed point' README.md
# Expected: line 134
grep 'BROKEN' docs/roadmap/v5/v5.3.0/MEASUREMENTS.md
# Expected: line 93 "Status: BROKEN"

# Bo.16 — known_issues claims no package manager:
grep 'No package manager' docs/known_issues.md
# Expected: line 33

# Bo.17 — version badge drift:
grep '5.0.6' docs/README.zh-CN.md docs/README.pt.md
# Expected: version badge lines

# Bo.14r — getting_started stale:
grep 'v4.143.0' docs/guides/getting_started.md
# Expected: line 188
grep '5,160' docs/guides/getting_started.md
# Expected: line 236

# Package guide exists:
wc -l docs/guides/packages.md
# Expected: 189

# Session reports complete:
ls docs/roadmap/v5/*/SESSION_REPORT.md | wc -l
# Expected: 11
```

## One last note to the lead

The README redesign is the single most impactful documentation change in
the project's history. Going from a 450-line wall of version history,
architecture diagrams, and benchmark tables to a 178-line clean front
door with Install / Hello World / Python-to-Native / Features /
Benchmarks / Build is exactly right. The Python-to-native table is
killer marketing — real scripts, real numbers, real speedups. The code
sample is perfectly chosen. This is the README of a project that knows
what it is.

The package guide is equally impressive. Most MVP package managers ship
with a "run this command" README. You shipped a complete guide with
schema tables, constraint syntax, lockfile format, auth flow, publish
options, and API reference. That is the quality of documentation that
makes adopters trust a tool.

The two new MEDIUMs are both trivial to fix — update one sentence in
the README, delete one row in known_issues. Eleven minutes of work for
all four carry-forwards. Do that and I am at 9.6 for the next panel.
The README redesign and package guide have raised the ceiling.

Grade: **9.4 / EXCEEDS.** Fourth consecutive EXCEEDS. Highest Boa score
in the project's history (9.1 -> 9.3 -> 9.4). Earned through two-cycle
MEDIUM closures, a transformative README redesign, and an excellent
package guide — tempered by two small but visible factual contradictions.
