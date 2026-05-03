# v5.40.0 — Pre-Phase Audit (Ai.\* — `ask` as a language primitive)

**Status: HARD STOP at Phase 0.** v5.40.0 cannot ship as designed.
Js.4.B is open and significantly worse than the v5.36.0
SESSION_REPORT documented. v5.40.0 Ai.4 (runtime adapter) rides on
`from_json::<T>`; without it, the runtime path has no mechanism.

The PROMPT explicitly anticipates this:

> **Hard prerequisite:** v5.39.0 shipped (Cr.\* crypto closeout)
> AND v5.36.0 Js.4.B fixed. If Js.4.B is still open at Phase 0,
> **STOP** and ship v5.36.x first.

## Gate results

| Gate                                    | Result | Notes                                     |
|-----------------------------------------|--------|-------------------------------------------|
| Baseline VERSION = 5.39.0               | ✅     | Pre-bump state; v5.39.0 ready/not-tagged  |
| `__struct_meta::<T>()` exists           | ✅     | `mapanare/lower.py:2278` + `semantic.py:1010` |
| `extract_with_schema` exists            | ✅     | `stdlib/ai/llm.mn:1987`                   |
| `ExtractError` exists                   | ✅     | `stdlib/ai/llm.mn:1930`                   |
| `to_json::<T>` flat structs             | ✅     | Single-level structs serialize correctly. |
| `to_json::<T>` nested structs           | ❌     | Nested struct fields print as `<?>` — `_emit_struct_to_json` doesn't recurse into struct-typed fields. |
| `from_json::<T>` no-import              | ❌     | IR emission fails: `extractvalue ... 1` yields `ptr` but consumer is `store i64`. JsonValue not registered when user code doesn't import json. |
| `from_json::<T>` with json imported     | ❌     | IR emits, links — but **runtime SEGV in `__mn_map_get`** when extracting a struct field from the decoded Object. The Map pointer in `JsonValue::Object` payload extraction is wrong. |
| Plain `decode(s)` (no decode_to)        | ✅     | `Result<JsonValue, JsonError>` with `match Object(entries)` works correctly. |

## Js.4.B repro at v5.39.0 HEAD

`/tmp/jsdt.mn` (concatenates `stdlib/text/string_utils.mn` +
`stdlib/encoding/json.mn` + main):

```mn
struct P { x: Int }
fn main() -> Int {
    print("start")
    let s: String = "{\"x\": 42}"
    let r: Result<JsonValue, JsonError> = decode(s)
    match r {
        Ok(jv) => {
            print("decoded ok")
            let dr: Result<P, JsonError> = decode_to::<P>(jv)
            match dr {
                Ok(p) => { print("p ok") },
                Err(e) => { print("p err") }
            }
        },
        Err(e) => { print("decode err") }
    }
    return 0
}
```

GDB:

```
Program received signal SIGSEGV, Segmentation fault.
0x000055555559bc43 in __mn_map_get ()
#0  0x000055555559bc43 in __mn_map_get ()
#1  0x0000555555590f97 in main ()
```

SEGVs *before* `print("start")` runs — first executable instruction
in main reaches `__mn_map_get` and dies on `map->key_type` because
the Map pointer is invalid.

## Why the bug is deeper than v5.36.0 SESSION_REPORT claimed

The v5.36.0 SESSION_REPORT said: "from_json::<T> builds successfully
but SEGVs at runtime in field extraction." This is technically
accurate but masks the structure of the failure:

1. **Two distinct failure modes** depending on whether json is
   imported:
   - **No-import:** invalid IR (`extractvalue` shape mismatch).
     `_do_enum_payload`'s Result/Option fallback runs because
     `JsonValue` isn't in `self._enums`. The fallback emits
     `extractvalue ... 1` (ptr) and `_put`s as `i64`. Caller
     fails IR validation.
   - **With-import:** valid IR, runtime SEGV at `__mn_map_get`.
     Goes through the proper boxed-enum path. `JsonValue::Object`'s
     payload Map gets extracted, but the resulting `ptr` value is
     wrong by the time it reaches the runtime call.

2. **`_is_self_ref` doesn't detect the recursion.**
   `JsonValue::Object` has payload `Map<String, JsonValue>`. The
   `_is_self_ref(JsonValue, Map<String, JsonValue>)` check looks at
   the outer kind (MAP) and doesn't recurse into the type
   parameters. So `("Object", 0)` is NOT marked boxed. Same problem
   for `Array(List<JsonValue>)`. The whole boxed-payload path
   (line 5178-5183) never fires for these variants.

3. **`TypeKind.MAP` lowers to `PTR` (opaque pointer)** at
   `_rty:988`. So the Object payload struct is `{ptr}` (one
   pointer field). When `decode()` constructs `Object(map)`, it
   stores the Map pointer in this `{ptr}`. When `decode_to`
   extracts, it loads that pointer and passes to `__mn_map_get`.
   On the surface this looks correct.

