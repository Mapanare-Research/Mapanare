# v5.16.0 — Te.4 — self-host string-interpolation parity

**Status:** PLANNING
**Breaking:** No. Source code that already uses `"${expr}"`
interpolation produces the same runtime behavior, just now in
both compilers instead of one. Source code that doesn't use
interpolation is byte-identical in/out.
**Prerequisite:** v5.15.0 shipped (Te.2 — comprehensions, terse
lambdas, implicit-return one-liner).
**Estimated effort:** 6–10h, one or two sessions. Pure self-host
lexer/parser work, no runtime / lowering / IR changes.

---

## Why this exists

The v5.13.0-prep audit on 2026-04-28 turned up a quiet divergence:
Python bootstrap `"${name}"` interpolation **works**, native
`mnc-stage1` `"${name}"` interpolation **errors with "Undefined
variable 'name}'"** because the self-hosted lexer/parser doesn't
recognize `${...}`. Same source, different behavior. The Python
side splits the literal into pieces and emits
`__mn_str_concat(__mn_str_from_int(...), ...)` calls; the native
side reads the entire `"${name}"` as a flat string token, then
the parser tries to lex `${name}` as `$ {name}` and fails.

This is the last remaining Python-vs-native string-handling gap.
Closing it before the v5.17.0 self-host rewrite (Sh.*) matters
because:

1. The Sh.* rewrite touches every module in `mapanare/self/` —
   if those modules start using `${...}` in their own code (which
   they will, because it reads better), they need to compile
   through the native compiler.
2. Validation buffer: any new lexer logic gets one full release
   (v5.16.0) of soak via `mnc fmt` and the test corpus before
   v5.17.0's giant rewrite consumes it. If there's a corner-case
   bug in the new lexing path, we want it surfaced on a small
   release, not buried in a 14k-line rewrite diff.
3. SPEC §4.2 already shows `print("${i}")` in casual examples;
   the spec promise has been real-but-unevenly-implemented for
   long enough.

This is also the natural shape of a "finish-the-spec" release —
the conversation that produced this plan called Te.4 "self-host
string-interpolation parity" specifically to give it a tight,
testable narrative.

---

## Goal

1. The native `mnc-stage1` lexer/parser accepts `"${expr}"`
   interpolation and produces IR functionally identical to what
   the Python bootstrap produces.
2. Edge cases match Python bit-for-bit: nested braces, escaped
   `\${`, empty `"${}"`, multi-expression `"${a}${b}"`,
   expressions with method calls (`"${x.upper()}"`), expressions
   with arithmetic (`"${1+2}"`), strings inside the expression
   (`"${"hi"}"` — likely an error in both, but consistently).
3. New goldens cover the matrix of cases.
4. The Python bootstrap stays the source of truth — if its
   behavior is surprising on some corner case, mirror it; do not
   fix Python and native simultaneously.
5. Strict 3-stage fixed point preserved.

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Te.4.A** | HIGH | Phase 0 spec: enumerate every interpolation behavior the Python bootstrap exhibits today (escape rules, nesting, empty, multi, expression types). Compile a fixture file through Python `emit-llvm` to lock the reference output. | 1–1.5h |
| **Te.4.B** | HIGH | `mapanare/self/lexer.mn`: extend STRING_LIT tokenization to detect `${` and `}` boundaries. Emit a sequence of `STRING_PART` tokens interleaved with normal expression tokens. (Or: lex flat strings + post-process — match whichever Python does.) | 2–3h |
| **Te.4.C** | HIGH | `mapanare/self/parser.mn`: build the equivalent AST node (`StringInterp(parts: list<Expr>)` or split-and-concat sugar — match the Python AST shape). | 1.5–2h |
| **Te.4.D** | HIGH | `mapanare/self/lower.mn`: lower `StringInterp` to the same `__mn_str_concat`/`__mn_str_from_int`/`__mn_str_from_float`/`__mn_str_from_bool` chain the Python lowerer produces. If the Python lowerer's expansion happens in `parser.py` (post-lex sugar), mirror that placement instead of in `lower.mn`. | 1.5–2h |
| **Te.4.E** | HIGH | Goldens: `tests/golden/string_interp_*.mn` covering the Te.4.A matrix. Each must produce byte-identical IR through Python and `mnc-stage1`. | 1–1.5h |
| **Te.4.F** | MEDIUM | `mnc fmt`: handle `${...}` whitespace canonicalization. Inside `${...}` — single space around binary ops, no leading/trailing space. | 0.5h |
| **Te.4.G** | LOW | SPEC.md §4.2 (or a new dedicated section): formally document interpolation semantics now that both compilers honor it. Replace casual `print("${i}")` mentions with a single canonical reference. | 0.5h |

---

## Phase plan

