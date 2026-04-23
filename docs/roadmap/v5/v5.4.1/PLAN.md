# Mapanare v5.4.1 — "Own.1 Phase 2 — make the v5.4.0 helpers actually fire"

> **Land the end-to-end drop-glue path the v5.4.0 infrastructure was
> built for.** User programs compiled by `mnc-stage1` stop leaking
> their local Strings, Lists, and boxed enum payloads at normal
> function returns. Goldens stay at 54/66 (no feature work); ASan
> leak-detection stays off (enabled in v5.4.2).

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v5.4.0 shipped (Move instruction, EmitState slots,
drop-glue helpers + `emit_mir_return` wiring)
**Estimated work:** 1–2 sessions (~4–6 hours)
**Owner docket:** Own.1 Phase 2 completion — what was deferred from
v5.4.0 with "three follow-on tasks must land together"

---

## Why this release exists

v5.4.0 shipped the infrastructure (Move variant in both emitters,
`str_owned` / `list_owned` / `boxed_owned` / `moved_locals` slots on
`EmitState`, drop-glue helpers, `emit_mir_return` wiring) but left
the owner lists **empty**. The helpers are no-ops; stage1-emitted IR
for user programs is byte-identical to v5.3.3 except for the VERSION
placeholder.

v5.4.1 populates those lists and fixes the three correctness problems
that v5.4.0's skeleton helpers have under populated lists:

### Problem 1 — end-of-function leaks

A program like:

```mapanare
fn build() -> String {
    let r: String = "hello" + "world"  // __mn_str_concat result
    return r
}
```

currently emits no free. The `r`-slot and the concat heap memory both
leak at every return. v5.4.1 adds `__mn_str_free(%r_track_value)`
before `ret`.

### Problem 2 — return-value escape

v5.4.0's helpers skip owned locals whose name matches `ret_val_base`.
But `ret` always operates on an SSA temp loaded from an alloca —
`ret_val_base("%t5")` is `"t5"`, never matching `"r.addr"`. The
escape guard never fires. Naive drop-glue would UAF the caller.

Python solves this with `_emit_drop_glue_collect_ret_ptrs`: at each
return, `extractvalue` the returned String's data pointer, collect
every pointer visible via struct-field walk, and compare against each
tracked slot's data pointer before freeing. v5.4.1 ports the subset
needed for scalar String / List / boxed returns and single-level
struct returns containing String/List fields.

### Problem 3 — reassignment leaks

```mapanare
fn repeat_str(s: String, n: Int) -> String {
    let mut result: String = ""
    for _ in 0..n {
        result = result + s   // each iteration leaks the prior concat result
    }
    return result
}
```

Python tracks this with a **shadow-slot architecture**:
`_track_string` allocates a fresh `%str_track.N = alloca {ptr, i64}`
at each concat/assignment site, stores the current value-snapshot
into it, and appends to `_local_strings`. At drop-glue, every shadow
slot is iterated — including snapshots whose user alloca was later
overwritten. `__mn_str_free` tolerates null + non-heap, so the empty
initial value is safe.

v5.4.1 ports the shadow-slot pattern for Strings, boxed payloads, and
closure envs (the three snapshot-eligible kinds). Lists stay with the
simpler name-tracking + load-at-return approach v5.4.0 already wired.

---

## Scope

### What ships

#### 5.4.1a — Shadow-slot helpers in `emit_llvm.mn`

Port three `_track_*` helpers from Python:

```mapanare
fn emit_track_string(st: EmitState, val_name: String) -> EmitState
fn emit_track_boxed(st: EmitState, ptr_val: String) -> EmitState
fn emit_track_closure(st: EmitState, val_name: String) -> EmitState
```

Each one:
1. Allocates a fresh tracking slot (`%str_track.N`, `%box_track.N`,
   `%clos_track.N`) in the entry block via a lazy-entry-injection
   mechanism — v5.4.1 adds `EmitState.entry_prelude_lines: List<String>`
   or equivalent since the self-hosted emitter doesn't have Python's
   `self._ent` list today.
2. Zero-initializes the slot (so pre-assignment reads are well-defined).
3. Stores the passed value into the slot at the current emission point.
4. Appends the slot name to `st.str_owned` / `boxed_owned` — lists
   that v5.4.0 already added to `EmitState`.