4. **The actual bug needs IR-level investigation that exceeds
   one-session scope.** Hypothesis: the alloca for the extracted
   `entries` value gets sized as `ptr` (8 bytes), but somewhere a
   load reads more than 8 bytes from it (treating it as a Map
   struct directly), or the wrong slot of the JsonValue payload
   struct gets read. Confirming requires either: emitter
   instrumentation matching MIR-value to alloca address, or
   side-by-side IR diff between the working
   `match jv { Object(entries) => ... }` path (which works) and
   the failing `decode_to`-emitted EnumPayload path. Both code
   paths emit the same MIR instruction (`EnumPayload`); the
   manual-`match` form goes through a different lowering arm in
   the emitter.

## Why this isn't a v5.39.1 hotfix

A v5.39.1 hotfix as scoped (~30-50 LOC compiler edit) does not
fit. The diagnosis exceeded the diagnosis budget; the actual fix
likely requires:

- Audit of `_is_self_ref` to recurse into MAP/LIST type args.
- Reconcile the `match`-vs-`EnumPayload` emitter divergence.
- Possibly a `_decode_json_field` rework to load through the
  payload pointer with the right type for each variant kind.
- Mirror the fix in `mapanare/self/lower.mn` AND
  `mapanare/self/emit_llvm.mn` (load-bearing for STRICT).
- Audit `to_json::<T>` nested-struct emission (related; same
  family).
- New link-and-run regression suite (current
  `tests/stdlib/test_struct_json.py` is compile-only — exactly
  why this stayed latent for 4 releases).
- Round-trip 5+ struct shapes through link-and-run (the gate
  Js.4.B was supposed to close).

Conservative estimate: **2-3 release sessions.** Multiple compiler
edits across both Python bootstrap and self-host. STRICT regressions
likely on first attempt. Not a one-session hotfix.

## Recommendation

**Three paths, in order of preference:**

### Path A — defer v5.40.0; ship v5.39.1 as scoped Js.4.B fix arc

Ship a multi-session **v5.39.1 + v5.39.2** arc dedicated to closing
Js.4.B properly:

- **v5.39.1**: fix `_decode_json_field` + `_do_enum_payload` for
  the no-import case (invalid IR → valid IR). Runtime can still
  SEGV — this gets the IR shape right.
- **v5.39.2**: close the runtime SEGV. Audit `_is_self_ref` for
  MAP/LIST recursion. Audit decode/decode_to layout symmetry.
  Add the link-and-run regression suite.
- **v5.39.3** (if needed): close `to_json::<T>` nested-struct
  recursion.
- Each release: mirror Python edits to self-host
  (`mapanare/self/lower.mn`, `mapanare/self/emit_llvm.mn`).
  STRICT preserved at each step.

Then v5.40.0 picks back up cleanly.

### Path B — ship v5.40.0 with `ask_text` only; defer `ask_typed` to v5.40.1

Ship the keyword + grammar + provider wiring + cache, with
`ask_typed::<T>` explicitly deferred. `ask_text(prompt) ->
Result<String, AskError>` returns the LLM's raw string unchanged
— no `from_json::<T>` involved. Manifesto-level ergonomic for
typed output is **explicitly downgraded** in CHANGELOG.

This is a degraded v5.40.0 — the keyword *is* shippable and useful
without typed output, but the typed-output ergonomic was the
manifesto sell. Document the deviation honestly.

### Path C — bundle the Js.4.B fix into v5.40.0

Adds the v5.39.1 + v5.39.2 scope on top of the ~50 LOC Ai.\*
compiler-edit budget. ~100-150 LOC of compiler edits in one
release with grammar / lower / semantic changes interleaving with
runtime serde fixes. **STRICT will fight this**, possibly across
multiple verify cycles. Not recommended.

## What was confirmed working

- `__struct_meta::<T>()` emits a JSON schema string at compile
  time. Works for the simple shapes tested.
- `to_json::<T>` for flat structs.
- `extract_with_schema` retry-on-malformed-JSON loop in
  `stdlib/ai/llm.mn`.
- `decode(s) -> Result<JsonValue, JsonError>` end-to-end
  including `match jv { Object(entries) => ... }` extraction.

## Diagnosis artifacts

- `/tmp/jsbug2.mn` — minimal repro of the working
  `match jv { Object(entries) => ... }` path (PASSES).
- `/tmp/jsdt.mn` — minimal repro of the failing
  `decode_to::<P>(jv)` path (SEGV in `__mn_map_get`).
- `/tmp/diag.py` — emitter instrumentation showing JsonValue's
  `boxed` set is empty at `_reg_enum` time (the Object/Array
  variants should be marked boxed-by-recursion but aren't).

## Decision required from lead

Three paths above. **Path A recommended.** Write back which to take
and v5.39.1 PROMPT can pick up the diagnosis artifacts above as
its starting point.
