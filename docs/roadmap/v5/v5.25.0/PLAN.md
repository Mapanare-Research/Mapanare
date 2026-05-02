# v5.25.0 — Pv.* — CI prevention infrastructure

**Status:** PLANNING
**Breaking:** No.
**Prerequisite:** v5.24.1 shipped.
**Estimated effort:** 1 session (~2–3 hours).
**Arc context:** Opens a new **Pv.\*** (prevention) sub-arc.
First release after the v5.23–v5.24 recovery arc closeout.
Structural pattern parallel to **Hy.\*** (v5.24.0): catch
silent-fail classes at PR time, not at the next pre-panel
hygiene release.

---

## Why this exists

Add the structural prevention layer that closes a class of
failure where a CI-only test path catches a bug that could
have been caught locally — typically because (a) a stale
local artifact masks the bug on the developer machine,
(b) a feature ships without an end-to-end test exercising it
through the .mn-caller side, or (c) a test asset only runs on
a non-Windows CI job and never on the developer's WSL.

The v5.24.0 Hy.\* gates closed this for **docs drift** (badges,
SPEC headers, version sync). Pv.\* extends the same structural
pattern to **runtime-link wiring** and **bootstrap memory
hygiene** — two surfaces where the v5.13.0 → v5.24.1 window
shipped latent issues that surfaced only on fresh-checkout CI.

Each gate Pv.\* adds is an instance of the same rule:
**a feature is not done until at least one test exercises it
end-to-end from the .mn-caller side, AND that test runs on
Linux pytest (not just on Windows pytest with a stale local
artifact).** Future Pv.\* releases will add gates whenever the
same class recurs.

---

## Goals

1. **Pv.1** Regression test: `_find_runtime_lib()` returns a
   real, link-able file post-`make build-rt`.
2. **Pv.2** Regression test: `mnc-stage1 preprocess` clean
   under valgrind on brace-only / colon-only / mixed inputs.
3. **Pv.3** Extend `make ci-gates` (v5.24.0 Hy.1) with a
   `clean-build-test` sub-gate so stale local artifacts can
   never mask missing-runtime-link bugs.
4. **Pv.4** `scripts/validate_wsl.sh` + `dev.ps1 Validate-WSL`
   target — Linux pytest signal from a Windows host without
   leaving the dev loop. Optional pre-push git hook template.
5. **Pv.5** CLAUDE.md cleanup — remove the now-stale v5.13.1
   "planned" entry (At.1's runtime-lib wiring shipped on `dev`
   between v5.24.1 and v5.25.0; nothing left to plan).
6. **Pv.6** Fix the publish-pipeline smoke fixtures and add
   a local gate that parses them through the Python bootstrap
   before they ship. Closes publish run #48 Linux + macOS
   tarball-smoke failures.
