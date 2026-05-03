# v5.38.0 — SESSION_REPORT

**Tag:** Re.\* — regex stdlib closeout
**Date:** 2026-05-03
**Branch:** dev
**Decision:** Lead-approved at Phase 0 to keep PCRE2 backend
(Pike VM rewrite deferred to v6.0+).

---

## TL;DR

v5.38.0 is the **fifth release in the stdlib gap-close arc**
(Dt.\* @ v5.34.0, Sq.\* @ v5.35.0, Js.\* @ v5.36.0, Ht.\* @
v5.37.0, Re.\* @ v5.38.0). It audits the *existing* PCRE2-backed
`stdlib/text/regex.mn` (271 LOC, shipped at v0.9.0), fixes two
pre-existing bugs that had silently broken the module at HEAD,
and extends the surface with a `Regex`-first compile-once API
plus a `Captures` type with named-group lookup. Backref-bearing
replacements (`$1`, `${name}`, `$$`) work through PCRE2's
default substitute mode — no new C runtime exports. Strict
3-stage fixed point preserved by construction at v5.37.0's
**241,898 lines / 0 diff** (33-release strict streak from
v5.7.1). Goldens 95/95.

**Adds zero language features, zero new MIR ops, zero new IR
shapes, zero new runtime functions.**

---

## Phase 0 audit (load-bearing)

Phase 0 reconciled the v5.38.0 PLAN's "net-new module at
`stdlib/regex/`, ~600 LOC Pike VM" framing against what
actually existed at v5.37.0 HEAD. **The PLAN's premise was
wrong.** Reality:

- `stdlib/text/regex.mn` (271 LOC) shipped a complete PCRE2
  wrapper since v0.9.0.
