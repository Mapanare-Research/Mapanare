# Coral -- Language Design Review of Mapanare v3.47.0

**Reviewer:** Coral
**Personality:** Thoughtful language designer who sees languages as art and challenges assumptions
**Previous Version Reviewed:** v3.45.0
**Verdict:** PASS
**Confidence:** 9/10
**Files Reviewed:**

- `mapanare/mapanare.lark` -- Grammar (473 lines, 13-level precedence climbing, bilingual keywords)
- `mapanare/types.py` -- Type system: TypeKind (26 kinds), TypeInfo, builtin registries, GPU builtins (430 lines)
- `mapanare/parser.py` -- Lark transformer: `di_stmt` maps to `PrintStmt`
- `mapanare/emit_llvm_text.py` -- LLVM text emitter (3,645 lines, GPU builtin dispatch added)
- `mapanare/emit_llvm_mir.py` -- LLVM MIR emitter (5,297 lines)
- `mapanare/self/ast.mn` -- Self-hosted AST
- `mapanare/self/parser.mn` -- Self-hosted recursive descent parser (2,255 lines)
- `mapanare/self/semantic.mn` -- Self-hosted semantic checker (1,880 lines, +36 lines: 8 GPU builtins registered)
- `mapanare/self/lower.mn` -- Self-hosted MIR lowering (3,734 lines)
- `mapanare/self/emit_llvm.mn` -- Self-hosted LLVM IR emitter (3,418 lines, GPU builtin declarations + dispatch)
- `mapanare/self/main.mn` -- Compiler driver (755 lines, version string "mapanare 3.47.0")
- `mapanare/self/transpiler.mn` -- Shared transpiler framework (596 lines)
- `mapanare/self/from_python.mn` -- Python-to-Mapanare transpiler (578 lines)
- `mapanare/self/from_php.mn` -- PHP-to-Mapanare transpiler (1,161 lines)
- `mapanare/self/from_typescript.mn` -- TypeScript-to-Mapanare transpiler (1,561 lines)
- `mapanare/self/from_go.mn` -- Go-to-Mapanare transpiler (1,524 lines)
- `mapanare/self/mnc_all.mn` -- Concatenated core modules (14,764 lines)
- `docs/SPEC.md` -- Language specification (28 sections, ~2,200+ lines)
- `docs/manifesto.md` -- Design philosophy
- `docs/getting-started.md` -- 12-section tutorial
- `docs/cookbook.md` -- 14 recipes
- `docs/reference.md` -- Language reference (version updated to 3.47.0)
- `docs/roadmap/v3.46.0/PLAN.md` -- GPU Foundation plan
- `docs/roadmap/v3.47.0/PLAN.md` -- GPU Examples + v4.0.0 Gate plan
- `docs/roadmap/v4.0.0/PLAN.md` -- Production release criteria
- `runtime/native/mapanare_core.c` -- C runtime core (2,685 lines, `str_concat` early returns fixed)
- `runtime/native/mapanare_io.c` -- C runtime I/O (1,672 lines, BCrypt cached, rand() removed)
- `runtime/native/mapanare_runtime.c` -- Agent scheduler (1,343 lines)
- `runtime/native/mapanare_gpu.c` -- GPU runtime via CUDA dlopen (1,951 lines)
- `examples/gpu/vector_add.mn` -- GPU vector addition example (21 lines)
- `examples/gpu/matmul_bench.mn` -- GPU matrix multiply example (25 lines)
- `examples/gpu/README.md` -- GPU example documentation
- `examples/cli/todo.mn` -- Interactive TODO manager
- `examples/cli/word_count.mn` -- Word/line/char counter
- `examples/network/http_fetch.mn` -- HTTP GET client
- `stdlib/pkg.py` -- Package manager (`tar.extractall` filter fixed)
- `tests/golden/BENCHMARKS.md` -- 40/40 golden, 40/40 stage1 match
- `tests/test_examples.py` -- Example validation (all dirs covered)
- `CHANGELOG.md` -- Release notes
- `VERSION` -- 3.47.0

---

## Executive Summary