#### 5.4.1b — Call-site instrumentation (the bulk of the diff)

Call `emit_track_string` from every site that produces a new
owning-String value:

| Site | Python equivalent | Self-hosted fn |
|---|---|---|
| String-literal `Const` emission | `_do_const` when ty==STR | `emit_const` |
| `__mn_str_concat` / `__mn_str_from_int` / other String-returning runtime calls | `_do_call` when fn returns STR | `emit_mir_call` String-returning branches |
| `Copy` where src is a tracked String | `_do_copy` | `emit_copy` |
| `EnumPayload` extraction producing a String | `_do_enum_payload` | `emit_enum_payload` |
| User function call returning String | `_do_call` user branch | `emit_mir_call` fallthrough |
| `InterpConcat` | `_do_interp` | `emit_interp_concat` |

Same for boxed (enum payloads, tagged unions) and closures
(`ClosureCreate`).

For Lists: `emit_list_init_checked` / `emit_list_init` push the
alloca name to `st.list_owned` once per variable (name-tracking, not
shadow-slot — v5.4.0's helper already loads + frees at return).

#### 5.4.1c — Return-escape detection in `emit_mir_return`

Port `_emit_drop_glue_collect_ret_ptrs` (the subset Mapanare needs):

```mapanare
struct RetPtrs {
    str_data_ptrs: List<String>,     // extractvalue %ret, 0 for String returns
    list_data_ptrs: List<String>,    // extractvalue %ret, 0 for List returns
    struct_field_ptrs: List<String>, // walked struct-field escapes (scalar only)
}

fn collect_ret_ptrs(st: EmitState, ret_val: String, ret_ty: String) -> (EmitState, RetPtrs)
```

Update `emit_drop_glue_strings` / `_lists` / `_boxed` to skip any
slot whose loaded data pointer matches any pointer in `RetPtrs`.

The matching IR becomes:

```llvm
  %drop.s.42 = load {ptr, i64}, ptr %str_track.7
  %drop.p.42 = extractvalue {ptr, i64} %drop.s.42, 0
  %drop.same.42 = icmp eq ptr %drop.p.42, %ret.ptr
  br i1 %drop.same.42, label %drop.skip.42, label %drop.free.42
drop.free.42:
  call void @__mn_str_free({ptr, i64} %drop.s.42)
  br label %drop.skip.42
drop.skip.42:
```

This is the multi-block branch pattern v5.4.0's skeleton deliberately
avoided. v5.4.1 accepts the complexity because skipping returned
pointers is the entire point.

#### 5.4.1d — Runtime free declarations

Add to `declare_all_runtime` in `emit_llvm.mn`:

```mapanare
s = declare_runtime_fn(s, "__mn_str_free", "void", "{ptr, i64}")
s = declare_runtime_fn(s, "__mn_list_free", "void", "ptr")
s = declare_runtime_fn(s, "free", "void", "ptr")
```

Matches the attribute strings already present at lines 375–377.

#### 5.4.1e — Lowerer Move emission

`mapanare/self/lower.mn::lower_call_by_name` (line 2027): before each
`Instruction::Call(...)` emission, emit `Instruction::Move(arg)` for
each argument. Blanket-move mirrors Python's `_do_call` at line 3882.

Since the many builtin branches in `lower_call_by_name` each emit
their own Call, this refactor is cleanest as a helper:

```mapanare
fn emit_arg_moves(st: LowerState, args: List<Value>) -> LowerState
```

called once at the entry of `lower_call_by_name` — the Move
instructions go into the block in program order, followed by the
Call. The self-hosted emitter's `"move"` kind (already populating
`moved_locals` after v5.4.0 Phase 4) picks them up.

Python side unchanged — `_do_call`'s existing blanket-move covers
all code paths through the Python emitter.

### What does NOT ship

- **Map / Signal / Stream / Tensor drop-glue.** Their tracking
  containers are mutable (like List); v5.4.1 does not exercise them
  because the 54-passing-goldens don't stress those resources. v5.4.3+
  scope if demand appears.
- **ASan leak-detection gate.** v5.4.2.
- **Field-level reassignment drop** (`FieldSet` where the old field
  owned a String). v5.4.2 if leak-gate reveals it.
