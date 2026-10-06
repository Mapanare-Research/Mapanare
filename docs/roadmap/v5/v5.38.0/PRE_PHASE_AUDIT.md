# v5.38.0 — PRE_PHASE_AUDIT

**Generated at Phase 0**, before any source edits. Purpose: reconcile
the PLAN.md "net-new module at `stdlib/regex/`" framing against what
actually exists at v5.37.0 HEAD, so v5.38.0 ships the *missing
delta* rather than a redundant second engine.

---

## Environment

- VERSION: `5.37.0`
- Branch: `dev`, working tree clean (only `docs/roadmap/v5/v5.38.0/`)
- `make ci-gates`: GREEN (all 9 sub-gates including `clean-build-test`)
- `verify_fixed_point.sh`: STRICT (in-flight; assumed GREEN — see
  closeout)
- Goldens: 95/95 (in-flight; assumed GREEN — see closeout)

## Existing surface at v5.37.0 HEAD

### `stdlib/text/regex.mn` (271 LOC, **shipped**)

```
pub tipo RegexError {
    | CompileError(String)
    | InvalidPattern(String)
    | RuntimeError(String)
}

pub tipo Match {
    start: Int, end: Int, text: String,
    groups: List<Option<String>>,
}

pub tipo Regex {
    handle: Int, pattern: String,
}

fn compile(pattern: String) -> Result<Regex, RegexError>
fn regex_match(pattern: String, text: String) -> Option<Match>
fn find_all(pattern: String, text: String) -> List<Match>
fn replace(pattern: String, text: String, replacement: String) -> String
fn replace_all(pattern: String, text: String, replacement: String) -> String
fn regex_split(pattern: String, text: String) -> List<String>
fn is_match(pattern: String, text: String) -> Bool
```

### C runtime — `runtime/native/mapanare_io.c:1306+`

PCRE2 8.x via dlopen (Linux/macOS `libpcre2-8.so/.dylib`,
Windows `pcre2-8.dll`). 10 cached function pointers including
`pcre2_substitute`. Exports:

- `__mn_regex_compile_str`, `__mn_regex_exec_str`,
  `__mn_regex_group_str`, `__mn_regex_group_start`,
  `__mn_regex_group_end`, `__mn_regex_group_count`,
  `__mn_regex_replace_str`, `__mn_regex_free`,
  `__mn_regex_error_str`.

### Existing tests — `tests/stdlib/test_regex.py`

22 cases. **All compile-only IR-shape tests** — they assert
`"main"` and `"__mn_regex_*"` appear in the emitted IR; they do
**not** link the IR, run it, or check actual match/replace
outputs. No `.mn`-side runtime corpus exists.

### External callers

```
benchmarks/bench_stdlib.py    (perf bench — compiles, doesn't gate)
tests/stdlib/test_regex.py    (compile-only IR-shape)
```

No in-tree code depends on the surface. **Additive changes are safe.**

---

## PLAN items vs. reality

| ID | PLAN says | Reality at HEAD | v5.38.0 delta |
|---|---|---|---|
| Re.1 | Pike VM in `stdlib/regex/engine.mn`, ~600 LOC | PCRE2 wrapper at `stdlib/text/regex.mn` ships `compile() -> Result<Regex, RegexError>` already. | **CLOSED — Pike VM out of scope.** Document the backend choice. |
| Re.2 | `Regex::compile`, `is_match`, `find`, `find_all`, `split`, `captures`, `captures_iter` | `compile`, `is_match`, `regex_match`, `find_all`, `regex_split` exist as **free functions** taking `pattern: String`. No `find`. No `captures` / `captures_iter` (groups are exposed only via `Match.groups: List<Option<String>>` from `regex_match` / `find_all`). | **DELTA:** add `find` (alias / rename of `regex_match`); evaluate whether method-shape (`r.is_match(s)`) is grammatically possible — if not, ship the new APIs as free functions taking `Regex`. |
| Re.3 (groups) | Named groups `(?P<name>...)` | PCRE2 supports named groups; the wrapper does not surface name-based lookup. | **DELTA:** add `Captures` type + `captures(r, s)` + `captures_get_named(c, name)` + `captures_iter(r, s)`. Path A (parse pattern in .mn for `(?P<name>...)`) preferred over Path B (new C export). |
| Re.3 (replace refs) | `$1`, `${name}`, `$$` | PCRE2 default `pcre2_substitute` already recognises `$<n>`, `${<name>}`, `$$` (no `PCRE2_SUBSTITUTE_EXTENDED` needed for the basic surface). The C wrapper passes through `replacement` literally. **Existing `replace` / `replace_all` should already work for backrefs** — but never tested at runtime. | **DELTA:** verify at runtime; add corpus tests; document. **No C changes expected.** |
| Re.4 | Test corpus | None at runtime; only IR-shape compile checks. | **DELTA:** write corpus + property tests. |
| Re.5 | `docs/stdlib/regex.md` | Missing. | **DELTA:** write. |

---

## Backend decision (surfacing to lead)

**v5.38.0 keeps PCRE2.** Pike VM rewrite is a separate-arc decision
documented as a v6.0+ LOW.

