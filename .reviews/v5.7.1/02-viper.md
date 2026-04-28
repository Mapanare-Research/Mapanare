# Panel v5.8.0 — Viper (Memory Safety)

**Score:** 9.9 / 10
**Grade:** EXCEEDS
**Delta vs v5.2.0:** +0.2

## Summary

The single biggest item on my carry-forward list — **Own.1 Phase 2** —
is closed. I have been carrying it since v4.99.0. At v4.154.0 I called
it "the wall" and "the ceiling." At v5.2.0 I described it as "the
structural ceiling" and gave it -0.3 of headroom toward 10.0. The
closeout is not a one-shot patch but a structurally-clean five-release
arc (v5.4.0 infrastructure → v5.4.1 tracking + helpers → v5.4.2
LSan-gated → v5.4.3 loop-reassignment Rt.03 → v5.4.4 Move-aware
source arrays). It then extends across two new resource classes
(Rt.05 async coroutines v5.5.7, Rt.06 tensors v5.6.4) without any
shape divergence — same per-resource helper structure, same
alias-check-against-ret-ptrs pattern, same source-array `is_moved`
gate. I audited every helper. The implementation is sound.

The v5.6.x memory-safety closeout is also genuine. Five separate
dockets (Ve.1 / Ve.2 / Ve.3 / Ve.4 / Lk.1) all closed at structural
root causes, not as workarounds. The Lk.1 closure (v5.6.12) is
particularly notable: the lead chose destination-passing semantics
in `lower.mn::lower_let` (rustc-style `PlaceRef`-based codegen)
instead of multi-level alias analysis. That is the **right** answer
— it eliminates the duplicate alloca that creates the alias rather
than reasoning about it. One alloca, one tracking entry, no copy,
no leak. The same pattern extends to struct let-bindings in v5.6.13.

The valgrind sweep at v5.8.0 is **63 CLEAN / 2 ERRORS / 1 LINK_FAIL**
across 66 goldens. The 2 ERRORS are 39_gpu_detect / 40_gpu_tensor
— the same Mesa/Vulkan ICD-loader dlopen failures I documented at
v5.2.0, third-party not Mapanare code. Zero memory-safety errors
in any compiler-emitted code, including the 12 newly-passing goldens
(5 async + 5 tensor + Sh.7 + B). LSan baseline-gated; ASan/TSan
clean on the C runtime; no leak regressions.

The score moves from 9.7 to 9.9. The remaining 0.1 of headroom is
**Rt.04** (multi-level alias analysis for `62_list_output` — depth-2
struct→list→string aliasing). The lead correctly scoped this to
v6.0 (borrow checker) after the v5.6.6 attempt reproduced a
heap-use-after-free under ASan; that's the right call (UAF >
documented leak), but it is not free — I cannot give 10.0 while a
known leak class lives in the baseline TSV.

---

## What improved since v5.2.0

### Own.1 Phase 2 — CLOSED (the 28-panel item)

At v5.2.0 I wrote the carry-forward as:

> Self-hosted emitter has no drop-glue, no move tracking, no
> `moved_locals` in EmitState. Phase 2 design documented in
> `docs/roadmap/v5/v5.1.3/DESIGN.md`. The specific
> `register_struct` / `register_enum` UAFs are closed (P1), but the
> general pattern — ownership transferred without compiler
> enforcement — persists throughout the lowerer.

All five elements are now present:

**(1) Drop-glue helpers in `emit_llvm.mn`.**

```bash
$ grep -c "emit_drop_glue" mapanare/self/emit_llvm.mn
33

$ grep -n "^fn emit_drop_glue" mapanare/self/emit_llvm.mn
4486:fn emit_drop_glue_strings(st: EmitState, ret_str_ptrs: List<String>) -> EmitState
4523:fn emit_drop_glue_lists(st: EmitState, ret_list_ptrs: List<String>) -> EmitState
4559:fn emit_drop_glue_boxed(st: EmitState, ret_box_ptrs: List<String>) -> EmitState
4607:fn emit_drop_glue_tensors(st: EmitState, ret_tensor_ptrs: List<String>) -> EmitState
4660:fn emit_drop_glue_destroy(st: EmitState) -> EmitState
4774:fn emit_drop_glue(st: EmitState, ret_val: String, ret_ty: String) -> EmitState
```

Six helpers: four per-resource (`_strings`, `_lists`, `_boxed`,
`_tensors`), one async-destroy-path (`_destroy`), one dispatcher.
Each per-resource helper takes a `ret_*_ptrs: List<String>` so the
caller can pass the SSA names that escape via the return value;
the helper then alias-checks each tracked slot against that list
and skips the free when it matches. This is the right shape — it
is exactly the per-slot `icmp eq ptr` + multi-block branch I
described in the v5.2.0 review as forward-compatible-with-future-
drop-glue.

**(2) Ownership tracking fields in `EmitState`.**

```bash
$ grep -c "str_owned\|list_owned\|boxed_owned\|tensor_owned\|moved_locals" mapanare/self/emit_llvm.mn
97
```

97 references. The actual EmitState declaration confirms the field
set:

```
emit_llvm.mn:159  ["lines", "counter", "functions", "structs", "module_name",
                  "str_counter", "str_globals", "current_ret_type", "enum_names",
                  "enum_infos", "enum_inline_slots",
                  "str_owned", "list_owned", "boxed_owned", "tensor_owned",
                  "moved_locals",
                  "entry_prelude_lines", "entry_block_body", "in_entry_block",
                  "loop_depth",
                  "str_owned_source", "list_owned_source",
                  "boxed_owned_source", "tensor_owned_source"]
```

24 fields total. Five owner lists (str/list/boxed/tensor + moved),
four parallel `_source` arrays carrying the bare SSA source name
(v5.4.4 — the Move-aware `is_moved` gate), one `loop_depth: Int`
(v5.4.3 — the Rt.03 loop-reassignment fix), three entry-block
buffer fields (v5.4.1 — so `emit_track_*` can fire from any basic
block while the tracking-slot allocas land in the function's entry
block). Reg.1 gate clean at 24/24 / 91 (verified by SESSION_REPORTs;
I trust the regression test).

**(3) Tracking hooks at every heap-allocating site.**

```bash
$ grep -c "emit_track_string\|emit_track_boxed\|emit_track_tensor" mapanare/self/emit_llvm.mn
21
```

I sampled the 21 call sites:

- `emit_llvm.mn:1209` — `emit_track_string(s_call, call_dest.name)`
  in the call-dispatch path (covers all runtime + user String returns,
  plus the v5.4.2 extension via `is_string_returning_builtin`).
- `emit_llvm.mn:1518` — `emit_track_tensor(s, dn)` after
  `__mn_tensor_alloc` in `emit_tensor_init` (v5.6.4 Rt.06).
- `emit_llvm.mn:1725` — `emit_track_string(s, dn)` for binop +
  String concat.
- `emit_llvm.mn:2950` — `emit_track_boxed(s, ep)` in
  `emit_enum_init`'s boxed-payload branch (v5.4.2 — closes
  `50_match_or_patterns`).
- `emit_llvm.mn:3758` — `emit_track_tensor(s_sl, dn)` in the
  tensor-slice special case.
- `emit_llvm.mn:4042` / `:4067` — `emit_track_tensor(s, dn)` in the
  generic `emit_mir_call` arms (covers all 20 broadcast/scalar
  binop fns + slice without duplicating their emit code, gated by
  `is_tensor_allocating_fn`).
- `emit_llvm.mn:5112` — `emit_track_string(s, tmp)` in the
  interp-concat path.

Plus the helpers themselves at lines 4312 (`emit_track_string`),
4339 (`emit_track_boxed`), and 4385 (`emit_track_tensor`). Each
helper has the v5.4.3 `loop_depth > 0` branch that prepends a
load + free of the prior slot value before the store, so loop-
reassignment doesn't leak.

**(4) `Move` MIR variant + lowerer emission.**

```bash
$ grep -c "Move(" mapanare/self/lower.mn
13
```

Move emission sites I sampled:

- `lower.mn:1386` — after `Some(val)` payload arg.
- `lower.mn:1395` — after `Ok(val)` payload arg.
- `lower.mn:1404` — after `Err(val)` payload arg.
- `lower.mn:2344` / `:2363` / `:2381` — same pattern in the
  `lower_call_by_name` arms for `Some`/`Ok`/`Err`.
- `lower.mn:2721` — `for vals[i] in StructInit fields` Move per
  field (this is the v5.4.4 patch — v5.4.4 SESSION_REPORT
  references the same line range).
- `lower.mn:2733` — same for EnumInit per payload.
- `lower.mn:2745`–`:2746` — MapInit per k/v pair.
- `lower.mn:2769` — `list.push(val)` consumes ownership.
- `lower.mn:3851`–`:3852` — IndexSet (`xs[i] = val` /
  `m[k] = v`) per index + value.

Pattern is correct. Every operation that consumes a heap-allocated
resource into a structure (struct, enum, list, map) emits
`Instruction::Move(val)` afterward. The emitter's `"move"` kind
handler at `emit_llvm.mn:1226-1240` pushes `stripped` (the bare
local name) onto `s.moved_locals`. Drop-glue then consults this
set via the parallel `_source` arrays (one per resource class):

```
emit_drop_glue_destroy:4671  let is_moved: Bool = (len(source) > 0) && list_has_string(s.moved_locals, source)
                       :4672  if !is_moved { ... emit free ... }
```

The `is_moved` gate fires per-slot. Aliased moves (the same SSA
value moved twice) are idempotent because `moved_locals` is a set
in spirit (the `list_has_string` check prevents double-free). The
Python side (`_move_resource` called from `_do_move` / `_do_call`
/ `_do_extern`) provides the canonical mirror.

**(5) `emit_drop_glue` wired into `emit_mir_return`.**

```
emit_llvm.mn:4914  let mut sa: EmitState = emit_drop_glue(st, val.name, inner_ty)
emit_llvm.mn:4927  let mut sv: EmitState = emit_drop_glue(st, "", ty)
emit_llvm.mn:4932  let mut s0: EmitState = emit_drop_glue(st, val.name, ty)
emit_llvm.mn:4938  let mut s1: EmitState = emit_drop_glue(st, val.name, ty)
emit_llvm.mn:4950  let mut sa2: EmitState = emit_drop_glue(st, val.name, "i32")
emit_llvm.mn:4956  let mut s2: EmitState = emit_drop_glue(st, val.name, ty)
emit_llvm.mn:4967  let mut svn: EmitState = emit_drop_glue(st, "", "void")
emit_llvm.mn:4975  let mut svna: EmitState = emit_drop_glue(st, "", "i32")
emit_llvm.mn:4979  let mut sv2: EmitState = emit_drop_glue(st, "", ret_ty)
```

9 call sites covering scalar return, void return, async-payload
return, sret-aggregate return, etc. The dispatcher at
`emit_llvm.mn:4774-4898` handles the resource extraction:

- Scalar String return: `extractvalue {ptr, i64} %ret, 0`
  → push to `ret_str_ptrs` (the data ptr).
- Scalar List return: `extractvalue {ptr, i64, i64, i64, i64} %ret, 0`
  → push to `ret_list_ptrs`.
- Scalar ptr return: dual-push to `ret_box_ptrs` AND
  `ret_tensor_ptrs` — the v5.6.4 Rt.06 design call (each helper
  alias-checks its own slot list, the over-approximation is safe).
- `%struct.*` return: walk one level of fields, extract each
  String / List / ptr field into the corresponding ret-ptr list.

Then call all four per-resource helpers. The order is deliberate
(string → list → boxed → tensor) so a list-of-strings free
sequence doesn't double-free strings via the data buffer (lists
free is shallow; strings inside the list are still tracked
individually).

The v5.5.7 destroy-path drop-glue is wired in at `emit_llvm.mn:5556`:

```
emit_llvm.mn:5552  if has_async_fns {
emit_llvm.mn:5556      s = emit_drop_glue_destroy(s)
```

This emits before `coro.cleanup` so cancelled-mid-flight async fns
free their tracked locals via `pthread_exit` paths. Correct shape
for coroutine cleanup.

**Verification: across all five releases the helper signatures
hold, the field set hold, the ownership invariants hold.** No
phantom helpers. No "we'll get to it next release" placeholders.
Every site I sampled has the right shape relative to the Python
mirror.

**This is the wall coming down.**

#### Per-release verification of the Own.1 P2 arc

**v5.4.0** (infrastructure) — Phase 0 baseline showed all 11 Sh.2
goldens already passing pre-release; v5.4.0 didn't close goldens,
it shipped the infrastructure that prevents Sh.2-shape regressions.
This is correct sequencing — close the latent UAF first via Cb.7
zero-after-push (v5.1.3), then ship the structural fix. Goldens
54/66 preserved; valgrind 0 new ERRORS; ASan 55 CLEAN unchanged.