At v3.45.0, I said v4.0.0 needed one more sentence in the spec. That sentence has been written. Section 23 of the SPEC no longer opens with non-functional code disguised as working code. It now opens with `gpu_available()`, `gpu_tensor_add()`, and a code example that compiles, runs, and produces correct results on an NVIDIA GPU. The section honestly distinguishes between what works today (the `gpu_*` builtins via CUDA dlopen) and what is planned (the `@gpu` decorator syntax). The same honesty that Sections 3.10 and 10.5 demonstrated for tensors and batch now extends to the entire GPU story. Three review cycles of asking for this fix. It is done.

But Section 23 is not the real story of v3.47.0. The real story is that Mapanare now has a working GPU compute path. A Mapanare program can detect a GPU, query its name and memory, allocate vectors, dispatch element-wise operations and matrix multiplications to CUDA, and collect results -- all from 21 lines of `.mn` source that compiles to a native binary. The GPU runtime (`mapanare_gpu.c`, 1,951 lines) loads `libcuda.so` via dlopen with no SDK dependency, embeds PTX kernels for all arithmetic operations, and degrades gracefully to CPU when no GPU is available. The `vector_add.mn` and `matmul_bench.mn` examples in `examples/gpu/` are real programs that run on real hardware. The five v3.45.0 review hard blockers are all resolved. The version string, the reference.md version, the self-hosted compiler rebuild, the `str_concat` early returns, the BCrypt handle caching, the `tar.extractall` filter, the test_examples.py coverage -- all addressed.

The language, as a design, has reached a state I would describe as coherent. It knows what it is. It is a compiled language with first-class agents, signals, streams, and now functional (if nascent) GPU compute, bilingual syntax that feels natural rather than forced, a Rust-inspired error model, and a self-hosted compiler that compiles itself to a fixed point. It is not Mojo -- it does not claim to replace Python for ML training loops. It is not Zig -- it does not claim to replace C for systems programming. It is something more specific: a language for building concurrent, reactive, data-processing programs that might talk to GPUs, might orchestrate AI agents, and definitely need to read files, fetch URLs, and process strings. That specificity is a strength. The design space is well-occupied.

---

## Progress Since Last Review

### FIXED (from v3.45.0 issues)

1. **[was MEDIUM -- P0] SPEC Section 23 (GPU Computing) lacks a status disclaimer.** **FIXED.** The section has been completely rewritten. The opening paragraph now reads: "Mapanare provides GPU-accelerated tensor operations via built-in functions. GPU compute uses the CUDA Driver API loaded at runtime via `dlopen` -- no SDK installation required." The code example uses `gpu_available()`, `gpu_tensor_add()`, and bilingual keywords (`si`, `pon`, `sino`). It compiles. The `@gpu` decorator syntax is clearly separated into Section 23.3 with an explicit status note: "The `@gpu` decorator syntax is specified but not yet connected to codegen." This is exactly what I asked for across three review cycles. It is done correctly.

2. **[was LOW] SPEC Section 1 "ML-ready" goal without caveat.** **FIXED.** Line 21 now reads: "**ML-ready (via GPU builtins).** GPU-accelerated tensor operations via `gpu_tensor_add/mul/matmul` builtins using CUDA. `Tensor<T>[shape]` type with compile-time shape verification is planned." The parenthetical "(via GPU builtins)" scopes the claim accurately. The second sentence adds "is planned" for the tensor type system. Honest.

3. **[was LOW] No `const` keyword in grammar.** **UNCHANGED.** Expected. v4.1 item.

4. **[was LOW] BENCHMARKS.md speed comparison labels misleading.** **UNCHANGED.** The Speed Comparison table still shows "Speedup" of "0.1x" for 38 of 40 tests without explaining the apples-to-oranges comparison. Now at 40 tests with two GPU entries. Cosmetic.

5. **[was LOW] Bounded-for loops with magic constants.** **SLIGHTLY REDUCED.** The core modules (excluding `mnc_all.mn` and transpilers) contain ~207 bounded-for loops with magic constants, down from the ~274 I counted at v3.45.0. The reduction likely reflects measurement precision rather than active migration, but the emit_llvm.mn growth to 3,418 lines (+99 from v3.45.0) suggests the new GPU dispatch code uses the same bounded-for pattern. The transpiler modules add ~22 more. Total across all `.mn` files: ~549 `for ... in 0..` occurrences.

6. **[was LOW] `main.mn:31` version string stale at "3.40.0".** **FIXED.** Now reads `"mapanare 3.47.0"`. The self-hosted compiler was rebuilt.

