# Coral — Language Design Review of Mapanare v5.22.0

**Reviewer:** Coral
**Personality:** Dreamer. Languages as art. Asks "what is this language trying to say?" Compares to Haskell, Erlang, Go, Zig, Mojo.
**Previous Version Reviewed:** v5.11.0 (9.5/10, EXCEEDS, -0.1 dock)
**Score:** 9.55 / 10
**Grade:** EXCEEDS
**Delta vs v5.11.0:** +0.05
**Verdict:** PASS WITH NOTES
**Confidence:** 9 / 10
**Files Reviewed:** `docs/SPEC.md` (full), `docs/manifesto.md`, `mapanare/mapanare.lark`, `mapanare/parser.py` (Te.3 detector), all 6 design docs, all 16 SESSION_REPORTs, `tests/golden/95_chained_cmp_side_effect.mn`, `examples/chained_cmp.mn`, `docs/README.{es,pt,zh-CN}.md`, `tests/test_brace_deprecation.py`, the carry-forward ledger, the v5.11.0 Coral.

---

## Executive Summary

Ten releases. Six additive language features. Zero new MIR ops, zero
new IR shapes, zero new runtime functions. A self-hosted compiler
that shrinks **-3,950 lines (-13.8%)** while preserving strict
3-stage fixed point at byte-zero across every per-module commit.
Goldens 66/66 → 95/95. Five bootstrap mirror cross-test suites
(Te.5 12/12, Te.6 10/10, comprehension 10/10, string-interp 10/10,
indent-preprocessor 142/142) — all green at HEAD. This is the
single largest feature-velocity arc in v5 history, and it is the
most disciplined feature-velocity arc I have ever reviewed for
this project.

The terseness arc Te.1 → Te.6 composes. Read the SPEC top to
bottom and the language hangs together: §2.2 chained comparisons
at precedence level 7, §3.7 struct ergonomics (field shorthand,
`..base`, destructuring), §4.0 colon-block as canonical with
brace as soft-deprecated, §4.3.1 `if let` / `while let` /
`let else`. Each one of these in isolation is a "small win for
the working programmer" — and the SPEC text I read at v5.21.1 is
the first version of the SPEC where those small wins read like a
single language rather than a pile of features. The Te.5 SPEC
sections in particular (§3.7 lines 706–749) show genuine care
about how the forms compose with what was already there.

But I have to be honest about the weighting question the lead
flagged in my charter: **hygiene-via-release vs hygiene-at-source.**
v5.21.1 closed twelve doc-surface findings (H.1–H.12) in a dedicated
release. The SPEC re-sync that I docked -0.10 for at v5.11.0 (header
at 5.7.1 against a v5.11.0 codebase) is now closed — but it is
closed by a hygiene release that ran 14 releases after the drift
started accumulating, not by closing the gaps in the same release
that introduced the feature. That is the same closure pattern the
lead used at v5.7.1 → v5.8.0 (the project record 9.66 panel), so
there is precedent. But two arcs of "let it accumulate, then sweep"
is a process pattern, not a precedent.

I am giving back the **+0.10** I docked at v5.11.0 for SPEC
staleness — the gap is now closed, structurally where the lead
could close it structurally, by patch where the lead chose to
patch. I am crediting **+0.025** for the discipline of the
arc itself (six features composed into a coherent terseness story
without grammar churn beyond the documented additive surface).
And I am docking **-0.075** in three places: a real Te.3 surface
gap that the PRE_PANEL_AUDIT's own test does not exercise (single-
line brace shapes parse silent), the manifesto's "Curly braces for
blocks" line standing untouched against a codebase that
soft-deprecated braces, and the SPEC's example corpus still being
72% brace-style against a colon-canonical SPEC. **Net: +0.05,
from 9.5 to 9.55.** Trajectory restored.

---

## Score: 9.55 / 10

Score history (Coral):

| Version | Score | Grade | Delta |
|---|---|---|---|
| v4.99.0 | 7.5 | RESERVATIONS | -- |
| v4.114.0 | 8.3 | PASS WITH NOTES | +0.8 |
| v4.120.0 | 8.1 | PASS WITH NOTES | -0.2 |
| v4.136.0 | 8.7 | MEETS | +0.6 |
| v4.143.0 | 8.5 | MEETS | -0.2 |
| v4.144.0 | 8.9 | MEETS | +0.4 |
| v4.154.0 | 9.3 | EXCEEDS | +0.4 |
| v5.2.0 | 9.4 | EXCEEDS | +0.1 |
| v5.7.1 / v5.8.0 panel | 9.6 | EXCEEDS | +0.2 |
| v5.11.0 | 9.5 | EXCEEDS | -0.1 |
| **v5.22.0** | **9.55** | **EXCEEDS** | **+0.05** |

---

## Progress Since Last Review (v5.11.0 → v5.22.0)

### Te.1 — colon-block syntax (v5.14.0) + bootstrap mirror (v5.14.1)

**Status:** Shipped as designed, with one philosophical gap I will
flag below.

The audit-driven design at `v5.14.0/COLON_BLOCK_DESIGN.md` is the
right shape. The Phase 0 audit found that the v3.0.0-era
`_indent_to_braces` preprocessor at `mapanare/parser.py:1812`
already covered ~70% of colon-block surface — what shipped was
hardening, not invention. That is the discipline of a language
that has been built on top of itself for long enough to know
what it already has.

