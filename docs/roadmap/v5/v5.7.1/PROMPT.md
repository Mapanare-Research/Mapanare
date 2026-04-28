# v5.7.1 Execution Prompt — SPEC + docs polish (pre-panel)

> Read `PLAN.md` first. Final docs/SPEC refresh before the v5.8.0
> re-panel. With 66/66 goldens (v5.7.0) and Ve.* / Sh.* / Rt.* /
> Own.1 Phase 2 closures behind us, the SPEC + README + known_issues
> need to reflect the full feature surface. Add a culebra clean
> baseline and a `docs/guides/culebra.md` guide so v5.8.0 panelists
> have structured diagnostic input.
>
> Estimated: 1–2 hours total. Pure docs/polish — no compiler edits.

---

## Read before starting

1. `docs/roadmap/v5/v5.7.1/PLAN.md` — this release's plan.
2. `docs/roadmap/v5/v5.7.0/SESSION_REPORT.md` — the 66/66 milestone.
3. `docs/SPEC.md` — current header version + sections to refresh.
4. `README.md` + `docs/README.{es,pt,zh-CN}.md` — badge + features list.
5. `docs/known_issues.md` — items to prune.
6. `docs/roadmap/v5/PARITY_GAPS.md` — verify Historical section.
7. Every per-release `culebra-journal.jsonl` from v5.6.9 → v5.7.0
   (5 files; aggregate into `arc-journal.jsonl`).
8. `.claude/skills/culebra-scan/SKILL.md` — used as primary input
   for the new `docs/guides/culebra.md`.

---

## Environment

Either WSL or Windows works. SPEC + README edits are docs-only.
Drop into WSL only for the culebra commands in Phase 3.

---

## GitNexus pre-flight

Skip — no compiler edits this release. Run `npx gitnexus analyze`
at end of session to keep the index fresh.

---

## Phase 0 — Version bump (~5 min)

```bash
echo "5.7.1" > VERSION
git add VERSION
git commit -m "v5.7.1: version bump — SPEC + docs polish"
```

---

## Phase 1 — SPEC refresh (~1 hour)

Bump `docs/SPEC.md`:

```diff
-Version: v5.4.143
+Version: v5.7.1
```

Walk every section. Verify text reflects the v5.4.0–v5.7.0
feature additions:

| Section | What to verify |
|---|---|
| §3 Type System | Tensor + Closure-typed param + Or-pattern bindings |
| §4 Pattern Matching | or-pattern with guards |
| §6 Async / Concurrency | Coroutine + scheduler + `block_on` (v5.5.x) |
| §7 Memory Model | Drop glue + ownership tracking (v5.4.0–v5.4.4) |
| §8 Tensor | Multi-dim indexing, broadcast, slicing, reductions (v5.6.x) |
| §11 Self-hosting | 66/66 goldens; strict/near fixed-point |
| §30 Package Management | Already polished v5.3.3 — verify still accurate |

Add a one-line note at the top:

> v5.7.1 — SPEC reflects native goldens 66/66 (v5.7.0) and
> self-host fixed-point restored (v5.6.9).

---

## Phase 2 — README + known_issues cleanup (~30 min)

### 2.1 README badges

Verify `README.md` and 3 translations show:
- Goldens: **66/66**
- Build status: green
- Self-host fixed-point: NEAR/STRICT

### 2.2 Feature list

Add to README "Native compiler features":
- Tensor literals + multi-dim indexing + broadcast + slicing + reductions
- Async / await / `block_on` via LLVM coroutines
- Closure-typed parameters
- Or-pattern matching with guards
- Drop-glue ownership tracking (string / list / boxed / tensor)

### 2.3 Known issues

Remove any entries closed in v5.4.0 → v5.7.0:
- Sh.4 (async) — closed v5.5.4–v5.5.7
- Sh.6 (tensor) — closed v5.6.0–v5.6.3
- Sh.7 (closure-typed) — closed v5.7.0
- B (or-pattern) — closed v5.7.0
- Ve.1 / Ve.2 / Ve.3 — closed v5.6.5 / v5.6.7 / v5.6.9
- Rt.03 / Rt.06 — closed v5.4.3 / v5.6.4

Update header "Last updated: v5.7.1".

### 2.4 PARITY_GAPS audit

Verify `docs/roadmap/v5/PARITY_GAPS.md` Historical section lists
every closure. Move any leftover Open items that are actually
closed.

---

## Phase 3 — Culebra clean baseline + arc journal (~30 min)

```bash
mkdir -p docs/roadmap/v5/v5.7.1/culebra

# Baseline against v5.7.0's stage2.ll (the 66/66 IR)
mapanare/self/mnc-stage1 mapanare/self/mnc_all.mn > /tmp/stage2.ll
culebra summary /tmp/stage2.ll \
    > docs/roadmap/v5/v5.7.1/culebra/summary.md
culebra triage /tmp/stage2.ll \
    > docs/roadmap/v5/v5.7.1/culebra/triage.md
culebra triage /tmp/stage2.ll --brief \
    > docs/roadmap/v5/v5.7.1/culebra/triage-brief.txt
culebra baseline save /tmp/stage2.ll \
    -o docs/roadmap/v5/v5.7.1/culebra/baseline-end.json

# Cross-reference health for the most-touched structs across the arc
for s in Value MIRType EmitState LowerState Instruction; do
    culebra health /tmp/stage2.ll --struct $s \
        > docs/roadmap/v5/v5.7.1/culebra/health-$s.txt
done

# Fixed-point under culebra
culebra fixedpoint mapanare/self/mnc_all.mn \
    --stage1 mapanare/self/mnc-stage1 \
    > docs/roadmap/v5/v5.7.1/culebra/fixedpoint.md

# Aggregate the per-release journals
cat docs/roadmap/v5/v5.6.9/culebra-journal.jsonl \
    docs/roadmap/v5/v5.6.10/culebra-journal.jsonl \
    docs/roadmap/v5/v5.7.0/culebra-journal.jsonl \
    > docs/roadmap/v5/v5.7.1/culebra/arc-journal.jsonl
wc -l docs/roadmap/v5/v5.7.1/culebra/arc-journal.jsonl
```

