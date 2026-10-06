# v5.39.2 — SESSION_REPORT — Js.4.B.2: `from_json::<T>` runtime SEGV closeout

**Status:** Ready, not tagged.
**Date:** 2026-05-03.
**Scope:** Second of two release sessions dedicated to closing
**Js.4.B**. v5.39.1 closed the IR-emission shape mismatch (no-import
case); v5.39.2 closes the runtime SEGV when extracting struct fields
from a decoded JSON Object. After v5.39.2 ships, **Js.4.B is closed**
and v5.40.0 (Ai.\* — `ask` keyword, manifesto-arc kickoff) picks up
cleanly with the typed-output ergonomic intact.

---

## Headline

- **Strict 3-stage fixed point preserved by construction** at
  v5.39.1's 241,898 lines / 0 diff (36-release strict streak from
  v5.7.1). **Zero `mapanare/self/*.mn` source touches** — Phase 0
  verification established that `mapanare/self/emit_llvm.mn::
  emit_map_init` already had the correct `key_size`/`val_size`
  derivation from `key_ty`/`val_ty` regardless of pair count. The
  Python bug was a latent drift between Python and self-host that
  the self-host already had right.
- **Goldens 95/95** preserved.
- **Compiler edit footprint:** ~25 LOC Python (`mapanare/emit_llvm_text.py`)
  — far below PROMPT's 80-150 LOC budget.
- **Test additions:** 1 new pytest harness file + 6 new .mn test
  cases — the link-and-run infrastructure that should have existed
  since v5.36.0.
- **Falsifiability round-trip locked** as the test suite itself —
  one Edit-and-pytest cycle reproduces.
- Bumped `VERSION` 5.39.1 → 5.39.2, `CHANGELOG.md`, `CLAUDE.md`,
  `docs/SPEC.md` header.
- **Js.4.B arc CLOSED.**

## Aggregate state entering v5.39.3

- **0 HIGH** — Js.4.B fully closed.
- **1 MEDIUM:** macOS notarization (carry from v5.33.0 Nu.2).
- **~7 LOW:** added `to_json::<T>` nested-struct recursion as
  v5.39.3 candidate (split per Phase 1 bundle decision); rest
  unchanged from v5.39.1 carries.

---

## Phase 1 — diagnosis: hypothesis revised mid-release

PROMPT/PLAN's leading hypothesis: **`_is_self_ref` doesn't recurse
through MAP/LIST type args.** `JsonValue::Object(Map<String,
JsonValue>)` and `Array(List<JsonValue>)` should be marked boxed
at registration time so the proper boxed-payload extraction path
fires; the audit proposed adding recursion through `MIRType.
type_info.args` for `LIST` / `MAP` / `OPTION` / `RESULT` wrappers.

**Phase 1 instrumentation confirmed `boxed=set()` for JsonValue:**

```
[DIAG] reg_enum('JsonValue') variants=[...] boxed=set()
        [Array,0]  kind=LIST ti.args=['JsonValue']  is_self_ref=False
        [Object,0] kind=MAP  ti.args=['','JsonValue'] is_self_ref=False
```

But Phase 1 IR-side audit (working `match jv { Object(entries)
=> entries[key] }` path under `tests/stdlib/test_struct_json_
runtime.py`-style harness) showed both **construction and
extraction agree on the same unboxed `{ptr}` layout**:

```
; construction (decode_object_inner)
%ep = call ptr @malloc(i64 8)
%fp = getelementptr {ptr}, ptr %ep, i32 0, i32 0
store ptr %map_handle, ptr %fp           ; store Map handle at offset 0

; extraction (_lower_decode_to OR manual match)
%pr = extractvalue {i64, ptr} %enum, 1   ; payload ptr
%pf = getelementptr {ptr}, ptr %pr, i32 0, i32 0
%pv = load ptr, ptr %pf                  ; load Map handle from offset 0
```

These agree. So `_is_self_ref` non-recursion is a real-but-
unrelated observation, **not** the load-bearing root cause. The
audit's hypothesis was wrong about the SEGV mechanism (though
it correctly identified that `_is_self_ref` doesn't recurse —
it just doesn't matter for correctness here, only for the
choice between unboxed direct storage and boxed indirection).

**Side-by-side IR diff `decode_to`-emitted vs manual `match`:**
both paths produce *the same* extraction shape. Both SEGV at HEAD.
The audit's "manual match works" was a red herring — the v5.39.0
test shown at audit time had `entries` as a **dead binding** (no
use after the `Object(entries) => print("got Object")` arm), so
the optimizer eliminated the lookup entirely. Once `entries["x"]`
is actually live, both paths fail identically.

