# Mapanare -- Agent Team Code Review Prompt

> Paste this entire prompt into Claude Code with agent teams enabled.
> Make sure you are in the root of the Mapanare repository before running.
> Update the VERSION variable below before each run.

---

## Version Configuration

**TARGET VERSION:** `v4.114.0`

> **This is the Phase D close-out panel.** Mapanare v4.111.0-v4.113.0
> is Phase D (self-hosted compiler maturity). v4.111.0 rebuilt
> mnc-stage1 from the full self-hosted pipeline and ran all 64 golden
> tests (21/64 → 26/64 after disabling 4 zero-ROI MIR passes).
> v4.112.0 ran 3-stage fixed-point verification, classified
> divergences, and closed docket #7 (byref size heuristic) with a
> single-file fix in `mapanare/self/emit_llvm.mn` (`struct_byte_size`
> + `is_byref_type_st` matching the Python bootstrap's `_tsz` at
> `emit_llvm_text.py:141`). v4.113.0 closed the remaining three
> v4.99.0 docket items: #8 (coroutine frame decoupled via named
> `mn_coro_frame_prefix_t` struct), #10 (SPEC §2.1.1 Reserved
> Keyword Master List — 42 entries, both lexers cross-referenced),
> #11 (7 specific `mapanare: async runtime:` error messages across
> 5 failure sites in the scheduler + `file_read_async`).
>
> v4.114.0 is the Phase D panel: zero new features, full 7-reviewer
> audit. After this panel: **11/11 items from the v4.99.0 docket are
> either CLOSED or ACCEPTED.** If this panel returns aggregate >=8.5
> with zero NEEDS WORK verdicts, Phase D closes and v4.115.0 opens
> Phase E (polish / v5.0.0 prep). If not, v4.114.1 becomes a recovery
> release addressing the findings before Phase E begins.

Set the review output directory based on this version:

```
.reviews/v4.36.0/
  README.md              # Summary index with verdict table and action items
  01-viper.md            # Rust reviewer
  02-boa.md              # Python reviewer
  03-cobra.md            # C++ reviewer
  04-mamba.md            # C reviewer
  05-anaconda.md         # GNU/GCC toolchain reviewer
  06-rattler.md          # LLVM reviewer
  07-coral.md            # Language design reviewer
  culebra_summary.md         # Arc-end Culebra summary
  culebra_baseline_delta.md  # Fixed/New/Remaining across the arc
  arc_journal.jsonl          # Concatenated per-version journals
```

Before starting, each reviewer MUST read:

1. `.reviews/v4.31.0/README.md` — the previous panel (recovery arc close, 9.343/10).
   All carry-forwards and action items from v4.31.0 must be cross-referenced.
2. `.reviews/CARRY_FORWARD.md` — the canonical carry-forward queue.
   Shows which items Arc 1 has closed and where.
3. `.reviews/REVIEW_CADENCE.md` — the cadence policy. Every reviewer
   should flag cadence-breaking scenarios they see in their lens.
4. Every `docs/roadmap/v4/v4.3{2,3,4,5}.0/SESSION_REPORT.md` — the session
   reports are the lead's claims about what each Arc 1 release shipped.
   The panel's job is to verify those claims against the code.
5. `.reviews/v4.36.0/PRE_PANEL_AUDIT.md` — the lead's own fact-check (18/18 claims PASS).

Reviewers should note in their review whether previous-panel issues
were **Fixed**, **Regressed**, **Still open**, or **Deferred with
documented tracking**. The arc-end panel is specifically a
verification panel — the lead has made 48+ claims across five
releases, and the panel grades the fraction of those claims that
actually hold.

---

## Mission

Create an agent team of 7 reviewers to perform a deep, comprehensive code review of the Mapanare programming language codebase. Mapanare is an AI-native compiled programming language where agents, signals, streams, and tensors are first-class primitives. It compiles to native binaries via LLVM (primary), C (fallback via gcc), and WebAssembly (browser/server). A self-hosted compiler exists (15,000+ lines of `.mn` across 11 modules in `mapanare/self/`) and reaches a near-fixed-point. Python, PHP, TypeScript, and Go transpilers allow `mapanare compile {.py,.php,.ts,.go}` — all self-hosted in `.mn` using shared `transpiler.mn` framework.

This is version `v4.31.0` — the arc-ending release in a five-version
**recovery arc** (v4.27.0 → v4.31.0) triggered by the v4.26.0 panel's
verdict. The previous panel grades were 9.79/10 unanimous at v3.47.0
and ~8.2/10 with 4 NEEDS WORK verdicts at v4.26.0 — the largest
single-cycle regression in project history. The recovery arc shipped:

**Arc structure:**

