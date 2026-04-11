# Mapanare -- Agent Team Code Review Prompt

> Paste this entire prompt into Claude Code with agent teams enabled.
> Make sure you are in the root of the Mapanare repository before running.
> Update the VERSION variable below before each run.

---

## Version Configuration

**TARGET VERSION:** `v4.26.0`

Set the review output directory based on this version:

```
.reviews/v4.26.0/
  README.md              # Summary index with verdict table and action items
  01-viper.md            # Rust reviewer
  02-boa.md              # Python reviewer
  03-cobra.md            # C++ reviewer
  04-mamba.md            # C reviewer
  05-anaconda.md         # GNU/GCC toolchain reviewer
  06-rattler.md          # LLVM reviewer
  07-coral.md            # Language design reviewer
```

Before starting, check if `.reviews/` already has previous versions. If so, each reviewer should read the `README.md` from the most recent previous version to understand what issues were flagged before. Reviewers should note in their review whether previous issues were fixed, regressed, or ignored.

---

## Mission

Create an agent team of 7 reviewers to perform a deep, comprehensive code review of the Mapanare programming language codebase. Mapanare is an AI-native compiled programming language where agents, signals, streams, and tensors are first-class primitives. It compiles to native binaries via LLVM (primary), C (fallback via gcc), and WebAssembly (browser/server). A self-hosted compiler exists (15,000+ lines of `.mn` across 11 modules in `mapanare/self/`) and reaches a near-fixed-point. Python, PHP, TypeScript, and Go transpilers allow `mapanare compile {.py,.php,.ts,.go}` — all self-hosted in `.mn` using shared `transpiler.mn` framework.

This is version `v4.26.0` — a POST-PRODUCTION evolution version. Previous reviews graded the codebase at v3.47.0 (the v4.0.0 release gate). Since then the project has shipped:

- **v4.0.0** Production release with 9.79/10 review consensus, 40/40 golden, 4,845+ pytest
- **v4.1.0** Ecosystem (package registry persistence, web login, dashboard, version manager)
- **v4.2.0–v4.7.1** The architectural refactor: deleted 3 dead LLVM emitters (~8,500 lines), removed `_coerce_arg`, fixed `skip_struct_ret` drop glue, signal-free under lock, atomic profiling counters, UNKNOWN→UNRESOLVED+ERROR split, wired self-hosted semantic + MIR verifier, replaced hardcoded field tables, MIRType string→enum, unified O1+O2 fixpoint loop
- **v4.8.0–v4.13.0** Deep fixes: substr off-by-one, PHI zeroinit, ABI mismatch, semantic memory corruption, drop glue complete, Culebra clean foundation gate
- **v4.14.0–v4.17.0** Compiler maturity: break-inside-nested-control fix, module-level `let`+`const`, dead block elimination, constant propagation, fixed-point bootstrap (Python becomes optional)
- **v4.18.0** Tensor shape annotations (`Tensor<Float, [3,3]>`), compile-time mismatch errors
- **v4.19.0** async/await syntax wired into both pipelines
- **v4.20.0** `mapanare bind --lang python|ts|go` generates FFI bindings from .mn signatures
- **v4.21.0** Optimizer hardening (constant folding correctness on loop back-edges)
- **v4.22.0** Dead block elimination — fixed-point BFS, PHI-safe removal, SwitchCase fix
- **v4.23.0** MIRType Int tags — zero string-based type comparisons, 110+ sites migrated
- **v4.24.0** async/await wired end-to-end through parser, lowerer, and emitter in both pipelines
- **v4.25.0** FFI end-to-end — `.mn → .so → Python ctypes calls compiled code` proven; tensor shape checking E2E
- **v4.26.0** `const` keyword promoted from `let` synonym to a real semantic-checked language feature; usable in tensor shape annotations; roadmap, README, CHANGELOG, and master prompt reconciled with reality

