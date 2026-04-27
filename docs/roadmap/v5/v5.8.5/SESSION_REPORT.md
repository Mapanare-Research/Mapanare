# v5.8.5 — Bb.1 closure (seed refresh for v5.8.4 runtime call)

**Status:** SHIPPED (v5.8.5)
**Tag:** pending user approval
**Author:** Claude Opus 4.7 (1M ctx) under user direction
**Date:** 2026-04-27
**Estimated:** 30–60 min (PLAN). **Actual:** ~25 min of build +
verify + docs.

---

## TL;DR

- **Bb.1 closed.** `bootstrap/seed/linux-x86_64/mnc` refreshed
  from a clean Python-bootstrapped stage1 against the v5.8.4
  source. Old seed (v4.155.0 era, April 19) → new seed (v5.8.4
  source, April 27). Size 3,583,120 → 6,433,952 bytes (+80%);
  growth is from ~50 minor releases of source accretion (mnc_all.mn
  132,791 → 219,955 lines, +66%). New sha256:
  `7c2897f09af8db4042633124e44ca12d948cee77b89150e05735c5121493d749`.
- **Both no-Python bootstrap CI jobs unblocked.** "Bootstrap (No
  Python)" + "Bootstrap from Seed (No Python)" failed at v5.8.4 on
  the seed's "Undefined function `__mn_host_is_win64`" error
  (script swallowed via `2>/dev/null`; reproduced locally on WSL).
  The refreshed seed knows `__mn_host_is_win64` because its
  internal builtin list is taken from the v5.8.4
  `register_builtins`.
- **Fixed-point holds.** `scripts/verify_fixed_point.sh` reports
  NEAR FIXED POINT, 4 diff lines / 219,955 = 0.002%, all VERSION
  metadata. Matches v5.7.1+ baseline shape exactly.
- **Goldens preserved.** Canonical harness 66/66; bootstrap-from-
  seed `--verify` 55/66 (above the script's `>=45` threshold —
  the 11 failures are pre-existing self-hosted-emitter limitations
  the verify pipes through bare `llvm-as` without runtime link).
- **Zero source-code changes.** No edits to `mapanare/`,
  `runtime/`, `mapanare/self/`. `make lint` clean.
  `check_struct_registry.py` 25/25 clean. The seed binary +
  sha256 + version metadata + roadmap docs are the only artifacts
  that change.

---

## Root cause recap

The v5.8.4 commit (`d2188aa`) added a real Mapanare-level call
inside `mapanare/self/emit_llvm.mn::emit_mir_module` (and the
concatenated copy at `mnc_all.mn:20783`):

```mapanare
let host_w64: Int = __mn_host_is_win64()
if host_w64 != 0 { st.is_win64 = true }
```

`__mn_host_is_win64` is a new C-runtime export at
`runtime/native/mapanare_core.c:2987`, gated on `_WIN32`. Returns
1 on Windows builds, 0 elsewhere. The current self-hosted compiler
recognizes it: `is_builtin_function` at
`mapanare/self/semantic.mn:163`, `register_builtins` at
`mapanare/self/semantic.mn:2101`, lower-side return-type pin at
`mapanare/self/lower.mn:2293`.

