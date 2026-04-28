# Panel v5.8.0 — Rattler (LLVM IR Correctness)

**Score:** 9.8 / 10
**Grade:** EXCEEDS
**Delta vs v5.2.0:** +0.5

## Summary

The v5.3.1 → v5.7.1 arc is the most significant correctness recovery in
the project's history from my axis. At v5.2.0 I scored **9.3 / 10
EXCEEDS** with a -0.3 delta because the In.1-stage2 fixed-point
regression broke the project's hardest-won self-consistency artifact —
`clone_instr_for_inline` covered only 10 of 30+ instruction kinds, and
the inliner's coverage gap silently produced invalid SSA wherever
the self-hosted compiler called itself. I asked specifically for two
things: extend the cloner to match `replace_uses_in_instr` coverage,
and restore fixed-point to at least NEAR. **Both done at v5.3.2;
verified clean at HEAD.** Plus the arc closed Sh.4 (async, real LLVM
coroutines), Sh.6 (tensor surface), Sh.7 (closure-typed parameters),
and B (or-pattern + identifier `None`) — every Sh.* docket I had
marked DEFERRED at v5.2.0 closed within the arc, and the goldens
went from 54/66 to 66/66 — first time in project history.

The IR-correctness bar held throughout. stage2.ll grew from 120,956
lines (FAIL) to 217,879 lines (`llvm-as` clean), and stage3.ll comes
out byte-identical except for VERSION metadata (4-line diff = 0.002%
within the NEAR threshold). The v5.6.x memory-safety closeout arc
closed Ve.1, Ve.2, Ve.3, Ve.4, and Lk.1 at structural root cause,
not via shortcut workarounds. The v5.5.4–v5.5.7 coroutine pipeline
is genuinely correct LLVM IR — `presplitcoroutine` attribute,
`@llvm.coro.id/begin/save/suspend/end` intrinsics, and CoroSplit
producing real `@foo.resume`/`@foo.destroy` split functions on every
async function with a real suspend point. The v5.7.0 Sh.7 closure
fix is symmetric across all four pipeline layers (parser, lower,
emit, mir_opt) — correct discipline for a load-bearing language
feature.

The remaining open items are all properly scoped: Rt.04 (multi-level
alias drop-glue, depth-2 struct→list→string) is correctly deferred to
v6.0 borrow-checker because v5.6.6 empirically demonstrated that any
single-level walk reproduces a UAF. Li.1 is unchanged from v5.2.0,
correctly deferred. There are zero NEW MEDIUM dockets opened in this
arc. From my axis the score is 9.8 — the ceiling moved up because
of the closure rate and the symmetry of the fixes, but there's still
0.2 reserved for the intermediate fixed-point churn (BROKEN at
v5.3.0, restored v5.3.2, broken transiently across v5.4.4 and across
the v5.5.x/v5.6.x arc, restored v5.6.11) and for the residual
v5.6.12 baseline-gated `62_list_output` leak which is honestly v6.0
work but is still a leak today.

## What improved since v5.2.0

### In.1-stage2 CLOSED (v5.3.2) — verified at HEAD

This was the single largest item from my v5.2.0 review (-0.45 in my
score breakdown). The root cause I diagnosed — `clone_instr_for_inline`
handling only 10 of 30+ instruction kinds — has been fixed completely.

**Verification at HEAD** (`mapanare/self/mir_opt.mn:864-1289`):

```
   864:fn clone_instr_for_inline(inst: Instruction, prefix: String, ...) -> List<Instruction> {
```

The function body now handles the following kinds with explicit rename
clauses (each with `if ik == "..."` + return):

