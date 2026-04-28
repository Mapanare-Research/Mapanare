# Mapanare v5.6.9 — "Ve.3 close — culebra-aided field-0 corruption diagnosis"

> **Close Ve.3 — the stage2 runtime OOM that v5.6.8 narrowed to a
> field-0-of-Value corruption on the third `Instruction::Alloca`
> emitted for `p1.mn`.** v5.6.8 ruled out hypotheses A (payload-type
> builder divergence) and D (Python emitter bug) and noted an
> adjacent struct_byte_size undercount that does NOT close the OOM.
> v5.6.9 drives the investigation with **culebra** as the primary
> diagnostic tool: bisect stage1 vs stage2, trace `%dest` through
> the chain, audit field indices for all internal structs, and
> identify whether the bug is at the LOWERER (corrupt MIR) or the
> EMITTER (bad load) — then fix it.

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v5.6.8 shipped (Ve.3 investigation; PLAN
hypothesis matrix narrowed). Culebra v3.0.0+ available
(`/home/uan/.cargo/bin/culebra`; templates 49+).
**Estimated work:** 1–2 sessions (~3–5 hours). The investigation
state is much tighter than v5.6.8's; the work is targeted.
**Owner docket:** Ve.3 (opened v5.6.7 after Ve.1+Ve.2 closure
narrowed blast radius; investigation expanded v5.6.8)

---

## Why this release exists

### The state at v5.6.8 close

```
[Stage 0] mnc-stage1: OK
[Stage 1] stage1 → stage2.ll: 207,619 lines, llvm-as OK
          mnc-stage2: builds, ~4.5 MB
[Stage 2] mnc-stage2 mnc_all.mn → stage3.ll: 0 lines (SIGSEGV)
          mnc-stage2 /tmp/p1.mn   → 0 lines (OOM)

DBG[1590] CORRUPT __mn_str_concat:
  a.ptr=0x830418 a.len=2     (= "  ")
  b.ptr=garbage  b.len=huge  (= dest.name on third Alloca)

emit_alloca eprint output (third call):
  dest.name.len=15  dest.name=[]  dest.ty.name=[Int]  dest.ty.kind=0
                          ↑ both reads see corrupt len, but data ptr
                            invalid so visible content is empty
```

`dest.ty` reads correctly (kind=TK_INT, name="Int") on all three
Alloca calls. **Only `dest.name` (Value's field 0, the first 16
bytes) is corrupt on the third call** — `len(dest.name)` returns
non-deterministic huge values across runs (uninitialised memory).

### What v5.6.8 ruled out

- **Hypothesis A** (payload-type builder divergence) — IR
  inspection showed both helpers produce
  `{ %struct.Value, %struct.MIRType }` for `Instruction::Alloca`.
- **Hypothesis D** (Python emitter bug) — `mnc-stage1-fromself`
  reproduces the OOM identically.

### Adjacent finding from v5.6.8

`struct_byte_size` undercounts named structs at 8 bytes (true: 80
for Value) due to two compounding bugs:
1. `register_internal_struct` pushes stub entries with
   `llvm_type="%struct.X"` (named form, not aggregate form).
2. `llvm_aggregate_size` counts ALL commas including those inside
   nested aggregates.

Patched `struct_byte_size` to delegate to `llvm_sizeof_st` →
correct sizes, stage2.ll +7%, **OOM persists**. The patch is
preserved as a candidate v5.6.10 hardening (after Ve.3 closes)
but not load-bearing for Ve.3.

### Active hypotheses for v5.6.9

#### Hypothesis E — Inliner produces corrupt third Alloca

`mir_opt::clone_instr_for_inline`'s Alloca branch (line ~917):
```mn
if ik == "alloca" {
    let new_dest: Value = rename_value(instr_dest(inst), prefix, renames)
    result.push(Instruction::Alloca(new_dest, instr_alloca_type(inst)))
    return result
}
```

`p1.mn` lowers to 2 explicit Allocas for `add`'s params, plus 2
inlined Allocas for `add` cloned into `main`. The third Alloca is
either the inliner's first cloned Alloca OR the lowerer's
post-inline param slot (depending on inline order).

`rename_value(v, prefix, renames)` constructs a new Value:
```mn
return new Value { name: new_name, ty: v.ty }
```

**Test E1**: log `dest.name` at the LOWERER side (in
`emit_instr` callers when `Instruction::Alloca` is constructed) to
confirm whether the corrupt name was already in MIR before
emission, OR whether it appears only at emit time.

**Test E2**: `culebra trace --function rename_value --var '%v'`
to follow the Value parameter through the function — does the
load+store+extract chain match Python's IR?

**Test E3**: `culebra diff` between Python's
`mir_opt__rename_value` and stage1's `rename_value` — find the
specific instruction that diverges.

