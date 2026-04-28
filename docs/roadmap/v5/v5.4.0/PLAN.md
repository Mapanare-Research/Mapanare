# Mapanare v5.4.0 — "Own.1 Phase 2: Self-Hosted Drop-Glue + Move Tracking"

> **Close Sh.2. Drive native goldens 54/66 → 65/66.** The v5.1.3 Phase 1
> workaround neutralized two specific sites (`register_struct`,
> `register_enum`) with the Cb.7 zero-after-push pattern. Phase 2 lands
> the real infrastructure: drop-glue emission in the self-hosted emitter,
> a `Move` MIR instruction, per-function ownership slots in `EmitState`,
> and move-on-call propagation through the lowerer.

**Status:** PLANNED
**Breaking:** No (ABI unchanged, grammar unchanged, stdlib unchanged)
**Prerequisite:** v5.3.3 shipped (SPEC + docs polish)
**Estimated work:** 3–5 sessions (~8–12 hours total)
**Owner docket:** Own.1 Phase 2 (deferred from v5.1.3; Viper v4.99.0 →
v5.3.0, 28 panels of carry-forward)

---

## Why this release exists

### The 54/66 ceiling

`python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1`
holds at 54/66 since v5.0.4. The 12-test gap decomposes per
`docs/roadmap/v4/v4.126.0/GOLDEN_TRIAGE.md`:

| Bucket | Tests | Root cause | Fix vehicle |
|---|---:|---|---|
| **Sh.2** emit_mir_call NULL-deref | **11** | Self-hosted emitter has no String/list ownership tracking; `find_function` returns a copied `FnEntry` whose `ret_type: String` is a stale pointer after the first call is emitted | **v5.4.0 (this release)** |
| Sh.4 async missing | 5 | `block_on` / `await` not in self-hosted `semantic.mn`; no coroutine lowering in self-hosted `lower.mn` | v5.5.0 |
| Sh.6 tensor missing | 5 | `Tensor` / `Float` types not registered; nested-array literal grammar not in self-hosted parser | v5.6.0 |
| Sh.7 closure-typed | 1 | Closure-capture parameters not resolved in self-hosted `semantic.mn` / `lower.mn` | v5.7.0 |
| B bootstrap-also-fails | 1 | `51_match_guards_and_or` or-pattern binding-set check is wrong in Python bootstrap too | v5.7.0 (orthogonal) |

**v5.4.0 closes the biggest single bucket: 11 of 12.**

### Why this has been deferred 28 panels

Viper has flagged ownership/drop-glue at every panel since v4.99.0.
Every release chose to defer it for the same reason: **the self-hosted
emitter has no drop-glue at all**, so fixing "move tracking" with no
drop-glue to skip is dead code. You need both halves at once, and the
drop-glue piece is the larger one (~200–400 LOC in `emit_llvm.mn`).

The v5.1.3 Phase 1 shipped the Cb.7 workaround at two specific sites
(`register_struct`, `register_enum`) — that handled the acute case
without requiring the full infrastructure. v5.1.3 DESIGN.md §5
documented the Phase 2 shape; this release implements it.

### Why the 11 Sh.2 tests crash today

From `GOLDEN_TRIAGE.md` root-cause analysis:

> Two reproducers triggered the same `emit_mir_call+0x236a4` crash:
> 1. `rec(n - 1) + rec(n - 2)` — two recursive calls in one expression
> 2. `let a: Int = make_int(1); let b: Int = make_int(2)` — two
>    let-bindings whose values are calls to the same function
>
> Counter-examples that do NOT crash:
> - `add(x) + add(x)` (two calls to a non-recursive helper)
> - `print(make_str(1)); print(make_str(2))` (in print statements, not
>   let bindings)

The crash happens inside `mnc-stage1` itself while it is compiling a
user `.mn` file. The `FnEntry` struct registered for a function has a
`ret_type: String` field; when `find_function` is called the second
time, the first call's emission path freed the backing heap for that
String, and the second `is_byref_type_st(s, fe.ret_type)` walks freed
memory → `__mn_str_starts_with+0x37` crash.

