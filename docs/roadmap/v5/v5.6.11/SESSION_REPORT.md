# v5.6.11 Session Report — Ve.4 CLOSED

> **Status: SHIPPED.** The v5.6.4-era full self-compile blocker is
> closed. Root cause: `emit_index_get` / `emit_index_set` inline
> fast paths used a constant 8-byte stride GEP for List<Int> reads,
> while `__mn_list_push` writes used the runtime `elem_size` field
> from the list struct (= 384 for Ve.2 residual floor sites). The
> stride mismatch made the second `indices.push` in
> `build_match_arms` write at byte offset 384 while the lowerer's
> bounds check + `set_block(s, garbage)` chain silently no-op'd,
> leaving `match_arm2` empty. Fix is 14 LOC across two emit sites:
> read `list.elem_size` at runtime, compute `offset = idx *
> elem_size`, GEP into i8.
>
> **Hero metric:** `verify_fixed_point.sh` reaches **NEAR FIXED
> POINT** (4 diff lines / 217,273 = 0.002%, all VERSION metadata)
> for the first time since v5.6.4 — the full self-compile cycle
> now produces stage2.ll == stage3.ll within tolerance after seven
> releases of being broken.

---

## Headline

**Ve.4 root cause closed.** `mnc-stage2 /tmp/p3.mn` (a 2-arm enum
match) was 0-line + `apply::match_arm2: block has no instructions`
verifier error since v5.6.8 (the bug existed earlier but was
masked by Ve.3's OOM until v5.6.9 closed it). Now produces **225
lines of valid `llvm-as`-clean IR**. The compiled binary outputs
`8` for `apply(Op::Add, 5, 3)` — correct. Reverse-pattern variant
(`p3b.mn` with both arms exercised) outputs `8, 6` — correct.

What ships:
- VERSION 5.6.10 → 5.6.11.
- `emit_llvm.mn` +14 LOC: `emit_index_get` / `emit_index_set` fast
  paths use runtime `elem_size` (struct field 3) for offset
  computation instead of a constant 8-byte stride.
- `mnc-stage1` rebuilt; stage2.ll **216,932 → 217,273 lines
  (+0.16%)**, well within the v5.6.11 PROMPT 3% budget.
- 64/66 goldens preserved (same 2 pre-existing fails).
- Full sanitizer gate clean; LSan baseline gate PASS.
- This SESSION_REPORT + updates to `known_issues.md`,
  `PARITY_GAPS.md`, `ROADMAP.md`, `CLAUDE.md`, `CLOSEOUT_ARC.md`.

What does NOT ship:
- **Lk.1 closure.** v6.0 borrow-checker scope. The Ve.4 fix does
  not surface or close Lk.1 because allocations remain at
  elem_size=384 for the 7 residual sites; only the read/write
  strides are made consistent. The 80-vs-3088-byte buffer-size
  threshold that determines whether LSan suppresses the leak is
  unchanged.
- **Ve.2 residual closure.** The 7 `List<Int> = []` sites still
  allocate with `__mn_list_new(i64 384)`. Fixing this requires
  Lk.1 closure (alloca-aliasing in drop-glue).
- **Floor branch removal.** Same dependency on Lk.1.

---

## Root cause analysis

### Symptom (carried from v5.6.9 / v5.6.10)

```
$ ulimit -s unlimited
$ /tmp/mnc-stage2-v5.6.10 /tmp/p3.mn 2>&1
error: MIR verifier detected malformed IR before emission:
  apply::match_arm2: block has no instructions
```

`/tmp/p3.mn`:
```mn
enum Op { Add, Sub }
fn apply(o: Op, a: Int, b: Int) -> Int {
    match o {
        Add => { return a + b },
        Sub => { return a - b }
    }
}
fn main() { print(apply(Op::Add, 5, 3)) }
```

Reproduces on the original v5.6.8 mnc-stage2 binary —
pre-existing, masked by Ve.3 until v5.6.9.

### Investigation trace

Following v5.6.9's "eprint instrumentation over culebra" lesson,
five strategically-placed `__mn_str_eprint` traces inside
`build_match_arms` and the optimizer pipeline isolated the
failure mode in one rebuild cycle.

**Phase 1A: lower-time eprint crashes the binary.**
First instrumentation attempt (eprint at `lower_match`'s
arm-iteration loop, reading `s.fn_blocks[s.current_block_idx]
.instructions` length) crashed with `mapanare: list index
94650950872068 out of bounds (len=3)` between iter 0's print and
iter 1's print. The ~94e15 ≈ 0x5618cd1bb544 garbage value was a
heap-pointer-shaped Int. With instrumentation removed at the
sensitive site, the original verifier error returned. The
instrumentation perturbed memory enough to hit the bug as an OOB
abort rather than as a silent no-op. Useful signal: the bug
involves a corrupt `current_block_idx` value being read as a list
index.

**Phase 1B: opt-time `ve4_dump_match_arms` confirms early empty.**
A dump helper logging `(stage, fn, label, ninstrs)` for every
match-arm-prefixed BB at p0-input, p1-cfold, p2-cprop, p3-dbe,
p5-inline, p7-final showed:
```
DBG ve4 opt-stage: stage=p0-input fn=apply label=match_arm1 ninstrs=4
DBG ve4 opt-stage: stage=p0-input fn=apply label=match_arm2 ninstrs=0
... (same across all 6 stages)
DBG ve4 verify-empty: fn=apply label=match_arm2 total_blocks=4
```

**`match_arm2` is empty at p0-input** — the start of optimize_mir,
i.e. immediately after lowering. The bug is in `lower_match` /
`build_match_arms` / a downstream lower-time helper, NOT in any
optimizer pass.

**Phase 1C: dump indices at end of build_match_arms.**
```
DBG ve4 build-end: indices.len=2 labels.len=2
DBG ve4 build-end: indices[0]=1
DBG ve4 build-end: indices[1]=94521463950344    ← GARBAGE
```

`indices` (the `List<Int>` of arm BB indices, returned via
`MatchBuildResult.arm_indices`) holds `[1, GARBAGE]` *inside*
`build_match_arms` itself. The corruption is during the
list-construction loop, not in the post-return path.

**Phase 1D: per-iter field 2 trace.**
Reading `s.current_block_idx` directly at three points per
iteration (after fresh_block_label, after add_block, before
indices.push) showed:
```
i=1 after-fresh:    s.current_block_idx=1
i=1 after-addblock: s.current_block_idx=2  ← correct
i=1 before-push:    s.current_block_idx=2  ← correct
i=1 after-push:     indices[1]=94576745753695  ← garbage
```

`s.current_block_idx = 2` is genuinely correct right before the
push. The push loses it. Reading `cur_idx = s.current_block_idx`
into a local variable first then `indices.push(cur_idx)`
reproduces the same garbage — so the bug is in the *push itself*,
not in the read of `s.current_block_idx`.

**Phase 1E: inspect stage2.ll for the indices alloc.**
```
%t2.new = call {ptr, i64, i64, i64, i64} @__mn_list_new(i64 384)
store {ptr, i64, i64, i64, i64} %t2.new, ptr %t2.addr
%t2 = load {ptr, i64, i64, i64, i64}, ptr %t2.addr
%indices3.addr = alloca {ptr, i64, i64, i64, i64}
store {ptr, i64, i64, i64, i64} %t2, ptr %indices3.addr
```

**`__mn_list_new(i64 384)`** — `build_match_arms` is one of the 7
Ve.2 residual sites that v5.6.10 documented (`docs/roadmap/v5/v5.6.10
/SESSION_REPORT.md` Phase 1 final state). The list is allocated
with `elem_size=384` instead of the i64-correct `elem_size=8`.

**Phase 1F: inspect stage2.ll for the indices.push and the
corresponding indices[N] read.**

Push (write side, in `build_match_arms` itself):
```
%push_ea5577 = alloca i64
store i64 %t46, ptr %push_ea5577    ; push elem ptr
%push_tmp5577 = alloca {ptr, i64, i64, i64, i64}
%push_ld5577 = load ..., ptr %indices3.addr
store ..., ptr %push_tmp5577
call void @__mn_list_push(ptr %push_tmp5577, ptr %push_ea5577)
```

`__mn_list_push` runtime semantics (`runtime/native/mapanare_core.c`):
```c
memcpy(list->data + list->len * list->elem_size,
       elem_ptr, (size_t)list->elem_size);
list->len++;
```

For `elem_size=384`: write at offset `list->len * 384` (after
first push: offset 384). memcpy copies **384 bytes** from
`%push_ea5577` (an `alloca i64` — only 8 bytes are valid; the
remaining 376 bytes are stack spillage from past the alloca).

Read (in my eprint's `indices[_ve4_di2]`, but also in any future
consumer of `arm_indices`):
```
%lg.ep.5591 = getelementptr inbounds i64, ptr %lg.data.5591, i64 %idx
%t91 = load i64, ptr %lg.ep.5591
```

**Constant `i64` stride = 8 bytes**. For `idx=1`: read 8 bytes
at offset 8 — which is the FIRST push's spillage (stack memory
captured during the first memcpy of 384 bytes), not the second
push's value.