7. **[was LOW] `reference.md` version at 0.5.0.** **FIXED.** Now reads "**Version:** 3.47.0".

8. **[was LOW] `cookbook.md` version string stale at 3.20.0.** **FIXED.** No longer present in search.

### NEW DEVELOPMENTS (v3.46.0 through v3.47.0)

9. **v3.46.0 -- GPU Foundation.** `mapanare_gpu.c` (1,951 lines) linked into native builds. CUDA Driver API loaded via dlopen -- no SDK dependency. Eight GPU builtins registered in `types.py`, `emit_llvm_text.py`, `semantic.mn`, and `emit_llvm.mn`: `gpu_available`, `gpu_device_name`, `gpu_device_memory`, `gpu_tensor_add`, `gpu_tensor_sub`, `gpu_tensor_mul`, `gpu_tensor_div`, `gpu_tensor_matmul`. Embedded PTX kernels for all operations at float64 precision. CPU fallback when no GPU detected. Golden tests 39 (`gpu_detect`) and 40 (`gpu_tensor`) added. 40/40 golden pass.

10. **v3.47.0 -- GPU Examples + Review Fixes.** Two real GPU examples: `vector_add.mn` (1000-element vector addition) and `matmul_bench.mn` (64x64 matrix multiply). SPEC Section 23 rewritten with working code. All five v3.45.0 hard blockers resolved: SPEC disclaimer, BCrypt handle caching, `rand()` fallback removed, `tar.extractall` filter, `test_examples.py` coverage. Version strings updated. `str_concat` early returns for empty operands. Self-hosted compiler rebuilt at v3.47.0. Compiled LLVM IR regenerated with GPU builtin declarations.

---

## Strengths

### The GPU Story Now Has Substance

The progression from v3.45.0 ("GPU is in the spec but nothing works from user code") to v3.47.0 ("you can dispatch matrix multiplications to a 4090 from 25 lines of Mapanare") is the kind of transformation that changes how a language is perceived. The approach is pragmatic and I admire the engineering philosophy behind it.

Rather than attempting the full `@gpu fn vector_add(a: Tensor<Float>[1024], ...)` pipeline -- which would require connecting decorator recognition, tensor type codegen, and kernel extraction -- the project chose to expose GPU compute through builtins that operate on `List<Float>`. This is the right call. `gpu_tensor_add(a, b)` takes two lists, uploads them to the GPU, runs a PTX kernel, and returns a new list. The C runtime handles device allocation, kernel dispatch, and synchronization. The language sees only function calls on lists.

This means GPU compute is accessible today, with the existing type system, the existing calling convention, and the existing drop glue. No new type kinds needed. No new ABI. No new codegen path. It degrades to CPU transparently. A program that calls `gpu_tensor_add` on a machine with no GPU will silently use CPU element-wise addition -- no code changes, no conditional compilation.

Mojo takes the opposite approach: deep compiler integration with MLIR, static kernel compilation, and compile-time shape analysis. That approach is more powerful but requires years of compiler engineering. Mapanare's approach is more modest but delivers value now. The SPEC correctly positions this as "builtins today, decorator syntax later." Honest and useful.

### All P0 Review Items Are Resolved

After three review cycles, every item I flagged as P0 or P1 has been addressed:

- SPEC Section 23 disclaimer (P0, 3 cycles) -- **rewritten**
- SPEC Section 1 "ML-ready" caveat (P1) -- **reworded**
- Self-hosted compiler version string (P1) -- **updated and rebuilt**
- `reference.md` version (P1) -- **updated**
- `cookbook.md` version string (P1) -- **updated**

The five v3.45.0 panel hard blockers:
- SPEC Section 23 -- **rewritten**
- `random_bytes` Windows fallback -- **returns empty, no `rand()`**
- BCrypt HMODULE leak -- **cached in static**
- `tar.extractall` filter -- **`filter='data'` added**
- `test_examples.py` coverage -- **all dirs covered**

Zero-percent resolution rate at v3.45.0. One hundred percent at v3.47.0. The discipline is appreciated.

### The Self-Hosted Compiler Keeps Pace

