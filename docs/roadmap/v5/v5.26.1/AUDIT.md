# v5.26.1 — AUDIT — Eu.1..Eu.4 root-cause + falsifiability

Per-Eu\* Phase 0 audit. Each section answers the five PROMPT
questions: (a) which exact emit/lower site, (b) what the
canonical IR shape should be, (c) what the lowerer/emitter
produces instead, (d) the proposed minimal fix, (e) the
validation command + falsifiability round-trip.

---

## Eu.1 — `emit_unwrap` Result Ok-payload extraction

### (a) Sites

- Python: `mapanare/emit_llvm_text.py::_do_unwrap` (line ~5229).
- Self-host: `mapanare/self/emit_llvm.mn::emit_unwrap` (line ~3694).

Single MIR `Unwrap` instruction emit site:
`mapanare/lower.py::_lower_error_prop` line 3701 and
`mapanare/self/lower.mn::lower_error_prop` line 3225 — both emit
`Unwrap` only on the `?`-operator success path. No other callers.

### (b) Canonical IR shape

For `Result<Int, String>` represented as
`{i1, {i64, {ptr, i64}}}` and unwrap dest typed as `Int = i64`:

```llvm
%uw_inner = extractvalue {i1, {i64, {ptr, i64}}} %t1, 1
%uw       = extractvalue {i64, {ptr, i64}}       %uw_inner, 0
; %uw : i64 — the Ok payload
```

### (c) What was emitted instead

```llvm
%t3 = extractvalue {i1, {i64, {ptr, i64}}} %t1, 1
; %t3 : {i64, {ptr, i64}} — the inner aggregate, not the Ok payload
store i64 %t3, ptr %v4.addr  ; <-- LLVM rejects: type mismatch
```

`emit_unwrap` did a single extractvalue at index 1 — correct for
Option (which uses the universal-erasure `{i1, ptr}` representation
where the ptr is loaded), wrong for Result.

### (d) Minimal fix

For `TK_RESULT` subjects, do TWO `extractvalue` ops (field 1 of
outer → inner aggregate; field 0 of inner → Ok payload). Mirrored
in Python and self-host. Option's existing path unchanged.

### (e) Validation + falsifiability

```bash
./mapanare/self/mnc-stage1 emit-llvm tests/golden/47_try_operator.mn 2>err > 47.ll
clang 47.ll runtime/native/libmapanare_rt.a -lm -lpthread -ldl -o 47
./47    # expects: "50\nfailed\n"
```

Falsifiability — revert the new TK_RESULT branch in
`emit_llvm_text.py::_do_unwrap`:
- Resurfaces the same single-extractvalue IR shape.
- clang rejects with the same error at line 235.
Re-apply: PASS again.

---

## Eu.2 — Result-literal type chain mismatch

### (a) Site

Self-host `mapanare/self/lower.mn::lower_call` arms for
`fn_name == "Ok"` (line ~2259) and `fn_name == "Err"` (line ~2276).
The downstream emitter `emit_wrap_ok` / `emit_wrap_err` is correct
when given a fully-typed `dest.ty` — the bug is at the lowerer
level.

### (b) Canonical IR shape

For `Ok(42)` constructed with no enclosing Result return type
(e.g., as an argument at a call site `classify(Ok(42))` where
`classify` accepts `Result<Int, String>`), the wrap_ok output
should be `{i1, {i64, {ptr, i64}}}` — matching the canonical
`Result<Int, String>` layout. The `emit_wrap_ok` branch
`if len(dest.ty.args) >= 2` handles this correctly *if* the
lowerer provides typed args.

### (c) What was emitted instead

`mapanare/self/lower.mn::lower_call` only used `current_fn.return_type`
when it was already `Result`. Otherwise it fell through to
`mir_result()` — empty args. `emit_wrap_ok` then computed:

- `res_ty = resolve_mir_type(dest.ty)` → `{i1, {ptr, ptr}}` (fallback for empty args).
- `inner_ty = "{ " + val_ty + ", " + llvm_ptr() + " }"` → `{i64, ptr}`.

Three disagreeing types in one chain:

```llvm
%t11.tag = insertvalue {i1, {ptr, ptr}} undef, i1 1, 0       ; outer
%t11.inner = insertvalue { i64, ptr } undef, i64 %t10, 0     ; inner
%t11 = insertvalue {i1, {ptr, ptr}} %t11.tag, { i64, ptr } %t11.inner, 1
;                                                  ^^^^^^^^^^^ insertvalue rejects
```

### (d) Minimal fix