#### Hypothesis F — Value field-0 layout divergence at sret/byref boundary

Value has type `%struct.Value = type { {ptr, i64}, %struct.MIRType }`.
Field 0 is `{ptr, i64}` (16 bytes); field 1 is `%struct.MIRType`
(64 bytes). Offset 0 should be 0, offset 1 should be 16, total 80.

If LLVM's backend computes a different stride for `%struct.Value`
in some context (e.g., when sret-returned vs when stored into a
local alloca), the first 16 bytes could slide while the rest
reads correctly.

**Test F1**: `culebra field-index-audit /tmp/stage2.ll` reports
all structs stuck at index 0. If Value or MIRType show up,
investigate.

**Test F2**: `culebra health /tmp/stage2.ll --struct Value` runs
PHI zeroinit / type-pun / null-load checks specific to Value.

**Test F3**: `culebra explain /tmp/stage2.ll <template>` for:
- `match-phi-zeroinit-corruption` (Critical)
- `option-type-pun-zeroinit` (Critical)
- `sret-zeroinitializer-return` (Critical)
- `return-type-divergence` (Critical)

#### Hypothesis G — Missing `noalias` on byref param ptrs

v5.6.8 noted the divergence: Python's IR emits
`ptr noalias %dest.byref`; the self-hosted emitter emits
`ptr %dest.byref` (no noalias). Pre-existing pattern.

If LLVM treats `noalias` on byref params as enabling load-store
forwarding (the alloca → store → load → extractvalue chain), then
WITHOUT noalias LLVM may keep the load-store round-trip
intact, but the round-trip may be MIScompiled — for example, if
the alloca's size-of-named-type is ABI-different from what
extractvalue expects.

**Test G1**: hand-edit the v5.6.8 stage2.ll to add `noalias` on
all byref param ptrs, recompile mnc-stage2, run `p1.mn`. If the
OOM closes, ship the noalias-on-byref fix as the v5.6.9 closure.

**Test G2**: if G1 doesn't close it, try emitting INLINE aggregate
types instead of named `%struct.Value` everywhere — closer to
Python's IR shape — and see if that closes it.

### Reproducer

Same as v5.6.8 (stable since v5.6.4):

```mn
// /tmp/p1.mn
fn add(a: Int, b: Int) -> Int { return a + b }
fn main() { print(add(1, 2)) }
```

Stage1 produces 215 lines of valid IR; mnc-stage2 OOMs
immediately on the third `Instruction::Alloca` emit.

---

## Scope

### What ships

#### 9.9a — Culebra triage + bisect of stage1 vs stage2

Run the full culebra investigation suite over the v5.6.8 stage2.ll.
Save outputs to `docs/roadmap/v5/v5.6.9/culebra/`:

```bash
mkdir -p docs/roadmap/v5/v5.6.9/culebra
culebra summary /tmp/stage2.ll > docs/roadmap/v5/v5.6.9/culebra/summary.md
culebra triage /tmp/stage2.ll --brief > docs/roadmap/v5/v5.6.9/culebra/triage.txt
culebra bisect mapanare/self/main.ll /tmp/stage2.ll --top 30 \
    > docs/roadmap/v5/v5.6.9/culebra/bisect.md
culebra field-index-audit /tmp/stage2.ll \
    > docs/roadmap/v5/v5.6.9/culebra/field-index-audit.txt
culebra health /tmp/stage2.ll --struct Value \
    > docs/roadmap/v5/v5.6.9/culebra/health-Value.txt
culebra health /tmp/stage2.ll --struct MIRType \
    > docs/roadmap/v5/v5.6.9/culebra/health-MIRType.txt
```

The bisect output ranks divergent functions by impact. v5.6.8's
investigation pointed at `emit_alloca`, `instr_dest`,
`rename_value`, `clone_instr_for_inline` — the bisect should
either confirm or surface different suspects.

**False positive policy** (per `/culebra-scan` SKILL):
- `missing-typedef` on forward-declared runtime structs in C
  headers — known FP, ignore via `.culebra-ignore`.
- `c-memcpy-size-mismatch` at runtime double/uint64_t bitcast — FP.
- `break-inside-nested-control` on return-in-for-loop in
  self-hosted .mn code — 43 intentional findings, FP.

Add a project-level `.culebra-ignore` if not present.

#### 9.9b — Hypothesis E test: trace through inliner

```bash
culebra trace /tmp/stage2.ll --function rename_value --var '%v' \
    > docs/roadmap/v5/v5.6.9/culebra/trace-rename_value.txt
culebra trace /tmp/stage2.ll --function clone_instr_for_inline --var '%inst' \
    > docs/roadmap/v5/v5.6.9/culebra/trace-clone_instr.txt
culebra diff mapanare/self/main.ll /tmp/stage2.ll \
    | grep -A 20 "rename_value\|clone_instr" \
    > docs/roadmap/v5/v5.6.9/culebra/diff-inliner.md
```

