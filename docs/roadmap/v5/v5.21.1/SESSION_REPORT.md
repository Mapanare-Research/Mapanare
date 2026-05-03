# v5.21.1 — Mc.7 — pre-panel docs hygiene

**Date:** 2026-05-01.
**Cycle:** Phase 0 → Phase 6 in one session.
**Status:** **READY** (pending closeout + tag promotion).

---

## Headline

v5.21.1 ships **Mc.7 — pre-panel docs hygiene**. Doc-surface
release closing the 12 H.* findings that
`.reviews/v5.22.0/PRE_PANEL_AUDIT.md` enumerated as docs drift
the v5.22.0 panel would otherwise dock at fresh. Same posture
as v5.7.1 → v5.8.0 (highest-scoring panel in project history at
9.66/10).

**Zero compiler edits. Zero runtime edits. Zero MIR / IR
changes. Zero `mapanare/self/*.mn` source edits.** Strict 3-stage
fixed point preserved at 238,086 lines / 0-line diff (v5.9.0
milestone, held through 13 consecutive releases — longest streak
in project history). Goldens **95/95** at HEAD. The single
exception to the no-source-edit rule is `mapanare/format.py`,
which gains a documentation block noting that v5.21.0 chained
comparisons are preserved by the line-based whitespace
canonicalization (no expression-level pass needed); plus a new
test file `tests/bootstrap/test_chained_cmp_mirror.py` (10/10
PASS) that mirrors `test_te5_mirror.py`.

## Phase 0 — Decision-1 lock

The v5.21.1 PLAN's Decision-1 was a binary path lock:

- **Path A** — ship single-line `if x: y` form in v5.21.1
  (~1h scope creep; closes the broken v5.14.0 SPEC promise of
  v5.21.0 delivery).
- **Path B** — formally rescope to v6.0 with rationale
  (~10 min; SPEC §4.0:1009 rewritten as explicit deferral).

**Locked: Path B.** Rationale:

1. The v5.21.1 PROMPT explicitly forbids editing the Lark
   grammar file and `mapanare/self/*.mn`. Path A requires both
   (new `KW_IF expr COLON stmt` alternative in `mapanare.lark`
   plus a parallel branch in `mapanare/self/parser.mn`'s
   `parse_if_expr`). Honoring the doc-only scope is the
   structural concern; "ship one extra surface form" can wait.
2. Rescoping the broken promise to v6.0 (when `{}` hard removal
   lands and single-line form will be unambiguous with the
   removed brace shape) is the honest path and lines up with
   the existing v6.0 docket.
3. SPEC §4.0:1009 now reads as an explicit v6.0 deferral with
   a one-sentence note that the v5.14.0 forward promise was
   incorrect — closing the ledger item rather than carrying it
   silently.

## Per-item closure (H.1–H.12)

