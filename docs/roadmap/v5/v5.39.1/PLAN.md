# v5.39.1 — PLAN — Js.4.B.1: fix `from_json::<T>` IR-emission shape

> **Surfaced from v5.40.0 Phase 0 audit
> (`docs/roadmap/v5/v5.40.0/PRE_PHASE_AUDIT.md`).** v5.39.1 is the
> first of two release sessions dedicated to closing Js.4.B (the
> v5.36.0 deferred `from_json::<T>` runtime SEGV — turned out to be
> two distinct bugs, not one). v5.39.1 closes the **IR-emission
> shape mismatch**; v5.39.2 closes the **runtime SEGV in
> `__mn_map_get`**. Then v5.40.0 (Ai.\* — `ask` keyword) picks up
> cleanly.

## Scope

**One bug class. Surgical fix. ~30-50 LOC compiler edit.** Strict
fixed point preserved. Goldens 95/95 preserved.

**Bug:** when user code calls `from_json::<T>(s)` without
importing `stdlib/encoding/json`, the emitter's `_do_enum_payload`
falls into the Result/Option fallback (line 5187 in
`mapanare/emit_llvm_text.py`) because `JsonValue` isn't
registered in `self._enums`. The fallback emits
`extractvalue {i64, ptr} %enum, 1` which yields a `ptr` (the
boxed payload pointer), then `_put`s the value into the value
table tagged with the dest type (e.g. `i64` for an Int field).
The next consumer reads with the wrong type → IR validation fails
at link.

Repro:

```mn
struct P { x: Int }
fn main() {
    let s: String = "{\"x\": 42}"
    let r: Result<P, JsonError> = from_json::<P>(s)
    match r { Ok(p2) => print("ok"), Err(e) => print("err") }
}
```

```
$ python3 -m mapanare emit-llvm /tmp/serde_simple.mn -o /tmp/serde_simple.ll
$ clang /tmp/serde_simple.ll runtime/native/libmapanare_rt.a -lpthread -ldl -lm -o /tmp/serde_simple
/tmp/serde_simple.ll:142:13: error: '%pl.48' defined with type 'ptr' but expected 'i64'
  store i64 %pl.48, ptr %t13.a.49
```

## Out of scope

- The runtime SEGV in `__mn_map_get` when json IS imported. That's
  v5.39.2.
- `to_json::<T>` nested-struct recursion (`<?>` for nested fields).
  Same family, separate fix. v5.39.2 or v5.39.3.
- Grammar / parser / semantic changes. v5.39.1 is emitter-only.
- Any `mapanare/self/*.mn` source touches beyond mirroring the
  `lower.mn` / `emit_llvm.mn` fix (load-bearing for STRICT).
- `tests/stdlib/test_struct_json.py` rewrite to link-and-run.
  Add a focused link-and-run case for the v5.39.1 fix; the full
  rewrite happens in v5.39.2 alongside the runtime fix.

## Phase plan

### Phase 0 — repro (~30 min)

```bash
cd /mnt/c/Users/Juan/Documents/GitHub/Mapanare
cat VERSION                               # expected: 5.39.0 or 5.39.1
git status --short
make ci-gates 2>&1 | tail -5
bash scripts/verify_fixed_point.sh 2>&1 | tail -3
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1 2>&1 | tail -3
# Expected: 95/95 + STRICT
```

Reproduce the IR-emission failure with `/tmp/serde_simple.mn`
above. Capture the failing IR section to the SESSION_REPORT for
falsifiability.

### Phase 1 — diagnose (~1h)

Read:

- `mapanare/emit_llvm_text.py:5131-5210` — `_do_enum_payload`.
  Note the two paths: `if en in self._enums` (boxed-payload path)
  vs. `else` (Result/Option fallback). Confirm with
  instrumentation that `JsonValue not in self._enums` for
  no-import user code.
- `mapanare/lower.py:2767` — `_lower_decode_to`. Note that it
  emits `EnumPayload(variant="Object")` etc. without registering
  JsonValue in `self._module.enums`.

Decide between two fix strategies:

**Strategy A — register JsonValue + JsonError in
`_lower_decode_to`.** When the user's compilation unit doesn't
already define them, inject the canonical layout:

```python
if "JsonValue" not in self._module.enums:
    self._module.enums["JsonValue"] = [
        ("Null", []),
        ("Bool", [TypeInfo(kind=TypeKind.BOOL)]),
        ("Int", [TypeInfo(kind=TypeKind.INT)]),
        ("Float", [TypeInfo(kind=TypeKind.FLOAT)]),
        ("Str", [TypeInfo(kind=TypeKind.STRING)]),
        ("Array", [TypeInfo(kind=TypeKind.LIST,
                             args=[TypeInfo(kind=TypeKind.ENUM, name="JsonValue")])]),
        ("Object", [TypeInfo(kind=TypeKind.MAP,
                              args=[TypeInfo(kind=TypeKind.STRING),
                                    TypeInfo(kind=TypeKind.ENUM, name="JsonValue")])]),
    ]
if "JsonError" not in self._module.structs:
    self._module.structs["JsonError"] = [
        ("message", TypeInfo(kind=TypeKind.STRING)),
        ("line",    TypeInfo(kind=TypeKind.INT)),
        ("col",     TypeInfo(kind=TypeKind.INT)),
    ]
```

Pros: routes through the proper boxed-enum path; downstream
extraction is correct. Cons: hardcoded layout in lower.py creates
coupling that could drift from `stdlib/encoding/json.mn`.
Mitigation: add a unit test that loads json.mn, parses it, and
asserts the lower.py-injected layout matches structurally.

**Strategy B — fix the emitter fallback.** In
`_do_enum_payload`'s `else` branch (line 5187+), when the
variant is not Result's `Ok`/`Err` or Option's `Some`/`None`,
treat the extracted `extractvalue ... 1` result as a payload
pointer and load through it with the dest's type:

```python
else:
    # Other variants: assume boxed-payload form (extractvalue
    # gives ptr to payload struct). Load through the pointer
    # with the dest's expected type.
    raw = self._f("pl")
    self._L(f"{raw} = extractvalue {et} {ev}, 1")
    dt = self._rty(i.dest.ty)
    if dt == VOID:
        dt = PTR
    if dt == PTR:
        self._put(i.dest, raw, PTR)
    else:
        # Dereference: payload struct's field 0 has dest type.
        fp = self._f("pf")
        self._L(f"{fp} = getelementptr inbounds {{{dt}}}, ptr {raw}, i32 0, i32 0")
        loaded = self._f("plv")
        self._L(f"{loaded} = load {dt}, ptr {fp}")
        self._put(i.dest, loaded, dt)
```

Pros: smaller diff; works for any unregistered enum, not just
JsonValue. Cons: assumes single-field-payload variant; multi-arg
variants would need richer logic. For Js.4.B's no-import case
(scope here), this is sufficient because `_decode_json_field`
calls `EnumPayload` once per field with single-arg variant
selectors (`"Int"`, `"Bool"`, `"Str"`, `"Float"`).

**Recommendation: Strategy A.** Single point of fix; keeps the
emitter fallback's contract narrow (Result/Option only). The
runtime SEGV in v5.39.2 will need the Strategy A path anyway
because `_is_self_ref` recursion only matters once JsonValue is
properly registered.

### Phase 2 — Python bootstrap fix (~1h)

Apply Strategy A in `mapanare/lower.py`. Place the registration
helper near `_lower_decode_to` and `_lower_from_json` so it runs
on first call. Idempotent — guard with `if "JsonValue" not in
self._module.enums`.

Verify locally:

```bash
python3 -m mapanare emit-llvm /tmp/serde_simple.mn -o /tmp/serde_simple.ll
clang /tmp/serde_simple.ll runtime/native/libmapanare_rt.a -lpthread -ldl -lm -o /tmp/serde_simple
echo "exit=$? (no-import case must build at IR level)"
```

Expected: build succeeds. Runtime may still SEGV — that's v5.39.2.
For v5.39.1, "build succeeds" is the gate.

### Phase 3 — self-host mirror (~1h, load-bearing for STRICT)

