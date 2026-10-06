# v5.38.0 — Re.\* — regex stdlib

**Status:** PLANNING
**Type:** Stdlib expansion. Net-new module at `stdlib/regex/`.
**Breaking:** No.
**Prerequisite:** v5.37.0 shipped (HTTP completeness).
**Estimated effort:** 1 session. ~800 LOC `.mn` for the engine,
plus ~300 LOC of tests.

---

## Why this exists

There is no regex stdlib. Common operations that downstream apps
expect — match a pattern, extract groups, replace — currently
require either ad-hoc string manipulation or shelling out to a
sed/grep child process. Both are bad answers.

This is item #5 of the stdlib gap-close arc. It's the most
self-contained item in the arc — pure algorithm, no external
dependencies, no FFI, no platform variation.

---

## Goals

1. **Re.1** — Compiled regex type: `Regex::compile(pattern:
   String) -> Result<Regex, RegexError>`.
2. **Re.2** — Match operations: `regex.is_match(s)`,
   `regex.find(s) -> Option<Match>`, `regex.find_all(s) ->
   List<Match>`.
3. **Re.3** — Capture groups: `Match::group(n: Int) ->
   Option<String>`, named groups via `(?P<name>...)`.
4. **Re.4** — Replace: `regex.replace(s, replacement: String)`,
   `regex.replace_all(s, replacement)`. Replacement supports `$1`,
   `$2`, `${name}` references.
5. **Re.5** — Tests: pattern correctness corpus + property tests
   for round-trip identities.

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Re.1** | HIGH | **Engine in `stdlib/regex/engine.mn`.** Pike VM (Thompson NFA simulation) — linear-time guaranteed in input length, bounded memory in pattern length. Standard textbook implementation; ~600 LOC. Supports: literals, `.`, `^ $`, `* + ? {n,m}`, character classes `[a-z]`, alternation `\|`, capture groups `(...)`, non-capturing groups `(?:...)`, named groups `(?P<name>...)`. **No backtracking; no lookaround in v5.38.0** (see Out of Scope). | 6h |
| **Re.2** | HIGH | **Public API in `stdlib/regex/api.mn`.** `Regex::compile`, `regex.is_match`, `regex.find`, `regex.find_all`, `regex.split`, `regex.captures` (single match with all groups), `regex.captures_iter` (all matches with groups). | 2h |
| **Re.3** | HIGH | **Replace in `stdlib/regex/replace.mn`.** `regex.replace(s, repl)` — first match. `regex.replace_all(s, repl)`. Replacement string syntax: literal text, `$0` (whole match), `$1..$9` (numbered groups), `${name}` (named groups), `$$` (literal `$`). | 2h |
| **Re.4** | HIGH (gate) | **Tests in `stdlib/regex/tests/`.** `test_basic.mn` (literal, anchors, quantifiers, classes), `test_groups.mn` (numbered + named), `test_replace.mn` (refs + escapes), `test_pathological.mn` (patterns that would catastrophically backtrack on PCRE — confirm linear time on Pike VM). Property tests: `find_all(s, p) ⊆ matches found by manual search`; `replace_all(replace_all(s, p, "X"), p, "X") = replace_all(s, p, "X")` (idempotent for replacements that don't introduce new matches). | 3h |
| **Re.5** | LOW | **Doc page** at `docs/stdlib/regex.md`. Pattern syntax reference + cookbook. Note explicitly: "no lookaround / backreferences in v5.38.0; PCRE compatibility deferred to a future release." | 1h |

---

## Phase plan

- **Phase 0** — Pre-flight; v5.37.0 HEAD clean.
- **Phase 1** — Re.1 engine. Full implementation before any API
  surface lands; engine bugs leak everywhere.
- **Phase 2** — Re.2 + Re.3 API on top.
- **Phase 3** — Re.4 tests.
- **Phase 4** — Re.5 docs.
- **Phase 5** — Bump + tag.

---

## Out of scope

- **Lookaround `(?=...)` / `(?!...)`.** Doable in NFA but adds
  significant engine complexity. Defer until concrete user
  demand.
- **Backreferences `\1` in patterns** (matching what a previous
  group captured). Backreferences make regex matching
  NP-complete in the worst case; the entire reason Pike VM is
  the choice is to *avoid* exponential blowup. PCRE-style
  backreferences are explicitly out of v5.x stdlib.
- **Unicode property classes (`\p{L}`).** Useful but requires
  bundling Unicode tables; defer.
- **Case-insensitive `(?i)` and other inline flags.** Add in a
  v5.38.x patch if straightforward; not blocking.
- **POSIX bracket expressions `[[:alpha:]]`.** Out; common
  classes (`\d \w \s`) sufficient.
- **Compile-time pattern checking.** Compiler doesn't validate
  regex strings at compile time — runtime `Result` shape
  handles errors. Future work.

---

## Risk

1. **Pike VM perf.** Linear-time guarantee is the killer
   feature; constant factors matter for short strings. Mitigation:
   benchmark against Python's `re` (which uses backtracking, so
   it's faster on average inputs but blows up on pathological
   ones); accept a 2-3× perf gap for the worst-case-linear
   guarantee. Re-visit if benchmarks show >5× gap.
2. **Capture group memory.** Each parallel NFA thread tracks its
   own capture state; pathological patterns with many groups +
   long inputs can use lots of memory. Mitigation: bounded
   thread count (Pike VM naturally bounds to O(states × groups)
   threads); document the limit.
3. **Regex bugs are subtle.** Replace cannot be tested
   exhaustively; engine has emergent behavior on combined
   features (alternation × quantifier × anchor). Mitigation:
   port a subset of Rust regex's test suite (Apache 2.0; OK to
   adapt) — it's the gold standard for engine correctness.

---

## Success criteria

- ✅ `Regex::compile(r"foo|bar").unwrap().is_match("hello bar")`
  returns true.
- ✅ Named groups: `r"(?P<year>\d{4})-(?P<month>\d{2})"` extracts
  both.
- ✅ Replace with backref: `replace_all("john smith", r"(\w+)
  (\w+)", "$2 $1")` → `"smith john"`.
- ✅ Pathological pattern `r"(a*)*b"` against
  `"aaaaaaaaaaaaaaaaaaaaaa"` (no `b`) terminates in <100ms (Pike
  VM is linear; PCRE-style backtracking would take seconds or
  hours).
- ✅ Goldens 95/95.
- ✅ Strict 3-stage fixed point preserved.

---

## Carry-forward delta

**Closes:**
- "no regex stdlib" gap.

**Inherits to v5.39.0:**
- Lookaround / backreferences / Unicode classes (new LOW; future
  releases as demand surfaces).
- Older carries (notarization, tzdb, Pg drivers, HTTP/2/3).
