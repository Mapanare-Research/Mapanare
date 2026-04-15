# v4.132.0 Session Report — Sh.2 String-residual: 9 heap-UAF → 0

> Release 2 of the Sh.2 fix arc. v4.131.0 closed the LIST branch of
> the extracted-alias drop-glue bug. v4.132.0 closes the STRING branch
> with the analogous fix in the same helper. All 9 post-v4.131.0
> sanitizer findings close; the remaining 5 valgrind ERRORS are the
> out-of-scope Ge.1 generics-init class.

## Headline

**ASan: 9 → 0 findings (stretch goal hit).**
**Valgrind ERRORS: 14 → 5 (target ≤ 6 hit; all 5 residual are out-of-scope Ge.1).**
**Goldens: 53 / 65 (no regression from v4.131.0 target).**
**Zero pytest regressions** (38 non-bootstrap failures / 13 bootstrap failures — byte-identical to v4.131.0 baseline).

## What shipped

### Code change — STRING branch of `_do_copy` (`mapanare/emit_llvm_text.py`)

Twelve lines (plus 8-line comment) added immediately after v4.131.0's
LIST fix in `LLVMTextEmitter._do_copy`. Mirror of v4.131.0's logic,
swapping `self._list_vars` for `self._str_slots`:

```python
if t == STR:
    src_str_tracked = i.src.name in self._str_slots
    if src_str_tracked:
        # Ownership transfer: remap tracking slot src → dest
        slot = self._str_slots.pop(i.src.name)
        self._str_slots[i.dest.name] = slot
    else:
        # src is an alias; untrack dest if it was previously an owner
        if i.dest.name in self._str_slots:
            self._str_slots.pop(i.dest.name)
```