| Kind | Line | Notes |
|---|---:|---|
| `return` | 869 | Copy + Jump to merge |
| `const` | 884 | dest |
| `copy` | 891 | dest + src |
| `binop` | 899 | dest + lhs + rhs |
| `call` | 908 | dest + args + indirect callee renaming (v5.7.0) |
| `alloca` | 936 | dest |
| `load` | 943 | dest + ptr |
| `store` | 951 | ptr + val |
| `unaryop` | 959 | dest + operand |
| `cast` | 967 | dest + src |
| `field_get` | 975 | dest + obj — v5.3.2 crash-site comment in source |
| `field_set` | 983 | obj + val |
| `struct_init` | 991 | dest + fields |
| `list_init` | 1006 | dest + elems |
| `tensor_init` | 1021 | dest + elems |
| `index_get` | 1036 | dest + obj + idx |
| `index_set` | 1045 | obj + idx + val |
| `map_init` | 1054 | dest + pairs |
| `enum_init` | 1069 | dest + payload |
| `enum_tag` | 1084 | dest + val |
| `enum_payload` | 1092 | dest + val |
| `wrap_some` | 1100 | dest + val |
| `wrap_none` | 1108 | dest only |
| `wrap_ok` | 1115 | dest + val |
| `wrap_err` | 1123 | dest + val |
| `unwrap` | 1131 | dest + val |
| `interp_concat` | 1139 | dest + parts |
| `phi` | 1154 | dest + entries (block_label prefixing) |
| `agent_spawn` | 1169 | dest + args |
| `agent_send` | 1184 | agent + val |
| `agent_sync` | 1192 | dest + agent |
| `signal_init` | 1200 | dest + val |
| `signal_get` | 1208 | dest + sig |
| `signal_set` | 1216 | sig + val |
| `stream_op` | 1224 | dest + src + args |
| `jump` | 1240 | block label prefixing |
| `branch` | 1246 | cond + true/false labels |
| `switch` | 1253 | tag + case/default labels |
| `await_suspend` | 1274 | dest + future (v5.5.2 Sh.4) |
| `block_on` | 1280 | dest + future (v5.5.2 Sh.4) |

**That's 39 explicit handlers.** The fallthrough at line 1287
(`result.push(inst); return result`) is correctly only reached for
truly novel future variants. Critically, every case verified above
includes both the `instr_dest(inst)` rename via `rename_value` AND
the operand renames — closing the use-def asymmetry that was the
v5.2.0 bug class.

The fixed-point verification at HEAD:

```
$ wc -l /tmp/stage2.ll /tmp/stage3.ll
  217879 /tmp/stage2.ll
  217879 /tmp/stage3.ll

$ diff /tmp/stage2.ll /tmp/stage3.ll
217879c217879
< !0 = !{!"5.8.0"}
---
> !0 = !{!"__MN_VERSION__"}

$ llvm-as /tmp/stage2.ll -o /dev/null; echo "RC=$?"
RC=0
```

**4-line diff, all VERSION metadata. NEAR FIXED POINT restored.**
This is exactly what I asked for in the v5.2.0 review's "path back
to 9.6+" section, item 1 (extend cloner) and item 2 (restore
fixed-point to at least NEAR). +0.40 baseline recovery.

The stage2.ll has `_inl0_6_t4`-style SSA values that I called out at
v5.2.0 as broken. Spot-check at HEAD shows them well-formed (sample
from `/tmp/stage2.ll:303-313`):

```
303:  br label %_inl0_6_entry
305:  %_inl0_6_line.addr = alloca i64
306:  store i64 %t0, ptr %_inl0_6_line.addr
307:  %_inl0_6_column.addr = alloca i64
308:  store i64 %t1, ptr %_inl0_6_column.addr
309:  %_inl0_6_end_line.addr = alloca i64
310:  store i64 %t2, ptr %_inl0_6_end_line.addr
311:  %_inl0_6_end_column.addr = alloca i64
312:  store i64 %t3, ptr %_inl0_6_end_column.addr
313:  %_inl0_6_line_val0 = load i64, ptr %_inl0_6_line.addr
```

Defs and uses match. `llvm-as` clean. Inliner output is well-formed.
**+0.05** for the symmetric coverage (cloner = renamer kinds).

### Sh.4 CLOSED (v5.5.4–v5.5.7) — real LLVM coroutine pipeline

At v5.2.0 I had this as DEFERRED LOW. It is now fully closed via the
v5.5.x coroutine arc. From my axis the IR shape is what matters:

**Verification at HEAD** (`mapanare/self/emit_llvm.mn`):

```
$ grep -c "presplitcoroutine" mapanare/self/emit_llvm.mn
2
$ grep -n "coro.id\|coro.begin\|coro.suspend\|coro.end" mapanare/self/emit_llvm.mn
837:    s = declare_runtime_fn(s, "llvm.coro.id", "token", "i32, ptr, ptr, ptr")
840:    s = declare_runtime_fn(s, "llvm.coro.begin", "ptr", "token, ptr")
841:    s = declare_runtime_fn(s, "llvm.coro.suspend", "i8", "token, i1")
842:    s = declare_runtime_fn(s, "llvm.coro.end", "i1", "ptr, i1, token")
1336:    s_aw = emit_line(s_aw, "  ... = call i8 @llvm.coro.suspend(...)")
5395:    s = emit_line(s, "  %coro.id = call token @llvm.coro.id(...)")
5398:    s = emit_line(s, "  %coro.hdl = call ptr @llvm.coro.begin(...)")
5404:    s = emit_line(s, "  %coro.init.susp = call i8 @llvm.coro.suspend(...)")
5544:    s = emit_line(s, "  %coro.final.susp = call i8 @llvm.coro.suspend(...)")
```