The self-hosted compiler (`mnc_all.mn`, 14,764 lines) now has GPU builtin support wired through semantic analysis and code generation. The `semantic.mn` registers all 8 GPU builtins with correct return types. The `emit_llvm.mn` declares the C runtime wrappers and dispatches calls with the correct ABI (list arguments as `ptr`, integer dimensions as `i64`). The compiler was rebuilt, the golden tests pass 40/40 on both bootstrap and stage1 with YES match across the board. The version string reads "mapanare 3.47.0".

This matters because the self-hosted compiler is the language's proof of self-sufficiency. If the self-hosted compiler cannot compile programs that use GPU builtins, the feature is second-class. It can.

### The C Runtime Is Now a Four-File Platform

With `mapanare_gpu.c` joining `mapanare_core.c`, `mapanare_io.c`, and `mapanare_runtime.c`, the native runtime totals 7,651 lines of cross-platform C covering: arena memory management, string interning, list/map/signal/stream operations, file I/O, TCP/TLS networking, SHA-256/HMAC/base64/hex crypto, PCRE2 regex, HTTP/1.1 client, agent scheduling with thread pool and ring buffers, and now CUDA GPU dispatch with embedded PTX kernels. All via dlopen for optional dependencies.

This runtime is what makes the "compiled" claim meaningful. Go is a compiled language because it ships a runtime. Zig is a compiled language because it ships a runtime. Mapanare now ships a runtime that handles the same class of problems, at a fraction of the code but with the same architectural principles: dynamic library loading for optional features, graceful degradation when libraries are absent, arena-based memory without garbage collection.

---

## Issues Found

### Carried Forward

1. **[LOW] No `const` keyword in grammar.** Unchanged. The `stdlib/math.mn` workaround (`pub fn pi() -> Float { da 3.141592653589793 }`) remains. Appropriate for v4.1.

2. **[LOW] Bounded-for loops with magic constants (~549 across all self-hosted `.mn` files).** Unchanged in architecture. The new GPU dispatch code in `emit_llvm.mn` adds more bounded-for loops, continuing the pattern. This is debt, not defect.

3. **[LOW] BENCHMARKS.md speed comparison labels misleading.** Unchanged. Now 40 tests. The "Speedup" column still shows "0.1x" for most tests without explaining the measurement asymmetry. Cosmetic.

### New Issues

4. **[MEDIUM] SPEC Section 2.1 documents `di` as "Bilingual alias for `let`" but the implementation makes `di` a print statement.** At line 121 of `docs/SPEC.md`, the contextual keywords table says: `| di | Bilingual alias for let (Spanish: "di" = "say/declare"). |`. But the grammar (`mapanare.lark:186`) defines `di_stmt: KW_DI expr`, and the parser (`parser.py:592`) maps it to `PrintStmt`. The keyword `di` is not a synonym for `let` -- it is a standalone print statement. The SPEC description is wrong.

    This matters because a reader consulting the SPEC to understand `di` will form the wrong mental model. The bilingual keyword system is a culturally significant feature of the language. It deserves accurate documentation. The confusion may stem from the Spanish etymology: "di" (imperative of "decir") means "say" or "tell", which maps naturally to "print" (tell the computer to say something), but the SPEC describes it as `let` (binding), which is a different concept entirely.

    **Suggested fix:** Update SPEC line 121 to: `| di | Bilingual alias for print (Spanish: "di" = "say/tell"). Syntax: di expr |`. Or, if the intent is for `di` to be a `let` alias (as the SPEC claims), update the grammar and parser to match.

    **Status:** MEDIUM. Spec-implementation divergence on a cultural feature.

5. **[MEDIUM] Bilingual keywords are undocumented in the SPEC, reference, and getting-started guide.** The grammar defines 14 bilingual keyword pairs (`pon`/`let`, `da`/`return`, `yo`/`self`, `si`/`if`, `sino`/`else`, `cada`/`for`, `mien`/`while`, `en`/`in`, `tipo`/`type`, `modo`/`trait`, `usa`/`import`, `nada`/`none`, `sal`/`break`, `sigue`/`continue`), plus `di` as a standalone print statement. These are used extensively in all examples (`todo.mn`, `vector_add.mn`, `matmul_bench.mn`) and in the SPEC's own code examples (Section 23 uses `si`, `pon`, `sino`, `cada`, `en`).

    Yet there is no bilingual keywords table in the SPEC. The reference (`docs/reference.md`) does not mention them. The getting-started guide does not mention them. A new user encountering `pon`, `mien`, `sino`, `cada` in the examples has no documentation to consult. The only references are the grammar file itself and the grammar comments.

    For a feature that is central to the language's cultural identity -- and that appears in the very first SPEC code example a reader will see in Section 23 -- this is a documentation gap that should be closed before v4.0.0.

    **Suggested fix:** Add a "Bilingual Keywords" subsection to SPEC Section 2.1 with a table mapping each Spanish keyword to its English equivalent. Add a note in the getting-started guide, perhaps in Section 1 (Hello World), explaining the bilingual system.

    **Status:** MEDIUM. Cultural signature feature without documentation.

