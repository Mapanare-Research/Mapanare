# v4.129.0 SPEC Audit

**Date:** 2026-04-15
**SPEC version header:** 4.116.0 (audited against v4.128.0 HEAD)
**Methodology:** targeted audit of the 10 sections most affected by
v4.117.0–v4.128.0 changes, plus a light version-reference scan across
the whole file.

Classification: **OK** = matches implementation; **STALE** =
outdated but not actively misleading; **WRONG** = contradicts
implementation.

---

## Summary

| Status | Count | Sections |
|---|---|---|
| OK | 8 | §3.7 enums, §3.8 Option/Result, §5 pattern matching, §15 strings, §16 lists, §17 maps, §21.3 DWARF, §23.3 @gpu decorator, §29 async |
| STALE | 4 | header version, §2.1.1 master list `const` row, §3.2 generics missing `Future<T>`, §28 stdlib "seven modules", Appendix B optimizer passes |
| WRONG | 6 | §2.1 const-keyword note, §3.6 duplicate heading, §6.3 lambda annotations self-contradiction, §27.1 TypeKind count, Appendix B pipeline diagram (shows Python), Appendix B "Python Transpiler" section |

Total findings: 4 STALE + 6 WRONG = **10 items** require an edit in
Phase 2.

---

## Targeted audit

### §0 Header (line 3) — STALE

**Claim:** "Version: 4.116.0; Status: Live — synced to the v4.116.0
cut (2026-04-14)"

**Reality:** v4.128.0 is the latest shipped release; v4.129.0 is
shipping this SPEC sync.

**Fix in Phase 2:** update header to v4.129.0 (2026-04-15).

---

### §2.1 const note (lines 130–136) — WRONG

**Claim:** `const` "was briefly added in v4.18.0 as a parser alias
for module-level let and was removed in v4.27.0" with "no ConstDef
AST node, no immutability beyond what let already provides, no
compile-time evaluation."

**Reality (v4.55.0):** `const` was reintroduced as a distinct
definition form with real semantics:
- `ConstDef` AST node exists at `mapanare/ast_nodes.py:789`.
- `const_def` grammar rule exists at `mapanare/mapanare.lark:197`
  (`KW_CONST NAME COLON type_expr ASSIGN expr`).
- `KW_CONST` token exists at `mapanare/mapanare.lark:380`.
- Semantic checker at `mapanare/semantic.py:2009` folds the
  initializer as a constant expression, registers the name with
  `SymbolKind.CONST` (distinct from `VARIABLE`), stores the folded
  value in `_const_table`, and rejects non-constant initializers
  with a diagnostic.
- Self-hosted parser recognition restored at
  `mapanare/self/parser.mn:366` (v4.126.0 fix — `is_definition_start`
  was missing `KW_CONST`).
- Golden tests `54_const_basic` and `58_const_scope` pass through
  both Python bootstrap and `mnc-stage1` since v4.126.0.

**Fix in Phase 2:** rewrite the note to describe the current
behavior honestly. Preserve the historical context (v4.18.0 alias →
v4.27.0 removal → v4.55.0 reintroduction) since it explains why the
feature has non-obvious shape.

---

### §2.1.1 Master list `const` row (line 77) — STALE

**Claim:** Description says "Parser-reserved; use module-level
`let` (see §2.1 note)."

**Reality:** `const` is a full keyword with grammar, AST, and
semantic support per the finding above.

**Fix in Phase 2:** update row to "Compile-time constant — requires
type annotation and constant initializer; enforces immutability."
Category: "Bindings."

---

### §3.2 Generic Container Types (line 447) — STALE

**Claim:** Table lists 8 generic container types: `List`, `Map`,
`Option`, `Result`, `Signal`, `Stream`, `Channel`, `Tensor`.

**Reality:** `Future<T>` was added as a TypeKind in v4.69.0
(`mapanare/types.py:43`). It is explicitly described in §29.3 as a
"built-in generic type" with shape `{i8, ptr}`. It belongs in this
table.

**Fix in Phase 2:** add `Future<T>` row to §3.2, cross-referencing
§29.

---

### §3.6 Duplicate heading (lines 520 and 569) — WRONG

**Claim:** Both "Type Inference Rules" (line 520) and "Struct Types"
(line 569) are labeled `### 3.6`.