The full intrinsic set is wired and correctly threaded through the
emitter. The `is_async` gate at `emit_llvm.mn:5264` correctly classifies
a function before deciding sret/coroutine codegen. The
`use_sret_return(...) && f.name != "main" && !is_async` predicate at
line 5269 is exactly correct — async functions must not use sret
because their return-by-payload-store rewrite via `current_ret_type`
sentinel `"ASYNC_PTR:"` happens at the emit_mir_return level. SsRT
rules out for async, byref-only routing for sret. Correct layering.

The v5.5.5 AwaitSuspend pipeline at `emit_llvm.mn:1265-1340` shows
the full 6-block save/suspend/switch pattern: fast-path readiness →
`aw.drive` (coro.resume inner) → `aw.check` (re-check state) →
`aw.suspend` (`__mn_coro_register_wait` + `coro.save` + `coro.suspend`
+ switch) → `aw.resume` → `aw.ready`. The dominance discipline is
correct: `%aw.hdl.N` is loaded into the entry BB before the fast-path
branch (per the v5.5.7 SESSION_REPORT), so the cleanup trio
(`coro.destroy + free + free`) is SSA-legal at all three entry edges
to `aw.ready.N`.

The post-opt CoroSplit produces `@outer.resume`/`@outer.destroy`,
`@fanout.resume`/`@fanout.destroy`, etc. on every async function with
a real suspend point — verified by SESSION_REPORT for goldens
56/57/58/59. golden 55_async_basic fast-path-only (no suspend
edge); produces no split functions, which is also correct.

**Sanitizer state on the 5 Sh.4 goldens** (from MEASUREMENTS §5.1
+ v5.5.7 SESSION_REPORT): valgrind 0 errors / 0 leaks (e.g.,
59_async_fanout = 36 allocs / 36 frees / 0 in use at exit), ASan
0 errors, LSan 0 leaks, TSan 0 races on 56/57/58/59 under
`MAPANARE_ASYNC_THREADS=4`. **This is the real thing, not Option A's
synchronous degenerate case.** +0.10 for clean coroutine codegen at
real LLVM ABI semantics.

### Sh.6 CLOSED (v5.6.0–v5.6.3) — tensor surface

At v5.2.0 also DEFERRED LOW. Closed across 4 phased releases.

**Verification at HEAD**:

```
$ grep -c "__mn_tensor_" mapanare/self/emit_llvm.mn
174
```

174 references to the tensor runtime API surface — the full set of
literal/get/set/broadcast/scalar/r-scalar/reduction/slice/free
runtime declarations and their emit-side handlers. The arc shape is
clean: literals + 1D get/set (v5.6.0), multi-dim
`__mn_tensor_{get,set}_{f64,i64}_nd` with variadic ABI (v5.6.1),
broadcast + scalar binops with correct `noalias ptr` return prefix
(v5.6.2), slicing + reductions (v5.6.3), drop-glue (v5.6.4 Rt.06).

The variadic call-site emission at v5.6.1 is correct — explicit
function-type prefix `call <ret> (ptr, i64, ...) @<fn>(<args>)` per
LLVM's varargs requirements. The `noalias` attribute is correctly
placed on RETURN values not function attributes (caught and fixed
during v5.6.2 development per the SESSION_REPORT — Python's emitter
had this latent design via `get_fn_ret_prefix`, the self-hosted
emitter mirrors).

The v5.6.4 Rt.06 tensor drop-glue completes Own.1 Phase 3:
`emit_track_tensor` mirrors `emit_track_boxed` structurally
(zero-init slot in entry-block prelude, store post-alloc, ownership
list push, loop-depth pre-store free). `emit_drop_glue_tensors`
parallels `_boxed`. The dual-push of ret-tensor-ptrs into both
`ret_tensor_ptrs` and `ret_box_ptrs` is correct over-approximation:
each helper alias-checks its own slot list, so the ptr appearing in
both lists short-circuits both drops on the matching helper, and
the non-matching helper's slot list doesn't alias the ret ptr — no
double-free, no missed-free. Symmetric reasoning for boxed returns.
**Clean drop-glue discipline.** +0.05.

Hero metric: all 5 tensor goldens (49–53) byte-identical to expected
output at HEAD. Verified via `python3 scripts/test_native.py`:
49_tensor_literal `1 3 1 3 2 6 1 6 ...`, 50_tensor_indexing
`1 3 4 6 10 30 ...`, 51_tensor_broadcast `11 44 9 36 ...`,
52_tensor_slicing `15 3 5 1 4 0 ...`, 53_linear_regression
`w = 1.96879 / b = 0.560177 / converging`. All tensor goldens are
LSan CLEAN per v5.6.4 SESSION_REPORT.

