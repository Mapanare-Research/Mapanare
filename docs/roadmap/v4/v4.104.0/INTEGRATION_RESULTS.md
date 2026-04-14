# v4.104.0 Phase 3 — Integration pipeline results (64/64 tests)

**Date:** 2026-04-13
**Pipeline:** `python3 -m mapanare emit-llvm` → `llvm-as` → `opt -O2` → `llc` → `clang -no-pie` (link against `libmapanare_rt.a`) → run.
**Runner:** `/tmp/run_integration.sh` (archived at `artifacts/integration-results.tsv`).
**Wall time:** 56 s for all 64 tests.

## Headline

**60 / 64 PASS** through the full LLVM 18.1.3 integration pipeline.

- **60 PASS** — IR emits, validates with `llvm-as`, survives `opt -O2`, lowers via `llc`, links, runs, exits 0.
- **2 SKIP** — require external input (see below).
- **2 FAIL** — two distinct pre-existing bugs in the Python bootstrap, neither caused by Phase A.

| Outcome | Count | Notes |
|---|---:|---|
| PASS | 60 | Full pipeline clean, exit 0 |
| SKIP — needs stdin | 1 | `35_stdin` (test reads from stdin; harness has none) |
| SKIP — needs network | 1 | `38_http` (test does an outbound HTTP call) |
| FAIL — emit step | 1 | `51_match_guards_and_or` |
| FAIL — llvm-as step | 1 | `47_try_operator` |
| FAIL — opt step | 0 | |
| FAIL — llc step | 0 | |
| FAIL — link step | 0 | |
| FAIL — runtime | 0 | |

## The two pipeline failures

### `51_match_guards_and_or` — FAIL at `emit` step

```
tests/golden/51_match_guards_and_or.mn:3:19: error: or-pattern alternatives must bind the same names: extra ['None']
  |
3 |         Some(0) | None => "zero or absent",
  |                   ^^^^
tests/golden/51_match_guards_and_or.mn:13:20: error: Undefined variable 'None'
  |
13 |     print(describe(None))
```

**Root cause:** The Python semantic checker's or-pattern binding rule
incorrectly fires on `Some(0) | None` because it treats `None` as a
variable binding, then complains that the arm introduces a name (`None`)
that isn't in the other alternative. `None` must be recognized as the
`Option::None` enum constructor, not as a binder.

**Severity:** MEDIUM — the pattern is legal Mapanare; the front-end
refuses to accept it. Not a Phase A fix; the v4.103.0 `else/sino` arc
touched the semantic checker for nested if/else, not match or-patterns.

**Docket candidate:** yes, for v4.106.0.

### `47_try_operator` — FAIL at `llvm-as` step

```
llvm-as: /tmp/v4_104_integration/47_try_operator.ll:93:13:
error: '%uw.11' defined with type '{ i64, { ptr, i64 } }' but expected 'i64'
  store i64 %uw.11, ptr %t3.a.12
            ^
```

**Root cause:** The Python emitter's `?`-operator lowering stores a
`Result<Int, String>` (type `{ i64, { ptr, i64 } }`) into a slot that was
declared with type `i64`. A type mismatch at the IR level — the bootstrap
never called `llvm-as` on this output so the bug has been latent since
the `?` operator shipped in v4.33.0.

**Severity:** HIGH — this test previously appeared PASS in the test-native
harness because the harness doesn't pipe through `llvm-as`; it only
inspects the string output. End-to-end integration rejects it.

**Docket candidate:** yes, for v4.106.0. First use-case for the
v4.105.0 debugging-infra release (sanitizer + llvm-as gate on every test).

## Step-by-step counts

Steps pass cumulatively — once a test fails at a step, downstream steps
aren't attempted.

| Step | PASS | FAIL | SKIP | Cumulative PASS |
|---|---:|---:|---:|---:|
| emit | 63 | 1 | 0 | 63 |
| llvm-as | 62 | 1 | 0 | 62 |
| opt -O2 | 62 | 0 | 0 | 62 |
| llc | 62 | 0 | 0 | 62 |
| link | 62 | 0 | 0 | 62 |
| runtime | 60 | 0 | 2 | 60 |

`opt -O2` accepted every IR that `llvm-as` accepted — zero opt crashes,
zero verifier failures under optimization. This is the main signal the
v4.99.0 panel asked for: **Phase A's fixes do not cause the optimizer to
reject the compiler's IR at -O2.**

## Observations

1. **Phase A stands up under -O2.** Every one of v4.100.0's MnString
   bitfield changes, v4.101.0's emitter move-semantics, v4.102.0's async
   linking, v4.103.0's closure/else work emits IR that `opt -O2` accepts
   without complaint.

2. **Linker wants `-no-pie`.** Modern Ubuntu defaults to PIE; the IR
   emits R_X86_64_32 relocations that require `-no-pie`. Matches
   `build_stage1.py` which already passes `-no-pie` for this reason.

3. **Runtime side is exclusively `libmapanare_rt.a`.** No other `.o` or
   `.so` needed. Async scheduler exports are present (v4.102.0 fix
   survives rebuild).

4. **One `llvm-as` gate catches a 17-version-old bug.** 47_try_operator
   has been PASS in the test-native harness since v4.33.0 despite
   emitting invalid IR. This is exactly what v4.105.0's CI-level
   `llvm-as` gate is designed to catch.

## Artifacts

- Full TSV: `docs/roadmap/v4/v4.104.0/artifacts/integration-results.tsv`
- Per-test logs: `/tmp/v4_104_integration/<test>.*.log` (session-local;
  not committed)
- Runner script: `/tmp/run_integration.sh` (session-local)

## Exit criterion (Exit #3)

- [x] All 64 golden tests run through the full integration pipeline.
- [x] Per-test result recorded in `INTEGRATION_RESULTS.md` and the TSV.
- [x] Failures separated by category: `emit` (1), `llvm-as` (1). No
  `opt`, `llc`, `link`, or runtime failures.
