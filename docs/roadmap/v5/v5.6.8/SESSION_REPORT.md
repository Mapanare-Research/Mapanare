# v5.6.8 Session Report — Ve.3 INVESTIGATION-ONLY

> **Status: INVESTIGATION SHIPPED — Ve.3 NOT closed.** v5.6.8 is a
> documentation/investigation release. The original PLAN scoped Ve.3
> closure (stage2 runtime OOM → non-empty stage3.ll) for v5.6.8;
> empirical evidence collected during this session shows the bug is
> deeper than the four hypotheses (A/B/C/D) the PLAN enumerated.
> Source code is unchanged from v5.6.6 (the post-v5.6.7 release that
> holds the v5.6.6 slot in the version sequence). Goldens 64/66
> preserved; mnc-stage1 binary regenerated from the same source as
> v5.6.7. The bug remains tracked as Ve.3 in `docs/known_issues.md`
> with v5.6.9+ scope and the substantially narrower hypothesis space
> documented below.

---

## Headline

**Ve.3 NOT closed.** `mnc-stage2 /tmp/p1.mn` still OOMs in
`__mn_str_concat ← llvm_alloca`; `verify_fixed_point.sh` still
produces 0-line `stage3.ll`. Source code unchanged from v5.6.7.
Investigation tightened the hypothesis space and produced a
single-step reproducer that surfaces the bug at a smaller MIR scale
than `mnc_all.mn`.

What ships:
- VERSION bumped 5.6.6 → 5.6.8 (the planned slot — v5.6.7 occupied
  the prior position; v5.6.8 holds this one).
- `mnc-stage1` binary regenerated from unchanged source via the
  Python bootstrap; byte-identical IR shape to v5.6.7's stage2.ll
  (207,619 lines, llvm-as clean).
- 64/66 goldens preserved; valgrind / ASan / LSan baselines unchanged
  per skipped Phase 4 (no source changes to gate).
- This SESSION_REPORT + updates to `known_issues.md`, `PARITY_GAPS.md`,
  `ROADMAP.md`, `CLAUDE.md` reflecting investigation outcomes.

What does NOT ship:
- Ve.3 fix. The four PLAN hypotheses (A — payload-type builder
  divergence, B — list elem_size mismatch, C — third hardcoded
  GEP site, D — Python emitter bug) are individually
  ruled out or proven not load-bearing for the OOM symptom.
- Non-empty stage3.ll. Same failure mode as v5.6.5 / v5.6.7.
- The structural fix in `struct_byte_size` (described below in
  §Investigation outcome 2). The patch was empirically verified
  to NOT close Ve.3 — it changes which functions get sret/byref
  but does not eliminate the OOM. Shipping it without closure
  would be a non-trivial IR layout change (stage2.ll grew +7%
  with the patch applied) for no observable benefit, against the
  "no cheap shit" directive.

---

## What was investigated

### Phase 0 — baseline confirmation

```
make build-rt && python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1
```

- Goldens 64/66 (matches v5.6.7 baseline)
- `verify_fixed_point.sh --keep`:
  - stage2.ll 207,619 lines, llvm-as clean
  - mnc-stage2 builds (4,492,248 bytes)
  - mnc-stage2 mnc_all.mn → SIGSEGV → stage3.ll 0 lines
- `mnc-stage2 /tmp/p1.mn` → OOM with
  `requested 5,107,809,313,525,936,626 bytes` from `__mn_alloc`
  via `__mn_str_concat ← llvm_alloca`. Reproduces the v5.6.4 →
  v5.6.7 signature.

### Phase 1 — symbolic trace

Built `/tmp/mnc-stage2-asan` with the v5.6.5 build script.
Instrumented `__mn_str_concat` to log inputs whose `len > 1M`
or whose `data` ptr falls in the suspicious 0x100000000 –
0x400000000 range, with `__builtin_return_address(0)` to
identify the actual call site (libc's `backtrace()` was
unreliable in this -O2 binary).

Trace from `mnc-stage2 /tmp/p1.mn`:

```
DBG[1590] CORRUPT __mn_str_concat: a.ptr=0x830418 a.len=2
        b.ptr=0x1000000d4 b.len=15  caller=<llvm_alloca+0x28>
```

