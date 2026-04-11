# Mapanare v4.27.0 — Honesty Recovery (CRITICAL items)

> **Recovery release. Zero new features.** v4.26.0 received the largest
> single-cycle review regression in project history (9.79 → ~8.2). Seven
> independent reviewers converged on the same finding: the v4.18.0–v4.26.0
> arc shipped parseable syntax without semantic enforcement or runtime
> wiring. v4.27.0 closes the 8 CRITICAL items and brings the
> CHANGELOG/ROADMAP/docs back into agreement with what the code actually does.

**Status:** PLANNED
**Breaking:** No (recovery — strictly closes claimed-but-not-real features)
**Prerequisite:** v4.26.0
**Estimated work:** 1–2 days of focused work per panel consensus
**No new features. None.**

---

## The Problem

v4.26.0 review verdict: **NEEDS WORK** (4 of 7 reviewers), aggregate
~8.2/10. The panel's headline finding, restated by all 7 reviewers
independently:

> The v4.18.0–v4.26.0 arc has been shipping parseable syntax without
> semantic enforcement or runtime wiring.

Specifically, six features that the CHANGELOG, ROADMAP, and SPEC describe as
working are not actually wired through to runtime:

1. `const` is a parser alias for `ModuleLetDef` — no `ConstDef` AST node, no
   immutability, tensor `Tensor<Float>[N, N]` silently drops shape
2. `@gpu` / `@cuda` / `@vulkan` raise `NotImplementedError` at `lower.py:986`
3. `await expr` lowers to `return self._lower_expr(expr.expr)` — pure identity
4. Tensor shape `const` dimensions don't resolve (only `IntLiteral` handled)
5. v4.25.0 FFI ships broken: DCE drops non-main-reachable functions, runtime
   archive not -fPIC, ctypes wrappers have no argtypes/restype, a
   `.replace("define internal ", "define ")` sledgehammer strips all linkage
6. v4.5.0 MIR verifier never wired into `compile()` — dead code 21 versions

Plus a process collapse:

- CHANGELOG advertises tests that don't exist on disk
- Carry-forward resolution rate fell from ~64% to ~10% in one cycle
- Two v4.0.0 hard-blockers (matmul shape NULL check, dimension validation)
  are byte-identical to v3.47.0 — 27 versions overdue
- `verify_fixed_point.sh` cannot return non-zero (`EXIT=0` unconditional)
- `main.ll` version string is `mapanare 4.7.1` — 19 versions stale; the
  regression test for it is currently failing locally

This release fixes the **CRITICAL** items only. HIGH items go to v4.28.0+.

---

## Phase 1: FFI Recovery (CRITICAL items #1–#4)

The v4.25.0 FFI claim "Python ctypes calls compiled Mapanare functions" is
true only for `add(int, int) -> int` and only by accident.

### Phase 1.1: Fix `bind.py` to populate argtypes/restype

- [ ] `mapanare/bind.py:135-180` — Generate `argtypes=[...]` and `restype=...`
      from each function's `MIRType`. Today the wrapper has neither, so ctypes
      defaults to `c_int` for everything and silently corrupts `Float`,
      `String`, `Bool`, and struct returns.
- [ ] Map `MIRType` → `ctypes` type via a single helper:
      - `Int` → `c_int64`
      - `Float` → `c_double`
      - `Bool` → `c_bool`
      - `String` → struct of `(c_char_p, c_int64)` (Mapanare strings are `{ptr, len}`, not C strings)
      - struct return → `Structure` subclass with `_fields_` populated from the MIR struct definition
- [ ] Add `tests/bind/test_python_binding.py` covering:
      - `add(int, int) -> int` (already passes)
      - `multiply(float, float) -> float` (currently silently corrupts)
      - `greet(string) -> string` (currently silently corrupts)
      - one struct return (e.g. `Point { x: int, y: int }`)

### Phase 1.2: Stop dropping exported FFI symbols at link time

- [ ] Today, `cli.py:1366` does
      `ll_text.replace("define internal ", "define ")` over the entire module.
      This is the textual hack that masks the underlying DCE bug. **Delete it.**
- [ ] In `emit_llvm_text.py`, plumb an `exported: set[str]` parameter through
      `_emit_function`. When emitting, choose `define internal` vs `define`
      per function based on membership.
- [ ] In `cli.py:cmd_bind`, build the exported set from the bindable surface
      (every public `fn` declared in the source `.mn` file) and pass it to the
      emitter.
- [ ] Verify with `nm libmath_lib.so` — `add`, `multiply`, `greet`, and the
      struct constructors must all appear as `T` (text/global) symbols.

### Phase 1.3: Build runtime archive with `-fPIC`

