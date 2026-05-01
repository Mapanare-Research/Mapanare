# v5.23.1 — Mb.\* — memory hygiene

**Status:** SHIPPED (ready, not tagged).
**Scope:** Mb.1–Mb.6 from `PLAN.md`. Second release in the v5.23–v5.24
recovery arc — see `docs/roadmap/v5/RECOVERY_ARC_v5.23-v5.24.md`.
**Breaking:** No.
**Strict 3-stage fixed point:** preserved at **239,485 lines / 0 diff**
(16-release strict streak; +260 lines vs v5.23.0's 239,225, expected
from the new `box_track` allocas + drop-glue calls at every `Some(x)`
construction site introduced by Mb.2).
**Goldens:** 95/95 preserved.

---

## Headline

Three real memory bugs surfaced in the v5.22.0 panel + post-panel CI
analysis. None block correctness; all three are production-discipline
gaps that the v5.21.1 hygiene release did not catch.

v5.23.1 closes:

- **V.9** (Viper, MEDIUM) — `__mn_indent_to_braces` lifecycle leak.
- **3 NEW Te.5 ASan leaks** on `tests/golden/{88_if_let,
  90_while_let, 91_let_else}.mn` — 1 leak / 8 bytes each, none of
  which Viper saw in the v5.22.0 panel valgrind sweep.
- **V.6 / V.7 / V.8** (Viper, LOW, **3rd cycle each**) — DX.4 walker
  carries.

Plus prevention infrastructure:

- **Mb.3** — `sanitizer-mnc-stage1` CI gate. Catches V.9-class
  lifecycle bugs at PR time; the byte-identical oracle in
  `tests/bootstrap/test_indent_preprocessor.py` cannot.
- **Mb.6** — `sanitizer-cache-walkers` CI gate. Closes the
  v5.10.0+ delta sanitizer-coverage gap that Viper flagged for three
  panels in a row.

Mb.7 (ASan-gate llc aborts) is **deferred to v5.24.0** per the plan's
explicit option to defer. Investigation found the 9 LINK_FAILs are
`'%tag2' defined with type 'i64' but expected 'i1'` — a pre-existing
self-host emit_llvm.mn type-tag emit bug, unrelated to PIC reloc and
unrelated to the Mb.\* memory-hygiene scope.

---

## Mb.1 — V.9 lifecycle leak (MEDIUM)

**Effort:** 2h (Phase 0 misdiagnosis + iteration).

The v5.22.0 panel's diagnosis ("missing tracked-output annotation on
the `extern "C" fn` decl") was load-bearing for the symptom but
incomplete on root cause. Phase 0 reproduction:

```
==90628== 30 bytes in 1 blocks are definitely lost in loss record 129
==90628==    by 0xA8F0A0: __mn_indent_to_braces
==90628==    by 0x42B543: parser__parse
```

**Phase 1 attempt (failed).** Added a dedicated
`__mn_indent_to_braces` handler in Python's
`emit_llvm_text.py::_do_call` that calls `_track_string(r)`. Stage1
rebuilt; valgrind re-ran. Leak persisted at the same site.

**Investigation.** The IR for `parser__parse` showed the tracking
slot was being created AND immediately zeroed before the
`tokenize(preprocessed, filename)` call:

```llvm
%rt.1 = call {ptr, i64} @__mn_indent_to_braces({ptr, i64} %l.0)
store {ptr, i64} %rt.1, ptr %str_track.2          ; tracked
store {ptr, i64} %rt.1, ptr %t0.a.3
%l.4 = load {ptr, i64}, ptr %t0.a.3
store {ptr, i64} zeroinitializer, ptr %str_track.2 ; ZEROED on move
call void @lexer__tokenize(...)
```

