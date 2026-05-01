# v5.23.2 — Te.3.B — bootstrap brace-deprecation mirror

**Status:** SHIPPED (ready, not tagged).
**Scope:** Te.3.B.1–Te.3.B.5 from `PLAN.md`. Third release in the
v5.23–v5.24 recovery arc — see
`docs/roadmap/v5/RECOVERY_ARC_v5.23-v5.24.md`.
**Breaking:** No (additive — adds warnings on previously-silent
shapes; no parser / IR / runtime semantics changed).
**Strict 3-stage fixed point:** preserved at **239,835 lines / 0
diff** (17-release strict streak; +350 lines vs v5.23.1's 239,485,
expected from the new C-extern call sites + parser.mn changes).
**Goldens:** 95/95 preserved.
**Bb.\* seed refresh:** required (mirrors v5.17.0 Sh.E precedent).

---

## Headline

Closes the **asymmetric closure** flagged independently by 3 v5.22.0
panel reviewers (Coral M1 + Anaconda §3 + Rattler #1):

1. **Python detector missed single-line `{...}` shape.** Pre-v5.23.2
   the detector was line-based — counted only lines whose trailing
   non-comment char was `{`. Single-line `fn main() { print("hi") }`
   ended in `}` and was silently uncounted. The PRE_PANEL_AUDIT.md's
   own canonical pre-flight test command demonstrated the gap by
   emitting **no warning** instead of the expected one.
2. **Native `mnc-stage1` had zero brace-deprecation logic at all.**
   `grep MAPANARE_NO_BRACE_WARNING mapanare/self/*.mn` returned zero
   hits. The Python detector itself had no `.mn` mirror — **PY:
   closed | SH: open** asymmetric state that should have been
   tracked per `.reviews/CARRY_FORWARD.md` dual-closure convention.

v5.23.2 fixes both at the same algorithm layer, byte-for-byte, with
a single source of truth (C-runtime export):

- **Te.3.B.1** — Python detector rewritten as a per-line
  character-walker with three rules ((a) line-end, (b) block-keyword
  context with no standalone `=`, (c) `=>` immediate prefix).
  Catches single-line shapes; correctly excludes struct / map
  literals (`Point { x: 1, y: 2 }`) that the naive walker would
  false-positive.
- **Te.3.B.2** — same algorithm ported to C runtime as
  `__mn_count_user_brace_block_openers` + `__mn_emit_brace_
  deprecation_warning`. `mapanare/self/parser.mn::parse` calls both
  before `__mn_indent_to_braces`. Same C-routing rationale as v5.14.1
  B.5 `__mn_indent_to_braces` — single source of truth, byte-identity
  by construction, sidesteps any bootstrap-lower string-walking
  pathologies.
- **Te.3.B.3** — new
  `tests/bootstrap/test_brace_deprecation_mirror.py` (11 cases) is
  the byte-identity contract.
- **Te.3.B.4** — `.reviews/v5.22.0/PRE_PANEL_AUDIT.md` updated with
  v5.23.2-update note documenting the gap closure for the v5.27.0
  panel.
- **Te.3.B.5** — Bb.\* seed refresh (`bootstrap/seed/linux-x86_64/
  mnc` + `mnc.sha256`). Required because the v5.10.0-vintage seed
  predates the new C-runtime exports — without refresh,
  `bash scripts/build_from_seed.sh` failed at stage 1 with the seed
  unable to lower the new builtin call sites.

---

## What changed

### Te.3.B.1 — Python detector rewrite (`mapanare/parser.py`)

The pre-v5.23.2 implementation was a per-line scanner that:

1. Masked strings/chars to spaces, dropped `//` comments.
2. Counted a line if `line_code.rstrip().endswith("{")` and not
   `endswith("#{")`.

This shape silently missed:

- Single-line block: `fn main() { print("hi") }` ends in `}`, not
  `{` — uncounted.
- Single-line match arm: `Some(y) => { y + 1 }` — uncounted.

v5.23.2 rewrote the detector as a per-line character-walker over
masked code (strings/chars/`//` comments → spaces, preserving column
positions). For each `{` (skipping `#{` map literals and `${`
interpolation), three rules in order:

- **Rule (a)** — `{` is the last non-WS char on its line. Catches
  multi-line `fn main() {` / `struct Point {` / `match expr {`.
- **Rule (b)** — a block keyword (`fn`, `if`, `else`, `while`,
  `for`, `match`, `loop`, `do`, `try`, `impl`, `trait`, `agent`,
  `struct`, `enum`) appears on the same line before the `{`, AND
  there is no standalone `=` between the latest such keyword and
  the `{`. The `=` filter is essential — it excludes
  implicit-return shapes like `fn make() -> Point = Point { x }`,
  which is an expression, not a block. The `=` detection excludes
  `==`, `!=`, `<=`, `>=`, `=>`, `+=`, `-=`, `*=`, `/=`, `%=` so
  comparison/compound operators don't disqualify.
- **Rule (c)** — the chars immediately before the `{` (after WS)
  are `=>`. Catches match-arm and closure block bodies on lines
  that don't have a block keyword (e.g.,
  `        Some(y) => { y + 1 }`).