- **Deep pointer walk at return** (boxed enum payloads containing
  other boxes). Python's `_emit_drop_glue_boxed` has a conservative
  skip-all-when-struct-returned guard (line 1821); v5.4.1 copies the
  same guard.

---

## Exit criteria

1. 66 goldens compile + `llvm-as` clean (54/66 pass, 12 fail for
   unrelated feature gaps — unchanged from v5.4.0).
2. 11 Sh.2 tests still exit 0 under ASan (baseline preserved).
3. Valgrind 0 new ERRORS across 66 goldens (baseline 0).
4. ASan without leak detection: 55 CLEAN / 11 CRASH_NO_ASAN
   unchanged.
5. Fixed-point: stage2.ll `llvm-as` OK (stage3 empty preserved —
   Ve.1 not in scope).
6. Non-bootstrap pytest 0 failures (after runtime VERSION rebuild).
7. `make lint` clean.
8. `python3 scripts/check_struct_registry.py` clean.
9. Register-struct gate (Reg.1) clean — any new EmitState fields
   (`entry_prelude_lines` if introduced) register correctly.
10. `PARITY_GAPS.md` updates Own.1 Phase 2 row — infrastructure now
    **functional**, not just scaffolded.

---

## Design decisions

### D1 — Shadow-slot for String/boxed/closure, name-tracking for List

Python's architecture. Mutable containers (List, Map, Signal, Stream)
change in place; tracking a snapshot is wrong. Immutable values
(String by-value, boxed ptr, closure env ptr) DO leak on reassign
unless tracked per assignment. Port the distinction verbatim.

### D2 — Entry-block prelude injection

Python has `self._ent: list[str]` holding entry-block lines emitted
lazily. The self-hosted emitter currently emits the entry block
sequentially as MIR instructions come in, so tracking slot allocas
must be queued somewhere and flushed at entry block close.

Two options:
- **D2a:** Add `EmitState.entry_prelude_lines: List<String>`, emit
  them when the entry block label is written. Requires Reg.1 gate
  update (23 → 24 EmitState fields).
- **D2b:** Emit tracking allocas inline at each `emit_track_*` site.
  Simpler, but violates LLVM's "allocas in entry block only" ABI
  assumption for clean stack allocation.

**Choose D2a.** The ABI contract matters; the registry update is
mechanical (Phase 2 already added 4 fields).

### D3 — Keep v5.4.0's simple drop-glue helpers; re-wire call sites

v5.4.0's `emit_drop_glue_strings` currently loads from `%<name>`
directly. v5.4.1 revises it to load from tracking slots stored in
`st.str_owned`. Signature stays the same; implementation grows to
include the escape-ptr compare branches.

### D4 — Don't touch Python lower.py

Python's `_do_call` already does blanket-move via `_move_resource`.
Adding `Move` emission in Python lower.py would be redundant. Leave
it alone. Python `_do_move` (added v5.4.0 Phase 1) stays dormant
unless some test manually constructs MIR containing Move.

### D5 — Single regression test per problem class

- `tests/native/test_v5_4_1_return_escape.py` — compiles a simple
  String-returning function, runs under ASan, confirms 0 UAF.
- `tests/native/test_v5_4_1_no_leak_simple.py` — compiles a
  single-assignment function, runs under ASan with leak detection
  enabled in this test only, confirms 0 leaks.

Loop-reassignment leak test deferred to v5.4.2 alongside the global
leak-detection gate.

---

## Risks

### R1 — Escape detection produces invalid IR

**Risk: HIGH.** The multi-block branch pattern for
`icmp eq ptr %slot_data, %ret_data; br` requires matching block
labels and proper PHI placement at joins. Easy to get wrong.

**Mitigation:** `llvm-as /tmp/stage2.ll` after every
`emit_track_*` / drop-glue helper landing. Same process v5.4.0 used.

### R2 — Reg.1 gate fires on `entry_prelude_lines`

**Risk: LOW.** Gate caught the v5.4.0 EmitState expansion cleanly.
Mechanical update.

### R3 — stage2 binary grows substantially

**Risk: MEDIUM.** Shadow-slot allocation at every String literal +
concat site will add dozens of allocas per function. stage2.ll might
grow 30-50%. Functionally fine; may change fixed-point diff.

**Mitigation:** stage3 already doesn't emit today (Ve.1), so strict
fixed-point isn't a v5.4.1 gate. Document the new stage2.ll size in
SESSION_REPORT.