Python's bootstrap applies `_do_call` blanket-move at line 3882, which
shields it from this family. The self-hosted emitter, compiled by the
Python bootstrap, inherits the same safety for the code Python *writes*
for it — but the self-hosted emitter's own `emit_llvm.mn` has patterns
that generate MIR where Python's `_do_call` tracking sees the ownership
transfer from a different angle than at `_move_resource`'s six sites.
The residual crashes are the patterns Python's `_move_resource` doesn't
cover but `_do_call` blanket-move would.

---

## Scope

### What ships

**Four coordinated pieces. Each is a phase.**

#### 5.4.0a — `Move` instruction in MIR (both emitters)

`mapanare/mir.py` — add `Move` dataclass after `Phi` (line 754):

```python
@dataclass
class Move(Instruction):
    value: MIRValue  # the local being moved
    # No dest — Move is a marker, not a producer
```

`mapanare/self/mir.mn` — add variant to `Instruction` enum at line 227:

```mapanare
Move(Value),
```

Python's `_do_call` blanket-move stays; the new `Move` lets the
lowerer be explicit where it already implicitly was, and lets the
self-hosted emitter recognize the transfer without needing to mirror
`_do_call`'s full heuristic.

#### 5.4.0b — Self-hosted emitter ownership slots

`mapanare/self/emit_llvm.mn::EmitState` — add 4 per-function tracking
lists after line 70:

```mapanare
// Own.1 Phase 2 (v5.4.0): per-function ownership tracking.
// Reset at emit_fn entry. Read by emit_drop_glue before ret.
str_owned: List<String>,       // local var names currently owning a String
list_owned: List<String>,      // local var names currently owning a List
boxed_owned: List<String>,     // local var names currently owning a boxed struct/enum
moved_locals: List<String>,    // locals transferred via Move — skip in drop-glue
```

Registry mirrors: `make_entry("EmitState", [...])` call site at line 94
gets 4 new field names; `register_internal_struct` call at line 139
gets the same list.

`register_struct` (`lower.mn`) already has the v4.143.0 Reg.1 gate — it
will flag the mismatch immediately if updates are inconsistent.

#### 5.4.0c — Drop-glue emission in `emit_llvm.mn`

The biggest piece. Port the Python `_emit_drop_glue` family into
Mapanare, scoped to the four resource kinds that matter for current
goldens (String, List, boxed struct/enum, closure env). Maps, signals,
streams, and tensors can defer — none of the 11 failing goldens
exercise their drop-glue paths, and adding them mid-release doubles the
surface area.

New functions in `emit_llvm.mn`:

| Function | LOC est. | Mirrors |
|---|---:|---|
| `emit_drop_glue(s, ret_val, ret_ty)` | ~40 | `_emit_drop_glue` @ emit_llvm_text.py:1576 |
| `collect_ret_ptrs(s, ret_val, ret_ty)` | ~60 | `_emit_drop_glue_collect_ret_ptrs` @ 1628 |
| `emit_drop_glue_strings(s, ret_str_ptrs, ret_ptr_fields)` | ~40 | `_emit_drop_glue_strings` @ 1703 |
| `emit_drop_glue_lists(s, ret_list_ptrs, ret_ptr_fields)` | ~40 | `_emit_drop_glue_lists` @ 1842 |
| `emit_drop_glue_boxed(s, ret_ptr_fields)` | ~40 | `_emit_drop_glue_boxed` @ 1785 |
| `emit_drop_glue_closures(s, ret_env, ret_ptr_fields)` | ~40 | `_emit_drop_glue_closures` @ 1744 |

**Total: ~260 LOC new Mapanare in `emit_llvm.mn`.**