7. Strict 3-stage fixed point preserved (zero
   `mapanare/self/*.mn` edits in v5.25.0 — Pv.\* is test +
   script + docs only).

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Pv.1** | MEDIUM (structural) | New `tests/test_runtime_lib_lookup.py` (~50 LOC). Asserts `mapanare.test_runner._find_runtime_lib()` returns a path that exists, has the canonical name (`libmapanare_rt.a` preferred), and is link-able by clang against a tiny IR fragment that references `__mn_str_eq`. The fixture explicitly deletes any `libmapanare_core.*` shadow files from the candidate dirs first to prove the lookup doesn't quietly fall back to a stale artifact. | 30 min |
| **Pv.2** | MEDIUM (structural) | New `tests/bootstrap/test_preprocess_memcheck.py` (~80 LOC). Runs `mnc-stage1 preprocess` on three fixtures — brace-only `fn main() { print(1) }`, colon-only `fn main(): print(1)`, and mixed — under `valgrind --error-exitcode=1`. Skips with marker on hosts without valgrind. Locks the brace-only fast path against future MnString lifecycle regressions; protects every fast-path edit going forward. | 1h |
| **Pv.3** | LOW (structural) | Extend `make ci-gates` with new sub-gate `clean-build-test`: `make clean && make build-rt && pytest tests/test_at_test_runtime.py -q`. Catches the runtime-archive-rename class structurally — any future renaming or relocation of `libmapanare_rt.a` without updating `_find_runtime_lib` (or vice versa) fails the gate before the PR lands. | 30 min |
| **Pv.4** | LOW | New `scripts/validate_wsl.sh` running the Linux pytest path from a Windows host. New `dev.ps1` function `Validate-WSL` invoking it via `wsl -d Ubuntu`. Documented in `docs/guides/dev_loop.md`. Optional pre-push git hook template at `scripts/hooks/pre-push.sample` (commented opt-in; running the full suite pre-push is the dev's call). | 1h |
| **Pv.5** | LOW (docs) | CLAUDE.md cleanup — remove the v5.13.1 entry from the "Planned / in-progress" section. The runtime-lib wiring (At.1's only remaining open item) shipped on `dev` between v5.24.1 and v5.25.0; the `@test` runtime is fully functional end-to-end on Python and native paths. No new entry needed; v5.13.1 simply leaves the planned list. | 15 min |
| **Pv.6** | MEDIUM | **Publish-pipeline smoke fixture fix.** The Hy.5 (v5.24.0) Linux + macOS tarball smoke jobs in `.github/workflows/publish.yml` author a hello fixture as `fn main(): print("hello from clean Linux smoke")` — single-line colon syntax that doesn't parse. Single-line `fn x(): y` was the v5.14.0 SPEC §1009 promise that v5.21.1 H.4 explicitly rescoped to v6.0; the fixture was authored against an unshipped feature. Replace with multi-line colon (`fn main():\n    print(...)`) or brace form. Add `tests/test_publish_smoke_fixtures.py` (~40 LOC) that extracts every `cat > /tmp/*.mn` heredoc from `.github/workflows/publish.yml` and parses each through `mapanare.parser.parse` — fails if any fixture would not compile. Locks the failure mode against any future workflow edit. | 1h |

---

## Phase plan

### Phase 0 — pre-flight verification (~10 min)

```bash
bash scripts/verify_fixed_point.sh --keep
make ci-gates
pytest tests/test_at_test_runtime.py \
       tests/bootstrap/test_indent_preprocessor.py \
       tests/bind/test_python_binding.py -q
# All must pass at v5.24.1 + intervening bugfix HEAD.
```

### Phase 1 — prevention tests (Pv.1 + Pv.2)

The contract for both: the test must be **falsifiable**. Use
`git stash` to temporarily revert the corresponding fix in
`mapanare/test_runner.py` / `runtime/native/mapanare_core.c`,
confirm the new test fails, restore the stash, confirm it
passes. Without that revert-and-restore step the test is
unfalsifiable — a test that can't fail isn't a test.

### Phase 2 — gate + tooling (Pv.3 + Pv.4)

`make ci-gates` extension is mechanical. WSL wrapper has one
gotcha: `wsl -d Ubuntu bash -c` runs in the user's home, not
the project root — the script must `cd` first. Pre-push hook
ships as `.sample` (commented opt-in); not enabled by default.

### Phase 3 — docs cleanup (Pv.5)

Single CLAUDE.md edit. v5.13.1 entry deleted from the
"Planned / in-progress" section. No replacement; the @test
runtime work just landed without a tagged release.

### Phase 4 — publish-smoke fixture fix (Pv.6)

YAML edit + new local gate test. Run order:

1. Edit `.github/workflows/publish.yml`: replace every
   `fn main(): print(...)` smoke heredoc with the multi-line
   form or brace form. Match the form to whatever the
   surrounding install script syntax expects.
2. Write `tests/test_publish_smoke_fixtures.py` parsing
   every heredoc in the workflow through `mapanare.parser`.
3. Falsifiability: `git stash` the workflow edit; new test
   fails with the same parse error from publish run #48;
   restore; test passes.

---

## Out of scope

- **Mb.7** (i64/i1 tag-emit, 9 LINK_FAIL goldens) — v5.26.0.
  Real codegen work; deserves its own release.
- **`to_terse` empty `#{}` rewriter bug** — v5.27.0. Latent
  since v5.24.1 with a manual SPEC §17.1 revert.
- **`mnc fmt` long-line wrap + import sort** — v5.27.0.
  Deferred from v5.13.0; 12 releases stale.
- **Docker builder-image diet** — explicit user opt-out.
  Stays in the carry-forward docket indefinitely.
- **`act` for local CI replay** — out of scope; the WSL
  wrapper closes 95% of the gap at 5% of the setup cost.

---

## Success criteria

- ✅ Goldens 95/95.
- ✅ Strict 3-stage fixed point preserved (line count
  identical to v5.24.1).
- ✅ `make ci-gates` (extended with Pv.3) passes.
- ✅ `tests/test_runtime_lib_lookup.py` and
  `tests/bootstrap/test_preprocess_memcheck.py` both pass;
  both can be made to fail by reverting the corresponding
  source change (the contract that proves the test exists).
- ✅ `scripts/validate_wsl.sh` runs the full pytest suite
  to completion from a Windows host invoking it via
  `dev.ps1 Validate-WSL`.
- ✅ CLAUDE.md "Planned / in-progress" section no longer
  contains v5.13.1.
- ✅ `.github/workflows/publish.yml` Linux + macOS tarball-
  smoke fixtures parse through `mapanare.parser`;
  `tests/test_publish_smoke_fixtures.py` green; the
  publish-pipeline failure from run #48 cannot recur.

---

## Carry-forward delta

Opens:
- **Pv.\* arc** — first prevention sub-arc; structural pattern
  parallel to Hy.\*. Future Pv.\* releases may add gates
  whenever a CI failure surfaces a "test that should have
  existed when the feature shipped."

Inherits to v5.26.0:
- **Mb.7** — i64/i1 tag-emit, 9 LINK_FAIL goldens.

Inherits from v5.24.1 docket (~5 LOW open items): unchanged.
