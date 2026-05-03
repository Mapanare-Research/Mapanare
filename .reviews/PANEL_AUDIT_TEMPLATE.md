# vX.Y.Z Pre-Panel Audit (TEMPLATE)

> Copy this template to `.reviews/vX.Y.Z/PRE_PANEL_AUDIT.md` before
> each panel cycle. Fill in `H.*` findings; bind each to the
> prior-panel finding ID it closes (or "(none — fresh)").
>
> Convention added at v5.24.1 (Wd.8) per Boa Bo.27 — when the
> pre-panel audit doesn't bind to panel-finding IDs, hygiene-release
> closures patch what the audit cites and walk past the panel-flagged
> shape. Bo.18r persisted across 3 consecutive panels (v5.7.1 /
> v5.11.0 / v5.22.0) under that failure mode. The "Closes prior-panel
> finding" column makes the cross-walk visible at a glance.

---

## How to fill this out

1. **Survey the prior-panel docket.** Open every reviewer file at
   `.reviews/v<prior>.0/0N-<reviewer>.md` and `.reviews/CARRY_FORWARD.md`
   and enumerate the open findings (HIGH / MEDIUM / LOW).
2. **For each finding the lead's audit pass surfaces, identify whether
   it closes a prior-panel finding.** Cite the prior-panel ID exactly
   (`Bo.18r`, `V.9`, `Co.M2`, `Ra.1`, `An.3`, `Ma.4`, `Cb.5`). If the
   audit finding is fresh, write "(none — fresh)" — that is honest and
   acceptable.
3. **For each prior-panel finding the audit does NOT plan to close,
   list it explicitly in the "deferred" section** with a target
   release. This prevents silent drop-through.

The hard rule: **every prior-panel HIGH and MEDIUM either appears in
the H.\* table (with its prior-panel ID cited) or appears in the
"deferred to <future release>" section.** No third option.

---

## Findings to clear in vX.Y.(Z-1) hygiene release

### Doc surface (Boa axis)

| # | Severity | Finding | **Closes prior-panel ID** | Closed in vX.Y.(Z-1) |
|---|---|---|---|---|
| H.1 | HIGH | <line/file claim, e.g. README.md:188 stale fixed-point line> | `Bo.18r` (v5.7.1 / v5.11.0 / v5.22.0) | <evidence pointer, e.g. line rewritten to v5.X.Y status> |
| H.2 | HIGH | <claim> | (none — fresh) | <evidence> |

### SPEC surface (Coral axis)

| # | Severity | Finding | **Closes prior-panel ID** | Closed in vX.Y.(Z-1) |
|---|---|---|---|---|
| H.3 | MEDIUM | <claim> | `Co.M3` (v5.22.0) | <evidence> |

### Bootstrap / fixed-point surface (Cobra / Rattler axis)

| # | Severity | Finding | **Closes prior-panel ID** | Closed in vX.Y.(Z-1) |
|---|---|---|---|---|
| H.4 | MEDIUM | <claim> | `Ra.2` (v5.11.0) | <evidence> |

### Process surface (Anaconda / Mamba axis)

| # | Severity | Finding | **Closes prior-panel ID** | Closed in vX.Y.(Z-1) |
|---|---|---|---|---|
| H.5 | MEDIUM | <claim> | `An.5` (v5.22.0) | <evidence> |

### Memory / runtime surface (Viper axis)

| # | Severity | Finding | **Closes prior-panel ID** | Closed in vX.Y.(Z-1) |
|---|---|---|---|---|
| H.6 | MEDIUM | <claim> | `V.9` (v5.22.0) | <evidence> |

---

## Prior-panel findings deferred (NOT closed by hygiene release)

| Prior-panel ID | Severity | Reason for deferral | Target release |
|---|---|---|---|
| `Pk.1.A` (v5.10.0) | LOW | <reason> | <vX.Y.Z> |

If this section is non-empty, every entry MUST cite a target release
(don't carry silently). If the target release subsequently slips, the
next pre-panel audit must re-surface the item with an updated target.

---

## Pre-flight commands

These commands establish the live state of the codebase before the
panel reviewers receive their packages. Run each and capture output
in this audit file as the live snapshot.

```bash
# Strict 3-stage fixed point
bash scripts/verify_fixed_point.sh --keep
# expected: stage2.ll == stage3.ll, N lines, 0 diff

# Native goldens
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1
# expected: 95/95 (or current corpus size)

# CI gates (Hy.* infrastructure, v5.24.0+)
make ci-gates
# expected: All gates GREEN

# Brace-deprecation detector (Te.3 surface, v5.19.0+)
echo 'fn main() { print("hi") }' > /tmp/brace_oneline.mn
python3 -m mapanare emit-llvm /tmp/brace_oneline.mn 2>&1 | grep warning
# expected: warning fires (post-v5.23.2 Te.3.B)

# Cadence check
python3 scripts/check_cadence.py
# expected: OK or OVERDUE with explicit minor-count
```

If any baseline fails, the audit MUST flag it as H.\* and the
hygiene release MUST close it before panel.

---

## Process observation

The "Closes prior-panel finding" column is **mandatory at every
audit**. If a current panel-flagged finding is not in the H.\* table
because the lead's self-audit didn't surface it, that's the v5.22.0
Bo.18r failure pattern — the audit should cross-reference the entire
prior-panel docket as the first pass before identifying new H.\*
items.

A panel review that catches a missing prior-panel-ID column on this
template is doing exactly what Bo.27 was filed to make easy.
