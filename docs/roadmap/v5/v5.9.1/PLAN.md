# v5.9.1 — DX.5 — `mnc <file.mn>` defaults to `run` (breaking)

**Status:** PLANNING
**Breaking:** Yes — single behavior change. The IR-dump path moves
from the implicit default to an explicit `mnc emit-llvm` subcommand.
**Prerequisite:** v5.9.0 shipped (DX.1–DX.4 + DX.6 + DX.7 closed,
strict 3-stage fixed-point restored).
**Estimated effort:**
- Phase 1 (DX.5 — dispatch + new subcommand) — 1h
- Phase 2 (deprecation warning for one release) — 30m
- Phase 3 (CHANGELOG + docs + tests) — 30m
- Phase 4 (validation matrix) — 1h
- **Total:** 3–4 hours, 1 focused session

---

## Goal

Close the last DX.* docket from the v5.8.7 Windows install probe.
Pre-v5.9.1 `mnc file.mn` emits LLVM IR to stdout — useful for
compiler developers debugging codegen, but a hostile first
impression for newcomers (`mnc hello.mn` dumps 200 lines of
`define i64 @main()`-shaped IR instead of running the program).

After v5.9.1:

- `mnc hello.mn` runs the program (compiles + executes), forwarding
  `argv[2..]` to the user binary.
- `mnc emit-llvm hello.mn` keeps the IR-emission path verbatim.
- `mnc emit-llvm hello.mn -o hello.ll` writes IR to a file.
- One stderr deprecation note on the implicit-run path for v5.9.1
  only, removed in v5.10.0 — gives downstream CI scripts that pipe
  `mnc file.mn > out.ll` a one-release migration window.

This is **dispatch-layer only**. Zero changes to the parser,
semantic checker, MIR, lowerer, optimizer, or emitters. The full
surface lives in `mapanare/self/main.mn::mn_main`.

---

## What's broken (recap from v5.8.7 Windows install probe)

> **Default command dumps IR instead of running.** `mnc file.mn`
> outputs LLVM IR rather than executing. New users hit this on the
> first program they write.

Cross-reference with source (post-v5.9.0 line numbers):

| Bug | File:line | Cause |
|---|---|---|
| `mnc file.mn` dumps IR | `mapanare/self/main.mn::mn_main` final fall-through | After all subcommand checks fail, `arg1` is treated as a filename and `compile()` + `print(cr.ir_text)` is called. Useful for compiler devs; surprising for everyone else. |

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **DX.5** | LOW-MEDIUM (UX, breaking) | `mnc file.mn` defaults to **run**. IR-emit moves to `mnc emit-llvm file.mn` (parallel to the existing Python `mapanare emit-llvm` subcommand). v5.9.1 prints a one-line stderr deprecation note on the implicit-run path; v5.10.0 removes the note. | 1–2h |

---

## Phase plan

### Phase 1 — DX.5 dispatch + `emit-llvm` subcommand

1. **New subcommand handler in `main.mn`.** Add an
   `emit-llvm` branch parallel to `test` / `build` / `run` /
   `compile` / `cache`:
   ```mn
   if arg1 == "emit-llvm" {
       if __mn_argc() < 3 {
           __mn_str_eprint("usage: mnc emit-llvm <file.mn> [-o output]\n")
           __mn_exit(1)
       }
       run_emit_llvm(__mn_argv(2))
       return
   }
   ```
2. **Lift the current default-fall-through body** into a new
   `run_emit_llvm(filename: String)` helper. This is a
   straight refactor: the existing `compile()` + `print(cr.ir_text)`
   lines move from `mn_main` to the helper. Optional `-o output`
   support: write to file via `__mn_file_write` instead of `print`.
3. **Default branch becomes implicit run.** When `arg1` doesn't
   match any subcommand, doesn't start with `-`, and ends with
   `.mn` (or any file the user can read):
   ```mn
   // Treat as 'mnc run <file>' for newcomers.
   if arg1.ends_with(".mn") {
       __mn_str_eprint("note: implicit 'run' is the default in v5.9+; use 'mnc emit-llvm' for IR output\n")
       run_program(arg1)
       return
   }
   ```
