# v5.36.0 — Session Report

> **Status:** ready, not tagged.
> **Theme:** Js.\* — JSON completeness arc.
> **Aggregate:** 0 HIGH / 1 MEDIUM (Js.4.B `decode_to`/`from_json`
> runtime SEGV — deferred to v5.36.1; macOS notarization carry from
> v5.33.0) / ~6 LOW (Bytes type for true streaming, named-tzdb,
> chunked I/O, codegen-driven serde, JSON5/JSONC/JSONPath, RFC 8785
> canonicalization, named tzdb).
> **Cadence:** unchanged. Next routine panel due v5.40.0.
> **Tag policy:** waits for explicit user approval per project memory.

## Summary

Third release in the stdlib gap-close arc:

- **Dt.\*** at v5.34.0 — date/time
- **Sq.\*** at v5.35.0 — sqlite + Tn.1 closure
- **Js.\*** at v5.36.0 — JSON

These three are the prerequisites named for v5.40.0 `ask` —
specifically the typed-LLM-response form `let plan: Plan =
ask("...")`. v5.36.0 delivers the API surface for that ergonomic
(`from_json::<T>`) at compile time; the runtime fix that closes
the round-trip is one release further out (Js.4.B → v5.36.1).

## Phase 0 surprise findings

Three things the PROMPT/PLAN got wrong, surfaced at Phase 0 audit:

1. **`stdlib/json/` package didn't exist.** The PROMPT specified
   splitting into `parse.mn` / `format.mn` / `stream.mn` /
   `serde.mn` under a new package; the existing 964-LOC
   `stdlib/encoding/json.mn` already covered all four areas as a
   single file. **Decision: keep single-file.** Same lesson as
   v5.34.0 Dt.\* deviation — multi-file stdlib modules hit
   cross-module mangling/extern-propagation limitations in the
   current toolchain.

2. **Runtime type metadata for structs doesn't exist.** PROMPT
   claimed it was "currently inlined in `mapanare_core.c` /
   `mapanare_runtime.c`" and Js.4 lifts/extracts it. Verified by
   IR inspection that `print(struct)` literally just emits
   `printf("%lld\n", first_field)` — no field iteration, no
   metadata. Building runtime reflection from scratch would be
   3-5 release sessions. **Decision (user-confirmed): Shape B —
   extend the existing compile-time `encode_struct::<T>` /
   `decode_to::<T>` intrinsics rather than build a runtime
   metadata system.** Same v5.40.0 ergonomic; bounded scope.

3. **`encode_struct` / `decode_to` already existed** as
   compile-time monomorphized intrinsics in `mapanare/lower.py`.
   PROMPT didn't acknowledge them; Js.4 was scoped as
   greenfield work. Reality: `to_json::<T>` is a thin alias;
   `from_json::<T>` is `decode(s)` + `decode_to::<T>(jv)` chain.

## Compiler-side bugs uncovered

Three compiler bugs surfaced during Js.\* work, two fixed
in-release, one deferred:

- **Js.0** (`mapanare/emit_llvm_text.py:1421`): `_san` sanitizer
  used `nm.lstrip("%")` (only leading), but call sites
  interpolated names into compound IDs like
  `f"_map_iter_{value.name}"` where `value.name` may already
  start with `%`. The embedded `%` survived sanitization →
  invalid LLVM IR (`%_map_iter_%entries37.addr`). **Bug: 1 line.
  Fix: 1 line + comment.** Goldens 95/95 preserved. Required
  for Phase 0 corpus runner to compile.
- **Js.0.B** (`mapanare/emit_llvm_text.py:5214` / `5223`):
  `_do_wrap_ok` and `_do_wrap_err` hardcoded the unfilled side
  of the Result struct as `ptr`, producing
  `{i1, {ok_ty, ptr}}` when downstream alloca was sized for
  `{i1, {ok_ty, err_ty}}`. Mismatch invisible until a Phi merge
  with both type args propagated hit a size conflict. Mirrored
  shape on _do_unwrap (which already inspects
  `i.val.ty.type_info.args`) — Wrap variants now do the same.
  **Required for Js.4 Shape B `from_json::<T>` to build.**
