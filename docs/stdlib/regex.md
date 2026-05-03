# Regex (`stdlib/text/regex.mn`)

Regular expressions for Mapanare. v5.38.0 ships a compile-once
`Regex`-first surface on top of the existing PCRE2 wrapper, plus
named groups via `Captures` and runtime tests covering ~50 cases.

**Backend:** PCRE2 8.x via dlopen (`libpcre2-8.so` / `.dylib` /
`.dll`). The Pike-VM-rewrite story (linear-time guarantee on
pathological input) is a v6.0+ candidate; PCRE2's JIT already
handles classic ReDoS shapes in microseconds. v5.38.0 deliberately
keeps the existing engine to avoid a parallel-implementation bug
matrix.

---

## Quick reference

```mn
// Compile once, match many.
let r: Result<Regex, RegexError> = compile("(?P<year>\\d{4})-(?P<month>\\d{2})")
match r {
    Ok(rx) => {
        // Boolean check.
        let ok: Bool = regex_is_match(rx, "date: 2026-05")

        // First match (Match struct).
        let one: Option<Match> = regex_find(rx, "date: 2026-05")

        // All matches.
        let all: List<Match> = regex_find_all(rx, "2026-05 vs 2027-12")

        // Captures with named groups.
        let c: Option<Captures> = regex_captures(rx, "date: 2026-05")
        match c {
            Some(cap) => {
                let yr: Option<String> = captures_get_named(cap, "year")
                let mo: Option<String> = captures_get_named(cap, "month")
            },
            None => { /* no match */ }
        }

        // Iterate captures across all matches.
        let it: List<Captures> = regex_captures_iter(rx, "2026-05 2027-12")

        // Replace (substitution syntax: $0..$9, ${name}, $$).
        let out: String = regex_replace_all(rx, "date: 2026-05", "$1/$2")

        // Free the compiled handle.
        let _: Regex = regex_free(rx)
    },
    Err(e) => { /* CompileError | InvalidPattern | RuntimeError */ }
}
```

---

## Types

### `RegexError`

```mn
pub tipo RegexError {
    | CompileError(String)    // PCRE2 reported a compile failure
    | InvalidPattern(String)  // empty pattern or local invariant violated
    | RuntimeError(String)    // unexpected runtime condition
}
```

### `Regex`

```mn
pub tipo Regex {
    handle: Int,      // opaque PCRE2 handle, 0 after regex_free
    pattern: String   // the original source pattern
}
```

### `Match`

```mn
pub tipo Match {
    start: Int,                       // byte offset of the whole match
    end: Int,                         // exclusive end byte offset
    text: String,                     // the matched substring
    groups: List<Option<String>>      // capture-group values; [0] is whole match
}
```

### `Captures` (v5.38.0)

```mn
pub tipo NamePair {
    name: String,
    index: Int  // 1-based capture-group index
}

pub tipo Captures {
    text: String,
    start: Int,
    end_pos: Int,
    group_values: List<String>,    // [0] = whole match; [i>=1] = group i
    group_present: List<Bool>,     // present[i] = false ⇒ group did not participate
    names: List<NamePair>          // pattern-derived; cached across captures_iter
}
```

`Captures` stores group state as parallel `List<String> +
List<Bool>` rather than `List<Option<String>>` to sidestep a
known v5.x drop-glue carry on `List<Option<X>>` append. The
public `captures_get` / `captures_get_named` helpers preserve the
`Option<String>` surface, so callers don't see the workaround.

---

## API

### Compilation

```mn
fn compile(pattern: String) -> Result<Regex, RegexError>
```

Compiles a PCRE2 pattern. `compile("")` returns
`Err(InvalidPattern("empty pattern"))`.

```mn
fn regex_free(r: Regex) -> Regex
```

Releases the PCRE2 handle. Returns a `Regex` with
`handle: 0` so the caller can keep the variable around without
double-frees. Idempotent.

### Match operations

```mn
fn regex_is_match(r: Regex, subject: String) -> Bool
fn regex_find(r: Regex, subject: String) -> Option<Match>
fn regex_find_all(r: Regex, subject: String) -> List<Match>
```

`regex_find` returns the first match starting from offset 0;
`regex_find_all` returns all non-overlapping matches in source
order, advancing past zero-width matches by one byte to guarantee
termination.

