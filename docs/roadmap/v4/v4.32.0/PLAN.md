# Mapanare v4.32.0 — Arc-End Panel Closure

> **Theme:** Close the 9 HIGH + MEDIUM items the v4.31.0 arc-end panel
> surfaced. Zero new features. This release is to the v4.27.0–v4.31.0
> recovery arc what v4.27.0 was to the v4.26.0 panel: a clean bug-fix
> closeout that makes the next growth cycle safe.

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v4.31.0 (with the 5 PASS + 2 PASS WITH NOTES panel verdict)
**Estimated work:** 1–2 days
**Delta review:** No (zero new syntax)
**Full panel:** No

---

## The Panel's Docket

The v4.31.0 arc-end panel returned aggregate **9.343/10** with 5 PASS + 2 PASS WITH NOTES + 0 NEEDS WORK. The recovery arc terminated successfully. But the panel surfaced 25 action items, of which 9 are HIGH or MEDIUM:

| # | Sev | Item | Reporter | File |
|---|---|---|---|---|
| 1 | HIGH | `__mn_list_get` NULL-on-OOB + emitter unconditional deref (segfault window from v4.31.0 cleanup) | Viper V2 | `mapanare_core.c`, `emit_llvm_text.py` |
| 2 | HIGH | Self-hosted emitter asymmetry — 7-cycle items closed only on the Python side | Rattler #8, Cobra #14 | `self/emit_llvm.mn`, `self/emit_llvm_ir.mn`, `self/mir_opt.mn` |
| 3 | MED | Committed `libmapanare_rt.a` stale (still has `__mn_list_oob_buf` symbol) | Boa M1 | `runtime/native/libmapanare_rt.a` |
| 4 | MED | `stage2.ll` `.gitignore`'d but never `git rm`'d | Cobra | `mapanare/self/stage2.ll` |
| 5 | MED | `_emit_drop_glue` at 437 lines, 10th extraction cycle | Cobra Issue #12 | `emit_llvm_text.py:1074` |
| 6 | MED | `mapanare_internal.h` unwired; `mnstr_to_cstr` 4-copy dup; `len < 0` memcpy crash | Mamba H3 | `runtime/native/*.c` |
| 7 | MED | `bind.py` String-field in struct returns + silent `int` annotation fallback | Boa M2, M3 | `mapanare/bind.py` |
| 8 | MED | Signal `recompute()` write outside lock (v4.28.0 scoped out propagate-side) | Viper M2 | `mapanare_core.c:2027-2125` |
| 9 | MED | CI `ci` job doesn't split gates; `check_changelog_honesty.py` fails without `.git` | Anaconda | `.github/workflows/ci.yml`, `scripts/check_changelog_honesty.py` |

