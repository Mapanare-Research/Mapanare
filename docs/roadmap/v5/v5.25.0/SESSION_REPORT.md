# v5.25.0 Session Report — Pv.* — CI prevention infrastructure

**Status:** READY (not tagged).
**Date:** 2026-05-02.
**Prerequisite:** v5.24.1 shipped (HEAD `e3cde77`).
**Effort:** 1 session. **Theme:** structural prevention layer.

---

## Headline

Opens the new **Pv.\*** sub-arc. Structural pattern parallel to
v5.24.0's **Hy.\***: every gate Pv.\* adds is an instance of the
same rule — **a feature is not done until at least one test
exercises it end-to-end from the .mn-caller side AND that test
runs on Linux pytest, not just on Windows pytest with a stale
local artifact**.

Closes the class of failure that produced two prerequisite
bugfixes between v5.24.1 and v5.25.0:

- `9dcbbb5` — `_find_runtime_lib` returned `None` because
  `mapanare/test_runner.py` still listed v3.x-era
  `libmapanare_core.*` candidate names; stale local archive
  masked it on Windows for 11+ releases.
- `9dcbbb5` — `__mn_indent_to_braces` brace-only fast path
  returned the input MnString aliased; double-free at
  function-end drop glue, surfaces only under valgrind / ASan.

Both bugs were caught on fresh-checkout CI; both could have been
caught locally. v5.25.0 adds the structural gate so the next
instance of the class fails at PR time.

**Zero compiler edits. Zero runtime edits. Zero
`mapanare/self/*.mn` source edits.** Strict 3-stage fixed point
preserved by construction at **239,835 lines / 0 diff** (20-release
strict streak; same line count as v5.24.1 — no source under
`mapanare/self/` changed). Goldens **95/95**.

---

## Items shipped

### Pv.1 — runtime-lib lookup regression test

`tests/test_runtime_lib_lookup.py` (~115 LOC, 3 cases).

Sweeps any `libmapanare_core.*` shadow artifacts in the candidate
dirs before invoking `_find_runtime_lib()` so a v3.x leftover
cannot mask a regression. Asserts:

1. `_find_runtime_lib()` returns a real, existing file.
2. The resolved name contains `rt` or `runtime` — defends against
   re-introduction of `libmapanare_core.*` (which has neither
   substring).
3. clang can link a tiny IR fragment that references
   `__mn_str_eq` against whatever archive the lookup returned.
   This is the load-bearing assertion: a test that just checks
   `_find_runtime_lib() is not None` would not catch a regression
   pointing at an empty or stale archive.

**Falsifiability round-trip (documented in the module docstring,
verified in this session):**

```
# Revert mapanare/test_runner.py to the pre-9dcbbb5 candidate list
# (libmapanare_core.{a,so,dll}). All 3 tests RED.
pytest tests/test_runtime_lib_lookup.py -v
# Restore. All 3 tests GREEN.
```

### Pv.2 — preprocess valgrind smoke test

`tests/bootstrap/test_preprocess_memcheck.py` (~115 LOC, 3
parameterized cases: brace-only, colon-only, mixed).

Runs `mnc-stage1 preprocess` on each fixture under valgrind with
`--leak-check=full` and `--show-leak-kinds=definite`. Two
assertions in order:

1. No generic heap-error pattern in stderr (`Invalid free`,
   `Invalid read`, `Invalid write`, `Use of uninitialised value`,
   `Mismatched free`, `double free`, `heap-use-after-free`).
2. No leak chain or error references `__mn_indent_to_braces` —
   mirrors v5.23.1 Mb.3's `sanitizer-mnc-stage1` grep pattern;
   catches future MnString lifecycle regressions in the indent
   preprocessor whether they manifest as a leak or a heap error.

**Why not `--error-exitcode=1`:** `mnc-stage1` has a pre-existing
single-shot leak from `__mn_argv` (~71 bytes, known and tracked
since v5.23.1 Mb.3). That leak is bounded to one fire per process
and is unrelated to the `__mn_indent_to_braces` lifecycle class.
Direct exit-code gating would conflate the two.

**Falsifiability round-trip (verified in this session):**

