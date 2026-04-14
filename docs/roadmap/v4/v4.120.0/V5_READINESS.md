# Mapanare v5 Readiness — Honest Gap Analysis

> Written at v4.119.0 (2026-04-14) as **informational input** to the
> v4.120.0 panel. This is not a recommendation to tag v5. It is a
> checklist: what is done, what is partial, what is planned, and what
> is unimplemented. The panel decides based on this plus the
> retrospective and the benchmark report.
>
> **Stance: neutral.** No advocacy. Tone favours the reader's ability
> to grade the evidence over any argument from the author.

---

## Decision rule (the mechanical gate)

From `POST_RECOVERY_MASTER_PROMPT.md` and `V5_DECISION.md` (v4.99.0):

- **Aggregate ≥ 9.0** AND **0 NEEDS WORK** → Option A — tag `v5.0.0`
- **Aggregate 8.5 – 9.0** → Option C — tag + continue
- **Aggregate < 9.0** with any NEEDS WORK → Option B — continue v4.121.0+

The panel is not being asked for a narrative judgment. The decision
follows the aggregate and the NEEDS WORK count. The material in this
file is provided to let each reviewer calibrate.

---

## What a "v5" tag would be

v5.0.0 is a **major version**: first breaking-change line after v4.x.
A shipped v5 carries the expectation that the language is stable at
this surface, the compiler is self-hosting in production, and the
runtime is safe to link into real programs.

Tagging v5 does **not** require:
- Every feature on `docs/roadmap/ROADMAP.md` to be implemented. The
  roadmap explicitly defers items like tensor reshape, stepped slices,
  and full suspension async to v5.x minor releases.
- `mnc-stage1` to produce byte-identical IR vs the Python bootstrap.
  Fixed-point stage1 → stage3 convergence is a self-hosting milestone;
  it is legitimate to ship v5 with a Python bootstrap that is the
  reference emitter and a self-hosted compiler that passes golden with
  known semantically-equivalent divergences.
- The CI matrix to grow beyond its current 10 enforcing gates.

Tagging v5 **does** require:
- The language surface (grammar, keyword list, SPEC) being stable
  enough that v5.0.1 can fix bugs without breaking v5.0.0 programs.
- The Python bootstrap producing correct code for every feature the
  SPEC claims.
- The self-hosted compiler being *real*: compiles real programs,
  produces real IR, not just parses and returns zero.
- The standard library having enough surface to do practical work
  (file I/O, HTTP, JSON, collection types, async).
- CI catching regressions that real users would hit.
- Documentation accurately reflecting what works and what doesn't.

---

## Status matrix — feature by feature

Color key: ✅ done · ◐ partial · ⬜ planned · ✖ not implemented.

### Language core

| Feature | Status | Evidence |
|---|---|---|
| Parser (LALR, 13-level precedence) | ✅ | `mapanare/mapanare.lark`, Python + self-hosted parsers both complete |
| AST (dataclasses) | ✅ | `mapanare/ast_nodes.py` + `mapanare/self/ast.mn` (781 lines, mirror) |
| Semantic checker (two-pass) | ✅ | `mapanare/semantic.py` + `self/semantic.mn` (1,729 lines) |
| MIR lowering | ✅ | `mapanare/lower.py` + `self/lower.mn` (3,602 lines) |
| MIR optimiser passes | ✅ | `mir_opt.py`; 4 zero-ROI self-hosted passes disabled v4.111.0 |
| LLVM IR emission | ✅ | `emit_llvm_text.py` + `self/emit_llvm.mn` (3,206 lines) |
| C source emission | ✅ | `emit_c.py` |
| WebAssembly (WAT) emission | ✅ | `emit_wasm.py` ~2,785 lines; WASI support |
| Bilingual keywords (English + Spanish) | ✅ | v3.x, regression-tested |
| Module imports | ✅ | cross-module at Python-bootstrap level (v3.7.0); self-hosted fixed-point still blocked on Sh.8 |
| `const` keyword | ◐ | v4.24.0 parser alias for `ModuleLetDef`; no immutability enforcement; v4.27.0 removed from grammar (Path B); v5.x will add real `ConstDef` if adopted |
| `async fn` + `await` + `block_on` | ✅ | Python bootstrap lowers; native runtime links (v4.102.0); 5/5 async benchmarks execute |
| `for await` | ⬜ | SPEC §29.7 explicitly planned/v5.x |
| `@gpu` / `@cuda` / `@vulkan` | ✅ | v2.0.0 LLVM codegen; PTX/SPIR-V embedding; runtime dlopen |
| FFI bindings (C / Python) | ✅ | v4.25.0 shipped broken; v4.27.0 fixed (FFI DCE, PIC, argtypes/restype) |
| Tensor literals, indexing, broadcasting | ✅ | v4.45.0 |
| Tensor reshape, mutable views, stepped slices | ⬜ | SPEC-listed v5.x items; not implemented |
| Error line numbers in diagnostics | ✅ | v3.10.0 |
| DWARF debug info | ✖ | SPEC §21.3 defers to v5.x; `-g` prints deferral warning (v4.29.0) |