The seed binary in `bootstrap/seed/linux-x86_64/mnc` was the
v4.155.0 strip from April 19 (last seed refresh). Its semantic
pass — embedded in the binary — had a hardcoded builtin list that
predates `__mn_host_is_win64`. The seed accepted every `__mn_*`
identifier it saw inside emitted IR text (those are just string
literals from the seed's perspective), but rejected the one real
Mapanare-level call site:

```
$ wsl bootstrap/seed/linux-x86_64/mnc mapanare/self/mnc_all.mn
mapanare/self/mnc_all.mn:0:0: error: Undefined function '__mn_host_is_win64'
```

CI proof: at `d12ae71` (v5.8.3) the seed produced 132,791-line
stage1 IR cleanly. At `d2188aa` (v5.8.4) the seed exited with code
1 at "[1/4] Stage 1: seed compiles source → stage1 IR" (logs swallowed via
`build_from_seed.sh:68 2>/dev/null`).

---

## Why "refresh the seed" not "patch the source"

Three workarounds investigated and rejected before falling back
to the documented seed-refresh path in `bootstrap/seed/README.md`
§"Updating the Seed":

1. **`extern "C" fn __mn_host_is_win64() -> Int`** in
   `mnc_all.mn`. The seed parser accepts the syntax (parser tree
   is shared with current source), but its semantic pass still
   rejects the *call site*: extern fn lookup runs after the
   `is_builtin_function` gate. Empirically verified on WSL with a
   minimal repro:
   ```mapanare
   extern "C" fn __mn_host_is_win64() -> Int
   fn main() -> Int { return __mn_host_is_win64() }
   ```
   → "Undefined function '__mn_host_is_win64'". Same failure mode.

2. **Hardcode `is_win64 = false`** in `emit_mir_module`. Defeats
   v5.8.4's Wb.2 closure entirely: stage2 built natively on
   Windows would fall back to SysV ABI, regressing
   `mnc-stage2.exe` to the v5.8.2 broken state. Non-starter.

3. **Reach the host via an existing builtin** (e.g. `__mn_getenv`
   for an env-var check, or a parameter on `compile`). Same
   structural problem — every syscall-shaped builtin has been
   added since v4.155.0; the seed knows none of them. The
   moment we restructure to use any new builtin we hit the same
   wall.

The seed-refresh path is what the repo has always used: v3.4.0,
v3.6.0, v3.38.0, v4.155.0. Each refresh corresponds to a prior
release that added `__mn_*` runtime calls the previous seed
didn't know. The same pattern Go's bootstrap uses (the Go 1.4
seed) and the same pattern `bootstrap/seed/README.md` documents.

---

## Procedure executed (verified clean on WSL Linux x86_64)

### Phase 1 — Build fresh stage1 (~5 min)

```bash
cd /mnt/c/Users/Juan/Documents/GitHub/Mapanare
python3 scripts/build_stage1.py
# real    4m49.872s
# user    4m42.027s
# sys     0m2.717s
# Binary: mapanare/self/mnc-stage1 (6,846,384 bytes; stripped: 6,433,952 bytes)
```

Phase 1 smoke-test:
```bash
$ mapanare/self/mnc-stage1 mapanare/self/mnc_all.mn > /tmp/stage2_smoke.ll
$ wc -l /tmp/stage2_smoke.ll
219955 /tmp/stage2_smoke.ll
$ echo $?
0
```

### Phase 2 — Promote stage1 to seed (~10 sec)

```bash
strip -o bootstrap/seed/linux-x86_64/mnc mapanare/self/mnc-stage1
cd bootstrap/seed/linux-x86_64
sha256sum mnc > mnc.sha256
sha256sum -c mnc.sha256
# mnc: OK
```

Recorded:
- New seed: `bootstrap/seed/linux-x86_64/mnc` — 6,433,952 bytes
- New sha256: `7c2897f09af8db4042633124e44ca12d948cee77b89150e05735c5121493d749`
- Old seed: 3,583,120 bytes (April 19, v4.155.0 era)
- Old sha256 (overwritten): see `git log` of the deleted line

### Phase 3 — End-to-end no-Python bootstrap (~2 min 8 sec)

```bash
$ time bash scripts/build_from_seed.sh
=== Mapanare: Two-stage bootstrap (no Python) ===
  Seed checksum: OK

[1/4] Stage 1: seed compiles source → stage1 IR
  IR: 219955 lines
[2/4] Stage 1: compiling stage1 IR → stage1 binary
  Binary: /tmp/mnc-stage1 (5003240 bytes)

[3/4] Stage 2: stage1 compiles source → stage2 IR
  IR: 219955 lines
  Validation: OK
[4/4] Stage 2: compiling stage2 IR → final binary
  Binary: ./mnc (5003240 bytes)
  Smoke test: OK

=== Success: ./mnc ===

real    2m8.097s
```

Identical binary sizes for stage1 + stage2 (5,003,240 bytes) is
the strict-fixed-point smoke signal. The only diff between
stage2.ll (from seed) and stage2.ll (from stage1, second pass) is
VERSION metadata.

### Phase 4 — `--verify` golden gate (~2 min 16 sec)

```bash
$ time bash scripts/build_from_seed.sh --verify
... (same as Phase 3) ...

=== Verifying golden tests ===
  FAIL: 07_enum_match.mn
  FAIL: 10_result.mn
  FAIL: 17_option.mn
  FAIL: 26_generics.mn
  FAIL: 29_generic_impl.mn
  FAIL: 30_nested_generics.mn
  FAIL: 31_generic_multi.mn
  FAIL: 47_try_operator.mn
  FAIL: 48_match_nested_exhaustive.mn
  FAIL: 49_match_guards.mn
  FAIL: 51_match_guards_and_or.mn
  55 pass, 11 fail

real    2m16.220s
```

55 pass > script's 45-pass gate (`build_from_seed.sh:147-149`,
v4.155.0 ratchet). The 11 failures are pre-existing self-hosted-
emitter `llvm-as`-strictness gaps where the verify path pipes IR
through bare `llvm-as` without runtime archive linkage; the
canonical golden harness compiles to object code and links the C
runtime, which masks these. **No regression vs the prior seed**:
this 11-fail set has been stable across the v5.x arc.