6. **[LOW] CHANGELOG does not include v3.46.0 and v3.47.0 entries.** The CHANGELOG's most recent entry is `[3.45.0] - 2026-04-08`. The v3.46.0 (GPU Foundation) and v3.47.0 (GPU Examples + v4.0.0 Gate) releases are not documented. The commit messages (`fbd382e` for v3.46.0, `c37b9bc` for v3.47.0) provide the information, but the CHANGELOG is the canonical release record. A user checking the CHANGELOG sees v3.45.0 as the latest release while the VERSION file says 3.47.0.

    **Status:** LOW. Two entries needed.

7. **[LOW] README version badge says 3.45.0, tests badge says 3698.** The README at line 28 has `version-3.45.0-blue` and line 29 has `tests-3698_passing`. The VERSION file says 3.47.0 and the test count is 4,845+. Both badges are stale by two versions.

    **Status:** LOW. Badge update.

8. **[NOTE] v3.47.0 PLAN.md has unchecked checkboxes.** Same pattern as v3.45.0 -- the plan status says "DONE" but all checkboxes are `- [ ]` rather than `- [x]`. Cosmetic but creates ambiguity about completion status.

    **Status:** NOTE. Cosmetic.

---

## Recommendations

### P0 -- Must fix before v4.0.0

1. **Add a bilingual keywords table to SPEC Section 2.1.** The bilingual keyword system is the single most culturally distinctive feature of the language. It appears in the SPEC's own code examples. It deserves a proper subsection with a full mapping table. This is not optional for a production release that uses Spanish keywords in its showcase examples. Estimated effort: 30 minutes.

2. **Fix SPEC line 121: `di` is a print statement, not a `let` alias.** Spec-implementation divergence. One line. Thirty seconds.

### P1 -- Should fix for quality

3. **Add v3.46.0 and v3.47.0 entries to CHANGELOG.** The CHANGELOG is the canonical release record. Two entries covering GPU builtins, review fixes, and examples.

4. **Update README badges** to version 3.47.0 (or 4.0.0 at tag time) and current test count.

5. **Add a brief bilingual keyword note to `docs/getting-started.md`** Section 1 or a new Section 0. Something like: "Mapanare supports bilingual keywords -- Spanish and English alternatives compile identically. You will see `pon` (let), `si` (if), `da` (return) throughout the documentation and examples."

### P2 -- Longer term

6. **Continue migrating core modules from bounded-for to while.** v4.1 priority. The GPU builtin additions in `emit_llvm.mn` added more bounded-for loops -- the pattern perpetuates itself.

7. **Add `const` to grammar and spec.** v4.1.

8. **Write a Tensor compilation demo.** Now that GPU builtins work, a proof-of-concept connecting the tensor type system (`Tensor<Float>[shape]` in grammar) to `gpu_tensor_*` builtins would close the last gap between the language's aspirations and its capabilities.

9. **Clarify BENCHMARKS.md speed comparison labels.** Cosmetic but persistent.

---

## v4.0.0 Readiness Assessment

**Verdict: CONDITIONAL PASS -- ready for v4.0.0 with 2 documentation fixes.**

This is the closest I have come to an unconditional pass. The two conditions are:

1. **Add bilingual keywords documentation to the SPEC.** A production release that uses Spanish keywords in its showcase examples, its GPU documentation, its CLI tools, and its self-hosted compiler cannot ship without a table explaining what those keywords mean. A reader encountering `pon a: List<Float> = [1.0, 2.0, 3.0, 4.0]` in the SPEC's Section 23 example deserves to know that `pon` means `let`. This is a 30-minute fix.