Call site: `emit_mir_return` at `emit_llvm.mn:3259` — insert
`emit_drop_glue` call before every `ret` emission, consulting
`st.moved_locals` to skip transferred values.

#### 5.4.0d — Lower move-on-call in `lower.mn`

When the lowerer emits a `Call` with arguments that are owning locals
(Strings, Lists, boxed structs, closures), emit `Move(arg)` before the
`Call`. This matches Python `_do_call`'s blanket-move semantics — every
non-primitive argument to every user function call is treated as
transferred unless the callee is known-pure.

Sites in `lower.mn`:
- `lower_call_by_name` (line ~2197) — main call path
- `lower_method_call` (if resource-bearing receiver is transferred)

**Scoping rule:** only emit `Move` for locals; don't move field-gets or
intermediate computation. Field-get results are tracked separately via
Python's `_str_slots` in the bootstrap emitter — leaving them out of
Move keeps parity simple.

### What does NOT ship

- **Maps / signals / streams / tensors drop-glue.** No golden requires
  them; adding them doubles review surface. v5.4.1+ patch release.
- **`@takes_ownership` user-facing annotation.** Not needed —
  move-on-call is blanket like Python. If specific callees need
  opt-out later, a `@keeps_ownership` negative annotation is simpler
  than positive `@takes_ownership`.
- **Borrow checker.** That is v6.0 territory per DESIGN.md §8.
- **The other 12th golden** (bootstrap-also-fails 51_match_guards_and_or).
  Orthogonal bug; v5.7.0 handles it alongside Sh.7.
- **Stage2 LICM (Li.1).** Deferred per CLOSEOUT_ARC.md.

---

## Exit criteria

The release is ready to ship when:

1. **`python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1`
   → ≥ 65 / 66 passing.** Pre-release baseline is 54/66. Target is 65
   (all 11 Sh.2 tests close; 12th is the bootstrap-also-fails out of
   scope). Minimum acceptable is 60/66 — if 5+ Sh.2 tests still crash,
   debug before shipping.
2. **Strict 3-stage fixed-point holds** (`bash
   scripts/verify_fixed_point.sh --keep` → stage2.ll == stage3.ll
   byte-identical except the known VERSION placeholder). The drop-glue
   additions change what `mnc-stage1` emits; stage2 and stage3 are both
   produced by the new binary so they must agree.
3. **`llvm-as` accepts stage2.ll without error.** The new drop-glue
   emitter writes valid IR — PHI placement, free-call signatures,
   extractvalue indices all have to match runtime ABI.
4. **Valgrind 0 new ERRORS** across 66 goldens (baseline 0/62/4 at
   v5.3.1 — the 4 WARNINGS_ONLY Ge.1 residuals are out of scope).
5. **ASan 0 new ASAN_ERROR** across 66 goldens (baseline 55/0/11;
   the 11 CRASH_NO_ASAN were the Sh.2 goldens crashing before ASan
   could initialize — target: those same 11 now reach ASan init and
   report 0 errors).
6. **Non-bootstrap pytest 0 failures** (modulo VERSION-mismatch tests
   fixed by the mandatory `build-rt` + `build_stage1.py` rebuild).
7. **Bootstrap pytest failure set byte-identical** — new drop-glue
   in self-hosted emitter changes stage1 binary size but not behavior
   for code that was already working.
8. **`make lint` clean.** No new ruff/black/mypy findings.
9. **`PARITY_GAPS.md` updated** — Own.1 moves from "Phase 1 CLOSED,
   Phase 2 v5.1.4+" to "Phase 1 + Phase 2 CLOSED v5.4.0". Sh.2 moves
   from open to Historical.

---

## Design decisions locked in

### D1 — Move instruction vs inference

**Decision: `Move` instruction in MIR, not dataflow inference.**

Rationale (from v5.1.3 DESIGN.md §3): annotation-style is simpler,
explicit, and mirrors what the Python bootstrap already does via
`_do_call` blanket-move. Inference requires escape analysis the
self-hosted compiler doesn't have and would duplicate LLVM's. The
`Move` instruction is a 1-variant addition; `moved_locals` is a single
list consulted once per return.

