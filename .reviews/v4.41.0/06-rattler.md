# Rattler -- LLVM Review of Mapanare v4.41.0 (Arc 2 Panel)
**Reviewer:** Rattler
**Personality:** The LLVM Wizard -- insufferably smart, patronizing, advice is gold
**Previous Version Reviewed:** v4.36.0 (Arc 1, PASS, 9.40/10)
**Arc Reviewed:** v4.37.0 -> v4.40.0 (Arc 2 -- LSP/editor tooling, zero codegen changes)
**Verdict:** PASS
**Confidence:** 10/10
**Score:** 9.40/10 (unchanged)

**Files Reviewed (evidence-checked):**

- `mapanare/lsp/diagnostics.py` (115 lines -- `run_semantic_check`, `semantic_error_to_diagnostic`, `parse_error_to_diagnostic`)
- `mapanare/lsp/server.py` (691 lines -- full server, `_analyze_and_publish`, `_run_and_publish_semantic_diagnostics`, debounced recheck)
- `mapanare/lsp/analysis.py` (top 80 lines -- imports from `mapanare.semantic` and `mapanare.ast_nodes`)
- `mapanare/self/lower.mn:3411-3425` (guard fall-through -- unchanged from v4.36.0)
- `mapanare/self/emit_llvm.mn:528` (`i64*` -- unchanged)
- `mapanare/self/emit_llvm.mn:949` (`void ()*` -- unchanged)
- `.reviews/CARRY_FORWARD.md` (P3, items 30-31 status)
- `CHANGELOG.md` sections `[4.37.0]` through `[4.41.0]`
- `git log` of codegen files since v4.36.0 (zero commits)

---

## Executive Summary

This is the easiest review I have ever written for Mapanare. Arc 2 is an LSP-only arc: four releases (v4.37.0 through v4.40.0) delivering workspace indexing, cross-module go-to-def, find-references, rename refactoring, context-aware completion, diagnostic streaming, and VS Code extension polish. v4.41.0 is the panel release with zero new features.

**Zero lines of LLVM codegen were touched.** The git log for `emit_llvm_text.py`, `lower.py`, `mir.py`, `pattern_matching.py`, `emit_llvm.mn`, `emit_llvm_ir.mn`, and `lower.mn` shows no commits between v4.36.0 and HEAD. My job here is to grade non-regression and verify one structural question: does the LSP's semantic check integration reuse the compiler's checker, or does it fork?

**Answer: no divergence.** The LSP calls the exact same functions the compiler does:

- `mapanare/lsp/diagnostics.py:96-98` imports `from mapanare.parser import parse` and calls `parse(source, filename=uri)`
- `mapanare/lsp/diagnostics.py:106-109` imports `from mapanare.semantic import check` and calls `check(program, filename=uri)`
- `mapanare/lsp/analysis.py:61-66` imports `SemanticError`, `BUILTIN_FUNCTIONS`, `BUILTIN_GENERIC_TYPES`, `PRIMITIVE_TYPES` from `mapanare.semantic`
- `mapanare/lsp/analysis.py:216,241,1269-1270` also import `parse` and `check` for within-file analysis paths

These are the same `parse()` and `check()` used by `mapanare/cli.py:360`. One parser, one semantic checker, two consumers. The LSP is a thin adapter that converts `SemanticError` objects (with 1-based line/column) to LSP `Diagnostic` objects (with 0-based line/column). The conversion at `diagnostics.py:24-29` is correct and handles the edge cases (missing end_line defaults to start line, missing end_col defaults to col+1).

The `_analyze_and_publish` path in `server.py` runs a lighter AST-walk-based analysis (for hover, completion, go-to-def) and emits its own diagnostic objects from that walk. The `_run_and_publish_semantic_diagnostics` path runs the full `parse` + `check` pipeline. Both paths publish to the same diagnostic endpoint. On save, both run. On change, the lighter analysis runs immediately and the heavier semantic check runs after a 300ms debounce. This is a reasonable architecture -- the two paths are complementary, not competing.