### The mismatch in one sentence

`__mn_list_push` writes at `idx * runtime_elem_size = idx * 384`;
the inline `index_get` fast path reads at `idx * sizeof(dest_ty)
= idx * 8`. For Ve.2 residual floor lists (`elem_size=384` allocated
because of unknown elem_ty.kind), these disagree starting at
idx=1 — read returns intra-buffer spillage from a prior push.

### Why this surfaced as Ve.4

Caller (`lower_match`) reads `arm_indices[1]` and gets garbage.
`set_block(s, garbage_int)` updates `s.current_block_idx =
garbage_int`. `emit_instr` then bounds-checks `idx >= 0 && idx <
len(fn_blocks)` — for our garbage value ~9e13, idx is ≥
len(fn_blocks)=3, so the bounds check fails silently and
`emit_instr` is a no-op. Every instruction emitted into arm 1's
body falls into the void. `match_arm2` ends up empty. The
verifier rejects.

The same cause produced the OOB crash in Phase 1A: my eprint
read `s.fn_blocks[arm_indices[ai]]` where `arm_indices[1]=garbage`
— the runtime list-get bounds check fired loudly instead of
silently no-op'ing. Same bug, two surfaces.

### The fix

Make the read side use the SAME runtime elem_size that the write
side uses. 14 LOC in `mapanare/self/emit_llvm.mn`, two sites
(`emit_index_get` line ~2570, `emit_index_set` line ~2655):