### Sh.7 CLOSED (v5.7.0) — closure-typed parameters

This is the most surgical fix in the arc. Four self-hosted changes
across all four compiler layers, each at the right abstraction.

**Verification at HEAD**:

1. **Parser fix** — `mapanare/self/parser.mn:1569-1599`. The
   `FAT_ARROW` handler now extracts multi-param lambdas from
   `(a, b) => ...`:

   ```
   1581:            match left {
   1582:                Ident(name) => {
   1583:                    params.push(new_param(name, none))
   1584:                },
   1585:                ListLit(elems) => {
   1586:                    let mut li: Int = 0
   1587:                    for _ in 0..32 {
   1588:                        if li >= len(elems) { break }
   1589:                        let elem: Expr = elems[li]
   1590:                        if expr_kind(elem) == "ident" {
   1591:                            params.push(new_param(expr_ident_name(elem), none))
   1592:                        }
   1593:                        li = li + 1
   1594:                    }
   1595:                },
   1596:                _ => {}
   1597:            }
   ```

   Pre-v5.7.0, only the `Ident` arm was handled — `ListLit` was a
   silent fallthrough leaving lambdas with zero params and
   undefined-variable errors when their bodies referenced `a, b, …`.
   The 32-iteration cap is fine for any plausible lambda arity.

2. **Lower fix** — `mapanare/self/lower.mn:2458-2477`. `lookup_var(st, fn_name)`
   precedes the lambda-rename path so fn-typed locals route through
   indirect-call SSA name:

   ```
   2465:    let var_lookup: Option<Value> = lookup_var(st, fn_name)
   2466:    match var_lookup {
   2467:        Some(addr_v) => {
   2468:            if addr_v.ty.kind == TK_FN() {
   2469:                let load_r: LowerResult = make_value(st, addr_v.ty, fn_name + "_val")
   2470:                let load_s: LowerState = emit_instr(load_r.state, Instruction::Load(load_r.value, addr_v))
   2471:                let dr_ind: LowerResult = make_value(load_s, mir_unknown(), "t")
   2472:                let s_ind: LowerState = emit_instr(dr_ind.state, Instruction::Call(dr_ind.value, load_r.value.name, args))
   2473:                return new_lower_result(dr_ind.value, s_ind)
   2474:            }
   2475:        },
   2476:        _ => {}
   2477:    }
   ```

   Mirrors Python `_lower_call` v4.103.0 docket #5. The Load-then-Call
   sequence with `load_r.value.name` (the SSA name `%fn_name_val`)
   passed as the Call's fn_name is exactly the right shape.

3. **Emit fix** — `mapanare/self/emit_llvm_ir.mn:233-247`. Both
   `emit_call_ir` and `emit_call_void` recognize `%`-prefixed
   callees:

   ```
   233:fn emit_call_ir(name: String, ret_ty: String, callee: String, args: String) -> String {
   234:    // v5.7.0 Sh.7: callees starting with `%` are SSA values (indirect
   235:    // call through a closure-typed local) — emit without `@` prefix.
   236:    if callee.starts_with("%") {
   237:        return "  " + name + " = call " + ret_ty + " " + callee + "(" + args + ")"
   238:    }
   239:    return "  " + name + " = call " + ret_ty + " @" + callee + "(" + args + ")"
   240:}
   ```

   This is the LLVM IR-level distinction between direct
   (`call <ret> @fn(...)`) and indirect (`call <ret> %fn(...)`) calls.
   Correct.

4. **Inliner fix** — `mapanare/self/mir_opt.mn:921-930`. The Call
   case in `clone_instr_for_inline` now renames `fn_name` when it's
   an SSA value:

   ```
   918:        // v5.7.0 Sh.7: indirect calls have fn_name == "%localval" and
   919:        // must be renamed alongside other SSA values; direct calls
   920:        // (`@some_fn`) keep their bare-symbol name unchanged.
   921:        let fn_str: String = instr_call_fn(inst)
   922:        let mut new_fn_str: String = fn_str
   923:        if fn_str.starts_with("%") {
   924:            let bare: String = fn_str.substr(1, len(fn_str) - 1)
   925:            let rn_opt: Option<String> = find_const(renames, fn_str)
   926:            match rn_opt {
   927:                Some(rn) => { new_fn_str = rn },
   928:                _ => { new_fn_str = "%" + prefix + bare }
   929:            }
   930:        }
   ```

   This is the correct invariant for the inliner: when a callee
   contains an indirect call, the fn_name SSA reference must rename
   alongside other SSA values, otherwise inlining produces a dangling
   reference to a name that no longer exists in scope. The
   `replace_uses_in_instr` companion at lines 689+ handles the same
   case for the use-side renamer.