### Runtime

| Feature | Status | Evidence |
|---|---|---|
| Arena-based memory (no GC) | ✅ | v0.x; regression-tested |
| Lock-free SPSC + thread-pool scheduler | ✅ | v4.93.0 scheduler; v4.102.0 first native async run; v4.115.0 user async I/O |
| Cooperative agent scheduler (mobile) | ✅ | v2.0.0 line |
| Signal reactivity (computed, subscribers, batching) | ✅ | v4.28.0 race closed |
| Stream operators (map/filter/take/skip/fold) | ✅ | v2.0.0 line |
| TCP + TLS (OpenSSL via dlopen) | ✅ | v4.x C runtime |
| File I/O, event loop (epoll / select) | ✅ | v4.115.0 native async I/O demos |
| String interning (configurable cap) | ✅ | v4.x; thread-safe after v4.28.0 |
| Tagged-pointer UB | ✅ REMOVED | v4.100.0: `MnString` bitfield replaces `mn_tag_heap` |
| Memory profiling (`mapanare_memory_stats()`) | ✅ | v2.0.0 |
| Full suspension async (preemptive) | ✖ | v5.x work; current cooperative model is the documented position |

### Self-hosted compiler (`mapanare/self/*.mn`)

| Milestone | Status | Evidence |
|---|---|---|
| 10 modules totalling 39,763 lines of `.mn` | ✅ | `wc -l mapanare/self/*.mn` |
| Parses its own source | ✅ | `mnc-stage1` compiles `mapanare/self/mnc_all.mn` |
| Emits IR that `llvm-as` validates | ◐ | passes for most modules; stage2 0/11 unchanged since v4.111.0 |
| Python-bootstrap produces golden | ✅ | 64/64 |
| Native mnc-stage1 produces golden | ◐ | 26/64 literal, 39/64 effective (Cat. A — same output, bootstrap inlines where stage1 does not) |
| Fixed-point stage1 → stage3 identity | ✖ | **Sh.8** (self-hosted `semantic.mn` lacks `None`/`Some`/`Ok` constructor registration) blocks stage1 self-compilation; `build_stage1.py` bypasses via `skip_check=True` |
| Async lowering in self-hosted | ✖ | **Sh.4** — async missing from self-hosted; 5 golden tests fail under mnc-stage1 |
| `const` lowering in self-hosted | ✖ | **Sh.5** — 2 tests |
| Tensor lowering in self-hosted | ✖ | **Sh.6** — 5 tests |
| Closure types in self-hosted | ✖ | **Sh.7** — 1 test |

### Standard library

| Module | Status | Notes |
|---|---|---|
| `stdlib/*` .mn files compilable | ✅ | 35/35 as of v3.6.0 |
| Core collection types (List, Map, Result, Option) | ✅ | built-in |
| Async primitives (Future, block_on) | ✅ | v4.115.0 |
| File I/O (read/write, async) | ✅ | `__mn_file_read_async` user-callable blocked on Sh.10 (pre-requisite Sh.9a) |
| HTTP client | ✅ | v4.115.0 demo (real GET to example.com) |
| TLS (OpenSSL via dlopen) | ✅ | C runtime |
| JSON | ⬜ | stdlib `.mn` module planned |
| Logging | ◐ | `tracing.py` (Python-side) OpenTelemetry-compat |
| SQL / database | ◐ | `mapanare_db.c` wired into build since v4.29.0 |
| HTML templating | ◐ | `mapanare_html.c` wired into build since v4.29.0 |
| AI/LLM drivers (`stdlib/ai/*`) | ✅ | LLM, embeddings, RAG |

