# Mapanare v4.132.0 — Sh.2 residual: String-field analog of v4.131.0 fix

> **Single-focus release.** v4.131.0 closed the LIST branch of the
> extracted-alias-with-drop-glue bug (53/65 goldens, 14 valgrind
> ERRORS, 9 ASan findings). The sanitizer sweeps show **all 9 remaining
> ASan findings AND all 9 valgrind "Invalid read size 1|2" ERRORS map
> to the same 9 tests, all classified as heap-use-after-free on String
> data** (MemcmpInterceptorCommon + __asan_memcpy frames). Same pattern
> as v4.131.0, different type. Fix is the STRING analog in `_do_copy`.

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v4.131.0
**Estimated work:** 1 sprint (fix is ~10 lines; verification is the bulk)
**Theme:** Close the other half of the extracted-alias bug class.

---

## Why v4.132.0 exists

v4.131.0's `_do_copy` fix handled `if t == LIST:`. The same bug exists
in `if t == STR` paths — a String extracted from a struct field
(`fe.ret_type`, `vi.value`, etc.) and Copy'd into a locally-tracked
String variable gets **freed by drop glue on the local**, invalidating
every other alias that the original FnEntry / VarInfo still holds.

## Evidence

9 tests fail identically on both sanitizers post-v4.131.0:

| Test | Valgrind | ASan |
|---|---|---|
| 10_result | Invalid read size 1\|2 | heap-UAF @ MemcmpInterceptorCommon |
| 19_nested_match | Invalid read size 1\|2 | heap-UAF @ MemcmpInterceptorCommon |
| 41_module_let | Invalid read size 1\|2 | heap-UAF @ __asan_memcpy |
| 42_module_let_string | Invalid read size 1\|2 | heap-UAF @ __asan_memcpy |
| 43_module_let_math | Invalid read size 1\|2 | heap-UAF @ __asan_memcpy |
| 47_try_operator | Invalid read size 1\|2 | heap-UAF @ MemcmpInterceptorCommon |
| 48_match_nested_exhaustive | Invalid read size 1\|2 | heap-UAF @ MemcmpInterceptorCommon |
| 54_const_basic | Invalid read size 1\|2 | heap-UAF @ __asan_memcpy |
| 58_const_scope | Invalid read size 1\|2 | heap-UAF @ __asan_memcpy |

Two sub-patterns in frame 0:
- `MemcmpInterceptorCommon` — String equality check reads freed String data
- `__asan_memcpy` — module-level `let x = foo()` copies freed String

Both are the same shape as Sh.2: a String owner's buffer is freed
while aliases still reference it.

## Phase 1 — Repro + IR inspection

- [ ] Run `10_result` under valgrind and ASan post-v4.131.0 mnc-stage1 build
- [ ] Dump the function containing the UAF (find frame 0 offset, match to symbol)
- [ ] Locate the `_do_copy` STRING path producing the premature `__mn_str_free`
- [ ] Verify the crash is analogous to v4.131.0's `reg_param_types.a.N` list-free pattern — this time on `str_track` allocas

## Phase 2 — Fix

In `mapanare/emit_llvm_text.py::_do_copy`, after the LIST branch,
apply the same logic to strings:

```python
if t == STR:
    # v4.132.0 Sh.2 String-residual fix: only track dest as owner
    # when src was a tracked owner. If src is an alias (from
    # field-get, enum-payload, function parameter), dest must not
    # be tracked — otherwise drop glue frees the aliased buffer.
    src_str_tracked = i.src.name in self._str_slots
    if src_str_tracked:
        # Ownership transfer
        slot = self._str_slots.pop(i.src.name)
        self._str_slots[i.dest.name] = slot
    else:
        # src is an alias; if dest was previously an owner, untrack it
        if i.dest.name in self._str_slots:
            self._str_slots.pop(i.dest.name)
```

