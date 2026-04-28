# Mapanare v5.6.8 — "Ve.3 close — stage2 runtime OOM, stage3 restored"

> **Close Ve.3 — the stage2 runtime corruption that has been the
> *real* blocker for non-empty stage3.ll since v5.4.4.** v5.6.5
> closed the parse_fn_body overflow (Ve.1); v5.6.7 closed the
> empty-list elem_ty propagation (Ve.2 partial); v5.6.8 closes the
> remaining: a corrupted String read inside `__mn_str_concat`
> called from `llvm_alloca` during stage2 emission.

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v5.6.5 (Ve.1) and v5.6.7 (Ve.2 partial) shipped.
The 384-byte list floor still covers the residual 18 sites — so we
have no safety net beneath the immediate symptom. If the bug is in
those 18 sites (i.e., it's actually elem_ty mis-propagation in a
non-`let` context), v5.6.8 may merge into the v5.6.9+ residual
closure. If it's a separate bug class (struct field offset
miscount, list elem_size writer/reader mismatch), it stands on its
own.
**Estimated work:** 1–2 sessions (~3–5 hours). The bug has been
hiding since v5.4.4 behind earlier crashes; investigation may
branch.
**Owner docket:** Ve.3 (opened v5.6.7 after v5.6.5 + v5.6.7 fixes
narrowed the blast radius)

---

## Why this release exists

### The stuck state

```
[Stage 0] mnc-stage1: OK
[Stage 1] stage1 → stage2.ll: 207k lines, llvm-as OK
          mnc-stage2: builds, ~4.5 MB
[Stage 2] mnc-stage2 mnc_all.mn → stage3.ll: 0 lines (SIGSEGV)
          mnc-stage2 /tmp/p1.mn   → 0 lines (OOM, garbage size)
```

`p1.mn` is the smallest reproducer:

```mn
fn add(a: Int, b: Int) -> Int { return a + b }
fn main() { print(add(1, 2)) }
```

