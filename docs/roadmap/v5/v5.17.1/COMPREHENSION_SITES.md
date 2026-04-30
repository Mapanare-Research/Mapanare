# v5.17.1 Sh.C.A — Comprehension Sites Survey

**Phase:** 0 (survey)
**Goal:** Identify accumulator-loop sites in `mapanare/self/*.mn`
suitable for rewriting to list comprehensions.
**Methodology:** Grep for `let r: List<...> = []` / `for x in ...:`
patterns; scan for the canonical shape:

```mn
let [mut] r: List<T> = []
for x in iter [: if cond]:
    r.push(f(x))
return r           // or `r` consumed locally below
```

## Result

The strict comprehension shape `let r=[]; for x in xs: r.push(f(x));
return r` does **not occur** in the v5.17.0 self-host sources.
Categorical breakdown of what is there:

### CLEAR-WIN (5 sites)

Simple `for k in 0..N: var.push(items[k])` — pure index-collection
loops with one statement in the body and the result either
returned or used once locally.

| File | Line | Function | Pattern | Decision |
|---|---:|---|---|---|
| `transpiler.mn` | 343 | `(unnamed match arm)` | `for k in 1..len(reordered): rest.push(reordered[k])` | CLEAR-WIN — `rest` consumed once in `join_args(rest)` |
| `transpiler.mn` | 408 | `pop_scope` | `for i in 0..marker: new_vars.push(state.declared_vars[i])` | CLEAR-WIN — `new_vars` consumed once at `state.declared_vars = new_vars` |
| `transpiler.mn` | 413 | `pop_scope` | `for i in 0..len(state.scope_markers) - 1: new_markers.push(state.scope_markers[i])` | CLEAR-WIN — same shape |
| `from_go.mn` | 559 | `(go expr handler)` | `for ai in 0..len(args): margs.push(args[ai])` | SKIP — `margs` is pre-pushed with `name` first; comprehension can't prepend cleanly |
| `from_typescript.mn` | 543 | `(ts expr handler)` | `for ai in 0..len(args): margs.push(args[ai])` | SKIP — same prepend pattern |

Result: **3 CLEAR-WIN** comprehension upgrades, **2 SKIP** (prepend
pattern incompatible with comprehension form).

### MAYBE / SKIP — bootstrap-era defensive iteration (12+ sites)

Pattern across `lower.mn`, `parser.mn`, `emit_llvm.mn`:

```mn
let mut r: List<T> = []
let mut i: Int = 0
let n: Int = len(xs)
for _ in 0..LARGE_BOUND:    // 50, 128, 256, 500, 2000
    if i < n:
        r.push(xs[i])
        i = i + 1
```

These are syntactically *not* range comprehensions — they're
manual-iteration idioms with an artificial upper bound. Converting
them to comprehensions would require *also* removing the artificial
bound (i.e., logic refactoring beyond syntax-only rewrite).

**Decision: SKIP.** Per PROMPT operating principle: "Do not
refactor logic while you're in there. Syntax-only." These sites
likely date to a bootstrap-era when range-for-loop reliability over
non-trivial bounds was uncertain; collapsing the pattern is its own
project. The 12+ sites:

- `parser.mn:1583` (`for _ in 0..128`)
- `lower.mn:575, 1543, 2767, 2858, 2863, 3023, 3395, 3766, 4470, 4492`
- `emit_llvm.mn:5737`

### SKIP — match-arm empty-list defaults (~30 sites in ast.mn)

Pattern:

```mn
match e {
    Call(_, a) => { return a },
    _ => { let empty: List<Expr> = []; return empty }
}
```

Not a loop; not a comprehension candidate. The `let empty = []`
is just a one-shot default for the `_` arm.

### SKIP — `transpiler.mn` literal-list builders (4 sites)

Pattern: `m.push(new_X(...)); m.push(new_X(...)); ... return m`
with N hardcoded entries (e.g., language-specific type-mapping
tables). Not loops; converting to a list literal `[new_X(...),
new_X(...), ...]` would be the fix here, but list-literal-of-N
constructor calls is brittle in the bootstrap (likely why the
push form is used).

**Decision: SKIP.** Out of comprehension scope.

## CLEAR-WIN sites to apply in Sh.C.B

1. `mapanare/self/transpiler.mn:340–345` — `rest` accumulator → comprehension in `match` arm.
2. `mapanare/self/transpiler.mn:407–410` — `new_vars` accumulator in `pop_scope`.
3. `mapanare/self/transpiler.mn:411–415` — `new_markers` accumulator in `pop_scope`.

Each will be applied as a separate commit with stage1 + goldens +
fixed-point validation between.

## Risk notes

The v5.15.1 Cb.* bootstrap mirror lowers `[expr for x in 0..n]`
through `_lower_comprehension` to the same MIR shape as a manual
`for x in 0..n: r.push(expr)` loop modulo SSA naming. Strict 3-stage
fixed point should be preserved by construction; if a specific site
breaks fixed point, that's a lowerer-determinism bug worth a
follow-up issue (and the site goes back into the SKIP column for
v5.17.1).


## v5.17.2 update — defensive-loop catalogue closed

The 11 SKIP'd defensive-iteration sites listed under
"Pattern across `lower.mn`, `parser.mn`, `emit_llvm.mn`" above
were rewritten in v5.17.2 Sh.H. All 10 Pattern A sites
(`lower.mn:575, 1542, 2766, 2858, 2863, 3022, 3393, 3764, 4459+4465`
and `emit_llvm.mn:5735`) became
`for i in 0..len(xs): r.push(xs[i])`. The 1 Pattern B site
(`parser.mn:1582`) became `while true:`. Strict 3-stage fixed point
preserved at 231,723 lines (0-line diff). Per-site verdicts and
LOC deltas in `docs/roadmap/v5/v5.17.2/SESSION_REPORT.md`.