- `compile() -> Result<Regex, RegexError>` already existed
  (PLAN's Re.1 main deliverable).
- C runtime PCRE2 wrapper at
  `runtime/native/mapanare_io.c:1306+` exposed 9 exports plus
  `pcre2_substitute` with the right options for `$1` / `${name}`
  / `$$` to work natively.
- Existing pytest at `tests/stdlib/test_regex.py` was
  compile-only IR-shape + **failing at HEAD** (parse error
  on `pon _: Int = ...`), and not in `make ci-gates`, so the
  failure was invisible.
- No in-tree callers of the module (only one bench file +
  the broken test).

The audit is committed at
`docs/roadmap/v5/v5.38.0/PRE_PHASE_AUDIT.md` and was surfaced
to the lead. Lead **confirmed PCRE2 as the v5.38.0 backend**
(Pike VM rewrite is a separate-arc decision, logged as v6.0+
LOW). Scoped delta agreed: extend existing module with new
`Regex`-first API + named-group support + runtime test corpus +
docs.

This deviates from the PLAN. It mirrors the v5.34.0 / v5.35.0 /
v5.37.0 pattern of Phase-0-driven scope corrections: the right
deliverable for the release window, not the deliverable named
in the PROMPT.

---

## What shipped

### Re.1 + Re.2 — Regex-first compile-once API

Added to `stdlib/text/regex.mn` (lines 305+):

```
fn regex_is_match(r: Regex, subject: String) -> Bool
fn regex_find(r: Regex, subject: String) -> Option<Match>
fn regex_find_all(r: Regex, subject: String) -> List<Match>
fn regex_replace(r: Regex, subject: String, replacement: String) -> String
fn regex_replace_all(r: Regex, subject: String, replacement: String) -> String
fn regex_free(r: Regex) -> Regex
```

The pre-existing pattern-string-first API (`regex_match`,
`find_all`, `replace`, `replace_all`, `regex_split`,
`is_match`) is **preserved unchanged**. Use the new
`Regex`-first verbs when matching the same compiled pattern
many times.

### Re.3 — Captures + named groups

```
pub tipo NamePair { name: String, index: Int }

pub tipo Captures {
    text: String, start: Int, end_pos: Int,
    group_values: List<String>,    // [0] = whole match
    group_present: List<Bool>,
    names: List<NamePair>
}

fn regex_captures(r: Regex, subject: String) -> Option<Captures>
fn regex_captures_iter(r: Regex, subject: String) -> List<Captures>
fn captures_get(c: Captures, idx: Int) -> Option<String>
fn captures_get_named(c: Captures, name: String) -> Option<String>
fn captures_count(c: Captures) -> Int
```

Named groups parse `(?P<name>...)` and `(?<name>...)` in the
pattern source via the new `parse_named_groups` walker
(~120 LOC). Walker handles escapes, character classes,
non-capturing groups (`(?:...)`), lookarounds (`(?=...)` /
`(?!...)` / `(?<=...)` / `(?<!...)`), atomic groups
(`(?>...)`), inline flags (`(?i)`), and comments (`(?#...)`)
correctly.

`Captures` stores group values as parallel
`List<String> + List<Bool>` rather than `List<Option<String>>`
to sidestep the v5.x drop-glue carry on `List<Option<X>>`
appends (caused snapshot_all_groups to hang in early testing).
Public API preserves `Option<String>` — callers don't see
the workaround.

### Re.4 — runtime test corpus

Two `.mn` test files under `stdlib/text/tests/`:

- `test_regex_smoke.mn` (10 sections): compile happy + error
  paths, `regex_is_match`, `regex_captures` named-group
  extraction, numbered-group access, unknown-name handling,
  `captures_count`, `captures_iter`, `regex_replace_all` with
  `$1`/`$2`, named backref via `${name}`, `$$` literal
  escape.
- `test_regex_corpus.mn` (~40 cases): literals + `.`,
  quantifiers (`*` `+` `?` `{n}` `{n,m}`), anchors (`^` `$`),
  character classes (`[a-z]` `[^...]` `\d` `\w` `\s`),
  alternation (`|`), non-capturing groups (`(?:...)`),
  capture groups (numbered), inline flag `(?i)`,
  `find_all` count assertions, `replace_all` edge cases.

Pytest harness `tests/stdlib/test_text_regex.py` mirrors the
v5.34/v5.35 concatenation pattern: read regex.mn, prepend to
each test main body, compile via Python LLVM emitter, link
against `libmapanare_rt.a`, run, assert "PASSED" in stdout.
Gated on `libpcre2-8` being dlopen-able. **3/3 tests pass.**

### Re.5 — docs

`docs/stdlib/regex.md`: pattern syntax reference,
type / API reference, 6 cookbook recipes (compile-once
match-many; extract named fields; swap pairs via `$1`/`$2`;
replace via named backref; iterate matches with groups;
case-insensitive via inline flag), deviation notes
(pattern-vs-replacement backref distinction; Pike VM v6.0+
note; PCRE2-version constraints), migration note from the
pre-v5.38.0 surface.

---

## Pre-existing bugs fixed in v5.38.0

### Bug 1 — `pon _: Int = ...` unparseable at HEAD

`stdlib/text/regex.mn` had **17 occurrences of
`pon _: Int = __mn_regex_free(handle)` (and one similar)** that
the current parser rejects (`_` is not a valid binding name).
The old `tests/stdlib/test_regex.py` (compile-only IR-shape)
failed at HEAD with `ParseError`, but it wasn't in `make
ci-gates`, so the failure was invisible. Fix: rename all
occurrences to `pon _drop: Int = ...`. **The pre-existing
old-API tests now pass** — 32/32 cases — though only because
they're compile-only.

### Bug 2 — `String.substr(start, count)` semantics

Mapanare's `String.substr(start, count)` takes a **count** as
the third argument, not an exclusive end-index — a Mapanare
quirk that bit my `parse_named_groups` walker once
(`pattern.substr(name_start, close_idx)` returned 8 chars
starting at name_start, not the slice I intended). Fix:
`substr(name_start, close_idx - name_start)`. The
pre-existing `regex_split` at lines 235/242 has the same
shape `text.substr(offset, text_len)` — it over-reads past
string end, but PCRE2 caps the bounds, so it's a latent
"silent over-read" rather than a visible crash.

---

## v5.x lowering carry uncovered (Re.6 — new MEDIUM)

While bringing up runtime tests, the Re-test exercising the old
pattern-string-first `regex_match("...", "...")` triggered an
LLVM IR error: `extractvalue operand must be aggregate type`
on `extractvalue i1 %l, 0`. Bisection isolated the trigger to
a `pon m: Option<Match> = regex_match(...)` local — the
Mapanare lowerer allocates `m` as `i1` (Bool) instead of as the
`Option<Match>` aggregate. Same bug class as v5.36.0 Js.0.B
(`_do_wrap_ok` / `_do_wrap_err` Result-shape mismatch) and
v5.26.1 Eu.\*.

- Reproduces standalone, with no v5.38.0 additions involved.
- Reproduces with `is_match` renamed to a different name (rules
  out a name-shadow / function-resolution artifact).
- The IR shows `regex_match(...)` lowered to an inlined
  `compile_str + exec_str + free + icmp sgt 0 + store i1`
  sequence — exactly the body shape of `is_match` (a Bool-
  returning sibling), not `regex_match` (an Option-returning
  function).

This is **out of scope for v5.38.0** — fix needed in
`mapanare/lower.py` / `emit_llvm_text.py`, not in the regex
module. Tracked as **Re.6 — new MEDIUM** carry-forward.
Investigation tractable; estimate 1-2 days focused work to
locate the lowering bug.

The v5.38.0 Regex-first API does not trigger this bug because
`Regex` (not `Option<Match>`) is the local type.

---

## Out of scope, deferred

- **Pike VM rewrite** — backend decision locked at PCRE2 for
  v5.38.0; rewrite is a v6.0+ candidate.
- **Re.6 — Option<Match> lowering bug** — new MEDIUM
  carry-forward.
- **`regex_replace` (single-shot) returns subject unchanged**
  on multi-match input — underlying C wrapper without
  `PCRE2_SUBSTITUTE_GLOBAL` does not substitute under current
  testing. v5.38.x follow-up; `regex_replace_all` validated.
- **`find` alias for `regex_match`** — calls broken
  `regex_match` (blocked by Re.6).
- **Rust regex Apache-2.0 corpus port** — v5.38.x candidate
  when Re.6 closes.
- **Pattern-side backreferences (`\1`)** — NP-complete worst
  case; explicitly out of v5.x stdlib.

---

## Verification

| Gate | Result |
|---|---|
| `make ci-gates` (9 sub-gates) | ✅ GREEN |
| `verify_fixed_point.sh` | ✅ STRICT (241,898 / 0 diff) |
| `test_native.py` goldens | ✅ 95/95 |
| `test_text_regex.py` (new) | ✅ 3/3 (smoke + corpus + parses-clean) |
| `test_regex.py` (legacy) | ✅ 32/32 (compile-only IR-shape) |
| `check_doc_freshness.py` | ✅ clean |
| `check_changelog_honesty.py` | ✅ clean |
| `make lint` | ✅ clean |

---

## Source delta

| File | Change |
|---|---|
| `stdlib/text/regex.mn` | +461 LOC (Re.1+Re.2+Re.3 surface) + 18 line-renames (Bug 1) + 2 substr-arg fixes (Bug 2) |
| `stdlib/text/tests/test_regex_smoke.mn` | new, ~270 LOC |
| `stdlib/text/tests/test_regex_corpus.mn` | new, ~150 LOC |
| `tests/stdlib/test_text_regex.py` | new, ~170 LOC |
| `docs/stdlib/regex.md` | new, ~360 LOC |
| `docs/roadmap/v5/v5.38.0/PRE_PHASE_AUDIT.md` | new |
| `docs/roadmap/v5/v5.38.0/SESSION_REPORT.md` | new (this file) |
| `CHANGELOG.md` | `## [5.38.0]` filled |
| `CLAUDE.md` | release-notes entry added |
| `docs/SPEC.md` | Hd-class header sync v5.37.0 → v5.38.0 |
| `VERSION` + 4 README badges | mechanical bump |

---

## Aggregate state entering v5.39.0

- **0 HIGH**
- **3 MEDIUM**: Re.6 (new — `Option<Match>` lowering bug);
  Ht.5 typed handler (Js.4.B drop-glue, carry); macOS
  notarization (carry from v5.33.0 Nu.2)
- **~9 LOW**: Pike VM rewrite candidate (new); `regex_replace`
  single-shot follow-up (new); Rust regex corpus port (new);
  plus the v5.37.0+ carries (Autobahn corpus, bounded-RSS
  streamer, closure-chain middleware, native `Bytes` type,
  cyclic-struct detection, `Map<String,String>` drop-glue)

Cadence: panel REMINDER fired at 9 minor versions since
v5.28.0; informational only (per v5.33.2 Cd.\*).