If the trace shows a load/store mismatch (e.g. wrong type on a
load), that's the bug. If the trace is clean, move to F.

#### 9.9c — Hypothesis F test: Value field-0 layout audit

```bash
culebra explain /tmp/stage2.ll match-phi-zeroinit-corruption
culebra explain /tmp/stage2.ll option-type-pun-zeroinit
culebra explain /tmp/stage2.ll sret-zeroinitializer-return
culebra explain /tmp/stage2.ll return-type-divergence

# Also inspect block-by-block for the suspect functions
culebra inspect /tmp/stage2.ll --function emit_alloca \
    > docs/roadmap/v5/v5.6.9/culebra/inspect-emit_alloca.md
culebra inspect /tmp/stage2.ll --function instr_dest \
    > docs/roadmap/v5/v5.6.9/culebra/inspect-instr_dest.md
```

#### 9.9d — Hypothesis G test: noalias-on-byref experiment

Hand-patch v5.6.8 stage2.ll to add `noalias` on every
`ptr %X.byref` param across all function definitions:

```bash
sed 's/ptr %\([a-zA-Z_]*\)\.byref/ptr noalias %\1.byref/g' \
    /tmp/stage2.ll > /tmp/stage2-noalias.ll
llvm-as /tmp/stage2-noalias.ll -o /dev/null && echo "llvm-as OK"
clang -O2 -c /tmp/stage2-noalias.ll -o /tmp/stage2-na.o
gcc -o /tmp/mnc-stage2-na /tmp/stage2-na.o \
    runtime/native/libmapanare_rt.a -no-pie -rdynamic -lm -lpthread -ldl
/tmp/mnc-stage2-na /tmp/p1.mn > /tmp/p1-na.ll 2>&1
echo "RC=$? lines=$(wc -l < /tmp/p1-na.ll)"
```

If RC=0 and lines>100, **noalias is the fix** — implement it in
the self-hosted emitter at `emit_mir_function`'s param-string
builder. ~5 LOC change.

If RC≠0, the bug is deeper. Move to instrument-the-lowerer phase.

#### 9.9e — Lowerer-side instrumentation (fallback)

If 9.9a–d don't identify the root cause, add `__mn_str_eprint` to
`emit_instr` (one-line: log every Alloca's dest.name as it goes
into MIR). Rebuild stage1 + stage2. Determine whether MIR has
corrupt names BEFORE emission (lowerer bug) or only at emission
(emitter bug).

Strip the eprint before commit.

#### 9.9f — Apply the fix + validate

Once the root cause is identified:
- Surgical fix at the divergent site (likely <50 LOC)
- Re-run `verify_fixed_point.sh --keep` — expect non-empty
  stage3.ll, STRICT or NEAR fixed-point
- `culebra fixedpoint` to verify the stage1→stage2→stage3 cycle
  stabilizes

#### 9.9g — Establish v5.6.9 culebra baseline

```bash
culebra baseline save /tmp/stage2.ll \
    -o docs/roadmap/v5/v5.6.9/culebra/baseline-end.json
culebra journal add "v5.6.9 shipped: Ve.3 closed — <root-cause>" \
    --action milestone
```

Move the journal to `docs/roadmap/v5/v5.6.9/culebra-journal.jsonl`
at session close.

### What does NOT ship

- **Ve.2 residuals** (18 × 384-byte floor sites). v5.6.10 scope.
- **The struct_byte_size patch from v5.6.8**. Re-evaluate in
  v5.6.10 once Ve.3 closes — its 7% IR growth is acceptable
  ONLY if it provides a real benefit (e.g. correct sret/byref
  classification for downstream releases).
- **Multi-level walk for Rt.04**. v6.0 borrow-checker scope.
- **Sh.7 / B closure work**. v5.7.0.

---

## Exit criteria

1. `mnc-stage2 /tmp/p1.mn` produces non-empty IR with
   `llvm-as` clean.
2. `mnc-stage2 mnc_all.mn` produces non-empty stage3.ll with
   `llvm-as` clean.
3. `bash scripts/verify_fixed_point.sh --keep` exits 0 with
   STRICT or NEAR fixed-point (≤ 100 diff lines).
4. `culebra fixedpoint` confirms cycle stabilization.
5. Harness 64/66 preserved (same 2 fails: 51 / 64).
6. stage2.ll growth vs v5.6.7's 207,619: < 5% (the 7% from the
   v5.6.8 struct_byte_size patch is OUT of scope here; if the
   v5.6.9 fix incidentally fixes the same bug class, we accept the
   growth — but don't bundle).