The crash signature (under v5.6.7's stage2):

```
mapanare: out of memory (requested 5,262,911,828,718,956,139 bytes)

#0  __mn_alloc(corrupt_size)
#1  __mn_str_concat
#2  llvm_alloca           — Mapanare source: "  " + name + " = alloca " + ty
#3  emit_mir_by_kind
```

`llvm_alloca` is a 1-line string formatter:

```mn
fn llvm_alloca(name: String, ty: String) -> String {
    return "  " + name + " = alloca " + ty
}
```

`__mn_str_concat(a, b)` allocates `a.len + b.len + 1` bytes. One of
the input Strings has a corrupted `len` field (or `data` ptr) →
huge alloc → OOM.

### What we know

- **ASan didn't catch it as heap-buffer-overflow.** The corrupted
  read is of *legally addressable* memory whose contents are wrong
  — not a buffer overflow / use-after-free. Rules out (most)
  out-of-bounds writes.
- **Pre-existing.** Same failure mode in v5.6.4 baseline, v5.6.5
  (post-Ve.1 fix), v5.6.7 (post-Ve.2 fix). My v5.6.5 and v5.6.7
  fixes didn't introduce it; just narrowed the blast radius.
- **Reproducer is tiny.** `p1.mn` is 2 fns / 4 lines. So the bug
  fires during emission of trivial MIR (BinOp, Const, Call,
  Return). Plenty of payload boxing, no fancy features.
- **stage1 (Python-emitted) handles `p1.mn` perfectly.** Same source
  through Python emitter produces 215 lines of valid IR. The bug is
  specifically in stage2 (self-hosted-emitted) running on its own
  source.

### Root-cause hypotheses

#### Hypothesis A — MIR Value's `name: String` read at wrong offset

`Value = { name: String, ty: MIRType }` = 16 + 64 = 80 bytes,
align 8. If a `Value` is stored in a payload at offset N and read
back at offset N+8 (or similar), `name`'s `{ptr, i64}` would be
read across `ty.name`'s `{ptr, i64}` boundary — getting half-ptr,
half-len → corrupt String.

Most likely site: `Instruction::BinOp(dest, op, lhs, rhs)`. v5.6.5's
GEP-trick emits `getelementptr inbounds <payload_ty>, ptr %ep, i32
0, i32 <idx>` for INIT and `getelementptr inbounds
<extracted_payload_ty>, ptr %pr, i32 0, i32 <idx>` for EXTRACTION.
Both reference the same `<payload_ty>` string built from
`build_payload_type_from_values` (init) or
`build_payload_type_from_variant` (extraction).

If those two helpers produce DIFFERENT `<payload_ty>` strings for
the same logical variant — e.g., init builds `{%struct.Value,
%enum.BinOpKind, %struct.Value, %struct.Value}` but extraction
builds `{%struct.Value, %struct.BinOpKind, %struct.Value,
%struct.Value}` (struct vs enum mismatch) — LLVM would compute
DIFFERENT field offsets on each side → cross-boundary reads.

**Test:** for one specific BinOp emit + extract, dump both
`<payload_ty>` strings and compare. If they differ, fix the
mismatch.

#### Hypothesis B — List<Struct> elem_size inconsistent

A `List<MIRFunction>` in the MIR module stores 208-byte elements.
If the list is created with `elem_size = 208` (correct via
GEP-trick) but read with `elem_size = 384` (legacy floor at some
unfixed site), each indexed read picks up bytes from the next
slot's start — corrupting whatever struct is being read.

**Test:** dump every `__mn_list_new(elem_size)` call site in
stage2.ll. For each unique caller, check if there's a corresponding
`__mn_list_get(idx)` site that uses a different stride. Look for
the `set_elem_size` runtime-side stride field.

#### Hypothesis C — A third hardcoded-fallback site

v5.6.5 missed something. `compute_payload_alloc_size` is fixed;
`compute_field_offset` is fixed; `sum_field_sizes` is fixed;
`compute_variant_field_offset` is fixed. But there might be:
- `emit_struct_init` — does it use the GEP-trick or hand-compute?
- `emit_struct_init_from_values` — same question (used by my v5.6.7
  short-circuit when dest is a struct).
- `emit_field_set` / `emit_field_get` — typed GEP with named struct
  vs hand-computed byte offset.

**Test:** grep for any remaining `getelementptr inbounds i8, ptr %X,
i64 <hardcoded>` patterns in stage2.ll. Check if any is tied to a
struct field access that diverges from LLVM's actual layout.

#### Hypothesis D — Stage2 inherits a stale-IR bug from Python

Less likely, but possible: Python's emitter compiles mnc_all.mn
into stage2.ll. Python's `_tsz` for `%struct.Value` might fall
through to `8` (no special case for named structs — it relies on
`_struct_ty[name]` being expanded INLINE at registration). If the
inlining produces a payload type string for a BinOp that
inadvertently resolves named types differently from how the
extraction expects, the stage2 binary inherits an internal
inconsistency.

**Test:** generate stage2.ll, then re-build `mnc-stage1` from
`stage2.ll` itself (call it `mnc-stage1-from-self`) and run it on
`p1.mn`. If it OOMs identically, the bug is in self-hosted
emission. If it works, the bug is in Python's compilation of
self-hosted source.

### Reproducer

Smallest crashing input: `/tmp/p1.mn` (2 functions, 1 BinOp). Stable
between releases. Use `mnc-stage2-asan` for ASan-instrumented
trace; use `gdb -batch` with conditional breakpoint on `__mn_alloc`
when `size > 1000000` to catch the corrupt allocation.

---

## Scope

### What ships

#### 9.8a — Symbolic ASan trace + classification

Build `mnc-stage2-asan` (already scripted at
`/tmp/build_stage2_asan.sh` from v5.6.5 work) with the v5.6.7
binary. Run on `p1.mn`. Expected: OOM with stack including
`__mn_str_concat`. Expand to identify what String is corrupt.

Sub-step: add a debug print in `__mn_str_concat` (runtime) that
logs `a.ptr`, `a.len`, `b.ptr`, `b.len` when `a.len + b.len > 10000`.
Catch the corrupt input live; correlate with the caller in
`llvm_alloca` to see which Value/MIRType resolution went wrong.

#### 9.8b — Confirm hypothesis

Drive each hypothesis (A/B/C/D) to a measurable test. Pick the one
the trace points to. If the trace is ambiguous, run hypotheses in
order of priority: A (most likely given our v5.6.5 GEP-trick
work) → B → C → D.

#### 9.8c — Fix the root cause

Surgical fix at the specific divergence site:

- **A**: align `build_payload_type_from_values` and
  `build_payload_type_from_variant` to produce identical
  `<payload_ty>` strings for the same logical variant.
  Likely a struct-vs-enum classification mismatch (one uses
  `%struct.X`, the other uses `%enum.X` for the same X). Add a
  shared resolver helper used by both.
- **B**: identify the read-side site using a wrong stride. Either
  fix it to use the writer's stride, or unify both via the
  GEP-trick on the actual element type.
- **C**: convert the remaining hardcoded-byte-offset site to a
  typed GEP. Same pattern as v5.6.5's `emit_enum_init` rewrite.
- **D**: more invasive — Python emitter would need a parallel fix.
  Defer to a Python-bootstrap-side micro-release if reproduced.

#### 9.8d — Validation

After the fix:

1. `mnc-stage2 /tmp/p1.mn` produces non-empty IR.
2. `mnc-stage2 mapanare/self/mnc_all.mn` produces non-empty
   `stage3.ll`.
3. `verify_fixed_point.sh --keep` exits 0 with stage3.ll
   non-empty and `llvm-as`-clean.
4. `diff stage2.ll stage3.ll` — classify STRICT (empty diff or
   VERSION-only) / NEAR (a few lines, ordering or VERSION) /
   DIVERGED (>1% lines — investigate before claiming closure).

### What does NOT ship

- **Multi-level walk for Rt.04.** Still v6.0 borrow-checker scope.
- **Ve.2 residual closure.** The 18 × 384-byte floor sites stay
  until v5.6.9+. They're SAFE (the floor over-allocates), just
  wasteful. Don't merge with Ve.3 unless the trace identifies a
  floor site as the bug.
- **General sizing audit.** Only fix the specific Ve.3 site.
  Resist scope creep.
- **Python emitter changes** unless Hypothesis D is confirmed.

---

## Exit criteria

1. `mnc-stage2 /tmp/p1.mn` produces non-empty IR with `llvm-as`
   clean.
2. `mnc-stage2 mnc_all.mn` produces non-empty stage3.ll with
   `llvm-as` clean.
3. `bash scripts/verify_fixed_point.sh --keep` exits 0.
4. `diff stage2.ll stage3.ll` ≤ 100 diff lines (DIFF_THRESHOLD
   default) — STRICT or NEAR fixed-point.
5. Harness 64/66 preserved.
6. stage2.ll growth vs v5.6.7's 207,616 lines: < 2%.
7. Valgrind sweep 0 new ERRORS.
8. ASan UAF sweep 0 new findings.
9. LSan baseline gate PASSES (62_list_output stays at 9 objs / 141
   B from v5.6.6 RESCOPE; Ve.3 closure shouldn't change leak
   counts — if it does, investigate).
10. Non-bootstrap pytest 0 failures.
11. `make lint` clean.
12. `check_struct_registry.py` 23/23/91 clean.
13. `docs/known_issues.md` Ve.3 row flipped to **CLOSED v5.6.8**.
14. `docs/roadmap/v5/PARITY_GAPS.md` — if Ve.3 is listed,
    flip to CLOSED. Add a "self-hosting fixed-point restored" note
    if STRICT/NEAR is achieved.

---

## Design decisions

### D1 — Symbolic trace before code change

The bug has been masked across 4 releases. Don't attempt fixes
without a confirmed trace identifying which String's `len` is
corrupt and where it was originally produced. Three sessions have
been burned on speculative "this might be the issue" — Ve.3
demands forensic evidence first.

### D2 — One-shot fix, not progressive

Unlike Ve.1 (which we shipped piecewise across v5.6.5 and v5.6.7),
Ve.3 should land in a single release. Either we have stage3.ll or
we don't. Partial fixes are progress on Ve.2, not Ve.3.

### D3 — Hypothesis ordering reflects v5.6.5/v5.6.7 history

A is most likely because v5.6.5's GEP-trick refactor built TWO
helpers (init + extraction) that should produce identical type
strings. Both helpers are new code; bugs happen. B is plausible
because list elem_size handling has changed twice (v5.6.5 hybrid,
v5.6.7 lowerer fix). C is possible but lower probability after
v5.6.5's malloc audit. D is only consulted if A/B/C all rule out.

### D4 — STRICT fixed-point vs NEAR

NEAR (≤ 100 diff lines) is fine — historic Mapanare has had NEAR
fixed-point since v4.x. STRICT is bonus. Don't tighten
DIFF_THRESHOLD; the goal is non-empty stage3.ll, not byte-identity.

### D5 — How other languages debug this

- **Rust** — same workflow: `RUSTC_BOOTSTRAP=1` self-compile, gdb
  on the smallest reproducer, valgrind.
- **GHC** — Haskell self-compiler bugs are debugged via comparing
  `-ddump-stg` output between consecutive stages.
- **Mapanare** — has `scripts/ir_doctor.py` for IR diff +
  baseline tracking. Use it post-fix to compare stage2.ll and
  stage3.ll structurally.

---

## Risks

- **R1 — Hypothesis-driven approach blind to root cause.** ASan
  catches buffer overflows, not "reading correct address but
  wrong contents". The trace might localize the SYMPTOM (corrupt
  String read at site X) without revealing the WRITE site that
  corrupted X. *Mitigation:* runtime instrumentation in
  `__mn_str_concat` to capture corrupt input live; backward
  trace via gdb to the most recent write to that String slot.