### D2 — Blanket move-on-call, not `@takes_ownership`

**Decision: every non-primitive argument to every user call is moved.**

Rationale: matches Python's `_do_call`. `@takes_ownership` would require
parser work (new attribute syntax), semantic work (callee metadata
lookup), and lowerer work (conditional emission). The blanket rule
produces the same safety and is 3 lines in `lower_call_by_name`.

If a future need arises for non-moving calls, add `@keeps_ownership`
as a negative annotation — smaller surface.

### D3 — Which resources get drop-glue in v5.4.0

**Decision: String, List, boxed struct/enum, closure env only.**

Maps, signals, streams, tensors don't have failing goldens that exercise
them. Adding them mid-release doubles review surface without closing
tests. v5.4.1 or v5.4.2 patch release can add them once v5.4.0 is
stable. The "4 kinds" choice mirrors what the 11 Sh.2 goldens actually
use (all are basic types + structs + closures + lists).

### D4 — Drop-glue lives in `emit_llvm.mn`, not a new module

**Decision: add to existing `emit_llvm.mn`.**

Rationale: `scripts/concat_self.sh` MODULES list is already mature;
adding a new module (e.g. `drop_glue.mn`) requires wiring in 3 places.
The 260 LOC fits alongside the existing ~3,200 LOC of `emit_llvm.mn`
without breaking the single-file cognitive load. Future refactor to a
separate module is a mechanical move.

### D5 — Python bootstrap changes

**Decision: add `Move` handler to Python emitter; otherwise unchanged.**

`_do_call` stays. The Python emitter's new job is to recognize the
`Move` instruction when compiling `emit_llvm.mn` for mnc-stage1. In
the Python emitter, `Move(val)` calls `_move_resource(val.name)` —
exactly the existing function. ~5 LOC added.

### D6 — Tests

`tests/native/test_sh2_close.py` — new pytest file. For each of the 11
Sh.2 goldens, add a test that:
1. Compiles the golden via mnc-stage1
2. Runs the resulting IR through `llvm-as`
3. (if `lli` available) runs the IR and compares output with reference

No existing golden needs to change. The harness already tracks 66; the
delta is that 11 more pass.

---

## Risks

### R1 — Drop-glue emission produces invalid IR

**Risk level: HIGH.** 260 LOC of new IR-writing code. Easy to get
PHI placement, extractvalue indices, or free-call argument types wrong.

**Mitigation:** run `llvm-as` on every stage2.ll attempt — existing
`scripts/verify_fixed_point.sh --keep` does this. Port the Python
helpers as closely as possible, not from scratch. Each drop-glue helper
gets a dedicated unit test using a hand-constructed MIR module.

### R2 — Move-on-call regresses a currently-passing golden

**Risk level: MEDIUM.** Blanket move is aggressive. A pattern that
currently works by accident (no-op drop glue + aliased local) could
break if we add a Move that the emitter then frees.

**Mitigation:** run the full 66-golden suite on every `build_stage1.py`
iteration. Any drop from 54 (before) triggers investigation before
continuing.

### R3 — Fixed-point breaks

**Risk level: MEDIUM.** New drop-glue emission changes what
`mnc-stage1` writes for every function it compiles (including
`emit_llvm.mn` itself). Stage2 will differ substantially from stage1;
the question is stage2 == stage3.

**Mitigation:** the pattern that worked at v5.0.6 (strict 3-stage at
`0c00ad07...` hash) is that both stages are produced by the same
binary. As long as `mnc-stage1` is deterministic (hash the binary
before each build), stage2 == stage3 will hold.

### R4 — New valgrind/ASan findings

**Risk level: MEDIUM.** Drop-glue that frees too eagerly is the
classic UAF source. The Python emitter had several iterations
(v4.101.0, v4.131.0, v4.132.0) to get `_emit_drop_glue_collect_ret_ptrs`
right.