**v5.4.1** (functional) — Owner lists populated; tracking hooks
fire; entry-block prelude buffer architecture correct. The
choice to NOT track string literals is the right call (they live
in rodata; `__mn_str_free` is_heap=0 no-ops on them; tracking
each blew get_fn_attrs-sized functions quadratically — Python's
`_mkstr` makes the same choice). I verified the narrow leak test
mentioned in the SESSION_REPORT: `greet() -> String` under
`detect_leaks=1` reports 0 leaks.

**v5.4.2** (LSan-gated) — `scripts/run_asan_leak_goldens.sh`
compile+link+executes every golden under LSan
(`detect_leaks=1:leak_check_at_exit=1`). The
`is_string_returning_builtin` extension covers 13 builtins whose
MIR dest defaults to `mir_unknown()` (read_file, sha256,
regex_replace, http_get, base64_*, hmac_sha256, hex_encode,
random_bytes, gpu_device_name, read_line, join, typeof) — closes
4 goldens × 9 leak objs / 202 B. The `emit_track_boxed(ep)` at
`emit_enum_init`'s boxed-payload path closes
`50_match_or_patterns`'s enum-payload box leak (16 B). The
`scripts/check_leak_summary.py` baseline-comparison gate
(`docs/roadmap/v5/v5.4.2/baseline/asan-leak-baseline.tsv`) lets a
leak only LEAK→CLEAN or LEAK_N → LEAK_<N (improvements); CLEAN→LEAK
or LEAK_N → LEAK_>N is a regression. I read the gate code at
`scripts/check_leak_summary.py:79-101` — the regression detection
logic is correct. `make leak-check` + the
`.github/workflows/sanitizers.yml` leak-check job ratify the sweep
as a merge requirement. **This is what I asked for.**

**v5.4.3** (Rt.03 loop-reassignment) — `EmitState.loop_depth: Int`
threaded through `emit_mir_basic_block` push/pop on
for_body/while_body/mapfor_body labels. The three `emit_track_*`
helpers prepend a `load + @__mn_str_free / @free` when
`loop_depth > 0`; outside loops the emission is byte-identical to
v5.4.2. Zero-init in the entry-block prelude + null-tolerant
runtime free fns make the first-iteration free a no-op without
a runtime branch.

```
emit_llvm.mn:4324  if s.loop_depth > 0 {
                       // load + @__mn_str_free for prior slot value
                   }
emit_llvm.mn:4348  if s.loop_depth > 0 { ... @free }    [boxed]
emit_llvm.mn:4393  if s.loop_depth > 0 { ... @__mn_tensor_free }  [tensor]
```

The pre-store free is structurally exactly the right pattern.
Closes `22_string_builder` from 6 objs / 19 B → CLEAN; baseline
TSV refreshed. **The D3 UAF risk I would normally flag** (aliased
copies + reassignment on the same loop iteration freeing what a
caller still holds) — verified did not materialize on the corpus
via the v5.4.3 UAF sweep being byte-identical. The shape is still
risky in principle (e.g., `let s = arr[i]; arr[i] = make_new()` in
a loop), but the current emitter doesn't lower in a way that
exposes it. I'll re-flag if a future feature creates that shape.

**v5.4.4** (Move-aware infrastructure) — Three new `_source`
arrays parallel to the existing owner lists, carrying the bare
SSA source name. `is_moved` check consults the source array
indexed identically. Lowerer Move emission at every
resource-consuming site (verified above with 13 grep hits).
Latent `emit_fn` flush cap of 65536 raised to 1M — that was a
silent truncation bug for large drop-glue tails on large
functions. **Good catch.** The guard-lift attempt for
`%struct.*` returns was implemented and reverted because the
~40 extractvalue lines per call site inflated stage2.ll by 5× and
triggered an mnc-stage2 runtime segfault (Ve.1 regression). The
lead's choice to revert is the right call — speculative bloat for
no observable leak benefit. v5.4.5+ would re-lift with a size
gate, but in practice (a) Lk.1 destination passing in v5.6.12
made this less urgent, and (b) Rt.04 is the only remaining
struct-return leak class and that needs multi-level alias analysis
not single-level walk.

#### Cross-resource verification (Rt.05 + Rt.06)

The infrastructure scaled to two new resource classes without any
shape divergence. This is the strongest signal that Phase 2 is
structurally complete (rather than just sufficiently complete for
the v5.4.x corpus):

**Rt.05 (v5.5.7 — async coroutine destroy-path drop-glue).**

```
emit_llvm.mn:4660  fn emit_drop_glue_destroy(st: EmitState) -> EmitState {
                       // Strings, Lists, Boxed, Tensors (4 unconditional loops)
                       // Each consults parallel _source arrays for is_moved gate
                   }
```

The destroy helper iterates all four resource classes
unconditionally (no aliased-ret-ptrs check because
`coro.cleanup` runs on cancellation paths where the return value
never escapes). SSA prefix `%drop.d.{s,l,b,t}.N` distinct from
normal-exit `%drop.{s,l,b,t}.N` so the two emit paths don't
collide. Wired in at `emit_llvm.mn:5556` for async fns. Valgrind
on `55_async_basic`: 5 allocs / 5 frees / 0 in use at exit. ASan
0 errors. LSan 0 leaks. TSan 0 races on 56/57/58/59 under
`MAPANARE_ASYNC_THREADS=4`. Same shape as the v5.4.x
per-resource helpers — no divergence.

**Rt.06 (v5.6.4 — tensor drop-glue).**

The tensor track follows the boxed shape line-for-line:
`tensor_owned` + `tensor_owned_source` parallel the boxed
fields; `emit_track_tensor` mirrors `emit_track_boxed` (zero-init
slot in entry-block prelude, store of the tensor ptr after the
alloc, ownership-list push, loop-depth branch); `is_tensor_allocating_fn`
predicate enumerates 22 runtime fns (1 alloc + 1 slice + 8
broadcast + 8 scalar + 4 rscalar); post-emit injection in the
generic `emit_mir_call` `Some(fe)` + `_` success branches covers
all 20 binop fns without duplicating v5.6.2's emit logic;
`emit_drop_glue_tensors` mirrors `_boxed`; `emit_drop_glue`
dispatcher's `%struct.*` ptr-field walk dual-pushes the same SSA
to both `ret_box_ptrs` and `ret_tensor_ptrs` — the
over-approximation is safe because each per-resource helper
alias-checks its own slot list. All 5 tensor goldens 49/50/51/52/53
report 0 objs / 0 B under LSan. **Baseline TSV flipped 49–53 from
COMPILE_FAIL/LEAK-allowed to CLEAN-required** (verified at
`docs/roadmap/v5/v5.4.2/baseline/asan-leak-baseline.tsv:48-52`).
Tightening the gate is the right move.

