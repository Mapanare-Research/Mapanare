# Mapanare Post-Recovery Roadmap — v4.32.0 onwards

> **Status:** draft — written 2026-04-11, the day the v4.31.0 panel returned
> **9.343/10 aggregate, 5 PASS + 2 PASS WITH NOTES, zero NEEDS WORK**.
> The recovery arc (v4.27.0–v4.31.0) is complete. This document is the
> long-horizon plan for what comes after, organized into **thematic arcs
> of five releases each**, where the fifth release in every arc is a
> scheduled panel release per `REVIEW_CADENCE.md`.
>
> This plan is deliberately long. **The major-version bump is a labelling
> decision, not a scope decision.** Every feature, every debt-drain
> item, and every deferred carry-forward lives in the v4.x line until
> the lead chooses to tag v5.0.0 — and that choice changes nothing about
> the work. The plan is written so the work is the work regardless of
> the version number stamped on it.
>
> **Anti-rush rules (from `RECOVERY_MASTER_PROMPT.md`) still apply:**
> each version ships only after its exit criteria are all green; if a
> version misses an exit criterion, a point-release (v4.32.1 etc.)
> opens rather than rolling the deficit forward; every new keyword or
> new `@decorator` gets a delta review at the PR that introduces it;
> every fifth release in an arc is a full 7-reviewer panel.

---

## Shape of the plan

**Nine thematic arcs, five releases each. Eight scheduled full panels.**
Every arc is: **3 feature/work releases → 1 consolidation release → 1 panel release**. Or sometimes: **4 feature/work releases → 1 panel release**. The fifth release of every arc is the 5-minor cadence panel per `REVIEW_CADENCE.md`.

| Arc | Versions | Theme | Panel release | Growth type |
|---|---|---|---|---|
| 1 | v4.32.0 – v4.36.0 | Arc-end closure + error handling + pattern matching | v4.36.0 | bug closure → language core |
| 2 | v4.37.0 – v4.41.0 | LSP maturity | v4.41.0 | developer experience |
| 3 | v4.42.0 – v4.46.0 | Tensor completeness | v4.46.0 | language primitive finish |
| 4 | v4.47.0 – v4.51.0 | Stdlib AI/LLM growth | v4.51.0 | library surface |
| 5 | v4.52.0 – v4.56.0 | Compiler debt drain (A7 / A8 / A9 / const Path A) | v4.56.0 | debt drain |
| 6 | v4.57.0 – v4.61.0 | Deprecation and deletion (Python emitter, llvmlite JIT, dead code) | v4.61.0 | debt drain |
| 7 | v4.62.0 – v4.66.0 | DWARF debug info minimum-viable → complete | v4.66.0 | capability |
| 8 | v4.67.0 – v4.71.0 | Coroutine design + async/await grammar + semantic | v4.71.0 | capability prep |
| 9 | v4.72.0 – v4.76.0 | Coroutine lowering + scheduler + end-to-end async | v4.76.0 | capability finish |

**Total: 45 releases, 9 panels, 9 thematic arcs.** The lead can tag v5.0.0 whenever they want during or after this plan — nothing about the plan changes if they do. The cadence document already says v5.0.0 would require a full panel on the immediately-prior v4.x tag as a release gate, which is satisfied by every arc's fifth release by construction.

---

## Guiding principles (held from the recovery arc)

1. **Features are either complete or absent.** No parser aliases, no
   grammar without semantics, no CHANGELOG entries for tests that do
   not exist. The `check_no_hollow_features.py` CI gate enforces this.

2. **Every new keyword and every new `@decorator` gets a delta
   review** at the PR that introduces it. Non-optional. The reviewer
   is assigned by lens (Rattler for emitter work, Anaconda for build
   /toolchain, Coral for language design, etc.).

3. **Exit criteria are pre-committed and verifiable.** Every PLAN.md
   ships with a checklist of exit items that either pass or fail; a
   release does not tag until every item is green. This is the
   v4.29.0 discipline that turned silent failure into loud failure.

4. **`CARRY_FORWARD.md` is the single source of truth for open
   findings.** The ledger is updated by every `SESSION_REPORT.md`
   append-only. Asymmetric items (Python-emitter closed / self-
   hosted-emitter open) are tracked with split columns.

5. **Delta reviews cannot be skipped** just because the lead thinks
   the feature is small. The v4.18.0–v4.26.0 regression started
   with "we don't need a review for this one" — the delta review
   cadence was written to make that sentence unsayable.

6. **Panel releases are deliberately quiet.** The 5th release of
   each arc ships with minimal new work so the panel has a stable
   target. The panel release's scope is carry-forward drain,
   measurement, documentation polish, and any HIGH/MEDIUM the
   previous four releases surfaced. Explicitly not a feature
   release.

7. **Break big work into small releases.** The recovery arc's
   biggest lesson was "never ship a feature you cannot verify end-
   to-end in the release that introduces it." Match lowering is
   split into 2 releases (rewrite + guards). LSP is split into 4
   releases. Tensors into 4 releases. Coroutines into 10 releases
   across 2 arcs. Each release delivers one coherent slice that
   can be fully tested at PR time.

8. **LOW debt is drained continuously.** Every growth release
   takes 2–3 LOW items from the ledger as "quality crumbs" along
   with its primary feature. The panel release sweeps anything
   still open. The recovery arc's LOW tail never gets ignored; it
   just gets distributed.

9. **The SESSION_REPORT.md per version is the lead's ledger.**
   Every claim in every session report is pre-verified against
   file:line or against a test name. The v4.31.0 panel fact-checked
   ~50 claims across five releases; future panels will do the same,
   and the session reports are written to make that fact-checking
   cheap.

10. **Panel releases can extend the arc.** If the scheduled panel
    returns NEEDS WORK, the next arc compresses — its first release
    becomes a recovery-style closeout of the panel docket, and
    arc's theme slides to later. The recovery arc template
    (`RECOVERY_MASTER_PROMPT.md`) is the playbook.

---

# Arc 1 — Error handling + pattern matching (v4.32.0 → v4.36.0)