### Captures (named-group + indexed access)

```mn
fn regex_captures(r: Regex, subject: String) -> Option<Captures>
fn regex_captures_iter(r: Regex, subject: String) -> List<Captures>
fn captures_get(c: Captures, idx: Int) -> Option<String>
fn captures_get_named(c: Captures, name: String) -> Option<String>
fn captures_count(c: Captures) -> Int
```

Named groups use the `(?P<name>...)` (Python style) and
`(?<name>...)` (Perl style) syntax; both produce the same
`captures_get_named` lookup. `captures_count` returns the total
slot count including index 0 (whole match), so a pattern with
two capture groups returns 3.

`captures_iter` parses the pattern's named-group table once and
shares it across every yielded `Captures`, keeping per-match
allocation bounded.

### Substitution

```mn
fn regex_replace_all(r: Regex, subject: String, replacement: String) -> String
fn regex_replace(r: Regex, subject: String, replacement: String) -> String
```

`regex_replace_all` substitutes every non-overlapping match.
The replacement string supports PCRE2's default substitute syntax:

| Form         | Meaning                                                  |
|--------------|----------------------------------------------------------|
| `$0`         | the whole match                                          |
| `$1` ... `$9`| numbered group reference                                 |
| `${name}`    | named group reference                                    |
| `$$`         | literal `$`                                              |

Note: `${name}` literals trigger Mapanare's source-level string
interpolation — build replacement strings via concatenation when
the substitution should reach PCRE2 untouched, e.g.
`"$" + "{last} $" + "{first}"`.

`regex_replace` (single-shot, not all) has a known v5.38.x
follow-up in the underlying C wrapper — use `regex_replace_all`
when the pattern matches at most once or you want every match
replaced.

---

## Pattern syntax (v5.38.0 supported subset)

PCRE2-default mode. Fully supported on Mapanare:

| Construct              | Meaning                                       |
|------------------------|-----------------------------------------------|
| `abc`                  | literal                                       |
| `.`                    | any character except newline                  |
| `^` / `$`              | start / end anchors                           |
| `*` `+` `?`            | greedy 0+ / 1+ / 0–1                          |
| `*?` `+?` `??`         | lazy quantifiers                              |
| `{n}` `{n,}` `{n,m}`   | repetition counts                             |
| `[abc]` / `[^abc]`     | character class / negated class               |
| `[a-z]`                | character range                               |
| `\d` `\w` `\s`         | digit / word / whitespace shorthand           |
| `\D` `\W` `\S`         | negations                                     |
| `\\` `\.` etc.         | literal escapes                               |
| `a\|b`                 | alternation                                   |
| `(...)`                | capturing group                               |
| `(?:...)`              | non-capturing group                           |
| `(?P<name>...)`        | named capturing (Python style)                |
| `(?<name>...)`         | named capturing (Perl style)                  |
| `(?>...)`              | atomic group (non-capturing)                  |
| `(?=...)` / `(?!...)`  | lookahead / negative lookahead                |
| `(?<=...)` / `(?<!...)` | lookbehind / negative lookbehind             |
| `(?i)` / `(?-i)` …     | inline flags (case-insensitive, etc.)         |
| `(?#…)`                | comments                                      |

### Out of scope for v5.38.0

- **Pattern backreferences** (`\1`, `(?P=name)`) — match what a
  previous group captured. Backreferences make matching
  NP-complete in the worst case; explicitly out of v5.x stdlib.
  *Replacement-string* backrefs (`$1` in the replacement, see
  above) are different and **are** in scope.
- **Unicode property classes** `\p{L}` — PCRE2 supports these if
  built with Unicode tables. Works at runtime if the linked
  PCRE2 has the tables; not asserted by the v5.38.0 corpus.
- **POSIX bracket expressions** `[[:alpha:]]` — `\d` `\w` `\s`
  cover the common cases. Works at runtime if PCRE2 supports
  it; not asserted.
- **Compile-time pattern checking** — pattern strings are not
  validated by the Mapanare compiler. Errors surface at
  `compile` runtime as `Result::Err(CompileError(message))`.

---

## Cookbook

### 1. Compile once, match many

```mn
match compile("\\d+") {
    Ok(rx) => {
        let mut total: Int = 0
        for s in inputs {
            if regex_is_match(rx, s) { total = total + 1 }
        }
        let _: Regex = regex_free(rx)
        print(str(total))
    },
    Err(e) => { print("bad pattern") }
}
```

