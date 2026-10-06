# v5.39.2 — PLAN — Js.4.B.2: close the `from_json::<T>` runtime SEGV

> **Second of the v5.39.1 + v5.39.2 arc** (surfaced at v5.40.0
> Phase 0). v5.39.1 closes the IR-emission shape. v5.39.2 closes
> the runtime SEGV in `__mn_map_get` AND adds the link-and-run
> regression suite that should have existed since v5.36.0. After
> v5.39.2 closes cleanly, v5.40.0 (Ai.\* — `ask` keyword) picks
> up with the typed-output ergonomic intact.

## Scope

**Two-bug-class fix + test-infrastructure rebuild.** Bigger than
v5.39.1; ~80-150 LOC compiler edit + ~250 LOC test infra.

**Bug A — runtime SEGV.** `from_json::<P>(s)` with json imported
emits valid IR but SEGVs in `__mn_map_get` when extracting a
struct field. Repro at v5.39.0 HEAD (will reproduce post-v5.39.1
because v5.39.1 only closes the IR-shape side):

```mn
// /tmp/jsdt.mn — concat stdlib/text/string_utils.mn +
// stdlib/encoding/json.mn + the body below.
struct P { x: Int }
fn main() -> Int {
    print("start")
    let s: String = "{\"x\": 42}"
    let r: Result<JsonValue, JsonError> = decode(s)
    match r {
        Ok(jv) => {
            print("decoded ok")
            let dr: Result<P, JsonError> = decode_to::<P>(jv)
            match dr { Ok(p) => print("p ok"), Err(e) => print("p err") }
        },
        Err(e) => print("decode err")
    }
    return 0
}
```

GDB:

```
Program received signal SIGSEGV, Segmentation fault.
0x000055555559bc43 in __mn_map_get ()
#1  0x0000555555590f97 in main ()
```

SEGV at `map->key_type` access (`runtime/native/mapanare_core.c:2333`)
— Map pointer is invalid by the time it reaches `__mn_map_get`.

**Bug B — `_is_self_ref` MAP/LIST recursion.** `_reg_enum`
marks variant payload fields as `boxed` only if `_is_self_ref(enum_name,
field_type)` returns True. For `JsonValue::Object(Map<String,
JsonValue>)`, the check looks at the outer kind (`MAP`) and
doesn't recurse into the type parameters. `_is_self_ref` should
recursively check `args` for any `MAP`, `LIST`, `OPTION`,
`RESULT`, etc. wrapper. Confirmed via emitter instrumentation at
v5.39.0 HEAD: `boxed=set()` for JsonValue.

These two bugs are likely related — the wrong boxing decision at
registration time causes a downstream layout mismatch between
`decode()` constructing `Object` and `decode_to`'s `EnumPayload`
extracting it.

**Bonus — `to_json::<T>` nested struct.** Top-level struct fields
that are themselves struct-typed serialize as `<?>` instead of
recursing. Same family. Decision at Phase 0: bundle into v5.39.2
or split to v5.39.3. Default: bundle if Phase 1's diagnosis
shows shared root cause; split otherwise.

## Out of scope

- Grammar / parser / semantic changes.
- Any work that would land in v5.40.0 (the `ask` keyword,
  `stdlib/ai/ask.mn`, etc.).

## Phase plan

### Phase 0 — pre-flight (~30 min)

```bash
cat VERSION                               # expected: 5.39.1
make ci-gates 2>&1 | tail -5
bash scripts/verify_fixed_point.sh 2>&1 | tail -3
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1 2>&1 | tail -3
# Expected: 95/95 + STRICT (post-v5.39.1)
python3 -m pytest tests/stdlib/test_struct_json_ir_shape.py -v
# Expected: GREEN (v5.39.1's contribution)
```

Re-confirm the v5.39.0 SEGV repro reproduces post-v5.39.1 (only
the IR-shape side closed, the runtime SEGV remains).

### Phase 1 — diagnose root cause (~2-3h)

This is a bigger investigation than v5.39.1. Three parallel
threads:

**Thread 1 — `_is_self_ref` recursion.** Read
`mapanare/emit_llvm_text.py::_is_self_ref`. Trace what types
it considers self-referential. Add a recursive helper that
descends into `MIRType.type_info.args` looking for any TypeInfo
matching the outer enum name. Sketch:

```python
def _is_self_ref(self, enum_name: str, t: MIRType) -> bool:
    ti = t.type_info
    if ti.kind in (TypeKind.STRUCT, TypeKind.ENUM) and ti.name == enum_name:
        return True
    if ti.kind in (TypeKind.LIST, TypeKind.MAP, TypeKind.OPTION,
                   TypeKind.RESULT) and ti.args:
        for a in ti.args:
            if self._is_self_ref(enum_name, MIRType(type_info=a)):
                return True
    return False
```

Phase 1 deliverable: instrumented run showing `boxed={('Array', 0),
('Object', 0)}` for JsonValue after the fix.

**Thread 2 — `decode_to` vs. `match` path divergence.** Read
both lowerings side-by-side:

- Manual `match jv { Object(entries) => ... }` lowers via
  `lower_match` → emit_match → enum extraction in
  `mapanare/lower.py:lower_match`.
- `decode_to`'s call to `_decode_json_field` emits
  `EnumPayload(variant="Int", payload_idx=0)` directly.

Both should produce equivalent IR for an Int field extraction.
Capture the IR for both paths in side-by-side files. Diff. The
bug is the difference.

Hypothesis (to confirm): the alloca-sizing path treats the
`entries` value's MIR type (MAP) as opaque pointer, but the
extraction load reads more than 8 bytes (or the wrong offset).
Once `_is_self_ref` correctly marks Object as boxed, the proper
boxed-payload path runs and the load layout matches.

**Thread 3 — `decode()` construction symmetry.** Read
`stdlib/encoding/json.mn::decode_object_inner` and trace what IR
the emitter produces for `JsonValue::Object(map)` construction.
Does the constructor side write the layout that the extractor
side expects? If `_is_self_ref` was wrong at registration time,
the constructor was also using the wrong layout.

### Phase 2 — apply fix (~2h)

Most likely fix is Thread 1 alone — fixing `_is_self_ref` to
recurse means JsonValue::Object and ::Array variants get marked
boxed; both decode() construction and decode_to extraction
flow through the proper boxed-payload path; layouts agree.

Apply in `mapanare/emit_llvm_text.py`. Verify locally:

```bash
python3 -m mapanare emit-llvm /tmp/jsdt.mn -o /tmp/jsdt.ll
clang /tmp/jsdt.ll runtime/native/libmapanare_rt.a -lm -lpthread -ldl -o /tmp/jsdt
/tmp/jsdt
# Expected: prints "start", "decoded ok", "p ok"
```

If the fix isn't sufficient, escalate to Thread 2 (lowering-side
fix) — possibly `_lower_decode_to` needs to emit additional
load-through ops, or `_decode_json_field` needs different lowering
for List/Map fields.

### Phase 3 — self-host mirror (~1-2h)

Apply equivalent change in `mapanare/self/emit_llvm.mn` (this
release likely needs the emitter side, not just lower.mn). Strict
3-stage rebuild; expect a NEAR diff first run, debug to STRICT.
Plan budget: 2-3 verify cycles.

### Phase 4 — link-and-run regression suite (~2h)

Build the test infrastructure that should have existed since
v5.36.0. New file `tests/stdlib/test_struct_json_runtime.py`
following the v5.34/v5.35/v5.39.0 concat pattern:

```python
"""v5.39.2 Js.4.B.2 — link-and-run regression for from_json::<T>.

Mirrors the v5.34.0 Dt.* / v5.35.0 Sq.* / v5.39.0 Cr.*
concatenation harness exactly: read stdlib/text/string_utils.mn
+ stdlib/encoding/json.mn, prepend to each .mn test main body,
compile via Python LLVM emitter, link against
libmapanare_rt.a, run, assert "PASSED" in stdout.

Tests under stdlib/encoding/json/tests/:
- test_from_json_int.mn       — struct { x: Int }
- test_from_json_string.mn    — struct { name: String }
- test_from_json_bool.mn      — struct { active: Bool }
- test_from_json_float.mn     — struct { ratio: Float }
- test_from_json_compound.mn  — struct { name: String, age: Int }
- test_to_from_roundtrip.mn   — to_json -> from_json -> assert eq
"""
```