**Symmetric across all four layers.** This is exactly the discipline
the project lacked at v5.2.0 (where `clone_instr_for_inline` covered
10 kinds while `replace_uses_in_instr` covered 30+). Each layer's fix
is precisely 8-15 LOC at the right abstraction. **+0.10**.

Hero metric: goldens 65/66 → 66/66 — first time in project history.
Confirmed at HEAD: `64_closure_typed 25L->245L 22bb 260stk 10ms (1
fns) stg1:3fns` (PASS).

### B CLOSED (v5.7.0) — or-pattern + identifier `None`

The fix is at `mapanare/_is_enum_variant_name`'s short-circuit for
built-in `None`/`Some`/`Ok`/`Err`, plus `Identifier("None")`
resolution in `_infer_expr` and `_lower_identifier` (Python
bootstrap). Self-hosted `bind_pattern` doesn't have the over-strict
check — just binds from the first alt — so no self-hosted mirror was
needed. Verified at HEAD via `51_match_guards_and_or` golden passing
(`PASS 51_match_guards_and_or 17L->298L 20bb 274stk 8ms (2 fns)`).
Bootstrap pytest 225 passed / 0 failed (was 13 baseline including
51) per v5.7.0 SESSION_REPORT.

This is small from my axis (the IR shape is unchanged because the
fix is at the AST→MIR boundary, not at the emit layer), but the
symmetry with Sh.7 is good — both shipped together at v5.7.0 to
close the corpus. +0.0 (correctness-neutral on my axis).

### Own.1 Phase 2 CLOSED (v5.4.0–v5.4.4) — drop-glue infrastructure

At v5.2.0 this was carried forward as a 28-panel-old item. The arc
closes it across 5 micro-releases (v5.4.0/.1/.2/.3/.4):

- v5.4.0: `Move` MIR variant in both emitters; four ownership-tracking
  slots in `EmitState` (`str_owned`/`list_owned`/`boxed_owned`/`moved_locals`);
  drop-glue helpers + `emit_drop_glue` dispatcher wired into
  `emit_mir_return`. Registry gate 23/23 clean. Owner-list population
  deferred.
- v5.4.1: shadow-slot architecture ported from Python; owner lists
  populated at all heap-allocating emit sites (`emit_mir_call`
  dispatch, `emit_binop +`, `emit_interp_concat`, `emit_list_init`).
  Three new EmitState fields for entry-prelude buffering. Drop-glue
  revised with per-slot `icmp eq ptr` alias-checks.
- v5.4.2: `detect_leaks=1` golden gate via
  `scripts/run_asan_leak_goldens.sh`. 13-builtin `is_string_returning_builtin`
  helper closes 4 goldens × 9 leak objs / 202 B.
- v5.4.3: `EmitState.loop_depth` field + `emit_track_*` pre-store
  free in loops. Closes Rt.03 (22_string_builder loop-reassignment
  leak).
- v5.4.4: Move-aware drop-glue infrastructure with parallel source
  arrays (`str_owned_source`/`list_owned_source`/`boxed_owned_source`).
  Lowerer `Move` emission in both lower.mn and lower.py. Guard-lift
  for `%struct.*` returns implemented and reverted (5× IR inflation
  + Ve.1 regression).

**Verification at HEAD** (`mapanare/self/emit_llvm.mn`):

```
$ grep -c "icmp eq ptr" /tmp/stage2.ll
3386
```

3,386 alias-check sites in stage2.ll. The drop-glue helpers are
firing extensively. The discipline is correct: each per-slot guard
short-circuits the free when the slot's value aliases the function's
ret ptr, preventing the UAF that v5.6.6's one-level walk demonstrated
empirically.

The infrastructure ships with the right scoping:
- Scalar String / List / ptr returns: per-slot alias-check via
  `extractvalue` once + `icmp eq ptr` + branch.
- Aggregate returns (struct / enum / Option / Result): conservative
  skip on all drops. UAF-safe; trades leaks for safety. v6.0
  borrow-checker scope.
- Multi-level alias (struct→list→string at depth 2): documented as
  Rt.04 carry-forward. v5.6.6 attempted single-level walk; reproduced
  UAF; reverted to RESCOPE skip. Correct call.