- **Js.4.B** (deferred to v5.36.1): `decode_to::<T>` builds and
  links cleanly post-Js.0.B but SEGVs at runtime in the
  field-extraction step. Confirmed for both Int and String
  field types with single-field structs. Most likely a v5.x
  drop-glue use-after-free where the parsed JsonValue's inner
  heap allocations are freed before `decode_to` reads them.
  Bug stayed latent because `tests/stdlib/test_struct_json.py`
  only verifies IR-text content (no link, no run). Investigation
  estimate: 4-8h per the v5.6.x drop-glue history. Tracked as
  `Js.4.B` priority MEDIUM for v5.36.1.

## Phase-by-phase

### Phase 0 — pre-flight + RFC 8259 corpus baseline

- Tn.1 closed in v5.35.0 SESSION_REPORT (renamed Sq.0).
  HARD GATE passes.
- Baseline strict fixed-point: 241,898 lines / 0 diff. Goldens
  95/95. v5.35.0 SESSION_REPORT confirmed.
- Vendored nst/JSONTestSuite at
  `stdlib/json/tests/fixtures/rfc8259/` (318 fixtures + LICENSE).
  **Gitignored at user request** — corpus runner clones-on-demand.
- Wrote `scripts/run_json_corpus.py` after several iterations
  (per-fixture invocation pattern; compile once, run binary 318
  times).
- Js.0 sanitizer fix landed during Phase 0 (blocker for any
  end-to-end test).
- Discovered `substr(start, count)` (NOT `(start, end)`) — the
  existing json.mn calls work because `substr(0, n)` happens
  to mean the same thing under either convention.
- Discovered v5.x match-cleanup SEGV that requires a `print`
  between consecutive file-reads in driver code; documented
  workaround in `scripts/run_json_corpus.py`. Not in v5.36.0
  scope.
- **Initial corpus baseline:** 275 CONFORM / 6 DEVIATE_ACCEPT /
  2 CRASH / 35 IMPL.
- Wrote `docs/roadmap/v5/v5.36.0/RFC_AUDIT.md` (auto-generated
  per-fixture audit).

### Phase 1 — Js.1 parser correctness

Three surgical edits to `stdlib/encoding/json.mn`:

- **Js.1.A** — leading-zero rejection in `parse_json_number`.
  After consuming first digit, if it's `0`, peek next char and
  reject if also a digit. Closes 3 fixtures
  (`n_number_-01.json`, `n_number_neg_int_starting_with_zero.json`,
  `n_number_with_leading_zero.json`).
- **Js.1.B** — unescaped control-char rejection in
  `parse_json_string`. Loop now reads `src.byte_at(p)` and
  rejects bytes < 32. The pre-fix special case for `\n`
  (line tracking + appended to result) is removed. Closes 3
  fixtures (`n_string_unescaped_ctrl_char.json`,
  `n_string_unescaped_newline.json`,
  `n_string_unescaped_tab.json`).
- **Js.1.C** — depth limit on nested arrays/objects. New
  `MAX_JSON_DEPTH: Int = 256` const. `decode_value` →
  `decode_value_d(..., depth=0)` private wrapper threading
  depth through to `decode_array` / `decode_object`. Closes
  2 fixtures (`n_structure_100000_opening_arrays.json`,
  `n_structure_open_array_object.json`).

**Final corpus state:** 283 CONFORM / 0 DEVIATE / 0 CRASH /
35 IMPL = 318 fixtures total. Existing 46 `test_json.py`
tests still pass.

### Phase 2 — Js.2 pretty-print

- `make_indent(spaces, level)` parameterized on indent size
  (was hardcoded 2 spaces).
- `encode_pretty(value, indent)` with `indent <= 0` early-
  returns through compact `encode` for byte-equality.