### 2. Extract named fields

```mn
let r = compile("(?P<year>\\d{4})-(?P<month>\\d{2})-(?P<day>\\d{2})")
match r {
    Ok(rx) => {
        match regex_captures(rx, "today: 2026-05-03") {
            Some(c) => {
                let y = captures_get_named(c, "year")
                let m = captures_get_named(c, "month")
                let d = captures_get_named(c, "day")
                /* … */
            },
            None => { /* no date in input */ }
        }
        let _: Regex = regex_free(rx)
    },
    Err(_) => {}
}
```

### 3. Swap pairs via `$1` / `$2`

```mn
let rx = compile("(\\w+) (\\w+)").unwrap()
let out = regex_replace_all(rx, "john smith", "$2 $1")
// out == "smith john"
let _: Regex = regex_free(rx)
```

### 4. Replace via named backref (build replacement at runtime)

```mn
let rx = compile("(?P<first>\\w+) (?P<last>\\w+)").unwrap()
// Build "${last} ${first}" by concatenation so Mapanare's source
// interpolation doesn't try to resolve `last` / `first`.
let repl: String = "$" + "{last} $" + "{first}"
let out = regex_replace_all(rx, "john smith", repl)
let _: Regex = regex_free(rx)
```

### 5. Iterate matches with groups

```mn
let rx = compile("(?P<num>\\d+)").unwrap()
let it: List<Captures> = regex_captures_iter(rx, "10 20 30")
let mut i: Int = 0
while i < len(it) {
    let c = it[i]
    let n = captures_get_named(c, "num")
    /* … */
    i = i + 1
}
let _: Regex = regex_free(rx)
```

### 6. Case-insensitive match via inline flag

```mn
let rx = compile("(?i)hello").unwrap()
regex_is_match(rx, "HELLO")  // true
regex_is_match(rx, "Hello")  // true
let _: Regex = regex_free(rx)
```

---

## Migration from the pre-v5.38.0 surface

The pre-v5.38.0 module shipped a pattern-string-first free-function
API:

```mn
regex_match(pattern, text)   // -> Option<Match>
find_all(pattern, text)      // -> List<Match>
replace(pattern, text, repl)
replace_all(pattern, text, repl)
regex_split(pattern, text)
is_match(pattern, text)
```

These are **preserved unchanged** in `stdlib/text/regex.mn`, but
the `pon _: Int = ...` syntax fails to parse on the current
parser; v5.38.0 retypes the throwaway bindings to `_drop`. There
is also a known v5.x lowering carry where
`pon m: Option<Match> = regex_match(...)` allocates `m` as `i1`
instead of as the `Match`-aggregate Option (tracked as Re.6,
follow-up after v5.38.0). Until that closes, the v5.38.0
**Regex-first** surface (`compile + regex_*` verbs +
`Captures`) is the recommended path — it does not trigger the
quirk because the `Regex` type lowers cleanly.

---

## Internals

- C wrapper: `runtime/native/mapanare_io.c` (PCRE2 dlopen,
  10 cached function pointers including `pcre2_substitute`).
- C exports: `__mn_regex_compile_str`, `__mn_regex_exec_str`,
  `__mn_regex_group_str`, `__mn_regex_group_start`,
  `__mn_regex_group_end`, `__mn_regex_group_count`,
  `__mn_regex_replace_str`, `__mn_regex_free`,
  `__mn_regex_error_str`. **No new C exports were added in
  v5.38.0** — the named-group lookup walks the pattern in
  Mapanare via `parse_named_groups`.
- Tests: `stdlib/text/tests/test_regex_smoke.mn` (10 sections
  covering compile + captures + named groups + replace) +
  `stdlib/text/tests/test_regex_corpus.mn` (~40 pattern-syntax
  cases). Pytest harness:
  `tests/stdlib/test_text_regex.py` (mirrors v5.34/v5.35
  concatenation pattern; gated on libpcre2-8 being dlopen-able).

## See also

- [`stdlib/json.md`](json.md) — JSON parsing (also dlopen-style backend wrapper)
- [`stdlib/sql.md`](sql.md) — SQLite (same dlopen pattern)
- [`stdlib/http.md`](http.md) — HTTP / router