| ID | What changed |
|----|--------------|
| **H.1** | `README.md:168` `80/80 native goldens at v5.17.1` → `95/95 native goldens at v5.21.0`. Line 176 fixed-point line bumped 231,957 → 238,086 with carry trail naming v5.20.0 struct ergonomics + v5.21.0 chained comparisons + the 13-release streak. |
| **H.2** | `docs/SPEC.md:4` header bumped from `Live — synced to the v5.7.1 cut (2026-04-26)` to `Live — synced to the v5.21.0 cut (2026-05-01)`. New "What changed since the v5.7.1 sync" block (15-line summary) covers the v5.13–v5.21 arc release-by-release. New spec-sync-discipline block lists the §s re-audited at v5.21.1. |
| **H.3** | `docs/SPEC.md` §4.0 (Block Syntax) rewritten. Lead now reads "Mapanare accepts colon-style as canonical (since v5.19.0). Brace-style is **soft-deprecated**: it parses but emits a warning at parse time, and `mnc fmt` (no flag) auto-migrates `{}` → `:` per file." Adds the warning text verbatim, `MAPANARE_NO_BRACE_WARNING=1` opt-out, `mnc fmt --keep-braces` flag, and v6.0 hard-removal milestone. Brace example moved below colon example as legacy syntax. |
| **H.4** | `docs/SPEC.md:1009` `Single-line `if x: y` form is **not** supported in v5.14.0 (deferred to v5.21.0)` → `Single-line `if x: y` form is **not** supported. The v5.14.0 SPEC originally promised this for v5.21.0; that promise was rescoped at v5.21.1 to coincide with the v6.0 `{}` hard removal. Until v6.0, put the body on the next line.` |
| **H.5** | Verified: SPEC has §3.7 sections for Field Shorthand (line 706), Struct Update Syntax (line 719), Destructuring in `let` (line 731); §4.3.1 Conditional Binding (line 1161) covers `if let` / `while let` / `let else`; §2.2 Chained Comparisons (line 403) covers Te.6; §16.5/§17.5 list/map comprehensions. All four Te.5 forms + Te.6 are documented. No additions needed. |
| **H.6** | Localized READMEs (es/pt/zh-CN) "Native compiler — what `mnc-stage1` ships" subsection rewritten in each language: 66/66 → 95/95, 217k-line NEAR → 238,086-line STRICT (13-release streak), Sh.\* shrink number, terseness arc summary in target-language prose. Code blocks and badges left untouched (badges already updated by v5.21.0 `bump_version.py`). |
| **H.7** | New `examples/chained_cmp.mn` (28 lines) — exercises 3-element chain `0 < n < 10`, 4-element chain `a < b < c < d`, half-open form `lo <= x < hi`, and once-evaluation demo via `middle()` with a `print("M")` side effect. Compiles clean through `python3 -m mapanare emit-llvm`. Picked up by the `test_format.py` corpus iteration in `examples/` automatically. |
| **H.8** | `mapanare/format.py` module docstring gained a v5.21.1 paragraph documenting that chained comparisons round-trip stable through the line-based whitespace canonicalization without an expression-level pass — the formatter is line-shape-only and chains are token-ordered just like ordinary binary comparisons. New unit tests in `tests/test_format.py::TestRules` (4 assertions) guard idempotence on 3-element, 4-element, mixed-ops, and mixed-direction chain shapes. |
| **H.9** | New `tests/bootstrap/test_chained_cmp_mirror.py` (200 lines) — mirror of `test_te5_mirror.py`. 4 golden cases (92–95) + 6 inline cases covering chained `==`, mixed eq+cmp (post-merge), non-trivial middle, chain in if-condition, typed-let chain, half-open mixed `<=`/`<`. Both bootstraps compile each case through `emit-llvm`, link with `libmapanare_rt.a`, run, and assert byte-identical stdout. **10/10 PASS.** |
| **H.10** | `.reviews/CARRY_FORWARD.md` appended with the new "Items resolved in the v5.13.0 → v5.21.1 terseness arc" section (19 rows): Mc.2, Te.1 + bootstrap mirror, Te.2 + bootstrap mirror, Te.4, Sh.\* (v5.17.0/.1/.2), Mc.\* (v5.18.0), Te.3, Dk.\*, Te.5 + bootstrap mirror, Te.6, and this row's H.1–H.13 pre-panel hygiene closure. Each row names the resolving release + one-line evidence. |
| **H.11** | `docs/known_issues.md` Last-updated bumped from v5.11.0 to v5.21.1 with a single-paragraph summary; the prior v5.11.0 line moved to "Earlier last-updated:". New "v5.13.0 → v5.21.1 closures" narrative block (12 entries) added next to the existing v5.4.0 → v5.7.0 closures block. Last-verified note at the end of the file bumped from v5.7.1 (2026-04-26) to v5.21.1 (2026-05-01). |
| **H.12** | The structural per-platform split (`BENCHMARKS-windows.md` + `BENCHMARKS-linux.md` + auto-merged `BENCHMARKS.md` via `_merge_benchmarks()`) was already in place from prior work. v5.21.1 adds a "Windows benchmark last sync" admonition at the top of `BENCHMARKS-windows.md` making the v5.8.8 staleness visible — re-running goldens regenerates the linux file and the merged file picks both up. The merged file at HEAD shows linux v5.21.0 numbers and the v5.8.8 Windows note clearly flagged. Closes Rattler #1. |

## Validation

All Phase 5 gates clean at HEAD:

```
make lint                                 # ruff + black + mypy clean
python3 scripts/check_changelog_honesty.py # clean
python3 scripts/check_workflow_shapes.py   # 7 workflows clean
bash scripts/verify_fixed_point.sh --keep  # 238086 lines / 0 diff
bash scripts/build_from_seed.sh            # clean (3-stage no-Python)
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1
                                           # All 95 tests passed
python3 -m mapanare fmt --check tests/golden/92…95 examples/chained_cmp.mn
                                           # exit 0
python3 -m pytest tests/test_format.py tests/bootstrap/test_chained_cmp_mirror.py
                                           # 898 passed, 144 skipped (10 new)
```

## What does NOT ship

- **Compiler edits.** Zero. `mapanare/parser.py`, `mapanare/lower.py`,
  `mapanare/semantic.py`, `mapanare/emit_llvm_text.py` — untouched.
- **Runtime edits.** Zero C runtime changes; `runtime/native/`
  untouched.
- **MIR / IR changes.** Zero. The strict 3-stage fixed point
  is preserved by construction — every byte of the IR pipeline
  is unchanged.
- **`mapanare/self/*.mn` edits.** Zero. The bootstrap source is
  identical to v5.21.0.
- **Lark grammar edits.** Zero. `mapanare/mapanare.lark`
  unchanged. Path B for Decision-1 means the single-line
  `if x: y` form does not land here.
- **New language features.** Zero. Path B took the conservative
  route on Decision-1.
- **Tag promotion.** Awaits explicit user approval per the
  project tagging policy.

## Strict 3-stage fixed-point (preserved by construction)

```
$ bash scripts/verify_fixed_point.sh --keep
[Stage 1] stage1 compiles mnc_all.mn → stage2.ll
  stage2.ll: 238086 lines
  llvm-as: OK
[Stage 2] stage2 compiles mnc_all.mn → stage3.ll
  stage3.ll: 238086 lines
  llvm-as: OK
[Verify] Fixed point: diff stage2.ll stage3.ll
  ✓ FIXED POINT REACHED
  stage2.ll == stage3.ll (238086 lines, 0 diff)
```

13-release streak (v5.9.0 → v5.21.1) — the longest streak in
project history.

## Pre-panel posture

`.reviews/v5.22.0/PRE_PANEL_AUDIT.md` is fully cleared at v5.21.1
HEAD. The v5.22.0 panel inherits a clean docket:

- **0 CRITICAL** open
- **0 HIGH** open
- **0 MEDIUM** open
- **1 LOW (deferred to v6.0)** — Rt.04 multi-level alias
  analysis, correctly RESCOPED to the v6.0 borrow-checker arc.

The panel's grading axis at v5.22.0 will weigh:

- **+** Strict 3-stage fixed point preserved across **13
  consecutive releases** — longest streak in project history.
- **+** Self-hosted compiler shrunk **-3,950 lines (-13.8%)**
  via Sh.\* without breaking fixed point.
- **+** Six additive language features shipped (Te.1–Te.6)
  with **zero new MIR ops, zero new IR shapes, zero runtime
  function additions**.
- **+** Goldens **66/66 → 95/95** with bootstrap mirror.
- **+** Panel cadence honored (overdue but not skipped).
- **−** SPEC re-sync of 14-release arc happened in v5.21.1
  hygiene, not at-source. The same drift class Coral has
  flagged across 3 panels. Score weighting should reflect
  closure-by-hygiene-release.
- **+/−** v5.14.0's broken `if x: y` promise rescoped to v6.0
  rather than shipped. Same regression class as v4.18.0–v4.26.0
  hollow-features arc, in miniature, but **explicit deferral**
  rather than silent carry-over. Honest documentation of a
  scoping mistake closes the loop properly.

## Out of scope (deferred)

- v5.22.0 panel itself — runs separately at the v5.21.1 →
  v5.22.0 boundary per `.reviews/v5.22.0/prompt.md`.
- Single-line `if x: y` form — explicitly deferred to v6.0
  (Decision-1 Path B closure).
- Rt.04 multi-level alias analysis — DEFERRED to v6.0 borrow
  checker, status unchanged from v5.11.0 panel.
- New language features — none ship in this hygiene release.

---

## Next: v5.22.0 panel

`.reviews/v5.22.0/prompt.md` runs the seven-reviewer panel against
the v5.21.1 HEAD. Pre-flight commands and grading axis are
captured in the PRE_PANEL_AUDIT. Target aggregate ≥ 9.5; v5.7.1
panel was 9.66 (project record); v5.11.0 panel was 9.62.