> **Theme:** Closing the arc-end panel and building out the language's
> expression-level error handling + pattern matching. Three releases of
> growth with one post-feature panel.

## v4.32.0 — Arc-end panel closure

**Zero new features.** Close the 9 HIGH + MEDIUM items from the v4.31.0 arc-end panel: `__mn_list_get` OOB abort, self-hosted emitter 7-cycle parity, binary artifact cleanup, `_emit_drop_glue` extraction, `mapanare_internal.h` wiring, `bind.py` struct-field unwrapping, signal recompute under lock, CI job splitting, carry-forward ledger schema update. Full details in [`v4.32.0/PLAN.md`](./v4.32.0/PLAN.md).

## v4.33.0 — The `?` operator

**New syntax — delta review.** First new language feature in 7 releases. Shorthand for `Result<T, E>` and `Option<T>` early-return. Grammar adds `postfix_try`, AST adds `TryExpr`, semantic checks the enclosing function returns a compatible type, lowering desugars to match + early return. Self-hosted mirror mandatory. Full details in [`v4.33.0/PLAN.md`](./v4.33.0/PLAN.md).

**Also sweeps:** 3 LOW items from the v4.31.0 docket — `mn_signal_propagate` recursion depth limit, `mnc-stage1` stripped build, Viper M5 agent-destroy message leak.

## v4.34.0 — Pattern matching rewrite (decision-tree lowering + exhaustiveness)

**Zero new syntax — pure correctness work.** Close `CARRY_FORWARD.md` A6 (the 69-line stage2/stage3 diff). Rewrite `_lower_match` in both Python and self-hosted pipelines to use Luc Maranget's 2008 decision-tree compilation algorithm. Produces minimal branches; no unreachable match arms materialized. Add exhaustiveness checking at **compile error level** in the semantic pass — today's match has incomplete checks and no rustc-quality "missing pattern" messages. Full details in [`v4.34.0/PLAN.md`](./v4.34.0/PLAN.md).

**Also sweeps:** 3 LOW items — `MN_PROFILE_FREE` never called, `__mn_read_line` stack truncation, arena allocator thread safety.

## v4.35.0 — Match guards + or-patterns

**New syntax — delta review.** Builds on v4.34.0's decision-tree infrastructure. Adds two syntactic forms: `case Some(x) if x > 0 => ...` (guards — existing pattern with a boolean condition) and `case A | B | C => ...` (or-patterns — alternatives with the same RHS). Maranget's algorithm handles or-patterns natively; guards become post-match branch checks. Full details in [`v4.35.0/PLAN.md`](./v4.35.0/PLAN.md).

**Also sweeps:** 3 LOW items — `ssl_load_library` CAS, `s_bcrypt` thread safety, `s_net_initialized` atomic.

## v4.36.0 — Panel release (arc 1 close)

