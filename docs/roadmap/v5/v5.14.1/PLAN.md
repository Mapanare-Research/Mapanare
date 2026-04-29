# v5.14.1 — bootstrap colon-block mirror (patch)

**Status:** PLANNING
**Breaking:** No. Pure additive: `mnc-stage1` learns to parse
colon-block syntax, exactly matching what the Python bootstrap
already does as of v5.14.0. Brace-style sources continue to compile
unchanged.
**Prerequisite:** v5.14.0 shipped (`mapanare fmt --to-terse` /
`--to-braces`, `pass` keyword, hardened `_indent_to_braces`).
**Estimated effort:** 6–10h, one or two sessions. The bulk is
porting the ~120-line preprocessor from `mapanare/parser.py` to
`.mn`; the `pass` keyword adds three lockstep edits in
`mapanare/self/{lexer,parser,...}.mn`.

---

## Why this exists

v5.14.0 shipped the colon-block surface syntax in the Python
bootstrap, plus the `mapanare fmt --to-terse` rewriter. By
explicit decision (PLAN.md "Deferred" section), the **bootstrap
mirror was deferred**: `mnc-stage1` continues to require brace
syntax. Users who write colon-style code today must run
`mapanare fmt --to-braces` before feeding it to the native
compiler.

That gap is acceptable in v5.14.0 because:

1. The Python bootstrap is the canonical reference compiler in
   dev workflows (`mapanare check`, `mapanare run`,
   `mapanare emit-llvm`).
2. Colon syntax in `mapanare/self/*.mn` itself only matters at
   v5.17.0 (Sh.\* — mechanical rewrite of self/), where
   `mapanare fmt --to-terse` is the migration tool.
3. Touching `mapanare/self/` is the only way to break the strict
   3-stage fixed point; v5.14.0 deliberately avoided that risk.

The gap stops being acceptable when **v5.16.0 (Te.4 self-host
string-interp parity) wants to be the validation buffer for v5.17.0**.
For v5.16.0 to do its job, the bootstrap must already accept the
colon syntax that v5.17.0 is about to land in `mapanare/self/`.

v5.14.1 is the load-bearing precondition. It can ship any time
between v5.14.0 and v5.16.0; "soon after v5.14.0" is the most
honest place for it because the design context is fresh.

---

## Goal

1. `mnc-stage1` accepts colon-block syntax for the same constructs
   the Python bootstrap does (fn, if/else/else if, while, for, let,
   trait, agent, impl, struct, enum, match).
2. `mnc-stage1` accepts the `pass` keyword as a no-op statement.
3. The bootstrap implementation **mirrors** the Python preprocessor:
   same algorithm, same comma-insertion rules for struct/enum/match,
   same continuation handling. A parametrized test asserts both
   preprocessors produce identical output on every parseable golden.
4. **Strict 3-stage fixed point preserved.** The new
   `_indent_to_braces`-equivalent in `.mn` must compile identically
   when stage1 → stage2 and stage2 → stage3.

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **B.1** | HIGH | Add `KW_PASS` to `mapanare/self/lexer.mn` (`is_keyword`, `keyword_token_type`). Mirror Python's `KW_PASS.2` regex behavior — match bare `pass` only, not `pass_*` identifiers. | 30m |
| **B.2** | HIGH | Add `pass_stmt` parsing to `mapanare/self/parser.mn`. Mirror Python's `pass_stmt: KW_PASS` — produce a `PassStmt` AST node. | 30m |
| **B.3** | HIGH | Add `PassStmt` to `mapanare/self/ast.mn`. Mirror Python `ast_nodes.py` shape. Add to `Stmt` discriminated tag. | 30m |
| **B.4** | HIGH | Wire `PassStmt` through semantic + lower as no-op. Mirror Python `semantic.py` (recognize as valid stmt) and `lower.py` (return None / emit zero MIR). | 1h |
| **B.5** | HIGH | Port `_indent_to_braces` to `mapanare/self/main.mn` (or a new `mapanare/self/preprocess.mn`). Same algorithm: indent-stack with `(level, needs_comma, prev_child_idx)` triples; comma insertion for struct/enum/match; continuation handling for else/sino. | 3–5h |
| **B.6** | HIGH | Wire the preprocessor into `compile()` in `main.mn` — call before `parse()`. | 30m |
| **B.7** | HIGH | New `tests/bootstrap/test_indent_preprocessor.py` — parametrized over every parseable golden, asserts the bootstrap preprocessor produces byte-identical output to the Python `_indent_to_braces`. This is the safety net. | 1–2h |
| **B.8** | MEDIUM | Forward `--to-terse` / `--to-braces` flags through native `mnc fmt` (currently shells out to `mapanare fmt` per v5.13.0 design; just needs to pass the new flags through). | 30m |
| **B.9** | LOW | Bb.\* seed refresh if any new C-runtime export is required. (None expected — the preprocessor is pure `.mn`.) | 30m–1h |

---

## Phase plan

**Phase 0 — Pre-implementation audit.** Run the existing v5.14.0
`tests/test_colon_blocks.py` against `mnc-stage1` to confirm the
exact failure shape. Document which goldens currently fail
parsing on the bootstrap. The list at v5.14.0 HEAD will be the
acceptance criterion: every file in that list must parse on
`mnc-stage1` after v5.14.1.