- `a` is the literal `"  "` (the leading-spaces prefix in
  `llvm_alloca`'s body `"  " + name + " = alloca " + ty`).
- `b` is the `name` parameter passed into `llvm_alloca`. Its
  `data` field reads as 0x1000000d4 (i.e. 1<<32 | 0xd4 — looks
  like a 32-bit value mis-loaded as a 64-bit pointer); its
  `len` field varies between runs (e.g. 15, 6,322,843,…,
  2,252,453,…). **Non-deterministic** values across runs ⇒
  reading uninitialised memory.

**Where it fires:** the *third* `Instruction::Alloca` to be
emitted for `p1.mn`. The first two (the `%a.addr` and `%b.addr`
allocas for the parameters of `add(a: Int, b: Int)`) emit
correctly; the third fails. Confirmed by adding an
`__mn_str_eprint` of `dest.name` and `len(dest.name)` at the
top of `emit_alloca` and rebuilding stage1:

```
DBG emit_alloca: dest.name.len=7  dest.name=[%a.addr]  dest.ty.kind=0
DBG emit_alloca: dest.name.len=7  dest.name=[%b.addr]  dest.ty.kind=0
DBG emit_alloca: dest.name.len=15 dest.name=[]         dest.ty.kind=0
```

`dest.ty.kind=0` (= `TK_INT`) on all three; `dest.ty.name="Int"` on
all three. **Only `dest.name` (field 0 of the Value struct) is
corrupt on the third call.** The MIRType field (field 1) reads
correctly. This rules out a pure ABI sizing bug on the whole
struct — only the first 16 bytes are mis-read, suggesting either
(a) a layout offset divergence at the field boundary, or (b) the
upstream producer of the third Alloca's dest writes garbage to
field 0.

### Phase 2 — hypothesis testing

#### Hypothesis D — Python emitter bug

**Ruled out.** The committed `mnc-stage1` binary (built by the
Python emitter) compiles `p1.mn` to a 215-line valid IR.
Re-building stage1 from `stage2.ll` itself (`mnc-stage1-fromself`)
reproduces the OOM identically: the bug is in the IR
that `mnc-stage1` produces for `mnc_all.mn`, not in how the
Python emitter handles either source.

#### Hypothesis A — payload-type builder divergence

`build_payload_type_from_values` (init site) and
`build_payload_type_from_variant` (extract site) both apply the
same `%struct.X → %enum.X` rewrite for the `is_enum_type`
predicate. For `Instruction::Alloca(addr, pty)` specifically,
both produce `{ %struct.Value, %struct.MIRType }`. Verified by
inspecting stage2.ll — the GEP-trick init at the only relevant
site (line 57989, `%t50.sz = ptrtoint ptr getelementptr
({ %struct.Value, %struct.MIRType }, ptr null, i32 1) to i64`)
matches the extract path's `load %struct.Value, ptr %d32.pr` at
field 0 (no GEP needed for idx 0). **Not the bug.**

#### Adjacent finding — `struct_byte_size` undercount

While drilling Hypothesis A, found that
`struct_byte_size("%struct.Value")` returns `8` (not the true
80) under the v5.6.7 code. Two compounding bugs:
1. `register_internal_struct` pushes stub entries with
   `llvm_type="%struct.X"` (the named form, not the inline
   `{...}` form); the forward search in `struct_byte_size`
   finds the stub first.
2. `llvm_aggregate_size` counts ALL commas in its argument
   string — including commas INSIDE nested aggregates. For the
   real `%struct.Value`'s inline form
   `"{ {ptr, i64}, %struct.MIRType }"`, split-by-"," gives 3
   parts → 24 bytes (not the true 80).

Patched `struct_byte_size` to delegate to `llvm_sizeof_st`
(which does recursive resolution via `lookup_struct_field_types`,
already taught to skip stub entries in v5.6.5). With the patch:
- `struct_byte_size("%struct.Value") = 80` (correct)
- `use_sret_return("%struct.Value") = true` (24 → 80, both > 16)
- `is_byref_type_st("%struct.Value") = true` (24 → 80, > 64
  threshold)

Stage2.ll grew 207,619 → 222,628 lines (+7.2%) with the patch:
many functions that previously returned `%struct.Value` /
`%struct.MIRType` directly now use sret; many parameter passes
now use byref. The IR is `llvm-as`-clean. **However, the OOM is
unchanged.** `mnc-stage2 /tmp/p1.mn` still crashes, with the
same DBG[1590] signature and the same `dest.name=[]` /
`dest.name.len=<huge>` pattern at the third `emit_alloca` call.

The patch is REVERTED in shipped v5.6.8 because:
- 7% IR growth without observable benefit is a regression risk
  for stage2.ll consumers (LSan / valgrind sweeps would re-baseline)
- The bug is unrelated to ABI sizing; shipping the patch would
  obscure the v5.6.9+ debugging surface
- "No cheap shit" — partial fixes that don't close the symptom
  are not in scope

The patch logic and findings are preserved here for v5.6.9+
to consider in the proper context (alongside whatever fixes
the OOM).

#### Hypothesis B / C — list elem_size mismatch / third hardcoded GEP

Not pursued in depth. The reproducer (`p1.mn`, 2 functions, 4
allocas total) doesn't exercise list-storage code paths beyond
the per-function `f.params`/`f.blocks` lists, which use the
runtime's own list machinery (independent of the GEP-trick fix
landed in v5.6.5). No hardcoded byte-offset GEP candidates were
identified in the reproducer's emission path.