- **R2 — Fix uncovers another layer.** Like v5.6.5 → v5.6.7. If
  v5.6.8 fixes the OOM but stage3.ll is empty for a different
  reason (e.g., MIR verifier failure, or Mapanare's `match`
  emit emits malformed IR — we already saw this with `p3.mn`),
  scope splits to v5.6.9. *Mitigation:* validate intermediate
  inputs (`p1.mn`, `p2.mn`, `p3.mn`) along the way to catch new
  failure modes early.
- **R3 — stage2.ll growth from added typed GEPs.** Hypothesis C's
  fix (convert remaining byte-offset GEPs to typed GEPs) could
  inflate stage2.ll. *Mitigation:* same 2% growth budget as
  exit criterion #6; tighten if exceeded.
- **R4 — `verify_fixed_point.sh` exit-on-divergence regression.**
  If stage3.ll is non-empty but diverges by >100 lines, the
  script fails as a "fixed point regression" — but Ve.3 closure
  still happened. *Mitigation:* override `DIFF_THRESHOLD=500`
  for the v5.6.8 run if needed; document in SESSION_REPORT;
  close Ve.3 anyway.
- **R5 — Bug is in Python emitter (Hypothesis D).** Then
  v5.6.8 doesn't close Ve.3 — needs a Python-side micro-release.
  *Mitigation:* Hypothesis D test (rebuild stage1 from stage2.ll,
  run on p1.mn) is fast; identifies blame attribution within the
  first hour of work.

---

## What NOT to do

- **Do not start coding before the trace is in.** Three releases
  of speculative fixes is enough.
- **Do not bundle Ve.2 residuals.** The 18 × 384-byte floor sites
  are explicitly v5.6.9+ scope — don't merge unless the Ve.3
  trace points there.
- **Do not touch the Rt.04 work.** Rt.04 is borrow-checker scope.
  v5.6.8 stays focused on Ve.3.
- **Do not lower the DIFF_THRESHOLD.** 100 lines is fine; we want
  non-empty stage3.ll, not byte-identity.
- **Do not skip the full sanitizer gate.** Ve.3 fix touches
  emission code; every program exercises it. A regression would
  be silent without the full sweep.
- **Do not delete the v5.6.7 SESSION_REPORT.** Ve.3 builds on
  Ve.2's analysis; cross-reference the chain in v5.6.8's session
  report.
