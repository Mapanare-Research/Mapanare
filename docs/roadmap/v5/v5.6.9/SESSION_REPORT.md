# v5.6.9 Session Report — Ve.3 PARTIAL CLOSED

> **Status: ROOT CAUSE IDENTIFIED AND FIXED.** Ve.3 closes
> structurally — the drop-glue UAF on `List<Enum>` returns is
> identified, fixed in `emit_drop_glue`, and verified by the
> primary reproducer (`/tmp/p1.mn`) compiling cleanly. The
> full-self-compile fixed-point (`mnc_all.mn → stage3.ll`)
> remains blocked, but by a **separate, pre-existing bug** in
> the self-hosted lowerer's match-arm handling that v5.6.8's
> OOM was masking. Tracked as new **Ve.4** in
> `docs/known_issues.md` for v5.6.10. Goldens 64/66 preserved;
> all sanitizer gates clean.

---

## Headline

**Ve.3 root cause closed.** `mnc-stage2 /tmp/p1.mn` was 0-line
OOM on every run since v5.6.4 — now produces 215 lines of
valid IR (`llvm-as` clean, `RC=0`). The fix is a 25-LOC guard
in `emit_drop_glue` that conservatively skips drops when the
function returns `{ptr, i64, i64, i64, i64}` (the list runtime
type) AND any boxed payloads are tracked in `boxed_owned` —
the same RESCOPE pattern v5.6.6 used for Rt.04 (List<String>
nested in a returned struct).

What ships:
- VERSION 5.6.8 → 5.6.9.
- `emit_llvm.mn` +25 LOC: list-return-with-boxed-owned guard
  in `emit_drop_glue`.
- `mnc-stage1` rebuilt; stage2.ll **207,619 → 201,743 lines**
  (−2.83%, well within the ±5% PLAN budget; the reduction
  comes from skipping boxed-drop emission paths that no
  longer fire for ~12 list-returning functions in `mir_opt`/
  `lower`/`emit_llvm` modules).
- 64/66 goldens preserved; full sanitizer gate clean.
- This SESSION_REPORT + updates to `known_issues.md`,
  `PARITY_GAPS.md`, `ROADMAP.md`, `CLAUDE.md` reflecting
  Ve.3 closure and Ve.4 opening.
- Culebra investigation artifacts in
  `docs/roadmap/v5/v5.6.9/culebra/`: triage outputs,
  `stage2-baseline.ll`, `stage2-after-fix.ll`, OOM
  reproducer log, and the per-session journal.

What does NOT ship:
- Non-empty `stage3.ll` from the full self-compile.
  `mnc-stage2 mnc_all.mn` segfaults due to a stack overflow;
  with `ulimit -s unlimited` it surfaces a clean **MIR
  verifier error** for empty match-arm blocks
  (`expr_kind::match_arm2: block has no instructions`,
  `expr_kind::match_arm3: ...`). This is a SEPARATE bug —
  reproduces on the **original v5.6.8 binary** with the same
  match-arm error pattern (verified by compiling `/tmp/p3.mn`
  through `/tmp/mnc-stage2` from before the fix). v5.6.8's
  Ve.3 OOM was masking it. Tracked as new **Ve.4** for
  v5.6.10.
- The struct_byte_size patch from v5.6.8. v5.6.9's fix is
  unrelated to ABI sizing — leave it for v5.6.10
  consideration as documented.

---

## Root cause analysis

### What v5.6.8 narrowed

v5.6.8 closed the v5.6.5/v5.6.7 hypothesis matrix:
- A (payload-type builder divergence) — RULED OUT by IR
  inspection
- D (Python emitter bug) — RULED OUT by `mnc-stage1-fromself`
  reproducing
- B (list elem_size mismatch) and C (additional hardcoded
  GEP) — DE-PRIORITISED (not exercised by `p1.mn`)

It surfaced the **third Alloca's `dest.name` is corrupt**
finding: only Value's field 0 (the 16-byte `name: String`)
reads as garbage; field 1 (`ty: MIRType`) reads correctly on
all three calls. v5.6.9 PLAN scoped E (inliner produces
corrupt third Alloca), F (Value field-0 layout divergence),
and G (missing `noalias` on byref params) as candidates.