**GDB pinpoints SEGV not in `__mn_map_get` but right after:**

```
=> 0x555555590dea: mov (%rcx), %rax
   ...
rdi 0x7fffffffd328  rsi 0x7fffffffd328  rdx 0x...  rax 0x0
```

The PC is in main, two instructions past the `__mn_map_get` return.
`__mn_map_get` *returned NULL* — the load `mov (%rcx), %rax` is
the post-call `load {i64, ptr}, ptr %rt.54` from the IR, derefing
NULL.

So `__mn_map_get` ran cleanly; it just couldn't find the key.

**Why? Inspecting the Map struct at the call site:**

```
0x5555557ef310:   buckets=0x5555557ef360
                  len=1     cap=16
                  key_size=8   val_size=8   bucket_size=18
                  key_type=0    val_type=0
```

`key_size=8`, `val_size=8`, `key_type=0/INT`. But the user code
constructed it as `Map<String, JsonValue>`. **The Map was built
with the wrong sizes and key-type.** String keys are 16 bytes
(`{ptr, i64}`), JsonValues are 16 bytes (`{i64, ptr}` boxed
enum), key_type should be 1/STR. Initial `m["key"] = value`
inserts wrote 16 bytes into 18-byte buckets and used the INT
hash function on the raw bytes; hash collisions and bucket
corruption guarantee any subsequent lookup misses.

**Root cause:** `mapanare/emit_llvm_text.py::_do_map_init`
empty-literal branch:

```python
if i.pairs:
    ksz = _tsz(self._rty(i.key_type))
    vsz = _tsz(fvt)
    ktag = (1 if STRING else 2 if FLOAT else 0)
else:
    ksz, vsz, ktag = 8, 8, 0     # <-- hardcoded defaults, ignores i.key_type / i.val_type
```

When the literal has no initial pairs, the hardcoded defaults
override the declared types. `decode_object_inner`'s
`pon mut entries: Map<String, JsonValue> = #{}` was the load-
bearing instance, but **any** `Map<String, X> = #{}` or
`Map<Float, X> = #{}` was silently miscompiled.

## Phase 2 — fix

`mapanare/emit_llvm_text.py::_do_map_init` (~25 LOC change):
derive `ksz` / `ktag` from `i.key_type` and `vsz` from
`i.val_type` unconditionally. The pair-bearing branch keeps
its existing logic for `vsz` (uses the first pair's actual
emitted type, which can be more precise than the declared
type for inferred kinds).

Defensive companion fix in `_do_enum_init` (both inline and
boxed paths): when an enum payload is a `Map`, drain the
consumed value's name from `_map_vars` (mirrors the existing
`_list_vars.remove` pattern). Doesn't fire in the v5.39.2
repro — `decode_object_inner` ends with the JsonValue holding
the entries map, and the function-exit drop glue happens to not
emit a `__mn_map_free_deep` for the moved map under the current
flow analysis. But the asymmetry between `_list_vars` and
`_map_vars` removal was a latent footgun that would surface
the moment `_map_vars` got tracked through a wider class of
ops.

**Falsifiability round-trip:** reverted `_do_map_init` to its
pre-fix shape (hardcoded `(8, 8, 0)` empty branch). All 6
parametrized cases in `tests/stdlib/test_struct_json_runtime.py`
fail. Reapplied; all 6 pass. The round-trip is the test suite
itself — one `Edit`-and-pytest cycle.

## Phase 3 — self-host mirror N/A

**PROMPT/PLAN deviation (load-bearing).** PROMPT scoped a mirror
in `mapanare/self/emit_llvm.mn` budgeted at ~1-2h. Phase 0
verification at `mapanare/self/emit_llvm.mn:3106-3169::
emit_map_init`:

```mn
let mut key_size: String = "16"     // line 3125 — defaults to 16, not 8
let mut val_size: String = "16"     // line 3126
if key_ty.kind == TK_INT() { key_size = "8" }      // narrow to 8 only when known
if key_ty.kind == TK_FLOAT() { key_size = "8" }
if val_ty.kind == TK_INT() { val_size = "8" }
if val_ty.kind == TK_FLOAT() { val_size = "8" }
if val_ty.kind == TK_BOOL() { val_size = "8" }
if val_ty.kind == TK_STRUCT() { val_size = "64" }
if val_ty.kind == TK_ENUM() { val_size = "64" }
```

Self-host derives `key_size` / `val_size` / `key_tag` / `val_tag`
from the declared `key_ty` / `val_ty` regardless of pair count.
The Python bug was a latent drift; the self-host already had it
right. STRICT preserved trivially by construction; v5.39.2 makes
**zero** `mapanare/self/*.mn` source touches (mirrors v5.39.1's
posture for the same load-bearing-but-N/A reason on a different
function).