---

## Carry-Forward Status

### P3 -- Self-hosted guard fall-through divergence

**Status: OPEN (2nd cycle)**

Still at `mapanare/self/lower.mn:3418-3425`:
```mapanare
// Guard fail: jump to next arm or merge
s = add_block(s, fail_label)
if ai + 1 < na_match {
    let next_label: String = arm_labels[ai + 1]
    s = emit_instr(s, Instruction::Jump(next_label))
} else {
    s = emit_instr(s, Instruction::Jump(merge_label))
}
```

Unchanged. The self-hosted lowerer still jumps to the next arm's action block on guard failure instead of rebuilding a decision tree from remaining arms. This is latent for the current test corpus but incorrect for mixed-variant guard scenarios. I recommended a ~20-line fix at v4.36.0. It was tracked to v4.37.0 in the carry-forward ledger but not addressed -- understandable given Arc 2's LSP-only scope.

I am not docking score for this because (a) the arc explicitly declared zero codegen changes, and (b) the item is tracked. But it is now at its 2nd cycle and should not reach a 3rd.

### Items 30-31 -- Opaque pointer cosmetic debt (`i64*`, `void ()*`)

**Status: EVERGREEN (moved to no-score-impact tracking)**

Still at `emit_llvm.mn:528` and `emit_llvm.mn:949`, unchanged for 12 cycles. As stated in my v4.36.0 review, I am no longer docking score for these. They are cosmetic: LLVM 15+ parses typed pointers as opaque `ptr`, no live call sites are affected, and `llvm-as` validation passes. Two one-line fixes whenever someone happens to be in those files.

---

## Verification: LSP Semantic Check Divergence Risk

The one structural question for this arc: could the LSP introduce a semantic check divergence where the editor shows different errors than `mapanare check`?

**Answer: No.** Both paths call `mapanare.semantic.check()` -- the same function, the same module, the same type checker. There is no forked or reimplemented checker in the LSP. The only difference is error presentation:

- The compiler (`cli.py`) calls `check_or_raise()` which raises on the first error
- The LSP (`diagnostics.py`) calls `check()` which returns a list of all errors

This is a correct boundary design: the LSP wants all errors for red-squiggle display; the compiler wants fail-fast for CLI UX. The underlying check logic is identical.

One minor observation: the `run_semantic_check` function at `diagnostics.py:112` has a bare `except Exception: pass` on semantic check crashes. This means if the semantic checker itself crashes (as opposed to returning errors), the LSP silently swallows the exception and returns only parse-level diagnostics. This is a reasonable defensive choice for an editor extension -- a crash in the checker should not block the user from seeing parse errors. But it does mean that a checker regression could go unnoticed in the LSP path if it manifests as a crash rather than incorrect error output. Not actionable, just noted.

---

## Score Rationale

| Factor | Assessment |
|--------|-----------|
| Codegen regression | None. Zero commits to codegen files. |
| LSP/checker divergence | None. Same `parse()` + `check()` functions. |
| P3 guard divergence | Still open, 2nd cycle. Not docking (zero-codegen arc). |
| Items 30-31 opaque pointers | Evergreen. No score impact. |
| New LLVM issues introduced | None. |

The score stays at **9.40/10**. There is nothing to add and nothing to subtract. The 0.60 gap from 10.0 is entirely P3 (the self-hosted guard fall-through divergence). When P3 closes, I will move to 9.6 or higher depending on the quality of the fix.

---

## Issues Found

None new. All items from v4.36.0 remain in their tracked state.

---

## Recommendations

1. **Close P3 in the next codegen-touching release.** The fix is ~20 lines in `lower.mn`. It has been on my ledger for two cycles. A third would be disappointing.
2. **Items 30-31 are officially cosmetic evergreens.** Fix them opportunistically; I will not mention them again unless they cause a real problem.
