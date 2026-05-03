# v5.17.1 — Sh.C + Sh.D + Sh.G — terse polish

**Status:** PLANNING
**Breaking:** No semantic change. Output IR must remain
byte-identical to v5.17.0 modulo whitespace in metadata strings,
i.e. **strict 3-stage fixed point preserved**.
**Prerequisite:** v5.17.0 shipped (mechanical colon-block rewrite
of `mapanare/self/`, bootstrap seed refresh, validation, minimal
docs).
**Estimated effort:** 5–8h, two sessions. Most of the work is
per-site judgment, not bulk rewriting.

---

## Why this exists

v5.17.0 ships `mapanare/self/` in colon-block form — the
mechanical brace → colon conversion. That's the headline change of
the terseness arc, but it leaves two upgrade patterns untaken:

1. **Verbose accumulator loops** that should be comprehensions.
   The mechanical `--to-terse` only rewrites block braces; it
   doesn't introduce new expressions. `let r = []; for x in xs:
   r.push(f(x)); return r` stays verbose even after Sh.B.

2. **The `let r: T = x; return r` constructor pattern.** Pervasive
   in `ast.mn`, `mir.mn`, `lower_state.mn` because the bootstrap
   grammar didn't support struct literal syntax for years; almost
   every constructor function is `fn make_thing(args) -> Thing { let
   r: Thing = first_field; ...; return r }`. v5.15.0 Te.2.D shipped
   block-form implicit return (last-expr-as-result, SPEC §4.5),
   so most of these can drop to `fn make_thing(args) -> Thing { ...;
   first_field }` or even `fn make_thing(args) -> Thing = first_field`
   for one-liners.

Both upgrades are visible to anyone reading the compiler source —
they're the difference between "Mapanare uses colon blocks" and
"Mapanare reads idiomatically." v5.17.1 is the small follow-up
release that closes the gap.

The SPEC and README examples also still show v5.13-era brace
syntax. v5.17.1 refreshes them to match what the compiler now
actually looks like.

---

## Goal

1. Apply loop → comprehension upgrades wherever the rewrite is a
   clear win (judgment call documented per site in
   SESSION_REPORT).
2. Apply trailing-`return r` → implicit-return upgrades wherever
   they don't lose readability.
3. Refresh `docs/SPEC.md` and `README.md` examples to terse +
   idiomatic style (comprehensions, implicit return where
   appropriate).
4. Goldens 80/80 throughout.
5. Strict 3-stage fixed point preserved (the v5.9.0 milestone,
   held since v5.9.0 except for the v5.16.0 4-line metadata
   diff, restored to 0 at v5.17.0).
6. Total `mapanare/self/*.mn` line count: aim for **another
   ~5%** shrink on top of v5.17.0's 13.2%, putting the v5.13.0 →
   v5.17.1 cumulative shrink in the **17–20%** range.

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Sh.C.A** | LOW | Survey: grep for accumulator loop patterns in `mapanare/self/*.mn`. Categorize candidates as CLEAR-WIN / MAYBE / SKIP. Write `COMPREHENSION_SITES.md`. | 1h |
| **Sh.C.B** | MEDIUM | Apply CLEAR-WIN comprehension upgrades. One commit per site. Validate stage1 + goldens between commits. | 2h |
| **Sh.D.A** | LOW | Survey: grep for `let r: T = X; return r` patterns and `let r: T = X; ...; return r` (multi-stmt constructor). Categorize. Write `IMPLICIT_RETURN_SITES.md`. | 1h |
| **Sh.D.B** | MEDIUM | Apply implicit-return upgrades. One commit per site (or per cluster of similar sites in the same file). Validate stage1 + goldens between commits. | 2h |
| **Sh.G.A** | LOW | Refresh `docs/SPEC.md` examples to terse style. | 1h |
| **Sh.G.B** | LOW | Refresh `README.md` first-impression example to terse style. | 0.5h |
| **Sh.G.C** | LOW | Update `CLAUDE.md`'s release-notes preamble. | 0.5h |

---

## Phase plan

### Phase 0 — Survey

For Sh.C, search for the accumulator-loop pattern:

```mn
let mut r: List<T> = []          // or `let r: List<T> = []` for non-mut
for x in xs:                     // or `for x in 0..len(xs)` style
    [ if cond: ]                 // optional filter
        r.push(f(x))             // or `r.push(x)`
return r
```

Tools:

```bash
# Direct push-loop pattern
grep -nA3 "let.*: List<.*> = \[\]" mapanare/self/*.mn |
  grep -B1 "\.push(" | head -40

# Range-based variant
grep -nB1 -A4 "for .* in 0\.\.len" mapanare/self/*.mn | head -40
```

For each match, decide:

- **CLEAR-WIN**: single push, simple transform, no side effects,
  result-list-only output → comprehension.
- **MAYBE**: minor side effect or readability trade-off → flag for
  case-by-case judgment.
- **SKIP**: multi-output / break / continue / complex transform /
  the index `i` is reused after the loop / mutation of state-
  threading variables (`s = ...`) → leave verbose.

For Sh.D, search for the trailing constructor pattern:

```bash
grep -nB1 -A3 "let r:" mapanare/self/*.mn |
  grep -A1 "let r:" | head -40
```

Patterns to look for:

```mn
fn make_X(...) -> X {
    let r: X = first_field           // ① simple assignment, no other body
    return r                          // → drop to `let r: X = first_field`
}                                     //   then drop trailing `return r` → bare expr
                                      //   then drop to fn-init form
                                      //   `fn make_X(...) -> X = first_field`

fn make_X(...) -> X {
    do_setup()                        // ② side-effect prelude
    let r: X = first_field
    return r                          // → drop to bare `first_field` (block-form)
}

fn make_X(...) -> X {
    let mut r: X = ...                // ③ r mutated in body
    r.field = ...                     // → cannot use one-liner; keep block form
    return r                          //   may still drop trailing `return r`
}                                     //   if the last statement evaluates to r
```

For each match, decide CLEAR-WIN / MAYBE / SKIP. Document in
`IMPLICIT_RETURN_SITES.md`.

Out-of-scope for upgrade:

- Functions that have multiple `return` statements in the body
  (block-form implicit return is conservative — opt-in by ABSENCE
  of explicit return).
- Functions where the trailing `return r` follows a loop or match
  whose tail might NOT terminate cleanly (would change the implicit-
  return semantics — easy to reason about it but easier still to
  skip).
- Functions where the explicit `return r` documents the return
  type for callers reading the local file (judgment call).

### Phase 1 — Apply comprehension upgrades

One commit per CLEAR-WIN site. After each commit:

```bash
python scripts/build_stage1.py
python scripts/test_native.py --stage1 mapanare/self/mnc-stage1
bash scripts/verify_fixed_point.sh
```

Stage1 must build green, goldens must stay 80/80, fixed point
must stay strict. If any of these fail, **revert the commit**, mark
the site as SKIP in `COMPREHENSION_SITES.md`, continue with the next
site.

Commit-message form:

```
v5.17.1 Sh.C.B: comprehension in <module>::<fn>
```

### Phase 2 — Apply implicit-return upgrades

Same gating as Phase 1. Cluster similar sites in the same file
into a single commit if they're truly mechanical (e.g.,
`ast.mn` has ~30 constructor functions following the same shape
— one commit can cover all of them as long as each is a clean
drop).

Commit-message form:

```
v5.17.1 Sh.D.B: implicit return in <module> (<n> sites)
```

### Phase 3 — Documentation refresh

#### Sh.G.A — SPEC.md

Walk every code example in `docs/SPEC.md`. For each, decide:

- Use colon-block syntax (mandatory — that's the canonical form).
- Use comprehensions where the example would naturally read better
  with one (e.g., a `map`-equivalent example).
- Use implicit return for one-liner constructors and short
  functions (the original SPEC examples use `return` explicitly
  even for `fn add(a, b) -> Int = a + b`-shaped functions).
- Keep brace style for any example that's specifically illustrating
  brace-vs-colon (none expected, but check).

Run `mapanare check` on every example to confirm it parses post-
edit (the SPEC has cross-reference tests at
`tests/spec/test_spec_compliance.py` that exercise this).

#### Sh.G.B — README.md

The README's flagship "Hello, world" / first example is the user's
first impression. Make it as terse as practical: colon-block,
comprehension if natural, implicit return.

Don't over-tighten — readability for someone who has never seen
Mapanare before still trumps line count.

#### Sh.G.C — CLAUDE.md

Update the release-notes preamble:

- Add the v5.17.1 entry (matching the existing format).
- Update the v5.17.0 entry from "ready, not tagged" to "shipped".
- Update the "Current baseline" line to reflect the new line count.
- Update the "Planned / in-progress" section to mark v5.17.0 and
  v5.17.1 as shipped, push the open arc forward.

### Phase 4 — Final validation

```bash
python scripts/build_stage1.py
python scripts/test_native.py --stage1 mapanare/self/mnc-stage1 -v
bash scripts/verify_fixed_point.sh
bash scripts/build_from_seed.sh
python -m pytest tests/ -v
make lint
```

All must pass.

### Phase 5 — Closeout

Write:

```
docs/roadmap/v5/v5.17.1/COMPREHENSION_SITES.md
docs/roadmap/v5/v5.17.1/IMPLICIT_RETURN_SITES.md
docs/roadmap/v5/v5.17.1/SESSION_REPORT.md
```

Update:

```
docs/SPEC.md            # examples in idiomatic terse style
README.md               # flagship example refresh
CLAUDE.md               # version preamble + roadmap update
CHANGELOG.md
```

SESSION_REPORT includes:

- Number of comprehension upgrades applied (and skipped, with
  reasons grouped by category).
- Number of implicit-return upgrades applied (one-liner form vs
  block-form, count for each).
- Per-module line-count delta from v5.17.0 to v5.17.1, with
  cumulative line-count from v5.13.0 → v5.17.1.
- Stage2/3 fixed-point byte-diff (should still be 0).
- Goldens result (80/80).
- Build-from-seed result.

---

## Risk register

| Risk | Likelihood | Mitigation |
|---|---|---|
| Comprehension upgrade changes MIR shape, breaks fixed point | MEDIUM | The v5.15.0 comprehension lowerer synthesizes the SAME loop nest the manual version uses (mod SSA naming); fixed point should hold. If it doesn't, the divergence is in lowerer determinism — debug there, not in the rewrite. |
| Implicit-return drop changes IR | LOW | Block-form `let r = x; return r` and bare `x` lower to identical MIR (the lowerer treats trailing-expr-as-return identically to explicit `return`). One-liner `fn f() -> T = expr` lowers to `Block([ReturnStmt(expr)])` at parse time, also identical. |
| Multiple-return functions accidentally upgraded | MEDIUM | Enforce: only upgrade fns with EXACTLY ONE `return` statement and that statement is the LAST. Phase 0 survey catches multi-return cases as SKIP. |
| Reviewer fatigue produces line-count drop without quality drop | LOW | Per-commit upgrade structure means each site is reviewed in isolation. SKIP is cheap; over-aggressive rewriting is expensive. |
| SPEC examples post-edit don't compile | LOW | `tests/spec/test_spec_compliance.py` and `tests/spec/test_spec_crossref.py` validate every code block. Run before declaring Sh.G.A done. |

---

## Out of scope (deferred)

- Deprecating `{}` syntax → **v5.19.0 Te.3**
- Rewriting `examples/` → **v5.19.0 Te.3.D** (alongside soft-
  deprecation; examples should switch wholesale, not in pieces).
- Rewriting `mapanare/*.py` (the bootstrap Python compiler) — it's
  Python.
- Rewriting `tests/` and `stdlib/` — out of the v5.17.x scope; if
  there's appetite, slate as v5.18.x or later.
- Compile-time speed regression analysis for comprehensions vs
  manual loops — they should produce identical MIR; if they
  don't, the lowerer needs work, not this release.
- Struct ergonomics (field shorthand, struct update) → **v5.20.0
  Te.5** (intentionally separate — those can't be auto-migrated
  by `--to-terse`, so they're opt-in for humans).

---

## Success criteria

- Comprehension upgrades applied at every CLEAR-WIN site.
- Implicit-return upgrades applied at every CLEAR-WIN site.
- Goldens 80/80 pass.
- Strict 3-stage fixed point preserved (line count + diff stays
  zero).
- `bash scripts/build_from_seed.sh` works.
- SPEC.md and README.md examples in idiomatic terse style and
  parse via `mapanare check`.
- `make lint` clean.
- SESSION_REPORT documents per-site decisions and cumulative
  line-count reduction from v5.13.0.