The "no cheap shit" directive is visible throughout: v5.4.4's
guard-lift attempt was reverted because it surfaced a Ve.1 stage2
runtime segfault. v5.6.10's scalar gate was reverted because it
surfaced Lk.1. v5.6.13 stopped at Layer 1 cleanup because Layer 2
(move-on-assignment) had no observable bug pressure. **Each
de-escalation made the right call.** +0.10.

### v5.6.x memory-safety arc — Ve.1, Ve.2, Ve.3, Ve.4, Lk.1 closed

Five dockets closed in this sub-arc, all at structural root cause:

| Docket | Closed | Symptom | Fix |
|--------|--------|---------|-----|
| Ve.1 | v5.6.5 | parse_fn_body 8B-past-256B malloc overflow | GEP-trick sizing + struct_byte_size delegate |
| Ve.2 | v5.6.7 partial → v5.6.12 closed | Empty-list elem_ty defaults to UNKNOWN → 8B slots | `lower_let_list_hint` + `extract_list_elem_ty` route through `lower_list_typed` |
| Ve.3 | v5.6.9 | drop-glue UAF on `List<Enum>` returns (multi-level alias) | RESCOPE: skip drops conservatively when `ret_ty == llvm_list_rt() && len(boxed_owned) > 0` |
| Ve.4 | v5.6.11 | match-arm empty BasicBlocks via elem_size mismatch | 14 LOC at `emit_index_get` + `emit_index_set` — load runtime elem_size, compute offset = idx × elem_size, GEP i8 + offset |
| Lk.1 | v5.6.12 | Alloca-aliasing leak via destination-passing semantics | `lower_list_typed_into(st, elements, hint, dest_name)` — destination passing in `lower_let` |

**Verification of Ve.4 fix at HEAD** (`mapanare/self/emit_llvm.mn:2588-2606`):

```
2588:        let data: String = "%lg.data." + cnt_lg
2589:        s = emit_line(s, "  " + data + " = load ptr, ptr " + dp)
2590:        // v5.6.11 Ve.4 — use runtime elem_size for the offset, not a constant
...
2598:        let eszp: String = "%lg.eszp." + cnt_lg
2599:        s = emit_line(s, "  " + eszp + " = getelementptr inbounds " + lt + ", ptr " + tmp + ", i32 0, i32 3")
2600:        let esz: String = "%lg.esz." + cnt_lg
2601:        s = emit_line(s, "  " + esz + " = load i64, ptr " + eszp)
2602:        let off: String = "%lg.off." + cnt_lg
2603:        s = emit_line(s, "  " + off + " = mul i64 " + idx.name + ", " + esz)
2604:        let ep: String = "%lg.ep." + cnt_lg
2605:        s = emit_line(s, "  " + ep + " = getelementptr inbounds i8, ptr " + data + ", i64 " + off)
2606:        s = emit_line(s, "  " + dn + " = load " + dest_ty + ", ptr " + ep)
```

This is correct. The runtime stride is loaded from list field 3
(`elem_size`), multiplied by the index, and GEP'd over an `i8`
pointer. SROA elides the runtime load when elem_size is a known
constant. The symmetry at `emit_index_set` (line 2689+) preserves
the read/write invariant. **This is the right fix at the right
abstraction.** Constant-stride GEP would be tempting (smaller IR,
LLVM optimizes), but with the runtime allocator floor at 384 bytes
for 7 residual sites, the consistency invariant requires runtime
elem_size on both read and write sides.

**Verification of Lk.1 fix at HEAD** (`mapanare/self/lower.mn:758-797`):

```
758:    // v5.6.12 Lk.1 fix — destination passing for List let-bindings.
759:    // When the hint path applies, pre-compute the var's alloca name
760:    // and lower the list literal directly into it via
761:    // `lower_list_typed_into`. Skips the post-emit Alloca + Store pair
762:    // entirely (those would create a duplicate alloca + useless copy
763:    // — exactly the alloca-aliasing leak from v5.6.10 Lk.1).
...
790:        let r2: LowerResult = lower_list_typed_into(s, expr_list_elements(value), hint_elem, var_base)
```

The destination-passing pattern is the correct structural answer.
The pre-v5.6.12 version emitted `Alloca` + `Store` after the value
lowered into a fresh tmp, creating two allocas (`%t<N>.addr` for the
tmp + `%var.addr` for the let binding) where pushes wrote back to one
and the drop-glue tracking pointed at the other. Mirrors rustc's
`PlaceRef` / result-location semantics. **Right abstraction; right
fix.** +0.10.