**Mitigation:** run the full `valgrind_all_goldens.sh` and
`run_asan_goldens.sh` sweeps before commit. Baseline at v5.3.1 is
valgrind 0/62/4 and ASan 55/0/11. Target post-v5.4.0 is 11/55/0 (the
11 Sh.2 goldens now reach ASan init) and 0 new valgrind ERRORS on the
originally-passing 54.

### R5 — `EmitState` struct registry drift

**Risk level: LOW.** Reg.1 gate (v4.143.0) already catches this.
Adding 4 fields to `EmitState` requires updating 3 places in
`emit_llvm.mn`. The gate runs in CI.

**Mitigation:** run `python3 scripts/check_struct_registry.py` locally
before commit. Re-run after every `EmitState` edit.

---

## Release sequencing (v5.5.x arc)

v5.4.0 is the base landing. If in-session estimate grows beyond 12
hours, split:

| Slot | Scope |
|---|---|
| **v5.4.0** | `Move` instruction (both MIRs), `EmitState` slots, String drop-glue only |
| **v5.4.1** | List + boxed drop-glue (closes remaining Sh.2 tests if v5.4.0 left some) |
| **v5.4.2** | Closure env drop-glue + move-on-call through method calls |
| **v5.4.3** | Maps / signals / streams / tensors drop-glue (optional; not blocking Sh.2) |

If v5.4.0 closes all 11 Sh.2 tests in one session, v5.4.1 becomes
"expand drop-glue to the remaining 4 resource kinds" rather than "finish
Sh.2." Prefer that outcome.

---

## Per-reviewer expected impact

| Reviewer | v5.4.0 target | v5.4.0 expected lift | v5.4.0 target |
|---|---:|---|---:|
| Rattler | 9.5–9.6 | +0.1 (goldens 54 → 65) | 9.6–9.7 |
| **Viper** | 9.7 | **+0.3** (Own.1 Phase 2 closes her 28-panel carry-forward) | **9.8–9.9** |
| Anaconda | 9.3–9.5 | +0.05 (tests pass more broadly) | 9.35–9.55 |
| Cobra | 9.1–9.3 | +0.1 (self-hosted parity narrows) | 9.2–9.4 |
| Coral | 9.5–9.6 | 0 | 9.5–9.6 |
| Boa | 9.5–9.6 | +0.05 (README parity numbers bump) | 9.55–9.65 |
| Mamba | 9.6–9.7 | +0.05 (stable Sh.2 close) | 9.65–9.75 |
| **Aggregate** | **9.45–9.55** | — | **9.6–9.7** |

Viper is the primary beneficiary. Own.1 has been her consistent ceiling
argument for 28 panels. Closing Phase 2 removes the general
"no-borrow-checker" complaint's specific anchor — the language still
has no user-visible borrow checker, but the compiler's internal
infrastructure now matches what Python emits, which closes the
parity-based argument. The general argument stands until v6.0.

---

## What NOT to do

- **Do not add `@takes_ownership` user syntax.** Blanket move-on-call
  is simpler and Python already does it. Parser work is out of scope.
- **Do not port all 8 Python drop-glue helpers.** Only 4 map to failing
  goldens; the other 4 (maps/signals/streams/tensors) are v5.4.1+.
- **Do not attempt a borrow checker.** v6.0 scope.
- **Do not disable the inliner or LICM** to work around fixed-point
  issues. Those have their own release slots.
- **Do not skip the sanitizer HARD GATE.** Drop-glue is the #1 UAF
  source. Any new ERROR/ASan finding is an unconditional rollback per
  PROMPT_TEMPLATE.md UB-risk tier.
- **Do not touch `mapanare/mir.py` or `mapanare/self/mir.mn` beyond
  adding `Move`.** No field renames, no enum reordering (breaks
  reg-struct gate).