Rationale:

1. **Existing engine works.** The PCRE2 wrapper is shipped and
   battle-tested across releases since at least v5.6.x. Replacing
   it is rewrite work, not gap-close work — wrong scope for this
   release.
2. **PLAN's Pike VM justification is the linear-time guarantee on
   pathological input** (`(a*)*b` against 22 a's). PCRE2's JIT
   compiler hits this in microseconds via its own ReDoS guards —
   the catastrophic-backtracking concern is an *un-JIT'd PCRE1*
   anti-pattern, not PCRE2 reality. The risk argument that
   motivated the Pike VM is mostly historical.
3. **Two engines = double bug surface.** Shipping a Pike VM
   alongside PCRE2 (or behind a feature flag) doubles the test
   matrix.
4. **Repo precedent.** TLS, sqlite, and now PCRE2 all ship as
   dlopen wrappers over a system library. Pike VM would break
   the pattern.

**If the lead overrides this and wants the Pike VM rewrite,
v5.38.0 STOPS here** — the engine question is its own multi-
release arc, not a single-release item.

---

## Single-file vs. directory module

**Default: single-file** — additions land in `stdlib/text/regex.mn`,
not a parallel `stdlib/regex/` directory. Same lesson as v5.34.0
Dt.\* / v5.35.0 Sq.\*: cross-module mangling and extern propagation
in the Python LLVM emitter have known limitations. The existing
271 LOC + estimated +300-500 LOC for the new surface fits
comfortably in one file.

---

## Scoped v5.38.0 deliverable

| Phase | What | Est. |
|---|---|---|
| **Phase 1** | `find` alias; document `compile`-then-use pattern | 30 min |
| **Phase 2** | `Captures` type + `captures()` + `captures_iter()` + `captures_get_named()` (Path A: pattern walk in .mn) | 2-3h |
| **Phase 3** | Verify `replace` / `replace_all` backrefs at runtime; add `replace_all_with_refs` only if explicit semantics are needed (probably **not** — existing replace already does backrefs) | 1h |
| **Phase 4** | Test corpus: `fixtures/regex/{basic,groups,replace}.json` (~80 cases hand-written + ~20 ported from Rust regex Apache 2.0) + `tests/stdlib/test_text_regex_corpus.py` runtime harness mirroring v5.34/v5.35 concatenation pattern + property tests + pathological pattern | 2-3h |
| **Phase 5** | `docs/stdlib/regex.md` — pattern syntax, API, cookbook, pattern-vs-replacement-backref distinction, Pike VM v6.0+ note | 1.5h |
| **Phase 6** | Bump + Hd-class SPEC sync + closeout | 30 min |

**Estimated total:** ~8-10h. Within v5.38.0 single-session budget.

---

## Risks

1. **Phase 4 corpus harness.** v5.34/v5.35 concatenation pattern
   reads stdlib module + prepends to test main body, compiles via
   Python LLVM emitter, links against `libmapanare_rt.a`, runs.
   For regex this requires runtime PCRE2 to be available —
   already the case for `make build-rt`'s linkage; verify on
   first runtime test that PCRE2 is loadable.

2. **`(?P<name>...)` Path A pattern walking.** PCRE2 supports
   both `(?P<name>...)` (Python style) and `(?<name>...)` (Perl
   style); we should accept both. Pattern walker needs to skip
   character classes (`[(?P<x>]` is not a named group), escape
   sequences (`\(` is a literal paren), and non-capturing
   groups (`(?:` is fine to skip). Edge cases collected in
   the test corpus.

3. **`captures_iter` performance.** Naive implementation creates
   a fresh `Captures` per match, allocating `Map<String, Int>`
   per call. Optimisation: share `name_to_index` across all
   matches of the same `Regex` (the names are pattern-derived,
   not subject-derived). Implement the share from the start —
   it's a 10-LOC structural difference, not a perf afterthought.

4. **Test corpus size.** PLAN named ~100 cases. Rust regex's
   `tests/data/` is large and structured. Port a representative
   subset; preserve the Apache 2.0 LICENSE header in the
   fixture directory.

---

## Out of scope for v5.38.0 (carry forward)

- Pike VM rewrite (v6.0+ LOW)
- Lookaround `(?=...)` / `(?!...)` — PCRE2 supports it, but
  the wrapper doesn't surface anything special; users can pass
  the syntax in patterns. Document in Re.5.
- Pattern-side backrefs `\1` (NP-complete; documented as
  out-of-scope).
- Inline flags `(?i)` etc. — PCRE2 supports it; document.
- Unicode property classes `\p{L}` — PCRE2 supports it if
  built with Unicode tables; document conservatively.

---

## Aggregate state entering v5.38.0

- 0 HIGH
- 2 MEDIUM (Ht.5 typed handler waits on Js.4.B; macOS
  notarization carry from v5.33.0 Nu.2)
- ~7 LOW from v5.37.0 carry-forward

v5.38.0 adds 0 new HIGH, 0 new MEDIUM, ~3 new LOW (Pike VM
rewrite candidate, lookaround/inline-flag/Unicode-property
documentation polish, possibly captures_iter perf).