2. **Fix the `di` keyword documentation.** The SPEC says `di` is a `let` alias. The implementation says it is a `print` statement. One of them is wrong. This is a 30-second fix.

Everything else is ready, and in most respects it exceeds the bar I would set:

**What is ready:**

- The language is externally usable. Real programs compile and run as native binaries.
- GPU compute works from user code on real hardware (NVIDIA via CUDA dlopen).
- 40/40 golden tests pass on both bootstrap and stage1, with full IR match.
- 4,845+ tests across the full pipeline.
- Self-hosted compiler: 14,764 lines core, rebuilt at v3.47.0 with GPU support.
- Four self-hosted language transpilers with shared framework.
- C runtime: 7,651 lines across four files providing OS abstraction, I/O, crypto, regex, networking, agent scheduling, and GPU dispatch.
- Package manager functional.
- Documentation suite: 12-section tutorial, 14-recipe cookbook, 3 migration guides, formal SPEC.
- Three first-class primitives (agents, signals, streams) fully operational.
- GPU compute via builtins operational, with honest SPEC documentation.
- Fixed-point self-compilation verified.
- Grammar, type system, semantic checker stable and internally consistent.
- All five v3.45.0 review hard blockers resolved.
- Error handling via `Result<T, E>` and `?` operator.
- Bilingual keywords functional everywhere (but undocumented).

**What I am releasing:**

- The ~549 bounded-for loops. Debt, not defect.
- No `const` keyword. Workaround exists. v4.1.
- Tensor type system not connected to GPU builtins. Honest in SPEC.
- BENCHMARKS.md speed comparison labels. Cosmetic.
- CHANGELOG missing v3.46.0/v3.47.0 entries. Should fix.
- README badges stale by two versions. Should fix.
- v3.47.0 PLAN.md unchecked checkboxes. Cosmetic.

**What I am watching for v4.1:**

- `const` keyword in grammar and spec.
- Core module migration from bounded-for to while.
- Tensor type system connected to GPU builtins.
- `batch` keyword in grammar (completing the signal model).
- `@gpu` decorator pipeline (connecting decorator recognition to PTX codegen).
- Bilingual keyword documentation expansion (beyond the SPEC table I am requesting).
- Stabilization of the transpiler pipeline for production use.

---

## Raw Notes

### On the Shape of the GPU Story

There is a philosophical question embedded in the GPU approach that I think is worth examining. The `gpu_tensor_*` builtins operate on `List<Float>`. Not `Tensor<Float>[shape]`. Not a new GPU-specific type. Plain lists.

This is simultaneously the most pragmatic and the most limiting design choice in the v3.46.0-v3.47.0 arc. Pragmatic because it requires no new type kinds, no new ABI, no new codegen path. The language already knows how to create lists, pass them to C functions, and receive lists back. Adding GPU compute was, from the type system's perspective, a matter of registering eight new builtin functions with existing types. The `emit_llvm_text.py` dispatch for `gpu_tensor_add` is 15 lines. The `semantic.mn` registration is 16 lines. The self-hosted emitter dispatch is 20 lines. This is the kind of economy that comes from making the right architectural bet early.

Limiting because `List<Float>` carries no shape information. `gpu_tensor_matmul(a, b, m, n, k)` takes five arguments instead of two because the caller must provide the matrix dimensions explicitly. The type system cannot verify that `len(a) == m * k` or that `len(b) == k * n`. Shape errors are runtime errors.

Compare this with the SPEC's tensor vision (Section 3.10): `Tensor<Float>[2, 3]` carries its shape in the type. `a @ b` verifies dimensional compatibility at compile time. That vision remains unimplemented. The gap between `gpu_tensor_matmul(a, b, 64, 64, 64)` and `a @ b` where `a: Tensor<Float>[64, 64]` is the distance between "GPU works" and "GPU is first-class."

I do not flag this as an issue because the SPEC is honest about it (Section 3.10 says "not yet implemented," Section 23.3 says "not yet connected to codegen"). But I note it because it defines the most important v4.1 design question: how do you connect the tensor type system to the GPU builtins? The answer will shape the language's identity in the ML space more than anything else.

### On `di` and the Grammar of Speech

