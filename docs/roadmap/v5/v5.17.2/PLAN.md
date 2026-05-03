# v5.17.2 — Sh.H — defensive-loop cleanup

**Status:** PLANNING
**Breaking:** No semantic change. IR must remain byte-identical to
v5.17.1 modulo whitespace in metadata strings, i.e. **strict
3-stage fixed point preserved**.
**Prerequisite:** v5.17.1 shipped (Sh.C + Sh.D + Sh.G — terse
polish).
**Estimated effort:** 2–4h, single session. Per-site rewrites are
small and isolated.

---

## Why this exists

v5.17.1's COMPREHENSION_SITES.md catalogued 12+ defensive-iteration
sites in `mapanare/self/*.mn` of the form:

```mn
let mut r: List<T> = []
let mut i: Int = 0
let n: Int = len(xs)
for _ in 0..LARGE_BOUND:    // 50, 100, 128, 256, 500, 2000, 5000
    if i < n:
        r.push(xs[i])
        i = i + 1
```

These are bootstrap-era idioms. At the time the code was first
written, `for x in 0..len(xs)` reliability over deeply-nested AST
walking was uncertain, and the artificial upper bound provided a
safety net against the loop running away. By v5.17.x — comprehensions
ship (v5.15.0/v5.15.1), range-for is everywhere in the same files
(e.g., `transpiler.mn` uses `for i in 0..len(xs)` natively, and
`lower.mn` itself uses `for k in 0..len(...)` in many places) — the
defensive bound is dead weight.

v5.17.1 SKIP'd these as out-of-scope-for-syntax-only because the
rewrite changes the iteration scheme (removes the manual index
variable, drops the artificial bound). v5.17.2 closes the catalogue
as a small dedicated release.

---

## Goal

1. Rewrite all 11 Pattern A (index-collection) sites to proper
   `for X in 0..n:` range loops.
2. Rewrite the 1 Pattern B (state-advance) site to a `while` loop
   if safe; SKIP otherwise.
3. **Strict 3-stage fixed point preserved.** The lowerer must emit
   the same MIR for the rewritten loop as for the original — both
   should produce a `for i in 0..N` over `module.functions[i]`.
4. Goldens 80/80 throughout.
5. No new compiler features. No grammar changes. No bootstrap seed
   refresh required.

---

## Inventory

The 12 sites from v5.17.1 COMPREHENSION_SITES.md, re-categorized:

### Pattern A — pure index-collection (11 sites, all CLEAR-WIN)

```mn
let mut r: List<T> = []
let mut i: Int = 0
let n: Int = len(xs)
for _ in 0..LARGE:
    if i < n:
        r.push(xs[i])
        i = i + 1
```

→

```mn
let mut r: List<T> = []
for i in 0..len(xs):
    r.push(xs[i])
```

| File | Line | Context |
|---|---:|---|
| `lower.mn` | 575 | `bind_method_self_param` — `new_params` from `method.params[1..]` |
| `lower.mn` | 1542 | tensor method-call arg packing |
| `lower.mn` | 2766 | `__mn_tensor_get` index packing |
| `lower.mn` | 2858 | `__mn_tensor_slice` start packing |
| `lower.mn` | 2863 | `__mn_tensor_slice` end packing |
| `lower.mn` | 3023 | closure capture: parent param packing |
| `lower.mn` | 3395 | for-comprehension body-stmts copy |
| `lower.mn` | 3766 | tensor-set index packing |
| `lower.mn` | 4459, 4465 | `verify_module` outer (functions) + inner (errors) — nested |
| `emit_llvm.mn` | 5735 | function-body emission outer loop |

(Note the v5.17.1 catalogue listed 12 sites but `lower.mn:4459` is
the outer loop of the same nest as `4465`; both rewrites are part
of one fix.)

### Pattern B — state-advance while-style (1 site, MAYBE)

```mn
for _ in 0..100:
    if peek_type(tokens, p) != "COMMA":
        p = expect(tokens, p, "RPAREN")
        return new_expr_result(...)
    p = p + 1
    let a: ExprResult = parse_expr(tokens, p, ...)
    args.push(a.expr)
    p = a.pos
```

| File | Line | Context |
|---|---:|---|
| `parser.mn` | 1582 | `parse_call_args` — call-argument list parser |

This is a `while true` in disguise. The artificial bound (100)
limits the maximum number of call arguments. The natural rewrite
is:

```mn
while true:
    if peek_type(tokens, p) != "COMMA":
        p = expect(tokens, p, "RPAREN")
        return new_expr_result(...)
    p = p + 1
    let a: ExprResult = parse_expr(tokens, p, ...)
    args.push(a.expr)
    p = a.pos
```

But `while true:` may not lower cleanly through mnc-stage1 (no
condition-based exit; the early `return` is the only exit). If
mnc-stage1's lowerer handles `while true` with a deferred exit,
this is CLEAR-WIN. If not, SKIP and document.

**Decision: validate with a 1-site dry run during Phase 0; SKIP if
the rewrite breaks fixed point or goldens.**

### Out of scope

- `from_*.mn` and `transpiler.mn` were already idiomatic in v5.17.0
  (use `for i in 0..len(xs)` natively); no defensive-loop sites
  there.