The `=` filter and rule (c) together correctly distinguish:

- `fn main() { ... }` — counted (rule (b), no `=`).
- `fn make() -> Point = Point { x }` — NOT counted (rule (b) sees
  `=` between `fn` and `{`).
- `Point { x: 1, y: 2 }` in colon body — NOT counted (no rule
  matches).
- `Some(y) => { y + 1 }` — counted (rule (c)).

Sweep across the corpus confirms canonical colon-style files
(`tests/golden/06_struct.mn`, `81_struct_shorthand.mn`, etc.) stay
at 0 — no false-positive UX regression.

False-positive surface is bounded to multi-line struct literals
(`let p = Point {` on a line by itself) — absent from the corpus,
documented in the docstring.

### Te.3.B.1.A — synthetic-filename suppression

`mapanare/parser.py::_parse_interp_expr` recursively calls
`parse(filename="<interp>")` on a brace-style synthesized wrapper
(`fn __interp__() { return <expr> }`) for every interpolated
expression. The new detector would otherwise fire on every
interpolated string in any user file.

Fix: skip the warning when filename is wrapped in `<...>` (synthetic
sentinel). Native bootstrap is unaffected — `parser.mn::split_interp_
parts` routes through `parse_expr` directly, never re-enters
`parse()`. Filter is Python-side only.

### Te.3.B.2 — Native mirror via C runtime

Following the v5.14.1 B.5/B.6 precedent for `__mn_indent_to_braces`,
the detector lives in C — not in `.mn` as PLAN initially proposed.
Rationale:

- **Single source of truth.** Same algorithm runs from both
  bootstraps, so byte-identity is by construction (the cross-
  bootstrap mirror test verifies). A `.mn` port would have to mirror
  the Python algorithm separately and could drift.
- **Bootstrap-lower pathology insurance.** The `.mn` port would
  involve non-trivial string walking with state machines and
  per-line buffer accumulation. The bootstrap lower at
  v5.14.0+ has documented pathologies on this shape
  (`String.split` index-mangle; deep nested if/else PHI predecessor
  mismatch — see `runtime/native/mapanare_core.c` line 3699).
  Routing through C sidesteps both classes by construction.
- **Performance.** Per-line buffer accumulation in `.mn` would be
  O(n²) string concatenation; in C it's a single linear pass with
  one alloc'd masked buffer.

Two new C exports:

- `MN_EXPORT int64_t __mn_count_user_brace_block_openers(MnString)`
  — pure counting fn, mirrors Python `count_user_brace_block_
  openers` algorithm character-by-character.
- `MN_EXPORT void __mn_emit_brace_deprecation_warning(MnString
  path, int64_t count)` — handles `MAPANARE_NO_BRACE_WARNING=1`
  env opt-out via `getenv()`, formats warning text byte-identical
  to Python's `_emit_brace_deprecation_warning`, writes to stderr.

Bootstrap wiring (5 files, ~30 LOC):

- `mapanare/self/semantic.mn` — both names added to
  `is_builtin_function` + global scope `define_in_scope` calls.
- `mapanare/self/lower.mn` — handle the call sites (return Int /
  void respectively, emit `Instruction::Call`).
- `mapanare/self/emit_llvm.mn` — `declare_runtime_fn` for both
  exports + `nounwind willreturn` attribute hints.
- `mapanare/self/parser.mn` — `parse()` calls
  `__mn_count_user_brace_block_openers(source)` then
  `__mn_emit_brace_deprecation_warning(filename, brace_count)` if
  count > 0, **before** `__mn_indent_to_braces`. Order matters —
  the preprocessor would otherwise convert every colon-block into
  brace form, making the two indistinguishable post-preprocess.

### Te.3.B.3 — Cross-bootstrap mirror test

`tests/bootstrap/test_brace_deprecation_mirror.py` — 10 cases via
`@pytest.mark.parametrize` + 1 explicit opt-out test. Each case:

1. Writes a fixture with the source.
2. Compiles via Python `mapanare emit-llvm`, captures stderr.
3. Compiles via native `mnc-stage1 emit-llvm`, captures stderr.
4. Filters stderr lines containing `"deprecated"` from both.
5. For `expected_count == 0`: asserts both warnings empty.
6. For `expected_count > 0`: asserts both contain `"deprecated"`,
   asserts byte-identical text, asserts `(N occurrence[s])` shape.

