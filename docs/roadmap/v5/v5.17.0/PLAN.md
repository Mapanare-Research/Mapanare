# v5.17.0 — Sh.* — self-host rewrite to terse syntax

**Status:** PLANNING
**Breaking:** No semantic change. The 14k-line self-hosted compiler
is rewritten in terse syntax. Output IR must be byte-identical to
v5.15.0 modulo trivial whitespace in metadata strings.
**Prerequisite:** v5.13.0 (`mnc fmt`), v5.14.0 (`--to-terse`),
v5.15.0 (comprehensions + implicit return + lambdas) all shipped.
**Estimated effort:** 12–20h, two or three sessions. Most of it is
review, not editing — `mnc fmt --to-terse` does the mechanical
work.

---

## Why this exists

The terseness thesis is unfalsifiable until the language's flagship
real codebase reads as terse. `mapanare/self/*.mn` is 14k+ lines of
brace-style code. People clone the repo to learn the language by
reading the compiler, see verbose `{}` everywhere with explicit
`return r` at the end of every function, and conclude Mapanare
isn't actually terser than Python. We need the showcase code to
match the marketing.

This release is mechanical: run `mnc fmt --to-terse` on all 10
modules, review the diff, manually upgrade verbose loops to
comprehensions where it's a clear win, manually drop trailing
`return r` patterns where implicit return applies, validate at
every step that goldens stay 66/66 and the strict 3-stage fixed
point holds.

The tooling burden is in the prerequisite releases. v5.17.0 is the
payoff release — the moment the language ships in its canonical
form.

---

## Goal

1. All 10 modules in `mapanare/self/` use colon-block syntax.
2. Common verbose loop patterns rewritten to comprehensions where
   it's a win (judgment call per site).
3. Trailing `let r: T = x; return r` constructor pattern simplified
   to implicit-return where applicable.
4. Goldens 66/66 throughout.
5. Strict 3-stage fixed point preserved (the v5.9.0 milestone, held
   since).
6. Bootstrap seed refresh (Bb.* arc) — the v0.6.0 frozen seed in
   `bootstrap/` may need updating since the new self/ uses syntax
   that v0.6.0 parser can't handle.
7. Line-count reduction target: **30%+ shrink** on
   `mapanare/self/*.mn`. Document actual figure in SESSION_REPORT.

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Sh.A** | HIGH | Phase 0 dry-run: `mnc fmt --to-terse --dry-run mapanare/self/` to preview the diff. Inspect for any rewriter bugs. | 1h |
| **Sh.B** | HIGH | Per-module mechanical rewrite: run `--to-terse` on each module sequentially, validate stage1 + goldens between modules. | 4–6h |
| **Sh.C** | MEDIUM | Manual pass: identify verbose loops → comprehensions. Conservative — skip if not an obvious win. | 2–3h |
| **Sh.D** | MEDIUM | Manual pass: drop `let r: T = x; return r` constructor pattern → implicit return where it doesn't lose readability. | 2–3h |
| **Sh.E** | HIGH | Bootstrap seed refresh: regenerate frozen seed in `bootstrap/` if the v0.6.0 parser can't read the new self/. May not be needed if seed parser already supports both syntaxes (depends on v5.14.0 design). | 1–3h |
| **Sh.F** | HIGH | Validate strict 3-stage fixed point preserved. Document line counts before/after in SESSION_REPORT. | 1h |
| **Sh.G** | LOW | README + docs example refresh — switch user-facing examples to terse syntax now that self/ has. | 1h |

---

## Phase plan

**Phase 0 — Dry-run survey.** Run `mnc fmt --to-terse --dry-run` on
every module. Read the diff carefully. Look for:

- Any place where `--to-terse` produces non-identical AST (bug in
  v5.14.0's rewriter; do not proceed until fixed)
- Comment-handling edge cases (comments at end-of-block can be
  ambiguous after rewriting)
- Long-line cases where terse form actually reads worse — note
  these for the manual pass to maybe restore brace form

Write `PHASE_0_SURVEY.md` listing per-module: line count before,
predicted line count after, any concerns.

**Phase 1 — Mechanical rewrite, module by module.**

Order matters: rewrite in dependency order (least-depended-on
first), so a broken rewrite doesn't cascade.

```text
1. ast.mn         (no dependencies)
2. lexer.mn       (depends on ast)
3. emit_llvm_ir.mn  (LLVM type constants only)
4. mir.mn
5. lower_state.mn
6. parser.mn      (depends on ast, lexer)
7. semantic.mn    (depends on ast, mir)
8. lower.mn       (depends on most things)
9. emit_llvm.mn   (depends on mir)
10. main.mn       (depends on everything)
```

After each module:

```bash
python scripts/build_stage1.py
python scripts/test_native.py --stage1 mapanare/self/mnc-stage1
```

If goldens break → revert that module's changes, file a v5.14.0
follow-up bug, defer.

**Phase 2 — Comprehension upgrade pass.** Search for explicit
result-list-builder loops:

```mn
let result = [];
for x in xs {
  if cond {
    result.push(transform(x));
  }
}
return result;
```

Rewrite to:

```mn
return [transform(x) for x in xs if cond];
```

Conservative: skip if the body has side effects beyond the push,
skip if the loop produces multiple side outputs, skip if the
transformation is genuinely complex.

**Phase 3 — Implicit return pass.** Search for the constructor
pattern:

```mn
fn make_node(...) -> Node {
  let r: Node = first_field;
  return r;
}
```

Drop to:

```mn
fn make_node(...) -> Node = first_field
```

Or, if the function has multiple statements, drop just the trailing
`let r = x; return r` to a bare `x` (block-form implicit return).

**Phase 4 — Bootstrap seed.** Run `bash scripts/build_from_seed.sh`.
If it fails because v0.6.0 parser can't read the new syntax,
refresh the frozen seed:

```bash
# regenerate seed
python scripts/build_stage1.py
cp -r mapanare/self/*.mn bootstrap/
# re-run
bash scripts/build_from_seed.sh
```

Document seed refresh in SESSION_REPORT (Bb.* arc bookkeeping).

**Phase 5 — Validate.** Strict 3-stage fixed point. Goldens 66/66.
build_from_seed.sh works. `make lint` clean.

**Phase 6 — Docs.** Update SPEC.md, README.md, examples to terse
style. SESSION_REPORT with before/after line counts.

---

## Risk register

| Risk | Likelihood | Mitigation |
|---|---|---|
| `--to-terse` rewriter has subtle bug → AST drift | MEDIUM | Phase 0 dry-run + Phase 1 module-by-module validation catches this. Each module's stage1 build must pass. |
| Strict fixed point breaks because emitted IR differs | HIGH | The IR should be byte-identical (same AST → same MIR → same IR). If it diverges, lowering is non-deterministic somewhere — debug in the lowerer, not the rewriter. |
| Bootstrap seed v0.6.0 can't read new syntax | HIGH | If v0.6.0 parser doesn't support colon blocks, refresh the seed. Document in Bb.* and CHANGELOG. |
| Manual passes (Phase 2/3) introduce semantic bugs | MEDIUM | Each manual edit must be a separate commit and validated by a goldens run. No batched manual passes. |
| Reviewer fatigue produces line-count drop without quality drop | LOW | Don't optimize for line count. Optimize for readability. If a brace-style block reads better than the colon equivalent in a tight context, keep it. |
| Self-hosted compile time regresses | LOW | Track build time before/after; report in SESSION_REPORT. Not a blocker but worth noticing. |

---

## Out of scope (deferred)

- Deprecating `{}` syntax → **v5.19.0 Te.3**
- Rewriting other code (`mapanare/*.py`, examples, tests)
- Performance optimizations of the rewritten code
- New compiler features
- Comment style canonicalization

---

## Success criteria

- All 10 modules in `mapanare/self/` use colon-block syntax
- Verbose loop → comprehension upgrades applied where they're
  clear wins (judgment call documented in SESSION_REPORT)
- Implicit-return upgrades applied where idiomatic
- Goldens 66/66 pass
- Strict 3-stage fixed point preserved (line count + diff stays
  zero)
- `bash scripts/build_from_seed.sh` works
- Line count reduction: 30%+ on `mapanare/self/*.mn` (target;
  document actual figure)
- `make lint` clean
- SESSION_REPORT documents per-module before/after line count and
  any decisions to keep brace style in specific spots