Compare against v5.6.10 baseline:

```bash
culebra baseline diff /tmp/stage2.ll \
    -b docs/roadmap/v5/v5.6.10/culebra/baseline-end.json \
    > docs/roadmap/v5/v5.7.1/culebra/baseline-delta-from-v5.6.10.md
```

Expected delta: closure-env structs (new, from v5.7.0); or-pattern
binding shapes (new, from v5.7.0); no critical findings.

---

## Phase 4 — `docs/guides/culebra.md` (~30 min)

Create a contributor guide for the culebra workflow Mapanare uses.
Source: `.claude/skills/culebra-scan/SKILL.md` + the v5.6.9–v5.7.0
session reports. Sections:

1. **What culebra is** — template-driven LLVM IR / generated C
   diagnostic engine. 49+ templates across ABI, IR, Binary,
   Bootstrap, C categories.
2. **Daily commands** — `triage`, `bisect`, `diff`, `compare`,
   `trace`, `inspect`, `fixedpoint`. Copy from SKILL.md §3.
3. **False positive policy** — `.culebra-ignore` + inline comments.
   List the 3 known FPs.
4. **Per-release journal** — `culebra journal add` discipline; the
   `culebra-journal.jsonl` per-release pattern v5.6.9+ uses.
5. **Panel input** — `culebra-journal.jsonl` aggregated to
   `arc-journal.jsonl` for the panel reviewers' input.
6. **Cross-reference**: v5.6.9 SESSION_REPORT for an end-to-end
   debugging example.

Cross-reference from `CLAUDE.md` (under "Skills" section) and from
the new contributor docs.

---

## Phase 5 — Commit (~10 min)

```bash
git add VERSION docs/SPEC.md \
    README.md docs/README.es.md docs/README.pt.md docs/README.zh-CN.md \
    docs/known_issues.md \
    docs/roadmap/v5/PARITY_GAPS.md \
    docs/roadmap/v5/v5.7.1/PLAN.md \
    docs/roadmap/v5/v5.7.1/PROMPT.md \
    docs/roadmap/v5/v5.7.1/SESSION_REPORT.md \
    docs/roadmap/v5/v5.7.1/culebra/ \
    docs/roadmap/v5/v5.7.1/culebra-journal.jsonl \
    docs/guides/culebra.md \
    CLAUDE.md docs/roadmap/ROADMAP.md

git commit -m "$(cat <<'EOF'
v5.7.1: SPEC + docs polish — pre-panel + culebra clean baseline

- SPEC refreshed to v5.7.1 (tensor / async / closure-typed / drop-glue
  sections updated)
- README 66/66 badge across 4 language variants
- known_issues.md pruned: Sh.4/6/7 + B + Ve.1/2/3 + Rt.03/06 closed
- PARITY_GAPS.md Historical section updated
- docs/guides/culebra.md published — contributor workflow + FP policy
- v5.6.9–v5.7.0 culebra-journals aggregated into arc-journal.jsonl
  (panel input for v5.8.0)
- v5.7.1 baseline.json saved as v5.8.0 panel anchor

No compiler edits. Pure docs/polish.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"

# Tag + push require explicit user approval
```

```bash
culebra journal add "v5.7.1 shipped: SPEC + docs polish; arc journal aggregated" \
    --action milestone --tags polish,pre-panel
cp ~/.culebra/journal.jsonl docs/roadmap/v5/v5.7.1/culebra-journal.jsonl
```

---

## Ready-to-ship checklist

- [ ] `VERSION` reads `5.7.1`
- [ ] `docs/SPEC.md` header version → 5.7.1; tensor/async/closure
      sections accurate
- [ ] `README.md` + 3 translations: 66/66 badge
- [ ] `docs/known_issues.md` pruned of all v5.4.0–v5.7.0 closures
- [ ] `PARITY_GAPS.md` Historical section complete
- [ ] `docs/guides/culebra.md` published, cross-referenced
- [ ] `docs/roadmap/v5/v5.7.1/culebra/baseline-end.json` saved
- [ ] `arc-journal.jsonl` aggregates 3+ release journals
- [ ] `culebra triage --brief` no NEW critical findings
- [ ] SESSION_REPORT written
- [ ] CLAUDE.md + ROADMAP.md entries added

---

## What NOT to do

- Do not bundle compiler edits. Pure docs/polish release.
- Do not skip the SPEC version bump.
- Do not invent new culebra workflow features in the docs guide —
  describe what the SKILL + v5.6.9–v5.7.0 session reports show.
- Do not delete v5.6.x entries from `docs/known_issues.md` if they're
  still active. Only prune CLOSED items.
- Do not tag without user approval.