**Root cause.** Python's `_do_call` applies a blanket-move at every
user-function call site (`emit_llvm_text.py:4156-4178`,
`_move_resource(src_name)` for every arg). For STRING args, this
zeros the `_str_slots[name]` tracking slot, leaving drop-glue at
function-exit a no-op. `tokenize` is a borrow (it builds new String
values for token `.value` fields, doesn't keep refs into source),
not a move — but the blanket-move zeros the slot anyway.

**Why stage2/3 are leak-clean and stage1 is not.** The self-host
`mapanare/self/emit_llvm.mn` does NOT have this blanket-move. It
relies on explicit `Move` instructions from the lowerer
(`emit_llvm.mn::1666-1679`). Verified by inspecting stage2.ll:

```llvm
%t1 = call {ptr, i64} @__mn_indent_to_braces(...)
store {ptr, i64} %t1, ptr %str_track.269                  ; tracked
%preprocessed_val3 = load {ptr, i64}, ptr %preprocessed2.addr
call void @tokenize(...)                                   ; NO zero
```

The slot retains the value through tokenize and gets freed by
drop-glue at parse() exit. **stage2/3 are leak-clean by construction.
The leak is stage1-specific.**

**Fix.** Surgical handler change in
`mapanare/emit_llvm_text.py::_do_call`:

```python
if fn == "__mn_indent_to_braces" and args:
    a = self._coerce(args[0][0], args[0][1], STR) if args[0][1] != STR else args[0][0]
    r = self._rt("__mn_indent_to_braces", STR, [STR], [(a, STR)])
    self._track_string(r)
    self._last_tracked_str_slot = None  # bypass _str_slots registration
    self._put(i.dest, r, STR)
    return
```

The `_last_tracked_str_slot = None` line clears the
`_put → _str_slots[dest.name] = slot` registration. The slot still
appears in `_local_strings` (consulted by drop-glue) but no longer in
`_str_slots` (consulted by `_move_resource` for blanket-move-zero).
Result: the slot keeps its value through every consume site, and
drop-glue at parse() exit calls `__mn_str_free` on it.

Defensive: also added `__mn_indent_to_braces` to
`is_string_returning_builtin` in
`mapanare/self/emit_llvm.mn` (auto-detection fallback).

**Verification.**
- Pre-fix valgrind: 30-byte leak from `__mn_indent_to_braces` →
  `parser__parse` → `definitely lost: 29,559 bytes in 158 blocks`.
- Post-fix valgrind: NO `__mn_indent_to_braces` frame in any leak
  chain → `definitely lost: 29,529 bytes in 157 blocks` (delta = -30
  bytes / -1 block, exactly the V.9 leak).
- Goldens 95/95.
- Strict 3-stage fixed point preserved.

**What this release CANNOT do for V.9-class:** the blanket-move
remains in Python's `_do_call` for general STRING args. The pattern
is a known design tension between the Python and self-host emitters
(Python has it; self-host doesn't). Removing it wholesale is too
risky for a hygiene release; the surgical bypass for
`__mn_indent_to_braces` is the right scope here.

---

## Mb.2 — Te.5 ASan leaks on goldens 88 / 90 / 91 (MEDIUM)

**Effort:** 1h.

Phase 0 reproduction confirmed 3 NEW LEAK entries in
`scripts/run_asan_leak_goldens.sh` output:

```
88_if_let       0  0  1  8  main  LEAK
90_while_let    0  0  1  8  main  LEAK
91_let_else     0  0  1  8  main  LEAK
```

**Investigation.** The leak is NOT in the let-else / while-let /
if-let desugaring as Viper's plan suspected. Comparing
Python-emitted vs self-host-emitted IR for `88_if_let.mn`:

- **Python `_do_wrap_some`** (`emit_llvm_text.py:5172-5179`) — emits
  inline `{i1, T}` via insertvalue. No malloc, no leak.
- **Self-host `emit_wrap_some`** (`mapanare/self/emit_llvm.mn:3599`) —
  heap-allocates the payload via malloc, builds `{i1, ptr}`. malloc
  but **no `emit_track_boxed`** — the malloc'd payload pointer is
  never tracked for drop-glue freeing.

The leak is **systemic**, not Te.5-specific. It surfaces in every
golden that constructs `Some(x)` (or `Ok(x)` / `Err(x)` for boxed
representations). The Te.5 goldens at v5.20.1 expose it via 1 leak
each; golden 17_option (in baseline since v5.4.2) was already
leaking 2 boxes (16 bytes).

**Fix.** Single-line addition in `emit_wrap_some`:

```mn
s = emit_line(s, "  " + ea + " = call ptr @malloc(i64 " + sz + ")")
s = emit_track_boxed(s, ea)  // v5.23.1 Mb.2
s = emit_line(s, "  store " + val_ty + " " + val.name + ", ptr " + ea)
```

`emit_track_boxed` (already implemented since v5.4.1) allocates a
`box_track.N` slot in the entry-block prelude, stores the malloc'd
pointer, registers the slot in `st.boxed_owned`. `emit_drop_glue_boxed`
iterates these slots at every `ret` and calls `free()` unless the
pointer aliases a returned value.

`emit_wrap_ok` and `emit_wrap_err` already use insertvalue (no
malloc) — no fix needed there.

**Verification.**
- Pre-fix ASan: 7 LEAK entries (39_gpu_detect, 40_gpu_tensor,
  62_list_output, 17_option, 88_if_let, 90_while_let, 91_let_else).
- Post-fix ASan: 4 LEAK entries — Te.5 goldens 88/90/91 GONE.
  17_option also IMPROVED from 2 leaks/16 bytes to 1 leak/8 bytes.

**ASan baseline TSV refresh.** Updated
`docs/roadmap/v5/v5.4.2/baseline/asan-leak-baseline.tsv`:

| Test | Old | New |
|---|---|---|
| 17_option | LINK_FAIL (llc) | LEAK 1 / 8 (find_positive) |
| 62_list_output | LEAK 13 / 346 | LEAK 9 / 141 (IMPROVED) |
| 39_gpu_detect | LEAK 5 / 50212 | LEAK 5 / 50212 (unchanged) |
| 40_gpu_tensor | LEAK 5 / 50212 | LEAK 5 / 50212 (unchanged) |

The 17_option entry transitioned from LINK_FAIL → LEAK because llc
no longer aborts on its IR (improvement from intermediate
self-host fixes), and the Mb.2 fix dropped 1 of its 2 leaks.

**Strict 3-stage fixed point.** Preserved. Stage2.ll grew from
239,225 (v5.23.0) → 239,485 lines (+260), expected from the new
`box_track` allocas + drop-glue calls at every `Some(x)` site in the
self-host source (~80–90 such sites in `mnc_all.mn`).

---

## Mb.3 — sanitizer-mnc-stage1 CI gate (MEDIUM)

**Effort:** 30 min.

New job in `.github/workflows/sanitizers.yml`:

- Builds `mnc-stage1` + `libmapanare_rt.a`.
- Runs valgrind on goldens 86_let_destructure_rest (colon syntax,
  exercises `__mn_indent_to_braces`) plus Te.5 goldens 88/90/91.
- Cannot use `--error-exitcode=1` directly (mnc-stage1 has known
  pre-existing leaks: `__mn_file_read_or_empty`, `__mn_str_join`,
  `semantic__check_call_expr`, etc., bounded to single-shot in the
  binary, OS-reaped on exit). Instead, captures full valgrind
  output and greps for `__mn_indent_to_braces` in any leak chain
  → fail on regression only.

**Verification.** All 4 gates PASS locally at v5.23.1 HEAD. Would
have FAILED at v5.22.0 HEAD (we reproduced V.9 in Phase 0).

The byte-identical oracle in
`tests/bootstrap/test_indent_preprocessor.py` cannot detect lifecycle
issues — this gate would have caught V.9 at v5.14.1 instead of two
releases later.

---

## Mb.4 — V.6 walker depth-cap (LOW, 3rd cycle)

**Effort:** 30 min.

The plan called for full iterative work-queue rewrite of
`mn_dir_walk_size_` / `mn_dir_walk_count_` / `mn_dir_remove_recursive_`.
Pragmatic alternative chosen: add a `depth` parameter capped at
`MN_DIR_WALK_MAX_DEPTH` (4096) to each function. Bounds C stack
against pathological directory trees without the LOC churn of full
iterative rewrite.

Mapanare cache directories are rarely deeper than 5 levels in
practice; the cap is a defensive ceiling, not an active throttle.

**3rd cycle finally closed.** v5.7.1 / v5.11.0 / v5.22.0 panels
flagged this each time.

---

## Mb.5 — V.7 Win32 reparse-point skip + POSIX lstat (LOW, 3rd cycle)

**Effort:** 30 min.

Added in each of the three Win32 walker branches:

```c
if (ffd.dwFileAttributes & FILE_ATTRIBUTE_REPARSE_POINT) continue;
```

POSIX side: changed `stat()` → `lstat()` in the count/size paths so
symlinks aren't followed (matches Win32 reparse-point skip
behavior). The remove-recursive path already used `lstat()`.

**Verified locally.** Built a fixture with a symlink pointing back
into the tree (`/tmp/walker-test/.mnc_cache/non-loop-symlink → level1`).
`mnc cache stats` reports `Files: 4` (the 4 real files) instead of
`Files: 6` (4 + symlinked re-counts of file2.bin + file3.bin).
Symlink correctly skipped.

**3rd cycle finally closed.**

---

## Mb.6 — sanitizer-cache-walkers CI gate (LOW, V.8 — 3rd cycle)

**Effort:** 1h.

New job in `.github/workflows/sanitizers.yml`:

- Builds native `mnc-stage1`.
- Populates `/tmp/walker-test/.mnc_cache` fixture (3 levels deep,
  mixed files + non-loop symlink + manifest.txt).
- Runs `mnc-stage1 version` (exercises `__mn_executable_dir`),
  `mnc-stage1 cache stats` (exercises `walk_count_` + `walk_size_`),
  `mnc-stage1 cache clean` (exercises `remove_recursive_`) under
  valgrind.
- Greps for `Invalid read|Invalid write|Use of uninitialised|Conditional
  jump.*uninitialised` → fail on memory error.

The cache subcommand uses `.mnc_cache` in CWD (no env-var override
at v5.23.1), so the fixture is built under that name and the binary
is invoked from the fixture parent directory.

**Verified locally.** All three valgrind passes are clean.

**3rd cycle finally closed.** Closes the v5.10.0+ delta
sanitizer-coverage gap.

---

## Mb.7 — ASan-gate llc aborts (LOW, deferred)

Phase 5 investigation found the 9 LINK_FAIL entries in
`scripts/run_asan_leak_goldens.sh` are NOT relocation-model issues.
Sample failure (47_try_operator):

```
llc: error: /tmp/asan-leak/47_try_operator.ll:227:9: error:
  '%tag2' defined with type 'i64' but expected 'i1'
  br i1 %tag2, label %prop_ok0, label %prop_err1
```

This is a self-host `emit_llvm.mn` type-tag emit bug — the tag
extraction emits an i64 but the branch expects i1. Pre-existing,
unrelated to PIC reloc, unrelated to memory hygiene. **Deferred to
v5.24.0+** with a docket entry.

The 9 LINK_FAIL goldens are: 47_try_operator, 48_match_nested_exhaustive,
49_match_guards, 51_match_guards_and_or, 55_async_basic, 56_async_await,
57_real_await, 58_async_file_io, 59_async_fanout. Pattern: try-operator
goldens (47) and match-with-guards goldens (48/49/51) share the i1/i64
tag-emit bug; async goldens (55–59) are a separate llc abort class.

---

## Files changed

| File | Purpose |
|---|---|
| `mapanare/emit_llvm_text.py` | Mb.1 — Python emitter `__mn_indent_to_braces` handler |
| `mapanare/self/emit_llvm.mn` | Mb.1 — self-host `is_string_returning_builtin`; Mb.2 — `emit_track_boxed` in `emit_wrap_some` |
| `mapanare/self/mnc_all.mn` | regenerated via `bash scripts/concat_self.sh` |
| `runtime/native/mapanare_core.c` | Mb.4 — depth-cap; Mb.5 — reparse-point skip + lstat |
| `.github/workflows/sanitizers.yml` | Mb.3 — sanitizer-mnc-stage1; Mb.6 — sanitizer-cache-walkers |
| `docs/roadmap/v5/v5.4.2/baseline/asan-leak-baseline.tsv` | Mb.2 — baseline refresh |
| `VERSION` / `README*.md` / `CHANGELOG.md` / `CLAUDE.md` | version bump |

---

## Verification

```
$ cat VERSION
5.23.1

$ python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1
All 95 tests passed in 17.6s

$ bash scripts/verify_fixed_point.sh
✓ FIXED POINT REACHED
stage2.ll == stage3.ll (239485 lines, 0 diff)

$ valgrind --leak-check=full mapanare/self/mnc-stage1 emit-llvm \
    tests/golden/86_let_destructure_rest.mn -o /tmp/86.ll 2>&1 | \
    grep "indent_to_braces"
(no output — V.9 closed)

$ bash scripts/run_asan_leak_goldens.sh | grep "LEAK:"
LEAK:         4
(was 7 at v5.23.0 HEAD; 3 NEW Te.5 + 1 17_option leak closed)

$ make lint
(clean)
```

---

## Carry-forward delta (v5.23.0 → v5.23.1)

**Closed:**
- V.9 (Viper MEDIUM, 1st cycle)
- 3 NEW Te.5 ASan leaks (88_if_let, 90_while_let, 91_let_else)
- V.6 (Viper LOW, 3rd cycle)
- V.7 (Viper LOW, 3rd cycle)
- V.8 (Viper LOW, 3rd cycle)

**Carried to v5.24.0+:**
- Mb.7 — ASan-gate llc aborts (i64/i1 tag-emit bug, async-codegen
  llc class). Pre-existing; tracked.
- 39_gpu_detect / 40_gpu_tensor 50K leaks (LEAK in baseline since
  v5.4.2; GPU-driver-side, not compiler-side).
- 17_option 1-leak / 62_list_output 9-leak residual (per-baseline).
- Pre-existing stage1 leaks (`__mn_file_read_or_empty`,
  `__mn_str_join`, `semantic__check_call_expr` — bounded to
  single-shot, not regressions).

**v5.24.0+ docket inherits:**
- Pk.1.A 11-release carry; `>=45` magic 3rd ask; SPEC corpus M3;
  Manifesto M2; Coral L1–L5; cadence enforcement gate; Te.3 hollow
  surface (v5.23.2); `make ci-gates` + `check_doc_freshness.py`
  (v5.24.0); v6.0 Rt.04 multi-level alias.