### What v5.6.9 found

Hypothesis E was **correct in mechanism but wrong in
location**. The bug isn't in `rename_value` or
`clone_instr_for_inline` directly — those produce the
correctly-named Value at clone time. The bug is in
**`emit_drop_glue` at function exit**: when the function
returns a list whose elements (Instruction enums) carry
heap-boxed payload pointers tracked in `boxed_owned`, the
unconditional `free()` of every tracked box leaves dangling
pointers in the returned list. The caller dereferences those
dangling pointers via `instr_dest(inst)` and reads garbage.

### The trace that made it definitive

After v5.6.8's hypothesis space + culebra's slow triage
output, the question was: at what point along
`lowerer → inliner → MIR → emitter` does `dest.name`
become garbage? Three `__mn_str_eprint` instrumentation
points (in `lower.mn::bind_fn_params`,
`mir_opt::clone_instr_for_inline` Alloca branch, and
`emit_llvm.mn::emit_alloca`) plus a fourth at the
`emit_mir_by_kind` dispatch (just before `instr_dest(inst)`)
gave the answer in one stage1+stage2 rebuild cycle:

```
DBG lower bind: addr.name=[%a.addr]                         CORRECT
DBG lower bind: addr.name=[%b.addr]                         CORRECT
DBG clone_inst: pre_dest.name=[%a.addr]                     CORRECT
DBG clone_inst: new_dest.name=[%_inl0_2_a.addr] prefix=...  CORRECT
DBG clone_inst: pre_dest.name=[%b.addr]                     CORRECT
DBG clone_inst: new_dest.name=[%_inl0_2_b.addr]             CORRECT
DBG dispatch alloca: extracted.name=[%a.addr]               CORRECT
DBG emit_alloca:    dest.name=[%a.addr]                     CORRECT
DBG dispatch alloca: extracted.name=[%b.addr]               CORRECT
DBG emit_alloca:    dest.name=[%b.addr]                     CORRECT
DBG dispatch alloca: extracted.name.len=5623822808517230443 extracted.name=[]  CORRUPT
DBG emit_alloca:    dest.name.len=5623822808517230443 dest.name=[]             CORRUPT
mapanare: out of memory (requested 5623822808517230446 bytes)
```

The corruption first appears between `clone_inst`'s push
into `result: List<Instruction>` and the dispatch's later
read via `instr_dest(inst)`. By the time emission reaches
the third Alloca, its dest.name (Value's field 0, an
MnString) is uninitialised heap memory — `len` reads as a
nondeterministic ~5e18 value, `data` reads as a dangling
ptr.

### Why the third Alloca specifically

`/tmp/p1.mn`:
```
fn add(a: Int, b: Int) -> Int { return a + b }
fn main() { print(add(1, 2)) }
```

The lowerer emits 4 Allocas for this program: `add()`'s 2
direct param-slot Allocas (`%a.addr`, `%b.addr` from
`bind_fn_params`), then `inline_small_functions` clones
`add()`'s body into `main()` with prefix `_inl0_2_`,
producing 2 inlined Allocas (`%_inl0_2_a.addr`,
`%_inl0_2_b.addr`). The first 2 emit correctly because the
direct path stores them in the LowerState (a struct return,
which `ret_ty_is_aggregate` correctly skips drops on). The
**third+ Allocas** travel through `clone_instr_for_inline`'s
return path which is `List<Instruction>` — a list runtime
type that is **not aggregate** per the v5.4.1 classification,
so drop_glue runs.

### Why the `boxed_owned` slots get filled

`%enum.Instruction = type {i64, ptr}` in stage2.ll: every
Instruction enum value is `{tag, heap_box_ptr}`. The
`Instruction::Alloca(new_dest, ty)` constructor in
`clone_instr_for_inline` allocates a heap box for the
payload and stores the box ptr in the {tag, ptr} pair. The
emitter tracks every such box via `emit_track_boxed` — the
slot goes into `boxed_owned`. By the time clone_instr_for_inline
returns, every cloned Instruction has produced one `boxed_owned`
entry.