**Phase 0 — Lock Python behavior as the spec.** Build the case
matrix. For each case, run through `python3 -m mapanare emit-llvm`
and capture the IR. The captured IR is the spec — anything
`mnc-stage1` emits that diverges is wrong (even if it's "more
correct" by some external standard).

Cases to cover:

| Case | Source | Expected behavior |
|---|---|---|
| Plain string | `"hello"` | No interp; single string constant |
| Single var | `"hi ${name}"` | Split + `__mn_str_concat` |
| Int interp | `"n=${n}"` | `__mn_str_from_int` then concat |
| Float interp | `"f=${f}"` | `__mn_str_from_float` then concat |
| Bool interp | `"b=${b}"` | `__mn_str_from_bool` then concat |
| Method call | `"${name.upper()}"` | Method called, result interpolated |
| Arithmetic | `"sum=${1 + 2}"` | Expression evaluated, result interpolated |
| Multi | `"${a} and ${b}"` | Two interp sites, concatenated |
| Empty | `"${}"` | Likely parse error in Python — match |
| Escaped | `"\${not_a_var}"` | Literal `${not_a_var}`, no interp |
| Nested string | `"${"hi"}"` | Likely parse error — match |
| Brace in expr | `"${f({k:1})}"` | Tricky: nested `}` mustn't close interp prematurely |

Write the matrix into `docs/roadmap/v5/v5.16.0/INTERP_SPEC.md`
with each case's expected IR shape (or expected error).

**Phase 1 — Read the Python implementation.** Find where the
Python bootstrap handles `${...}`. Likely candidates:

- `mapanare/parser.py` — post-lex sugar: STRING_LIT token gets
  split into pieces during transformer phase.
- `mapanare/lower.py` — lowering phase produces concat chain.
- A dedicated `string_interp.py` module — less likely.

Document the location and the exact algorithm in
`INTERP_SPEC.md`. The native port mirrors this algorithm; do
not invent a new one.

**Phase 2 — Self-host lexer (Te.4.B).** Extend
`mapanare/self/lexer.mn` to match Python's approach. If Python
does a single `STRING_LIT` token then post-processes, the
self-host lexer changes are minimal — just expose enough info
for the parser to do the same split. If Python emits multi-token
sequences, mirror that.

Test incrementally: every case from Te.4.A's matrix should lex
to the same token shape as the Python lexer (or to a token shape
that the parser can post-process identically).

**Phase 3 — Self-host parser (Te.4.C).** Build the AST nodes.
Match the Python AST shape exactly — same node names, same
field names, same nesting structure. The downstream lowerer
expects a specific shape; conformance is non-optional.

**Phase 4 — Self-host lowering (Te.4.D).** If lowering happens
post-parse, port the Python lowerer's logic to `lower.mn`. If
lowering already happens (because parsing produces concat-chain
AST directly), this phase may be empty.

After this phase, the Phase 0 fixture file should produce
byte-identical IR through both compilers. Validate explicitly.

**Phase 5 — Goldens (Te.4.E).** Move each Te.4.A case from the
spec doc into a real golden. Two-way validation:

```bash
python3 -m mapanare emit-llvm tests/golden/string_interp_X.mn -o /tmp/py.ll
./mapanare/self/mnc-stage1 emit-llvm tests/golden/string_interp_X.mn -o /tmp/native.ll
diff /tmp/py.ll /tmp/native.ll  # must be empty (modulo metadata)
```

**Phase 6 — fmt + spec docs (Te.4.F + Te.4.G).** Whitespace rules
inside `${}`. SPEC §4.2 polished. SESSION_REPORT.

---

## Risk register

| Risk | Likelihood | Mitigation |
|---|---|---|
| Python bootstrap has hidden behavior the spec doc misses | HIGH | Phase 0 is exhaustive; the case matrix is the contract. Anything not in the matrix that surfaces later is a docs/spec gap, not a Te.4 regression — handle in a follow-up release. |
| Self-host lexer port has subtle off-by-one on nested braces | MEDIUM | Test `"${f({k:1})}"` early in Phase 2. Brace counting is the classic place this breaks. |
| `${...}` interaction with raw / triple-quoted strings | LOW | Triple-quoted strings exist in the grammar (`TRIPLE_STRING`). Decision in Phase 0: do they support interp? If Python does, mirror; if not, document. |
| Strict 3-stage fixed point breaks because emitted IR differs trivially (whitespace in metadata) | MEDIUM | Compare IR byte-for-byte except documented module-metadata strings. If the only diff is metadata, it's a fixed-point preservation per existing convention. |
| Te.4 ships, then the v5.17.0 self-host rewrite trips a corner case the goldens didn't cover | MEDIUM | The goldens cover the Te.4.A matrix; the rewrite will exercise broader patterns. Treat any v5.17.0-surfaced interp bug as a Te.4 follow-up patch (v5.16.1), not a Sh.* defect. |
| `mnc fmt`'s string-interp canonicalization fights with author intent | LOW | Be conservative in Te.4.F: normalize whitespace inside `${}` only, do not rewrite expressions. |

---

## Out of scope (deferred)

- f-string-style format specifiers (Python's `f"{x:.2f}"`,
  `f"{x:>10}"`) — defer to a future We.* arc; scope creep here
  multiplies the test matrix
- Raw string literals (`r"${not_interp}"`) — defer; SPEC doesn't
  mention them
- Multi-line string interpolation in TRIPLE_STRING — defer
  unless Python already supports it (Phase 0 decides)
- Format-time error messages on malformed `${...}` — match
  Python's current quality; improve later as a polish pass
- New runtime str builders (e.g., `__mn_str_from_list`) — not
  needed; existing builders cover the matrix

---

## Success criteria

- Every case in `INTERP_SPEC.md` produces byte-identical IR
  (modulo trivial metadata) through Python `emit-llvm` and
  `mnc-stage1 emit-llvm`
- 8+ new goldens land in `tests/golden/string_interp_*.mn`,
  all passing on both compilers
- Goldens 74+/74+ (existing 66 + Te.2's 6 + Te.4's 8)
- Strict 3-stage fixed point preserved
- `mnc fmt --check` clean on the new goldens
- `bash scripts/build_from_seed.sh` works (no seed refresh
  needed — purely lexer/parser changes don't add new C-runtime
  exports)
- SPEC.md has a single canonical interpolation section
- `make lint` clean
- SESSION_REPORT documents the case matrix + the location of
  Python's interpolation logic for future maintainers