**FULL 7-REVIEWER PANEL RUNS.** First 5-minor cadence panel since v4.31.0. Deliberately quiet scope:
- Sweep remaining LOW items from the v4.31.0 docket: `cuda_matmul` upload rc (v3.47.0 #3), self-hosted bounded-for sentinels (9th cycle)
- Carry-forward ledger drain — items closed opportunistically in v4.32.0–v4.35.0 get formal closure rows
- Documentation polish (cookbook chapters for `?` operator, match guards, or-patterns)
- Measurement: fresh `culebra summary`, `culebra baseline save`, full benchmark run
- Pre-panel audit: SESSION_REPORT claims fact-checked against file:line by the lead
- **Panel runs against v4.36.0 tag. Arc extends into v4.37.0+ if verdict is NEEDS WORK.**

---

# Arc 2 — LSP maturity (v4.37.0 → v4.41.0)

> **Theme:** Turn the basic LSP into something a developer actually
> wants to use. No compiler-core changes. Four releases of focused
> editor-tooling work, one panel release.

## v4.37.0 — LSP foundation (workspace index + go-to-definition + hover)

**No new syntax.** Build the workspace-wide symbol index that the rest of the arc depends on. Index built once at workspace load, refreshed on save. Implements go-to-definition across modules (not just within a file — the v4.26.0 Boa review called out same-file-only as the current limit) and hover types using the existing `semantic.py` type inference.

**Scope:**
- `mapanare/lsp/workspace.py` — new module. Workspace indexer that walks the project tree, parses every `.mn` file, and builds `Dict[str, List[SymbolDef]]`.
- Save-on-change incremental updates (re-parse only the changed file, update its symbols in the index).
- LSP `textDocument/definition` handler returns the `Location` for the symbol under the cursor by querying the index.
- LSP `textDocument/hover` handler runs inference on the enclosing function and returns the type of the symbol under the cursor, formatted through `diagnostics.py`.
- `tests/lsp/test_workspace_index.py` — unit tests for index build, update, lookup.
- `tests/lsp/test_goto_definition.py` — integration tests using a small `tests/lsp/fixtures/` project.
- `tests/lsp/test_hover_types.py` — integration tests for inferred types on every binding.

**Also sweeps:** Carry-forward LOW items from v4.36.0 panel if the panel surfaces any.

## v4.38.0 — LSP navigation (find-references + rename refactoring)

**No new syntax.** Extends the workspace index to support reverse lookup (which call sites reference symbol X) and text-based rename with semantic validation.

**Scope:**
- `workspace.py` — track reverse references as part of the index build.
- LSP `textDocument/references` handler returns every call site + read site of the symbol under the cursor.
- LSP `textDocument/rename` handler. Cross-file text rewrite. Rejects renames to names already in scope (with a rustc-quality diagnostic). Handles qualified vs unqualified uses correctly.
- `tests/lsp/test_find_references.py`.
- `tests/lsp/test_rename_refactoring.py` — cases: rename a top-level function, rename a struct field, rename a module-level let, reject rename to shadowed name, reject rename across a trait implementation boundary.

**Also sweeps:** 2–3 LOW items from the running carry-forward queue.

## v4.39.0 — LSP completion (imports + types + field access)

**No new syntax.** Context-aware completion based on what's in scope.

**Scope:**
- LSP `textDocument/completion` handler. Three contexts:
  - After `import ` — offer `stdlib::`, local modules, installed packages
  - In type position — offer builtin types + user struct/enum types
  - After `.` on a value — offer the fields of the value's inferred type
- Completion uses the workspace index built in v4.37.0; no new infrastructure.
- `tests/lsp/test_completion.py` with one test per context.

**Also sweeps:** 2–3 LOW items.

## v4.40.0 — LSP diagnostic streaming + VS Code extension polish

**No new syntax.** Incremental re-check on save; diagnostics pushed to the client without the user running a command. VS Code extension publishes a new marketplace build.

**Scope:**
- LSP `textDocument/publishDiagnostics` — run on save or after a short idle timeout (~300ms debounce).
- Reuse the existing `SemanticChecker` + `diagnostics.py` renderer.
- VS Code extension: update to consume the new LSP capabilities, bump version, update marketplace listing.
- `tests/lsp/test_diagnostics_stream.py` — integration test confirming diagnostics arrive within the debounce window.
- `docs/reference.md` §Editor Integration — document the full LSP surface.

## v4.41.0 — Panel release (arc 2 close)

**FULL 7-REVIEWER PANEL.** Second 5-minor cadence panel. Scope same shape as v4.36.0: LOW sweep, documentation polish, measurement refresh, pre-panel audit, panel runs.

---

# Arc 3 — Tensor completeness (v4.42.0 → v4.46.0)

> **Theme:** Close SPEC §3.10 — tensors become a first-class compilable
> primitive, not a GPU-runtime-only thing. v4.18.0 claimed tensors were
> first-class; v4.25.0 added shape checking; v4.28.0 fixed matmul. This
> arc finally ships tensor literals, indexing, broadcasting, reductions,
> and slicing at the language level.

## v4.42.0 — Tensor literals + runtime primitive wiring

**New syntax — delta review.** Tensor literal form: `Tensor<Float>[[1.0, 2.0], [3.0, 4.0]]`. Shape inferred from the literal, type-checked against the type annotation. Compiles to calls into `runtime/native/mapanare_gpu_builtins.c` with CPU fallback when GPU is unavailable.

**Scope:**
- Grammar: tensor literal production as an alternative to list literal when the type annotation is `Tensor<T>[...]`.
- AST: `TensorLiteral(shape: list[int], elements: list[Expr], element_type: TypeExpr)`.
- Parser + semantic.
- Lowering: to an allocator call + element-by-element stores.
- Runtime: extend `mapanare_gpu_builtins.c` with `__mn_tensor_from_list` if it doesn't already exist.
- CPU fallback path for when CUDA/Vulkan are absent.
- `tests/golden/47_tensor_literal.mn` (note: golden numbering resumes from where it left off after v4.30.0's async deletions).
- Self-hosted mirror.
- Delta review — new syntax, runtime crossing.

**Also sweeps:** 2 LOW items.

## v4.43.0 — Tensor indexing + bounds checking

**New syntax — delta review.** `t[i, j]` for 2-D; `t[i, j, k]` for 3-D; general n-D via comma-separated indices. Bounds checked at runtime (matching v4.32.0's `__mn_list_get` abort-on-OOB discipline).

**Scope:**
- Grammar: `index_expr: expr "[" expr ("," expr)* "]"` — today only accepts one index.
- Semantic: multi-index for tensor types only; single-index still works for lists.
- Lowering: lower to `__mn_tensor_get_nd` runtime call.
- Runtime: extend with n-D get/set primitives, bounds check + abort.
- `tests/golden/48_tensor_indexing.mn`.
- Self-hosted mirror.
- Delta review.

**Also sweeps:** 2 LOW items.

## v4.44.0 — Tensor broadcasting for binary ops

**No new syntax.** The arithmetic operators already exist; broadcasting is a semantic + runtime extension.

**Scope:**
- Semantic: when both operands are tensors, check shape compatibility under NumPy broadcasting rules (dim of 1 broadcasts). Mismatch is a compile-time error with a rustc-quality "these shapes cannot broadcast" message.
- Runtime: `__mn_tensor_add_broadcast`, `_sub`, `_mul`, `_div` that handle shape expansion.
- `tests/golden/49_tensor_broadcast.mn` — include shape-mismatch negative case.
- Self-hosted mirror.
- No delta review needed — no new syntax, only semantic tightening.

**Also sweeps:** 2 LOW items. **Closes Coral LOW item 19** (SPEC §3.10 Status line update — tensors are no longer "not yet implemented in any backend").

## v4.45.0 — Tensor reductions + slicing + views

**New syntax — delta review** (slicing is new).

**Scope:**
- Reductions via method syntax: `t.sum()`, `t.mean()`, `t.max()`, `t.min()`, `t.argmax()`, `t.argmin()`. All optionally take `axis: Int`.
- Slicing syntax: `t[0..2, :]` — range + wildcard — returns a view (new tensor header, shared underlying buffer).
- Grammar: range expression in index position + `:` wildcard.
- Runtime: view types that don't own their buffer; drop glue skips the buffer free on views.
- `tests/golden/50_tensor_ops.mn` — a linear regression example that uses literals + indexing + broadcasting + reductions + slicing, and asserts convergence within tolerance of a reference NumPy implementation.
- Self-hosted mirror.
- Delta review.

## v4.46.0 — Panel release (arc 3 close)

**FULL 7-REVIEWER PANEL.** Third 5-minor cadence. Same shape: LOW sweep, polish, measurement, audit, panel.

---

# Arc 4 — Stdlib AI/LLM growth (v4.47.0 → v4.51.0)

> **Theme:** Expand `stdlib/ai/` so the "AI-native" claim means something
> users can `import`, not just an agent primitive. Four library-only
> releases and one panel. No compiler changes.

## v4.47.0 — `stdlib/ai/llm.mn` — unified LLM interface + streaming

**No new syntax.** Library work on top of existing agent + stream + HTTP primitives.

**Scope:**
- `stdlib/ai/llm.mn` — unified `chat(messages: List<Message>) -> ChatResponse` API. Backend selection via config: OpenAI, Anthropic, Ollama, local llama.cpp.
- Streaming: `chat_stream(messages) -> Stream<ChatChunk>`. Consumes the existing `Stream<T>` primitive; agents can iterate.
- `examples/ai/basic_chat.mn` — 30-line example against Ollama.
- Integration tests that require Ollama skip honestly if unavailable (tracking comment `v4.47.0-ollama-missing`).

**Also sweeps:** 2 LOW items.

## v4.48.0 — `stdlib/ai/structured.mn` — typed structured output

**No new syntax.** Leverages Result + existing struct types + JSON parsing.

**Scope:**
- `chat_structured<T>(messages, schema: T) -> Result<T, ParseError>` — type-parameterized.
- JSON schema generation from struct type at compile time (reuses the v3.x JSON stdlib).
- Retry logic on parse failure with schema hint injection.
- `tests/stdlib/ai/test_structured.py` — offline tests using fixture responses.
- `examples/ai/structured_extraction.mn` — extract a struct from prose text.

**Also sweeps:** 2 LOW items.

## v4.49.0 — `stdlib/ai/embeddings.mn` + `stdlib/ai/rag.mn`

**No new syntax.** Library work.

**Scope:**
- `stdlib/ai/embeddings.mn` — pluggable embedding backend. Returns `List<Float>`.
- `stdlib/ai/rag.mn` — chunking helpers, cosine similarity, top-k retrieval against an in-memory vector list.
- `tests/stdlib/ai/test_embeddings.py`, `test_rag.py`.

**Also sweeps:** 2 LOW items.

## v4.50.0 — AI/LLM end-to-end demos + cookbook chapter

**No new syntax.** Integration-layer release.

**Scope:**
- `examples/ai/chat_agent.mn` — a streaming chat agent using `@agent` + `Stream<ChatChunk>` + the LLM module. End-to-end demo that runs against local Ollama.
- `examples/ai/rag_agent.mn` — agent that retrieves context and streams an answer.
- `docs/cookbook.md` §Building an AI Agent in Mapanare — full tutorial walking through both examples.
- README.md updated with AI-native demo snippet (the recovery arc deliberately did not touch README claims for the AI-native story because there was nothing to point at; v4.50.0 gives the story something to point at).

## v4.51.0 — Panel release (arc 4 close)

**FULL 7-REVIEWER PANEL.** Fourth 5-minor cadence panel.

---

# Arc 5 — Compiler debt drain (v4.52.0 → v4.56.0)

> **Theme:** Close four long-standing `CARRY_FORWARD.md` items that were
> tracked to v5.0.0 or v5.x. The plan puts them in v4.x because "nothing
> changes if we tag v5.0.0" — the work is the work. Closing them in v4.x
> means each gets its own focused release instead of being bundled into a
> v5.0.0 mega-release.

## v4.52.0 — Self-hosted semantic wiring (A7)

**Closes `CARRY_FORWARD.md` A7.** The self-hosted `semantic.mn` exists (1,729 lines) but is not called from `self/main.mn:compile()`. The v4.5.0 CHANGELOG said "self-hosted semantic analysis wired into compile()"; the v4.26.0 panel flagged it as false; the Python side was closed in v4.27.0; A7 is the self-hosted side.

**Scope:**
- `docs/roadmap/v4/v4.52.0/AUDIT.md` — read `mapanare/self/semantic.mn` and `mapanare/semantic.py` side-by-side. Document every divergence. Classify each as "benign" (fine for self-hosted to behave differently) or "must fix" (semantic error that the Python side catches must be catchable self-hosted).
- Wire `semantic_check(prog)` into `self/main.mn:compile()` after parse, before lower. Return `List<SemanticError>`; on non-empty, print via `mn_str_eprint` with rustc-quality rendering and exit 1.
- Diagnostic renderer in self-hosted (mirror of `mapanare/diagnostics.py`). If the self-hosted side doesn't have one, add `mapanare/self/diagnostics.mn`.
- `tests/self_hosted/test_semantic_wiring.py` — compile a deliberately-broken `.mn` file through `mnc-stage1` and confirm exit 1 + expected error text.
- Fixed-point must hold. The semantic check runs before lowering, so the lowered IR should be unchanged — verify stage2/stage3 diff ≤ current threshold.

**Also sweeps:** 2 LOW items.

## v4.53.0 — `UNRESOLVED` / `ERROR` split (A8)

**Closes `CARRY_FORWARD.md` A8.** The self-hosted `semantic.mn` uses `UNKNOWN` where the Python side uses `UNRESOLVED` (type not yet inferred) + `ERROR` (type is definitely wrong). The split makes semantic errors fire at the right place — an `UNRESOLVED` type during inference is progress; an `ERROR` type is a bug and should halt.

**Scope:**
- Extend `TypeKind` in `mapanare/self/types.mn` (or wherever it lives self-hosted) with `UNRESOLVED` + `ERROR` variants. Migrate every `UNKNOWN` call site.
- Update inference to distinguish: unknown-because-not-yet-inferred vs unknown-because-type-error.
- Mirror the change in `mapanare/types.py` if it hasn't been made in Python side (audit first — it was closed in v4.5.0 on the Python side).
- `tests/semantic/test_unresolved_vs_error.py` — one case per transition.

**Also sweeps:** 2 LOW items.

## v4.54.0 — `emit_c.mn` decision (A9)

**Closes `CARRY_FORWARD.md` A9.** The 770-line self-hosted C emitter references MIR types that no longer exist. Decide Path A (rewrite to match current MIR) or Path B (delete + strike the claim).

**Scope:**
- `docs/roadmap/v4/v4.54.0/DECISIONS.md` — written first, states the chosen path and why.
- Most likely Path B: the Python C emitter at `mapanare/emit_c.py` (2,408 lines) covers the same surface for fallback-to-gcc compilation. Delete `mapanare/self/emit_c.mn`, strike the v4.2.0 claim in CHANGELOG, update `docs/roadmap/v4/README.md`.
- If Path A: port the stale file to the current `mir.mn` types. Much bigger scope — probably slips into a v4.54.1 if needed.
- Standard closeout with A9 marked CLOSED in the ledger.

## v4.55.0 — `const` Path A — real `ConstDef` AST node

**Closes the original v4.26.0 `const` CRITICAL properly** — 29 versions after it was first filed. v4.27.0 chose Path B (revert) as the cheap closure. v4.55.0 is the Path A that was always "budgeted for a future release that needs named tensor dimensions." The tensor arc (v4.42.0–v4.45.0) delivered the need.

**Scope:**
- Grammar: `const_def: "const" NAME ":" type_expr "=" expr`. `KW_CONST: "const"`.
- AST: `ConstDef(name, type: TypeExpr, value: Expr)` — **distinct from `ModuleLetDef`**. v4.26.0's mistake was aliasing; v4.55.0 doesn't.
- Parser: propagates the **full `TypeExpr`** (the v4.26.0 parser bug that collapsed to `.name` is specifically avoided).
- Semantic: constant-folding at compile time. Initializer must evaluate to a literal. Reject non-constant initializers with rustc-quality message.
- Symbol table: `is_const=True` and `is_module_level=True`. Assignment to a `const` is a semantic error (real immutability).
- `resolve_shape_from_type` extended to handle named `ConstDef` references. `Tensor<Float>[N, N]` where `const N: Int = 4` resolves to `[4, 4]`.
- Self-hosted mirror.
- `tests/golden/51_const_tensor_shape.mn` — the use case.
- `tests/parser/test_const.py` and `tests/semantic/test_const.py` — **the files that v4.26.0's CHANGELOG claimed existed but didn't**. Now they exist for real.
- Delta review (Anaconda or Coral lens).

## v4.56.0 — Panel release (arc 5 close)

**FULL 7-REVIEWER PANEL.** Fifth 5-minor cadence panel.

---

# Arc 6 — Deprecation and deletion (v4.57.0 → v4.61.0)

> **Theme:** Drain `CARRY_FORWARD.md` items A3 (Python emitter removal)
> and A4 (llvmlite JIT removal). Plus a final dead-code audit and test
> honesty pass. This is the "stop carrying deprecated code" arc.

## v4.57.0 — Python emitter deprecation (warnings only)

**No deletion — warning-only release.** Give users (and tests) one release of loud warnings before the deletion in v4.58.0.

**Scope:**
- `mapanare/emit_python_mir.py` — add `warnings.warn("PythonMIREmitter is deprecated; use LLVM backend. Deletion in v4.58.0.", DeprecationWarning)` at every public entry.
- `mapanare/cli.py` — if `emit-mir` or `jit` commands dispatch through Python emitter, print a stderr warning with the v4.58.0 deletion target.
- `tests/conftest.py` — any `_PYTHON_MIR_XFAIL` entries currently tracked to v5.0.0 re-point to v4.58.0.
- CHANGELOG v4.57.0 entry documents the migration path clearly.

**Also sweeps:** 2 LOW items.

## v4.58.0 — Python emitter deletion (A3)

**Closes `CARRY_FORWARD.md` A3.**

**Scope:**
- `mapanare/emit_python_mir.py` — deleted (~1,220 lines).
- `mapanare/cli.py` `cmd_run`, `cmd_jit`, `cmd_compile` paths that defaulted to Python — rewrite to default to LLVM.
- Tests tagged `_PYTHON_MIR_XFAIL` — delete the tests, delete the xfail entries in `tests/conftest.py`.
- Bootstrap: `scripts/build_from_seed.sh` already goes through LLVM via `mnc-stage1`; verify no path still goes through Python.
- `docs/migration/v4.57-to-v4.58.md` — user-facing migration note for anyone still using `emit-python-mir` or `jit`.

**Also sweeps:** 2 LOW items.

## v4.59.0 — llvmlite JIT deprecation + deletion (A4)

**Closes `CARRY_FORWARD.md` A4.** Combined in one release because the llvmlite JIT has a smaller footprint than the Python emitter and there's no user-facing path that depends on it today.

**Scope:**
- `mapanare/jit.py` — deleted.
- `mapanare/cli.py cmd_jit` — deleted (or rewritten to be an alias for `mnc run`).
- `requirements*.txt` — llvmlite entries removed.
- `tests/jit/` — deleted.
- SPEC §JIT rewritten to describe `mnc run` (AOT compile + execvp) as the canonical "run" path.

**Also sweeps:** 2 LOW items.

## v4.60.0 — Dead code audit + test honesty final pass

**Sweep release.**

**Scope:**
- `python -m vulture mapanare/ --min-confidence 90` — audit output, delete real dead code, annotate false positives.
- Every `pytest.mark.skip` / `xfail` with a tracking comment older than v4.40.0 — force the tracking comment to be rewritten or the test to be unskipped. The `check_silent_skips.py` gate already enforces tracking comments; v4.60.0 enforces that the tracking version is not ancient.
- Any stale CHANGELOG entry from the v4.18.0–v4.26.0 era that still has a claim that hasn't been re-verified — re-verify or strike.
- Any TODO/FIXME comment in the codebase older than v4.30.0 — resolve or file as a `CARRY_FORWARD.md` LOW item with a tracking version.
- CARRY_FORWARD.md audit: every row with cycles ≥ 3 re-examined. Close or re-commit with explicit tracking version.

## v4.61.0 — Panel release (arc 6 close)

**FULL 7-REVIEWER PANEL.** Sixth 5-minor cadence panel.

---

# Arc 7 — DWARF debug info (v4.62.0 → v4.66.0)

> **Theme:** Close `CARRY_FORWARD.md` A2. DWARF debug info was claimed in
> v0.7.0, never implemented, tracked for six review cycles. This arc
> ships it from infrastructure through llvm-dwarfdump --verify clean to
> real gdb backtraces with source line and variable info.

## v4.62.0 — DWARF infrastructure + design document

**No user-visible feature. Foundation for the arc.**

**Scope:**
- `docs/roadmap/v4/v4.62.0/DESIGN.md` — read LLVM's DWARF documentation end-to-end; document which `llvm.dbg.*` intrinsics we need, which DI* metadata types, how the MIR needs to carry source-position info through lowering.
- Audit: does MIR currently carry `Span` on every instruction? If not, add it.
- `mapanare/mir.py` — `DebugInfo` dataclass + attachment hooks on `Function` and `BasicBlock`.
- `mapanare/emit_llvm_text.py` — infrastructure only: a `_emit_debug_metadata` method that knows how to emit `!0 = !{...}` style metadata. Not wired to actual DWARF types yet.
- `scripts/check_dwarf.sh` — runs `llvm-dwarfdump --verify` on a `-g` build. Expected to be empty output for now (no DWARF yet); subsequent releases in the arc fill it in.

## v4.63.0 — DICompileUnit + DISubprogram emission

**First real DWARF emission.**

**Scope:**
- Emit `!DICompileUnit` at module top with `language: DW_LANG_C99`, `producer: "mapanare MAPANARE_VERSION"`, `file: !...`, `emissionKind: FullDebug`.
- Emit `!DIFile` for every source file touched by the module.
- Emit `!DISubprogram` for every function with `name`, `scope`, `file`, `line`, `type`, `spFlags: DISPFlagDefinition`.
- Attach `!dbg` to the function definition via the `!<n>` reference.
- `scripts/check_dwarf.sh` — now `llvm-dwarfdump --verify` on a `-g` build of `tests/golden/01_hello.mn` is expected to show `DICompileUnit` and `DISubprogram` entries and exit 0.
- `tests/llvm/test_dwarf_compile_unit.py` — grep the emitted IR for `!DICompileUnit` and `!DISubprogram` and verify structure.

## v4.64.0 — Line metadata on every instruction

**!dbg attachments.**

**Scope:**
- Every LLVM instruction emitted from `emit_llvm_text.py` gets a trailing `, !dbg !<n>` where `!<n>` is a `!DILocation(line: <line>, column: <col>, scope: !<subprogram>)`.
- MIR → LLVM lowering threads the instruction's source `Span` through to the emitted metadata.
- `scripts/check_dwarf.sh` now includes a round-trip test: compile a golden with `-g`, run it under `addr2line`, verify the reported source line matches the known line in the `.mn` source.
- `tests/llvm/test_dwarf_line_info.py`.

## v4.65.0 — DILocalVariable + llvm.dbg.declare/value

**Complete DWARF minimum-viable.** Closes the arc's capability scope.

**Scope:**
- Emit `!DILocalVariable` for every `let` binding.
- Emit `llvm.dbg.declare(metadata ptr %<alloca>, metadata !<local>, metadata !DIExpression())` at the `alloca` site.
- For SSA values that live through `mem2reg`, emit `llvm.dbg.value(...)` at update sites.
- `tests/llvm/test_dwarf_variables.py` — compile with `-g`, run under `gdb` in a subprocess, assert the backtrace shows local variables by name.
- gdb integration test (may be skipped honestly in CI environments without gdb; otherwise mandatory).

## v4.66.0 — Panel release (arc 7 close)

**FULL 7-REVIEWER PANEL.** Seventh 5-minor cadence panel.

---

# Arc 8 — Coroutine foundation (v4.67.0 → v4.71.0)

> **Theme:** Real `async`/`await` via LLVM coroutine intrinsics. The
> v4.30.0 Path B strike was always temporary — the deferral was about
> scope, not intent. This arc is the first of two that ship real
> coroutines: design + grammar + semantic + MIR changes. Lowering
> happens in arc 9.

## v4.67.0 — Coroutine design document

**No new feature. Pure design work.**

**Scope:**
- `docs/roadmap/v4/v4.67.0/DESIGN.md` — the big document.
  - LLVM coroutine intrinsics study: `llvm.coro.id`, `llvm.coro.alloc`, `llvm.coro.begin`, `llvm.coro.suspend`, `llvm.coro.save`, `llvm.coro.end`, `llvm.coro.free`, `llvm.coro.resume`, `llvm.coro.destroy`.
  - References: LLVM Coroutines docs, the 2016 Gor Nishanov coroutine split patches, Clang's `-fcoroutines-ts` implementation.
  - Mapanare-specific: how does this interact with the existing `runtime/native` cooperative scheduler (currently mobile-only)? Should the scheduler extend to desktop? Design decision with rationale.
  - Pass pipeline: coro-split must run before inlining. Where in our optimizer does that sit?
  - Stream integration: what does `for await chunk in stream { ... }` lower to in terms of suspension points?
  - Risk register: what's hard? What's the smallest unit of coroutine work that can be verified end-to-end?
- Design doc reviewed informally by Rattler (LLVM lens) before any code ships.

**No code changes — design-only release.** The SESSION_REPORT for v4.67.0 is the design doc plus a one-page summary of decisions.

## v4.68.0 — async/await grammar + AST + parser

**New syntax — delta review (mandatory).** `async`/`await` return to the grammar for real this time.

**Scope:**
- Grammar: `async_fn_def: "async" "fn" ...`; `await_expr: "await" expr`.
- Terminal: `KW_ASYNC: "async"`, `KW_AWAIT: "await"`.
- AST: `AsyncFnDef`, `AwaitExpr` — real nodes, not aliases. The v4.30.0 deletion is reverted at the grammar level; the AST and parser are reintroduced.
- Parser transformer: builds the nodes and propagates spans.
- Self-hosted mirror.
- `tests/parser/test_async_await.py` — positive + negative parse cases.
- Delta review (Rattler + Anaconda — both lenses matter for new syntax that affects compile pipeline).
- **No semantic, no lowering, no runtime in this release.** Attempting to *compile* an `async fn` in v4.68.0 produces a rustc-quality error: "async/await is under construction; see v4.69.0–v4.71.0 for incremental support." That's the honest interim state.

## v4.69.0 — Semantic analysis for async functions

**No new syntax.** Build on v4.68.0's AST.

**Scope:**
- `SemanticChecker` — when visiting an `AsyncFnDef`, mark the function as async in the symbol table.
- When visiting an `AwaitExpr`, verify the enclosing function is async. Reject with rustc-quality message otherwise.
- Verify the awaited expression has type `Future<T>` or `Stream<T>` (new type constructors to be added — see below).
- The function's return type: `async fn foo() -> T` is sugar for `fn foo() -> Future<T>` in the type system.
- `mapanare/types.py` — add `FUTURE` to `TypeKind` if not present. `Future<T>` and `Stream<T>` become first-class type constructors.
- Self-hosted mirror.
- `tests/semantic/test_async_semantics.py` — type checking cases.

**Compiling an `async fn` still fails in v4.69.0** — but now the error moves from the parser to the lowerer, which has a placeholder that says "async lowering coming in v4.70.0."

## v4.70.0 — MIR suspension points + coroutine lowering part 1

**No new syntax. Major internal work.**

**Scope:**
- `mapanare/mir.py` — new instruction kinds: `Suspend`, `CoroutineState`, `AwaitPoint`. Metadata on functions marked `async`.
- `mapanare/lower.py` `_lower_async_fn` — lower an `async fn` body into a MIR function with suspension points at every `await`. Reference: the design doc from v4.67.0.
- `emit_llvm_text.py` `_emit_coroutine_prelude` — emit the coro-split prelude for every async function:
  - `%id = call token @llvm.coro.id(...)`
  - `%size = call i64 @llvm.coro.size.i64()`
  - `%mem = call ptr @malloc(i64 %size)`
  - `%hdl = call ptr @llvm.coro.begin(token %id, ptr %mem)`
- Not yet: actual suspension, resume handling, cleanup. That's v4.71.0.
- `tests/llvm/test_coroutine_prelude.py` — grep the emitted IR for the prelude pattern. Compile with `-O0` and verify `llvm-as` accepts it.

## v4.71.0 — Panel release (arc 8 close)

**FULL 7-REVIEWER PANEL.** Eighth 5-minor cadence panel.

Arc 8 close: async/await is at the grammar-semantic-partial-lowering stage. It compiles to something LLVM accepts but doesn't actually run yet (no suspend points wired, no scheduler integration). The panel's job at v4.71.0 is to verify that what shipped is coherent, not to validate end-to-end async — that's arc 9's work.

---

# Arc 9 — Coroutine completion (v4.72.0 → v4.76.0)

> **Theme:** Finish the coroutine work. Actual suspension, scheduler
> integration, Stream async iterator, end-to-end async golden test.

## v4.72.0 — Coroutine lowering part 2: suspend + resume + destroy

**Scope:**
- `emit_llvm_text.py` `_emit_coroutine_suspend` — lower every MIR `AwaitPoint` to:
  - `%save = call token @llvm.coro.save(ptr %hdl)`
  - `%result = call i8 @llvm.coro.suspend(token %save, i1 false)`
  - `switch i8 %result, label %suspend [ i8 0, label %resume i8 1, label %cleanup ]`
- `_emit_coroutine_epilogue` — lower every async fn exit to `@llvm.coro.end`.
- Runtime wrapper: `__mn_coroutine_resume(handle)` → `@llvm.coro.resume(ptr %hdl)`.
- `tests/llvm/test_coroutine_lowering.py` — compile and inspect IR, confirm suspend/resume structure matches the LLVM coroutine ABI.

## v4.73.0 — Runtime scheduler integration (desktop extension)

**Scope:**
- `runtime/native/mapanare_runtime.c` — the cooperative scheduler that exists for the mobile target (`MAPANARE_MOBILE` build flag) gets extended to desktop. Design choices already made in v4.67.0's DESIGN.md.
- Scheduler drives coroutine handles: resume, destroy, await-point awareness.
- `__mn_runtime_spawn_coroutine(handle)` entry point.
- Stress test: 1000 coroutines, each doing N suspension points, verify all complete.

## v4.74.0 — Stream async iterator interface

**New syntax — delta review.** `for await chunk in stream { ... }`.

**Scope:**
- Grammar: `for_await: "for" "await" pattern "in" expr block`.
- AST: `ForAwait(pattern, iterable, body)`.
- Semantic: iterable must be `Stream<T>`; the enclosing function must be async.
- Lowering: desugar to a loop with an `await stream.next()` at the top and a break on `None`.
- Runtime: `Stream<T>` gets a `next() -> Future<Option<T>>` method.
- `tests/golden/52_for_await.mn`.
- Delta review.

## v4.75.0 — End-to-end async demo + tests

**Integration release.**

**Scope:**
- `tests/golden/53_real_await.mn` — multiple `async fn`s, multiple suspension points, result accumulation across a coroutine boundary, verified behavior matches the expected cooperative schedule. This is the golden test the v4.26.0 panel flagged as missing.
- `examples/async/http_fanout.mn` — fetch 10 URLs concurrently via `async fn`s, aggregate results. End-to-end demo.
- `examples/async/chat_stream.mn` — the v4.50.0 stdlib/ai chat agent rewritten to use `for await chunk in llm.chat_stream(...)` and return via `async fn`.
- `docs/cookbook.md` §Async programming in Mapanare — tutorial.
- `CARRY_FORWARD.md` A1 marked CLOSED.

## v4.76.0 — Panel release (arc 9 close)

**FULL 7-REVIEWER PANEL.** Ninth 5-minor cadence panel. At this point:

- All `CARRY_FORWARD.md` A1–A9 items closed (if not already)
- All v4.31.0 arc-end panel docket items closed
- Language surface: `?` operator, pattern matching with guards/or-patterns, tensor completeness, stdlib AI/LLM, DWARF debug info, real async/await
- Compiler hygiene: self-hosted semantic wired, Python emitter deleted, llvmlite JIT deleted, `emit_c.mn` resolved
- Nine independent panels across the arc

**This is where the lead can choose to tag v5.0.0** if they want a major label on the work. The v4.76.0 panel is already a full release-gate-quality panel by construction (5-minor cadence + arc close). Tagging v5.0.0 from v4.76.0 is zero additional work; staying in v4.x is zero additional work. Either is fine.

---

## Panel schedule summary

| Panel # | Release | Arc closed | Trigger |
|---|---|---|---|
| — | v4.31.0 | recovery arc | recovery-arc terminator (done) |
| 1 | v4.36.0 | arc 1 (error handling + match) | 5-minor cadence |
| 2 | v4.41.0 | arc 2 (LSP) | 5-minor cadence |
| 3 | v4.46.0 | arc 3 (tensor) | 5-minor cadence |
| 4 | v4.51.0 | arc 4 (stdlib AI) | 5-minor cadence |
| 5 | v4.56.0 | arc 5 (compiler debt drain) | 5-minor cadence |
| 6 | v4.61.0 | arc 6 (deprecation + deletion) | 5-minor cadence |
| 7 | v4.66.0 | arc 7 (DWARF) | 5-minor cadence |
| 8 | v4.71.0 | arc 8 (coroutine foundation) | 5-minor cadence |
| 9 | v4.76.0 | arc 9 (coroutine completion) | 5-minor cadence |

Plus delta reviews on every new-syntax release: v4.33.0 (`?`), v4.35.0 (guards + or-patterns), v4.42.0 (tensor literals), v4.43.0 (tensor indexing), v4.45.0 (tensor slicing), v4.55.0 (real `const`), v4.68.0 (`async`/`await` grammar), v4.74.0 (`for await`). Eight delta reviews.

**Panels are not optional, and arcs never skip theirs.** If a panel returns NEEDS WORK, the next arc compresses — its first release becomes a recovery-style closeout. The next arc's theme slides. The plan is the same; the pace is the same; the sequence adjusts.

---

## What this plan deliberately does NOT do

- **No v5.0.0 scheduling.** Major bumps are a labeling concern. The plan has enough built-in panel gates (9 of them) that tagging v5.0.0 at any arc close is fine. The lead chooses when they want the major label.
- **No features committed past v4.76.0.** Arc 9 ends with async/await shipping. Post-async growth is explicitly not planned here — it's the lead's call whether to continue into AI-native primitives, GPU kernel fusion, distributed agent routing, autograd, etc.
- **No compression of big features.** Coroutines get 10 releases across 2 arcs. Tensors get 4 releases. LSP gets 4 releases. The recovery arc's lesson was "small coherent increments with end-to-end verification per release" — this plan holds that line.
- **No features in panel releases.** v4.36.0, v4.41.0, v4.46.0, etc. are deliberately quiet so the panel has a stable target.
- **No carry-forward debt left unscheduled.** Every open item in `CARRY_FORWARD.md` has a home: `A1` at v4.75.0, `A2` at v4.65.0, `A3` at v4.58.0, `A4` at v4.59.0, `A5` at the Culebra upstream (not this repo), `A6` at v4.34.0, `A7` at v4.52.0, `A8` at v4.53.0, `A9` at v4.54.0.
- **No backwards compatibility constraints that force awkward design.** We can break things in v4.x if the old behavior was wrong — the recovery arc taught us to prefer honest deletion over preserving hollow syntax. The plan uses this freedom sparingly but uses it.

---

## Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| v4.32.0 Phase 1.2 (self-hosted emitter parity) cascades | medium | high | Time-box to one sprint; if it cascades, v4.33.0 slips and becomes a parity-only release |
| Delta reviewer unavailable | low | medium | Reviewers are internal characters, availability is a scheduling issue |
| A scheduled panel returns NEEDS WORK | medium over 9 panels | high | Recovery protocol re-engages at the next release; the arc extends |
| Coroutine work turns out bigger than 10 releases | medium | high | Arc 8 is design-heavy on purpose — if v4.67.0–v4.71.0 surfaces that the scope is wrong, re-sequence arc 9 |
| DWARF variables (v4.65.0) pull in pass-pipeline surprises | medium | medium | Scoped small; if it cascades, ship `DILocalVariable` only and defer `llvm.dbg.declare`/`value` to a follow-up point release |
| Tensor broadcasting shape-error quality becomes a design hole | low-medium | low | v4.44.0 is dedicated to shape errors; if not enough, budget a v4.44.1 point release |
| Carry-forward ledger drifts out of sync | medium | medium | Update protocol in `CARRY_FORWARD.md` footer; every SESSION_REPORT appends only |
| A new hollow feature slips through a delta review | very low | catastrophic | Both the CI hollow-features gate and the delta reviewer must sign off; both must agree before merge |
| The plan's 45 releases overwhelm the lead | medium-high | high | The plan is optional in its entirety. Each arc closes in 5 releases. The lead can pause between arcs indefinitely. The 9-panel structure means every 5 releases is a natural breakpoint |

---

## How to read this document

Every **arc** is a 5-release unit that closes with a panel. Within each
arc, the first 4 releases are work (features, debt drain, or both), and
the 5th is a deliberately-quiet consolidation release where the full
panel runs.

Every **release** has its own `PLAN.md` in `docs/roadmap/v4/vX.Y.Z/PLAN.md`.
This document is the high-level shape; the PLAN.md files are where the
per-release detail lives. As of 2026-04-11, full PLAN.md files exist
for:

- `v4.32.0/PLAN.md` — arc-end panel closure
- `v4.33.0/PLAN.md` — the `?` operator
- `v4.34.0/PLAN.md` — match decision-tree rewrite + exhaustiveness
- `v4.35.0/PLAN.md` — match guards + or-patterns

Subsequent PLAN.md files get written as each release approaches, following
the recovery-arc template (PLAN.md + PROMPT.md + SESSION_REPORT.md per
release directory).

---

## Summary

**45 releases. 9 panels. 9 thematic arcs. Zero v5.0.0 work — all of it lives in v4.x.** The major bump is a labeling decision the lead makes whenever they want, with no impact on the plan.

Every release has:
- A theme that closes exactly one design concern cleanly
- Pre-committed verifiable exit criteria
- Delta review if it adds syntax
- LOW item sweep (2–3 items from the carry-forward queue)
- Scheduled panel release at the 5-minor cadence

The shape preserves every anti-rush rule the recovery arc installed, and
adds one: **big features break into small releases that each verify end-
to-end at PR time.** Coroutines take 10 releases. Tensors take 4. LSP
takes 4. DWARF takes 4. None of it is compressed to hit a version-number
milestone; all of it is shippable whenever the work is ready.