Apply equivalent change in `mapanare/self/lower.mn`. The Python
file structure is the gold copy; the self-host mirror has to
match shape-for-shape.

Rebuild stage1 + verify:

```bash
python3 scripts/build_stage1.py
bash scripts/verify_fixed_point.sh
# Expected: STRICT preserved. If NEAR diff, check v5.31.0 lesson
# (rebuild stage1 between bump and verify so VERSION doesn't ghost
# in cached IR metadata). v5.39.1 isn't bumping yet at this phase.
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1 2>&1 | tail -3
# Expected: 95/95
```

### Phase 4 — focused link-and-run regression (~1h)

Add ONE link-and-run test for the v5.39.1 IR-shape fix. Don't try
to lock the runtime — that's v5.39.2.

`tests/stdlib/test_struct_json_ir_shape.py`:

```python
"""v5.39.1 Js.4.B.1 — from_json::<T> IR-shape regression.

Locks the IR-emission fix: from_json::<T>(s) compiles to valid IR
even when the user does not import stdlib/encoding/json (the
JsonValue / JsonError types are auto-registered by the lowerer).
Compile-and-link only — runtime correctness is gated separately
in v5.39.2."""

# Two cases:
# 1. from_json::<P> for `struct P { x: Int }` — no json import.
#    Assert IR emits AND links cleanly (the v5.39.0-HEAD failure
#    was at link, "%pl.48 defined with type ptr but expected i64").
# 2. Same but for `struct Q { name: String }` — confirms String
#    field also extracts cleanly through the new path.
```

### Phase 5 — bump + closeout (~30 min)

```bash
python3 scripts/bump_version.py 5.39.1
$EDITOR CHANGELOG.md       # ### Fixed: Js.4.B.1
$EDITOR CLAUDE.md          # release-notes entry; "first of v5.39.1 + v5.39.2 arc"
$EDITOR docs/roadmap/v5/v5.39.1/SESSION_REPORT.md
$EDITOR docs/SPEC.md       # Hd-class header re-sync to v5.39.1 cut
python3 scripts/check_doc_freshness.py
python3 scripts/build_stage1.py
bash scripts/verify_fixed_point.sh        # STRICT
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1 2>&1 | tail -3
make ci-gates && make lint
python3 -m pytest tests/stdlib/test_struct_json_ir_shape.py -v
```

## Closeout checklist

- [ ] `_lower_from_json` / `_lower_decode_to` register JsonValue +
      JsonError in `self._module.enums` / `self._module.structs`
      when missing
- [ ] Mirror in `mapanare/self/lower.mn`
- [ ] Strict 3-stage fixed point preserved
- [ ] Goldens 95/95
- [ ] `tests/stdlib/test_struct_json_ir_shape.py` GREEN
- [ ] CHANGELOG `### Fixed` entry honest about v5.39.1 + v5.39.2
      arc framing — runtime SEGV still open
- [ ] CLAUDE.md release-notes entry calls out the v5.40.0
      Phase-0-driven scope discovery
- [ ] gitnexus_detect_changes matches expected
- [ ] `npx gitnexus analyze --embeddings` after commit
- [ ] SESSION_REPORT documents the falsifiability round-trip
      (revert fix → reproduce IR error → reapply → green)

## Notes for v5.39.2 PROMPT

- v5.39.1 closes the IR-emission shape. Runtime SEGV in
  `__mn_map_get` remains.
- v5.39.2 picks up:
  1. Audit `_is_self_ref` for MAP/LIST type-arg recursion.
  2. Reconcile `_do_enum_payload`-via-`decode_to` path with
     `match`-via-pattern-bind path (the latter works at HEAD;
     the former SEGVs).
  3. Add the **link-and-run** regression suite (5+ struct
     shapes) — close the test gap that hid Js.4.B for 4 releases.
  4. `to_json::<T>` nested-struct recursion (related; either
     bundle here or split to v5.39.3).
- v5.39.2 may need `mapanare/self/emit_llvm.mn` edits too
  (depending on which side the fix lands). Plan extra time for
  STRICT recovery.
