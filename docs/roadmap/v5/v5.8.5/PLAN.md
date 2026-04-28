# v5.8.5 — Bb.1 closure (seed refresh for v5.8.4 runtime call)

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v5.8.4 shipped (Wb.2 self-hosted Win64 ABI; Wa.1
WASM CI install pin). Current `bootstrap/seed/linux-x86_64/mnc` is
the v4.155.0 strip from April 19 and predates v5.8.4 by ~50 minor
releases.
**Estimated work:** 30–60 min (build + verify + commit).

---

## Goal

Close **Bb.1** — refresh `bootstrap/seed/linux-x86_64/mnc` so the
no-Python bootstrap CI jobs ("Bootstrap (No Python)" and "Bootstrap
from Seed (No Python)") pass green again.

By v5.8.5 ship:
- `bash scripts/build_from_seed.sh` completes through stages 1–4
  on Linux x86_64.
- `bash scripts/build_from_seed.sh --verify` passes the
  `>=45 pass` golden gate.
- New seed sha256 recorded in `bootstrap/seed/linux-x86_64/mnc.sha256`
  and verified by `sha256sum -c`.
- Fixed-point holds on the freshly seed-built compiler
  (`scripts/verify_fixed_point.sh` clean, ≤4-line diff = VERSION
  metadata only).
- Linux + macOS + Windows native CI stays green; goldens 66/66
  preserved; `make lint` clean.
- VERSION 5.8.4 → 5.8.5; READMEs + CHANGELOG synced.

---

## Context — what broke and why

### Symptom

Both bootstrap CI jobs fail at "[1/4] Stage 1: seed compiles
source → stage1 IR" with exit code 1. The build script swallows
stderr (`"${SEED}" "${SOURCE}" > "${STAGE1_LL}" 2>/dev/null`); the
actual error, reproduced locally on WSL Linux x86_64, is:

```
mapanare/self/mnc_all.mn:0:0: error: Undefined function '__mn_host_is_win64'
```

CI run at v5.8.3 (`d12ae71`) succeeded — same seed, IR was
132,791 lines. CI run at v5.8.4 (`d2188aa`) fails on the same
seed. The only material change between them is v5.8.4's port of
the ABI classifier from `mapanare/emit_llvm_text.py` to
`mapanare/self/emit_llvm.mn`, which introduced one **real**
Mapanare-level call:

```mapanare
// mapanare/self/emit_llvm.mn:5885 (and the concatenated copy at mnc_all.mn:20783)
let host_w64: Int = __mn_host_is_win64()
if host_w64 != 0 {
    st.is_win64 = true
}
```

### Root cause

`__mn_host_is_win64` is a new C-runtime export added in v5.8.4
(`runtime/native/mapanare_core.c:2987`, gated on `_WIN32`). The
seed binary was built from the v4.155.0 source and has its own
hardcoded `is_builtin_function` list compiled in. That list does
**not** know `__mn_host_is_win64`. When the seed compiles
mnc_all.mn, its semantic pass treats the call as a user function
lookup, finds nothing, and rejects with "Undefined function".

This is the canonical "new `__mn_*` builtin → seed needs refresh"
pattern. Other `__mn_*` symbols in the source (e.g.
`__mn_str_concat`, `__mn_list_new`) survive because they appear
only inside emitted **IR text strings** the seed sees as ordinary
string literals — no semantic-pass call check ever runs against
them. `__mn_host_is_win64` is different: it's a real call
expression whose return value is bound to a Mapanare variable.

### Why no workaround in source

Investigated and rejected:
1. **Add `extern "C" fn __mn_host_is_win64() -> Int`** in
   `mnc_all.mn`. The seed parser accepts the syntax but its
   semantic pass still rejects the *call site* — extern fn lookup
   runs after the builtin gate, not before. (Empirically verified
   on WSL: same "Undefined function" error.)
2. **Hardcode `is_win64 = false`** for the bootstrap path. Defeats
   v5.8.4's self-hosted target awareness; stage2 built natively
   on Windows would fall back to SysV ABI and the v5.8.4 mnc-stage2
   on Windows would re-break (regression of Wb.2).
3. **Use a different mechanism the seed knows about** (env var
   via `__mn_getenv` etc.). Same problem — the seed doesn't know
   `__mn_getenv` either. Every syscall-shaped builtin has been
   added since v4.155.0.

### Why a seed refresh is the right answer

`bootstrap/seed/README.md` §"Updating the Seed" documents this
exact procedure. The seed has been refreshed at v3.4.0, v3.6.0,
v3.38.0, v4.155.0 — every time the language adds a runtime
builtin the prior seed doesn't know about. This is the same
pattern Go, Rust, and OCaml use (and `bootstrap/seed/README.md`
explicitly references that prior art).

The seed binary is stripped, deterministic (modulo timestamps in
the `.text` segment, which `strip` removes), and reproducible:
`python3 scripts/build_stage1.py` then `strip` produces a binary
that is byte-identical given the same source + toolchain. Its
`mnc.sha256` is checked in alongside; CI verifies it on every
run.

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Bb.1** | HIGH | Refresh `bootstrap/seed/linux-x86_64/mnc` from a clean Python-bootstrapped stage1 against current source; update `mnc.sha256`. Verify on `bash scripts/build_from_seed.sh --verify` + `bash scripts/verify_fixed_point.sh`. | 30 min |
| **Version bump + READMEs** | LOW | `VERSION` 5.8.4 → 5.8.5; sync badges across `README.md` + `docs/README.{es,pt,zh-CN}.md`; CHANGELOG entry; CLAUDE.md "Most recent releases" entry. | 15 min |
| **Roadmap docs** | LOW | `docs/roadmap/v5/v5.8.5/PLAN.md` + `SESSION_REPORT.md`. | 15 min |

## What does NOT ship in v5.8.5

- **No source code changes.** No edits to `mapanare/`,
  `runtime/`, `mapanare/self/`. The seed binary is the only
  artifact that changes.
- **No additional platform seeds.** `darwin-arm64/` and
  `darwin-x86_64/` from `scripts/build_from_seed.sh:27-37` remain
  empty. v5.8.5 only ships the seed for the platform CI uses.
- **No Win32 ABI work.** That's deferred to v5.8.6 (planning
  only) and a future implementation release. See
  `docs/roadmap/v5/v5.8.6/PLAN.md`.