Self-host `lower_call` Ok/Err branches now default missing args
mirroring `mapanare/lower.py:2398`:
- `Ok(arg)` with no Result context → `Result<arg.ty, String>`.
- `Err(arg)` with no Result context → `Result<Int, arg.ty>`.

The existing emit_wrap_ok / emit_wrap_err code then handles the
fully-typed dest correctly.

### (e) Validation + falsifiability

```bash
./mapanare/self/mnc-stage1 emit-llvm tests/golden/48_match_nested_exhaustive.mn 2>err > 48.ll
clang 48.ll runtime/native/libmapanare_rt.a -lm -lpthread -ldl -o 48
./48    # expects: "ok: 5\nerr: zero\nok: 42\nerr: fail\n"
```

Falsifiability — revert the default-args branches:
- Standalone `Ok(42)` literal at call site re-emits `{i1, {ptr, ptr}}`
  outer with `{i64, ptr}` inner; clang rejects same insertvalue
  type disagreement.
Re-apply: PASS again.

---

## Eu.3 — `match` on primitive subject

### (a) Sites

- Self-host `mapanare/self/lower.mn::lower_match` line ~4485 (the
  unconditional `EnumTag` emit).
- Self-host `mapanare/self/lower.mn::bind_ident_pattern` line ~4711
  (alloca name collision under cascade dispatch).
- Python `mapanare/lower.py::_lower_match` already uses Maranget
  decision tree → no Python-side fix needed.

### (b) Canonical IR shape

Two alternatives are both valid LLVM:

1. **Sequential cascade** (chosen for v5.26.1):
   ```llvm
   br label %match_arm0          ; jump to first arm
   match_arm0:
     ; arm 0 entry: literal check or guard, jump to body or next arm
   match_arm1:
     ; arm 1 entry: ditto
   ```
2. **Direct switch on primitive value** (would also work for
   pure-literal-arms cases):
   ```llvm
   switch i64 %n, label %default [
     i64 0, label %arm_zero
     ...
   ]
   ```

For golden 49's mix of literal and ident-with-guard arms, the
cascade is structurally simpler — alts that are guards re-check
their own conditions; alts that are literals re-check
`subject == LIT` at entry.

### (c) What was emitted instead

```llvm
%n_val0 = load i64, ptr %n.addr
%tag1 = extractvalue i64 %n_val0, 0     ; <-- LLVM rejects (i64 not aggregate)
switch i64 %tag1, label %match_arm5 [
    i64 0, label %match_arm2             ; only the literal-0 arm
]
```

The `EnumTag` emit was unconditional even for primitive subjects.
Even if the extractvalue had succeeded, the switch had only the
literal arm; ident-with-guard arms 0/2/3 set `default_lbl` in turn
and were overwritten by the wildcard arm 4 — the switch dispatched
guard arms to the wildcard.

### (d) Minimal fix

1. `lower_match` detects `subj_kind ∈ {TK_INT, TK_BOOL, TK_STRING}`
   and bypasses the switch — emits unconditional jump to `arm[0]`.
2. The arm-body loop adds an implicit `subject == LIT` re-check
   at literal-pattern arms (so cascade fall-through can't
   accidentally execute a literal arm body for a non-matching
   subject).