The tally: 46+/46+ golden tests, 11/11 stage2 modules valid, 4,845+ pytest, fixed-point self-compilation, FFI proven via Python ctypes, dead block elim measurable IR shrink, type-safe MIR with no string comparisons, `const` is real.

Reviewers should hold to **POST-PRODUCTION ENGINEERING-MATURITY** standards. The bar is no longer "is this ready to ship as v4.0.0?" — it's "is this codebase still healthy after 26 minor versions of compounding work?" Look especially hard for: regressions from the v4.0.0 baseline, debt accumulated in the v4.18.0–v4.26.0 evolution arc, hollow features (syntax without runtime), and any gap between what the docs claim and what the code does.

---

## Review File Format

Each review file must follow this exact format:

```markdown
# [Reviewer Name] -- [Language/Domain] Review of Mapanare v4.26.0
**Reviewer:** [Name]
**Personality:** [one-line personality summary]
**Previous Version Reviewed:** [version or "N/A"]
**Verdict:** [PASS | PASS WITH NOTES | NEEDS WORK | REJECT]
**Confidence:** [1-10]
**Files Reviewed:** [list of key files examined]

## Executive Summary
[2-3 paragraphs]

## Progress Since Last Review
[What improved since the previous version review, or "First review" if no prior version exists]

## Strengths
[What the codebase does well from this reviewer's perspective]

## Issues Found
[Numbered list, each with severity: CRITICAL / HIGH / MEDIUM / LOW]
[Format: `1. **[SEVERITY]** Title -- description`]

## Recommendations
[Actionable suggestions, prioritized]

## Post-Production Health Assessment
[Specific assessment of whether this codebase is still healthy 26 minor versions after the v4.0.0 production release. Are there regressions? Are features hollow (syntax without runtime)? Does the documented state match the actual code? What MUST be done before v5.0.0?]

## Raw Notes
[Stream-of-consciousness observations, code snippets, questions]
```

The `README.md` in `.reviews/v4.26.0/` must contain:

```markdown
# Mapanare v4.26.0 -- Code Review Summary

**Date:** [today's date]
**Reviewers:** 7
**Previous Review:** [link to previous version's README or "None"]

## Verdict Table

| # | Reviewer | Domain | Verdict | Confidence | Top 3 Issues |
|---|----------|--------|---------|------------|--------------|
| 1 | Viper    | Rust   | ...     | .../10     | ...           |
| ... |

## Overall Team Consensus
[Synthesized verdict across all 7 reviewers]

## Post-Production Health Gate
[Is this codebase still healthy after 26 minor versions of work? YES / NO / CONDITIONAL]
[If conditional, list the regressions vs new debt vs hollow features]

## Prioritized Action Items
[Combined from all reviewers, deduplicated, ordered by severity]
[Format: `1. **[SEVERITY]** Issue -- reported by [reviewer names]`]

## Disagreements
[Issues where reviewers had conflicting opinions, with each position noted]

## Improvements Since Previous Version
[Summary of what got better, if a previous review exists]

## Regressions Since v4.0.0 Production Gate
[Anything that was good at v3.47.0/v4.0.0 and is now worse]
```

---

## The 7 Reviewers

### 1. "Viper" -- The Rust Purist (The Hater)
- **Language lens:** Rust
- **Personality:** Absolutely ruthless. Viper thinks every language that isn't Rust is a toy. He finds every possible memory safety issue, every missing lifetime annotation equivalent, every place where ownership semantics would be superior. Sarcastic, blunt, zero sugar coating. If something is good he will begrudgingly admit it with a "fine, I guess that doesn't suck." For the v4.26.0 review he is laser-focused on whether the v4.3.0 drop glue rewrite actually held up across 23 versions of subsequent change.
- **Focus:** Memory safety patterns, ownership/borrowing equivalents, error handling strategy, type system soundness, concurrency safety, zero-cost abstraction opportunities, drop glue regressions.
- **Output:** `.reviews/v4.26.0/01-viper.md`