The 11 test cases:

| Case | Source shape | Expected count |
|---|---|---:|
| `single_line` | `fn main() { print("hi") }` | 1 |
| `multi_line` | `fn main() {\n    print("hi")\n}\n` | 1 |
| `escaped_brace` | `print("\{not a block}")` | 0 |
| `brace_in_string` | `print("{")` | 0 |
| `brace_in_comment` | `// {` then code | 0 |
| `map_literal` | `let m = #{ 1: 2 }` | 0 |
| `interp_inside_string` | `print("${n}")` | 0 |
| `mixed_colon_brace` | colon fn + brace fn | 1 |
| `no_braces` | pure colon | 0 |
| `multiple` | three brace fns | 3 |
| `opt_out` | brace fn + `MAPANARE_NO_BRACE_WARNING=1` | 0 in both |

11/11 PASS at HEAD.

### Te.3.B.4 — PRE_PANEL_AUDIT.md template update

`.reviews/v5.22.0/PRE_PANEL_AUDIT.md` "Pre-flight commands" section
gained:

- A **v5.23.2 update note** at the top of the brace-deprecation flow
  explaining that the canonical pre-flight command now fires the
  warning correctly post-Te.3.B.1, and that pre-v5.23.2 the gap was
  silent.
- A **native parallel command** (`mapanare/self/mnc-stage1 emit-llvm
  /tmp/brace.mn -o /tmp/x.ll 2>&1 | head -3`) showing the byte-
  identical native warning post-Te.3.B.2.
- An **opt-out parallel** for the native side
  (`MAPANARE_NO_BRACE_WARNING=1 mapanare/self/mnc-stage1 ...`).
- The bootstrap-mirror-test count updated:
  `test_brace_deprecation_mirror.py 11/11 (added v5.23.2)`.

### Te.3.B.5 — Bb.\* seed refresh

Required. The v5.10.0-vintage seed at
`bootstrap/seed/linux-x86_64/mnc` does not know about the new
C-runtime exports — its `is_builtin_function` rejects unknown names,
so `bash scripts/build_from_seed.sh` failed at stage 1.

Refreshed per the v5.17.0 Sh.E precedent:

- Copied `mapanare/self/mnc-stage1` → `bootstrap/seed/linux-
  x86_64/mnc` (7,109,816 bytes).
- Regenerated `bootstrap/seed/linux-x86_64/mnc.sha256`.

Post-refresh `bash scripts/build_from_seed.sh` succeeds — stage1 IR
239,835 lines, stage2 IR 239,835 lines, smoke test OK.

---

## Strict 3-stage fixed point

`bash scripts/verify_fixed_point.sh --keep`:

```
[Stage 1] stage1 compiles mnc_all.mn → stage2.ll
  stage2.ll: 239835 lines
  llvm-as: OK
[Stage 2] stage2 compiles mnc_all.mn → stage3.ll
  stage3.ll: 239835 lines
  llvm-as: OK
[Verify] Fixed point: diff stage2.ll stage3.ll
  ✓ FIXED POINT REACHED
  stage2.ll == stage3.ll (239835 lines, 0 diff)
```

**+350 lines vs v5.23.1's 239,485**, expected from:

- New `parse()` call sites for `__mn_count_user_brace_block_openers`
  + `__mn_emit_brace_deprecation_warning` (2 builtin call instances
  in `mapanare/self/parser.mn`).
- New `declare_runtime_fn` declarations in `mapanare/self/
  emit_llvm.mn` (2 declarations into the IR's runtime decl
  preamble).
- New `is_builtin_function` + scope entries in `mapanare/self/
  semantic.mn` (4 `define_in_scope` calls).
- New lowering arms in `mapanare/self/lower.mn` (2 call lowerings).

17-release strict streak preserved (longest in project history,
held since v5.9.0).

---

## CI gate

The new
`tests/bootstrap/test_brace_deprecation_mirror.py` runs in the same
`pytest tests/bootstrap/` invocation that already runs the 4
existing mirrors (`test_te5_mirror`, `test_chained_cmp_mirror`,
`test_string_interp_mirror`, `test_comprehension_mirror`,
`test_indent_preprocessor`). 53 mirror tests now / was 42.

---

## Files touched