### Ecosystem

| Package | Status | Notes |
|---|---|---|
| **Dato** (DataFrame/numpy equivalent) | ✅ | repo at `github.com/Mapanare-Research/dato` |
| `net/crawl` (web crawler) | ✅ | agents-based |
| `security/scan` (vulnerability scanner) | ✅ | agents-based |
| `security/fuzz` (fuzzer) | ✅ | agents-based |
| Package manager / registry | ⬜ | **not implemented.** Single biggest ecosystem gap vs mainstream v5 languages |
| Language server (LSP) | ◐ | directory exists; not mentioned in CI |
| Playground | ✅ | `playground/` (WASM-based) |
| CLI (`mapanare run`, `build`, `check`, etc.) | ✅ | shipped since early v4; note: 14 pre-rename tests assert on `mapanare compile` (v4.117.0 flaky audit) |

### Documentation

| Document | Status | Evidence |
|---|---|---|
| `docs/SPEC.md` | ✅ | 4.116.0 Live header; sync-discipline note; §29 async status; §2.1.1 reserved keyword table |
| `docs/manifesto.md` | ✅ | design philosophy |
| `docs/getting-started.md` (624 lines) | ✅ | full tutorial |
| `docs/guides/getting_started.md` (244 lines) | ✅ | v4.116.0 — practical walk for compiled-language developers |
| `docs/guides/async.md` (244 lines) | ✅ | v4.115.0 |
| `docs/guides/debugging.md` | ✅ | v4.116.0 rewrite |
| `docs/cookbook/async.md` | ✅ | v4.116.0 update (Sh.9a/9b recipes) |
| `README.md` | ✅ | v4.116.0 update; badge at 4.116.0 |
| `docs/rfcs/*` | ✅ | RFC archive |
| Roadmap (`docs/roadmap/*`) | ✅ | v4.116.0 row through v4.118.0 row published; v4.119.0 + v4.120.0 PLAN.md + PROMPT.md on disk |
| CHANGELOG | ✅ | `[4.0.0]` through `[4.118.0]` entries; `[Unreleased]` header |

### CI / quality gates

| Gate | Enforcing | Since |
|---|---|---|
| Black | ✅ | v4.0.0 |
| Ruff | ✅ | v4.0.0 |
| Mypy | ✅ | v4.0.0 |
| pytest (3.11 + 3.12) | ✅ | v4.0.0 |
| Native C runtime (plain gcc) | ✅ | v4.x |
| AddressSanitizer CI | ✅ | v4.105.0 |
| ThreadSanitizer CI (async) | ✅ | v4.105.0 (extended v4.117.0) |
| Valgrind full golden | ✅ | v4.105.0 |
| WASM cross-compile | ✅ | v2.0.0 line |
| Android cross-compile | ✅ | v2.0.0 line |
| Coverage | ◐ informational | v4.117.0 |

---

## Known gaps that would embarrass a v5 label

These are the things a new Mapanare user would hit and find unpleasant.
The panel can weigh each against the v5 bar.

1. **Self-hosted async/tensor/const gaps.** 13 of the 25 real self-
   hosted golden failures are features the Python bootstrap supports
   but `mnc-stage1` has not learned yet. A user who writes idiomatic
   Mapanare (async for a network client, tensors for data work, const
   for program constants) and then tries to run it through the native
   compiler will hit `ERROR` or silent wrong output. **Impact: HIGH.**
   Mitigation: the Python bootstrap handles all of these; users who
   `python -m mapanare run` get correct behaviour. Recommended v5.x
   work.
2. **Fixed-point convergence cannot be proved today.** `verify_fixed_
   point.sh` fails at Stage 1 because of Sh.8. The v4.112.0 rename
   from "fixed-point verification" to "divergence analysis + byref
   fix" is honest, but a user who reads "self-hosting compiler" and
   expects a proven stage1 = stage2 = stage3 identity will not find
   it. **Impact: MEDIUM** (self-hosting is a project-internal
   milestone; user-visible correctness is unaffected).