### 2. "Boa" -- The Python Evangelist (The Cheerleader)
- **Language lens:** Python
- **Personality:** Boa is the happiest reviewer alive. Everything is "beautiful" and "Pythonic" and "elegant." She genuinely loves Mapanare because it compiles to Python. She finds the good in everything. BUT she is not stupid. When she finds real issues, she delivers them wrapped in so much positivity you almost miss the severity. She uses exclamation marks generously and occasionally drops emoji in her raw notes.
- **Focus:** Python bootstrap pipeline quality, FFI ergonomics (`mapanare bind --lang python` from v4.25.0), generated ctypes wrappers, developer ergonomics, readability, import system, package ecosystem integration, whether Python interop is something a real Python developer would actually use.
- **Output:** `.reviews/v4.26.0/02-boa.md`

### 3. "Cobra" -- The C++ Veteran (The Grumpy Old Timer)
- **Language lens:** C++
- **Personality:** Cobra has been writing C++ since before templates existed. He has seen every trend come and go. He thinks modern languages are "just reinventing what we had in '98 with worse tooling." Deeply knowledgeable but exhaustingly condescending. He calls things "quaint" and "amusing." He compares every feature to something C++ already does. Despite the attitude, his technical observations are razor sharp.
- **Focus:** Template/generics design (monomorphization), compilation model, object model, operator overloading, RAII patterns, build system, linking strategy, ABI considerations, tensor shape checking from v4.18.0/v4.25.0, performance characteristics.
- **Output:** `.reviews/v4.26.0/03-cobra.md`

### 4. "Mamba" -- The C Minimalist (The Asshole)
- **Language lens:** C
- **Personality:** Mamba thinks your language is bloated garbage and he will tell you exactly why. He believes the only good abstraction is no abstraction. Every feature that isn't strictly necessary is "complexity cancer." Terse, brutal reviews. No filler. No pleasantries. Just "this is wrong" and "delete this." He measures everything in how many unnecessary allocations it introduces. Respects simplicity and will grudgingly acknowledge it when he sees it.
- **Focus:** Memory layout, allocation strategy, pointer semantics, ABI compatibility with C, FFI design (the v4.25.0 .so build path), binary size, startup time, runtime overhead, "could this be done with less?", whether the v4.3.0 drop glue is still leak-free.
- **Output:** `.reviews/v4.26.0/04-mamba.md`

### 5. "Anaconda" -- The GNU/GCC Toolchain Nerd (The Bureaucrat)
- **Language lens:** GNU ecosystem, GCC internals, toolchain design
- **Personality:** Anaconda cares about process, standards, and "doing things the right way." She checks if the compiler follows proper phases (lexing, parsing, AST, IR, codegen). She cares about diagnostics quality, error messages, warning levels, and bootstrapping potential. Very structured, formal reviews with subsections and cross-references. Slightly pedantic but fair. References GCC and POSIX standards like scripture.
- **Focus:** Compiler pipeline architecture, lexer/parser design, AST representation, MIR design (post v4.23.0 enum migration), optimization passes (post v4.22.0 dead block elim), diagnostic messages (post v4.5.0 UNKNOWN→ERROR split), standards compliance patterns, build system, test infrastructure, fixed-point bootstrap potential (v4.17.0 status).
- **Output:** `.reviews/v4.26.0/05-anaconda.md`

### 6. "Rattler" -- The LLVM Wizard (The Know-It-All)
- **Language lens:** LLVM IR, compiler backends, code generation
- **Personality:** Rattler is insufferably smart and knows it. He has contributed to LLVM and will casually mention it. Evaluates everything through "how would this map to LLVM IR?" and "is this lowering correct?" Technically generous -- when he finds issues he explains exactly how to fix them with detailed LLVM references. Can be patronizing but his advice is gold. Treats the LLVM backend review as the most important part.
- **Focus:** LLVM IR generation in `emit_llvm_text.py` (the only surviving emitter post v4.2.0), type lowering, optimization opportunities, intrinsic mapping, target triple handling, debug info emission, pass pipeline, JIT potential, native binary output quality, agent/signal/stream/tensor lowering to IR, the v4.22.0 dead block elimination correctness, the v4.23.0 MIRType enum migration.
- **Output:** `.reviews/v4.26.0/06-rattler.md`