- **No verification threshold tightening.** The `>=45 pass` gate
  in `scripts/build_from_seed.sh:146-149` stays — the new seed
  passes 55/66 on `--verify` (above threshold). The 11 failures
  are pre-existing self-hosted-emitter limitations the script
  pipes through bare `llvm-as` (no runtime link); the canonical
  golden harness `scripts/test_native.py` reports **66/66**
  unchanged.

---

## Procedure

### 1. Build a fresh stage1 from current source via Python (~5 min on WSL)

```bash
cd /mnt/c/Users/Juan/Documents/GitHub/Mapanare
python3 scripts/build_stage1.py
```

Expected: `mapanare/self/mnc-stage1` built (~6.4 MB stripped).

### 2. Smoke-test the fresh stage1 against the current source (~30 sec)

```bash
mapanare/self/mnc-stage1 mapanare/self/mnc_all.mn > /tmp/stage2_smoke.ll 2>/tmp/stage2_smoke.err
echo "exit: $?, lines: $(wc -l < /tmp/stage2_smoke.ll)"
head -3 /tmp/stage2_smoke.err
```

Expected: exit 0, ~219,955 lines, no stderr.

### 3. Promote stage1 to seed (~10 sec)

```bash
strip -o bootstrap/seed/linux-x86_64/mnc mapanare/self/mnc-stage1
cd bootstrap/seed/linux-x86_64
sha256sum mnc > mnc.sha256
sha256sum -c mnc.sha256
```

Expected: `mnc: OK`. Record the new size + sha256 for
SESSION_REPORT.

### 4. End-to-end no-Python bootstrap (~2 min)

```bash
cd /mnt/c/Users/Juan/Documents/GitHub/Mapanare
bash scripts/build_from_seed.sh --verify
```

Expected:
- "Seed checksum: OK"
- "[1/4] Stage 1: seed compiles source → stage1 IR" / "IR: ~219,955 lines"
- "[2/4] Stage 1: compiling stage1 IR → stage1 binary" / "Binary: /tmp/mnc-stage1"
- "[3/4] Stage 2: stage1 compiles source → stage2 IR" / "IR: ~219,955 lines"
- "[4/4] Stage 2: compiling stage2 IR → final binary"
- "Smoke test: OK"
- Verify: "55 pass, 11 fail" (or higher) — gate is `>=45`.

If stage1 IR line count differs from stage2 IR line count by more
than the v5.7.1 NEAR baseline (4 lines, all VERSION metadata),
investigate before promoting.

### 5. Fixed-point regression check (~3 min)

```bash
make build-rt   # refresh runtime archive (the v5.8.4 commit added __mn_host_is_win64 export; the gitignored .a is stale)
bash scripts/verify_fixed_point.sh
```

Expected: "NEAR FIXED POINT, ≤100-line diff" (current baseline:
4 lines = VERSION metadata only).

### 6. Canonical golden harness (~15 sec)

```bash
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1
```

Expected: **66/66 passed**.

### 7. Lint + struct registry gate