The Ve.3 RESCOPE at v5.6.9 is honest: 25 LOC in `emit_llvm.mn:4763`
skips drops conservatively for `ret_ty == llvm_list_rt() && len(boxed_owned) > 0`.
Cost: intermediate boxes leak. Accepted per v5.6.6 precedent — UAF
prevention > leak prevention, and multi-level alias analysis is
v6.0 borrow-checker scope. The RESCOPE pattern is consistent across
v5.6.6 (Rt.04), v5.6.9 (Ve.3), v5.6.13 (Layer 2 move-on-assignment).

### Stream-C closed (v5.3.1)

I had this as a v5.2.0 LOW carry-forward suspecting a regression from
the Perf.1 inline list change. Closed cleanly: 74/74 C runtime tests
pass under plain / ASan / TSan (verified §1.3 of MEASUREMENTS).
+0.05.

### E1 LLVM-version-sensitive test relaxed (v5.3.1)

I had this as An.9-llvm18 LOW NEW carry-forward. Closed at v5.3.1.
+0.05.

### Lint-v5.2.0 closed (v5.3.1)

I had this as a v5.2.0 LOW carry-forward (4 black, 9 ruff). Closed
at v5.3.1; `make lint` clean throughout the rest of the arc.
+0.0.

## What remains open

### Rt.04 — multi-level alias drop-glue (MEDIUM, deferred to v6.0)

This is the only MEDIUM-severity carry-forward. The resource lives
at struct→list→string depth 2 (e.g., `62_list_output`'s returned
struct holds a List<String>). v5.6.6 empirically demonstrated that
any single-level `%struct.*` field walk reproduces a UAF — the walk
sees the list-alias but doesn't descend into the list to alias its
String elements. Three gate thresholds tested
(N=8/M=50, N=4/M=20, N=4/M=10); UAF reproduced at all. Honest scope:
the structural fix is the borrow checker (v6.0).

`62_list_output` stays LEAK at HEAD (baseline-gated, 13 obj / 346 B
refreshed v5.6.12). The leak is real and detected by LSan; it
just doesn't escalate to a regression because the baseline TSV
already includes it.

This is correctly scoped — the alternative (ship a single-level walk
with known UAF) would be much worse than a documented leak. But
it's still a leak today. **-0.10** off the perfect score, not
because the deferral is wrong but because the leak is observable
in the corpus today.

### Sh.5 — `const` in fn bodies (LOW, deferred)

Unchanged from v5.2.0. Module-level `const` works; fn-body partial
support. Workaround documented (use `let`). v5.x feature track.
Correctly deferred.

### Sh.9a / Sh.9b — async emitter quirks (LOW, deferred)

Documented in `docs/guides/async.md` with workarounds. v5.x feature
track. Not on my axis directly (these are higher-level async API
issues, not coroutine ABI issues — those are clean).

### Gr.1 — multi-line list/tensor literals parse-error (LOW, deferred)

Workaround: put literal on one line. v5.x parser quirk.

### Rt.2 / Rt.3 — runtime quirks (LOW, deferred)

`dir_create(recursive=true)` ignores the flag; `tmpfile_path` returns
literal `/tmp/mn_tmp_XXXXXX` without `mkstemp`. Both have documented
workarounds. v5.x.

### Rt.01 / Rt.02 — third-party leaks (LOW, n/a)

libcuda driver state (260 B) + Mesa/Vulkan ICD loader (~50 KB).
Suppressed in `scripts/asan_leak_suppressions.txt` and baseline-gated
in `scripts/check_leak_summary.py`. Not Mapanare correctness issues.

### Li.1 — LICM unit tests pass, live goldens regress (LOW, unchanged)

Unchanged from v5.2.0. Pass remains disabled in both pipelines.
Correctly deferred. v5.x.

## Score breakdown

Starting from v5.2.0 baseline of 9.3:

| Item | Adjustment |
|------|-----------:|
| In.1-stage2 closure (v5.3.2): cloner extended to 39 explicit kinds; fixed-point restored to NEAR | +0.40 |
| Inliner output well-formed at HEAD: `%_inl0_6_*` SSA values defined-then-used; `llvm-as` clean on stage2.ll | +0.05 |
| Sh.4 closure (v5.5.4–v5.5.7): real LLVM coroutine pipeline; `presplitcoroutine` + intrinsics + CoroSplit-ready; clean sanitizer gate on 5 async goldens | +0.10 |
| Sh.6 closure (v5.6.0–v5.6.3): tensor surface ported with correct variadic ABI, `noalias` placement, drop-glue (Rt.06) | +0.05 |
| Sh.7 closure (v5.7.0): symmetric 4-layer fix (parser + lower + emit + mir_opt) at right abstractions | +0.10 |
| Own.1 P2 closure (v5.4.0–v5.4.4): drop-glue infrastructure ships across 5 releases, with explicit reverts on bad attempts ("no cheap shit" discipline) | +0.10 |
| Ve.4 fix (v5.6.11): elem_size-stride GEP correctness at right abstraction (runtime stride for both read/write paths) | +0.05 |
| Lk.1 fix (v5.6.12): destination-passing semantics at lower.mn::lower_let; correct rustc-style `PlaceRef` mechanism | +0.10 |
| Stream-C closure (v5.3.1) | +0.05 |
| An.9-llvm18 closure (v5.3.1) | +0.05 |
| Lint-v5.2.0 closure (v5.3.1) | +0.0 |
| Goldens 54/66 → 66/66 (first time in project history) | +0.05 |
| Rt.04 leak observable in corpus today (62_list_output 13 obj / 346 B baseline-gated) | -0.10 |
| Intermediate fixed-point churn across the arc (BROKEN v5.3.0, restored v5.3.2, transient breakage v5.4.4 + v5.5.x + v5.6.x, restored v5.6.11) | -0.10 |
| **Net** | **+0.50** |

**9.3 + 0.50 = 9.8 / 10 EXCEEDS**

Reserved 0.2 from a perfect score:
- 0.10 for Rt.04 leak (the structural answer is v6.0; correctly
  deferred but the leak is real today)
- 0.10 for the intermediate fixed-point churn — restored at v5.6.11,
  but the system was BROKEN-or-NEAR through 7 releases of the v5.6.x
  arc, and the v5.4.4 guard-lift Ve.1 regression was a self-inflicted
  break that required a revert. The end state at v5.7.1 is the right
  state, but the journey had observable churn.

## Carry-forward to v6.0

| Docket | Severity | Status | Scope |
|---|---|---|---|
| Rt.04 | MEDIUM | DEFERRED → v6.0 | Multi-level alias drop-glue (struct→list→string depth 2). 62_list_output stays LEAK; structural fix is the borrow checker. |
| Li.1 | LOW | OPEN (4+ cycles) | LICM needs fixpoint + preheader. Pass disabled. v5.x. |
| Sh.5 | LOW | DEFERRED | `const` in fn bodies; v5.x feature. |
| Sh.9a / 9b | LOW | DEFERRED | async emitter quirks; documented workarounds. |
| Gr.1 | LOW | DEFERRED | multi-line literal parse-error. |

## Reproducibility

All claims in this review can be verified at HEAD:

```bash
# 1. Inliner cloner coverage — 39 explicit handlers
grep -nE "^    if ik ==" mapanare/self/mir_opt.mn | head -50

# 2. Fixed-point restored — 4-line VERSION metadata diff
bash scripts/verify_fixed_point.sh --keep
diff /tmp/stage2.ll /tmp/stage3.ll
# Expected: 4 lines, all VERSION metadata
llvm-as /tmp/stage2.ll -o /dev/null; echo "RC=$?"
# Expected: RC=0

# 3. Inliner output well-formed
grep -n "%_inl[0-9]" /tmp/stage2.ll | head -20
# Expected: %_inlN_M_* SSA values used after definition

# 4. Coroutine intrinsic emission
grep -c "presplitcoroutine" mapanare/self/emit_llvm.mn  # 2
grep -n "coro.id\|coro.begin\|coro.suspend\|coro.end" mapanare/self/emit_llvm.mn

# 5. Tensor surface
grep -c "__mn_tensor_" mapanare/self/emit_llvm.mn  # 174

# 6. v5.7.0 Sh.7 indirect-call routing in lower.mn
grep -n "lookup_var(st, fn_name)" mapanare/self/lower.mn  # line 2465
grep -n "starts_with(\"%\")" mapanare/self/emit_llvm_ir.mn  # lines 236, 243

# 7. Ve.4 elem_size-stride fix
grep -n "v5.6.11 Ve.4" mapanare/self/emit_llvm.mn

# 8. Lk.1 destination-passing fix
grep -n "lower_list_typed_into\|lower_struct_new_into" mapanare/self/lower.mn

# 9. Drop-glue alias check sites
grep -c "icmp eq ptr" /tmp/stage2.ll  # 3386

# 10. Goldens 66/66
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1
# Expected: All 66 tests passed
```

---

**One-line summary for lead: 9.8 / 10 EXCEEDS — In.1-stage2 closed
+ Sh.4/6/7+B closed + Ve.1/2/3/4 + Lk.1 closed at root cause +
fixed-point NEAR + 66/66 goldens; -0.2 for Rt.04 leak (v6.0 scope)
and intermediate v5.6.x fixed-point churn.**