3. **No package manager / registry.** A v5 language tag invites
   comparison with Go, Rust, and Python. All three have a canonical
   package registry. Mapanare does not. **Impact: MEDIUM for
   adoption.** The `stdlib/` surface is adequate for single-program
   work; a package registry is a v5.x deliverable.
4. **Boxed-enum payload overhead.** Docket **Rt.1**. `enum_match` is
   24× slower than C gcc and 2× slower than Rust. A user who writes
   enum-heavy dispatch will notice. **Impact: MEDIUM** (no
   correctness bug; the benchmark is honest about the gap).
5. **`List<Int>` indexing quirk in a print context.** Docket **Qs.1**:
   `arr.push(42); print(str(arr[0]))` prints `<?>`. Did not surface
   in the v4.118.0 benchmark suite (all checksums correct), but the
   test that caught it in v4.107.0 still fails. **Impact: LOW but
   user-visible if hit.**
6. **`optimizer.py` at 9% coverage.** Likely dead code per the v4.117.0
   coverage report. Either delete or re-wire. **Impact: COSMETIC**
   (nothing is broken; the repo just has a 1,000-line module that
   isn't called).
7. **14 stale CLI tests** pre-rename. v4.117.0 flaky audit catalogued
   them; v5 should fix or delete. **Impact: COSMETIC.**
8. **TBAA metadata declared but not wired.** Docket **TBAA.1**. Module
   header defines type nodes that are never attached to a load or
   store. **Impact: COSMETIC** (zero runtime effect; comment in
   `emit_llvm_text.py:910-926` misleading).

No gap on this list produces incorrect code for a program the SPEC
promises works. Every gap is documented in a docket, the SPEC, or the
session reports. Nothing is hidden.

---

## What would need to change between v4.119.0 and v5.0.0 (if tagged)

**Nothing.** v4.119.0 is the last release before the panel. If the
panel votes Option A, the `v5.0.0` tag would be applied to the
v4.119.0 commit (or a successor no-change commit), CHANGELOG
`[5.0.0]` would replace `[Unreleased]`, the `VERSION` file would read
`5.0.0`, and the `dev` branch would continue as `v5.1.0` development.

No additional engineering work is required to "earn" v5 between now
and the panel. The v4.99.0 panel's three NEEDS-WORK items (tagged
pointer, list indexing, async link) are **closed with evidence**. The
v4.106.0 patch item (Rt.1 lambda signature) is closed. The v4.114.0
Phase D panel's audit (`DOCKET_AUDIT.md`) walked 11 items with
`file:line` evidence.

Whether "nothing additional is required" corresponds to ≥ 9.0
aggregate and 0 NEEDS WORK is the panel's judgement.

---

## Author's neutral summary

- The recovery arc (20 releases) **closed the v4.99.0 docket
  completely**.
- The self-hosted compiler **runs the golden suite** (26/64 literal,
  39/64 effective) — vs. 0/61 at v4.99.0.
- The async benchmarks **link and execute** — vs. 0/5 at v4.94.0.
- The benchmark geomean **narrowed from 9.5× to 5.46× vs. C gcc** —
  the one load-bearing performance win (string_concat) is entirely
  v4.108.0's MIR rewrite.
- Ten CI gates are **enforcing**, including three sanitizer gates that
  catch regressions a user would hit.
- Documentation is **current** through v4.116.0; the v4.118.0 benchmark
  report is new.
- Eleven dockets remain open; none are CRITICAL; two are HIGH and the
  rest are MEDIUM / LOW. All are named, scoped, and sized.

**Whether this is a v5 is for the panel.** The evidence is in the
repository. The decision rule is mechanical. This document states only
what is done, what isn't, and where the reader can verify each item.

## Cross-references

| To verify | Read |
|---|---|
| Recovery arc narrative | `RETROSPECTIVE.md` (this directory) |
| Hard numbers | `STATISTICS.md` (this directory) |
| Claim-level verification of SESSION_REPORTs | `AUDIT_NOTES.md` (this directory) |
| Benchmark evidence | `benchmarks/FINAL_REPORT_v4.120.md` |
| v4.99.0 docket closure | `docs/roadmap/v4/v4.114.0/DOCKET_AUDIT.md` |
| Open docket ledger | `.reviews/CARRY_FORWARD.md` |
| Language spec | `docs/SPEC.md` |