Each test prints "PASSED" or "FAILED <case>" and asserts the
former. ~250 LOC across 6 .mn files + ~100 LOC harness.

If `to_json::<T>` nested-struct fix bundles in this release, add
`test_nested_struct.mn`; else mark XFAIL with link to v5.39.3.

### Phase 5 — bump + closeout (~30 min)

```bash
python3 scripts/bump_version.py 5.39.2
$EDITOR CHANGELOG.md       # ### Fixed: Js.4.B.2 + closes v5.39.1+v5.39.2 arc
$EDITOR CLAUDE.md          # release-notes entry; arc-closeout note
$EDITOR docs/roadmap/v5/v5.39.2/SESSION_REPORT.md
$EDITOR docs/SPEC.md       # Hd-class header re-sync
python3 scripts/check_doc_freshness.py
python3 scripts/build_stage1.py
bash scripts/verify_fixed_point.sh        # STRICT — load-bearing
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1 2>&1 | tail -3
make ci-gates && make lint
python3 -m pytest tests/stdlib/test_struct_json_runtime.py -v
# Sanitizer pass on stage1 + stage2 (compiler edits = UB-risk tier):
make build-rt CFLAGS="-fsanitize=address -g"
python3 scripts/build_stage1.py
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1 2>&1 | tail -3
make build-rt   # reset
```

## Closeout checklist

- [ ] `_is_self_ref` recurses through MAP / LIST / OPTION /
      RESULT type args
- [ ] `boxed` set for JsonValue contains `("Array", 0)`,
      `("Object", 0)` post-fix (instrumented verify)
- [ ] `from_json::<P>(s)` round-trips for at least 5 struct
      shapes via link-and-run
- [ ] `tests/stdlib/test_struct_json_runtime.py` GREEN
- [ ] Mirror in `mapanare/self/emit_llvm.mn` (likely) and/or
      `mapanare/self/lower.mn`
- [ ] STRICT 3-stage fixed point preserved
- [ ] Goldens 95/95
- [ ] CHANGELOG honest: arc-closeout note pointing at v5.40.0
      unblocking
- [ ] CLAUDE.md release-notes entry: "Js.4.B closed; v5.40.0
      Ai.\* manifesto-arc kickoff unblocked"
- [ ] gitnexus_detect_changes matches expected
- [ ] `npx gitnexus analyze --embeddings` after commit
- [ ] SESSION_REPORT documents falsifiability round-trip for
      every fix line item

## Notes for v5.40.0 PROMPT post-v5.39.2

- Re-run the Phase 0 gate from v5.40.0 PROMPT (the round-trip
  test). Should pass cleanly post-v5.39.2.
- Update v5.40.0 PROMPT.md "Hard prerequisite" line to confirm
  Js.4.B closed.
- v5.40.0 compiler-edit budget unchanged at ~50 LOC for the
  grammar / lower / semantic glue.
- The Path-A v5.39.1 + v5.39.2 arc preserves the manifesto-level
  ergonomic Path B would have downgraded.

## Risk register

- **STRICT regression on first verify after self-host mirror.**
  Likely. Plan 2-3 rebuild cycles. The v5.31.0 lesson applies:
  rebuild stage1 between bump and verify.
- **`to_json::<T>` nested-struct fix expands scope.** If it
  bundles cleanly into the same `_is_self_ref` fix, ship together;
  if not, defer to v5.39.3 — don't bloat the release.
- **Multiple compiler edits across both Python + self-host.**
  This is exactly the shape that produced NEAR diffs at v5.31.0
  and v5.36.0. Budget extra time.
- **Test infrastructure being net-new.** The link-and-run harness
  itself could have bugs that mask the fix. Run a falsifiability
  check: revert the emitter fix → tests must fail with the
  expected SEGV → reapply → tests pass.