```
# Edit runtime/native/mapanare_core.c::__mn_indent_to_braces
# fast-path: replace ``return __mn_str_from_parts(src, n_src);``
# with the pre-9dcbbb5 ``return source;`` aliasing.
make build-rt && python3 scripts/build_stage1.py
pytest tests/bootstrap/test_preprocess_memcheck.py -v
# brace_only RED with `Invalid free` referencing
# __mn_indent_to_braces in the call chain. colon_only / mixed
# stay GREEN (they take the slow path which doesn't alias).
# Restore fresh-copy. All 3 tests GREEN.
```

### Pv.3 — `make ci-gates` extension

New `clean-build-test` sub-gate (9 sub-gates total, up from 8 at
v5.24.0). Wired into `Makefile`:

```makefile
clean-build-test:
    @rm -f runtime/native/libmapanare_rt.a \
           runtime/native/libmapanare_runtime.so \
           runtime/native/libmapanare_runtime.dylib \
           runtime/native/libmapanare_runtime.dll
    @$(MAKE) -s build-rt >/dev/null
    @pytest tests/test_at_test_runtime.py \
            tests/test_runtime_lib_lookup.py \
            -q --no-header --tb=short
```

The explicit `rm -f` is what makes the rebuild meaningful: `make
clean` alone does not touch
`runtime/native/libmapanare_*.{a,so,dylib,dll}`, so without the
`rm -f` the second `make build-rt` would reuse the existing
archive and the gate's premise (catching archive-rename drift)
would be unfalsifiable.

The pytest scope deliberately includes both
`test_at_test_runtime.py` (end-to-end mapanare-test → clang-link)
and `test_runtime_lib_lookup.py` (the Pv.1 unit lookup test) so
the gate covers both the integration and unit angles.

`make ci-gates` final state at v5.25.0 HEAD: **9/9 sub-gates
GREEN**.

### Pv.4 — WSL pre-push wrapper

Three artifacts.