- New aliases: `to_json`, `to_json_pretty`, `parse`. Identical
  behavior to the legacy spellings; gives v5.36.0+ idiomatic
  surface that v5.40.0 `ask` work can build against.

### Phase 3 — Js.3 streaming parser (LITE)

User-confirmed Js.3-LITE shape: ship the API contract on top
of the existing batch parser.

- New types: `JsonStreamParser` (events list + cursor + error
  state), `JsonStreamStep` (parser + Option<JsonEvent>).
- New functions: `json_stream_open(text)`,
  `json_stream_next(p)`, `json_stream_error(p)`.
- True chunked I/O deferred to a release that adds a `Bytes`
  type and a chunk-aware state machine (estimate: ~10-15h
  rather than PROMPT's claimed 4h).

Mapanare structs are value types and have no method-call
syntax, so the API uses free functions returning a
`JsonStreamStep` each time (functional-style threading).

### Phase 4 — Js.4 (Shape B) typed serde

User-confirmed Shape B: extend existing
`encode_struct::<T>` / `decode_to::<T>` rather than build
runtime reflection.

- Semantic routing for `to_json` and `from_json` in
  `mapanare/semantic.py:981` (with reuse of
  `encode_struct` / `decode_to` validation).
- Lower routing in `mapanare/lower.py:2268`:
  `to_json::<T>(v)` → `_lower_encode_struct(expr, v)`;
  `from_json::<T>(s)` → new `_lower_from_json(expr, s)`.
- New `_lower_from_json` emits `decode(s)` runtime call +
  Switch on Result tag + Ok arm calls `_lower_decode_to(expr,
  jv)` + Err arm rewraps + Phi merge.
- **`_lower_decode_to` Result type-args fix.** Pre-fix it
  used `MIRType(TypeInfo(kind=TypeKind.RESULT))` with no args,
  so the user's match arms read the Ok payload as `ptr` rather
  than the struct shape. Now sets `args=[T, JsonError]`.
- **Js.0.B compiler fix** in `_do_wrap_ok` / `_do_wrap_err`
  (described above) required for the type-args propagation to
  not produce mismatched IR.

**Status:** `to_json::<T>` works end-to-end (compile + link +
run; verified with `Point{3,4}` → `{"x": 3, "y": 4}`).
`from_json::<T>` builds successfully but SEGVs at runtime.
**Js.4.B (runtime fix)** deferred to v5.36.1.

Field-type coverage (carry from existing `_encode_field_to_json` /
`_decode_json_field`):

| Type | encode | decode |
|---|---|---|
| `Int` | ✓ | ✓ (compile) / SEGV (run) |
| `Float` | ✓ | ✓ (compile) / SEGV (run) |
| `Bool` | ✓ | ✓ (compile) / SEGV (run) |
| `String` | ✓ | ✓ (compile) / SEGV (run) |
| `Option<T>` | ✓ | ✓ (compile) / SEGV (run) |
| `List<T>` | partial (str fallback) | unsupported |
| `Map<String, T>` | partial (str fallback) | unsupported |
| nested struct | partial | unsupported |
| enum | partial | unsupported |

Coverage extension to `List`/`Map`/nested-struct/enum is
deferred to a release that does the runtime fix anyway.

### Phase 5 — Js.5 tests + Js.6 sqlite + Js.7 docs

- **Js.5** — `tests/stdlib/test_json_corpus_baseline.py`. Runs
  `scripts/run_json_corpus.py` end-to-end and asserts
  CONFORM ≥ 283 / DEVIATE ≤ 0 / CRASH ≤ 0. Marked
  `pytest.mark.slow` — opted into via `pytest -m slow`.
  Includes a self-test for the summary parser (catches
  pretty-print drift in `RFC_AUDIT.md`).
- **Js.6 sqlite integration — DEFERRED to v5.36.1.** Was scoped
  to add `Value::Json(JsonValue)` to `stdlib/sql/sqlite/value.mn`
  with bind/column round-trip. Implementation requires
  `from_json::<JsonValue>` runtime path which is broken at
  v5.36.0 ship; deferring keeps the feature paired with its
  required fix.
- **Js.7** — `docs/stdlib/json.md`. Written. Documents
  strictness changes, every public API, the Js.3-LITE memory
  characteristic, and the Js.4.B deferred runtime fix
  explicitly so callers know what they can and can't rely on.

### Phase 6 — Vb.\* mechanics

- `bump_version.py 5.36.0` clean.
- CHANGELOG full entry under `## [5.36.0]` with
  `### Added` / `### Changed` / `### Fixed` covering all
  Js.\* items + Js.0 / Js.0.B compiler fixes.
- This SESSION_REPORT.
- CLAUDE.md release-notes entry at top of "Current Version &
  Roadmap".
- SPEC.md header re-synced (`5.35.0` → `5.36.0`); new sync
  block added at top describing what v5.36.0 ships,
  specifically calling out Js.1 strict mode (`### Changed`,
  potentially breaking) and Js.4 (`from_json::<T>` runtime
  deferred).
- Stage1 rebuilt post-bump (per v5.31.0 lesson).
- `verify_fixed_point.sh` STRICT preserved at v5.35.0's
  241,898 lines / 0 diff.
- `python3 scripts/test_native.py` — 95/95 goldens GREEN.
- `gitnexus_detect_changes` — staged scope matches expected.
- `git push origin dev` clean.
- **NO TAG** per project memory (waits for explicit user
  approval).

## Surprises / lessons captured

- **`substr(start, count)` not `(start, end)`.** The existing
  json.mn happens to compute correct results via `substr(0, n)`
  but new code that does `substr(i, i+1)` for "one char at i"
  reads `i+1` characters. Worth a note in any future stdlib
  documentation pass.
- **`None`, not `None()`.** Mapanare's nullary enum constructor
  syntax is bare-name. The runtime errors with "Undefined
  function 'None'" if the user writes `None()`.
- **Single-line struct literals only.** Multi-line struct
  literal syntax (`new T { ... newline-separated fields ... }`)
  isn't supported by the current parser. Workaround: pre-bind
  fields to local variables, then construct on a single line.
  Tracked LOW; should be a future grammar extension.
- **`tests/stdlib/test_struct_json.py` only checked IR text,
  never linked or ran.** This let `decode_to` codegen ship with
  type-args bugs invisible to CI for many releases. Js.5
  corpus runner test pattern (build + run binary) is the
  preferred shape for catching these.
- **The v5.x match-cleanup SEGV reproduced reliably** in driver
  code that does a sequence of file-reads + match without
  intervening `print` calls. Worth a separate investigation
  release; tagging as a v5.36.x or v5.37.0 LOW.

## Aggregate state entering v5.37.0

- **0 HIGH**
- **1 MEDIUM**
  - **Js.4.B** — `decode_to::<T>` / `from_json::<T>` runtime
    SEGV. Compile-tested at v5.36.0. Required for v5.40.0
    `ask` typed-response ergonomic. Investigation:
    drop-glue use-after-free in JsonValue inner payload
    deref. **Target: v5.36.1.**
  - macOS notarization carry from v5.33.0 Nu.2 ad-hoc
    signing.
- **~6 LOW**
  - Native `Bytes` type → enables true chunked Js.3 streaming
    + `Value::Blob(Bytes)` migration in sqlite stdlib.
  - Js.6 sqlite `Value::Json(JsonValue)` — paired with Js.4.B.
  - Field-type coverage extension in `_encode_field_to_json` /
    `_decode_json_field` for `List`/`Map`/nested-struct/enum
    — paired with Js.4.B.
  - `JsonParseOpts { strict: false }` opt-out — only useful
    if a real-world corpus needs lenient mode.
  - Multi-line struct literal syntax (parser).
  - v5.x match-cleanup SEGV when arms only do file_write
    without print.
  - Cyclic-struct detection in `to_json::<T>` (`JsonError::Cyclic`).
