# Coral — Language Design Review (Arc 10)

**Grade: 9/10**
**Verdict: PASS**

## Assessment

Arc 10 is infrastructure and debt, not features. This is the right call. The language is feature-complete through v4.76.0 (async/await, DWARF, tensors, AI stdlib). What it needed was the testing infrastructure to protect those features from regression, the documentation to make them accessible, and the discipline to close every open item on the carry-forward ledger.

**SPEC Futures section (29):** The formal semantics are accurate and well-structured. The 7 subsections cover declaration, suspension, type representation, synchronous driver, lifecycle, memory model, and primitive interactions. The `Future<T> = {i8, ptr}` representation is clearly explained with its rationale (uniform size, handle reuse). The `block_on` semantics correctly document the deadlock risk when called from async code.

**Carry-forward ledger:** I walked every row. All items marked CLOSED have evidence pointers. The two remaining OPEN items (A5 Culebra-external, A10 accepted grammar gap) are correctly classified as non-Mapanare-owned. This is the first time in project history the ledger shows 0 owned open items.

**Cookbook approach:** Tutorial-first is the right choice. The 7 sections build progressively from basic async fn through fan-out and pitfalls. The examples match the golden tests (55-57), establishing a link between documentation and test evidence.

## Specific findings

1. **PASS**: SPEC section 29 cross-references the Coroutine Design Document correctly.
2. **PASS**: Appendix C correctly updated — `async`/`await` moved from reserved to real keywords.
3. **PASS**: Carry-forward ledger is genuinely at zero. No item was closed without evidence.
4. **NOTE**: The cookbook note about async examples requiring `mnc run` rather than `emit-llvm` is honest and necessary.

## Score justification

9/10 — the SPEC section is normatively correct, the ledger is genuinely clean, and the documentation fills the gap Boa has flagged for 6 panels. Best infrastructure arc in the project.