4. **Per-subcommand help.** `print_subcommand_help("emit-llvm")`
   gets a 4-line block; `print_help_text()` lists `mnc emit-llvm
   <file.mn>` after the implicit-run line.
5. **Update v5.9.0 usage block at `mn_main`'s `argc < 2`
   branch** to mention `mnc <file.mn>` runs the file and
   `mnc emit-llvm <file.mn>` emits IR.

### Phase 2 — Deprecation messaging

The PROMPT version of step 1.3 includes the stderr deprecation
note. That's all the deprecation surface needs — anyone piping
`mnc file.mn > out.ll` will see the note on stderr (which
typically isn't redirected in shell `>` pipelines), with
explicit instructions to migrate to `mnc emit-llvm`. v5.10.0
deletes the note.

### Phase 3 — Docs + tests

1. **CHANGELOG.md** `[5.9.1]` block flags the change as **BREAKING**
   in bold so anyone scanning notes sees it. Migration recipe
   inline: `mnc file.mn > out.ll` → `mnc emit-llvm file.mn -o out.ll`.
2. **`tests/test_cli_default.py`** (new) covers:
   - `mnc hello.mn` runs and prints program output (NOT IR text)
   - `mnc emit-llvm hello.mn` prints IR (contains `define`,
     `target triple`)
   - `mnc emit-llvm hello.mn -o out.ll` writes the IR to `out.ll`,
     stdout silent
   - The deprecation note appears on stderr for the implicit-run
     path
3. **`docs/known_issues.md`** last-updated rolled to v5.9.1; DX.5
   row added to the closed list.
4. **`docs/roadmap/v5/PARITY_GAPS.md`** DX.5 → Historical row.
5. **README.md + es/pt/zh-CN** — update any "compile to IR" example
   from `mnc file.mn` to `mnc emit-llvm file.mn`. Add a short
   migration note.

### Phase 4 — Validation matrix

```bash
# Lint
make lint

# Goldens 66/66 (no IR-emission changes — must hold byte-identical)
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1

# Strict fixed-point (the v5.9.0 milestone — must hold)
bash scripts/verify_fixed_point.sh --keep
md5sum /tmp/stage2.ll /tmp/stage3.ll  # expected: identical

# CLI tests
pytest tests/test_cli_help.py tests/test_cli_default.py -v

# Sanity smoke
echo 'fn main() { print("hello v5.9.1") }' > /tmp/dx5.mn
./mapanare/self/mnc-stage1 /tmp/dx5.mn       # expected: "hello v5.9.1"
./mapanare/self/mnc-stage1 emit-llvm /tmp/dx5.mn | head -5  # expected: IR
```

---

## Decisions

### Decision 1: behavior on `mnc <non-mn-file>` (e.g. `mnc Makefile`)?

Currently the default branch reads the file regardless of extension
and tries to compile. With DX.5 the new default checks
`ends_with(".mn")` and routes to `run_program`. For non-`.mn` files:

- **Recommend: error out with helpful hint.** "error: 'Makefile'
  is not a .mn file. Use `mnc emit-llvm <file>` for non-`.mn`
  files (lexer/parser will report the actual issue), or `mnc
  compile <file>` for transpilation of .py/.php/.ts/.go." The old
  behavior (silently try to compile a non-`.mn` file) was a
  diagnostic regression from any explicit subcommand.

### Decision 2: `mnc emit-llvm` vs `mnc emit` vs `mnc ir`?

PROMPT's original sketch uses `emit-llvm` for symmetry with the
Python CLI. Alternatives:

- `mnc emit` — shorter, but ambiguous (we have multiple emitters:
  llvm, c, wasm).
- `mnc ir` — shortest. Concrete to "this is the IR backend." Loses
  the "llvm" specificity.
- `mnc emit-llvm` — exact mirror of `mapanare emit-llvm` from the
  Python CLI, which is the closest-prior-art on the project.

**Recommend: `mnc emit-llvm`**. Project consistency wins. If we
add WASM emission to the native CLI later, `mnc emit-wasm` slots
in cleanly.

### Decision 3: stderr deprecation note text?

PROMPT's draft: `note: implicit 'run' is the default in v5.9+;
use 'mnc emit-llvm' for IR output`. Mid-length, gives the migration
recipe inline. Alternatives — bare warning; multi-line block. Stay
with the one-liner — the user can read more in the changelog.

### Decision 4: when does the deprecation note get removed?

Two release windows ahead — v5.11.0 — gives downstream CI scripts
two soak releases. v5.10.0 alone is enough technically (one full
release-cycle window), but the cost of carrying the note is one
stderr line; the cost of removing too soon is breaking someone's
unattended CI.

**Recommend: remove in v5.11.0.** Documented in CHANGELOG `[5.9.1]`
under "deprecation timeline."

---

## What ships in v5.9.1

- **Source changes:**
  - `mapanare/self/main.mn` — `emit-llvm` subcommand branch,
    `run_emit_llvm` helper, default-fall-through becomes
    implicit-run with stderr note, `print_subcommand_help` +
    `print_help_text` + usage-block updates.
  - `mapanare/self/mnc_all.mn` — regenerated via
    `bash scripts/concat_self.sh`.
- **Tests:**
  - `tests/test_cli_default.py` — NEW, ~30 LOC, ~6 test cases.
- **Docs:**
  - `docs/roadmap/v5/v5.9.1/PLAN.md` (this file)
  - `docs/roadmap/v5/v5.9.1/PROMPT.md` (execution prompt)
  - `docs/roadmap/v5/v5.9.1/SESSION_REPORT.md` (closeout)
  - `CHANGELOG.md` `[5.9.1]` block (BREAKING-flagged)
  - `docs/known_issues.md` — DX.5 row → CLOSED v5.9.1
  - `docs/roadmap/v5/PARITY_GAPS.md` — DX.5 row → Historical
  - `CLAUDE.md` release-history bullet
  - `docs/roadmap/ROADMAP.md` — Where We Are entry
  - `README.md` + `docs/README.{es,pt,zh-CN}.md` — IR-emission
    examples updated to `mnc emit-llvm`.
- **Bootstrap:**
  - **No seed refresh.** v5.9.1 doesn't add new builtin call sites;
    the v5.9.0 seed compiles v5.9.1 source unchanged.
- **Version:** 5.9.0 → 5.9.1 at end of Phase 4.

## What does NOT ship in v5.9.1

- **Compiler / parser / semantic / MIR / lower / emitter
  changes.** Zero. Same scope discipline as v5.9.0.
- **The deprecation note removal.** Tracked for v5.11.0.
- **macOS / Windows runtime smoke test.** Linux validation only —
  the dispatch logic is platform-agnostic. CI exercises macOS +
  Windows.

---

## Risk register

| ID | Risk | Mitigation |
|---|---|---|
| DX5.R1 | A downstream CI script silently breaks because the stderr deprecation note isn't seen (script redirects 2>&1 to /dev/null). | The script ALSO breaks in v5.10.0 when behavior diverges; v5.9.1's deprecation note is best-effort. CHANGELOG flags BREAKING in bold. |
| DX5.R2 | `mnc <existing-binary-name>` (e.g. user has a file `mnc compile.mn` thinking it's `mnc compile`-style) hits the implicit run instead of compile. | The implicit-run gate checks `ends_with(".mn")` only — non-`.mn` files don't trigger it; they error out per Decision 1. |
| DX5.R3 | The deprecation note prints on every CI build, polluting log volume. | Acceptable cost for one release. v5.10.0 keeps the note, v5.11.0 removes. Volume per CI run = 1 line. |
| DX5.R4 | Old test that asserted `mnc file.mn` produces IR (e.g. legacy test_native.py harness) breaks. | `tests/test_cli_default.py` covers both paths so regressions surface; `scripts/test_native.py` already uses internal compilation paths, not the CLI default. |
| DX5.R5 | Strict fixed-point (the v5.9.0 milestone) regresses because the new dispatch branch shifts MIR layout. | Phase 4 runs `verify_fixed_point.sh` and gates on strict equality. Dispatch branches don't affect IR emission of the compiler itself; risk is theoretically zero. |

---

## Closure checklist for v5.9.1

### Phase 1 (DX.5 dispatch)

- [ ] `emit-llvm` branch added to `mn_main` before the default fall-through
- [ ] `run_emit_llvm` helper extracts the current default-IR-emission body
- [ ] `-o output` flag handled (writes to file via `__mn_file_write`)
- [ ] Default fall-through routes to `run_program` for `.mn` files
- [ ] Non-`.mn` files print an error with migration hint (Decision 1)
- [ ] `print_help_text` and `print_subcommand_help("emit-llvm")` updated

### Phase 2 (deprecation messaging)

- [ ] One-line stderr note prints on every implicit-run invocation
- [ ] CHANGELOG `[5.9.1]` block flags BREAKING in bold
- [ ] Migration recipe documented inline

### Phase 3 (docs + tests)

- [ ] `tests/test_cli_default.py` exists and passes 6+ cases
- [ ] `docs/known_issues.md` last-updated → v5.9.1
- [ ] `docs/roadmap/v5/PARITY_GAPS.md` DX.5 → Historical
- [ ] README + localized variants updated for IR-emission examples
- [ ] CLAUDE.md release-history bullet added

### Phase 4 (validation)

- [ ] `make lint` clean
- [ ] Goldens 66/66 byte-identical
- [ ] `bash scripts/verify_fixed_point.sh` reports STRICT (0 diff)
- [ ] `tests/test_cli_help.py` + `tests/test_cli_default.py`: all pass
- [ ] Manual smoke: `mnc hello.mn` runs; `mnc emit-llvm hello.mn` emits IR
- [ ] `bash scripts/build_from_seed.sh` clean (no seed refresh required)

### Documentation + release

- [ ] `CHANGELOG.md` `[5.9.1]` block filled in (BREAKING-flagged)
- [ ] `docs/roadmap/v5/v5.9.1/SESSION_REPORT.md` written
- [ ] `VERSION` bumped 5.9.0 → 5.9.1
- [ ] `git tag v5.9.1` — pending user approval per project rule

---

## What this plan trusts vs. what it gates

**Trusts:**
- v5.9.0 strict fixed-point holds at HEAD (verified at v5.9.0 ship).
- The Python CLI's `mapanare emit-llvm` precedent is the right
  template for the native CLI surface.
- `__mn_file_write` works on Linux + macOS + Windows. The native
  runtime exports it; v5.9.0 added the test coverage that
  surfaces any platform-specific bug.

**Gates on Phase 4 validation:**
- Strict fixed-point holds (DX.5 must not regress the v5.9.0
  milestone).
- `tests/test_cli_default.py` covers the deprecation note path.
- The stderr deprecation note is line-1 of `mnc <file>.mn`'s
  stderr — it must NOT appear on `mnc emit-llvm`'s path.

---

## Cross-version coordination

This release is **independent** of any v5.10.0 work (Win.1b
bundled toolchain). The two surfaces don't overlap:
- v5.10.0: ships LLVM/clang inside the install bundle so DX.3's
  install-instructions become a fallback only.
- v5.9.1: dispatch-layer change in `main.mn`. Driver layer.

If v5.10.0 is in progress when v5.9.1 is ready, ship sequentially
to keep release notes clean.

This release **removes** the deprecation note in v5.11.0. The
v5.11.0 PLAN should track that as a one-line cleanup item.
