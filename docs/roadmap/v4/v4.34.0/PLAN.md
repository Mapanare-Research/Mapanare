# Mapanare v4.34.0 — Pattern Matching Rewrite (Decision Tree + Exhaustiveness)

> **Zero new syntax. Pure correctness + error-quality work.** This
> release closes `CARRY_FORWARD.md` A6 (the 69-line stage2/stage3 diff
> that has been open since v4.28.0) by rewriting the match lowering in
> both Python and self-hosted pipelines using Luc Maranget's 2008
> decision-tree compilation algorithm, and upgrades exhaustiveness
> checking from "warning or missing" to "compile-time error with
> rustc-quality diagnostic."

**Status:** DONE (2026-04-12)
**Breaking:** No (same surface syntax; improved IR shape and error messages)
**Prerequisite:** v4.33.0 (the `?` operator release — `?` desugars to match, so v4.34.0's match rewrite automatically improves `?` IR quality)
**Delta review:** No (zero new syntax — decision-tree rewrite is invisible to users except via better error messages)
**Full panel:** No (cadence fires at v4.36.0)
**Estimated work:** 2 sprints (this is bigger than v4.33.0; the algorithm is well-documented but the mirror work is non-trivial)
**Theme:** Close A6. Upgrade exhaustiveness checking. Make match IR consistent between Python and self-hosted lowering.

---

## Why now

**Why the rewrite.** The v4.28.0 fixed-point verification established a 69-line residual diff between `stage2.ll` (produced by `mnc-stage1` compiling `mnc_all.mn`) and `stage3.ll` (produced by `mnc-stage2` compiling the same source). Culebra attribution traced the diff to the match-lowering code path. Specifically: the self-hosted emitter materializes unreachable-but-alloca-safe match arms slightly differently from the Python bootstrap. Both are correct — `llvm-as` accepts both — but they don't produce byte-identical IR, which means the fixed-point claim is "near fixed-point at 0.062%" instead of "true fixed-point at 0%".

A6 has been open for 6 releases (v4.28.0, v4.29.0, v4.30.0, v4.31.0, v4.32.0, v4.33.0). The v4.26.0 panel flagged it; the recovery arc explicitly deferred it ("v5.x rewrite of match lowering"); the v4.31.0 panel re-flagged it as the one carry-forward the arc did not close. v4.34.0 closes it.

**Why now.** Three reasons:

1. **`?` is the right predecessor.** v4.33.0 shipped `?`, which desugars to `match`. Any IR quality improvement to `match` lowering automatically improves `?` chains too. Doing the rewrite immediately after `?` ships means `?` users never experience the "old match lowering" era in production.
2. **Exhaustiveness checking is load-bearing for a type-safe language.** Today, the semantic checker does incomplete exhaustiveness checking — some cases fire warnings, some don't fire at all, and the warnings aren't rustc-quality. A language that claims to be type-safe and has `Option`/`Result` as first-class primitives needs exhaustiveness as a compile error, not a warning. Cobra flagged this at v4.26.0 as "an embarrassment."
3. **v4.35.0 match guards need the decision-tree infrastructure.** Adding guards to the existing match lowerer would require another hack; building them on top of a decision-tree compiler is clean. The right order is: rewrite first, then add guards.

**What is Maranget's algorithm.** Luc Maranget's 2008 paper "Compiling Pattern Matching to Good Decision Trees" (ML workshop) gives the standard decision-tree compilation used by OCaml, Haskell, Rust, Swift, Scala, and basically every production ML-family compiler. The algorithm:

1. Start with a pattern matrix: rows are `case` arms, columns are the sub-expressions being matched.
2. Choose a column to split on. Heuristic: the column with the most distinct constructors first — "necessity-based selection" in Maranget's paper.
3. For each constructor appearing in that column, create a sub-matrix containing only the rows that could match that constructor, and recurse.
4. Leaves are the actions (the RHS of each `case` arm).
5. Exhaustiveness: if a sub-matrix has no rows, the match is non-exhaustive — emit an error naming the missing pattern.

The output is a decision tree with minimal branching. Unreachable match arms are detected as "rows that never appear in any sub-matrix" and warned about.

**Why the current lowering produces 69 lines of diff.** The Python bootstrap uses a naive "sequential match" lowering: each case arm becomes a block that checks the full pattern, jumps to the next arm on mismatch, jumps to a merge block on match. The self-hosted rewrite (added in v3.x) uses a slightly different shape — same semantics, different instruction order, different unreachable-arm materialization. The two are byte-different because neither is canonical. Maranget decision-tree compilation is canonical, and if both sides implement it faithfully, they produce identical IR.

---

## Design document (Phase 0 — before code)

This release is unusual: the design document is Phase 0, not an optional appendix. The algorithm is complex enough that getting it wrong is easy, and getting two independent implementations (Python + self-hosted) to agree byte-for-byte requires shared design notes.

### Phase 0.1: Write `docs/roadmap/v4/v4.34.0/DESIGN.md`

The document should cover:

1. **Algorithm reference.** Link to the Maranget paper and (at least) the Rust RFC for how they adapted it. Note any deviations we plan.
2. **Pattern matrix representation.** Data structure: `PatternMatrix = List[Row]` where `Row = { patterns: List[Pattern], action: ActionRef, guard: Optional[Expr] (v4.35.0) }`. Column operations: "specialize by constructor C", "default".
3. **Constructor enumeration.** For each user-defined enum type, the compiler needs the full list of variant tags. For builtins: `Option` → `[Some, None]`, `Result` → `[Ok, Err]`, integers → "infinite, default arm required", strings → "infinite, default arm required".
4. **Decision-tree node types.** `Leaf(action)`, `Switch(column_index, cases: Map[Tag, DecisionTree], default: Optional[DecisionTree])`, `Fail(reason: NonExhaustive | Unreachable)`.
5. **Emission rules.** How does a `DecisionTree` lower to MIR basic blocks? `Leaf` → jump to the action block; `Switch` → MIR `TagSwitch` instruction (reuse the existing one if it exists, otherwise add one); `Fail` → unreachable.
6. **Error diagnostics.** When a `Fail(NonExhaustive)` is emitted, the diagnostic names which pattern is missing. Maranget's algorithm produces a witness for the missing pattern as a byproduct of the specialization walk — use that.
7. **Byte-identical invariant.** Both Python and self-hosted implementations must produce the same MIR block ordering, same block names, same instruction order. Specific rules:
   - Blocks are named `match_<N>_case_<M>` deterministically where N is the match counter and M is the case index.
   - The default-case block is named `match_<N>_default` or `match_<N>_unreachable` depending on whether the match is provably exhaustive.
   - Column-selection heuristic is "leftmost column with most distinct constructors; tiebreak by column index" (deterministic).
   - Instruction order within a block follows the pattern matrix row order.
8. **Migration path.** How does the new lowerer coexist with any remaining call sites to the old one? Plan: replace `_lower_match` wholesale in one commit; no dual-path period.
9. **Risk: nested patterns.** OCaml-style nested destructuring patterns (`Some(Ok(Pair(x, y)))`) require column explosion. The current Mapanare grammar supports some nesting; audit the grammar before committing to the algorithm complexity.
10. **Risk: literal patterns.** Integer literal patterns (`case 42 => ...`) have no constructor enumeration. Handle as "per-literal specialization with default arm required." Maranget covers this in §4 of the paper.
11. **Out of scope for v4.34.0.** Guards (v4.35.0), or-patterns (v4.35.0), range patterns (`case 1..10 =>`) — tracked separately if needed.

### Phase 0.2: Informal review by Cobra + Rattler

- [ ] Rattler reviews the emission rules. Verifies that decision trees with the specified block-naming discipline produce IR that `llvm-as` will accept without surprises.
- [ ] Cobra reviews the pattern-matrix data structure. Verifies the C++-veteran's concern that it's not over-engineered.
- [ ] Both sign off before Phase 1 starts coding.
- [ ] DESIGN.md committed alongside the PLAN.md. The delta review at v4.35.0 will reference DESIGN.md for the guards addition.

**No code ships in Phase 0.** DESIGN.md is the artifact.

---

## Phase 1 — Python pipeline rewrite

### Phase 1.1: Pattern matrix data structure

- [ ] `mapanare/lower.py` — new internal classes:

  ```python
  @dataclass
  class PatternRow:
      patterns: list[Pattern]  # length = N columns
      action_idx: int  # index into match_arms list
      # v4.35.0 will add: guard: Optional[Expr]
      # v4.35.0 will add: source_span: Span

  @dataclass
  class PatternMatrix:
      rows: list[PatternRow]
      columns: list[MIRValue]  # sub-expressions being matched
      # Methods: specialize(col, ctor) -> PatternMatrix; default(col) -> PatternMatrix
  ```

- [ ] `Pattern` class extensions (if the current AST Pattern doesn't support everything we need):
  - `PatternWildcard()` — the `_` pattern
  - `PatternLiteral(value: int | str | bool)` — for integer/string/bool literal patterns
  - `PatternConstructor(tag: str, subpatterns: list[Pattern])` — for enum variants
  - `PatternBinding(name: str, subpattern: Pattern)` — for `case x @ Some(42) =>` (might not be in v4.34.0 scope; audit)
  - `PatternStruct(type_name: str, fields: dict[str, Pattern])` — for struct destructuring
  - `PatternTuple(elements: list[Pattern])` — for tuple destructuring if supported

### Phase 1.2: Decision-tree builder

- [ ] `mapanare/lower.py` — new method `_build_decision_tree(matrix: PatternMatrix) -> DecisionTree`:

  ```python
  def _build_decision_tree(self, matrix: PatternMatrix) -> DecisionTree:
      # Base cases
      if not matrix.rows:
          return Fail(reason="NonExhaustive", witness=self._build_witness(matrix))
      if self._is_all_wildcards(matrix.rows[0]):
          # First row matches everything; it's the action
          return Leaf(action=matrix.rows[0].action_idx)

      # Choose a column to split on
      col_idx = self._select_column(matrix)
      col_type = matrix.columns[col_idx].type

      # Enumerate constructors for this column
      ctors = self._enumerate_constructors(col_type)
      cases: dict[str, DecisionTree] = {}
      for ctor in ctors:
          specialized = matrix.specialize(col_idx, ctor)
          cases[ctor.tag] = self._build_decision_tree(specialized)

      # Default arm (for open-ended types like Int or when not all constructors are covered)
      default: Optional[DecisionTree] = None
      if not self._is_closed_type(col_type) or not self._all_ctors_covered(matrix, col_idx, ctors):
          defaulted = matrix.default(col_idx)
          default = self._build_decision_tree(defaulted)

      return Switch(column_idx=col_idx, cases=cases, default=default)
  ```

- [ ] Helper: `_select_column(matrix: PatternMatrix) -> int` — the "leftmost with most distinct constructors" heuristic. Deterministic tiebreak by column index.
- [ ] Helper: `_enumerate_constructors(type: MIRType) -> list[Constructor]` — for enum types, returns all variants; for builtins, returns the known set; for open types (Int, String, List), returns empty (→ default required).
- [ ] Helper: `_is_closed_type(type: MIRType) -> bool` — enum types and bounded builtins are closed; Int/String/List are open.
- [ ] Helper: `_build_witness(matrix: PatternMatrix) -> Pattern` — used for `NonExhaustive` diagnostics to name which pattern is missing. Walks the partial decision tree to construct a concrete pattern that would have matched.

### Phase 1.3: Decision-tree emitter

- [ ] `mapanare/lower.py` — new method `_emit_decision_tree(tree: DecisionTree, matrix: PatternMatrix, merge_block: str) -> None`:

  ```python
  def _emit_decision_tree(self, tree: DecisionTree, matrix: PatternMatrix, merge_block: str) -> None:
      if isinstance(tree, Leaf):
          # Emit a jump to the action block
          action_block = self._action_blocks[tree.action]
          self._emit_jump(action_block)
          return
      if isinstance(tree, Fail):
          # Should never be reached at runtime, but LLVM needs a terminator
          self._emit_unreachable()
          return
      if isinstance(tree, Switch):
          col_value = matrix.columns[tree.column_idx]
          # Emit a TagSwitch MIR instruction
          cases_mir = []
          for tag, subtree in tree.cases.items():
              subtree_block = self._fresh_block(f"match_{self.match_counter}_case_{tag}")
              cases_mir.append((tag, subtree_block))
              # Recurse into the subtree from this block
              with self._in_block(subtree_block):
                  # Extract the payload binding for this case
                  self._emit_payload_extraction(col_value, tag)
                  self._emit_decision_tree(subtree, self._specialized_matrix(...), merge_block)
          default_block = None
          if tree.default is not None:
              default_block = self._fresh_block(f"match_{self.match_counter}_default")
              with self._in_block(default_block):
                  self._emit_decision_tree(tree.default, self._default_matrix(...), merge_block)
          self._emit_tag_switch(col_value, cases_mir, default_block)
          return
      raise AssertionError(f"Unknown decision tree node: {type(tree)}")
  ```

- [ ] The block-naming discipline (`match_<N>_case_<tag>` / `match_<N>_default`) is deterministic across the Python and self-hosted implementations. **This is the byte-identity invariant.**

### Phase 1.4: Replace `_lower_match`

- [ ] `mapanare/lower.py` — the old `_lower_match` method is replaced wholesale with:

  ```python
  def _lower_match(self, node: MatchExpr) -> MIRValue:
      # Build the initial pattern matrix from match arms
      matrix = self._build_initial_matrix(node)
      # Build the decision tree
      tree = self._build_decision_tree(matrix)
      # If the tree reports non-exhaustive, error out
      self._check_exhaustiveness(tree, node)
      # Emit MIR blocks for the tree
      merge_block = self._fresh_block(f"match_{self.match_counter}_merge")
      self._emit_decision_tree(tree, matrix, merge_block)
      # Return a PHI at the merge block that binds the action results
      self._enter_block(merge_block)
      return self._match_phi
  ```

- [ ] The action blocks (one per `case` arm's RHS) are pre-built; the decision tree's `Leaf` node jumps to them. This means action code is lowered exactly once even if the decision tree "visits" the action from multiple branches (common when a match has or-patterns — but or-patterns are v4.35.0, so for v4.34.0 this is "exactly once per arm, period").

- [ ] Old `_lower_match` methods removed. Grep `mapanare/lower.py` for `_lower_match_old` / `_lower_case_arm` / `_match_chain` / any helper that was only called from the old lowering and is now dead. Delete.

### Phase 1.5: Exhaustiveness checking in the semantic pass

- [ ] `mapanare/semantic.py` — the exhaustiveness check currently lives in the lowerer (or nowhere). Move it to `semantic.py`:

  ```python
  def check_match_exhaustive(self, node: MatchExpr) -> None:
      matrix = self._build_pattern_matrix(node)
      non_exhaustive_witnesses = self._find_non_exhaustive(matrix)
      for witness in non_exhaustive_witnesses:
          self._error(SemanticError(
              line=node.span.line,
              column=node.span.column,
              end_line=node.span.end_line,
              end_column=node.span.end_column,
              message=f"non-exhaustive match: pattern `{witness}` is not covered",
              suggestion=f"add a `case {witness} => ...` arm, or use `_` to match all remaining cases",
              filename=self.filename,
          ))
  ```

- [ ] The exhaustiveness check re-runs the decision-tree build (without emitting) to find `Fail(NonExhaustive)` nodes and their witnesses. This is intentional duplication with `lower.py`'s tree build — the semantic pass needs to surface errors *before* the lowerer runs, so the user sees the error at the right place.
- [ ] Alternative: factor out `_build_decision_tree` into a shared helper that both `semantic.py` and `lower.py` call. This is the cleaner design but requires more file surgery. DESIGN.md should pick one.
- [ ] Detect unreachable arms: an arm whose pattern row is "dominated" by an earlier row produces a warning via `_warning` (not an error — unreachable arms are a code smell, not a bug).

### Phase 1.6: MIR TagSwitch (if needed)

- [ ] `mapanare/mir.py` — if the decision-tree emission needs a `TagSwitch` MIR instruction kind that doesn't exist yet, add it. Most likely it already exists (match lowering has been there since v1.x) but may need extension for the "default arm" case.
- [ ] `MIRVerifier` (in the same file) — if `TagSwitch` was extended, update the verifier to accept the new shape.

### Phase 1.7: LLVM emitter update (if needed)

- [ ] `mapanare/emit_llvm_text.py` — if `TagSwitch` was extended, update the emission rule. Most likely existing emission already handles "switch with default" since that's LLVM's default for `switch` instructions.
- [ ] **Goal: zero functional change in emit_llvm_text.py for v4.34.0.** The rewrite is at the MIR level; the emitter just sees cleaner MIR. If this goal is violated, the scope has expanded and we slow down.

---

## Phase 2 — Self-hosted mirror

> **The byte-identity invariant is the hardest part of this release.**
> If the two implementations drift apart at any level (block ordering,
> instruction ordering, witness construction), the 69-line stage2/
> stage3 diff doesn't close.

### Phase 2.1: Pattern matrix data structure in self-hosted

- [ ] `mapanare/self/lower.mn` (or a new file `mapanare/self/match_compile.mn` if the match logic deserves its own module — DESIGN.md should pick) — define the Mapanare equivalents of `PatternRow`, `PatternMatrix`, `DecisionTree` as struct + enum types.
- [ ] Constructor functions following the project convention (`new_pattern_row`, `new_pattern_matrix`, `new_decision_tree_leaf`, etc.).
- [ ] Helper functions mirroring the Python side exactly: `specialize_matrix(matrix, col, ctor)`, `default_matrix(matrix, col)`, `select_column(matrix)`, etc.

### Phase 2.2: Decision-tree builder in self-hosted

- [ ] Mirror `_build_decision_tree` with `build_decision_tree(matrix, state)`. Same heuristics, same deterministic tiebreak, same output shape.
- [ ] The column-selection heuristic must produce the **same result** as the Python version on equivalent inputs. If there's any tiebreak ambiguity, lock it down in DESIGN.md so both implementations do the same thing.

### Phase 2.3: Decision-tree emitter in self-hosted

- [ ] Mirror `_emit_decision_tree` with `emit_decision_tree(tree, matrix, merge_block, state)`. Same block naming (`match_<N>_case_<tag>` / `match_<N>_default`), same MIR instruction order.
- [ ] **Byte-identity checkpoint:** after this phase lands, regenerate `mnc_all.mn`, build `mnc-stage1`, compile `mnc_all.mn` through `mnc-stage1` to produce `stage2.ll`, compile `mnc_all.mn` through `mnc-stage2` to produce `stage3.ll`, diff. **Target: 0 lines of diff** (A6 closed).

### Phase 2.4: Exhaustiveness checking in self-hosted semantic

- [ ] `mapanare/self/semantic.mn` — add `check_match_exhaustive(node, state)`. Mirror the Python implementation.
- [ ] This depends on the self-hosted semantic being wired into `self/main.mn:compile()`. **Today (v4.33.0) it is NOT.** A7 is scheduled for v4.52.0. So v4.34.0's self-hosted exhaustiveness check exists but is not invoked at compile time until v4.52.0 wires the semantic pass. That's acceptable — the Python side catches the errors for users at compile time; the self-hosted side is ready for when A7 lands.

### Phase 2.5: Rebuild + validate byte-identity

- [ ] `python scripts/build_stage1.py` — rebuild
- [ ] `python scripts/test_native.py --stage1 mapanare/self/mnc-stage1` — all 45 golden tests still pass
- [ ] `bash scripts/verify_fixed_point.sh` — **target: 0 lines of diff** (down from 69 at v4.33.0)
- [ ] If the diff is not zero, the byte-identity invariant was violated somewhere. Use `culebra diff stage2.ll stage3.ll` to find which function diverges; use `culebra extract` to pull the offending function from both files; read them side-by-side; fix the divergence.
- [ ] This phase is iterative. Plan for 2–4 diff-fix cycles before convergence.

---

## Phase 3 — Exhaustiveness upgrade (compile-time errors)

### Phase 3.1: New `tests/semantic/test_match_exhaustive.py`

Positive and negative cases:

- [ ] `test_option_some_none_exhaustive` — `match opt { Some(x) => ..., None => ... }` — passes
- [ ] `test_option_only_some_is_error` — `match opt { Some(x) => ... }` — errors with "pattern `None` is not covered"
- [ ] `test_result_ok_err_exhaustive`
- [ ] `test_result_only_ok_is_error` — errors with "pattern `Err(_)` is not covered"
- [ ] `test_enum_all_variants_exhaustive` — user-defined enum with 3 variants, all covered
- [ ] `test_enum_missing_variant_is_error` — errors with the missing variant name
- [ ] `test_enum_wildcard_catchall_exhaustive` — `case _` covers everything
- [ ] `test_nested_pattern_exhaustive` — `Some(Ok(x))`, `Some(Err(e))`, `None` — the cross-product of Option × Result
- [ ] `test_nested_pattern_missing_is_error` — `Some(Ok(x))`, `None` — missing `Some(Err(_))`
- [ ] `test_int_match_without_default_is_error` — integer match without a default arm
- [ ] `test_string_match_without_default_is_error`
- [ ] `test_unreachable_arm_is_warning` — `Some(x), Some(42) => ...` — second arm is unreachable, warning fires
- [ ] `test_exhaustive_message_names_witness` — verify the error message contains the witness pattern name
- [ ] `test_exhaustive_message_includes_suggestion` — verify the suggestion text

### Phase 3.2: Diagnostic quality

- [ ] Run the negative cases by hand and visually inspect the error output. The rendered diagnostic should look like:

  ```
  error: non-exhaustive match: pattern `Err(_)` is not covered
    --> src/foo.mn:12:5
     |
  12 |     match result {
     |     ^^^^^^^^^^^^^^
  13 |         Ok(x) => x + 1,
     |
     = help: add a `case Err(_) => ...` arm, or use `case _ => ...` to match all remaining cases
  ```

- [ ] If the rendered output is not rustc-quality, iterate on the diagnostic rendering before merging.

### Phase 3.3: Cookbook + SPEC

- [ ] `docs/cookbook.md` §Pattern Matching — add "Exhaustiveness" subsection with the error-quality example.
- [ ] `docs/SPEC.md` §Pattern Matching — update to state that non-exhaustive matches are compile errors, not warnings. Document the "default arm required for open types" rule.
- [ ] `docs/SPEC.md` — document the v4.34.0 decision-tree lowering as the canonical shape. This is valuable historical record: the reviewer at v5.1.0 can read it and understand why the IR is the way it is.

---

## Phase 4 — Golden test refresh

### Phase 4.1: Existing match golden tests

The existing golden tests that exercise `match` will produce different IR under the new lowering. Options:

**Option A: regenerate reference IR for every affected test.**
- [ ] Run `python scripts/test_native.py --bless` (or equivalent) to regenerate reference `.ref.ll` files.
- [ ] Manually inspect each diff: does the new IR look cleaner (fewer blocks, clearer flow)? If yes, commit. If no, the decision-tree lowering has a bug; investigate.
- [ ] Affected tests (grep `tests/golden/*.mn` for `match`):
  - `tests/golden/07_enum_match.mn`
  - `tests/golden/10_result.mn`
  - `tests/golden/32_generic_enum.mn`
  - Any test that uses `Option` / `Result`
  - `tests/golden/47_try_operator.mn` (v4.33.0's new test — `?` desugars to match, so its IR changes too)

**Option B: keep reference IR, verify new lowering produces equivalent IR.**
- Unrealistic — the whole point of the rewrite is to produce different (cleaner) IR. Option A is correct.

### Phase 4.2: New match test

- [ ] `tests/golden/48_match_nested_exhaustive.mn` — deliberately exercises nested patterns: `Option<Result<T, E>>` with all 3 combinations (Some(Ok), Some(Err), None). Verifies the new lowering handles nested constructor specialization correctly.

### Phase 4.3: Benchmark comparison

- [ ] `benchmarks/run_all.py` — if there's a benchmark that times match-heavy code, run it before and after. The new decision-tree lowering should produce faster code (fewer branches per case).
- [ ] Record the comparison in the SESSION_REPORT.

---

## Phase 5 — LOW item sweep

v4.33.0 swept 3 LOW items. v4.34.0 sweeps 3 more from the v4.31.0 panel tail.

### Phase 5.1: `MN_PROFILE_FREE` never called (6th cycle, Viper)

- [ ] `runtime/native/mapanare_core.c:72-74` defines the macro. `__mn_free` at ~line 103-105 does NOT call it. Result: `mn_alloc_live` is monotonic — it counts total bytes ever allocated, not currently-live bytes. The counter's name is a lie.
- [ ] Fix: call `MN_PROFILE_FREE(size)` inside `__mn_free` before the actual free.
- [ ] Verify: run a program that allocates and frees in a loop; `mn_alloc_live` should stay flat, not grow monotonically.

### Phase 5.2: `__mn_read_line` 4KB stack truncation (6th cycle, Viper)

- [ ] `runtime/native/mapanare_core.c:1372-1379` — `fgets` into a `buf[4096]` stack buffer. Any input line longer than 4095 bytes is silently truncated.
- [ ] Fix: use `getline(3)` on POSIX (POSIX.1-2008; dynamic allocation; reads arbitrarily long lines). On Windows, loop `fgets` calls until the last character is `\n` or EOF, accumulating into a growing buffer.
- [ ] Test: `tests/runtime/test_read_line_long_input.py` — pipe a 10KB line to the program via stdin, verify it's read intact.

### Phase 5.3: Arena allocator thread safety

- [ ] `runtime/native/mapanare_core.c:203-221` — `mn_arena_alloc` does `blk->used += size` non-atomically. The arena is not thread-safe, and this has been an open v4.0.0 audit item.
- [ ] Fix: add a mutex to the arena block. Lock around `blk->used` updates. Or: use atomic `__sync_fetch_and_add` / `InterlockedExchangeAdd` on the `used` field.
- [ ] Test: `tests/runtime/tsan/arena_stress.c` — 8 threads, each allocating small chunks from a shared arena, 10k iterations. TSan clean.

---

## Phase 6 — Verification

### Phase 6.1: Full validation

- [ ] `black --check .` — clean
- [ ] `ruff check .` — clean
- [ ] `mypy mapanare/ runtime/` — clean
- [ ] `pytest tests/ -n auto` — all passing (including the new exhaustiveness tests and the regenerated goldens)
- [ ] `python scripts/test_native.py --stage1 mapanare/self/mnc-stage1` — 46/46 golden (45 from v4.33.0 + 1 new `48_match_nested_exhaustive.mn`)
- [ ] `python scripts/ir_doctor.py stage2` — 11/11 stage2 modules valid
- [ ] `bash scripts/verify_fixed_point.sh` — **target: 0 lines of diff** (closing A6)
- [ ] If the diff is still > 0, the byte-identity invariant was violated. Do NOT ship until it's zero. The whole point of this release is the convergence.

### Phase 6.2: A6 closure evidence

- [ ] `.reviews/CARRY_FORWARD.md` A6 row marked CLOSED with evidence: "Maranget decision-tree rewrite in both pipelines; stage2/stage3 diff now 0 lines."
- [ ] Cross-link from v4.34.0 SESSION_REPORT to the relevant lines in `verify_fixed_point.sh` output.

### Phase 6.3: Exhaustiveness quality

- [ ] Visual inspection of 5 representative negative cases. All 5 produce rustc-quality diagnostics with witness + suggestion.
- [ ] Count of exhaustiveness-related errors in the self-hosted test corpus: compile all 46 goldens through the semantic checker; expect 0 new errors (none of the existing goldens should have been relying on incomplete exhaustiveness).
- [ ] If any existing golden fails exhaustiveness checking, that's a bug in the test: fix it (add the missing arm) before merging.

### Phase 6.4: Fact-check against DESIGN.md

- [ ] Re-read DESIGN.md end-to-end. Every decision made in the document is reflected in the code. Any implementation deviation is documented in SESSION_REPORT.
- [ ] Specific checkpoints:
  - Block naming discipline: `match_<N>_case_<tag>` / `match_<N>_default` — verify via grep in emitted IR
  - Column selection heuristic: trace one example through both Python and self-hosted implementations and confirm they pick the same column
  - Witness construction: verify the witness in a non-exhaustive error is the minimal pattern that would have matched

---

## Phase 7 — Closeout

- [ ] `VERSION` — bump `4.33.0` → `4.34.0`
- [ ] `CHANGELOG.md` — new `[4.34.0]` entry. Every backticked path must resolve. Every test name must exist. Honesty CI clean.
- [ ] `docs/roadmap/v4/v4.34.0/SESSION_REPORT.md` — written, with:
  - Phase 0 DESIGN.md summary and the informal-review outcome
  - Phase 1 Python rewrite (line counts, helper introductions)
  - Phase 2 self-hosted mirror (byte-identity convergence narrative)
  - Phase 3 exhaustiveness upgrade
  - Phase 4 golden test refresh (which tests had IR regenerated, which got new tests)
  - Phase 5 LOW sweep
  - Phase 6 verification
  - Fixed-point diff number (target 0)
  - Any decisions that deviated from DESIGN.md with rationale
- [ ] `docs/roadmap/ROADMAP.md` — v4.34.0 row added
- [ ] `docs/roadmap/v4/README.md` — v4.34.0 row added
- [ ] `.reviews/CARRY_FORWARD.md` — A6 CLOSED, 3 LOW rows from Phase 5 CLOSED

---

## Exit criteria (20 items)

| # | Check | Evidence |
|---|---|---|
| 1 | `DESIGN.md` written and reviewed by Cobra + Rattler before code | `docs/roadmap/v4/v4.34.0/DESIGN.md` exists + two sign-off lines at the bottom |
| 2 | Pattern matrix + decision tree data structures in `mapanare/lower.py` | grep finds `PatternMatrix`, `DecisionTree`, `Switch`, `Leaf`, `Fail` |
| 3 | `_build_decision_tree` implemented with Maranget's algorithm | grep finds the method + unit tests cover it |
| 4 | `_emit_decision_tree` produces deterministic block naming | verified by inspecting emitted IR |
| 5 | `_lower_match` replaced wholesale; old helpers deleted | `git diff` shows net line reduction in `lower.py` |
| 6 | Self-hosted pattern matrix + decision tree in `self/lower.mn` | grep finds mirror types in `.mn` files |
| 7 | Self-hosted decision-tree builder produces same result as Python | byte-identity at fixed-point |
| 8 | Self-hosted emitter uses same block-naming discipline | `diff stage2.ll stage3.ll` returns 0 lines |
| 9 | **Fixed-point diff is 0 lines** (A6 closed) | `verify_fixed_point.sh` output |
| 10 | Exhaustiveness errors fire at compile time, not lowering time | `tests/semantic/test_match_exhaustive.py` — all 13 cases pass |
| 11 | Exhaustiveness error diagnostics are rustc-quality (witness + suggestion) | visual inspection + `test_exhaustive_message_names_witness` |
| 12 | Unreachable arm detection fires as a warning (not silent) | `tests/semantic/test_match_exhaustive.py::test_unreachable_arm_is_warning` |
| 13 | All 45 existing golden tests still pass (new IR, same behavior) | `test_native.py --stage1` returns 46/46 (new one + existing) |
| 14 | New `48_match_nested_exhaustive.mn` golden test added | file exists + passes |
| 15 | LOW: `MN_PROFILE_FREE` wired; regression test | Phase 5.1 evidence |
| 16 | LOW: `__mn_read_line` reads arbitrary-length lines | Phase 5.2 evidence |
| 17 | LOW: Arena allocator TSan-clean | Phase 5.3 evidence |
| 18 | A6 marked CLOSED in `CARRY_FORWARD.md` | manual diff review |
| 19 | 3 LOW rows marked CLOSED in `CARRY_FORWARD.md` | manual diff review |
| 20 | SESSION_REPORT.md written with honest fact-checkable claims | file exists |

---

## What v4.34.0 explicitly does NOT do

- **Match guards** (`case Some(x) if x > 0 => ...`) — v4.35.0
- **Or-patterns** (`case A | B => ...`) — v4.35.0
- **Range patterns** (`case 1..10 => ...`) — v5.x backlog
- **Pattern bindings** (`case x @ Some(42) => ...`) — v5.x backlog
- **Active patterns** (F#-style) — v5.x backlog, probably not
- **Match as an expression in binding position** (`let x: Int = match foo { ... }`) — it should already work (MatchExpr is an expression in the AST), but v4.34.0 doesn't change its semantics. If it doesn't work today, it's a separate bug, not a v4.34.0 scope item.
- **Dual-path lowering** where the old lowerer stays as a fallback — no. The rewrite is wholesale. Either it works end-to-end or it doesn't ship.
- **Any changes to `?` operator behavior** — `?` desugars to match, so v4.34.0's rewrite automatically applies. v4.33.0 and v4.34.0 together produce the first consistent match + try experience.

---

## Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| The byte-identity invariant is hard to hit — two implementations drift apart during the rewrite | **high** | high | DESIGN.md is Phase 0 on purpose; the invariant is spelled out in the design doc; iteration on diff-fix cycles is planned; Culebra `diff` helps isolate divergences |
| Maranget's algorithm has edge cases we miss | medium | medium | Rust's chalk / rustc has published their implementation; reference it for edge cases; if a case is missed, a golden test will fire |
| The exhaustiveness error witness construction produces confusing witnesses | medium | low | Visual-inspection phase (Phase 3.2); if the witnesses look bad, iterate before merging |
| Existing golden tests had incomplete patterns that the new exhaustiveness checker catches as errors | medium | low | Expected at Phase 4.1 — fix the goldens (add the missing arms) before merging. This is a win, not a regression |
| The self-hosted implementation cascades into a rewrite bigger than one sprint | medium | medium | The scope is bounded by the DESIGN.md; if it cascades, split: v4.34.0 ships the Python rewrite only, and v4.34.1 (point release) ships the self-hosted mirror. A6 closure slips to v4.34.1. |
| Non-exhaustive match was accepted as a warning in user programs; users get errors after upgrade | low | low | The CHANGELOG v4.34.0 entry calls this out as a semver-minor breaking change (users of broken code get errors). Document the migration: "add a `_ => ...` default arm or the specific missing cases." Rust and Swift had the same migration; it was fine. |
| Unreachable-arm warnings fire on code that was legitimately defensive (e.g., matching a sentinel value that "shouldn't happen") | low | low | Allow suppression via `#[allow_unreachable_arms]` attribute or similar; or just leave the warning because it's correct |

---

## Reference

- Maranget, Luc. "Compiling Pattern Matching to Good Decision Trees." *ML '08: Proceedings of the 2008 ACM SIGPLAN Workshop on ML.* https://doi.org/10.1145/1411304.1411311
- Rust RFC 0107: "pattern matching design" — https://github.com/rust-lang/rfcs/blob/master/text/0107-pattern-guards-with-bind-by-move.md (and follow-ups)
- OCaml compiler `matching.ml` — https://github.com/ocaml/ocaml/blob/trunk/lambda/matching.ml (reference implementation, ~4000 lines — don't copy line-for-line, but read it)
- [`docs/roadmap/v4/POST_RECOVERY_ROADMAP.md`](../POST_RECOVERY_ROADMAP.md) §Arc 1 — the roadmap context
- [`.reviews/CARRY_FORWARD.md`](../../../../.reviews/CARRY_FORWARD.md) A6 — the carry-forward this release closes
- [`v4.33.0/PLAN.md`](../v4.33.0/PLAN.md) — the `?` operator release, which v4.34.0's match rewrite indirectly improves

---

## After v4.34.0

v4.35.0 opens with match guards + or-patterns — new syntax, delta review mandatory. Both features build directly on v4.34.0's decision-tree infrastructure. v4.35.0 is the natural extension of the match rewrite: v4.34.0 made match correct and consistent; v4.35.0 makes it expressive.

See [`docs/roadmap/v4/v4.35.0/PLAN.md`](../v4.35.0/PLAN.md).