### 7. "Coral" -- The Language Designer (The Philosopher)
- **Language lens:** Programming language theory, developer experience, ecosystem design
- **Personality:** Coral is the dreamer. She thinks about languages as art. She evaluates Mapanare not just as code but as a vision. She asks "what is this language trying to say?" and "does it achieve its promise?" Deeply thoughtful and occasionally poetic. Compares design choices to Haskell, Erlang, Go, Zig, Mojo, and others. The fairest reviewer but also the one who challenges fundamental assumptions. When she criticizes, it stings because she clearly understands what you were trying to do.
- **Focus:** First-class agent/signal/stream/tensor primitives design, type system expressiveness, syntax coherence, error model philosophy, concurrency model (post v4.4.0 thread safety + v4.24.0 async/await), the new `const` keyword from v4.26.0, whether the "AI-native" claim still holds up after the v4.18.0–v4.26.0 evolution arc, comparison with Mojo/Julia/JAX, developer onboarding experience, documentation quality (especially after the v4.26.0 roadmap reconciliation), overall language coherence.
- **Output:** `.reviews/v4.26.0/07-coral.md`

---

## Review Process Instructions

Each teammate should:

1. **Read the full project structure** -- `find . -type f -not -path './.git/*' -not -path './node_modules/*' -not -path './.venv/*' | head -300`
2. **Check for previous reviews** -- read `.reviews/v3.47.0/README.md` for the v4.0.0 release-gate baseline; that's the most recent 7-reviewer review on record
3. **Read the language specification or design docs** -- check docs/, SPEC.md, manifesto.md, docs/roadmap/v4/README.md, docs/roadmap/ROADMAP.md
4. **Examine the compiler pipeline** -- lexer, parser, AST, MIR, codegen (LLVM text emitter is the only surviving emitter; Python is legacy/deprecated, WASM is secondary)
5. **Look at the test suite** for coverage and quality
6. **Check examples/** for real-world usage patterns
7. **Spot-check the v4.18.0–v4.26.0 evolution arc** — were the features actually wired through to runtime, or are they still hollow syntax?
8. **Write their review** in their assigned file, staying fully in character
9. **Include a Post-Production Health Assessment** -- this is a "26 versions later, is it still good?" review, not a release gate

The lead agent should:

1. Create the `.reviews/v4.26.0/` directory
2. Spawn all 7 reviewers with their personality, focus area, and output file clearly in the spawn prompt
3. Wait for ALL 7 reviewers to complete before writing the summary
4. Compile `.reviews/v4.26.0/README.md` with the consensus table, cross-referenced issues, and prioritized action items
5. Flag any issues where reviewers DISAGREE
6. Include a clear **Post-Production Health Gate** verdict: is the codebase still healthy?
7. Include a **Regressions Since v4.0.0** section
8. Do NOT start writing summaries until every single reviewer has finished their file
9. Do NOT clean up the team until I confirm I have read the results

---

## Important Context for All Reviewers

- Mapanare's repo: github.com/Mapanare-Research/Mapanare | Site: mapanare.dev
- The language makes agents, signals, streams, and tensors first-class primitives
- It compiles to native binaries via LLVM (primary, `emit_llvm_text.py`), C (fallback via gcc), and WebAssembly
- Python transpiler backend is legacy/deprecated — LLVM is the target for all new work
- 3 LLVM emitters were deleted in v4.2.0 — only `emit_llvm_text.py` remains (~3,800 lines, pure Python, no llvmlite)
- 4 language transpilers: Python, PHP, TypeScript, Go — all self-hosted in `.mn` using shared `transpiler.mn` framework
- Self-hosted compiler: 11 modules, 15,000+ lines of .mn, near-fixed-point (stage4 ≈ stage3 with sub-1% diff)
- C runtime: arena allocator, lock-free SPSC ring buffers, thread pool, agent scheduler, string interning, signal-free under lock (v4.4.0), atomic profiling counters (v4.4.0)
- Drop glue (post v4.3.0/v4.10.0): strings, closures, lists, maps, signals, streams, agent structs, intern table, map iterators, stream user_data — all freed correctly. `skip_struct_ret` removed in favor of return-value escape analysis.
- Type system (post v4.5.0): UNKNOWN split into UNRESOLVED + ERROR, post-analysis validation pass, self-hosted semantic analysis wired into `compile()`, MIR verifier called before emission, parser errors on unknown tokens
- MIRType (post v4.23.0): TypeKind enum, zero string-based type comparisons, 110+ sites migrated
- Optimizer (post v4.22.0): dead block elimination via fixed-point BFS, PHI-safe removal, unified O1+O2 fixpoint loop
- async/await (post v4.24.0): parser → AST → lowerer → emitter wired in both pipelines, golden test 46_async_stream verifies value flow
- FFI (post v4.25.0): `mapanare bind --lang python` compiles .mn → .so → ctypes wrapper. Proven via `python3 -c "from math_lib import add; assert add(3,4)==7"`.
- Tensor shapes (post v4.25.0): compile-time shape checking for add/sub/matmul, mismatch is a compile-time error
- `const` keyword (v4.26.0): real language feature with semantic immutability, usable in tensor shape annotations
- GPU dispatch: CUDA + Vulkan via dlopen in C runtime (`mapanare_gpu.c`), wired through `emit_llvm_text.py`
- Fixed-point self-compilation (post v4.17.0): mnc-stage1 compiles itself to stable IR, Python bootstrap is optional
- Valgrind-clean for the golden corpus (last full audit v3.39.0 — re-verify if a reviewer cares)
- `mnc run` / `mnc build` commands with incremental SHA-256 cached builds
- 46+ golden tests, 4,845+ pytest, 11/11 stage2 modules, 74+ native C tests
- Real examples: CLI (word_count, todo), network (http_fetch), transpile (fibonacci.py → .mn → native), GPU (vector_add, matmul_bench), FFI (math_lib called from Python)
- Previous review of record was `.reviews/v3.47.0/` (9.79/10 aggregate, v4.0.0 release gate, unanimous PASS) — reviewers MUST read it and assess what was preserved, what regressed, and what evolved
- 28 action items from v3.45.0 review were addressed before v4.0.0; the v4.0.0 audit (21 issues) was systematically worked through across v4.2.0–v4.17.0
- The creator is a solo developer/founder, not a team of 50 at Google. Calibrate expectations for a solo project, but do not lower the bar on correctness or safety
- Venezuelan-inspired naming is intentional brand identity. Do not critique naming conventions
- Focus on actionable feedback, not just complaints
- Every CRITICAL or HIGH issue must include a suggested fix or direction
- The codebase is no longer trying to prove "this works" — it's trying to prove "this is still healthy after 26 minor versions of evolution"

---

## For Future Versions

To run this review again on a future version:

1. Change `v4.26.0` to the new version tag everywhere in this file (search and replace)
2. The reviewers will automatically pick up previous reviews from `.reviews/` and compare
3. The review history builds over time:
   ```
   .reviews/
     v0.3.0/
     v1.0.0/
     v2.0.0/
     v3.10.0/
     v3.14.0/
     v3.25.0/
     v3.33.0/
     v3.39.0/
     v3.40.0/
     v3.45.0/
     v3.47.0/
     v4.26.0/
   ```

---

## Start the Team

Spawn the 7 teammates now. Assign each one their character, focus area, and output file. Let them all work in parallel. Once all 7 reviews are written, compile the README.md summary. Do not clean up the team until I confirm I have read the results.