#### Verdict on Own.1 Phase 2

The 28-panel item is closed at the structural root cause. I would
have accepted "Phase 2 partially complete" with a smaller score
bump if the closeout was just v5.4.0 + v5.4.1. The fact that the
arc extends through Rt.05 (async, v5.5.7) and Rt.06 (tensor,
v5.6.4) without architectural divergence is a stronger signal —
the same per-resource helper structure survived two new resource
classes added in feature releases. That is what robust
infrastructure looks like.

The v5.2.0 "ceiling" comment specifically said that 10.0 requires
either:
> (a) Drop-glue + move tracking in the self-hosted emitter, or
> (b) A full borrow checker (v6.0).

Option (a) is now done. That's worth +0.2 from 9.7 (-0.3 of
9.7→10.0 ceiling, restored to -0.1 of 9.9→10.0 ceiling for
remaining Rt.04 carry-forward).

---

### v5.6.x memory-safety closeout (Ve.1 / Ve.2 / Ve.3 / Ve.4 / Lk.1)

Five separate dockets surfaced during the v5.6.x bug-closeout arc.
Every one closed at structural root cause; none as workarounds.

**Ve.1 (v5.6.5) — `parse_fn_body` heap-buffer-overflow.**

Open since v5.4.4. ASan reported 154,355 errors / 42 contexts on
full `mnc_all.mn` self-compile. Root cause was NOT the parser but
`llvm_type_size`'s hardcoded 256-byte fallback for any `%struct.*`
type — `FnDefData` is 264 bytes, every `Definition::FnDef(fd)`
boxing overflowed by 8. The fix: rewrite the emission pipeline
to defer ABI computation to LLVM's DataLayout via the GEP-trick
(`ptrtoint ptr getelementptr (%T, ptr null, i32 1) to i64`)
+ typed field GEPs — the pattern Clang uses for opaque-size
emission. ASan post-fix: **0 heap-buffer-overflow errors** on
`mnc_all.mn` (was 154k+). Hardcoded-malloc sites: **435 → 2**
(99.5% elimination). `llvm-as` clean.

This fix is **the right kind**. Instead of patching one struct
size, the lead replaced the entire layout-engine. LLVM computes
sizes at link time. No hand-rolled sizing. Future structs scale
automatically. Same pattern Clang and rustc use.

**Ve.2 (v5.6.7 partial → v5.6.12 closed) — empty-list elem_ty floor.**

`let xs: List<String> = []` was lowering to MIR with
`elem_ty.kind=TK_UNKNOWN` (resolved to `i64`), so lists allocated
with 8-byte slots instead of the type's actual size. The 384-byte
floor masked this across Span/Block/String/Param/Decorator/Stmt/
FnDefData lists since v4.x. v5.6.7 introduced
`lower_list_typed_into` to thread element-type hints from `let`
annotations. v5.6.12 closed all 7 residual `__mn_list_new(i64 384)`
sites via destination-passing in `lower_let` (see Lk.1 below).
**Floor sites: 7 → 0.**

**Ve.3 (v5.6.9) — drop-glue UAF on `List<Enum>` returns.**

This is the docket I would have flagged at v4.154.0 if the
`mir_opt::clone_instr_for_inline` path was load-bearing. Returns
`List<Instruction>` where Instruction is `%enum.Instruction = type
{i64, ptr}` — `{tag, heap_box_ptr}` pairs whose payload_ptr IS one
of the freed boxes. The single-level alias check in
`drop_glue_boxed` compared against `ret_box_ptrs` (empty for list
returns), so all boxes got freed → caller dereferenced dangling
payload via `instr_dest(inst)` → `__mn_str_concat → llvm_alloca →
__mn_alloc(garbage_size)` OOM.

Same multi-level aliasing class as v5.6.6 Rt.04 (List<String>
nested in returned struct, 2 levels deep). The fix matches
v5.6.6's RESCOPE pattern — 25 LOC at `emit_llvm.mn:4763`
(verified the actual line: `4809  if ret_ty == llvm_list_rt() &&
len(boxed_owned) > 0`). Cost: intermediate boxes NOT in returned
list leak; accepted per v5.6.6 precedent (UAF prevention > leak
prevention). **`mnc-stage2 /tmp/p1.mn` was 0-line OOM since
v5.6.4; now 215 lines `llvm-as` clean RC=0.**

The lead's investigation discipline is worth highlighting:
4 strategically-placed `__mn_str_eprint` traces inside
`build_match_arms` and the optimizer pipeline isolated the failure
mode in one rebuild cycle. That's better than I do most days. The
SESSION_REPORT's culebra retrospective is also worth reading
(`docs/roadmap/v5/v5.6.9/SESSION_REPORT.md`) — it correctly
identifies that culebra v2.4.0 needed Windows-style paths under
WSL interop and that `triage --brief` took 7m37s on 207k-line
stage2.ll, while 4 eprints + 1 `should_inline → return false`
confirmation found the bug in ~8 min total. **Right tool for the
job.**

**Ve.4 (v5.6.11) — match-arm empty BasicBlocks via elem_size mismatch.**

The v5.6.4-era fixed-point regression that broke
`verify_fixed_point.sh` since v5.6.4 (7 releases). Root cause:
`emit_index_get` / `emit_index_set` inline fast paths for
i64/double/ptr element types emitted `getelementptr inbounds i64,
ptr %data, i64 %idx` (constant 8-byte stride), while
`__mn_list_push` writes used the runtime `elem_size` field from
the list struct (= 384 for the 7 Ve.2 residual `List<Int> = []`
floor sites). At elem_size=384 the second push wrote 8 bytes of
i64 + 376 bytes of stack spillage at byte offset 384, while the
inline-GEP-i64 read at byte offset 8 returned the FIRST push's
intra-buffer spillage (a heap-pointer-shaped Int garbage value).
Caller's `set_block(s, garbage)` then made `emit_instr`'s
`idx < len(fn_blocks)` bounds check silently no-op every
instruction in the second match arm.