- **v4.27.0 "Honesty Recovery"** — closed 8 CRITICAL items: FFI
  argtypes/restype wiring, FFI DCE respect for `pub`, runtime `-fPIC`,
  `@gpu` removed (Path B), MIRVerifier wired into `compile()`, `const`
  removed (Path B), two parallel diagnostic systems consolidated,
  CHANGELOG v4.18.0–v4.26.0 rewritten in stricken form
- **v4.28.0 "Concurrency + v3.47.0 carry-forwards"** — closed
  HIGH-severity concurrency items: signal value mutation under lock,
  agent inbox MPSC-safe producer lock, type registry reader-writer
  lock, `mn_init_tag_strings` pthread_once (7-cycle carry-forward
  finally closed), matmul shape NULL check + dimension validation
  (27 versions overdue), GLSL temp file race, Windows GPU init race
  propagation, `main.ll` version string regression
- **v4.29.0 "Build infrastructure + test honesty"** — wired
  `mapanare_db.c` (1,130 lines) and `mapanare_html.c` (812 lines) into
  `build_stage1.py` + `Makefile` + `_RUNTIME_FN_ATTRS`; `extern
  "Python" fn` removed (Path B); DWARF claim struck (Path B);
  `--no-check` stderr warning; `verify_fixed_point.sh` `set -euo
  pipefail` + `DIFF_THRESHOLD` ratchet + exit propagation; stale
  `stage3.ll` zero-byte file deleted; `NotImplementedError` CI gate;
  silent-skip CI gate
- **v4.30.0 "Codegen + optimizer + emitter carry-forwards"** — `await`
  removed (Path B); `_emit_agent_wrap` wired to real
  `{AgentName}_handle` dispatch with `malloc`'d reply buffer;
  `MIROptimizerNonConvergence` ICE replaces silent warning; `DCE`
  drains internally to a fixed point in one call (fixed
  `emit_llvm__emit_binop` non-convergence that had been silently
  warning every build since v4.2.0); `stream_fusion` folded into the
  unified fixpoint loop; self-hosted `clean_phis_in_block` invoked;
  `_RUNTIME_FN_ATTRS` audited with +70 `noalias`/`willreturn`
  annotations across 55 runtime symbols; all six 7th-cycle
  carry-forwards verified clean
- **v4.31.0 "Documentation truth + process hardening"** — SPEC code-
  block drift cleaned (132 blocks across 4 docs verified parseable);
  SPEC line 121 `di` mislabel fixed; bilingual keywords table added;
  Spanish README synced; `mapanare/emit_c.py` docstring 27-version
  stale update; User-Agent wired to `MAPANARE_VERSION` macro from
  `VERSION` file (closes 5+ minor stale string); `__mn_list_oob_buf`
  4KB dead workaround deleted; new CI scripts for changelog honesty,
  docs drift, hollow features; `.reviews/CARRY_FORWARD.md` and
  `REVIEW_CADENCE.md` initialized

**The tally at v4.31.0:** 44/44 golden tests, fixed-point at ≤100 diff
lines out of ~111k (0.062%), 4,845+ pytest, `extern "Python"` +
`async`/`await` + `@gpu` + `const` all removed (Path B), DWARF
struck, `_emit_agent_wrap` + all six emitter carry-forwards closed,
five SESSION_REPORT.md files documenting every change, three new CI
gates from v4.29.0 + v4.31.0 specifically designed to catch the next
hollow-feature regression at PR time.

**Reviewers should hold to ARC-END VERIFICATION standards.** The
question is not "is this code healthy?" — it is **"does every claim
in every v4.27.0–v4.31.0 SESSION_REPORT.md hold up against the code
that shipped in this tag?"** The lead has made ~50 claims across five
recovery releases. Your job is to fact-check them.

**Specifically look for:**

- **Re-regression**: any v4.26.0 item marked CLOSED in
  `.reviews/CARRY_FORWARD.md` that is actually still open
- **Partial fixes that were advertised as full**: e.g. if
  `_emit_agent_wrap` was wired but only handles scalar returns, the
  v4.30.0 SESSION_REPORT's "Agents actually dispatch" claim is partial
- **New hollow features introduced during the recovery arc**: v4.30.0
  added a fallback stub path in `_emit_agent_wrap`; is it a real
  fallback or a new hollow surface?
- **Gaps between `SESSION_REPORT.md` prose and the code diff**: if a
  SESSION_REPORT says "X was fixed in file Y:line Z", that file and
  that line must reflect the fix at the v4.31.0 tag
- **Carry-forwards not listed in `.reviews/CARRY_FORWARD.md`**: any
  open item you find that isn't in the file is a process bug — either
  the item was missed by the arc or the tracking file is incomplete

The recovery arc's whole thesis is: a lead's self-assessment is not
sufficient — an external panel is needed. This panel's output is the
only thing that can end the arc.

---

## Review File Format

Each review file must follow this exact format:

```markdown
# [Reviewer Name] -- [Language/Domain] Review of Mapanare v4.31.0
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