### What drop_glue_boxed sees

`emit_drop_glue` for a list return (`{ptr, i64, i64, i64,
i64}`) extracts the LIST'S data ptr as `ret_list_ptrs[0]`.
It calls `drop_glue_boxed` with `ret_box_ptrs = []` (the
list itself isn't a box). For each `boxed_owned` slot,
`drop_glue_boxed` does `icmp eq ptr` against `ret_box_ptrs`
— always false because the list contains
`{tag, payload_ptr}` pairs and the payload_ptr is NOT the
list's data ptr. So every box is freed.

The boxed payloads ARE referenced through the returned list
(via Instruction enums' payload pointers), but drop_glue's
single-level alias check can't see that — the same shape as
v5.6.6 Rt.04's `St { lines: List<String>, n: Int }` (3
levels deep instead of 2 for our case).

### The fix

Match the v5.6.6 Rt.04 RESCOPE pattern: when returning a
list AND any `boxed_owned` slots are tracked, conservatively
skip ALL drops in this function. The cost is leaks for
intermediate boxes that aren't in the returned list. The
benefit is no UAF.

```mn
// v5.6.9 Ve.3 — List<Enum> return UAF
if ret_ty == llvm_list_rt() && len(st.boxed_owned) > 0 {
    return st
}
```

Inserted at `emit_llvm.mn:4763`, immediately after the
existing `ret_ty_is_aggregate` skip. 25 LOC including the
explanatory comment.

---

## Culebra: what it gave us, what it didn't

The PLAN scoped culebra as the **primary** diagnostic. In
practice, culebra's contribution was bounded — most of the
diagnostic value came from targeted `__mn_str_eprint`
instrumentation. Recording the friction here so v5.6.10+
sessions can adjust expectations and the tool itself can
improve.

### What culebra did contribute

- `triage --brief` confirmed two critical signal classes
  exist in stage2.ll: `function-count-drop` (940 hits) and
  `return-type-divergence` (37 hits). The latter pointed
  at Hypothesis F's territory.
- The `explain return-type-divergence` output (16 seconds
  on stage2.ll, much faster than `triage`) listed every
  matched function — let me visually confirm the template
  was matching aggregate-return runtime declarations rather
  than user code, and pivot away from F as a likely root
  cause.
- The journal mechanism (`culebra journal add`) produced a
  durable log of the investigation that lands in the
  release folder for v5.6.10 starting context.

### What culebra cost us

- **Windows binary, WSL interop required.** `culebra` at
  `/home/uan/.cargo/bin/culebra` is a Windows PE32+
  executable v2.4.0 (the PLAN expected v3.0.0+). It runs
  through WSL's `/init` interop layer and rejects WSL-style
  paths like `/tmp/stage2.ll` with
  `"The system cannot find the file specified"`. Required
  copying the IR file to a Windows-accessible path under
  `/mnt/c/...` and using the C:\-style path string. First
  attempt with WSL-style path appeared to hang silently for
  several minutes before I realised it was an interop
  issue, not slow parsing.
- **Slow on large IR.** `culebra triage --brief` took
  **7m37s** on stage2.ll (207,619 lines). `culebra summary`
  never completed — killed at 5+ minutes. `culebra triage`
  (full, non-brief) took comparable time. This is far too
  slow for a tight iterate-instrument-rebuild loop. After
  one `triage --brief`, I pivoted entirely to eprint
  instrumentation which gave a definitive answer in
  ~2 minutes per stage1+stage2 rebuild cycle.
- **False positives in the loud signals.** The 37
  `return-type-divergence` hits were **all** runtime
  declaration lines with `{ptr, i64}` aggregate returns
  (`__mn_str_concat`, `__mn_str_substr`, `__mn_list_new`,
  `__mn_range`, etc.). These returns are correct — the
  template appears to flag any aggregate return as
  divergent without confirming what the other stage
  actually emits. Investigating these would have been a
  dead end. The PLAN's `.culebra-ignore` mechanism handles
  3 known FP classes; this one isn't documented.
- **Help output incomplete.** The `journal` subcommand
  isn't listed in `culebra --help` even though it works
  (the existing `.culebra-journal.jsonl` had ~50 prior
  entries from earlier releases). Without the prior journal
  file as evidence, I'd have assumed `journal` was a
  v3.0+ feature and skipped it.
- **No parallelism.** Running multiple culebra commands at
  once would have stressed the WSL interop further;
  serially they each take 7+ minutes. The cost isn't
  recoverable through threading in this configuration.

### What culebra didn't surface

The actual root cause — drop_glue_boxed freeing list-element
payloads at function return — wasn't matchable by any
template I ran. The `triage` output's 5 root causes
(`function-count-drop`, `return-type-divergence`,
`fixed-point-delta`, `byte-count-mismatch`,
`stage-output-divergence`) describe symptoms of stage1/stage2
divergence at the IR-text level, not heap-lifecycle bugs.
The `field-index-audit` and `health` subcommands were
designed for layout-class bugs (PHI zeroinit, type-pun, null
loads) — none of which are this bug's class.

### Adjustments for v5.6.10+

If culebra is to remain the primary tool for next session:
1. Build a Linux-native version (avoid WSL interop entirely;
   binary path access at `/tmp/...` would unblock parallelism).
2. Profile and optimise `triage` and `summary` paths for
   200k+ line IR (or split scans by function and aggregate).
3. Either narrow `return-type-divergence` to only cross-stage
   confirmed mismatches (compare main.ll's declaration
   against stage2.ll's), or document it as a known noisy
   template alongside the existing 3 FPs.
4. Add a template class for **drop-glue / lifetime bugs**:
   detect functions that return `{ptr, ...}` (a list) and
   call `@free` on tracked `box_track.*` slots without an
   `icmp eq ptr` against an extracted list-element payload
   ptr. This would have flagged exactly Ve.3's pattern.

If culebra's slowness is structural for the WSL config,
default to eprint instrumentation in v5.6.10+. The 4-eprint
trace that solved Ve.3 took one rebuild cycle (~2 minutes);
the equivalent culebra investigation would have been
40+ minutes.

---

## Ve.4 — match-arm verifier error (newly opened)

`mnc-stage2-fix4 /tmp/p3.mn` (a simple 2-arm match) and
larger inputs hit:

```
error: MIR verifier detected malformed IR before emission:
  apply::match_arm2: block has no instructions
```

Reproduces on the **original v5.6.8 mnc-stage2** binary
(verified independently): this bug existed in v5.6.8 but was
masked by Ve.3's earlier OOM in the same compilation
pipeline. Now that Ve.3 is closed, programs that exercise
match expressions (including `mnc_all.mn` itself, which
makes heavy use of match for AST/MIR enum discrimination)
fail at the verifier before stage3 emission can begin.

**What it likely is** (NOT root-caused this release):
match-arm lowering produces a basic block whose body is
empty when the arm body is a single tail expression like
`return "..."`. The Python-built stage1 lowers correctly
(goldens 64/66 pass through stage1+lli), so the bug is
specifically in how stage1 compiled the self-hosted
lowerer's match-arm-handling code into stage2.ll. In other
words: the source code is correct, but stage1's emit of it
into stage2.ll produces a binary that, when run, generates
malformed MIR for match expressions.

**Stack overflow caveat**: under the default 8 MB stack,
`mnc-stage2 mnc_all.mn` SIGSEGVs at a stack address before
the verifier can fire. `ulimit -s unlimited` lets the
verifier surface the actual malformed-MIR cause. v5.6.8
SESSION_REPORT attributed mnc_all.mn's SIGSEGV to Ve.3 — in
fact it's the stack-overflow surfacing of Ve.4 that v5.6.9
now exposes cleanly with `ulimit`.

Tracked as Ve.4 in `docs/known_issues.md`. Scoped for
v5.6.10 alongside the broader emit_drop_glue conservatism
tightening (currently the v5.6.9 fix only fires on `boxed_owned`;
attempting `len(str_owned) > 0` ALSO triggers the same
match-arm bug, suggesting it's reachable without my fix as
well, just with different memory contents).

---

## Phase-by-phase summary

### Phase 0 — baseline (10 min)

```
echo "5.6.9" > VERSION
make build-rt
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1
# 64/66 PASS (matches v5.6.8 baseline)

mapanare/self/mnc-stage1 mapanare/self/mnc_all.mn > /tmp/stage2.ll
# stage1 RC=0, stage2.ll 207,619 lines, llvm-as OK

build /tmp/mnc-stage2 from stage2.ll via clang -O2 + gcc link
/tmp/mnc-stage2 /tmp/p1.mn → RC=1, lines=0, OOM (5,211,334,405,724,985,539 bytes)
```

### Phase 1 — culebra triage (40 min, see §Culebra above)

- `triage --brief`: 5 root causes, 15748 findings: 2 critical
  (function-count-drop, return-type-divergence)
- `explain return-type-divergence`: 37 hits, all runtime
  declarations (FP, not real signal)
- pivoted to eprint after recognising the per-command
  cost was ~7 minutes

### Phase 2/3/4 — hypothesis testing (60 min)

**Hypothesis G (noalias on byref) — RULED OUT.**
Hand-patched stage2.ll with `noalias` on every `ptr %X.byref`
in function signatures (79 patches). `mnc-stage2-na /tmp/p1.mn`
still OOMs (different garbage size, same signature). Same
memory-corruption pattern.

**Hypotheses E and F via eprint instrumentation —
combined approach.** Added 3 eprints:
1. `lower.mn::bind_fn_params` — direct Alloca creation
2. `mir_opt.mn::clone_instr_for_inline` Alloca branch —
   inliner-cloned Alloca creation, both pre and post
   `rename_value`
3. `emit_llvm.mn::emit_alloca` — emission read

Then a 4th at `emit_mir_by_kind` dispatch (`instr_dest(inst)`
extraction). The trace pinpointed corruption first appearing
between clone_inst's push and dispatch's read — i.e. between
MIR storage and emit-time read. This is incompatible with
hypotheses about rename_value or about Value layout (those
would corrupt at clone time, not later).

The remaining suspect: function exit code (drop-glue) freeing
heap-allocated Value names (which are MnStrings allocated by
`"%" + prefix + ...` concat).

Followed up with a disable-inlining test (`should_inline →
return false`) — the OOM disappeared, confirming the bug is
specifically along the inlining path. Then traced the exit
code of `clone_instr_for_inline` in stage2.ll: 48 calls to
`@free(ptr)` with no `icmp eq ptr` aliasing checks. Match.

### Phase 5 — fix + validate (30 min)

```mn
if ret_ty == llvm_list_rt() && len(st.boxed_owned) > 0 {
    return st
}
```

Inserted at `emit_llvm.mn:4763`. Rebuilt stage1, stage2,
re-tested:
- `/tmp/p1.mn`: RC=0, 215 lines, llvm-as clean ✓
- `mnc_all.mn`: RC=139 (segfault) — but on Ve.4 (match-arm
  verifier bug surfacing as stack overflow under default
  stack limit)

Tried broadening the fix to `len(str_owned) > 0 ||
len(list_owned) > 0 || len(boxed_owned) > 0`: introduces
the SAME Ve.4 match-arm error on programs as small as p3.mn.
Reverted to the narrower `boxed_owned`-only condition; the
match-arm error STILL appears for mnc_all.mn — confirming
Ve.4 is independent of the fix's breadth.

### Phase 6/7 — sanitizer gate + goldens

- Goldens harness: 64/66 (`51_match_guards_and_or` B and
  `64_closure_typed` Sh.7 are the same 2 fails as v5.6.8;
  diff shows only timing variation)
- ASan UAF sweep: 0 errors / 65 CLEAN / 1 CRASH_NO_ASAN
  (matches baseline)
- Valgrind sweep: 0 errors / 66 WARNINGS_ONLY (matches
  baseline)
- LSan baseline gate: PASS (no leak regressions, 62_list_output
  unchanged at 9 / 141 B per Rt.04 v5.6.6 RESCOPE)
- Non-bootstrap pytest: 5584 passed, 116 skipped, 9 xfailed
- `make lint`: clean
- `check_struct_registry.py`: 23/23/91 clean

### Phase 8/9 — docs

This file. CLAUDE.md / known_issues.md / ROADMAP.md / 
PARITY_GAPS.md updates.

---

## Metrics

- `VERSION`: 5.6.8 → 5.6.9
- `mapanare/self/mnc-stage1`: 6,270,112 bytes (rebuilt;
  +0 vs v5.6.8 — strip-pruned size identical, source delta
  is 25 LOC compressed away)
- `stage2.ll`: 207,619 → **201,743 lines (−2.83%)**, llvm-as
  clean. Reduction comes from skipping 5,876 lines of
  drop-glue extracts/free calls in ~12 list-returning
  functions across `mir_opt` / `lower` / `emit_llvm`.
- Goldens harness: **64/66** preserved (no regressions; same
  2 fails: `51_match_guards_and_or` B and `64_closure_typed`
  Sh.7)
- ASan UAF sweep: 0 ASAN_ERROR / 65 CLEAN / 1 CRASH_NO_ASAN
- Valgrind sweep: 0 ERRORS / 66 WARNINGS_ONLY
- LSan baseline gate: PASS
- Non-bootstrap pytest: 5584 passed, 116 skipped, 9 xfailed
- `make lint`: clean
- `check_struct_registry.py`: 23/23/91 clean
- Reproducer: `mnc-stage2 /tmp/p1.mn` 0 lines OOM →
  **215 lines llvm-as clean RC=0**
- `mnc-stage2 mnc_all.mn`: 0 lines SIGSEGV (default stack)
  → 0 lines MIR verifier error (Ve.4) under
  `ulimit -s unlimited`

---

## What's next

- **v5.6.10** — close Ve.4 (match-arm lowering producing
  empty blocks in self-hosted compiled code) and revisit
  the v5.6.8 struct_byte_size patch. Estimated 1 session.
  After Ve.4 closes, mnc_all.mn → stage3.ll should produce
  non-empty IR and the fixed-point can be re-evaluated.
- **v5.6.11+** — Ve.2 residuals (18 × 384-byte floor sites)
  + struct_byte_size hardening if the patch proves
  load-bearing post-Ve.4.
- **v5.7.0** — Sh.7 closure + B or-pattern → 66/66.
- **v5.7.1** — SPEC docs polish.
- **v5.8.0** — RE-PANEL.

The closeout arc continues: v5.6.5 (Ve.1) → v5.6.6 (Rt.04
RESCOPED) → v5.6.7 (Ve.2 PARTIAL) → v5.6.8 (Ve.3
investigation) → **v5.6.9 (Ve.3 root cause closed; Ve.4
opened)** → v5.6.10 (Ve.4 close) → v5.7.x panel.

---

## Out of scope

- The full self-compile fixed-point (waits on Ve.4).
- The v5.6.8 struct_byte_size patch.
- Multi-level alias analysis for drop-glue (v6.0
  borrow-checker scope).
- Sh.7 / B work (v5.7.0).

---

## Why ship v5.6.9 now

Ve.3 has been the primary self-hosting blocker since v5.6.4
(four releases). v5.6.9 closes its root cause cleanly with a
25-LOC fix that matches the existing v5.6.6 RESCOPE pattern.
Goldens preserved, sanitizer gates clean, primary reproducer
fixed. The stage3.ll fixed-point exit criterion remains
unmet — but blocked by an independent bug (Ve.4) that v5.6.8
was masking, not by Ve.3 itself.

Per v5.6.6's "Rt.04 attempted + RESCOPED" precedent, shipping
honest scoping over premature closure is the right call: the
investigation surface for v5.6.10 is now Ve.4 (match-arm
lowering), not Ve.3 (drop-glue UAF). Future-Claude starts
with a tighter target than v5.6.8 left.