- [ ] `Makefile` — add `-fPIC` to the `CFLAGS` for the runtime archive build
      rule. This is currently missing, so the FFI fallback path that
      "links without runtime" only works when the function uses zero runtime
      symbols.
- [ ] `scripts/build_stage1.py` — same fix for the script-driven build.
- [ ] Verify with `readelf -d libmapanare_rt.a 2>&1 | grep TEXTREL` — should
      have no `TEXTREL` (text relocations indicate non-PIC code).
- [ ] Verify FFI now succeeds with the runtime included:
      `python3 -c "import ctypes; ctypes.CDLL('./libmath_lib.so', ctypes.RTLD_NOW)"`

### Phase 1.4: Round-trip pytest

- [ ] `tests/bind/test_python_binding.py` — full round-trip:
      compile `examples/bind/math_lib.mn` → `libmath_lib.so` → ctypes import →
      assert `add(3,4)==7`, `multiply(2.0,3.0)==6.0`, `greet("hi")=="hello hi"`,
      and a struct round-trip.

---

## Phase 2: `@gpu` Decorator (CRITICAL #5)

The v4.18.0 CHANGELOG claim "@gpu auto-kernel extraction" is false.
`lower.py:986` literally raises `NotImplementedError`. The compiler crashes
the moment a `@gpu` function is encountered.

**Decision required (lead picks one before starting):**

### Path A: Wire @gpu to existing runtime

- [ ] Remove the `raise NotImplementedError` at `lower.py:986`
- [ ] Lower `@gpu`-decorated functions to a `MIRGpuKernel` metadata entry
      (`mir.py` already has `MIRGpuKernel`)
- [ ] Emit a CPU fallback via the existing function body
- [ ] Wire dispatch to `runtime/native/mapanare_gpu.c` via the existing
      `gpu_tensor_*` builtins (v3.46.0 — already working)
- [ ] Add a golden test that exercises `@gpu` end-to-end: define a function,
      call it, see the value flow through

### Path B: Strike the claim, delete the syntax

- [ ] Remove `@gpu`, `@cuda`, `@vulkan` decorator recognition from
      `parser.py` and `mapanare/self/parser.mn`
- [ ] Delete `lower.py:986` entirely
- [ ] Remove the GPU sections from `docs/SPEC.md`, `README.md`,
      `docs/README.es.md`, and `CHANGELOG.md` (moving them to
      `docs/roadmap/v4/v4.18.0/SUMMARY.md` as historical note)
- [ ] Note in `docs/manifesto.md` that GPU dispatch is via runtime builtins
      (`gpu_tensor_*`), not `@gpu` decorators

**Lead recommendation:** Path B if the CPU-fallback wiring is more than ~2
hours. The code that exists works (`gpu_tensor_*` builtins ship correct
results on RTX 4090). The decorator was always sugar.

---

## Phase 3: MIR Verifier Wiring (CRITICAL #6)

`mir.py:1118-1259` defines `MIRVerifier`. Zero call sites. The v4.5.0
CHANGELOG says "MIR verifier called before emission" — false for 21 versions.
The self-hosted equivalent (`lower.mn:3692`) is also unreferenced.

- [ ] `cli.py:_compile_to_llvm_ir` — add
      `MIRVerifier().verify(mir_module)` immediately before the call to the
      LLVM emitter. ~5 lines.
- [ ] Add a `--no-verify` escape hatch to `cli.py` for the rare case where a
      developer needs to bypass verification (e.g., debugging the verifier
      itself). Print a warning to stderr when used.
- [ ] `mapanare/self/main.mn:compile()` — add the equivalent call to
      `verify_module()` (defined in `lower.mn:3620-3717`) before the emit step.