`_str_slots` is the String analog of `_list_vars` (both are
v4.101.0-era move-tracking state). `_move_resource` at payload
construction sites already zeroes both maps, but **only if the map
key exists**. Without the transfer, a Copy of a tracked source into a
temporary (which is what the MIR builder emits for every "pass a
String to an enum constructor" pattern) produced an untracked dest,
so `_move_resource(dest)` was a no-op and drop glue on the source
freed the buffer while the callee still referenced it.

Without the else branch, a second problem remained: `let mut s = "x";
s = fe.ret_type` made `s` a "still tracked" owner with the slot
pointing at the old `"x"`. When drop glue ran at return, it freed the
buffer `fe` still aliased. The untrack-on-alias branch closes that
half.

## Phase 1 — mechanism confirmation

`10_result.mn` canonical repro under post-v4.131.0 `mnc-stage1`:

```
==13116== Invalid read of size 1
==13116==    at 0x48524A7: bcmp
==13116==    by 0x723878: __mn_str_find
==13116==    by 0x6D6CC6: emit_llvm__emit_enum_payload
==13116==  Address 0x6aa7890 is 0 bytes inside a block of size 5 free'd
==13116==    at 0x484988F: free
==13116==    by 0x66FC67: lower__bind_one_pattern_field
==13116==  Block was alloc'd at __mn_str_concat
==13116==    by 0x66D15D: lower__bind_one_pattern_field
```

Maps exactly to `mapanare/self/lower.mn:3659` —

```mn
let indexed_name: String = variant_name + ":" + toString(pi)
s = emit_instr(s, Instruction::EnumPayload(payload_r.value, subject, indexed_name))
return s
```

The concat result is tracked as a local in `bind_one_pattern_field`.
At the `Instruction::EnumPayload(...)` constructor, the enum lowering
path calls `_move_resource` on payload values — but the MIR Copy from
`indexed_name` to the constructor's temporary never propagated
tracking, so `_move_resource` on the temp is a no-op. Drop glue on
return frees the buffer the freshly-constructed Instruction still
holds a pointer to. The parent emitter later reads it via
`emit_enum_payload` → UAF.

## Phase 2 — fix applied, per-test verification

```
valgrind  ./mnc-stage1 tests/golden/10_result.mn   # 0 errors
mnc-stage1 output → llvm-as                        # unchanged correctness path
```

## Phase 3 — verification sweep

| Gate | Pre (v4.131.0) | Post (v4.132.0) | Target | Status |
| --- | --- | --- | --- | --- |
| Goldens through `mnc-stage1` | 53 / 65 | 53 / 65 | ≥ 53 | ✅ met |
| Valgrind ERRORS | 14 | 5 | ≤ 6 | ✅ met |
| ASan ASAN_ERROR | 9 | 0 | 0 | ✅ stretch hit |
| Valgrind WARNINGS_ONLY | 51 | 60 | — | (+9, expected: errors demote to warnings) |
| ASan CLEAN | 45 | 54 | — | (+9, one-to-one with ERROR closures) |
| Pytest (non-bootstrap) | 38 fail / 5088 pass | 38 fail / 5088 pass | no new fails | ✅ byte-identical failure set |
| Pytest (bootstrap) | 13 fail / 212 pass | 13 fail / 212 pass | no new fails | ✅ byte-identical failure set |
| `libmapanare_rt.a` | unchanged | unchanged | byte-identical | ✅ (runtime/ untouched) |

All 9 Sh.2 String-residual tests (10_result, 19_nested_match,
41_module_let, 42_module_let_string, 43_module_let_math,
47_try_operator, 48_match_nested_exhaustive, 54_const_basic,
58_const_scope) are **clean under both valgrind and ASan**. The 5
remaining valgrind ERRORS are `26_generics`, `29_generic_impl`,
`30_nested_generics`, `31_generic_multi` (all "Conditional jump or
move depends on uninitialised value"), and `32_generic_enum`
("Invalid read of size 8") — the Ge.1 generics-initialization class
documented as out-of-scope in `PLAN.md`. The 11 ASan CRASH_NO_ASAN
are the Sh.4/Sh.6/Sh.7 feature-gap goldens (async / tensor /
closure-typed) — not memory-safety bugs.

## Exit criteria scorecard

| # | Check | Target | Stretch | Result | Status |
| --- | --- | --- | --- | --- | --- |
| 1 | Phase 1 repro matches v4.131.0 shape (String analog) | yes | — | Confirmed: `bind_one_pattern_field` concat → drop-glue free → read in `emit_enum_payload` | ✅ |
| 2 | Fix implemented, ~10-20 lines | yes | — | 12 logic lines + 8-line comment block | ✅ |
| 3 | Valgrind ERRORS | ≤ 6 | ≤ 3 | 5 (all out-of-scope Ge.1) | ✅ target met |
| 4 | ASan findings | 0 | 0 | 0 | ✅ stretch hit |
| 5 | Goldens | ≥ 53 | ≥ 58 | 53 | ✅ target met |
| 6 | Pytest regressions | 0 | 0 | 0 (38 non-bootstrap + 13 bootstrap — byte-identical) | ✅ |
| 7 | `libmapanare_rt.a` byte-identical | yes | — | runtime/ untouched | ✅ |

## Sanitizer artifacts

- `docs/roadmap/v4/v4.132.0/valgrind-summary.tsv` — per-test (66 rows)
- `docs/roadmap/v4/v4.132.0/asan-summary.tsv` — per-test (66 rows)

## Diff stat

```
mapanare/emit_llvm_text.py                              | +20 -0 (this release: STR branch of _do_copy)
docs/roadmap/v4/v4.132.0/SESSION_REPORT.md              | new
docs/roadmap/v4/v4.132.0/asan-summary.tsv               | new
docs/roadmap/v4/v4.132.0/valgrind-summary.tsv           | new
CHANGELOG.md                                            | <release entry appended>
VERSION                                                 | 4.131.0 → 4.133.0
```

1 code file touched. No C runtime changes. No self-hosted `.mn`
source changes. Zero risk to the bootstrap path.

## Carry-forward

| Docket | Status | Disposition |
| --- | --- | --- |
| Sh.2 String-residual | **CLOSED** | This release |
| Sh.2 LIST branch | CLOSED (v4.131.0) | — |
| **Ge.1** generics-init (new) | OPEN | v4.133.0+; 5 valgrind ERRORS (26_generics, 29_generic_impl, 30_nested_generics, 31_generic_multi, 32_generic_enum) |
| An.1 test hygiene | OPEN | v4.133.0 (per v4.132.0 PLAN "After") |
| Sh.11 fixed-point blocker | OPEN | v4.134.0 track |
| Sh.4/5/6/7 feature gaps | OPEN | v5.x track |
| Panel (v5 gate attempt 3) | DEFERRED | v4.136.0 (shifted from v4.135.0 per PLAN post-v4.132.0 note) |

## What this release does NOT do

- Touch the 4 "Conditional jump uninit" generics tests + 1 "size 8"
  generic-enum test — they are a distinct bug class (Ge.1), out of
  scope per PLAN §4 exit criteria note.
- Touch An.1, Sh.11, or any feature-gap docket.
- Add any self-hosted `.mn` changes. The fix lives entirely in the
  Python emitter.
- Re-run the panel.

## Next

Per PLAN "After v4.132.0": fix landed clean with all 9 tests closing
→ **v4.133.0 opens An.1 test hygiene** (38 pre-existing non-bootstrap
failures + 13 bootstrap failures, 6 families).