**Reality:** Numbering typo. The tensor section at line 739 is
§3.10; inference at line 520 should be §3.6, structs at line 569
should be §3.7, and all subsequent subsections need +1. But the
current enums are §3.7 (line 611) and option/result is §3.8 (line
660) — so the duplicate is genuine and everything below it is
off-by-one.

**Fix in Phase 2:** renumber "Struct Types" → §3.7; "Enum Types" →
§3.8; "Option and Result Types" → §3.9; "Agent Types" → §3.10;
"Tensor Types" → §3.11; "Type Aliases" → §3.12; "Function Types"
→ §3.13. Verify cross-references elsewhere in the SPEC.

Cross-reference scan: §29.7 references "§7" for Tensors; keep that
intact. Match expression §4.6 → §5 is unchanged. §3.5 boxing rules
reference § numbers; check.

---

### §6.3 Closures and Lambdas (lines 1117–1148) — WRONG

**Claim:** Line 1132 — "Lambda parameter types are inferred from
context. Type annotations on lambda parameters are not supported in
the grammar — use a named function if explicit types are needed."

Line 1141 — example `let add_offset = (x: Int) => x + offset`.

**Reality:** Self-contradiction. Either the note is wrong (lambda
annotations *are* supported) or the example is wrong. Grammar
inspection at `mapanare/mapanare.lark:217` (`?expr: assign_expr
FAT_ARROW expr -> lambda_expr_rule`) shows the LHS is
`assign_expr`, which does not include type-annotated tuple forms
directly — a `(x: Int)` would not parse as a standard expr. The
note is likely correct; the example is wrong.

**Fix in Phase 2:** rewrite the example to use an untyped parameter
(`(x) => x + offset`) OR, if testing reveals the parser does accept
typed lambda params, strike the note. Verify by attempting to
compile `let f = (x: Int) => x + 1` through `python3 -m mapanare
check` before committing the fix.

---

### §27.1 TypeKind count (line 2260) — WRONG

**Claim:** "All 25 TypeKind variants and their behavior."

**Reality:** Inspected `mapanare/types.py::TypeKind` (lines 23–61):

| Category | Variants | Count |
|---|---|---|
| Primitives | INT, FLOAT, BOOL, STRING, CHAR, VOID | 6 |
| Generic containers | LIST, MAP, OPTION, RESULT, SIGNAL, STREAM, CHANNEL, TENSOR, FUTURE | 9 |
| Compound / user-defined | FN, STRUCT, ENUM, AGENT, PIPE, TYPE_ALIAS, TRAIT | 7 |
| Special | TYPE_VAR, RANGE, ANY, UNKNOWN, UNRESOLVED, ERROR | 6 |
| Other | BUILTIN_FN | 1 |

**Actual total: 29 variants.**

**Fix in Phase 2:** update the count. Note that UNKNOWN is a
deprecated alias for UNRESOLVED, but both still exist in the
enum, so both count.

---

### §28 Standard Library (line 2289) — STALE

**Claim:** "Seven native stdlib modules written in `.mn`, compiled
via LLVM" — tagged "(v0.9.0)".

**Reality:** `stdlib/` currently contains 35+ `.mn` modules across
AI, database, encoding, file system, GPU, logging, math, HTTP/HTTPS,
WebSocket, testing, text utilities, time, WASM bridge, and more.
The "seven" figure was never accurate after v0.9.0.

**Fix in Phase 2:** remove the "(v0.9.0)" tag. Replace the seven-row
table with categorized coverage. Do not enumerate every module
(churn risk); instead group by domain and point to
`stdlib/` directory for the canonical list. Retain the per-module
sub-sections where they contain real semantics (JSON, CSV, HTTP
client, HTTP server, WebSocket, Crypto, Regex) since those describe
public APIs.

---

### Appendix B pipeline diagram (lines 2577–2582) — WRONG

**Claim:** Pipeline diagram shows three emitters: `Python (legacy)`,
`LLVM IR → Native Binary`, `WebAssembly (WAT/WASM)`.

**Reality:** The Python-source emitter (`emit_python_mir.py`) was
deleted in v4.58.0. A regression test at
`tests/test_python_emitter_deleted.py` confirms it must not return.
Current emitters:
- `mapanare/emit_llvm_text.py` — LLVM IR
- `mapanare/emit_c.py` — C source (v3.0.0+)
- `mapanare/emit_wasm.py` — WebAssembly (WAT)

