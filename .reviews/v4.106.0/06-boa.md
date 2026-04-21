# Boa v4.106.0 Review — Developer Experience

## Score: 8.5/10
## Verdict: PASS

## Context: v4.99.0 → v4.106.0

At v4.99.0 I graded 7.5/10 PASS WITH NOTES on three UX items: binary-corruption
disclosure in README / `build_from_seed.sh` (#6), list indexing (#2), and
async-specific error messages (#11). Two have since been genuinely closed by
the underlying fix shipping; the third (#11) remains open but was always
slated for later. The star of this release for my lens is the Phase 4 crash
breadcrumb handler.

## Item #6 — Binary-corruption disclosure

**SUPERSEDED.** Corruption fix shipped in v4.101.0 via `_move_resource` at
6 sites in `emit_llvm_text.py` (12 occurrences, verified). I checked both
surfaces:

```
$ grep -in "corrupt\|known issue" README.md scripts/build_from_seed.sh
(no matches)
```

README contains no stale warning. `build_from_seed.sh` is clean. The
disclosure item lost its reason to exist the moment v4.101.0 landed, and
the docs correctly reflect that. Closing this item is the right call.

## Crash diagnostics (v4.105.0 Phase 4) — MASSIVE improvement

Reproduced the new output live:

```
$ ./mapanare/self/mnc-stage1 tests/golden/03_function.mn
[CRASH] SIGSEGV during compile at tests/golden/03_function.mn
./mapanare/self/mnc-stage1[0x731d53]
/lib/x86_64-linux-gnu/libc.so.6(+0x45330)[0x7f4e1f50f330]
./mapanare/self/mnc-stage1(mir_opt__block_successors+0xc1)[0x689a01]
```

Pre-v4.105.0 line 1 was `[CRASH] Signal 11 at:` — no source file, no phase,
opaque signal number. The new first line tells me:

1. **Symbolic signal name** (`SIGSEGV`, not `Signal 11`).
2. **Compiler phase** (`during compile` — distinguishing startup vs
   shutdown vs actual compilation crashes).
3. **Which source file** the compiler was eating when it died.

Three actionable facts from the first line. This is the textbook
before-and-after a DX review wants. It's also AS-safe (`write(2)` +
hand-rolled int format + `backtrace_symbols_fd`), with the one documented
trade-off on glibc's `backtrace()` first-call lazy-load — disclosed up front
in `PHASE4_BREADCRUMBS.md`. That kind of honest caveating is the right
tone. Claim 19 VERIFIED in the pre-panel audit.

## Error messages overall

Python bootstrap errors are good. `51_match_guards_and_or` produced:

```
tests/golden/51_match_guards_and_or.mn:3:19: error: or-pattern alternatives
must bind the same names: extra ['None']
  |
3 |         Some(0) | None => "zero or absent",
  |                   ^^^^
```

File, line, column, underline, specific diagnostic. Rust-style. The
`diagnostics.py` infrastructure is paying its rent.

## Item #11 — Async-specific error messages — STILL OPEN

```
$ ./mapanare/self/mnc-stage1 tests/golden/55_async_basic.mn
tests/golden/55_async_basic.mn:0:0: error: Undefined function 'block_on'
```

Three problems: (a) `0:0` position is a lie — `block_on` is on a real line,
(b) "Undefined function" is wrong diagnosis — `block_on` *is* defined in
the Python bootstrap, it's just not yet known to the stage1 self-hosted
semantic checker, (c) no hint that the user should fall back to
`python3 -m mapanare run` for async. A developer hitting this after reading
an async tutorial will conclude the language is broken rather than "the
self-hosted compiler doesn't know this builtin yet." This is exactly what I
flagged in v4.99.0 and it's untouched. OPEN, docket #11 still valid.

## Findings

- Crash handler UX: A-grade work. The breadcrumb API is the foundation to
  later emit per-function granularity from `.mn` (noted by Phase 4 as
  future work). Correct scope for this release.
- README / `build_from_seed.sh` disclosure hygiene: clean.
- Bootstrap error messages: production quality.
- Stage1 error messages for unsupported features: still rough.

## Docket items I would open

| # | Item | Severity |
|---|---|---|
| Bo.1 | Async errors in stage1 should say "feature not yet supported in self-hosted compiler; fall back to Python bootstrap" rather than "Undefined function" | MEDIUM |
| Bo.2 | Position `0:0` in stage1 semantic errors masks the real source line — regression vs bootstrap | MEDIUM |
| Bo.3 | (future) Emit `__mn_set_current_source(file, line)` from `.mn` at function entry for per-function crash granularity | LOW |

## Grade justification

Up from 7.5 → 8.5. Plus 1.0 for the crash handler (first-line actionable,
AS-safe, honestly documented), plus 0.5 for item #6 being genuinely
resolved and docs tracking reality. Minus 0.5 held back because item #11 is
still raw and `0:0` position loss in stage1 is a regression I hadn't
previously seen. PASS — the dev-facing surface is materially better than
at v4.99.0.

## One-line summary

Crash handler is a clear UX win, corruption disclosure no longer needed,
async errors still tell developers the wrong story.
