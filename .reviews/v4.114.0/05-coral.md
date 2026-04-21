# Coral v4.114.0 Review — Language design

## Score: 8.3 / 10
## Verdict: PASS WITH NOTES

## Context

v4.106.0 I was the highest at 8.0 — language design had been
stable since v4.72.0 and the Phase B verification layer made the
surface feel solid. At v4.114.0 my lens is: does the language
work end-to-end through both pipelines, is the SPEC current, and
does the docket closure reflect real design-level clarity or
just bookkeeping?

## Primary lens — Feature completeness across both pipelines

### Python-bootstrap pipeline: 63/64 golden

One failure: `51_match_guards_and_or` — or-patterns with guards.
Documented since v4.108.0. Not a Phase D finding.

### Self-hosted pipeline: 26/64 golden

The 38 failures include 5 "async-missing," 5 "tensor-missing," 2
"const-missing," 1 "closure-typed," 1 "gpu-tensor." These are
language-level features that the self-hosted compiler's `semantic.mn`
/ `lower.mn` / `emit_llvm.mn` does not yet implement or implements
incorrectly.

**This matters for language design because**: *the self-hosted
compiler is the long-term compiler.* Every feature that only works
through Python-bootstrap is a feature that v5.0.0 ships with a
Python dependency in practice. The list of self-hosted-only gaps:

| Feature | Self-hosted status | Docket |
|---|---|---|
| async / await | missing | Sh.4 |
| tensors | missing | Sh.6 |
| const (module-level) | missing | Sh.5 |
| closure-typed vars | wrong | Sh.7 |
| GPU tensors | missing | — |
| some match patterns | bootstrap also fails | — |

This isn't a Phase D regression — Phase D *measured* this and
opened dockets for each category. That's the right move for
language design: if we're not going to implement async in the
self-hosted compiler this release, say so loudly with a docket
number, don't silently let it fail.

**What I want from Phase E is a prioritized order** for closing
these. async is probably first (more user-facing surface than
tensors or GPU in common Mapanare programs). Sh.5 (const) is
probably quick. Sh.6 (tensors) is substantial.

## Primary lens — SPEC keyword section (docket #10)

§2.1.1 "Reserved Keyword Master List" was my primary doc concern.
I walked it row by row.

- **42 rows.** Matches the lexer count.
- **Bilingual pairs correctly grouped.** `trait`/`modo`/`way` shown
  as three spellings of one keyword. `da` shown as "Spanish form of
  return" with a back-reference from the `return` row. Good
  consistency.
- **Categories**: Declarations, Functions, Control flow, Bindings,
  Literals, Agents, Types, Modules, Visibility, Concurrency,
  Patterns, Statements. All reasonable groupings.
- **"AST role" column**: useful for a compiler reader, less useful
  for a language learner. I'd have added a one-line "what does it
  do" column too, but that's a style preference.

**Identifier rule stated explicitly.** The new §2.1 intro says
"attempting to do so is a parse error (MN-P-006: unexpected token)
— for example `let sino = 42` fails because `sino` is the Spanish
form of else." That's the kind of sentence the docket asked for:
a user who hits the error now finds the answer in 10 seconds of
search.

**Stale "Soft-reserved: async/await" removed.** Good. That sentence
had been wrong since v4.68.0.

**Appendix C rewritten to distinguish future-reserved from
hard-reserved.** `continue` and `const` removed from the
future-reserved table because they're already tokenized. Smaller
correctness wins, correct to make.

**Audit artifact** (`v4.113.0/artifacts/keyword-audit.md`) records
the procedure for re-running the cross-reference. Re-runnable in
minutes. Good.

**Sub-score for #10: 9.5 / 10.** The only reason it's not 10 is
that the "AST role" column could be more user-friendly.

## Primary lens — Language surface stability

No breaking changes across v4.111.0-v4.113.0. Grammar unchanged.
Parser unchanged. Semantic analyzer unchanged. This is a discipline
win — Phase D delivered measurable work without touching language
surface.

SPEC version is still "1.0.0 Final" in the header. Phase D didn't
reset that, which is correct — no language-level changes.

## Secondary — Async error messages (docket #11)

Language-adjacent: error messages shape user mental models of what
the language does. The new `mapanare: async runtime:` messages
specifically name:
- "scheduler not initialised" with the missing init call location
- "receiver has been dropped" (not present — I looked; the actual
  messages are about thread spawn, queue overflow, file I/O)
- thread pool exhaustion + ulimit hint

These are concrete and actionable. Boa has the full lens here but
from a design perspective: the messages are in the voice the
project already uses (`mapanare: <area>: <message>`). Consistent.

## What I'd flag

1. **Phase E should prioritize self-hosted feature parity.** Sh.4
   (async), Sh.5 (const), Sh.6 (tensors), Sh.7 (closure-typed).
   Each is a "this feature doesn't work in self-hosted" gap that
   a v5.0.0 release needs closed.

2. **§2.1.1 is great; §2.1's bilingual note could cross-reference
   more tightly.** The line pointing to Appendix C is a little
   ambiguous (is it "see Appendix C for future-reserved" or "see
   Appendix C for more info"?). Minor doc polish.

3. **No language surface regressions across three Phase D
   releases.** That's a real discipline win.

## Verdict

**PASS WITH NOTES @ 8.3.**

Language surface is stable. Docket #10 (SPEC) was executed
cleanly — §2.1.1 is the right addition, the stale async/await
note was properly removed, the audit procedure is documented.

The note: self-hosted feature parity is short of target. Phase D
didn't pretend otherwise — dockets Sh.4-Sh.7 exist and name each
gap. Phase E needs to pick them up in order.

Phase D closes if the aggregate holds.