The `di` keyword is a small thing, but it reveals something about the language's relationship with its bilingual identity. In Spanish, "di" is the imperative of "decir" -- "say" or "tell." As a print statement, `di "hello"` literally means "say hello." This is poetic and natural. It is the right mapping.

But the SPEC says `di` is a `let` alias. This is wrong, and the wrongness is interesting because it suggests the documentation was written from an assumed design rather than the implemented design. Someone thought `di` should be the Spanish for `let` (perhaps from "decir" in the declarative sense -- "I declare"), and that assumption was documented without checking the grammar.

This matters beyond the specific bug because the bilingual keyword system is not a gimmick. It is a cultural statement about who programming languages are for. The `todo.mn` example uses `pon`, `mien`, `si`, `sino`, `da` -- and it reads like natural Spanglish. The GPU examples use `cada i en 0..1000`. The self-hosted compiler is 14,764 lines of bilingual Mapanare. This is not a feature that can be casually misrepresented in the spec.

### On the Resolution of Three Cycles of Feedback

I want to acknowledge what happened between v3.45.0 and v3.47.0 with respect to the review process. At v3.45.0, the panel identified 28 action items, 5 hard blockers, and a 0% resolution rate on carry-forward items from v3.40.0. The aggregate score dipped for the first time in six cycles. The criticism was specific and constructive.

The response was equally specific. In two versions:

- All 5 hard blockers resolved (SPEC S23, BCrypt, rand(), tar filter, test coverage).
- My three-cycle P0 (SPEC S23) addressed with a complete section rewrite, not a band-aid disclaimer.
- My P1 items (version strings, reference.md, cookbook.md) all updated.
- SPEC Section 1 "ML-ready" reworded with honest caveat.
- `str_concat` early returns implemented (Mamba, 2nd cycle).
- BCrypt handle cached in static (Viper/Mamba).
- `random_bytes` returns empty instead of insecure `rand()` (Viper).

This is the kind of responsive engagement that makes a review process meaningful. The feedback was heard, prioritized, and executed. The items that were deferred (bounded-for loops, `const` keyword, BENCHMARKS labels) were the right items to defer -- they are debt, not defect.

### Comparison Update (v3.47.0)

| Dimension | v3.45.0 | v3.47.0 | Change |
|-----------|---------|---------|--------|
| Golden tests | 38/38 | 40/40 | +2 (GPU) |
| GPU compute | Specified, not functional | Functional via CUDA dlopen | Qualitative leap |
| C runtime lines | 5,700 | 7,651 | +1,951 (GPU) |
| GPU builtins | 0 | 8 | gpu_available + 3 info + 4 tensor ops |
| SPEC S23 accuracy | Misleading | Honest | 3-cycle P0 resolved |
| Review hard blockers | 5 open | 0 open | 100% resolution |
| Self-hosted compiler version | "3.40.0" (stale) | "3.47.0" (current) | Fixed |
| Real GPU examples | 0 | 2 | vector_add + matmul_bench |

### On What Mapanare Is

I have reviewed this language across multiple versions now, and I think I can finally articulate what it is, rather than what it is trying to be.

Mapanare is a language for building concurrent, reactive, data-processing programs with native compilation, designed by someone who grew up coding in Spanish and wants other people like them to feel at home in a programming language. It has agents because concurrent actors are the right abstraction for orchestration workloads. It has signals because reactive data binding is the right abstraction for state management. It has streams because composable data pipelines are the right abstraction for processing. It has GPU builtins because modern compute sometimes needs a GPU. It has bilingual keywords because programming is for humans and not all humans think in English.

The "AI-native" label is a positioning choice, and I think the honest version of that claim is now supportable. Agents with typed channels, signals with automatic dependency tracking, streams with backpressure, GPU tensor operations with graceful CPU fallback -- these are the building blocks of AI orchestration systems. The language does not replace PyTorch for training. It does not replace JAX for differentiation. It provides the infrastructure around those tools: the concurrent agent that coordinates multiple model calls, the reactive signal that updates when a model response arrives, the stream that processes inference results, the GPU builtin that accelerates a computation.

That is a coherent design. The design works. The documentation should say so -- with a bilingual keywords table, because the documentation should be as honest about the language's cultural identity as it is about its GPU capabilities.

v4.0.0 needs two documentation fixes. Then it is done.