- [ ] Run the full golden suite: any verifier failures get fixed at the
      lowering site (or the verifier rule gets relaxed if it's overzealous).
- [ ] The verifier currently checks: empty functions, unterminated blocks,
      terminators in middle, phi placement. None of those should fail on the
      golden corpus today — if they do, that's a v4.27.0 fix, not a v4.28.0
      defer.

---

## Phase 4: `const` Decision (CRITICAL #7)

Two viable paths. The lead picks **before starting** so Phase 4 doesn't
oscillate.

### Path A: Real `ConstDef`

- [ ] Introduce `ConstDef` AST node distinct from `ModuleLetDef` in
      `mapanare/ast_nodes.py`
- [ ] `parser.py:1444-1459` — fix the transformer to produce `ConstDef` and
      to propagate the **full `TypeExpr`**, not collapse it to `.name`. Today
      tensor shape arguments are discarded at parse time.
- [ ] `semantic.py` — track `const` immutability in the symbol table; reject
      assignment with a `Diagnostic` (after Phase 5)
- [ ] `semantic.py` — `resolve_shape_from_type` already exists; extend it to
      look up `const` identifiers in the symbol table and substitute the
      literal value
- [ ] `mapanare/self/parser.mn`, `ast.mn`, `semantic.mn`, `lower.mn` — mirror
      the change in the self-hosted compiler
- [ ] `tests/parser/test_const.py` — assert `const NAME: Type = value`
      parses; assert tensor shape with const dimension parses
- [ ] `tests/semantic/test_const.py` — assert assignment to `const` is a
      compile-time error; assert `const`-shaped tensor matches a literal-shaped
      tensor of the same size; assert `const`-shaped tensor mismatch is a
      compile error
- [ ] `tests/golden/47_const.mn` + `.ref.ll` — golden test exercising
      module-level `const` and a `const`-shaped tensor

### Path B: Revert and re-document

- [ ] Remove `const_def` rule from `mapanare/mapanare.lark`
- [ ] Remove `const_def` transformer from `parser.py`
- [ ] Remove all references to the `const` keyword from `README.md`,
      `docs/README.es.md`, `docs/SPEC.md`, `CHANGELOG.md` (v4.18.0 and v4.26.0
      entries), `docs/roadmap/v4/README.md` (v4.18.0 and v4.26.0 rows),
      `docs/roadmap/ROADMAP.md`
- [ ] Self-hosted compiler — remove `const` keyword recognition from
      `mapanare/self/lexer.mn`, `parser.mn`
- [ ] Document in `docs/SPEC.md` that there is no `const` keyword and that
      module-level `let` is the way to declare top-level immutable values

**Lead recommendation:** Path A if `parser.py:1444-1459` can be fixed in
under 1 hour. Otherwise Path B and re-cut the feature properly in v4.32.0+
when there's a clean shape-resolution architecture.

---

## Phase 5: Diagnostics Consolidation (CRITICAL #8)

Two parallel diagnostic systems exist. `diagnostics.py` is rustc-quality
(328 lines, labels, suggestions, source underlines). `semantic.py:125-151`
has its own `SemanticError` with point-only spans. Every semantic error
underlines a single character regardless of expression width.

- [ ] `semantic.py:125-151` — delete `SemanticError` and the helpers around it
- [ ] Replace all `raise SemanticError(...)` call sites with
      `Diagnostic(...).emit()` from `diagnostics.py`
- [ ] Self-hosted: cross-wire `mapanare/self/semantic.mn` error sites to
      `mapanare/self/diagnostics.mn` (or its equivalent)
- [ ] Snapshot test: pick 5 representative semantic errors, verify the new
      output shows: source filename, line number, column range (not point),
      labeled span, suggestion line where applicable
- [ ] Run the full diagnostics test suite: any test that pinned the old
      `SemanticError` text needs updating to the new `Diagnostic` text

---

## Phase 6: Honesty Sprint (paperwork)

These are editorial fixes. They take ~1 hour total but they are required
because the current state is factually false.

### Phase 6.1: CHANGELOG correction

- [ ] `CHANGELOG.md` — strike the v4.26.0 entry's claims that don't match
      ground truth:
      - "Added: `tests/parser/test_const.py`" → false unless Path A is taken
      - "Added: `tests/semantic/test_const.py`" → same
      - "Added: `tests/golden/47_const.mn`" → same; golden count is 46, not 47
      - "Added: `const` keyword for compile-time constants" → false unless
        Path A
- [ ] Add a v4.27.0 entry honestly describing the recovery work
- [ ] Move the empty `[Unreleased]` section above `[4.27.0]`

### Phase 6.2: ROADMAP correction

- [ ] `docs/roadmap/ROADMAP.md` "Where We Are" — update from v4.26.0 to
      v4.27.0; explicitly note that v4.27.0 is a recovery release after the
      v4.26.0 review verdict
- [ ] `docs/roadmap/ROADMAP.md` release history — append v4.27.0 row
- [ ] `docs/roadmap/v4/README.md` versions table — append v4.27.0 row, mark
      v4.18.0–v4.26.0 features as "shipped, stabilized in v4.27.0"

### Phase 6.3: README + SPEC correction

- [ ] If Path B for `const`: scrub `README.md`, `docs/README.es.md`,
      `docs/SPEC.md` of `const` keyword references
- [ ] Either way: scrub `README.md` and `docs/SPEC.md` of the
      `Tensor<Float, [DIM, DIM]>` syntax. The grammar form is
      `Tensor<Float>[DIM, DIM]`. Pick one and update the other.
- [ ] Strike the v4.18.0 `@gpu` auto-kernel claim from `README.md` and
      `docs/SPEC.md` if Path B for @gpu
- [ ] Strike the v4.24.0 "async/await wired end-to-end" line from
      `README.md` (await is identity until v4.30.0)

### Phase 6.4: Stale on-disk artifacts

- [ ] `mapanare/self/main.mn:32` — note that the version string regression
      will be fixed in v4.28.0; do NOT fix here. (v4.27.0 stays focused on
      CRITICAL items.) Track in `docs/roadmap/v4/v4.28.0/PLAN.md`.

### Phase 6.5: Write the SESSION_REPORT

- [ ] `docs/roadmap/v4/v4.26.0/SESSION_REPORT.md` — does not exist; create a
      truthful one summarizing what shipped and pointing at the
      `.reviews/v4.26.0/README.md` outcome
- [ ] `docs/roadmap/v4/v4.27.0/SESSION_REPORT.md` — write at the end of the
      release with measurements

---

## Exit Criteria

| # | Check | Required |
|---|-------|----------|
| 1 | `bind.py` populates `argtypes` and `restype` from MIRType | YES |
| 2 | `tests/bind/test_python_binding.py` covers Int, Float, String, Struct | YES |
| 3 | `nm libmath_lib.so` shows all exported FFI symbols as `T` | YES |
| 4 | `cli.py:1366` `.replace("define internal ", "define ")` deleted | YES |
| 5 | `libmapanare_rt.a` built with `-fPIC` (verified via `readelf -d`) | YES |
| 6 | `@gpu` either works end-to-end OR is removed from grammar entirely | YES |
| 7 | `MIRVerifier().verify()` called in `_compile_to_llvm_ir` | YES |
| 8 | `verify_module()` called in self-hosted `compile()` | YES |
| 9 | `const` is either a real `ConstDef` with tests OR removed from grammar | YES |
| 10 | `semantic.py:125-151 SemanticError` deleted; uses `diagnostics.py` | YES |
| 11 | CHANGELOG v4.26.0 entry corrected (no claims about non-existent files) | YES |
| 12 | CHANGELOG v4.27.0 entry written | YES |
| 13 | 46/46+ golden (47/47 if Path A const) | YES |
| 14 | 11/11 stage2 modules valid | YES |
| 15 | black/ruff/mypy clean | YES |
| 16 | `docs/roadmap/v4/v4.26.0/SESSION_REPORT.md` exists and is truthful | YES |
| 17 | `docs/roadmap/v4/v4.27.0/SESSION_REPORT.md` written | YES |

---

## What v4.27.0 explicitly does NOT do

These are tracked in v4.28.0+ and are **out of scope** for v4.27.0:

- v4.0.0 carry-forward matmul fixes (→ v4.28.0)
- New concurrency races (signal set/recompute, agent ring, type registry) (→ v4.28.0)
- Windows GPU init race propagation (→ v4.28.0)
- `mapanare 4.7.1` version string regression (→ v4.28.0)
- Orphaned `mapanare_db.c` and `mapanare_html.c` (→ v4.29.0)
- `extern "Python" fn` 79 xfailed tests (→ v4.29.0)
- `verify_fixed_point.sh` `EXIT=0` unconditional (→ v4.29.0)
- `await` coroutine implementation OR strike (→ v4.30.0)
- `_emit_agent_wrap` no-op stub (→ v4.30.0)
- Optimizer non-convergence ICE (→ v4.30.0)
- Stale emitter carry-forwards (i64*, void()*, list bitcast, etc.) (→ v4.30.0)
- SPEC update, Spanish README sync, User-Agent bump (→ v4.31.0)
- DWARF debug info decision (→ v4.31.0)
- CI gates that prevent future hollow features (→ v4.31.0)

The reason for the strict scope is the same reason the panel verdict was
NEEDS WORK: this version cannot contain any new features, period. Including
"and also fix this small thing." If it isn't a CRITICAL item from the
v4.26.0 panel, it goes to v4.28.0+.

---

## Verification Protocol

After **every** phase, run:

```bash
# Lint clean
black --check . && ruff check . && mypy mapanare/

# Golden tests
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1

# Stage2
python3 scripts/ir_doctor.py stage2 --timeout 60

# Phase 1 specific
python3 -m pytest tests/bind/ -v
python3 -c "import ctypes; lib = ctypes.CDLL('./libmath_lib.so', ctypes.RTLD_NOW); lib.add.argtypes=[ctypes.c_int64,ctypes.c_int64]; lib.add.restype=ctypes.c_int64; assert lib.add(3,4)==7"

# Phase 3 specific
python3 -c "from mapanare.cli import _compile_to_llvm_ir; _compile_to_llvm_ir('tests/golden/01_hello.mn')"
# (must call MIRVerifier; check via instrumented assertion or coverage tool)

# Phase 5 specific
python3 -m pytest tests/diagnostics/ -v
```

Before commit: the full validation suite that mirrors CI:

```powershell
.\dev.ps1
```