- `parser.mn` has many `while`-style argument-parser loops already
  using the `for _ in 0..N` pattern; v5.17.2 only rewrites the
  one cleanest case (1582). The rest stay until evidence accumulates
  about lowerer support for `while true:`.

---

## Phase plan

### Phase 0 — Pattern B viability check (if proceeding with parser.mn:1582)

```bash
# Apply ONLY parser.mn:1582 change.
$EDITOR mapanare/self/parser.mn
python3 scripts/build_stage1.py
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1
bash scripts/verify_fixed_point.sh
```

If any check fails: `git checkout mapanare/self/parser.mn` and mark
Pattern B SKIP in COMPREHENSION_SITES.md.

If all checks pass: commit as `v5.17.2 Sh.H.B: state-advance while
in parser.mn::parse_call_args` and continue.

### Phase 1 — Pattern A rewrites (11 sites, one commit per file)

`lower.mn` has 9 sites; `emit_llvm.mn` has 1; `parser.mn` already
covered in Phase 0.

```bash
# For each file:
$EDITOR mapanare/self/<MODULE>.mn        # apply all sites in this file
python3 scripts/build_stage1.py
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1
bash scripts/verify_fixed_point.sh
python3 scripts/concat_self.py           # regen mnc_all.mn
git add mapanare/self/<MODULE>.mn mapanare/self/mnc_all.mn
git commit -m "v5.17.2 Sh.H.A: defensive-loop cleanup in <module> (<n> sites)"
```

Per-commit gates:

- Stage1 builds green.
- Goldens 80/80.
- Strict 0-line fixed point.

If a specific site breaks fixed point, **revert the site** (not the
whole file) and mark SKIP. Continue with the rest of the file.

### Phase 2 — Validation + closeout

```bash
python3 scripts/build_stage1.py
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1 -v
bash scripts/verify_fixed_point.sh
bash scripts/build_from_seed.sh
python3 -m pytest tests/ -v
make lint
```

Write:

```
docs/roadmap/v5/v5.17.2/SESSION_REPORT.md
```

Update:

```
VERSION                   # 5.17.1 → 5.17.2
CHANGELOG.md              # v5.17.2 entry
CLAUDE.md                 # release-notes preamble + Planned section
docs/roadmap/v5/v5.17.1/COMPREHENSION_SITES.md  # mark sites as
                                                # closed in v5.17.2
```

SESSION_REPORT includes:

- Pattern A sites applied vs SKIP, with reasons.
- Pattern B verdict (applied, SKIP'd, or n/a if Phase 0 caught it).
- Per-module line-count delta from v5.17.1 to v5.17.2.
- Stage2/3 byte-diff (target 0).
- Goldens result (80/80).
- Build-from-seed result.

---

## Risk register

| Risk | Likelihood | Mitigation |
|---|---|---|
| `for i in 0..len(xs)` lowers to different MIR than `for _ in 0..LARGE: if i < n` | LOW | Per-commit fixed-point gate catches this. Two `0..N` ranges should produce the same iteration MIR. If they diverge, the lowerer has a determinism bug worth a follow-up — SKIP the site for v5.17.2. |
| `while true:` lowering breaks for parser.mn:1582 | MEDIUM | Phase 0 isolation; SKIP and continue if it breaks. |
| Removed defensive bound surfaces a real iteration-count assumption | LOW | The artificial bounds (50, 100, 128, etc.) all comfortably exceed any realistic input — they were "obviously big enough" by construction. Goldens validate that no real input hits them. If a golden breaks because the new range exceeds the old defensive bound, that's a *bug we want to find* — the old code was capping iteration silently. |
| Site reads more clearly with the explicit index variable | LOW | Per-site judgment. If a reviewer prefers the manual form for clarity (e.g., the `i` is reused after the loop), SKIP. |

---

## Success criteria

- All Pattern A CLEAR-WIN sites rewritten.
- Pattern B parser.mn:1582 applied OR explicitly SKIP'd with
  documented reason.
- Goldens 80/80.
- Strict 3-stage fixed point preserved (231,957 lines, 0 diff).
- `bash scripts/build_from_seed.sh` works.
- `make lint` clean.
- COMPREHENSION_SITES.md updated to reflect closure of the catalogued
  defensive-loop section.
- SESSION_REPORT documents per-site decisions.

---

## Out of scope (deferred)

- Comprehension upgrades for sites where the rewrite IS a list
  comprehension (e.g., `[xs[i] for i in 0..len(xs)]`). v5.17.2
  intentionally rewrites to plain range-for, not to comprehension,
  to keep each commit a minimal logic refactor. A follow-up could
  promote the cleanest cases to comprehension form, but that's a
  separate judgment call and would require its own per-site survey.
- BLOCK_LONG implicit-return upgrades (28 sites in v5.17.1
  IMPLICIT_RETURN_SITES.md) — those are intentionally SKIP'd
  forever, not deferred.
- `tests/`, `stdlib/`, `examples/` — not in v5.17.x scope.
- `mapanare/*.py` (Python bootstrap) — not in v5.17.x scope.

---

## Next

- v5.18.0 — Mc.1/3/4 — tooling pack (LSP, `mnc init`, `mnc check`,
  VSCode extension).
- v5.19.0 — Te.3 + Dk.* — closeout (soft-deprecate `{}`, ship
  Docker images).
- v5.20.0 — Te.5 — struct ergonomics.