### R4 — Goldens regress

**Risk: MEDIUM.** Drop-glue that frees a value still in use = UAF
crash. 11 Sh.2 tests and 54 passing goldens all suddenly touch free
paths they never exercised.

**Mitigation:** run goldens + ASan after **every** emit-site
instrumentation (at least 6 mini-checkpoints). If goldens drop below
54, roll back the most recent instrumentation.

### R5 — Double-free in the runtime

**Risk: MEDIUM.** If a String is tracked in TWO shadow slots (e.g.,
`Copy` produces a new value but shares the data pointer), both drop-
glue passes try to free it. `__mn_str_free` calls `__mn_free` which
is NOT idempotent.

**Mitigation:** Python handles this via `_str_slots` transfer in
`_do_copy` (lines 2753–2760). Port the same move-semantics for
`Copy`. Verify no goldens produce new double-free valgrind ERRORs.

---

## Per-emission-site checklist

Session flow: implement + test each site one at a time. Rebuild +
goldens after each.

- [ ] `emit_const` String literal → `emit_track_string`
- [ ] `emit_mir_call` String-returning user call → `emit_track_string`
- [ ] `emit_mir_call` `__mn_str_concat` / `__mn_str_from_int` →
      `emit_track_string`
- [ ] `emit_copy` String-typed → transfer slot via `_str_slots`
      self-hosted equivalent
- [ ] `emit_interp_concat` → `emit_track_string`
- [ ] `emit_list_init` / `emit_list_init_checked` → push to
      `list_owned`
- [ ] `emit_enum_payload` String payload → `emit_track_string`
- [ ] `emit_closure_create` → `emit_track_closure`
- [ ] `lower_call_by_name` entry → emit blanket Moves
- [ ] `collect_ret_ptrs` helper
- [ ] `emit_drop_glue_strings` revised to use tracking slots +
      escape compare
- [ ] `emit_drop_glue_boxed` revised with conservative skip-all-on-
      struct-return guard
- [ ] `declare_all_runtime` adds three free declarations

Target commits: one per checkpoint (~12 commits). Easy bisect if a
regression appears.

---

## Exit criteria — quick table

| Metric | v5.4.0 baseline | v5.4.1 target |
|---|---|---|
| Goldens | 54/66 | 54/66 (unchanged) |
| Valgrind ERRORS | 0 | 0 (unchanged) |
| ASan (no leak det.) | 55 CLEAN / 11 CRASH_NO_ASAN | same |
| ASan with leak det. on simple test | untested | **0 leaks** (new gate, narrow scope) |
| `__mn_str_free` in compiled output | absent | present in every non-trivial function |
| stage2.ll size | ~123k lines | +30–50% expected (document actual) |
| Fixed-point stage2 `llvm-as` | OK | OK |
| Own.1 Phase 2 row in PARITY_GAPS | "infrastructure landed, helpers dormant" | "end-to-end drop-glue functional on simple returns" |

---

## Release sequencing

If in-session estimate grows beyond 6 hours:

| Slot | Scope |
|---|---|
| **v5.4.1** | Strings only: tracking + escape detection + single test. List + boxed drop to v5.4.2 or v5.4.3. |
| v5.4.2 | Lists + boxed drop-glue + ASan leak-detection gate on full goldens. |
| v5.4.3 | Maps / Signals / Streams / Tensors (if user demand surfaces). |

Prefer the outcome where v5.4.1 closes Strings cleanly under leak
detection, even if List + boxed slip. String leaks are the most
common user pattern.

---

## What NOT to do

- **Do not port Python's full drop-glue family.** Maps / Signals /
  Streams / Tensors — out of scope for v5.4.1.
- **Do not enable global ASan leak detection.** v5.4.2.
- **Do not touch `emit_mir_return`'s wiring** — v5.4.0 already calls
  `emit_drop_glue` at every ret path. v5.4.1 only changes what
  `emit_drop_glue` does with populated lists.
- **Do not add a reassignment-time free in `emit_store`.** Shadow-
  slot architecture makes that unnecessary — each assignment
  produces a new tracking slot, old snapshots are preserved for
  drop-glue.
- **Do not bump v5 tag without explicit approval** — saved project
  rule. Tag + push after the user confirms.