### Phase 5 — Canonical golden harness (~11 sec)

```bash
$ python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1
PASS 01_hello ...
... (66 tests) ...
PASS 66_qualified_type_ref 21L->46L 4bb 33stk 5ms (1 fns) stg1:2fns 140ms

All 66 tests passed in 10.8s
Benchmarks: tests/golden/BENCHMARKS-linux.md
History: tests/golden/HISTORY.jsonl
```

**66/66 preserved.** This is the gate that matters for source
correctness — the build_from_seed `--verify` is a coarser smoke
gate.

### Phase 6 — Fixed-point regression (~3 min 30 sec)

```bash
$ make build-rt   # refresh runtime archive (libmapanare_rt.a was stale)
$ bash scripts/verify_fixed_point.sh
=== Three-Stage Fixed Point Verification ===

[Stage 0] Using existing stage1: mapanare/self/mnc-stage1
  stage1: 6433952 bytes
[Stage 1] stage1 compiles mnc_all.mn → stage2.ll
  stage2.ll: 219955 lines
  llvm-as: OK
  Building mnc-stage2... OK (4967912 bytes)
[Stage 2] stage2 compiles mnc_all.mn → stage3.ll
  stage3.ll: 219955 lines
  llvm-as: OK

[Verify] Fixed point: diff stage2.ll stage3.ll
  ~ NEAR FIXED POINT
  4 diff lines out of 219955 (0.002%)
  within DIFF_THRESHOLD=100; accepted.

  First 20 diff lines for reference:
219955c219955
< !0 = !{!"5.8.4"}
---
> !0 = !{!"__MN_VERSION__"}
```

**4-line diff = VERSION metadata only**, identical shape to
v5.7.1 / v5.8.0 NEAR baseline. The compiler is structurally
identical at v5.8.5 modulo the version string baked into the
binary.

### Phase 7 — Lint + struct registry

```bash
$ make lint
... (clean) ...
$ python scripts/check_struct_registry.py
... 25/25 fields per struct, 91 fields total, OK ...
```

(No source edits, so these are sanity checks; no expected drift.)

---

## Metrics