`scripts/validate_wsl.sh` — strict-mode bash script that resolves
the repo root from its own location (so `wsl -d Ubuntu bash -c`
running in `$HOME` doesn't break the `cd`), runs `make build-rt`,
rebuilds `mnc-stage1` via `python3 scripts/build_stage1.py`, and
execs `pytest tests/ -x -n auto --tb=short`.

`dev.ps1 validate-wsl` — new mode added to the existing
`ValidateSet` and dispatch switch. Resolves the repo's WSL path
via `wsl -d Ubuntu wslpath -a "$Root"` and forwards stdout/stderr.

`scripts/hooks/pre-push.sample` — opt-in hook template (commented
header explains how to enable). Resolves `validate_wsl.sh` from
its own location so the hook works whether copied or symlinked
into `.git/hooks/`. Not enabled by default — forcing the full
Linux pytest suite on every push kills the dev loop and produces
resentment, not safety.

### Pv.5 — CLAUDE.md cleanup

Single edit: deleted the v5.13.1 "Planned / in-progress" entry.
The runtime-lib wiring (At.1's only remaining open item from the
v5.13.0-prep audit) shipped on `dev` between v5.24.1 and v5.25.0
as commit `9dcbbb5`. The `@test` runtime is fully functional
end-to-end on both Python and native paths; nothing left to plan
under v5.13.1.

`grep -nE "v5\.13\.1" CLAUDE.md` returns 0 hits at v5.25.0 HEAD.

### Pv.6 — publish-pipeline smoke fixture fix

Two parts.

**YAML edit:** `.github/workflows/publish.yml` Linux + macOS
tarball-smoke fixtures rewritten from
`echo 'fn main(): print("...")' > /tmp/hello.mn` to a
`printf 'fn main():\n    print(...)\n' > /tmp/hello.mn`
multi-line colon shape. Single-line `fn x(): y` was the v5.14.0
SPEC §1009 forward promise that v5.21.1 H.4 explicitly rescoped
to v6.0; the fixture was authored against an unshipped feature
and broke the publish pipeline at run #48.

**Local gate:** `tests/test_publish_smoke_fixtures.py` (~135 LOC,
2 cases) extracts every inline `.mn` fixture from `publish.yml`
across four shapes — bash `echo`, bash `printf`, PowerShell
here-string, and bash `cat <<EOF` heredoc — and parses each
through `mapanare.parser.parse`. The first test asserts at least
4 fixtures were extracted (guards against a regex update that
silently drops every fixture, which would pass the parse loop
trivially). The second asserts every fixture parses.

**Five fixtures locked at v5.25.0 HEAD:**

| Target | Shape | Body |
|---|---|---|
| `mnc_smoke.mn` | echo single-line | `fn main() { print("hello from mnc smoke") }` |
| `/tmp/hello.mn` | printf multi-line colon | Linux smoke |
| `/tmp/hello.mn` | printf multi-line colon | macOS smoke |
| `hello.mn` | PowerShell here-string brace | Windows SDK smoke |
| `hello.mn` | PowerShell here-string brace | Windows clean smoke |

**Falsifiability round-trip (verified in this session):**

```
# Revert publish.yml Linux smoke to single-line colon. The new
# test FAILs with the same parse error as publish run #48
# (Unexpected ':' — expected '->', '=', '{').
pytest tests/test_publish_smoke_fixtures.py -v
# Restore. PASS.
```

---

## Validation

| Check | Result |
|---|---|
| `make ci-gates` | 9/9 GREEN |
| `bash scripts/verify_fixed_point.sh` | stage2.ll == stage3.ll, **239,835 lines / 0 diff** |
| `python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1` | **95/95 PASS** |
| `pytest tests/test_runtime_lib_lookup.py` | 3/3 PASS |
| `pytest tests/bootstrap/test_preprocess_memcheck.py` | 3/3 PASS |
| `pytest tests/test_publish_smoke_fixtures.py` | 2/2 PASS |
| `pytest tests/test_at_test_runtime.py` (via clean-build-test) | green |

Strict 3-stage fixed-point streak now **20 releases** (v5.9.0 →
v5.25.0).

---

## Carry-forward delta

**Closed at v5.25.0:**

- v5.24.1 Pv-class follow-up — runtime-lib lookup contract
  unsealed; preprocess fast-path memory hygiene unsealed; both
  prerequisites for v5.25.0's gate work shipped on `dev` as
  `9dcbbb5` (Pv.1 + Pv.2 lock those bug classes).
- v5.13.1 placeholder retired (Pv.5).
- Publish-pipeline run #48 Linux + macOS tarball-smoke fixture
  failure (Pv.6 YAML edit + Pv.6 gate test).

**Inherits to v5.26.0:**

- **Mb.7** — i64/i1 tag-emit, 9 LINK_FAIL goldens. Deliberately
  out of scope for v5.25.0 (real codegen work; deserves its own
  release per PLAN).

**Inherits from v5.24.1 docket (~5 LOW open items):**
unchanged. The Pv.\* arc adds no new docket entries — it's a
prevention release, not a fix release.

---

## Out of scope (explicitly held)

- **Mb.7** — v5.26.0.
- `to_terse` empty `#{}` rewriter bug — v5.27.0.
- `mnc fmt` long-line wrap + import sort — v5.27.0.
- Docker builder-image diet — explicit user opt-out, indefinite.
- `act` for local CI replay — out of scope; the WSL wrapper
  closes 95% of the gap at 5% of the setup cost.

---

## Lessons / patterns

**Falsifiability is the contract.** Every Pv.\* test was
demonstrably failable: write the test, revert the corresponding
bugfix in `mapanare/test_runner.py` or
`runtime/native/mapanare_core.c` or `.github/workflows/publish.yml`,
confirm RED, restore, confirm GREEN. Without that round-trip the
test is unfalsifiable infrastructure that rots silently. Every
Pv.\* docstring documents the round-trip explicitly so the next
person to touch the file knows how to verify the lock still
locks.

**The clean-build-test sub-gate's `rm -f` matters.** Without it,
`make clean` leaves `libmapanare_rt.a` in place and the rebuild
is a no-op. The gate would still pass — but on the existing
archive, not a freshly-built one — defeating the entire point of
catching archive-rename drift. Cheap, but easy to get wrong.

**The Pv.2 grep-for-symbol pattern was load-bearing.** The first
draft used `--error-exitcode=1` and went RED on ALL 3 fixtures
because of the pre-existing `__mn_argv` single-shot leak. That
would have been a useless test — a 100% noise floor masks any
real signal. Mirroring v5.23.1 Mb.3's grep pattern restored
signal-to-noise to "any indent_to_braces reference is bad."

---

## Next release

**v5.26.0** — **Mb.7 — i64/i1 tag-emit fix.** Closes the 9
LINK_FAIL goldens (47, 48, 49, 51, 55–59). Real codegen work in
self-host `emit_llvm.mn`. v5.23.1 Mb.7 deferred-investigation
note documents the diagnosis; PLAN due in v5.26.0/.