### Phase 1.5 — additional findings worth preserving

#### `noalias` divergence between Python emitter and self-hosted emitter

The Python-emitted IR for `mapanare/self/main.ll`:

```
define void @emit_llvm__emit_alloca(
    ptr noalias sret(...) %__sret__,
    ptr %st.byref,
    ptr noalias %dest.byref,           ← noalias
    {...} %ty
) ...
```

The self-hosted-emitted IR for the same source:

```
define void @emit_alloca(
    ptr noalias sret(%struct.EmitState) %__sret__,
    ptr %st.byref,
    ptr %dest.byref,                   ← MISSING noalias
    %struct.MIRType %ty
) ...
```

Python's emitter adds `noalias` to byref struct parameters; the
self-hosted emitter does NOT. This is a pre-existing divergence
(predates v5.6.x). It SHOULD NOT cause incorrectness on its own —
LLVM treats `noalias` as a hint, and missing it makes optimisation
more conservative not less. But it's a candidate to investigate in
v5.6.9+ if other paths fail: with `noalias` LLVM may move loads
across the call (assuming the input doesn't alias caller state),
which could expose a memory-init ordering bug elsewhere.

#### Named struct types vs inline aggregate types

Python emits inline aggregate types (`{ {ptr, i64},
%struct.MIRType }` written out at every use site). The self-hosted
emitter uses named `%struct.X` types throughout. For LLVM's
backend ABI lowering both should be equivalent, and stage2.ll
passes `llvm-as`. But if the backend treats them differently for
some reason (e.g. inline types disambiguating identical-shape but
distinct-identity structs), it could matter. Adjacent investigation,
not load-bearing for v5.6.8.

---

## Reproducer

The smallest crashing input remains stable across v5.6.4 → v5.6.8:

```mn
fn add(a: Int, b: Int) -> Int { return a + b }
fn main() { print(add(1, 2)) }
```

(saved to `/tmp/p1.mn` per scripts/build_stage2_asan.sh expectations)

```
$ /tmp/mnc-stage2 /tmp/p1.mn
mapanare: out of memory (requested ~5e18 bytes)
[exit 1, stage1 produces 215 lines of valid IR for the same input]
```

Stack (with debug instrumentation):
```
__mn_alloc(garbage_size)
  ← __mn_str_concat   (a.len=2 valid, b is the corrupt name)
    ← llvm_alloca("  " + name + " = alloca " + ty)
      ← emit_alloca(st, dest, ty)   ← dest.name reads garbage on 3rd call
        ← emit_mir_by_kind(...)     ← kind=="alloca" branch
```

The third Alloca's `dest.name` is read from uninitialised memory:
`len(dest.name)` returns nondeterministic huge values across runs;
`__mn_str_eprint(dest.name)` prints empty (data ptr is invalid or
points to immediately-zero bytes).

---

## Hypothesis updates

### Active for v5.6.9+

- **Lowerer / inliner produces a corrupt third Alloca.** The
  first two Allocas (param slots `%a.addr`, `%b.addr` of `add`)
  emit correctly. The third — produced by either (a) the
  inliner cloning add()'s body into main() with renamed
  destinations, or (b) the lowerer's loop unrolling
  intermediate var creation — has corrupt name. Investigate
  `mir_opt::clone_instr_for_inline` and `mir_opt::rename_value`:
  do their compiled outputs in stage1 differ from the Python
  bootstrap's compilation? Specifically check whether
  `find_const(renames, v.name)` returns spurious `Some(empty_string)`
  for the third Alloca.
- **Field-0 vs Field-1 layout divergence on Value.** Only
  `dest.name` (field 0 of Value) is corrupt; `dest.ty` (field 1)
  is correct. If LLVM's backend computed a different stride for
  Value at the boundary between caller and callee, only the first
  16 bytes would slide. Check stage2.ll's
  `%struct.Value = type { {ptr, i64}, %struct.MIRType }`
  alignment requirements: `{ptr, i64}` is 8-aligned; `%struct.MIRType`
  is also 8-aligned (its first field is `{ptr, i64}`). LLVM
  should agree on offsets 0 and 16.

### Ruled out

- **D — Python emitter bug.** Python-built mnc-stage1 handles
  p1.mn correctly; rebuild-from-self reproduces the bug.
- **A — payload-type builder divergence.** Both helpers produce
  identical strings for `Instruction::Alloca`'s payload at
  v5.6.7's emit code.

### De-prioritised

- **C — additional hardcoded GEP site.** Not seen in p1.mn's
  emission path.
- **B — list elem_size mismatch.** Not triggered by p1.mn.

---

## What to investigate next (v5.6.9+)

1. **Add `__mn_str_eprint` of dest.name at every Alloca/Load/Store
   emit site**, rebuild stage1 + stage2, and check whether the
   corruption is at the LOWERER (Alloca's dest.name was already
   garbage in the MIR) or at the EMITTER (dest is loaded from a
   bad alloca slot).
2. **Compare stage1's IR for `mir_opt::clone_instr_for_inline`'s
   Alloca branch vs Python's IR** for the same Mapanare source.
   Look for diff in load/store patterns, missing noalias, or
   different field offsets.
3. **Switch the experimental `struct_byte_size` patch back on**
   and re-run with the eprint instrumentation. The 7% IR growth
   may surface a different failure mode that's easier to diagnose
   (for example, ASan may catch an out-of-bounds access that
   the under-allocated structs are masking).
4. **Test whether emitting noalias on byref param ptrs** (matching
   Python's emitter) closes the bug in isolation. Single-line
   change in `emit_mir_function`'s param-string builder.
5. **Test with `llc -O0` directly on stage2.ll** instead of
   clang's pipeline, to rule out Clang-specific optimisations
   that may interact with self-hosted-emitted IR shape.

---

## Metrics

- `VERSION`: 5.6.6 → 5.6.8
- `mapanare/self/mnc-stage1`: 6,270,128 bytes (rebuilt from
  unchanged source — strip-pruned size identical to v5.6.7)
- stage2.ll: 207,619 lines, llvm-as clean (no change vs v5.6.7)
- Goldens harness: **64/66** preserved (same 2 fails:
  `51_match_guards_and_or` B and `64_closure_typed` Sh.7)
- `make lint`: clean
- `check_struct_registry.py`: 23/23/91 clean
- Non-bootstrap pytest: not re-run (no source changes)
- Valgrind / ASan / LSan sweeps: not re-run (no source changes
  to gate; v5.6.7 baselines apply)

---

## Out of scope

- v5.6.9 lands the actual Ve.3 fix once the residual hypothesis
  matrix narrows further. Estimated: 1–2 sessions.
- v5.7.0 stays Sh.7 + B or-pattern → 66/66.
- v5.7.1 SPEC docs polish.
- v5.8.0 RE-PANEL.

---

## Why ship v5.6.8 at all

This release packages the investigation evidence so v5.6.9+ work
starts with a tighter hypothesis space than v5.6.5 / v5.6.7 left.
Without it, the next session would re-derive the same trace data,
re-run Hypothesis A's struct_byte_size patch, and re-discover
that it doesn't close the OOM. v5.6.8 documents that wall and
points the next session at the lowerer/inliner path instead.

The release follows v5.6.6's "Rt.04 attempted + RESCOPED" pattern:
honest scoping over premature closure. Goldens / baseline parity
preserved; no risk of regression.