7. `culebra triage --brief` reports no NEW critical findings vs
   the v5.6.9 baseline.
8. Valgrind sweep 0 new ERRORS.
9. ASan UAF sweep 0 new findings.
10. LSan baseline gate PASSES (62_list_output unchanged at 9 / 141 B
    per Rt.04 v5.6.6 RESCOPE).
11. Non-bootstrap pytest 0 failures.
12. `make lint` clean.
13. `check_struct_registry.py` 23/23/91 clean.
14. `docs/known_issues.md` Ve.3 row → **CLOSED v5.6.9**.
15. `docs/roadmap/v5/PARITY_GAPS.md` — add a "self-hosting
    fixed-point restored" entry if STRICT/NEAR achieved.
16. `docs/roadmap/v5/v5.6.9/culebra-journal.jsonl` populated with
    every milestone / fix / triage action.

---

## Design decisions

### D1 — Culebra-first, ad-hoc-instrumentation-second

v5.6.8 used `__mn_str_eprint` instrumentation as the primary
diagnostic. v5.6.9 leads with culebra — it's structurally aware
of LLVM IR, can bisect divergent functions in one command, and
catches the FP class up-front. Hand instrumentation is a fallback,
not the entry point.

### D2 — Honor culebra false positives

Per `/culebra-scan` SKILL: at least 3 known FP classes exist in
the Mapanare codebase. Do NOT chase findings in those classes.
Add to `.culebra-ignore` at start of session; re-evaluate at end.

### D3 — Single-fix release

Ve.3 closure should land as ONE surgical fix at the root cause,
not as a stack of partial mitigations. v5.6.8 already documented
that Hypothesis A's struct_byte_size patch is partial — DO NOT
ship that here. If Ve.3's fix happens to overlap with that
patch, accept the IR growth; otherwise leave the v5.6.8 patch
for v5.6.10.

### D4 — STRICT fixed-point vs NEAR

Same as v5.6.8: NEAR (≤ 100 diff lines) is acceptable; STRICT
is bonus. The goal is non-empty stage3.ll and a stable cycle,
not byte-identity.

### D5 — Add `.culebra-ignore` to repo

Single-source-of-truth for known FPs. Commit at session start so
every team member (human + agent) gets the same suppression set.

### D6 — Journal every action

```bash
culebra journal add "v5.6.9 phase 1: triage shows X" --action milestone
culebra journal add "Hypothesis E ruled out: rename_value IR matches Python" --action analysis
culebra journal add "Root cause: <X>" --action fix
```

The journal becomes the v5.6.10 starting context.

---

## Risks

- **R1 — Culebra surfaces only false positives.** The bug may be
  outside its template coverage (49 templates is broad but not
  total). Mitigation: 9.9e fallback (eprint instrumentation).
- **R2 — Hypothesis E + F + G all rule-out.** Then the bug is in
  a fourth, unidentified class. Mitigation: this release becomes
  another investigation-only, like v5.6.8. Don't force a fix.
- **R3 — noalias-on-byref fix surfaces a different bug.** Adding
  noalias is a HINT, but if Mapanare's emitter generates IR that
  DOES alias byref pointers somewhere, noalias would BREAK that
  code. Mitigation: full sanitizer sweep after the fix; revert if
  any new finding.
- **R4 — culebra binary not available in CI.** Local-only tool.
  Mitigation: shipping binaries is OUT of scope for v5.6.9; the
  artifacts (summary.md, triage.txt, bisect.md) are what land in
  the repo, not the tool.
- **R5 — IR layout change cascades.** If the fix changes how
  Value is laid out, downstream LSan / valgrind baselines may
  shift. Mitigation: re-establish baselines as part of the
  release; document in SESSION_REPORT.

---

## What NOT to do

- **Do not ship a partial fix.** Ve.3 closure means non-empty
  stage3.ll, not "we fixed something adjacent."
- **Do not chase culebra false positives.** Stick to the SKILL's
  documented FP list + add new ones to `.culebra-ignore` as found.
- **Do not bundle Ve.2 residuals.** v5.6.10 scope. The 18 × 384-byte
  floor sites are SAFE; chasing them now obscures Ve.3 closure.
- **Do not re-apply the v5.6.8 struct_byte_size patch unless the
  root-cause investigation specifically points there.** The
  patch's 7% IR growth without observable benefit is exactly
  what v5.6.8 warned against.
- **Do not skip the full sanitizer gate.** Ve.3 fix touches
  emission code; every program exercises it.
- **Do not tag v5.6.9 without user approval.** v-tag timing rule.
- **Do not commit `/tmp/mnc-stage2-na` or other ad-hoc binaries.**
  Investigation artifacts go in `docs/roadmap/v5/v5.6.9/culebra/`.