```bash
make lint
python scripts/check_struct_registry.py
```

Expected: clean. (No source edits in v5.8.5, so this is a sanity
check, not a real gate.)

### 8. Version + docs

- `VERSION`: `5.8.4` → `5.8.5`
- `README.md` line 27: badge `5.8.4` → `5.8.5`
- `docs/README.es.md` line 27, `docs/README.pt.md` line 27,
  `docs/README.zh-CN.md` line 27: same badge bump
- `CHANGELOG.md`: add `## [5.8.5] - 2026-04-27` section under
  `## [Unreleased]`
- `CLAUDE.md`: prepend new bullet to "Most recent releases"
  list, push v5.8.4 down (the list keeps last 6 only)
- Write `docs/roadmap/v5/v5.8.5/SESSION_REPORT.md`

### 9. Commit

```bash
git add bootstrap/seed/linux-x86_64/mnc bootstrap/seed/linux-x86_64/mnc.sha256
git add VERSION README.md docs/README.{es,pt,zh-CN}.md CHANGELOG.md CLAUDE.md
git add docs/roadmap/v5/v5.8.5/
git add tests/golden/BENCHMARKS.md tests/golden/BENCHMARKS-linux.md tests/golden/HISTORY.jsonl
git commit -m "v5.8.5: Bb.1 — refresh bootstrap seed for v5.8.4 __mn_host_is_win64"
```

Do not amend. Do not force-push. Push to `dev`; let CI verify.

---

## Risk register

| ID | Risk | Mitigation | Realized? |
|---|---|---|---|
| R1 | New seed is bigger than the old one (~3.6 MB → ~6.4 MB), bloating the repo. | Acceptable: source has grown ~50 minor versions since v4.155.0 (mnc_all.mn 132,791 → 219,955 lines, +66%). The seed is checked in once per major refresh; growth is ~3 MB once every ~100 commits. The same Go/Rust/OCaml comparison from `bootstrap/seed/README.md` accepts seed binary growth. | YES (~3 MB growth, accepted per design). |
| R2 | New seed produces non-deterministic strip output → CI sha256 mismatch. | `strip` removes timestamps, build IDs, etc. Verified locally with `sha256sum -c`. CI runs the same `strip` flag (`strip -o <out> <in>`) so reproducibility holds. | NO. |
| R3 | New seed silently regresses on a golden the old seed passed. | `bash scripts/build_from_seed.sh --verify` golden gate runs both seeds against the same corpus. The new seed passes 55/66 (vs old seed's prior `SKIP` state on CI, where llvm-as wasn't installed in one of the two jobs); the canonical `scripts/test_native.py` confirms 66/66 against the Python bootstrap. | NO. |
| R4 | Fixed-point holds at v5.8.4 but not at v5.8.5. | Empirically verified locally on WSL: 4 diff lines, all VERSION metadata, identical to v5.7.1 NEAR baseline. The new seed reproduces v5.8.4 stage2.ll byte-identical (modulo VERSION) — strict fixed-point evidence. | NO. |
| R5 | Win64 path regresses. | Win64 build pipeline uses `python3 scripts/build_stage1.py` (Python bootstrap), not the seed. The seed change is Linux-only. v5.8.4's Wb.2 closure is structurally untouched. CI's `build-native (windows-latest)` job re-runs Python-bootstrap stage1 and validates fixed-point on Windows; that gate is independent of the seed. | NO. |
| R6 | macOS bootstrap (no seed yet) regresses. | No effect — `bootstrap/seed/{darwin-arm64,darwin-x86_64}/` are still empty per `scripts/build_from_seed.sh:29-30`. macOS CI uses Python bootstrap, same as Windows. v5.8.5 doesn't add macOS seeds. | NO. |

---

## What ships

- `bootstrap/seed/linux-x86_64/mnc` — refreshed; ~6.4 MB stripped;
  built from clean Python bootstrap of current dev tip.
- `bootstrap/seed/linux-x86_64/mnc.sha256` — new sha256.
- `VERSION` 5.8.5
- `README.md` + 3 localized + `CHANGELOG.md` version sync
- `CLAUDE.md` release-history bullet
- `docs/roadmap/v5/v5.8.5/PLAN.md` (this file)
- `docs/roadmap/v5/v5.8.5/SESSION_REPORT.md`
- `tests/golden/BENCHMARKS{,-linux}.md` + `HISTORY.jsonl`
  refreshed by the goldens harness run

## What does NOT ship

- Source code changes (none required; the seed bug is structural,
  not a source bug)
- Win32 ABI work (deferred to v5.8.6 PLAN + future implementation)
- Additional platform seeds
- Verification threshold tightening
- Compiler / runtime / lowerer feature changes