**Phase 1 — `pass` keyword in bootstrap.** B.1, B.2, B.3, B.4 in
order. Each in its own commit so a regression bisect is cheap. After
this phase: `mnc-stage1` should compile a brace-style program with
`pass` in it (a strict subset of colon-block work).

Validation between B.4 and B.5:

```bash
python scripts/build_stage1.py
python scripts/test_native.py --stage1 mapanare/self/mnc-stage1
bash scripts/verify_fixed_point.sh --keep
```

Goldens 66/66 and strict fixed point must both still hold —
adding `pass` to bootstrap is structurally similar to adding
`break`, so the fixed point should be untouched.

**Phase 2 — Preprocessor port.** B.5 + B.6. The hard part. Read
`mapanare/parser.py:1812-1955` and port line-by-line to `.mn`.
Watch for:

- Mapanare doesn't have Python tuples → use a small `IndentFrame`
  struct with `level: Int`, `needs_comma: Bool`, `prev_child_idx: Int`.
- Mapanare's string methods: `.substr`, `.ends_with`, `.replace`,
  `.starts_with` (verify availability against `mapanare/self/lexer.mn`).
  Use `__mn_*` runtime helpers if a method is missing.
- Mutation of `out` (the output line buffer) for back-patching
  trailing commas — make sure the bootstrap supports list element
  assignment of the form `out[i] = out[i] + ","`.

Validation after Phase 2:

```bash
python scripts/build_stage1.py
python scripts/test_native.py --stage1 mapanare/self/mnc-stage1
bash scripts/verify_fixed_point.sh --keep
```

**This is where fixed point is most likely to break.** If the new
`.mn` code is compiled into stage1, then stage1 compiles the same
`.mn` to stage2, the IR must be byte-identical. Any non-determinism
(map iteration order, hash collisions, etc.) will surface here.

**Phase 3 — Cross-bootstrap validation.** B.7. Add
`tests/bootstrap/test_indent_preprocessor.py` with a
parametrized test that:

1. Compiles a small test program through both Python's
   `_indent_to_braces` and the bootstrap's `.mn` equivalent (via
   a new `mnc-stage1 preprocess` subcommand or by extracting the
   preprocessor output another way).
2. Asserts byte-identical output for every parseable golden.

Without this test, a divergence between the two preprocessors
goes undetected until v5.17.0 fails on some edge case. Failing
loudly now is the whole point.

**Phase 4 — Native fmt flag forwarding.** B.8. Edit
`mapanare/self/main.mn`'s `cmd_fmt` to forward `--to-terse` /
`--to-braces` flags through the shell-out to `mapanare fmt`.

**Phase 5 — Closeout.** SESSION_REPORT, CHANGELOG entry, CLAUDE.md
release-notes entry.

---

## Risk register

| Risk | Likelihood | Mitigation |
|---|---|---|
| Strict 3-stage fixed point breaks | MEDIUM | Phase 2 validation is explicit. If it breaks, isolate by reverting B.5 and bisecting which preprocessor sub-rule introduces non-determinism. |
| Bootstrap `.mn` lacks a string method `_indent_to_braces` needs | LOW | Phase 2 audit lists every method called. Workaround: add a `__mn_*` C-runtime helper (Bb.\* seed refresh path, well-trodden). |
| Bootstrap preprocessor diverges from Python on an edge case | MEDIUM | B.7 cross-bootstrap test catches this on every CI run. The corpus is the test oracle; if both preprocessors agree on the corpus, they're acceptably equivalent. |
| `pass` keyword addition breaks `mnc-stage1` self-build | LOW | `pass` is added as a real keyword (not contextual); the bootstrap parser doesn't currently use the identifier `pass` per v5.14.0 audit. |
| List element assignment (`out[i] = ...`) not supported in self-host | LOW | If unsupported, rewrite to build a parallel `comma_overlay: Map<Int, Bool>` and apply at output time. |

---

## Out of scope (deferred)

- Single-line `if x: y` form — deferred to v5.21.0 Te.6.
- Block expressions in colon form — deferred (no clean
  equivalent; block expressions in v5.14.0+ remain brace-only).
- Promoting the preprocessor to a real INDENT/DEDENT lexer — only
  if a real-world bug demands it; the text-level approach is
  sufficient for the corpus and for v5.17.0's mechanical rewrite.
- Comment-aware reformatting — deferred to v5.20.0+.

---

## Success criteria

- `mnc-stage1` compiles every colon-style program the Python
  bootstrap accepts. Cross-bootstrap test (B.7) is green on every
  parseable golden.
- `mnc-stage1` compiles `fn empty(): pass`.
- Goldens 66/66 (brace-form, unchanged corpus) still pass.
- **Strict 3-stage fixed point preserved.**
- `mnc fmt --to-terse foo.mn` and `mnc fmt --to-braces foo.mn`
  work via native CLI (forwarded to Python).
- `make lint` clean.

---

## What it unblocks

- **v5.16.0 (Te.4)** can land self-host string-interp parity work
  with confidence that the bootstrap parser already accepts the
  syntax v5.17.0 will introduce.
- **v5.17.0 (Sh.\*)** can run `mnc fmt --to-terse mapanare/self/`
  and the result will compile through *both* compilers — Python
  bootstrap and `mnc-stage1` — preserving the strict 3-stage
  fixed point on a colon-style codebase.