I verified the fix at `emit_llvm.mn:2585-2606`:

```
emit_llvm.mn:2598  let eszp: String = "%lg.eszp." + cnt_lg
emit_llvm.mn:2599  s = emit_line(s, "  " + eszp + " = getelementptr inbounds " + lt + ", ptr " + tmp + ", i32 0, i32 3")
emit_llvm.mn:2600  let esz: String = "%lg.esz." + cnt_lg
emit_llvm.mn:2601  s = emit_line(s, "  " + esz + " = load i64, ptr " + eszp)
emit_llvm.mn:2602  let off: String = "%lg.off." + cnt_lg
emit_llvm.mn:2603  s = emit_line(s, "  " + off + " = mul i64 " + idx.name + ", " + esz)
emit_llvm.mn:2604  let ep: String = "%lg.ep." + cnt_lg
emit_llvm.mn:2605  s = emit_line(s, "  " + ep + " = getelementptr inbounds i8, ptr " + data + ", i64 " + off)
```

Load `list.elem_size` (struct field 3) at runtime, compute
`offset = idx * elem_size`, then GEP the i8 pointer. SROA elides
the runtime load when elem_size is a known constant (so this is
zero-cost in the typical case). For the 7 floor sites it
correctly produces a 384-byte stride matching the push.

**`verify_fixed_point.sh` reaches NEAR (4 diff lines / 217,879 =
0.002%) for the first time since v5.6.4** — `mnc-stage2 mnc_all.mn`
now produces non-empty stage3.ll byte-identical to stage2.ll
(modulo VERSION). This is also the right kind of fix: read-side
strides made consistent with write-side strides regardless of
allocator choice.

**Lk.1 (v5.6.12) — alloca-aliasing leak via destination-passing.**

This is the closure I want to highlight as best-of-arc.

The leak: drop-glue tracks the ListInit destination alloca
(`%t0.addr`) but mutating pushes write back to a separate
var-binding alloca (`%arr1.addr`); at function exit,
`__mn_list_free(ptr %t0.addr)` is a no-op while the buffer at
`%arr1.addr` is never freed.

Two ways to fix this:
- **(a) Multi-level alias analysis** in drop-glue (track which
  allocas alias which buffers; free the right one).
- **(b) Destination-passing semantics** in lower_let (eliminate
  the duplicate alloca; pre-compute the var's alloca name and
  lower the ListInit directly into it).

The lead chose (b). `lower_list_typed_into(st, elements, hint,
dest_name)` accepts a caller-supplied dest name; when value is a
list literal with an annotated element type, `lower_let` pre-
computes the var's alloca name (e.g. `%indices0.addr`) and
lowers the `ListInit` directly into it — no scratch
`%t<N>.addr`, no `Store(%var.addr, %t<N>)` copy. The emitter's
`dn + ".addr"` convention then derives the same alloca name as
the let var: one alloca, one tracking entry, no copy.

Verified at `lower.mn:3522-3550`:

```
fn lower_list_typed_into(st: LowerState, elements: List<Expr>, hinted_elem_ty: MIRType, dest_name: String) -> LowerResult {
    ...
    // Use the caller-supplied dest_name (e.g. "%indices0") instead of
    // fresh-tmp. tmp_counter is NOT bumped here; the caller already
    // reserved the slot when it picked the variable's name.
    let dest_val: Value = new_value(dest_name, mir_list())
    let new_s: LowerState = emit_instr(s, Instruction::ListInit(dest_val, elem_type, vals))
    return new_lower_result(dest_val, new_s)
}
```

This is the rustc `PlaceRef`-based codegen pattern (result-location
semantics rather than value-then-copy). The comment at
`lower.mn:3520-3521` explicitly cites this. It is exactly the
right reference for this fix — Rust solved this same problem the
same way for the same reason.

**v5.6.13 extends to struct let-bindings** via
`lower_struct_new_into` (verified at `lower.mn:3695`). Same
pattern. Eliminates the duplicate `.si` scratch alloca in
`emit_struct_init`. `.si = alloca` site count: **240 → 0**. Net
struct allocas: **2,206 → 2,113 (−93)**.

**Hero metric**: `65_list_int_indexing` LSan **CLEAN** at v5.6.12
(was: would have leaked 80 bytes if the scalar gate were applied
without the Lk.1 closure). The decision to gate the scalar fix on
the Lk.1 closure first — even though it required two more releases
(v5.6.10 partial + v5.6.11 Ve.4 + v5.6.12 closure) — is the right
discipline. Shipping the scalar gate without the alias fix would
have surfaced new leaks; shipping the alias fix without the gate
would have left the 384-floor sites; doing both in the right order
closes both without regression.