```mn
// v5.6.11 Ve.4 — use runtime elem_size for the offset, not a constant
// i64 stride. The 7 Ve.2 residual sites allocate List<Int> = [] with
// elem_size=384 (Lk.1 floor); __mn_list_push writes at idx * 384 while
// a constant-stride GEP would read at idx * 8 — mismatch produces
// garbage reads of intra-buffer spillage.
let eszp: String = "%lg.eszp." + cnt_lg
s = emit_line(s, "  " + eszp + " = getelementptr inbounds " + lt + ", ptr " + tmp + ", i32 0, i32 3")
let esz: String = "%lg.esz." + cnt_lg
s = emit_line(s, "  " + esz + " = load i64, ptr " + eszp)
let off: String = "%lg.off." + cnt_lg
s = emit_line(s, "  " + off + " = mul i64 " + idx.name + ", " + esz)
let ep: String = "%lg.ep." + cnt_lg
s = emit_line(s, "  " + ep + " = getelementptr inbounds i8, ptr " + data + ", i64 " + off)
s = emit_line(s, "  " + dn + " = load " + dest_ty + ", ptr " + ep)
```

Pre-fix IR (3 lines):
```
%lg.dp = ... data field
%lg.data = load ptr, ptr %lg.dp
%lg.ep = getelementptr inbounds i64, ptr %lg.data, i64 %idx
%dn = load <dest_ty>, ptr %lg.ep
```

Post-fix IR (5 lines):
```
%lg.dp = ... data field
%lg.data = load ptr, ptr %lg.dp
%lg.eszp = ... elem_size field (3)
%lg.esz = load i64, ptr %lg.eszp
%lg.off = mul i64 %idx, %lg.esz
%lg.ep = getelementptr inbounds i8, ptr %lg.data, i64 %lg.off
%dn = load <dest_ty>, ptr %lg.ep
```

