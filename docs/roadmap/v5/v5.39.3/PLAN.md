# v5.39.3 — PLAN — `to_json::<T>` nested-struct recursion

> Split-from-v5.39.2 follow-on. v5.39.2 closed the runtime SEGV in
> `from_json::<T>` (Js.4.B.2) but explicitly held back the
> `to_json::<T>` nested-struct fix because it lives in a different
> code path and bundling would have inflated v5.39.2's scope. This
> release closes that hole. After v5.39.3 ships, the typed-serde
> surface (`to_json::<T>` ↔ `from_json::<T>`) round-trips cleanly
> for nested struct shapes — the manifesto-arc ergonomic v5.40.0
> Ai.\* will exercise via `ask_typed::<T>`.

## Scope

**One bug, one code path, one fix.** Smaller than v5.39.2; ~30-50
LOC compiler edit + ~30 LOC test infra (one new `.mn` test case
appended to v5.39.2's harness).

**Bug.** `to_json::<Wrap>(w)` for a struct with a struct-typed
field emits the field as `<?>` instead of recursing into the
inner struct. Repro at v5.39.2 HEAD:

```mn
struct Inner { x: Int, y: String }
struct Wrap { name: String, inner: Inner }
fn main() {
    let w: Wrap = Wrap("ok", Inner(42, "hi"))
    print(to_json::<Wrap>(w))
}
```

Actual:   `{"name": "ok", "inner": <?>}`
Expected: `{"name": "ok", "inner": {"x": 42, "y": "hi"}}`

**Root cause.** `mapanare/lower.py:2681::_encode_field_to_json`
has explicit handlers for `STRING` / `INT` / `FLOAT` / `BOOL` /
`OPTION` (the latter recurses on the inner type) but no branch
for `STRUCT`. Fallback at line 2762 emits `Call(fn_name="str",
args=[field_val])` — `str()` of a struct prints the placeholder
`<?>` (see `mapanare/emit_llvm_text.py:3465`).

Sibling gaps for the same family: `LIST`, `MAP`, `ENUM` (user-
defined enums, not `Option`) also fall through to the `str()`
placeholder. Phase 1 decides whether to bundle these or hold for
v5.39.4 — default is **structs first** (the manifesto-arc
load-bearing case), bundle the others if the recursion shape is
trivially reusable (it is for LIST; less so for MAP/ENUM).

## Out of scope

- Grammar / parser / semantic changes.
- `from_json::<T>` for nested struct fields (separate bug; will
  surface once v5.39.3 lands and the round-trip test exercises
  it). Hold for v5.39.4 if needed.
- Self-host mirror — likely N/A. The Js.4 typed-serde surface
  is Python-bootstrap-only at HEAD (verified at v5.39.1 Phase 0:
  `grep -rn "from_json\|decode_to\|encode_struct\|to_json"
  mapanare/self/` → 0 matches). v5.39.3's edit lives in
  `_encode_field_to_json` — same code-path family. Phase 0
  re-verifies; if 0 matches, mirror is structurally N/A and
  STRICT preserved trivially (mirrors v5.39.1 + v5.39.2 posture).

## Phase plan

### Phase 0 — pre-flight (~15 min)

```bash
cat VERSION                               # expected: 5.39.2
make ci-gates 2>&1 | tail -3
bash scripts/verify_fixed_point.sh 2>&1 | tail -3
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1 2>&1 | tail -3
# Expected: STRICT 241,898/0 + 95/95
python3 -m pytest tests/stdlib/test_struct_json_runtime.py \
                  tests/stdlib/test_struct_json_ir_shape.py \
                  tests/stdlib/test_struct_json_layout.py \
                  tests/stdlib/test_struct_json.py
# Expected: 25 passed, 1 xfailed (v5.39.2 carry)

# Confirm the repro at v5.39.2 HEAD
cat > /tmp/tojson_nested.mn <<'EOF'
struct Inner { x: Int, y: String }
struct Wrap { name: String, inner: Inner }
fn main() {
    let w: Wrap = Wrap("ok", Inner(42, "hi"))
    print(to_json::<Wrap>(w))
}
EOF
python3 -m mapanare emit-llvm /tmp/tojson_nested.mn -o /tmp/tojson_nested.ll
clang /tmp/tojson_nested.ll runtime/native/libmapanare_rt.a \
      -lm -lpthread -ldl -o /tmp/tojson_nested
/tmp/tojson_nested
# Expected pre-fix: {"name": "ok", "inner": <?>}

grep -rn "from_json\|decode_to\|encode_struct\|to_json" mapanare/self/
# Expected: 0 matches → self-host mirror N/A
```

### Phase 1 — diagnose + decide bundle scope (~30 min)

Read `mapanare/lower.py:2681-2765::_encode_field_to_json`. Confirm
the missing kinds: STRUCT, LIST, MAP, ENUM. The OPTION branch
(line 2729+) is the right shape to mirror — it extracts the inner
value and recurses on the inner type.

**Bundle decision matrix:**

| Kind   | Recursion shape          | Phase 1 estimate    |
|--------|--------------------------|----------------------|
| STRUCT | Mirror `_lower_encode_struct`'s field-loop | 25-30 LOC, load-bearing |
| LIST   | `[` + items joined with `, ` + `]`         | 15-20 LOC, additive |
| MAP    | `{` + `"key": val` joined + `}`            | 25-30 LOC, additive |
| ENUM   | `"VariantName"` or `{"VariantName": payload}` | 30-40 LOC, requires variant introspection |

**Default:** STRUCT only in v5.39.3. Bundle LIST if recursion
helper is easy to share (likely is). Hold MAP and ENUM for
v5.39.4 — those have invariant questions (key encoding for
non-string-keyed maps; tagged-union JSON shape for enums) that
deserve their own session.

If Phase 1 surfaces unexpected complexity in STRUCT (e.g.,
`_lower_encode_struct` requires CallExpr machinery that isn't
trivially refactorable), STRUCT-only ships and the rest defer.

### Phase 2 — apply fix (~1h)

**Refactor target:** extract a shared helper

```python
def _emit_struct_json_body(self, struct_val: Value, struct_name: str) -> Value:
    """Emit MIR that produces a JSON `{...}` string for struct_val.
    Shared between _lower_encode_struct (top-level entry) and
    _encode_field_to_json (recursion from a struct-typed field)."""
```

Both `_lower_encode_struct` and the new `TypeKind.STRUCT` branch
in `_encode_field_to_json` call it. Avoids duplication; preserves
the existing `_lower_encode_struct` external API (still takes
`CallExpr` and unpacks `type_args[0]`).

In `_encode_field_to_json`, add:

```python
if kind == TypeKind.STRUCT:
    struct_name = ftype.type_info.name
    return self._emit_struct_json_body(field_val, struct_name)
```

If LIST bundles in Phase 1's decision: add a similar branch that
emits `"[" + items.map(encode).join(", ") + "]"` — needs an MIR
loop construct over the list. Reference `_lower_encode_struct`'s
linear `for i, (fname, ftype) in enumerate(fields)` — the runtime
loop shape will need a `while i < len(xs)` because runtime list
length is dynamic, not compile-time.

Verify locally:

```bash
python3 -m mapanare emit-llvm /tmp/tojson_nested.mn -o /tmp/tojson_nested.ll
clang /tmp/tojson_nested.ll runtime/native/libmapanare_rt.a \
      -lm -lpthread -ldl -o /tmp/tojson_nested
/tmp/tojson_nested
# Expected post-fix: {"name": "ok", "inner": {"x": 42, "y": "hi"}}
```

### Phase 3 — self-host mirror (likely N/A, ~5 min verify)

Re-verify Phase 0's grep result. If 0 matches, mirror is
structurally N/A; STRICT preserved trivially (zero
`mapanare/self/*.mn` source touches). Run
`bash scripts/verify_fixed_point.sh` post-bump as the proof.

If matches DO exist (unlikely), apply equivalent change in
`mapanare/self/lower.mn::encode_field_to_json` (or whichever
self-host name maps). Plan 1-2 verify cycles per the
v5.31.0 / v5.36.0 lesson.

### Phase 4 — extend regression suite (~30 min)

Append to v5.39.2's harness — single new `.mn` test case under
`stdlib/encoding/json/tests/`:

```mn
// stdlib/encoding/json/tests/test_to_json_nested_struct.mn
struct Inner { x: Int, y: String }
struct Wrap { name: String, inner: Inner }

fn main() -> Int {
    pon w: Wrap = Wrap("ok", Inner(42, "hi"))
    pon encoded: String = to_json::<Wrap>(w)
    si encoded.contains("<?>") {
        print("FAIL test_to_json_nested_struct: still emits <?> placeholder")
    } sino si encoded.contains("\"x\": 42") && encoded.contains("\"y\": \"hi\"") {
        print("PASSED test_to_json_nested_struct")
    } sino {
        print("FAIL test_to_json_nested_struct: unexpected output")
    }
    return 0
}
```

Add `"test_to_json_nested_struct.mn"` to `TEST_FILES` in
`tests/stdlib/test_struct_json_runtime.py`. Falsifiability:
revert `_encode_field_to_json`'s STRUCT branch, the test fails
with the `<?>` substring check.

If LIST also lands, add a second case
`test_to_json_list_field.mn` covering
`struct { items: List<Int> }`.

### Phase 5 — bump + closeout (~30 min)

```bash
python3 scripts/bump_version.py 5.39.3
$EDITOR CHANGELOG.md       # ### Fixed: to_json::<T> nested-struct
$EDITOR CLAUDE.md          # release-notes entry
$EDITOR docs/roadmap/v5/v5.39.3/SESSION_REPORT.md
$EDITOR docs/SPEC.md       # Hd-class header re-sync
python3 scripts/check_doc_freshness.py
make build-rt              # rebuilds with new MAPANARE_VERSION
python3 scripts/build_stage1.py
bash scripts/verify_fixed_point.sh   # STRICT
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1
make ci-gates && make lint
python3 -m pytest tests/stdlib/test_struct_json_runtime.py \
                  tests/stdlib/test_struct_json_ir_shape.py \
                  tests/stdlib/test_struct_json_layout.py \
                  tests/stdlib/test_struct_json.py
```

## Closeout checklist

- [ ] `_encode_field_to_json` adds `TypeKind.STRUCT` branch
      (and possibly `LIST` per Phase 1 decision)
- [ ] Shared helper `_emit_struct_json_body` extracted from
      `_lower_encode_struct`
- [ ] Pre-fix: `/tmp/tojson_nested.mn` prints `<?>`
      Post-fix: prints recursive JSON
- [ ] `tests/stdlib/test_struct_json_runtime.py` gains
      `test_to_json_nested_struct.mn` (and possibly
      `test_to_json_list_field.mn`); GREEN
- [ ] Falsifiability locked (revert STRUCT branch → test fails;
      reapply → green)
- [ ] Self-host mirror verified N/A (or applied if surprise
      matches surface)
- [ ] STRICT 3-stage fixed point preserved (241,898 / 0)
- [ ] Goldens 95/95
- [ ] `make ci-gates` GREEN; `make lint` clean
- [ ] CHANGELOG honest about bundle scope (STRUCT only vs
      STRUCT+LIST); v5.39.4 tracked if MAP/ENUM held
- [ ] CLAUDE.md release-notes entry
- [ ] `docs/SPEC.md` header re-synced to v5.39.3 cut
- [ ] `gitnexus_detect_changes` matches expected scope
- [ ] `npx gitnexus analyze --embeddings` after commit

## Risk register

- **Helper-refactor scope creep.** Extracting
  `_emit_struct_json_body` from `_lower_encode_struct` may
  surface that `_lower_encode_struct` mixes call-expr argument
  unpacking with the body-emit logic. If clean-extraction is
  hard, inline the body directly in the new STRUCT branch
  (some duplication, smaller diff). The shared helper is the
  right shape but not load-bearing for correctness.
- **LIST bundle expands diff.** If Phase 1 decides to bundle
  LIST and the runtime list-iteration MIR is more involved than
  estimated, defer LIST to v5.39.4. Don't let scope creep on a
  small follow-on release.
- **`from_json::<T>` for nested structs.** Currently `decode_to`
  only handles primitive field types (`_decode_json_field` at
  `lower.py:3002`). v5.39.3 ships `to_json::<T>` for nested
  structs; the round-trip test forces `from_json::<T>` to also
  handle nested structs. If v5.39.3's round-trip test fails on
  the `from_json` side, that's v5.39.4's whole release. Test
  shape: `to_json -> string -> from_json -> assert eq` for a
  nested struct. If it fails, document the asymmetry in
  CHANGELOG `### Changed` (`to_json` recurses; `from_json`
  doesn't yet) and split.

## Notes for v5.40.0 PROMPT post-v5.39.3

- v5.40.0 PROMPT's "Hard prerequisite" line (already updated at
  v5.39.2 to "SATISFIED") stays valid — `from_json::<T>` for
  flat structs remains GREEN. v5.39.3 strengthens the
  `to_json::<T>` side; v5.40.0's `ask_typed::<T>` will benefit
  from clean nested-struct round-trips.