The `_str_slots` registry is the String analog of `_list_vars`.
`_move_resource` (v4.101.0) uses it. Drop glue reads through it via
the tracking slot alloca.

**Caveat**: `_str_slots` maps name → tracking alloca. The tracking
alloca was written by `_track_string` as part of allocation. Moving
"ownership" between names is more subtle for strings than for lists
because the alloca's role is "zero to suppress drop glue" rather than
"holds the actual owner." Phase 1 inspection needs to verify the
correct mechanism before coding.

- [ ] Implement the fix
- [ ] Rebuild mnc-stage1
- [ ] Re-run 10_result — no UAF under valgrind or ASan
- [ ] Check `emit_llvm__emit_mir_call` IR for `__mn_str_free` call count — should drop

## Phase 3 — Verification sweep

- [ ] Golden test count through mnc-stage1 — target ≥ 53 (no regression); stretch ≥ 58
- [ ] Valgrind sweep — target ≤ 6 ERRORS (down from 14); stretch ≤ 3
- [ ] ASan sweep — target 0 ASAN_ERROR (down from 9); stretch 0
- [ ] Zero regressions vs v4.131.0 baseline
- [ ] Full pytest: no new failures vs v4.131.0 (38 failures baseline)
- [ ] `libmapanare_rt.a` byte-identical

## Phase 4 — Closeout

- [ ] `SESSION_REPORT.md` with honest delta numbers
- [ ] `CHANGELOG.md [4.132.0]` entry
- [ ] Update `docs/roadmap/v4/README.md`, `ROADMAP.md`, CLAUDE.md
- [ ] Bump VERSION to 4.133.0

---

## Exit criteria

| # | Check | Target | Stretch | Downside |
|---|---|---|---|---|
| 1 | Phase 1 repro matches v4.131.0 shape (String analog) | yes | — | if different → re-scope |
| 2 | Fix implemented, ~10-20 lines | yes | — | if structural → ship partial + continue |
| 3 | Valgrind ERRORS | ≤ 6 | ≤ 3 | > 10 → fix incomplete |
| 4 | ASan findings | 0 | 0 | > 3 → wrong fix class |
| 5 | Goldens | ≥ 53 (no regression) | ≥ 58 | < 53 → revert |
| 6 | Pytest regressions | 0 | 0 | any → revert |
| 7 | `libmapanare_rt.a` byte-identical | yes | — | any change → document |

The 4 "Conditional jump uninitialised" tests (26_generics,
29_generic_impl, 30_nested_generics, 31_generic_multi) and the 1 "size
8" test (32_generic_enum) are **out of scope for v4.132.0** — they're
a generics-initialization bug class, not Sh.2. Documented for v4.133.0+
track as new docket **Ge.1**.

---

## What this release does NOT do

- Close the generics uninitialised-read bucket (Ge.1 — v4.133.0+)
- Touch An.1 (38 pytest failures — v4.133.0)
- Touch Sh.11 (fixed-point blocker — v4.134.0)
- Re-run the panel (deferred to v4.136.0)
- Re-scope if Phase 1 shows the bug is wider — that becomes v4.132.1 or a deferral, not a sprawl

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| `_str_slots` doesn't work the same way as `_list_vars` | medium | high | Phase 1 inspection verifies mechanism before coding |
| Fix closes some but not all 9 tests | medium | medium | Accept partial close; scope v4.132.1 or v4.133.0 for residual |
| Fix breaks existing String drop-glue semantics | low | high | Full pytest + golden sweep before commit; revert if regression |
| Generics uninitialised class turns out to be same root cause | low | medium | If Phase 1 shows it, expand scope; otherwise defer to Ge.1 |

---

## After v4.132.0

If v4.132.0 lands clean (valgrind ≤ 6, ASan 0, ≥ 58 goldens): v4.133.0
opens An.1 test hygiene.

If v4.132.0 lands partial: v4.133.0 continues residual sanitizer
closures; An.1 shifts to v4.134.0.

Panel target remains v4.136.0.