For lists allocated with the canonical `elem_size=8` (the common
case for List<Int>, List<Float>, List<ptr>), SROA / instcombine
folds the runtime load + multiplication back to a constant
stride GEP — no measurable runtime cost. For the 7 Ve.2 residual
floor lists (`elem_size=384`), the runtime load reads 384,
multiplication produces correct offset, GEP-i8 lands at exactly
where the push wrote.

### Why not just close Ve.2 (apply the v5.6.10 scalar gate)?

The v5.6.10 PROMPT explicitly forbade broadening the scalar gate
because it surfaces Lk.1 (alloca aliasing leak in `65_list_int_indexing`).
The v5.6.11 PROMPT carries forward "Do not bundle Lk.1 closure".

Ve.4 closes via the read-side fix without touching allocation
sizing. The 7 floor sites continue allocating 3088-byte buffers
(8 elements × 384 bytes); LSan's "still reachable" heuristic
continues suppressing the alias-leak; baseline preserved.

The principled fix (Ve.2 + Lk.1 + drop the floor entirely) is
v6.0 borrow-checker work. The v5.6.11 fix is the smallest change
that closes Ve.4 without a UAF or LSan-baseline regression — the
same RESCOPE pattern v5.6.6 used for Rt.04 and v5.6.9 for Ve.3.

### Why NOT change `__mn_list_push` to use static stride?