This shows up clean in `bash scripts/verify_fixed_point.sh`
post-bump: 241,898 / 0 diff, no STRICT regression.

## Phase 4 — link-and-run regression suite

**This is the test infrastructure that should have existed since
v5.36.0.** The pre-existing `tests/stdlib/test_struct_json.py`
(20 cases, v5.36.0 carry) is compile-only — it validates that
the IR text generates without errors but never links or runs.
That's exactly why the SEGV stayed latent for 4 releases
(v5.36.0 → v5.39.0).

`tests/stdlib/test_struct_json_runtime.py` mirrors the v5.34.0 /
v5.35.0 / v5.39.0 concatenation pattern: read
`stdlib/text/string_utils.mn` + `stdlib/encoding/json.mn`,
prepend to each `.mn` test main body, compile via the Python
LLVM emitter, link against `libmapanare_rt.a`, run, assert
`"PASSED"` (and no `"FAIL "`). 6 .mn test files under
`stdlib/encoding/json/tests/`:

| File                            | Cover                                                        |
|---------------------------------|--------------------------------------------------------------|
| `test_from_json_int.mn`         | `struct PInt { x: Int }` round-trip via `from_json::<PInt>`  |
| `test_from_json_string.mn`      | `struct PStr { name: String }`                               |
| `test_from_json_bool.mn`        | `struct PBool { active: Bool }`                              |
| `test_from_json_float.mn`       | `struct PFloat { ratio: Float }`                             |
| `test_from_json_compound.mn`    | mixed `{ name: String, age: Int }`                           |
| `test_to_from_roundtrip.mn`     | `to_json::<T>(struct) -> from_json::<T>(string) -> assert eq` |

All 6 GREEN at HEAD. v5.39.1's `test_struct_json_ir_shape.py` (4
cases) and `test_struct_json_layout.py` (2 cases) preserved
GREEN. Existing `test_struct_json.py` (20 compile-only cases)
preserved GREEN.

## Bundle-or-split decision: `to_json::<T>` nested-struct → split

Phase 1 ran the `to_json` nested-struct repro:

```mn
struct Inner { x: Int, y: String }
struct Wrap { name: String, inner: Inner }
fn main() {
    let w: Wrap = Wrap("ok", Inner(42, "hi"))
    print(to_json::<Wrap>(w))
}
```

Output post-v5.39.2-fix: `{"name": "ok", "inner": <?>}` — still
emits `<?>` placeholder for the inner struct field.

This is a **different code path** (`_emit_struct_to_json` in the
encoder, not `_do_map_init`). The fix would need to recurse into
struct-typed fields when emitting `to_json::<T>`. Bundling into
v5.39.2 would have inflated scope beyond the surgical Js.4.B.2
fix. **Split to v5.39.3.**

## Falsifiability anchor for v5.39.3+

Pre-fix repro (locked in v5.39.2 SESSION_REPORT):

1. `cat stdlib/text/string_utils.mn stdlib/encoding/json.mn` +
   user struct + `from_json::<T>(s)` call → SEGV at exit 139.
2. `gdb -batch -ex 'run' -ex 'bt' /tmp/jsdt`:
   ```
   Program received signal SIGSEGV, Segmentation fault.
   PC inside main, two instructions past __mn_map_get return.
   __mn_map_get returned NULL → caller load {i64, ptr} from NULL.
   ```
3. Map struct at SEGV site has `key_size=8, val_size=8,
   key_type=0/INT` instead of `key_size=16, val_size=16,
   key_type=1/STR` for `Map<String, JsonValue>`.

Post-fix:
- All 6 `test_struct_json_runtime.py` cases GREEN.
- `/tmp/jsdt.mn` repro prints `start / decoded ok / p ok` and
  exits 0.

## Closing

- Compiler edit: ~25 LOC Python, single file
  (`mapanare/emit_llvm_text.py`), surgical.
- STRICT preserved by construction at v5.39.1's 241,898 / 0.
- Goldens 95/95.
- Tests added: 6 new runtime cases (link-and-run, the test
  infrastructure that should have existed since v5.36.0).
  Falsifiability locked.
- CHANGELOG honest about the audit-hypothesis revision and
  the bundle/split decision.
- SPEC header re-synced to v5.39.2 cut.
- Deviation from PLAN (Phase 3 self-host mirror N/A) documented
  here and in CHANGELOG `### Changed`.
- v5.40.0 (`ask` keyword) Hard-prerequisite ("Js.4.B closed")
  satisfied. Manifesto-arc kickoff unblocked.

See `PLAN.md` and `PROMPT.md` for original scope and execution
prompt.