3. `bind_ident_pattern` uniquifies its alloca name with
   `tmp_counter` (mirrors `bind_one_pattern_field`'s pattern).
   Without this, multiple ident-pattern arms binding `x` collide
   on `%x.addr` because the cascade reaches every arm (vs. switch
   dispatch where only one arm was actually reached at a time).

### (e) Validation + falsifiability

```bash
./mapanare/self/mnc-stage1 emit-llvm tests/golden/49_match_guards.mn 2>err > 49.ll
clang 49.ll runtime/native/libmapanare_rt.a -lm -lpthread -ldl -o 49
./49    # expects: "negative\nzero\nsmall\nlarge\n"
```

Falsifiability:
- Revert the primitive-subject branch in `lower_match` →
  `extractvalue i64` resurfaces.
- Revert the `bind_ident_pattern` uniquify → "multiple definition
  of local value named '%x.addr'" appears.
Re-apply both: PASS.

---

## Eu.4 — `match` or-pattern + guards duplicate switch cases

### (a) Sites

- Self-host `mapanare/self/lower.mn::build_match_arms` line ~4413
  (case duplication).
- Self-host `mapanare/self/lower.mn::lower_match` arm-body loop
  (or-pattern alt entry-time disambiguation).

### (b) Canonical IR shape

For `Some(0) | None | Some(x) if guard ...`:

```llvm
switch i64 %tag, label %wild_arm [
    i64 1, label %arm0       ; Some — first arm with this tag wins
    i64 0, label %arm0       ; None — first arm with this tag wins
]
arm0:
  ; or-pattern entry: which alt fired?
  switch i64 %ortag, label %arm1 [
      i64 1, label %check_some_payload  ; Some → check payload == 0
      i64 0, label %arm0_body            ; None → direct match
  ]
check_some_payload:
  %p = extractvalue ..., 1
  %eq = icmp eq i64 %p, 0
  br i1 %eq, label %arm0_body, label %arm1
arm0_body:
  ; arm 0 actual body
arm1:
  ; arm 1 (Some(x) if guard) — bind, eval guard, fall through on miss
```

### (c) What was emitted instead

```llvm
switch i64 %tag1, label %match_arm5 [
    i64 1, label %match_arm1   ; Some from arm 0's or-pattern
    i64 1, label %match_arm2   ; Some from arm 1
    i64 1, label %match_arm3   ; Some from arm 2
    i64 1, label %match_arm4   ; Some from arm 3 — DUPLICATE
]
```

Four arms with `Some(...)` pattern → four `(Some, label)` entries
in `cases`. LLVM rejects duplicates. Even setting that aside, the
or-pattern alt `None` was parsed as `IdentPat("None")` not
`ConstructorPat`, so `is_enum_variant("None")` returned false
(None isn't user-registered) → the alt fell into the `ident`
branch which set `default_lbl` instead of pushing a switch case.

### (d) Minimal fix

1. **Dedup**: `build_match_arms` tracks `seen_tags: List<String>`
   and only pushes a switch entry the first time each tag is
   seen. Default label is set once (first wildcard or
   ident-non-enum wins) — mirrors the discipline that the
   wildcard arm should win over earlier ident arms.
2. **Recognize built-in variants**: new helper
   `is_builtin_variant_name(n)` recognises `None`/`Some`/`Ok`/`Err`
   as variants when they appear as `IdentPat`. The parser doesn't
   wrap these in `ConstructorPat`. Used both in `build_match_arms`
   ident branch and in the new or-pattern entry-switch logic.
3. **Or-pattern entry disambiguation**: at arm-body entry, if the
   pattern is `or` AND any alt is a constructor-with-literal-arg,
   emit a per-alt entry switch with cases:
     - Constructor alt with no payload → direct match → body run.
     - Constructor alt with literal arg → payload-check block →
       branch (body run / next arm).
     - `IdentPat` alt that's a built-in variant or registered
       variant → direct match → body run.
     - default → next arm (or merge if last).
   Then continue arm body in the body-run block (existing bind +
   guard + body emission).

### (e) Validation + falsifiability

```bash
./mapanare/self/mnc-stage1 emit-llvm tests/golden/51_match_guards_and_or.mn 2>err > 51.ll
clang 51.ll runtime/native/libmapanare_rt.a -lm -lpthread -ldl -o 51
./51    # expects: "zero or absent\nzero or absent\nsmall positive\nlarge positive\nnegative\n"
```

Falsifiability:
- Revert dedup logic → resurfaces "duplicate case value in
  switch" link error.
- Revert or-pattern entry-switch logic → `Some(5)` enters arm 0's
  `"zero or absent"` body (wrong output); `None` falls through
  to arm 2's body (wrong output).
Re-apply both: PASS.

---

## Cross-cutting

### Strict 3-stage fixed point — preserved

`stage2.ll == stage3.ll` at 241,842 lines / 0 diff. 22-release
strict streak. Line delta vs v5.26.0: +1,849 lines (270 LOC of
new self-host code × ~7-line IR amplification).

### `make ci-gates` — clean

`make lint` passes; mypy + ruff + black all clean on changed
files.

### Bb.\* — no seed refresh required

`bash scripts/build_from_seed.sh` succeeds against existing
v5.10.0 seed. None of the four fixes change C-runtime call shapes.

### Test harness

`tests/llvm/test_async_link.py` — 10/10 PASS (was 6 PASS + 4 XFAIL
at v5.26.0 HEAD). The four `pytest.xfail(reason)` short-circuits
were removed from `test_deferred_link_failures`. Reason fields
rewritten from "v5.26.1: <bug class>" to "v5.26.1 <Eu.X>: closed —
<one-line summary>" to document the closure rather than the bug.

### Out-of-scope (held)

- `scripts/test_native.py` link-cycle integration — v5.27.0+.
- General decision-tree match lowering rewrite — v6.0+.
- Result/Option representation refactor — v6.0+.