Plus one ledger-hygiene item: the `CARRY_FORWARD.md` file needs two additions
(Viper's V1 drop-glue skip-struct-ret and M5 agent destroy message leak) and a
schema update to split Python-emitter closures from self-hosted-emitter
closures (Rattler + Cobra consensus).

v4.32.0 closes all 9 items + the ledger hygiene. LOW items 10–25 stay in the
ledger for later releases.

---

## Phase 1 — HIGH items

### Phase 1.1 — `__mn_list_get` OOB correctness (Viper V2)

The v4.31.0 cleanup deleted `__mn_list_oob_buf` (the 4KB thread-local
zero-buffer workaround from pre-v4.14.0). `__mn_list_get` now returns `NULL`
on OOB instead of reading zeros from the buffer. But the emitter's index-get /
index-set paths at `emit_llvm_text.py:3101-3108` dereference the returned
pointer unconditionally — `load <ety>, ptr <tp>` — so any program path that
hits OOB now segfaults instead of silently reading zeros.

**Correct fix (Viper's preference):** abort loudly at the runtime call site.
Silent zero reads were a bug; NULL returns turn that bug into a crash at a
predictable location.

- [ ] `runtime/native/mapanare_core.c:1011-1015` — `__mn_list_get` OOB path:
      replace `return NULL;` with
      `fprintf(stderr, "mapanare: list index %ld out of bounds (len=%ld)\n", idx, list->len); abort();`
- [ ] Add a matching abort in `__mn_list_set` OOB path.
- [ ] `tests/runtime/test_list_bounds.py` — new file. Compile and run a
      program that deliberately hits OOB; assert the subprocess exits via
      abort with the expected stderr pattern. Use `pytest.parametrize` to
      cover `get` and `set`, empty-list and non-empty-list, negative and
      past-end indices.
- [ ] Cookbook note: `docs/cookbook.md` §Lists — add a one-paragraph note
      that OOB is a hard abort, not a silent zero. Suggest `if idx < list.len`
      guards at the call site for defensive code.
- [ ] Re-verify `tests/llvm/test_break_nested.py::test_break_in_if_in_for`
      still passes — the v4.14.0 regression test is the canary for the bug
      the original workaround existed for.

### Phase 1.2 — Self-hosted emitter parity (Rattler #8, Cobra #14)

The v4.30.0 `CARRY_FORWARD.md` claim "six 7-cycle emitter items re-verified
clean" is **correct for the Python emitter** (verified by Rattler against
`mapanare/emit_llvm_text.py`) but **false for the self-hosted emitter**
(`mapanare/self/emit_llvm.mn`, `mapanare/self/emit_llvm_ir.mn`, and friends,
which Rattler read in full during the v4.31.0 review and found unchanged at
source). Specifically:

| Location | Current | Target |
|---|---|---|
| `mapanare/self/emit_llvm.mn:264-288` `get_fn_attrs` | returns only `" nounwind"` / `" nounwind readonly"` for every entry | mirror the Python `_RUNTIME_FN_ATTRS` table: `noalias` on every allocator's pointer return, `willreturn` on every `readonly` query, `nounwind` on every deterministic function |
| `mapanare/self/emit_llvm_ir.mn:116-125` `emit_add`/`emit_sub`/`emit_mul` | return plain `add` / `sub` / `mul` | emit `add nsw` / `sub nsw` / `mul nsw` for signed integer arithmetic, matching `emit_llvm_text.py:2010-2062` |
| `mapanare/self/emit_llvm.mn:352` `__mn_map_new` declaration | 3 parameters | 4 parameters: `int64_t key_size, int64_t val_size, int64_t key_type, int64_t val_type` (match the runtime `mapanare_core.c` declaration) |
| `mapanare/self/mnc_all.mn:13259` `__mn_map_new` live call | 3 args | 4 args (the emitter fix above generates the right shape; `mnc_all.mn` is regenerated from `self/*.mn` via `scripts/build_stage1.py`'s concatenation step) |

**Approach:**

- [ ] Audit `mapanare/self/emit_llvm.mn:264-288` against the Python
      `_RUNTIME_FN_ATTRS` table at `emit_llvm_text.py:243-399`. Port every
      entry that has a runtime-side counterpart. For self-hosted runtime
      symbols that don't exist in the Python table (rare — mostly none),
      add with conservative defaults.
- [ ] Update `get_fn_attrs` return signature if needed to carry multi-attr
      strings (`" nounwind willreturn"` vs just `" nounwind"`).
- [ ] `mapanare/self/emit_llvm_ir.mn:116-125` — add `nsw` modifier to
      integer arithmetic. Float arithmetic stays as-is.
- [ ] `mapanare/self/emit_llvm.mn:352` — declare `__mn_map_new` with 4
      params, matching `runtime/native/mapanare_core.c:__mn_map_new`.
- [ ] Regenerate `mapanare/self/mnc_all.mn` via `python scripts/build_stage1.py`.
      Verify `mnc_all.mn:13259` (the call site that Rattler cited) now emits
      a 4-arg call. Grep the file: `grep "__mn_map_new" mapanare/self/mnc_all.mn`.
- [ ] Rebuild `mnc-stage1` via `python scripts/build_stage1.py`. Verify
      binary builds.
- [ ] Regenerate stage2.ll via `bash scripts/verify_fixed_point.sh` and
      confirm: (a) `llvm-as` still clean, (b) `grep "noalias" stage2.ll`
      returns a nonzero count (previously zero — this is the proof the
      self-hosted emitter now emits the annotations), (c)
      `grep "nsw" stage2.ll` returns a nonzero count, (d) stage2-vs-stage3
      diff ≤100 lines (should actually improve, but the goal is "not worse").
- [ ] Run all 44 golden tests through `mnc-stage1`. Zero regressions.
- [ ] Run 11/11 stage2 validation via `python scripts/ir_doctor.py stage2`.
- [ ] **Important**: this change **regenerates `mnc_all.mn`** and the
      subsequent `main.ll`. The line counts in measurements tables will
      shift. Record the before/after numbers so the SESSION_REPORT has them.

### Phase 1.3 — `CARRY_FORWARD.md` schema update (Rattler, Cobra, Viper consensus)

The ledger currently has one closure status per item. The arc-end panel
surfaced that some closures are Python-emitter-only while the self-hosted
side is still stale. Add explicit columns so this asymmetry can never hide
again.

- [ ] `.reviews/CARRY_FORWARD.md` — add a new schema note at the top:
      "Items that affect both the Python and self-hosted compiler
      pipelines are tracked with **two** closure states. Ledger rows
      with asymmetry are marked `PYTHON: closed, SELF-HOSTED: open`
      (or vice versa). A symmetric closure requires both."
- [ ] Update rows #30–#35 (the six 7-cycle emitter items — `i64*`, `void ()*`,
      list bitcast, `nsw`, `__mn_map_new` arity, `noalias`/`willreturn`)
      to show Python-side closed v4.30.0, self-hosted-side closed v4.32.0
      (or keep asymmetric until Phase 1.2 actually lands — update the row
      at PR merge time, not before).
- [ ] Add **two new rows** for Viper's ledger-gap findings:
      - Row #49: "Drop-glue skip-struct-ret early return at
        `emit_llvm_text.py:1097-1099` (8th cycle, Viper Issue #14 at v4.26.0,
        not previously in ledger)" — status: will be closed opportunistically
        by Phase 2.2 extraction below, or if not, remains OPEN tracked to
        v4.33.0.
      - Row #50: "Agent `mapanare_agent_destroy` drops in-flight messages
        without freeing them (2nd cycle, Viper M5 at v4.26.0, not previously
        in ledger)" — status: OPEN, tracked to v4.33.0.

---

## Phase 2 — MEDIUM items (artifact + hygiene)

### Phase 2.1 — Stale binary artifacts (Boa M1, Cobra)

- [ ] `git rm runtime/native/libmapanare_rt.a` — the committed archive
      is stale (contains the `__mn_list_oob_buf` symbol that the source
      deleted in v4.31.0). Binary artifacts belong in `make build-rt`
      output, not in the repo.
- [ ] `.gitignore` — add `runtime/native/libmapanare_rt.a` so it doesn't
      get re-committed.
- [ ] Same treatment for every other committed `.a` / `.o` / `.so` /
      `.dll` / `.obj` in `runtime/native/` — audit `ls runtime/native/`
      and `git rm` everything binary. `make install` / `make build`
      will regenerate them on first build.
- [ ] `git rm mapanare/self/stage2.ll` — it's already in `.gitignore`
      but `git ls-files mapanare/self/stage2.ll` returns a hit. Remove
      the tracked copy.
- [ ] Audit: `git ls-files | xargs -I{} sh -c 'file "{}" 2>/dev/null | grep -E "ELF|PE32|Mach-O|current ar archive|shared object" && echo "{}"'` — any binary file that's still tracked gets a `git rm`.
- [ ] `Makefile install` — add a `build-rt` precondition so fresh clones
      build the archive before anything that needs it. Already the
      dependency graph says this but make it explicit in the README.
- [ ] CI: `check-runtime-sources` still validates the source list; add
      a complementary check that no binary artifact is tracked.

### Phase 2.2 — Drop glue extraction (Cobra Issue #12, 10th cycle)

`_emit_drop_glue` at `mapanare/emit_llvm_text.py:1074` is now 437 lines —
up from 343 at v4.26.0, 300 at v3.39.0. Monolithic. Every new drop-glue
case gets appended. Cobra has been asking for extraction since v3.39.0
and promised to escalate to HIGH in v4.33.0 if v4.32.0 doesn't close it.

**Extraction target:**

```python
# mapanare/emit_llvm_text.py

def _emit_drop_glue(self, ret_ty: MIRType, ret_ptr_fields: list[int]) -> str:
    """Top-level dispatcher. Delegates to per-resource helpers by MIRType.kind."""
    lines = []
    for field_idx, field_type in enumerate(ret_ty.fields):
        if field_idx in ret_ptr_fields:
            continue  # caller's responsibility
        kind = field_type.kind
        if kind == TypeKind.STRING:
            lines.extend(self._emit_drop_glue_string(field_idx, field_type))
        elif kind == TypeKind.LIST:
            lines.extend(self._emit_drop_glue_list(field_idx, field_type))
        elif kind == TypeKind.MAP:
            lines.extend(self._emit_drop_glue_map(field_idx, field_type))
        elif kind == TypeKind.CLOSURE:
            lines.extend(self._emit_drop_glue_closure(field_idx, field_type))
        elif kind == TypeKind.SIGNAL:
            lines.extend(self._emit_drop_glue_signal(field_idx, field_type))
        elif kind == TypeKind.STREAM:
            lines.extend(self._emit_drop_glue_stream(field_idx, field_type))
        elif kind == TypeKind.AGENT:
            lines.extend(self._emit_drop_glue_agent(field_idx, field_type))
        # else: scalar or unmanaged — no drop needed
    return "\n".join(lines)
```

- [ ] Extract each of the 7 helpers. Keep the existing logic byte-identical;
      this is a pure refactor, not a behavior change.
- [ ] Top-level function drops below 50 lines (dispatch only).
- [ ] Each helper is 30–60 lines, focused on one resource type.
- [ ] Regenerate `mapanare/self/main.ll` — the byte output must be **identical**
      before and after extraction. Verify with `diff main.ll.before main.ll.after`
      showing zero lines of diff.
- [ ] Update `tests/llvm/test_drop_glue.py` to test each helper in isolation
      via `_emit_drop_glue_<kind>` direct calls.
- [ ] `CARRY_FORWARD.md` Cobra Issue #12 marked CLOSED with evidence:
      "line count dropped from 437 → <50 for the dispatch; per-type helpers
      average 45 lines each."
- [ ] **Opportunistic**: during extraction, address Viper V1 (drop-glue
      early return for ptr-containing struct returns at `emit_llvm_text.py:1097-1099`).
      The early return short-circuits `_extract_ret_ptrs`. If the new
      per-type helpers correctly consult `ret_ptr_fields` (as the extraction
      target above does), the early return becomes obsolete and can be
      deleted. If the refactor doesn't naturally eliminate it, keep the
      early return and update `CARRY_FORWARD.md` row #49 (from Phase 1.3)
      to OPEN tracked to v4.33.0.

### Phase 2.3 — `mapanare_internal.h` wiring + `mnstr_to_cstr` consolidation (Mamba H3, 6th cycle)

`runtime/native/mapanare_internal.h` (63 lines) is unwired — no `#include`
sites in the runtime. `mnstr_to_cstr` has 4 copies across `mapanare_core.c`,
`mapanare_io.c`, `mapanare_db.c`, `mapanare_html.c`, and the `len < 0`
sentinel from `__mn_file_read_or_empty` crashes at `mapanare_io.c:875-882`
because the `memcpy` has no `len > 0` guard.

- [ ] `runtime/native/mapanare_internal.h` — define `mnstr_to_cstr` as a
      `static inline` function. This is an internal helper so static inline
      is correct (no ODR issue, no linker bloat, each TU gets its own copy
      but that's fine for 20 lines of code).
- [ ] Delete the 4 local copies in `core.c`, `io.c`, `db.c`, `html.c`.
- [ ] Add `#include "mapanare_internal.h"` to the 4 files.
- [ ] `mapanare_io.c:875-882` — audit the memcpy. If the source len is
      `-1` (the file-read sentinel), the memcpy is a UB read. Add the
      `len > 0` guard, or fix `__mn_file_read_or_empty` to never return
      `-1` (change the API to return `size_t` and use 0 for empty).
- [ ] Test: `tests/runtime/test_file_read_empty.py` — compile a program
      that reads an empty file and verify it doesn't crash.
- [ ] Sanity: `tests/runtime/test_mnstr_conversion.py` — one call from
      each of the 4 files' code paths, verify the returned cstring is
      correct.

### Phase 2.4 — `bind.py` struct-field unwrapping + annotation fallback (Boa M2, M3)

Two gaps Boa found during v4.31.0 live-testing of the FFI path:

**M2**: `bind.py` declares user struct types as `ctypes.Structure`
subclasses, but for a struct with a `String` field (e.g. `Point{name: String, x: Float}`),
the `_MnString` sub-struct is not auto-unwrapped when the Python caller
accesses the field. The caller gets back a `_MnString` where they expect
a `str`.

**M3**: `_py_annotation_for` falls back to `"int"` for compound types it
doesn't recognize (`List<Int>`, `Result<T, E>`, etc.). Silent corruption.

- [ ] `mapanare/bind.py` — when generating struct type declarations,
      also generate property accessors on the `ctypes.Structure` subclass
      that auto-unwrap `_MnString` fields into Python `str`.

      ```python
      class Point(Structure):
          _fields_ = [("name", _MnString), ("x", c_double)]

          @property
          def name(self) -> str:
              return self._name.to_str()

          @name.setter
          def name(self, value: str) -> None:
              self._name = _MnString.from_str(value)
      ```

      (With `_fields_` renaming to `_name` so the property can shadow it.)
- [ ] Recursive: a struct field that is itself a struct type with a
      String inside must also unwrap. Test with a nested struct.
- [ ] `_py_annotation_for` — raise a `BindError` on unknown compound
      types instead of returning `"int"`. The error message names the
      type and suggests filing an issue (or extending the mapping if
      the user knows the target ctypes form).
- [ ] `tests/bind/test_python_binding.py` — add:
      - `test_struct_with_string_field` — round-trip a `Person{name: String, age: Int}`
      - `test_nested_struct_round_trip` — round-trip a struct with a nested struct
      - `test_unknown_type_raises_bind_error` — negative test, confirms
        unknown compound types fail loudly

### Phase 2.5 — Signal recompute race (Viper M2)

The v4.28.0 concurrency work was scoped to the write-side of `__mn_signal_set`.
Viper's original M2 pointed at `mn_signal_recompute` which writes to
`signal->value` via `compute_fn` outside the lock, and `mn_signal_propagate`
which calls recompute outside the mutex. Two readers subscribing to the
same computed graph can tear-read during a write.

- [ ] `runtime/native/mapanare_core.c:2027-2036` — `mn_signal_recompute`:
      acquire the signal mutex before invoking `compute_fn`, release after.
- [ ] `runtime/native/mapanare_core.c:2091-2125` — `mn_signal_propagate`:
      take the lock before the recompute call if not already held. Be careful
      about lock ordering: the propagate path walks subscribers, which may
      themselves be signals with their own locks. Document the ordering
      (topological / acquire-in-DFS-order) inline.
- [ ] TSan stress test: `tests/runtime/tsan/signal_recompute_stress.c` —
      4 threads, each driving an independent computed-signal graph.
      Expect zero TSan races.
- [ ] Follow the `v4.28.0` TSan test pattern — same compile flags, same
      iterations-per-thread. Add to `tests/runtime/tsan/` and to the
      existing TSan CI step.

### Phase 2.6 — CI gate hygiene (Anaconda)

- [ ] `.github/workflows/ci.yml` — split the `ci` job's five back-to-back
      CI gates into independent jobs (or at minimum, use `if: always()`
      on each step so a gate-1 failure doesn't mask gates 2-5). The
      failure surface should tell the PR author which gates failed, not
      just "the first one."
- [ ] `scripts/check_changelog_honesty.py` — detect whether a `.git`
      directory exists. If not (e.g. in a Debian `dpkg-buildpackage`
      environment where `.git` is scrubbed before running tests),
      fall back to `grep -r` instead of `git grep`. Same detection
      pattern in `check_no_hollow_features.py` if it uses `git grep`.
- [ ] Test: run the script against a tarball extraction (no `.git`)
      and verify it still exits 0 on clean input.

---

## Phase 3 — Verification + closeout

### Phase 3.1 — Full validation suite

- [ ] `.\dev.ps1 validate` (Windows) or `make test lint` (Linux) —
      black + ruff + mypy + pytest + WAT emission all clean
- [ ] `python scripts/test_native.py --stage1 mapanare/self/mnc-stage1` —
      44/44 golden tests through mnc-stage1
- [ ] `python scripts/ir_doctor.py stage2` — 11/11 stage2 modules valid
- [ ] `bash scripts/verify_fixed_point.sh` — fixed-point diff ≤100 lines;
      happy path (exit 0) and regression path with `DIFF_THRESHOLD=5`
      (exit 1) both verified
- [ ] `make check-runtime-sources` — clean
- [ ] `python scripts/check_silent_skips.py tests/` — clean
- [ ] `python scripts/check_changelog_honesty.py` — clean (after CHANGELOG
      entry is written)
- [ ] `python scripts/check_docs_drift.py` — clean (no doc changes in
      v4.32.0 should touch parseable blocks)
- [ ] `python scripts/check_no_hollow_features.py` — clean (no new
      decorators, no new `raise NotImplementedError`, no new AST classes
      without lowering)

### Phase 3.2 — CHANGELOG + VERSION + SESSION_REPORT

- [ ] `VERSION` — bump `4.31.0` → `4.32.0`
- [ ] `CHANGELOG.md` — new `[4.32.0]` entry.
      **Every backticked path must resolve on disk** (`check_changelog_honesty.py`
      will fail the build if not). Every test name must exist. Every symbol
      must be greppable. No hollow claims.
- [ ] `docs/roadmap/v4/v4.32.0/SESSION_REPORT.md` — honest session log,
      matching the recovery-arc template. Include: what shipped, what didn't,
      decisions made with rationale, verification log (actual command output).
- [ ] `docs/roadmap/ROADMAP.md` — v4.32.0 row added
- [ ] `docs/roadmap/v4/README.md` — v4.32.0 row added
- [ ] `.reviews/CARRY_FORWARD.md` — updates from Phase 1.3

### Phase 3.3 — Pre-push regression

The recovery arc established the pre-push discipline from `CLAUDE.md`:
full validate suite before any commit, mirrors CI exactly. Do the full
`.\dev.ps1` run once before tagging. WAT emission included.

- [ ] `python -m mapanare emit-wasm examples/wasm/hello.mn -o /dev/null`
- [ ] `python -m mapanare emit-wasm examples/wasm/wasi_app.mn -o /dev/null`

---

## Exit criteria (18 items)

| # | Check | Evidence |
|---|---|---|
| 1 | `__mn_list_get` aborts loudly on OOB with regression test | `tests/runtime/test_list_bounds.py` passes; v4.14.0 break-nested canary still passes |
| 2 | Self-hosted `get_fn_attrs` returns `noalias`/`willreturn` where Python does | `grep "noalias" stage2.ll` > 0; rebuild+llvm-as clean |
| 3 | Self-hosted `emit_add/sub/mul` emit `nsw` modifier | `grep "add nsw" stage2.ll` > 0 |
| 4 | Self-hosted `__mn_map_new` declared + called with 4 args | `mnc_all.mn` regenerated; every call site is 4-arg |
| 5 | 44/44 golden tests pass through mnc-stage1 | `scripts/test_native.py` clean |
| 6 | 11/11 stage2 modules valid | `ir_doctor.py stage2` clean |
| 7 | Fixed-point diff ≤100 (should be ≤69, ideally lower from self-hosted parity) | `verify_fixed_point.sh` clean |
| 8 | `libmapanare_rt.a` and other binary artifacts `git rm`'d | `git ls-files` returns no binary files in `runtime/native/` |
| 9 | `mapanare/self/stage2.ll` no longer tracked | `git ls-files mapanare/self/stage2.ll` returns nothing |
| 10 | `_emit_drop_glue` top-level < 50 lines, extracted into 7 per-resource helpers | line count measured before/after |
| 11 | `mapanare_internal.h` wired; `mnstr_to_cstr` single definition | `grep -c "mnstr_to_cstr" runtime/native/*.c` returns 1 (the include) + 1 (the include) + etc., not 4 local copies |
| 12 | `len < 0` crash window at `mapanare_io.c:875-882` closed | `tests/runtime/test_file_read_empty.py` passes |
| 13 | `bind.py` struct-field `String` unwrapping works | `test_struct_with_string_field` passes |
| 14 | `bind.py` unknown compound types raise `BindError` | `test_unknown_type_raises_bind_error` passes |
| 15 | Signal recompute runs under lock | `tests/runtime/tsan/signal_recompute_stress.c` TSan-clean |
| 16 | CI `ci` job split + `check_changelog_honesty.py` .git-free fallback | CI logs show all gates running independently |
| 17 | `CARRY_FORWARD.md` schema updated + 2 new rows added + asymmetric items flagged | manual diff review |
| 18 | `SESSION_REPORT.md` written with honest fact-checkable claims | one file at `docs/roadmap/v4/v4.32.0/SESSION_REPORT.md` |

---

## What v4.32.0 explicitly does NOT do

Carry-forward from the v4.31.0 panel LOW docket (items 10–25) stays open:

- `mn_signal_propagate` unbounded recursion (8th cycle) — v4.33.0+
- `MN_PROFILE_FREE` never called (6th cycle) — v4.33.0+
- `__mn_read_line` 4KB stack truncation (6th cycle) — v4.33.0+
- Arena allocator not thread-safe — v4.33.0+
- `ssl_load_library` CAS-before-init (3rd cycle) — v4.33.0+
- `s_bcrypt` cache thread safety (3rd cycle) — v4.33.0+
- `s_net_initialized` non-atomic (5th cycle) — v4.33.0+
- `cuda_matmul` upload rc (v3.47.0 #3) — v4.33.0+
- Self-hosted bounded-for sentinels (9th cycle) — v4.33.0+
- SPEC §3.10 tensor "not yet implemented" status line — v4.36.0 (tensor completeness release)
- `examples/` agents/signals/streams demos — v4.37.0 (AI/LLM stdlib release)
- `mnc-stage1` shipped unstripped — v4.33.0+ (Makefile tweak, one line)
- Viper M5 agent destroy message leak — v4.33.0+ (20-line runtime change)

No new language features. No new decorators. No new AST classes. No new
grammar. v4.32.0 is specifically the panel-closure release; v4.33.0 is
the first growth release.

---

## Reference — the arc-end panel

- `.reviews/v4.31.0/README.md` — panel summary (9.343 aggregate, 5 PASS + 2 PASS WITH NOTES)
- `.reviews/v4.31.0/01-viper.md` — HIGH V2 detail, V1/M2/M5 ledger gaps
- `.reviews/v4.31.0/02-boa.md` — M1 stale archive, M2/M3 bind.py
- `.reviews/v4.31.0/03-cobra.md` — Issue #12 drop glue 10th cycle, stage2.ll tracking bug
- `.reviews/v4.31.0/04-mamba.md` — H3 mapanare_internal.h, len<0 crash
- `.reviews/v4.31.0/05-anaconda.md` — CI job splitting, git-grep fallback
- `.reviews/v4.31.0/06-rattler.md` — self-hosted emitter asymmetry detail with file:line
- `.reviews/v4.31.0/07-coral.md` — no v4.32.0 items (all closed in-arc)
- `.reviews/CARRY_FORWARD.md` — the ledger, to be updated by Phase 1.3
- `docs/roadmap/v4/POST_RECOVERY_ROADMAP.md` — the 10-version plan this release opens

---

## After v4.32.0

v4.33.0 opens with the first new language feature in 7 releases: the `?`
operator for `Result<T, E>` and `Option<T>`. See
`docs/roadmap/v4/POST_RECOVERY_ROADMAP.md` §v4.33.0 for the full scope.
Delta review is mandatory per `REVIEW_CADENCE.md`.

The v4.32.0 SESSION_REPORT will document which LOW docket items were closed
opportunistically (e.g. if Phase 2.2 drop-glue extraction happens to fix
Viper V1, mark it closed in the ledger) and which still carry forward to
v4.33.0+.