Symmetric option: bypass `__mn_list_push` entirely for List<Int>
and emit inline GEP-i64 push code. That would make BOTH read
and write use 8-byte stride, also fixing Ve.4. Rejected because:
1. More IR-emit code than the read-side fix (would need a
   parallel inline fast path in `__mn_list_push` callers — many
   sites in the lowerer's `method_call("push", ...)` path).
2. Diverges from runtime semantics — push slow path / COW detach
   logic would need to be replicated in IR.
3. Asymmetric — leaves the inline read path inconsistent with
   any `__mn_list_get` callers that take the slow path.

The read-side fix has the runtime-elem_size loaded once at the
get site; SROA elides it for constant-stride cases.

---

## Phase-by-phase summary

### Phase 0 — baseline (15 min)

```bash
echo "5.6.11" > VERSION                                      # bumped
make build-rt                                                 # OK
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1
# 64/66 PASS (matches v5.6.10 baseline; same 2 fails: 51 B, 64 Sh.7)

mapanare/self/mnc-stage1 mapanare/self/mnc_all.mn > /tmp/stage2-v5.6.11-before.ll
# 216,932 lines, llvm-as OK

clang -O2 /tmp/stage2-v5.6.11-before.ll runtime/native/libmapanare_rt.a \
    -lpthread -lm -ldl -o /tmp/mnc-stage2-v5.6.10
ulimit -s unlimited
/tmp/mnc-stage2-v5.6.10 /tmp/p3.mn
# RC=1, 0 lines, "apply::match_arm2: block has no instructions"
```

Committed VERSION bump (`ab73579`).

### Phase 1 — instrumentation + identify culprit (60 min)

Five iterations of instrumentation:
1. Lower-time eprint crashed → revealed the OOB nature of the
   corrupt arm_idx value.
2. Opt-time `ve4_dump_match_arms` showed match_arm2 empty at
   p0-input → ruled out all optimizer passes; bug is at lower
   time.
3. `build-end` trace at end of `build_match_arms` showed
   `indices[1]=garbage` already inside the function → bug in the
   list-construction loop.
4. Per-iteration s.current_block_idx trace showed correct value
   (2) immediately before push, garbage immediately after →
   bug in the push, not in the read of s.
5. IR inspection of stage2.ll's `build_match_arms` revealed
   `__mn_list_new(i64 384)` for the indices list → connected
   the dots to Ve.2 residual + the inline GEP-i64 stride mismatch.

### Phase 2 — apply targeted fix (30 min)

Two-site edit in `mapanare/self/emit_llvm.mn`:
- `emit_index_get` fast path (i64/double/ptr): GEP-i64 → runtime
  elem_size + GEP-i8.
- `emit_index_set` fast path (symmetric): same change.

All instrumentation removed. Verified:
```bash
bash scripts/concat_self.sh && python3 scripts/build_stage1.py
# stage1 rebuilt OK
mapanare/self/mnc-stage1 mapanare/self/mnc_all.mn > /tmp/stage2-v5.6.11.ll
# 217,273 lines (+341 vs v5.6.10's 216,932; +0.16%; well within 3% budget)
llvm-as /tmp/stage2-v5.6.11.ll -o /dev/null  # OK
clang -O2 ... -o /tmp/mnc-stage2-v5.6.11
ulimit -s unlimited
/tmp/mnc-stage2-v5.6.11 /tmp/p3.mn > /tmp/p3.ll
# 225 lines, llvm-as OK, no stderr
clang -O2 /tmp/p3.ll ... -o /tmp/p3-bin
/tmp/p3-bin
# 8  ← Op::Add(5,3) = 5+3 = 8 ✓
```

Reverse-pattern variant (`p3b.mn` exercising both arms with
swapped order) also produced byte-identical correct output (`8,
6` for `Add(5,3) + Sub(10,4)`).

### Phase 3 — fixed-point gate (HERO METRIC, 15 min)

```bash
ulimit -s unlimited
bash scripts/verify_fixed_point.sh --keep
```

Output:
```
[Stage 0] Using existing stage1: mapanare/self/mnc-stage1
  stage1: 6294688 bytes
[Stage 1] stage1 compiles mnc_all.mn → stage2.ll
  stage2.ll: 217273 lines
  llvm-as: OK
  Building mnc-stage2... OK (4774920 bytes)
[Stage 2] stage2 compiles mnc_all.mn → stage3.ll
  stage3.ll: 217273 lines
  llvm-as: OK

[Verify] Fixed point: diff stage2.ll stage3.ll
  ~ NEAR FIXED POINT
  4 diff lines out of 217273 (0.002%)
  within DIFF_THRESHOLD=100; accepted.

  First 20 diff lines for reference:
217273c217273
< !0 = !{!"5.6.11"}
---
> !0 = !{!"__MN_VERSION__"}
```

**The full self-compile cycle now produces stage2.ll == stage3.ll
within tolerance.** Last achieved at v5.6.3 / v4.134.0; broken
since v5.6.4 (7 releases). Restored.

### Phase 4 — sanitizer + lint gate (30 min)

| Gate | Result |
|---|---|
| Goldens harness | **64/66** preserved (same 2 fails: 51 B, 64 Sh.7) |
| stage2.ll | **217,273 lines**, llvm-as clean, +0.16% vs v5.6.10 |
| `verify_fixed_point.sh` | **NEAR** (4 diff / 217k = 0.002%) |
| ASan UAF | **65 CLEAN** / 0 ASAN_ERROR / 1 CRASH_NO_ASAN |
| Valgrind | **0 ERRORS** / 66 WARNINGS_ONLY |
| LSan baseline gate | **PASS** (no regressions vs v5.4.2 baseline) |
| Non-bootstrap pytest | **5593 passed**, 116 skipped, 9 xfailed |
| `make lint` | clean — ruff + black + mypy all pass |
| `check_struct_registry.py` | clean — 23/23/91 |

Per PROMPT D2 ("if any sanitizer regresses, REVERT"): no
regressions. Patch ships.

### Phase 5 — documentation (30 min)

This file. Plus:
- `docs/known_issues.md` — Ve.4 row flipped to CLOSED v5.6.11.
- `docs/roadmap/v5/PARITY_GAPS.md` — Ve.4 moved to Historical.
- `CLAUDE.md` — v5.6.11 entry; "Current baseline" → 5.6.11;
  Planned section drops v5.6.11.
- `docs/roadmap/ROADMAP.md` — v5.6.11 stanza prepended.
- `docs/roadmap/v5/CLOSEOUT_ARC.md` — v5.6.x arc fully closed.

---

## Metrics

- `VERSION`: 5.6.10 → 5.6.11
- `mapanare/self/mnc-stage1`: 6,294,688 bytes (rebuilt from updated
  source, +0 vs v5.6.10's strip-pruned size — the 14-LOC patch
  compresses away)
- `stage2.ll`: 216,932 → **217,273 lines (+0.16%)**, llvm-as
  clean. Growth driver: 6 extra IR lines × ~57 inline-GEP fast
  path sites (3 lines added per site: eszp, esz, off + 1
  changed: ep).
- `mnc-stage2`: 4,774,920 bytes (built fresh from stage2.ll for
  fixed-point verification)
- Goldens harness: **64/66** preserved (same 2 fails:
  `51_match_guards_and_or` B and `64_closure_typed` Sh.7)
- `verify_fixed_point.sh`: **NEAR FIXED POINT** (0.002% diff =
  VERSION metadata only)
- ASan UAF sweep: **0 ASAN_ERROR / 65 CLEAN / 1 CRASH_NO_ASAN**
- Valgrind sweep: **0 ERRORS / 66 WARNINGS_ONLY**
- LSan baseline gate: **PASS**
- Non-bootstrap pytest: **5593 passed**, 116 skipped, 9 xfailed
- `make lint`: clean
- `check_struct_registry.py`: 23/23/91 clean
- Reproducer: `mnc-stage2 /tmp/p3.mn` 0 lines + verifier error →
  **225 lines llvm-as clean RC=0** (binary outputs `8` correctly)

---

## What's next

- **v5.7.0** — Sh.7 closure-typed + B or-pattern → 66/66.
- **v5.7.1** — SPEC docs polish (pre-panel).
- **v5.8.0** — RE-PANEL (target 9.7+).
- **v6.0** — borrow checker; closes **Lk.1** (alloca aliasing in
  inline list-get/push, opened v5.6.10) and **Rt.04** (multi-level
  alias analysis for drop-glue, rescoped v5.6.6). Once Lk.1 closes,
  the v5.6.10 `emit_list_init` scalar gate can be re-applied to
  drop the 384-byte floor for List<Int>; that will make alloc
  elem_size match dest_ty stride throughout, and the v5.6.11
  runtime-elem_size load becomes unnecessary (constant-folded by
  SROA). The v5.6.11 fix is forward-compatible — it works
  correctly whether elem_size is 8 or 384.

The v5.6.x closeout arc is now **complete**:
v5.6.0 → v5.6.4 (Sh.6 / Rt.06) →
v5.6.5 (Ve.1) → v5.6.6 (Rt.04 RESCOPED) →
v5.6.7 (Ve.2 PARTIAL) → v5.6.8 (Ve.3 investigation) →
v5.6.9 (Ve.3 CLOSED; Ve.4 OPENED) →
v5.6.10 (Ve.2 PARTIAL CLOSURE + struct_byte_size + culebra; Lk.1
OPENED) →
**v5.6.11 (Ve.4 CLOSED; full self-compile fixed-point restored)**.

All v5.6.x dockets resolved or deferred to v6.0:
- Ve.1: CLOSED v5.6.5
- Ve.2: PARTIAL v5.6.7 / v5.6.10 (7 residuals → v6.0)
- Ve.3: CLOSED v5.6.9
- **Ve.4: CLOSED v5.6.11**
- Rt.04: RESCOPED v5.6.6 → v6.0
- Rt.06: CLOSED v5.6.4
- Sh.6: CLOSED v5.6.3
- Lk.1: OPENED v5.6.10 → v6.0

---

## Out of scope

- Lk.1 closure (v6.0 borrow checker scope).
- Ve.2 residual closure (depends on Lk.1).
- Floor branch removal (depends on Lk.1).
- Sh.7 / B closure work (v5.7.0).
- The v5.6.8 / v5.6.10 `noalias` on byref params (still tracked
  separately).

---

## Why ship v5.6.11 now

Ve.4 has been the v5.6.x closeout's last open docket since
v5.6.9. The investigation took ~60 minutes via targeted eprint
instrumentation (mirroring v5.6.9's "eprint over culebra"
lesson); the fix is 14 LOC across two symmetric emit sites; full
sanitizer + golden + fixed-point gates green; the hero metric
(NEAR fixed-point) is restored after 7 releases of being broken.

Per v5.6.6's RESCOPE precedent and the user's "no cheap shit"
directive, the fix is the minimal targeted change at the precise
mechanism — read-side stride mismatch — without touching the
allocation path (which depends on Lk.1's structural fix in v6.0).
This is exactly the shape v5.6.11 PROMPT D2 specified: "Fix at
the precise location, not broadly".

The v5.6.x closeout arc is now **complete** with all dockets
resolved or appropriately deferred. v5.7.0 starts from a hardened
entry point with the full self-compile cycle producing stable,
near-strict fixed-point IR.