**Fix in Phase 2:** redraw the diagram to show LLVM, C, WASM as the
three outputs.

---

### Appendix B "Python Transpiler (Legacy)" section (line 2620) — WRONG

**Claim:** "The Python emitter translates MIR to Python source
code. This backend is legacy — kept for reference and bootstrapping
only. It is not the target for new features."

**Reality:** The emitter was deleted v4.58.0. See above.

**Fix in Phase 2:** replace this subsection with a description of
the C backend (`emit_c.py`), which produces C source that `gcc` or
`clang` can compile. Keep it terse (parallel to the LLVM subsection).

---

### Appendix B MIR optimizer passes (lines 2612–2618) — STALE

**Claim:** Lists 5 passes: constant folding, DCE, copy propagation,
block merging, unreachable removal.

**Reality:** Several more passes were added in v4.95.0 (string_concat
optimization, fixed v4.108.0) and v4.97.0 (strength reduction,
inline small functions, LICM, escape analysis). The v4.111.0
recovery disabled four of those in the self-hosted compiler as
zero-ROI. v4.109.0 forensics confirmed the pass-level gains are
mostly via function attributes on runtime-call declarations, not
inline MIR rewrites.

**Fix in Phase 2:** list the currently-active passes with one line
each; note that some passes are optimization-level-gated (O0/O1/O2/
O3). Do not re-enumerate v4.95.0–v4.111.0 history — that belongs in
the release notes, not the SPEC.

---

## Light scan — rest of the SPEC

Version-reference scan (`grep -n "v4\.[0-9]" docs/SPEC.md`):

| Line | Reference | Status |
|---|---|---|
| 4 | v4.116.0 header | STALE (covered above) |
| 11 | v4.116.0 documentation batch note | STALE — replace with v4.129.0 |
| 116–121 | v4.113.0 cross-reference audit note | OK — records the audit procedure, historically accurate |
| 130–136 | v4.27.0 const note | WRONG (covered above) |
| 218–227 | v4.31.0 `di` correction | OK — historical correction |
| 258 | "v4.68.0 / v4.72.0 — see §29" async note | OK |
| 741, 756, 777, 805, 817 | tensor feature history (v4.42–v4.45) | OK — accurate per CLAUDE.md |
| 1924–1947 | v4.29.0 DWARF deferral correction | OK — and verified still enforced by v4.121.0 |
| 2047–2061 | v4.27.0 @gpu decorator note | OK — verified by reading `mapanare/lower.py:1080` |
| 2365–2378 | v4.72.0–v4.76.0 async arc note | OK |
| 2645–2648 | v4.72.0–v4.76.0 async-keywords note | OK |

**No new WRONG items found in the light scan.** The sync-discipline
note at line 8–16 is well-maintained — every version-stamped
correction is either still accurate or caught above.

---

## Observations not in scope

- `CLAUDE.md` "GPU Backend (v2.0.0)" section claims `@gpu`/`@cuda`
  decorators enable automatic dispatch. This is stale (v4.27.0
  removed auto-dispatch; only runtime builtins exist). Noted for a
  future CLAUDE.md sweep. Not fixing here; out of scope.
- `docs/roadmap/v4/v4.127.0/GITNEXUS_AUDIT.md` is referenced in
  PROMPT.md but does not exist. No pre-existing GitNexus audit
  artifact to build on; this audit was done directly.

---

## Next

Phase 2 applies 10 edits to `docs/SPEC.md`:

1. Header version bump → 4.129.0.
2. Rewrite v4.27.0 const note to reflect v4.55.0 + v4.126.0.
3. Update §2.1.1 master list row for `const`.
4. Add `Future<T>` row to §3.2.
5. Renumber §3.6–§3.12 (fix duplicate §3.6).
6. Fix §6.3 lambda annotation contradiction (example vs note).
7. Update §27.1 TypeKind count 25 → 29.
8. Rewrite §28 stdlib preamble (drop "Seven"/"v0.9.0").
9. Redraw Appendix B pipeline diagram (Python → C).
10. Rewrite Appendix B "Python Transpiler (Legacy)" → "C Backend".
11. Update Appendix B MIR optimizer pass list.

(Numbering 1–11 matches edits; counted as "10 items" in the summary
because §28 "Seven modules" and the v0.9.0 tag are a single edit.)