**Adjacent finding** (62_list_output's pre-existing Rt.04 leak):
the scalar gate + Lk.1 closure unmasked it. With the duplicate
alloca eliminated, LSan's "still reachable" heuristic no longer
finds a stale stack pointer aliasing into the heap buffer, so the
144-byte list buffer (with 9 strings inside) is correctly reported
as a direct leak. Baseline refreshed `9 obj/141 B → 13 obj/346 B`.
**This is honest accounting** — the leak source is unchanged
(struct→list→string depth-2 alias from v5.6.6 Rt.04 RESCOPE);
LSan's heuristic just got a clearer view. The lead documented this
explicitly in the v5.6.12 SESSION_REPORT and updated the baseline
TSV instead of trying to hide the change. That's how it should be
done.

#### Verdict on v5.6.x memory-safety closeout

5 dockets, all closed at structural root cause across 8 releases
(v5.6.5 → v5.6.12). One docket (Rt.04) explicitly RESCOPED to
v6.0 with documented UAF risk if attempted in v5.x scope. Zero
shortcut workarounds. The investigation discipline (eprint over
culebra in v5.6.9; reproducer at `/tmp/p1.mn` for Ve.3; reproducer
at `/tmp/p3.mn` for Ve.4) is consistently right-sized to the
problem. Worth +0.05.

---

## What remains open

### Rt.04 — Multi-level alias analysis (v6.0 carry)

The single remaining memory-safety carry. Documented at
`docs/known_issues.md:47`:

> **Rt.04** | Multi-level alias analysis for drop-glue. v5.6.6
> attempted a one-level `%struct.*` field walk and reproduced a
> UAF in `62_list_output` — the resource lives at struct→list→
> string (depth 2). Fix needs the v6.0 borrow checker.
> 62_list_output stays LEAK (baseline-gated, 13 obj / 346 B
> refreshed v5.6.12). | extract intermediate concats into
> let-bindings outside the struct-returning function's body |
> v6.0 (borrow checker)

I read the v5.6.6 RESCOPE rationale at `emit_llvm.mn:4737-4771`
end-to-end. The decision is correct:

- v5.6.6 attempted a one-level `%struct.*` field walk with a size
  gate (N=8/M=50 → +10.3% stage2.ll growth, over budget; N=4/M=20
  → +3.67%; N=4/M=10 → +2.39%, under budget but UAF is real).
- ASan reproduced a heap-use-after-free at every gate threshold:
  `__mn_str_free → emit_drop_glue_strings → memcpy →
  __mn_str_join → main`. The String slots whose data lives inside
  the returned list got freed prematurely; the caller's join
  read freed memory.
- Multi-level walk would close 62_list_output but **scoped to v6.0
  borrow checker** — type-level ownership is the structural answer;
  per-emit-site walks at depth 2 explode in IR size and don't
  generalize to arbitrary nesting.

The cost today: `62_list_output` stays LEAK (13 obj / 346 B,
baseline-gated). This is documented, the LSan baseline gate
prevents regression, and the workaround (extract intermediate
concats into let-bindings outside the struct-returning function's
body) is documented in `docs/known_issues.md`. **Acceptable, but
not free.**

The lead's discipline on this is exactly right — UAF prevention >
leak prevention is the order I would also choose. A documented
346-byte leak in one golden is far less dangerous than a UAF that
could surface anywhere a `%struct.*` containing a List<String> is
returned.

I am not changing my score for this beyond the 9.9 ceiling cap.
Closing Rt.04 in v6.0 (borrow checker) gets us to 10.0.

### Rt.01 / Rt.02 — Third-party leaks

`gpu_available()` on a CUDA-capable host leaks 260 B of libcuda
driver state per process (one-shot init, reclaimed by kernel at
exit). Vulkan / Mesa ICD loader retains ~50 KB of per-process
state after `vkDestroyInstance`. Both third-party (external
drivers); both baseline-gated; both have the same FP class as
v5.3.0. Not Mapanare bugs.

The valgrind sweep at v5.8.0 shows the Mesa/Vulkan errors:

```
39_gpu_detect: ==75441== ERROR SUMMARY: 124247 errors from 596 contexts
40_gpu_tensor: ==75713== ERROR SUMMARY: 127791 errors from 650 contexts
```

Same shape, same frame class (`<unknown module>` for Mesa ICD,
libcuda for CUDA driver init). Suppressed via
`scripts/asan_leak_suppressions.txt` for the symbolic-suppressable
class (libcuda); baseline-gated via
`scripts/check_leak_summary.py` for the unsymbolic class
(`<unknown module>`).

This is what I'd expect — it is unchanged from v5.2.0. Not a
finding.

### LSan baseline TSV — current state

I read the baseline at
`docs/roadmap/v5/v5.4.2/baseline/asan-leak-baseline.tsv` end-to-end.
67 lines, 3 LEAK entries:

```
40:39_gpu_detect      0  0  5   50212  -          LEAK   (Rt.02 Mesa/Vulkan)
41:40_gpu_tensor      0  0  5   50212  -          LEAK   (Rt.02 Mesa/Vulkan)
63:62_list_output     0  0  13  346    __mn_alloc LEAK   (Rt.04 v6.0)
```

50/53 entries are CLEAN. The remaining 14 are LINK_FAIL (Python
bootstrap path issues for try-operator, match-related goldens,
async-marked COMPILE_FAIL pre-Sh.4-closure). The LINK_FAIL class
is not memory safety — it's a Python emit-llvm bug that v5.5.4+
self-hosted closes by going through `mnc-stage1` instead.

The baseline is honest. 3 LEAK entries, all documented, all third-
party or Rt.04. **No silent grandfathering.** The
`scripts/check_leak_summary.py:79-101` regression detection logic
prevents new leak classes from sneaking in.

---

## Sanitizer state — v5.8.0

### Valgrind (66 goldens, --error-exitcode=99 --leak-check=no)

Per `/tmp/v58_valgrind_summary.txt`:

```
63 CLEAN (0 errors)
 2 ERRORS  (39_gpu_detect, 40_gpu_tensor — Mesa/Vulkan dlopen)
 1 LINK_FAIL (47_try_operator — Python bootstrap emit-llvm bug)
```

I sampled the entire summary. The 63 CLEAN entries include all 5
async goldens (55–59) — every one reports
`ERROR SUMMARY: 0 errors from 0 contexts`. All 5 tensor goldens
(49–53) — same. The closure-typed (`64_closure_typed`) and
or-pattern (`51_match_guards_and_or`) goldens — same. **Every
golden that 12 of had been failing at v5.3.0 is now valgrind clean
at v5.8.0**.

Compared to my v5.2.0 review:

| Class | v5.2.0 | v5.8.0 | Delta |
|---|---:|---:|---|
| CLEAN | 62 | **63** | +1 |
| ERRORS (memory safety) | 0 | 0 | parity |
| ERRORS (GPU loader, third-party) | 2 | 2 | same FPs |
| LINK_FAIL (Python bootstrap path) | (not broken out) | 1 | pre-existing |

The 47_try_operator link failure is a Python-bootstrap
emit-llvm bug (`store i64 %uw.12, ptr %t3.a.13` with mismatched
struct type `{i64,{ptr,i64}}`). Native `mnc-stage1` produces clean
IR for this golden (verified in §2's 66/66). Probably present
silently at v5.3.0 as well. Not a regression; not memory safety.

### ASan (C runtime hardening)

```
TestCRuntimeASan::test_asan_no_errors PASSED  (74/74 C tests, 0 errors)
```

vs v5.2.0: 3 stream tests failed under ASan
(`stream_from_list_collect`, `stream_map`, `stream_filter`).
Closed at v5.3.1 (Stream-C carry-forward). Confirmed.

### TSan (C runtime hardening)

```
TestCRuntimeTSan::test_tsan_no_races PASSED  (74/74 C tests, 0 races)
```

vs v5.2.0: 3 stream tests failed under TSan. Closed at v5.3.1.
Confirmed.

### LSan (golden-suite leak gate)

Baseline-gated per `scripts/check_leak_summary.py`. 50/53 testable
goldens CLEAN; 3 baseline-gated LEAK (Rt.02 × 2 + Rt.04).
v5.5.4–v5.5.7 async + v5.6.0–v5.6.3 tensor + v5.6.4 Rt.06 +
v5.6.12 Lk.1 all flipped their goldens from COMPILE_FAIL/LEAK-allowed
to CLEAN-required. This **tightens the gate**.

### Pathology audit (culebra v2.4.0)

The v5.7.1 baseline at `docs/roadmap/v5/v5.7.1/culebra/`:

```
5 root causes, 15,829 findings
  - 2 critical (function-count-drop, return-type-divergence) — known FPs
  - 3 high (fixed-point-delta, byte-count-mismatch, stage-output-divergence) — text-pattern noise
No new critical findings vs v5.6.10 anchor.
Per-struct health (Value, MIRType, EmitState, LowerState, Instruction): all clean.
String-byte-count: 6,398/6,398 correct.
llvm-as on stage2.ll: VALID.
```

The two critical findings are documented FPs:
`function-count-drop` (940+ hits) and `return-type-divergence`
(37 hits) — both reflect culebra's text-pattern templates flagging
runtime declarations like `__mn_str_concat`, `__mn_str_substr`,
`__mn_list_new` whose Python and self-hosted forms diverge in IR
text but are semantically identical (the Python bootstrap declares
them inline; the self-hosted emitter declares them via
`declare_runtime_fn`). Same FP class as v5.6.10 anchor. **No new
critical findings.**

The new `docs/guides/culebra.md` (§3 false-positive policy)
documents this FP class explicitly. The contributor guide is
6 sections covering daily commands, FP policy, per-release journal,
panel input, cross-reference. WSL interop gotcha (Windows binary
needs Windows paths) and performance notes (`triage --brief` fast,
full `triage` ~7-8 min on 217k IR) documented inline.
**This is exactly the right kind of process polish.**

---

## Score breakdown

Starting from v5.2.0 baseline of **9.7 / 10**:

| Adjustment | Delta | Rationale |
|---|---:|---|
| Own.1 Phase 2 CLOSED (28-panel item) | +0.20 | The single largest item on my carry-forward list since v4.99.0. Five-release arc (v5.4.0 → v5.4.4) with infrastructure → tracking → LSan-gate → Rt.03 → Move-aware. Architecture survived two new resource classes (Rt.05 async v5.5.7, Rt.06 tensor v5.6.4) without divergence. The wall is down. |
| Ve.1/Ve.2/Ve.3/Ve.4/Lk.1 closeout | +0.05 | 5 dockets, all closed at structural root cause across v5.6.5 → v5.6.12. UAF prevention prioritized over leak prevention (Rt.04 RESCOPED, Ve.3 RESCOPE pattern). Investigation discipline consistently right-sized (`__mn_str_eprint` over culebra for Ve.3; reproducer-driven debugging). |
| Sh.4/Sh.6/Sh.7/B closures (12 goldens) | 0 | Not memory-safety axis; valgrind-clean preserved across the new goldens. Cobra/Coral grade these. |
| Stream-C / ASan / TSan recovery (v5.3.1) | +0.05 | Was the v5.2.0 "3 stream test failures under ASan/TSan" item; closed cleanly at v5.3.1 with a logic-bug fix not a sanitizer suppression. **The right fix.** |
| LSan baseline gate operational (v5.4.2) | +0.05 | Baseline TSV + `scripts/check_leak_summary.py` regression detection + `make leak-check` CI integration. Tightening the gate via post-release flips (49–53 → CLEAN-required) is exactly what I asked for at v5.2.0. |
| Rt.04 ceiling (v6.0 carry) | -0.05 | One LEAK class baseline-gated until v6.0 borrow checker. The v5.6.6 attempt reproduced a UAF; the rescope decision is correct but not free. |
| Honest baseline accounting (v5.6.12) | +0.05 | The 62_list_output LSan increase 9 obj/141 B → 13 obj/346 B was disclosed (pre-existing leak unmasked by stack-layout shift, not new), baseline TSV refreshed openly, full rationale in v5.6.12 SESSION_REPORT. **No silent grandfathering.** |
| Sanitizer matrix preserved across feature releases | +0.05 | v5.5.4–v5.5.7 (real LLVM coroutines) + v5.6.0–v5.6.3 (full tensor surface) + v5.7.0 (closure-typed + or-pattern) all preserve the valgrind/ASan/LSan/TSan baseline. Adding 12 goldens × 4 sanitizers without surfacing any new memory-safety class is non-trivial. |

Sum: 9.7 + 0.20 + 0.05 + 0.05 + 0.05 - 0.05 + 0.05 + 0.05 = **10.05**

Capped at 9.9 — the Rt.04 ceiling holds the score below 10.0
until the borrow checker lands. The above adjustments are
intentionally generous because the work is unusually deep, but the
ceiling is hard. **Final: 9.9 / 10 EXCEEDS, +0.2 vs v5.2.0.**

---

## Carry-forward (for v5.8.0+)

| Docket | Severity | Scope |
|---|---|---|
| **Rt.04** | LOW (in v5.x scope) → MEDIUM (in v6.0 scope) | Multi-level alias analysis for drop-glue. The structural fix is the borrow checker. v5.6.6 attempted a one-level `%struct.*` field walk and reproduced a UAF in `62_list_output` — confirmed the depth-2 (struct→list→string) shape is unreachable from a single-level walk. Stays LEAK (13 obj / 346 B, baseline-gated). The workaround (let-binding extraction) is documented in `docs/known_issues.md`. Closes when the borrow checker lands. |

No HIGH carry-forward. No CRITICAL ever. The carry-forward list is
**1 item** — the shortest it has been since I started reviewing.

---

## What I would flag for v5.8.0+ (forward-looking, not scoring)

These are observations, not findings. Including them so the v6.0
panel has continuity:

1. **The Lk.1 destination-passing pattern should generalize.** The
   v5.6.13 extension to struct let-bindings closes 240 sites of
   `.si` scratch allocas. The same pattern would benefit enum and
   map let-bindings, but v5.6.13 SESSION_REPORT documents the
   empirical analysis showing they don't have the same `.si`-shape
   scratch — emit_enum_init / emit_map_init produce purely register
   insertvalue chains. **Verified.** No action needed today, but
   if either emitter changes shape (e.g., to support large-enum
   sret), the destination-passing pattern is worth reapplying.

2. **The `_source` array `is_moved` gate is index-aligned with
   owner lists.** This is a tight invariant — pushes to
   `str_owned` MUST be paired with pushes to `str_owned_source`
   in the same order, or `is_moved` checks the wrong source.
   Audit confirms current code maintains this; but a future
   refactor that pushes to one without the other would silently
   regress to non-Move-aware behavior (drop-glue would fire on
   moved values, double-free, UAF). **Recommend:** factor a
   `track_owned(s, list_kind, ssa_name, source_name)` helper
   that updates both arrays atomically. The current pattern of
   matched pairs is correct but fragile.

3. **The `%struct.*` field walk in `emit_drop_glue` is single-level
   only.** The v5.6.6 RESCOPE comment at `emit_llvm.mn:4737-4771`
   documents this and references the depth-2 case (Rt.04). The
   walk infrastructure is in place; only the recursion / depth
   gate is missing. If v6.0 borrow checker work reveals the walk
   approach is workable for a bounded-depth subset, the call site
   at `emit_llvm.mn:4851-4892` is the place to add the recursion.

4. **The `loop_depth` counter is shared across nested loops.**
   It correctly tracks any-loop-depth via push/pop, but does NOT
   distinguish nested-loop scopes. For loop-reassignment freeing,
   this is fine — any depth > 0 fires the pre-store free. But if
   future code wants per-scope tracking (e.g., "only free across
   the outermost loop boundary"), the shape would need extending.
   Not today's problem.

---

## Reproducibility

```bash
# Drop-glue helpers
grep -c "emit_drop_glue" mapanare/self/emit_llvm.mn
# expect: 33

grep -n "^fn emit_drop_glue" mapanare/self/emit_llvm.mn
# expect: 6 functions (strings, lists, boxed, tensors, destroy, dispatcher)

# Ownership tracking field references
grep -c "str_owned\|list_owned\|boxed_owned\|tensor_owned\|moved_locals" mapanare/self/emit_llvm.mn
# expect: 97

# Tracking hooks
grep -c "emit_track_string\|emit_track_boxed\|emit_track_tensor" mapanare/self/emit_llvm.mn
# expect: 21

# Async destroy-path drop-glue (v5.5.7)
grep -n "emit_drop_glue_destroy" mapanare/self/emit_llvm.mn
# expect: 4660 (definition), 5556 (call site for has_async_fns)

# Destination-passing helpers (v5.6.12 / v5.6.13)
grep -n "lower_list_typed_into\|lower_struct_new_into" mapanare/self/lower.mn
# expect: 6+ matches (definitions + call sites)

# v5.6.11 Ve.4 elem_size-stride fix
grep -n "elem_size\|getelementptr inbounds i8" mapanare/self/emit_llvm.mn | head -10
# expect: load list.elem_size + GEP i8 in emit_index_get/set fast paths

# Move emission in lower
grep -c "Move(" mapanare/self/lower.mn
# expect: 13

# LSan baseline gate logic
sed -n '79,101p' scripts/check_leak_summary.py
# expect: regression detection (CLEAN→LEAK, LEAK_N → LEAK_>N)

# Baseline TSV current state
grep -n "LEAK" docs/roadmap/v5/v5.4.2/baseline/asan-leak-baseline.tsv
# expect: 3 LEAK entries (39_gpu_detect, 40_gpu_tensor, 62_list_output)

# Valgrind sweep
cat /tmp/v58_valgrind_summary.txt
# expect: 63 ERROR SUMMARY: 0 errors / 2 ERRORS (gpu) / 1 LINK_FAIL

# C hardening
python3 -m pytest tests/native/test_c_hardening.py -v
# expect: 3/3 PASS
```

---

## Raw notes

- The destroy-path drop-glue (`emit_drop_glue_destroy`) iterates
  all four resource classes unconditionally without any
  `ret_*_ptrs` alias check. This is correct because the destroy
  path runs on cancellation (no return value escapes), but if
  someone ever adds a "structured cancellation with partial
  return" feature (Rust async cancellation safety), the destroy
  helper would need its own escape analysis. Not today's problem.

- The `%struct.*` field walk's dual-push to `ret_box_ptrs` AND
  `ret_tensor_ptrs` (v5.6.4 Rt.06) is over-approximation safe but
  could become under-approximation unsafe if a future field type
  is added that should be in *exactly one* of the lists (e.g., a
  `Closure` with its own free fn). Each per-resource helper
  alias-checks its own slot list, so the over-approximation
  becomes "skip free on a non-aliased slot" → leak, not UAF.
  Acceptable for now; revisit if a fifth resource class lands.

- The `set_block(s, garbage_int)` mode in v5.6.11's Ve.4 trace —
  where `emit_instr`'s `idx < len(fn_blocks)` bounds check
  silently no-ops every instruction in a match arm because the
  garbage int is huge — is a **fascinating bug-amplification
  pattern**. The wrong-stride read produced garbage for one
  variable; that variable's use as a block index turned the read
  bug into "every instruction in this block is dropped";
  fixed-point regressed for 7 releases. The lesson: **bounds
  checks that silently no-op on out-of-range are bug
  amplifiers**, not bug catchers. Not changing my score for it,
  but flagging because the Python bootstrap and the C runtime
  both have similar patterns elsewhere; it's worth a future
  audit.

- The 47_try_operator LINK_FAIL in the v5.8.0 valgrind sweep is
  a Python-bootstrap emit-llvm bug, not a memory-safety finding.
  The native `mnc-stage1` path produces clean IR for this golden
  (verified in MEASUREMENTS §2's 66/66). Mentioning because it
  appears in the v5.8.0 valgrind summary as the only non-CLEAN
  non-GPU result, and a future panelist might mistake it for a
  regression. It is not.

- Score arithmetic: 9.7 + 0.20 (Own.1 P2 closure) + 0.05 (Ve.*/Lk.1
  closeout) + 0.05 (Stream-C ASan/TSan recovery) + 0.05 (LSan
  baseline gate operational) + 0.05 (honest accounting on
  62_list_output baseline) + 0.05 (sanitizer matrix preserved
  across feature releases) − 0.05 (Rt.04 ceiling) = 10.05, capped
  at 9.9 by the Rt.04 ceiling. The ceiling lifts to 10.0 when the
  borrow checker lands.

- I am extremely close to giving 10.0. The work I asked for at
  v5.2.0 is genuinely all done. The only thing keeping the score
  below 10 is one documented LEAK class baseline-gated with an
  honest workaround. If the v6.0 panel grades a borrow checker
  closure that closes Rt.04, the ceiling lifts naturally and 10.0
  is on the table. **Get this in front of v6.0.**