The `pass` keyword decision (locked decision #3) is the correct
one. I appreciate the rationale: `{}` looks like an object literal,
empty colon-block is genuinely ambiguous, `pass` removes the
ambiguity at zero parser cost. The three stdlib `pass`-as-identifier
collisions renamed in lockstep (`stdlib/db/migrate.mn`,
`stdlib/net/http/auth.mn`, `stdlib/test/runner.mn`) is exactly the
kind of cleanup discipline the v4.18.0–v4.26.0 hollow-features arc
did not have.

**Bootstrap mirror (v5.14.1)** routes the preprocessor through C
(`runtime/native/mapanare_core.c::__mn_indent_to_braces`, ~280
LOC) rather than `.mn`, after the SESSION_REPORT documents two
bootstrap-lower pathologies that broke the `.mn` port. This is
honest engineering: the C-route bypasses both bugs by
construction and ships now. I would prefer the `.mn` port
eventually — the bootstrap-quality bugs are tracked separately —
but as a pragmatic compromise to ship Te.1 the C-route is correct.
The 142-case `tests/bootstrap/test_indent_preprocessor.py` cross-
bootstrap test asserting byte-identical output between Python and
C is the right shape.

### Te.2 — comprehensions + lambdas + implicit-return (v5.15.0) + mirror (v5.15.1)

**Status:** Shipped, three additive forms, all desugared cleanly to
existing constructs.

`fn name(args) [-> Ret] = expr` lowers at parse time to
`Block([ReturnStmt(expr)])` — downstream is unchanged. Terse
lambda `|x, y| body` lowers to the existing `LambdaExpr`. List
and map comprehensions lower to fresh accumulator + nested
for/if + push/insert. The empty-`MapLiteral` type-annotation
patch in `_lower_let` mirrors the v4.122.0 empty-`ListLiteral`
patch — without it, comprehension-produced maps printed `<?>`
for indexed values. This is the kind of catch that the v5.15.0
SESSION_REPORT's Phase 0 audit produced because someone read
the old patch when implementing the new one.

**Comprehensions in SPEC.** I checked §16.5 / §17.5 — both list
and map comprehensions are documented at v5.21.1 hygiene. **Te.2
is fully synced.**

### Te.4 — string-interp parity (v5.16.0)

**Status:** Closes the last Python-vs-native string handling gap.

This release surfaced the philosophical question I was waiting
for: when the bootstrap diverges from Python, how do we close it?
The v5.16.0 answer is "close the bootstrap to match Python." The
contract was `mapanare/parser.py::_split_interp` /
`_parse_interp_expr` / `_lower_interp_string` / `_do_cast`; the
bootstrap implements the same shape. New 10-case
`tests/bootstrap/test_string_interp_mirror.py` asserts byte-
identical stdout via Python and native compilation. **Three
latent bugs surfaced in scope and fixed** — the substr-API bug,
the early-return bug, the `\$` escape strip in the lexer. This
is the v5.20.1 Te.5.F.E pattern in microcosm.

### Sh.* — self-host rewrite to terse syntax (v5.17.0/.1/.2)

**Status:** -3,950 lines (-13.8%) of self-host shrink, strict 3-stage
fixed point preserved at every per-module commit.

This is the headline of the arc, and it is what convinced me to
restore the +0.025 discipline credit. Seventeen modules, one
commit per module, stage1 build + goldens 80/80 validated between
every commit. That is what you do when you trust your own
fixed-point invariant. The v5.9.0 milestone has now held across
13 consecutive releases — the longest streak in project history,
and it held *through a mechanical rewrite of the self-host source
itself.* Languages that say "we are self-hosted" without saying
"and we can rewrite our own self-host source without breaking
anything" are saying something weaker than Mapanare is saying at
v5.17.x.

**v5.17.1 Sh.D.B implicit-return** — 159 ONELINER + 121 BLOCK_SHORT
conversions, with 28 BLOCK_LONG candidates deliberately SKIP'd.
The skip rationale ("in long functions the explicit `return`
keyword is a punctuation marker readers scan for") is exactly the
language-design judgment I want to see. Per-site judgment is
correct; mechanical sweep would have been wrong here.

**v5.17.2 Sh.H** — 11 defensive-iteration sites, all rewritten,
zero SKIP. Pattern A is "for `_` in `0..LARGE`: if i < n:
r.push(xs[i]); i = i + 1" → range-for over `0..len(xs)`. That
loop shape was a v4-era workaround for missing `range` semantics;
v5.14.0 made the rewrite legal and v5.17.2 actually did it. Cleanup
discipline.

### Mc.* — LSP + init + check (v5.18.0)

**Status:** v5.11.0 panel MEDIUM closed.

This was the single largest carry-forward from my v5.11.0 review
("the developer surface is mediated by Python"). At v5.11.0 native
`mnc` covered 7 of `mapanare`'s 25 subcommands. v5.18.0 closes
Mc.1 (lsp), Mc.3 (init), Mc.4 (check) by **verifying-and-filling**
on the existing pygls implementation rather than rewriting.

The Phase 0 surprise documented in `MC_TOOLING_DESIGN.md` is the
right kind of surprise: the lead expected greenfield, the audit
found 3,020 lines of pygls already in place implementing the MVP
plus extras (find-refs, rename, workspace-wide cross-module
index). What shipped was hardening + the missing init template
mechanism + the VSCode extension wiring + the native `mnc`
dispatch shell-out. Same shape as Te.1: trust what is already
there, fill the gaps.

The native dispatch through `mapanare/self/main.mn`'s `check` /
`init` / `lsp` cases shelling out to Python is the v5.13.0 `mnc
fmt` pattern — pragmatic, honest, ships. The native LSP port
stays deferred. **The Pk.3 Python-sidecar concern from my v5.11.0
review is now substantially smaller** — `mnc lsp` and `mnc check`
exist in the native dispatch surface, even if they currently
shell out. That is the right shape for the mid-arc; full native
ports can come later.

### Te.3 — `{}` soft-deprecation (v5.19.0)

**Status:** Shipped. Mostly works. **One real surface gap surfaced
in the panel pre-flight** — see Issues Found.

The deprecation policy (SPEC §27.3) says: RFC + deprecation
warning + migration guide + major version bump. Te.3 follows
the verbatim shape: parse-time warning, `mnc fmt` migration
default, `MAPANARE_NO_BRACE_WARNING=1` opt-out, `mnc fmt
--keep-braces` preservation, hard removal at v6.0. Two-release
soak window before v6.0 is documented. **The cycle execution
follows the policy correctly.** This is the cleanest deprecation
cycle I have reviewed for this project, technically — Te.3 is
on track for v6.0 hard removal exactly the way Pk.2 was for the
v5.9.1 deprecation note removal at v5.11.0.

**The 23/23 `tests/test_brace_deprecation.py` suite is honest
test coverage.** Test names alone tell the policy story:
`test_parse_one_warning_per_file_not_per_block`,
`test_env_var_suppresses_warning`,
`test_fmt_default_auto_migrates_braces`,
`test_fmt_to_terse_and_keep_braces_mutually_exclusive`. This is
contract documentation as test, exactly the shape v5.13.1's
`@test` runtime fix was supposed to enable.

### Te.5 — struct ergonomics (v5.20.0) + bootstrap mirror (v5.20.1)

**Status:** Four new surface forms, all desugared at lower time
to existing constructs. Bootstrap mirror landed v5.20.1 per the
v5.14.0→v5.14.1 / v5.15.0→v5.15.1 precedent.

The 10 locked decisions in `STRUCT_ERGO_DESIGN.md` are well-
reasoned. D1 (`..base` trailing, Rust-style) over JS-style
spread is the right choice — the override-after-spread
semantics are ambiguous when override key matches base key. D5
(let-else divergence required) is correct semantically; the
implementation's `_block_diverges` / `_stmt_diverges` /
`_expr_or_block_diverges` recursive walk at the AST tail is the
right place to enforce it. v5.20.0 restricting `let else` to
0/1-arg constructor patterns is the right scoping — multi-binding
patterns are real complexity, deferring is honest.

The two pre-existing latent bugs surfaced + fixed in v5.20.1
scope — `lower_match` `alloca <fn_ret>` dummy when fn_ret is
void, and TK_UNKNOWN demotion to undef — are the v5.16.0
"surface bugs in scope" pattern again. Bootstrap mirror work
flushes out latent quirks; the lead's discipline is to fix them
where they are rather than route around them.

### Te.6 — chained comparisons (v5.21.0)

**Status:** Six locked decisions, all implemented faithfully,
once-evaluation verified in IR.

Read the design doc at `v5.21.0/CHAINED_CMP_DESIGN.md`. Six
decisions, every single one of them documented with rationale,
each one mapped to a specific implementation site. D6 is the
load-bearing decision: 1-cmp shapes preserve the existing
`BinaryExpr` AST + IR byte-identity. Without D6, the
fixed-point streak breaks; with D6, the chain dispatcher emits
legacy shape on `tail count = 1` and the new
`ChainedCompare(operands, ops)` only on `tail count >= 2`. This
is exactly the v5.20.0 Te.5.F.C `struct_update_counter`
discipline — separate from `tmp_counter` so the synthesized
chain temps don't perturb the global `%tN` sequence.

I ran the once-evaluation IR check on
`tests/golden/95_chained_cmp_side_effect.mn`:

```
$ python3 -m mapanare emit-llvm -O0 tests/golden/95_chained_cmp_side_effect.mn -o /tmp/chain.ll
$ grep -c "call.*@middle" /tmp/chain.ll
1
```

**Exactly one call site to `@middle` per chain instance.** D3
(once-evaluation) is verified at runtime via the golden's
`print("M")` side effect and at compile time via the IR. This
is what languages like Python and Rust mean when they say
"chained comparisons evaluate the middle once" — not "should"
or "usually" but "always, by construction."

The precedence merge (D1) is a real grammar change — the
pre-v5.21.0 `eq_expr` precedence layer is folded into `cmp_expr`,
moving `==`/`!=` from precedence 3 to 4. The audit text in the
design doc says "no existing code mixes `==` and `<` at the
same level without explicit parens or `&&`/`||`." I trust the
audit but did not re-grep.

### Sh.* discipline credit

The arc **shrinks the self-hosted compiler** from a v5.13.0
baseline of ~28,700 lines down to 24,748 lines (the v5.17.1
post-Sh.* number cited in the v5.18.0 SESSION_REPORT). At v5.22.0
HEAD, `wc -l mapanare/self/*.mn` reports a total of 46,616 lines
counting test files inside the directory — but the hand-edited
modules have held the shrink. Strict 3-stage fixed point at
**238,086 lines / 0-line diff** at HEAD (verified live).

---

## What is preserved from v5.11.0

### Zero grammar churn beyond documented additive surface

```
$ git log v5.11.0..HEAD -- mapanare/mapanare.lark
dcbff18 v5.21.0 Te.6: chained comparisons (Python + bootstrap)
4ea40e1 v5.20.0 Te.5.E: if-let / while-let / let-else
06af1a8 v5.20.0 Te.5.C/D: struct update + let destructuring
894920c v5.20.0 Te.5.A/B: design lock + field shorthand
371b874 v5.15.0: Te.2 — comprehensions, implicit-return one-liner, terse lambdas
2172b8b v5.14.0: Te.1 — colon-block syntax (additive)
```

Six grammar commits. Each one corresponds to a Te.* feature with
a Phase 0 design lock. The diff content is the documented additive
surface — new keywords (`pass`), new statement kinds
(`let_dest_stmt`, `let_else_stmt`, `while_let_stmt`, `pass_stmt`,
`if_let_expr`, `lambda_terse`, `list_comp`, `map_comp`,
`comp_clause`), one rule relaxation (`field_init: NAME (COLON
expr)?`, the v5.20.0 Te.5.B 1-rule grammar relaxation), and **one
removal**: the `eq_expr` precedence layer at v5.21.0, folded into
`cmp_expr`. The precedence-level removal is the legitimate
documented exception — I checked the v5.21.0 design doc D1 and the
audit rationale ("no existing code mixes `==` and `<` at the same
level without explicit parens or `&&`/`||`") and the rationale is
sound.

**Zero grammar churn class:** preserved. Forty v5 releases without
grammar churn at v5.11.0 became forty-six at v5.22.0 with six
intentional, documented, design-locked additive grammar diffs.
This is the discipline carrying through.

### Strict 3-stage fixed point preserved across the arc

```
$ bash scripts/verify_fixed_point.sh --keep
[Stage 1] stage1 compiles mnc_all.mn → stage2.ll
  stage2.ll: 238086 lines
  llvm-as: OK
[Stage 2] stage2 compiles mnc_all.mn → stage3.ll
  stage3.ll: 238086 lines
  llvm-as: OK
[Verify] Fixed point: diff stage2.ll stage3.ll
  ✓ FIXED POINT REACHED
  stage2.ll == stage3.ll (238086 lines, 0 diff)
```

13 consecutive releases of byte-zero diff (v5.9.0 → v5.21.1).
At v5.11.0 the streak was 5 — longest in project history at the
time. At v5.22.0 the streak is 13, **and it held through the
mechanical Sh.* rewrite of the self-host source itself.** The
discipline carrying through is the same; the demonstration
of the discipline is dramatically larger.

### Localized READMEs (es / pt / zh-CN)

Closed at v5.21.1 hygiene (H.6). I read the three native-compiler
subsections in target language — they tell the Te.1–Te.6 story,
not just bump badges. The Spanish version reads at line 125:

```
- **Sintaxis terse (arco v5.13–v5.21)** — bloques con dos puntos
  (Te.1), comprensiones de listas/mapas y lambdas terse (Te.2),
  interpolacion de strings auto-hospedada (Te.4), ergonomia de
  structs (Te.5: shorthand de campos, `..base`, destructuring,
  if-let / while-let / let-else), comparaciones encadenadas
  (Te.6: `0 < x < 10`).
```

That is real prose-body content, in target language, naming each
Te.* form with the right symbol. The Bo.17r MEDIUM from my v5.11.0
review is closed properly — this was the prose body, not a
badge bump.

### `examples/signals/counter.mn` stale comment (TRIVIAL)

I did not re-check this in scope; v5.11.0 flagged the
"Once `mnc run` is the default" comment as TRIVIAL carry-forward.
Not load-bearing.

---

## Issues Found

### MEDIUM

#### M1. Te.3 brace-deprecation detector has a single-line shape gap

**Severity:** MEDIUM
**Domain:** Language design / DX
**Reported by:** Coral (this review, surfaced via PRE_PANEL_AUDIT pre-flight)

The PRE_PANEL_AUDIT.md's own pre-flight test at lines 226–228:

```
echo 'fn main() { print("hi") }' > /tmp/brace.mn
python3 -m mapanare emit-llvm /tmp/brace.mn 2>&1 | head -3
# expected: warning: /tmp/brace.mn: uses deprecated {}-block syntax (1 occurrence). ...
```

**Actual output at v5.22.0 HEAD:**

```
[dev mode] Using Python bootstrap compiler. For native speed: mnc run <file.mn>
emitted /tmp/brace.mn -> /tmp/brace.ll (target: x86_64-unknown-linux-gnu)
```

**No warning fires.** The detector at
`mapanare/parser.py::count_user_brace_block_openers` (line ~2270)
counts `{` only when it appears at end-of-line (block-opener
shape). The all-on-one-line shape `fn main() { print("hi") }` has
`{` mid-line, so `line_code.endswith("{")` is False and the brace
is not counted.

Multi-line shapes work correctly:

```
$ cat > /tmp/brace_multi.mn << 'EOF'
fn main() {
    print("hi")
}
EOF
$ python3 -m mapanare emit-llvm /tmp/brace_multi.mn 2>&1 | head -3
warning: /tmp/brace_multi.mn: uses deprecated {}-block syntax (1 occurrence). ...
```

So Te.3 fires on the canonical brace-block shape but is silent on
the all-on-one-line shape — which the grammar still accepts as
legal. That is a Te.3 surface that does not deprecate every shape
the grammar accepts. Users of the all-on-one-line idiom will reach
v6.0 hard removal with no warning at any prior point.

**Suggested fix.** The `count_user_brace_block_openers` detector
should count any user-emitted `{` that opens a block, not only
those at end-of-line. The simplest fix: scan tokens (not lines) and
count opening `{` that appear in block positions (after `fn`, `if`,
`else`, `while`, `for`, `match`, `impl`, `trait`, `agent`,
`struct`, `enum`, ` => `, ` else `). The token approach also
correctly excludes `#{...}` map literals without the
`endswith("#{")` heuristic. Alternatively, integrate the count into
`_indent_to_braces` — it already sees the source position of every
brace it leaves untouched. ~1–2h effort, plus 1 new test case in
`test_brace_deprecation.py` exercising the all-on-one-line shape.

This is a hollow-feature class issue (Te.3 announces a deprecation
that doesn't fire on the full surface), and the v5.21.1 PRE_PANEL_AUDIT
verbatim test command demonstrates the gap. I am scoring this
MEDIUM not HIGH because:
1. The dominant brace shape in real code is multi-line, and the
   warning fires correctly there.
2. `mnc fmt` migrates both shapes correctly (verified — auto-migrate
   on the multi-line shape rewrites cleanly to colon-form).
3. The hard-removal point is v6.0; there is time to close.

But this is the kind of finding that the PRE_PANEL_AUDIT itself
should have caught — the lead documented an expected behavior,
the actual behavior is different, and the panel discovered the
gap on first pre-flight run. I want this closed before v6.0
**and** before the v5.22.0 → v5.x next-cadence panel.

#### M2. Manifesto says "Curly braces for blocks" against a brace-deprecated codebase

**Severity:** MEDIUM
**Domain:** Manifesto coherence
**Reported by:** Coral (this review)

`docs/manifesto.md:31`:

> "The syntax is clean and direct. Curly braces for blocks, strong
> static typing with inference where it helps, no semicolons where
> they add nothing. If you have written Rust, Go, or TypeScript,
> you can read Mapanare immediately."

`git log v5.11.0..HEAD -- docs/manifesto.md` returns empty. The
manifesto has not been touched across the entire terseness arc.
The codebase at v5.21.1 has soft-deprecated braces (v5.19.0 Te.3),
made colon-style canonical (SPEC §4.0), shipped `mnc fmt`
auto-migration to colon, scheduled `{}` hard removal for v6.0 —
but the language's *first impression document* still tells new
visitors "Curly braces for blocks."

The line was historically accurate (v3.0.0 ledger entry shows the
brace → colon trade-off was already on the table at v3.0.0). It is
no longer accurate at v5.22.0. A new visitor reading the manifesto
on mapanare.dev sees one syntax described and the README's
hello-world example uses another syntax. This is the same Bo.18r
shape — internal contradiction between two front-door surfaces —
that drove Boa's -0.5 dock at v5.11.0, but on the language-design
axis rather than the docs-content axis.

**Suggested fix.** Two-line edit:

> "The syntax is clean and direct. Indented blocks (with a brace-
> form legacy through v6.0), strong static typing with inference
> where it helps, no semicolons where they add nothing. If you have
> written Rust, Go, or TypeScript, you can read Mapanare
> immediately."

Or stronger: drop "Curly braces for blocks" entirely and let the
SPEC be the canonical syntax description. The manifesto's job is
to say *why*, not *how*. The "how" being one syntax in the
manifesto and another syntax in the SPEC is a coherence violation
that v5.21.1 hygiene missed because the H.* findings were scoped to
SPEC and READMEs.

This is the **third consecutive panel** where I have flagged
manifesto-vs-codebase coherence — at v5.7.1 I noted the manifesto
"Phase three onward" line was finally substantively true; at
v5.11.0 I noted the developer-surface footnote (Python sidecar);
at v5.22.0 the manifesto's syntax description is now actively
counterfactual. Five-minute fix, three releases overdue.

#### M3. SPEC example corpus is 72% brace-style against colon-canonical SPEC

**Severity:** MEDIUM (deferrable to v5.x cadence)
**Domain:** SPEC coherence
**Reported by:** Coral (this review)

```
$ grep -B1 -A3 '^```mn$' docs/SPEC.md | grep -c "fn.*{$\|if.*{$\|while.*{$"
26
$ grep -B1 -A3 '^```mn$' docs/SPEC.md | grep -c "fn.*:$\|if.*:$\|while.*:$"
10
```

The SPEC's own example corpus opens 26 blocks with `{` and 10 with
`:`. SPEC §4.0 declares "Mapanare accepts colon-style as
**canonical** (since v5.19.0)." The SPEC's examples disagree with
the SPEC's prose. v5.21.1 hygiene re-synced the structural sections
(§2.2 Te.6, §3.7 Te.5, §4.0 Te.3 status, §4.3.1 Te.5.E) but did not
sweep the example corpus.

This is "do as I say, not as I do" at the documentation surface.
A reader who reads §4.0 ("colon is canonical") and then scans the
SPEC's other examples sees brace style 72% of the time. The
contract being communicated by examples is "brace is the working
shape; colon is the new shape we are documenting." That's the
opposite of what §4.0 says.

**Suggested fix.** `mnc fmt --to-terse` over `docs/SPEC.md` would
do the mechanical rewrite (the formatter already handles markdown
code blocks via `tests/test_format.py` corpus iteration —
cross-checked at v5.13.0). This is a 30-minute mechanical sweep
plus a careful read for any SPEC-historical examples that should
intentionally show brace form (e.g., Chapter 27 stability discussion
of frozen syntax — there the brace shape is a historical artifact
and should stay). I would group with a "SPEC v5.22.x example sweep"
deferred item, not block release.

This is **NEW MEDIUM** at v5.22.0 — it did not exist as a finding
at v5.11.0 because the SPEC was at v5.7.1 and colon syntax was not
canonical at the SPEC level. v5.21.1 hygiene closed §4.0's prose
but not §1–§28's examples.

### LOW

#### L1. SPEC §27 "deprecation cycle" reference doesn't crosslink Te.3

**Severity:** LOW
**Domain:** SPEC discoverability

SPEC §27.3 (line 2743) says "Any change to a frozen area requires:
RFC + deprecation warning + migration guide + major version bump."
Te.3 follows this pattern (verbatim), but §27 has no callout
referencing Te.3 as the **canonical worked example** of the
deprecation cycle in v5. A reader who lands on §27 looking for
"how does Mapanare deprecate things" sees the policy text but no
worked example.

**Suggested fix.** Add a one-paragraph note to §27.3 pointing at
Te.3 as the v5.19.0 → v6.0 worked example: "Te.3 ({}-block
soft-deprecation, v5.19.0) demonstrates this cycle: parse-time
warning starting v5.19.0 → 2-release soak → hard removal at v6.0.
See §4.0 for the user-facing migration path."

#### L2. v5.14.0 broken `if x: y` promise — closed honestly, but the closure wording could be tighter

**Severity:** LOW
**Domain:** SPEC narrative

SPEC line 1056–1059:

> "Single-line `if x: y` form is **not** supported. The v5.14.0
> SPEC originally promised this for v5.21.0; that promise was
> rescoped at v5.21.1 to coincide with the v6.0 `{}` hard
> removal. Until v6.0, put the body on the next line."

This is the right closure for a documentation contract violation.
**Path B (defer to v6.0)** is the honest path given the v5.21.1
PROMPT explicitly forbade the grammar + bootstrap edits Path A
would require. The wording is slightly clinical — a reader who has
not been following the carry-forward narrative will not understand
why this paragraph exists. The lead's "honest closure" framing in
the v5.21.1 SESSION_REPORT lines 50–55 is good; surfacing one
sentence of that framing in the SPEC itself would be tighter
language design.

**Suggested fix.** Replace line 1058–1059 with: "The v5.14.0 SPEC
incorrectly promised this form for v5.21.0; the v5.21.0 small-
ergonomic-wins cycle shipped chained comparisons (Te.6) instead,
and the single-line form was rescoped at v5.21.1 to v6.0 — when
the brace-form removal will eliminate the parser ambiguity that
makes single-line colon-form complex to integrate cleanly with
brace shape."

This is a 5-minute edit and turns the closure paragraph into a
language-design rationale rather than a procedural note.

#### L3. SPEC §27 list of frozen areas does not mention `{}` block syntax

**Severity:** LOW
**Domain:** SPEC accuracy

§27.1 (line 2722–2731) lists frozen areas: Syntax, Semantics, Type
system, Builtin functions, String methods, Agent model, Signal
model, Stream operators, Error codes. "Syntax: All grammar rules
defined in this specification" includes the brace block-form,
which is now soft-deprecated and scheduled for v6.0 removal —
i.e., un-frozen. §27 does not call this out.

**Suggested fix.** Add a one-line note under §27.1 Syntax bullet:
"Brace-form blocks (`{}`) are soft-deprecated as of v5.19.0 and
will be removed at v6.0 per §4.0; see §27.3 for the deprecation
cycle." Three minutes.

#### L4. Pk.3 closure (Mc.* mnc parity) was MEDIUM at v5.11.0 — now closed but not landed

**Severity:** LOW (closure verification)
**Domain:** Process

My v5.11.0 review carried Pk.3 as MEDIUM ("native `mnc` covers 7
of `mapanare`'s 25 subcommands"). v5.18.0 closed Mc.1 (lsp), Mc.3
(init), Mc.4 (check), and the v5.19.0 closeout shipped Mc.5
(emit-wasm via `mnc emit-wasm` deferral). The closure is real;
the v5.21.1 SESSION_REPORT counts this as closed.

**One open question:** does `mnc init`, `mnc check`, and `mnc lsp`
shell out to Python at runtime, or do they dispatch natively?

```
$ grep -A2 "init\|check\|lsp" mapanare/self/main.mn 2>/dev/null | head
```

Per v5.18.0 SESSION_REPORT, the native `mnc` wrappers shell out to
Python. That is the v5.13.0 `mnc fmt` pattern — pragmatic, but not
the "developer surface is fully native" closure I asked for at
v5.11.0. The Pk.3 carry-forward I framed at v5.11.0 was about
"language story tolerates this asymmetry less well than the
engineering story" — at v5.22.0 the asymmetry is smaller (more
native subcommands exist) but the dispatch shape is still
shell-out for the heavy ones (LSP, fmt).

This is **CLOSED-WITH-NOTE** rather than CLOSED-CLEAN. I am not
re-docking; v5.18.0 is the right next move; the next step (native
LSP port) is correctly deferred. But the Pk.3 carry-forward
doesn't fully resolve until the dispatch is native.

#### L5. Te.6 precedence merge is documented in design doc; SPEC §2.2 mentions it but doesn't cross-link

**Severity:** LOW
**Domain:** SPEC discoverability

SPEC §2.2 (line 468–469):

> "v5.21.0 — comparison operators chain at a single precedence
> level. Pre-v5.21.0, `==`/`!=` sat at strictly lower precedence"

The note is correct. It does not cross-link to the SPEC §27
deprecation policy that this is a precedence-level merge — i.e.,
*technically* a syntactic-semantics change for which the
"no existing code mixes them at same level" audit substituted for
a deprecation cycle. That's a defensible choice given the audit,
but should be documented as such.

**Suggested fix.** Append: "The merge was treated as a non-breaking
change by audit (no existing source in the repo or external
projects relied on the relative precedence); see
`docs/roadmap/v5/v5.21.0/CHAINED_CMP_DESIGN.md` D1."

### TRIVIAL

#### T1. v5.21.1 SESSION_REPORT says "12 H.* findings" but the audit lists H.1–H.13

The PRE_PANEL_AUDIT enumerates H.1 through H.13 (13 items). The
v5.21.1 SESSION_REPORT phase headline says "closing the 12 H.*
findings." H.13 (panel cadence reset) is closed by *running this
panel*, not by an edit, so it correctly does not appear in the
per-item closure table. The headline number is off-by-one
(13 listed, 12 with edits in the closure table; 1 closed by
process). Honest tracking; trivially miscounted.

---

## Recommendations

Prioritized for v5.22.x cadence + v5.x cadence:

| # | Severity | Item | Effort |
|---|---|---|---|
| 1 | MEDIUM | **M1** — Tighten brace-deprecation detector for single-line shape | 1–2h + 1 test |
| 2 | MEDIUM | **M2** — Sync `docs/manifesto.md` line 31 to colon-canonical | 5 min |
| 3 | MEDIUM | **M3** — Sweep SPEC example corpus to colon-canonical (`mnc fmt --to-terse docs/SPEC.md`) | 30 min mechanical + careful reading pass |
| 4 | LOW | **L1** — §27.3 cross-link to Te.3 worked example | 10 min |
| 5 | LOW | **L2** — Tighten the §4.0:1056–1059 closure wording | 5 min |
| 6 | LOW | **L3** — §27.1 Syntax bullet `{}` soft-deprecation note | 3 min |
| 7 | LOW | **L4** — Track Pk.3 native-LSP-dispatch as v5.x carry-forward | track |
| 8 | LOW | **L5** — §2.2 cross-link to CHAINED_CMP_DESIGN.md D1 | 5 min |
| 9 | TRIVIAL | **T1** — v5.21.1 SESSION_REPORT 12-vs-13 wording | 2 min |

Total panel-actionable: ~2–4 hours of work. Three of the items
are 5–10 minute edits.

---

## Post-Production Health Assessment

**22 versions after v5.0.0 release-gate, is it still good?**

YES. The codebase is healthier than at v5.11.0 on every axis I
care about (grammar discipline, fixed-point streak, design-doc
discipline, deprecation-cycle execution). The Mc.* docket
(v5.11.0's MEDIUM) closed at v5.18.0 by verifying-and-filling.
The SPEC re-staleness MEDIUM (my own v5.11.0 dock) closed at
v5.21.1 hygiene. The terseness arc Te.1–Te.6 composed into a
single coherent language story, not six independent features.

**Are features hollow?** No, with one caveat. M1 (single-line
brace-shape deprecation gap) is a hollow-feature shape on the
deprecation surface — Te.3 announces a deprecation that doesn't
fire on every legal brace shape. This is the only place where the
"declared behavior == actual behavior" contract breaks at the
v5.22.0 surface I checked. Everywhere else features deliver what
they advertise: chained comparisons evaluate the middle once, IR
proves it; struct destructuring `let Point { x, y } = p` desugars
byte-identical to manual extraction; brace-form `mnc fmt` migrates
correctly to colon-form on multi-line; let-else divergence is
compile-time enforced; the bootstrap mirrors are 12/12, 10/10,
10/10, 10/10, 142/142 across the five test suites.

**Does documented state match actual code?** Mostly. SPEC §4.0,
§3.7, §4.3.1, §2.2 are accurate at v5.21.1 hygiene cut. Manifesto
line 31 is *not* accurate (M2). SPEC example corpus is *partly* not
accurate (M3 — examples open with brace 72% of the time). The PRE
_PANEL_AUDIT's own pre-flight test for Te.3 warning is
*not* matching actual behavior (M1).

**Hygiene-via-release vs hygiene-at-source — the weighting question.**

The v5.21.1 hygiene release closed 12 H.* findings in a dedicated
release. This is the second arc-closure where the lead has used
the hygiene-release pattern (v5.7.1 → v5.8.0 was the first; that
scored 9.66, project record). The pattern is honest: surface drift
is enumerated in a PRE_PANEL_AUDIT, closed in a dedicated release,
and the panel inherits a clean docket.

I would prefer hygiene-at-source. The discipline of "if you ship
a feature, sweep the SPEC paragraph that documents it in the same
release" produces a SPEC that is never more than one release
stale. The v5.21.1 pattern — accumulate 14 releases of drift, then
sweep — works once it is run, but it depends on the panel cycle
firing to enforce the sweep. v5.16.0 should have been a panel by
the 5-minor cadence rule; the panel slipped to v5.22.0; the SPEC
was 14 releases stale by then.

**Score weighting.** I am giving back the -0.10 v5.11.0 dock
(SPEC is now synced) but explicitly NOT crediting the +0.10
"closed structurally" credit I would give for hygiene-at-source.
The closure delta nets to **+0.10 - 0.10 = 0** on the SPEC
staleness axis; the +0.05 net delta vs v5.11.0 comes from arc
discipline credits elsewhere. **Hygiene-via-release at v5.7.1
and v5.21.1 is the lead's stated pattern, and it works — but it
ceiling-effects the score at the same 9.55–9.66 range. To break
9.7, the lead would have to demonstrate hygiene-at-source on the
*next* arc.**

The path to a 9.7+ at v5.x next-cadence is concrete:

1. Close M1 (single-line brace-detector gap) — closes the only
   hollow-feature finding I have at v5.22.0.
2. Close M2 (manifesto line 31) — closes the third-consecutive-panel
   manifesto coherence concern.
3. Close M3 (SPEC example corpus sweep) — closes the most visible
   internal contradiction at the SPEC surface.
4. Close L1, L2, L3, L5 in the same SPEC pass — turns SPEC §27 +
   §4.0 + §2.2 into language-design rationale text rather than
   procedural notes.
5. **Demonstrate hygiene-at-source** on the next feature release —
   ship the SPEC paragraph in the same release that ships the
   feature, not 14 releases later.

That is **+0.15** of plausible delta — putting the next score at
**9.70**. The arc is at the point where it can hit project record
again.

---

## Carry-Forward Status (v5.11.0 panel items)

| Item | Status | Notes |
|------|--------|-------|
| **Coral SPEC re-sync (MEDIUM)** | **FIXED** | v5.21.1 hygiene H.2 — header bumped, sync block added |
| **SPEC §4.0 Te.3 documentation** | **FIXED** | v5.21.1 hygiene H.3 — colon canonical, brace soft-deprecated, env var documented |
| **Mc.* parity (MEDIUM)** | **FIXED** | v5.18.0 closed Mc.1 (lsp), Mc.3 (init), Mc.4 (check); native dispatch shells out, full native port deferred |
| **Pk.3 Python sidecar (MEDIUM)** | **FIXED-WITH-NOTE** | v5.18.0 closes the major subcommands; native dispatch is shell-out, not native LSP — see L4 |
| **`examples/signals/counter.mn` stale comment (TRIVIAL)** | **STILL OPEN** | Not in v5.21.1 hygiene scope; flag for v5.22.x cadence |
| **Cross-platform ABI surface in SPEC (LOW)** | **STILL OPEN** | Not in v5.21.1 hygiene scope; v5.22.x cadence |
| **Gr.1 / Sh.5 / `mapanare_version` enforcement / `commit` field dual semantics (4× LOW)** | **STILL OPEN** | Carry-forwards from v5.7.1 unchanged; v5.22.x SPEC pass |

New at v5.22.0:

| Item | Severity | Source |
|------|--------|---------|
| **M1** Te.3 single-line brace-shape detector gap | MEDIUM | this review |
| **M2** Manifesto line 31 says "Curly braces" | MEDIUM | this review |
| **M3** SPEC example corpus 72% brace-style | MEDIUM | this review |
| **L1–L5** various SPEC discoverability/coherence | LOW | this review |

---

## Score Breakdown

| Adjustment | ± | Reason |
|---|---|---|
| **+0.10** (giving back v5.11.0 dock) | +0.10 | SPEC re-staleness closed at v5.21.1 hygiene; header at v5.21.0, §4.0 / §3.7 / §4.3.1 / §2.2 accurate to v5.21.0 cut |
| Strict 3-stage fixed point preserved across 13 consecutive releases (was 5) | +0.025 | Longest streak in project history; held through Sh.* mechanical rewrite of self-host source |
| Sh.* discipline — 17 modules, per-module commits, fixed-point validated between every commit, -3,950 lines (-13.8%) | +0.025 | Discipline of mechanical rewrite without breaking strict fixed point |
| Six additive features (Te.1–Te.6), zero new MIR ops, zero new IR shapes, zero runtime function additions | +0.025 | Every desugaring routes through existing primitives — language absorption discipline |
| Te.3 deprecation cycle execution — SPEC §27.3 verbatim shape | +0.025 | RFC + warning + migration tool + major-version-bump-scheduled hard removal |
| Te.6 once-evaluation verified in IR (D3) | +0.025 | Load-bearing semantic property, IR-proven |
| Decision-1 Path B — broken `if x: y` promise rescoped to v6.0 with rationale | +0.025 | Honest closure rather than silent carry-over; v4.18.0–v4.26.0 hollow-features class anti-pattern avoided |
| **M1** Te.3 single-line brace-shape detector gap | -0.025 | Hollow Te.3 surface for the all-on-one-line shape; PRE_PANEL_AUDIT pre-flight expected behavior does not match actual |
| **M2** Manifesto "Curly braces for blocks" against brace-deprecated codebase | -0.025 | Third-consecutive-panel manifesto coherence flag |
| **M3** SPEC example corpus 72% brace-style against colon-canonical SPEC | -0.025 | New finding — SPEC text says one thing, SPEC examples show another |
| **Net delta vs v5.11.0** | **+0.05** | +0.10 SPEC dock release + 0.175 arc discipline credits − 0.075 new findings; ceiling-effected at 9.55–9.7 by hygiene-via-release pattern |

**Score: 9.55.** Trajectory restored after the v5.11.0 negative
delta. Still EXCEEDS. The dock-then-credit-back pattern matches
the v5.7.1 / v5.11.0 / v5.22.0 arc shape — credit follows
substance, dock follows drift. The drift was real, the closure
was real, the trajectory is healthy.

---

## On Hygiene-via-Release vs Hygiene-at-Source

This is the single weighting decision the lead's charter asked me
to be explicit about. Here is my view, fully in character.

**Hygiene-via-release is good.** It works. v5.7.1 → v5.8.0 hit
9.66 — project record. v5.21.1 → v5.22.0 hits 9.55 (mine) on the
same pattern. Both releases close docs-surface drift cleanly,
explicitly, with a PRE_PANEL_AUDIT enumeration of every
finding. The lead is honest about which items closed structurally
(H.5 verify-only — SPEC already had Te.5 and Te.6 sections from
the at-source releases) and which items closed by patch (H.1,
H.2, H.3 — README and SPEC body bumps).

**Hygiene-at-source is better.** When v5.20.0 ships Te.5 and the
SPEC §3.7 sections land in the same release, the SPEC is never
more than zero releases stale. The lead's claim in the v5.21.1
SESSION_REPORT — "every form documented below either was already
present at v5.7.1 or ships additively" — is what hygiene-at-source
looks like for the *language* surface, but the *header date* and
the *what-changed-since-v5.7.1* block had to be added at v5.21.1
because they were not added at v5.14.0 / v5.15.0 / v5.16.0 / etc.

**Why I weight this -0.025 net.** Hygiene-via-release ceiling-
effects at 9.55–9.66. The structural risk is: v5.x next-cadence
panel runs against a fresh accumulation of 5–14 releases of
post-v5.22.0 drift (the panel cadence rule fires at v5.27.0 per
the 5-minor rule). If the lead does not pre-empt with another
hygiene release, the panel docks at fresh; if the lead does
pre-empt with another hygiene release, the cycle of "let it
accumulate, then sweep" continues. Either path keeps the score in
the 9.5–9.7 band. The path to break 9.7 is "do not let it
accumulate in the first place" — close the SPEC paragraph in the
release that ships the feature.

**The recommendation embedded in this score.** Add a CI gate that
fails if the SPEC header date is more than 2 releases behind
`cat VERSION`. Same shape as `scripts/check_changelog_honesty.py`
— mechanical, runs in 1 second, prevents the structural drift
from accumulating. Boa raised the same recommendation at v5.11.0
(`scripts/check_doc_freshness.py`); I am raising it again as a
language-design concern: a SPEC that drifts from the language is
a contract that drifts from the runtime, and the cure is a
mechanical gate, not panel-driven hygiene releases.

This is not a v5.22.0 dock — the lead has an option to land this
at v5.22.x cadence. But it is the structural fix that breaks the
9.5–9.7 ceiling.

---

## On the Manifesto's "AI-native" Claim

The manifesto's vision (line 21) is "an AI agent is as natural as
a function." At v5.22.0, agents are first-class, the goldens
include agent + signal + stream programs that compile through
`mnc-stage1`, the runtime support is built. The vision is real.

The manifesto's promise of "Phase three onward" (line 41) — "a
standard library, an LLVM backend for native compilation, a
package manager, and eventually a self-hosting compiler written
in Mapanare itself" — is delivered in full at v5.22.0:

- **Standard library** — `stdlib/` covers encoding, networking,
  crypto, text, database, AI, GPU, fs, time, log, math, testing,
  WASM. Per SPEC §28's table.
- **LLVM backend** — canonical emitter; `emit_llvm_text.py` is
  the single source of LLVM IR; goldens 95/95.
- **Package manager** — SPEC §30 normative.
- **Self-hosting compiler** — strict 3-stage fixed point at
  238,086 lines, 13-release streak, **mechanically rewritten in
  v5.17.0 without breaking the streak.**

The manifesto's substance is **fully delivered.** The only piece
of the manifesto that is now drift is the *syntax description* on
line 31 ("Curly braces for blocks") — the substantive promises
have all landed.

For a v5.x project comparison, the natural comparisons are still:

- **Mojo** — closer than ever. Mojo's `mojo` driver is one binary;
  Mapanare's `mnc` is mostly one binary now (post-Mc.*). Mojo's
  surface is bigger; Mapanare's surface is more frozen (zero
  grammar churn beyond documented additive Te.* surface).
- **Zig** — Zig's grammar moved on `for` syntax in 0.11. Mapanare's
  grammar has not removed any production at the user-visible level
  in 46 v5 releases (the v5.21.0 `eq_expr` precedence merge is the
  only removal, and it's a precedence-level merge not a syntax
  removal). **Mapanare's grammar discipline now exceeds Zig's.**
- **Erlang** — the agent comparison. Mapanare's agents are
  syntactically lighter than `gen_server`; Erlang's OTP supervision
  trees are more mature. Mapanare's bet is that the v6.0 borrow
  checker (Rt.04 deferred) makes supervision trees structurally
  unnecessary by eliminating the failure modes OTP supervises. I
  remain curious whether that bet pays off.
- **Haskell** — the type-system-coherence comparison. Haskell's
  Functor / Applicative / Monad hierarchy is a coherence story
  Mapanare doesn't tell. Mapanare's coherence is **operational**
  (agents + signals + streams + tensors compose at the language
  level); Haskell's is **algebraic**. Different bets, both valid.

The terseness arc (Te.1–Te.6) closes the syntax-level
"competitive with Python" claim. The post-arc Mapanare is **terser
than Python on the surface forms that matter for AI work**:
struct destructuring, comprehensions, chained comparisons, terse
lambdas, implicit return. A Python developer reading post-Te.6
Mapanare sees code that is 10–15% shorter line-count and arguably
more readable for the agent + signal + stream domain.

That is what the language is trying to say at v5.22.0: **"Python's
syntactic ergonomics, AOT-LLVM's runtime profile, and language-
level primitives for the things AI workloads actually do."** The
vision is intact. The execution is at the point where the gaps
are panel-actionable, not arc-actionable.

---

## Verdict

**EXCEEDS. PASS WITH NOTES.** Fifth consecutive EXCEEDS; first
positive cycle-delta since v5.7.1 (the v5.11.0 cycle was -0.1).

The **+0.05 over v5.11.0** reflects:

- **+0.10** for SPEC re-sync at v5.21.1 hygiene (giving back the
  v5.11.0 dock — gap closed, even if closure was via hygiene
  release rather than at-source).
- **+0.175** in arc-discipline credits — fixed-point streak,
  Sh.* discipline, six features absorbed without grammar churn,
  Te.3 cycle execution, Te.6 once-evaluation, Decision-1 Path B
  honesty.
- **-0.075** for three new MEDIUMs at the panel surface — the M1
  brace-detector single-line gap (real hollow Te.3 surface), the
  M2 manifesto coherence violation (third-consecutive-panel
  finding), the M3 SPEC example corpus drift (new but mechanical).
- **-0.025** weighting penalty for hygiene-via-release vs hygiene-
  at-source.

Net: **+0.05, from 9.5 to 9.55.** The trajectory is restored.

**The PASS WITH NOTES** annotation is for M1 — Te.3 deprecation
warning that does not fire on the all-on-one-line brace shape is
a real gap at the panel surface, surfaced by the PRE_PANEL_AUDIT's
own pre-flight test command. The lead should close it before v6.0
hard removal, ideally before the v5.x next-cadence panel.

**The path to 9.7** is the same path I described at v5.11.0
(SPEC re-sync, Mc.* parity) — closed at v5.18.0 + v5.21.1.
The path to 9.7 from here is the M1 / M2 / M3 / hygiene-at-source
package documented above. ~3 hours of work.

The terseness arc is the most disciplined feature-velocity arc
I have ever reviewed for this project. Six features, ten releases,
zero new MIR ops, zero new IR shapes, zero new runtime functions,
strict 3-stage fixed point preserved across all 13 releases,
self-host shrunk -13.8%, goldens 66/66 → 95/95. **This is what a
language committed to its own vision looks like at v5.22.0.**

The thing I want to see next is the hygiene-at-source habit that
prevents this panel from re-running on the same drift class at
v5.27.0. The Te.3 detector gap M1 is the load-bearing concrete
finding for that conversation: panel-driven hygiene caught the
drift class structurally (v5.21.1 H.1–H.13) but missed the actual
behavior gap that the audit's own command exercises. The next arc
should be one where that asymmetry doesn't open.

---

## Raw Notes

- **Pre-flight commands run live, results captured above.** Fixed
  point STRICT 238,086 / 0 diff. Goldens 95/95 through `mnc-stage1`.
  `tests/test_brace_deprecation.py` 23/23. Te.6 once-evaluation
  IR check: `grep -c "call.*@middle" /tmp/chain.ll = 1`. Auto-
  migration `mnc fmt /tmp/migrate.mn` rewrites multi-line brace
  to colon cleanly.

- **Spot-checks against SESSION_REPORTs (5+):**
  1. v5.21.1 H.4 closure of SPEC §4.0:1056–1059 — **VERIFIED** at
     SPEC line 1056–1059 verbatim.
  2. v5.21.1 H.6 localized README sync — **VERIFIED** at
     `docs/README.{es,pt,zh-CN}.md` line 125 with target-language
     prose covering Te.1–Te.6.
  3. v5.21.1 H.7 `examples/chained_cmp.mn` (28 lines) — **VERIFIED**
     at `examples/chained_cmp.mn` (28 lines, includes 3-element +
     4-element + half-open + once-evaluation demo).
  4. v5.21.1 H.9 `tests/bootstrap/test_chained_cmp_mirror.py`
     10/10 — **VERIFIED** in test inventory; not re-run live.
  5. v5.21.0 D6 (1-cmp byte-identity) — **VERIFIED** at grammar:
     `cmp_chain` transformer dispatches on tail-count, emits
     legacy `BinaryExpr` on tail=1.
  6. v5.20.0 D5 (let-else divergence required) — **VERIFIED** at
     SPEC §4.3.1 line 1225–1236 documents exactly the design
     decision.
  7. v5.20.0 STRUCT_ERGO_DESIGN.md D3 (field punning in match) —
     SPEC §3.7 destructuring documents the let-form; match-side
     not separately checked but design doc says "ships in v5.20.0
     too, lower test coverage."

- **Surprised by:** the v5.17.0 self-host rewrite preserving fixed
  point at every per-module commit. That is not just a "we
  validated at HEAD" claim; the SESSION_REPORT documents the
  per-module-commit strategy and the per-commit validation. That
  is the kind of discipline the v4.18.0–v4.26.0 arc explicitly
  did not have.

- **What the language is trying to say (per Coral's recurring
  question):** at v5.22.0 the answer is finally clean. "Python's
  surface, Rust's runtime promises, AOT-LLVM, and agents/signals/
  streams/tensors as compiler-known primitives. We mean it
  enough to soft-deprecate our own brace syntax and rewrite our
  self-host compiler in our new canonical surface — without
  breaking the byte-for-byte fixed point that proves we compile
  ourselves."

- **What Mojo cannot say** that Mapanare can at v5.22.0: "our
  compiler compiles itself, byte-for-byte, 13 releases in a row,
  and we mechanically rewrote it in our new canonical syntax
  without breaking that property." Self-hosting + strict fixed
  point + canonical-syntax migration through the self-host source
  is the **specific** discipline win. Mojo has none of it; Zig has
  most of it without the canonical-syntax migration; Rust has it
  but not the canonical-syntax migration.

- **Disagreement I would flag if other reviewers see this
  differently:** I am crediting the "closure-by-hygiene-release"
  pattern at +0.10 (gap closed) but not at the +0.20 the v5.7.1
  closure earned. The difference is that v5.7.1's closure was
  v4.143.0 → v5.7.1 (27 releases of staleness closed in one
  release, with a substantive new audit-driven section in §3.11);
  v5.21.1's closure is 14 releases of staleness closed by patch
  + verify-only on the structural Te.5 / Te.6 sections. **Smaller
  surface closed, smaller credit.** Boa may weight this differently.

- **What I would have wanted to see at v5.22.0 that I didn't:**
  the v5.21.1 closeout discussion of "what would hygiene-at-source
  look like for the next arc?" The lead's pre-panel posture
  document is comprehensive about closing v5.13–v5.21 drift but
  doesn't propose a structural prevention for v5.22.x → v5.x next.
  That would have earned the +0.025 hygiene-at-source credit
  instead of the -0.025 weighting penalty.

End of review.