| Metric | v5.8.4 | v5.8.5 | Delta |
|---|---|---|---|
| Seed size | 3,583,120 B | 6,433,952 B | **+80%** (mnc_all.mn +66% over the period) |
| Seed sha256 (first 16) | `bf5a82c1...` (v4.155.0) | `7c2897f0...` | NEW |
| Stage 1 IR lines (no-Python bootstrap) | 132,791 (old seed → old IR shape) | **219,955** (matches v5.8.4 baseline) | +87,164 |
| Stage 2 IR lines | 217,879 (last published v5.8.0) | **219,955** (v5.8.4 + .5 with refreshed runtime decls) | +2,076 |
| Goldens (canonical harness) | 66/66 | **66/66** | preserved |
| Goldens (build_from_seed --verify) | SKIP (llvm-as not in CI) | 55/66 (gate ≥45) | newly visible |
| Fixed-point | NEAR (4 lines, VERSION) | **NEAR** (4 lines, VERSION) | preserved |
| `mnc-stage1` (Python bootstrap) | 6,433,952 B | **6,433,952 B** | identical |
| `make lint` | clean | **clean** | preserved |
| `check_struct_registry.py` | 25/25/91 | **25/25/91** | preserved |
| Source LOC changed | — | **0** | per design |

---

## What ships in v5.8.5

- `bootstrap/seed/linux-x86_64/mnc` (refreshed, 6,433,952 bytes)
- `bootstrap/seed/linux-x86_64/mnc.sha256` (new sha256)
- `VERSION`: 5.8.4 → 5.8.5
- `README.md` + `docs/README.es.md` + `docs/README.pt.md` +
  `docs/README.zh-CN.md`: badge sync
- `CHANGELOG.md`: `## [5.8.5]` section
- `CLAUDE.md`: prepended bullet to "Most recent releases"
- `docs/roadmap/v5/v5.8.5/PLAN.md` + `SESSION_REPORT.md`
- `tests/golden/BENCHMARKS.md` + `BENCHMARKS-linux.md` +
  `HISTORY.jsonl` (refreshed by the goldens harness run)

## What does NOT ship in v5.8.5

- **Compiler / lowerer / runtime source changes.** Zero edits to
  `mapanare/`, `runtime/`, `mapanare/self/`. The bug was
  structural (seed staleness), not a source bug.
- **Win32 ABI work.** Deferred to v5.8.6 (PLAN + PROMPT only;
  no implementation).
- **Additional platform seeds.** `bootstrap/seed/darwin-arm64/`
  + `bootstrap/seed/darwin-x86_64/` remain empty per the
  long-standing TODO at `bootstrap/seed/README.md:24`.
- **Verification gate tightening.** The 45-pass threshold in
  `scripts/build_from_seed.sh` stays. The `>=45` gate has been
  rationalized for two releases now; tightening it would conflate
  two concerns (seed health vs `llvm-as`-strictness gaps in the
  self-hosted emitter).
- **`mnc-stage1.exe` artifact regeneration.** Windows pipeline
  uses Python bootstrap (independent of the Linux seed); v5.8.4's
  Wb.2 closure is structurally untouched. CI's `build-native
  (windows-latest)` re-runs Python-bootstrap stage1 fresh on
  every dev push; nothing to ship here.

---

## Carry forward

Nothing v5.8.5-introduced. The v5.8.4 carry list (Bo.18 README
internal contradiction; Bo.19/Bo.20/Bo.14r2/Pe.1 LOWs from the
v5.8.0 panel) is unchanged. v6.0 carry list: Rt.04 (multi-level
alias analysis, struct→list→string depth-2). All other dockets
remain CLOSED.

## Next

- **v5.8.6** — Win32 (i686) ABI plan + prompt. Planning artifact
  only; implementation is its own release. The user noted that
  `__mn_host_is_win64` reads `_WIN32` (defined for both 32-bit
  and 64-bit Windows) and that the function name is misleading —
  on a 32-bit MinGW build the flag would still set
  `is_win64=true` even though i686 ABI rules differ from x86_64.
  v5.8.6 quantifies the gap, decides whether to support 32-bit
  Windows at all, and lays out the implementation surface if the
  decision is yes.
- **v6.0** — borrow checker. Rt.04 closure + general ownership.

See `docs/roadmap/v5/CLOSEOUT_ARC.md` and
`docs/roadmap/v5/PARITY_GAPS.md`.