| File | LOC delta | Notes |
|---|---:|---|
| `mapanare/parser.py` | +120 / -80 | Te.3.B.1 detector rewrite + synthetic-filename suppression |
| `tests/test_brace_deprecation.py` | +50 / 0 | 5 new regression tests for the rewrite |
| `runtime/native/mapanare_core.c` | +220 / 0 | Te.3.B.2 — C-runtime detector + warning emitter |
| `mapanare/self/semantic.mn` | +10 / 0 | Te.3.B.2 — register builtins + scope |
| `mapanare/self/lower.mn` | +10 / 0 | Te.3.B.2 — lower the calls |
| `mapanare/self/emit_llvm.mn` | +12 / 0 | Te.3.B.2 — IR declarations + attrs |
| `mapanare/self/parser.mn` | +12 / 0 | Te.3.B.2 — hook into `parse()` |
| `mapanare/self/mnc_all.mn` | regenerated | concat from above |
| `tests/bootstrap/test_brace_deprecation_mirror.py` | +160 / 0 | NEW — 11-case mirror |
| `.reviews/v5.22.0/PRE_PANEL_AUDIT.md` | +18 / -3 | Te.3.B.4 |
| `bootstrap/seed/linux-x86_64/mnc` | binary refresh | Te.3.B.5 |
| `bootstrap/seed/linux-x86_64/mnc.sha256` | sha refresh | Te.3.B.5 |
| `VERSION` | 5.23.1 → 5.23.2 | Phase 6 |
| `CHANGELOG.md` | + `[5.23.2]` block | Phase 6 |
| `CLAUDE.md` | + v5.23.2 release note | Phase 6 |

---

## Validation checklist (all GREEN)

- [x] `bash scripts/verify_fixed_point.sh --keep` — 239,835 lines /
      0 diff.
- [x] `python3 scripts/test_native.py --stage1
      mapanare/self/mnc-stage1` — 95/95.
- [x] `bash scripts/build_from_seed.sh` — clean (post-Bb.\* seed
      refresh).
- [x] `make lint` — ruff + black + mypy clean.
- [x] `pytest tests/test_brace_deprecation.py` — 28/28 (was 23/23
      pre-v5.23.2; +5 regression tests for the rewrite).
- [x] `pytest tests/bootstrap/test_brace_deprecation_mirror.py` —
      11/11.
- [x] `pytest tests/bootstrap/test_{te5,chained_cmp,string_interp,
      comprehension}_mirror.py` — all green; 42 + 11 = 53 total
      mirror tests.
- [x] Te.3.B.1 manual: single-line `fn main() { print("hi") }`
      fires warning in Python.
- [x] Te.3.B.2 manual: same source fires byte-identical warning in
      `mnc-stage1`.
- [x] `MAPANARE_NO_BRACE_WARNING=1` opt-out honored in both
      bootstraps.

---

## Out of scope (held)

- **Te.3 hard removal of `{}`** — v6.0.
- **`mnc fmt --keep-braces` polish for single-line shapes** —
  Coral L3, deferred to v5.24.x if needed.
- **Hy.\* structural hygiene gates** — v5.24.0.
- **Manifesto M2 / SPEC corpus M3** — v5.24.1.
- **Self-host source migration** to colon-only — `mnc_all.mn` still
  emits 3,116-occurrence warning on every parse, but those are
  legitimate deprecated brace usages in `.mn` source (mostly
  single-line `=> { ... }` match-arm bodies in `ast.mn` and
  `lower.mn`). Migration is a separate Te.3.D-style mechanical
  rewrite tracked for v5.24.0+.

---

## Carry-forward delta

Te.3 hollow / asymmetric closure (Coral M1 + Anaconda §3 + Rattler
#1) — **CLOSED at v5.23.2.**

Aggregate state entering v5.23.x → v5.27.0 panel:

- v5.22.0 panel inherited: 4 HIGH / 8 MEDIUM / ~12 LOW.
- v5.23.0 closed all HIGH (15 items mechanical).
- v5.23.1 closed Mb.\* memory hygiene (V.9, V.6, V.7, V.8 + 3 Te.5
  ASan).
- v5.23.2 closes Te.3 asymmetric (1 MEDIUM × 3 reviewer cycles).
- Remaining open: ~3 MEDIUM (Te.3.C, hygiene gates, manifesto
  drift) + ~7 LOW + 1 v6.0-rescoped.

---

## References

- `docs/roadmap/v5/v5.23.2/PLAN.md`
- `docs/roadmap/v5/v5.23.2/PROMPT.md`
- `docs/roadmap/v5/RECOVERY_ARC_v5.23-v5.24.md`
- `docs/roadmap/v5/v5.14.1/SESSION_REPORT.md` (B.5 C-routing
  precedent)
- `docs/roadmap/v5/v5.17.0/SESSION_REPORT.md` (Sh.E seed-refresh
  precedent)
- `.reviews/v5.22.0/05-coral.md` finding M1
- `.reviews/v5.22.0/03-anaconda.md` §3
- `.reviews/v5.22.0/01-rattler.md` finding #1
