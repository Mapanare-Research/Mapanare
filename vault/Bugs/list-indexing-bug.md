---
docket: 2
severity: critical
found: "[[v4.99.0]]"
fixed: "[[v4.101.0]]"
status: fixed
tags: [bug, critical, fixed, phase-a, emitter]
---

# List Indexing Bug / Emitter Output Corruption

**Docket #2** from [[v4.99.0]] panel. Initially reported as "list indexing returns garbage." Turned out to be the same root cause as the mnc-stage1 output corruption that was misattributed to [[tagged-pointer-ub]].

## The Bug

The self-hosted emitter output had 16-byte garbage prefixes on declaration lines. The bytes matched an `MnString` struct (`{ ptr, len }`) being written where the string's content should be.

## Root Cause ([[v4.101.0]])

**Move-semantics gap** in `mapanare/emit_llvm_text.py`. Six sites in `_do_list_push`, `_do_struct_init`, `_do_field_set`, and related paths were writing the MnString struct address instead of dereferencing `s.data`.

## Impact

- Golden tests: 0/61 -> 16/62 after fix
- Regression test: `tests/golden/62_list_output.mn` added

## Reviewers

- [[Coral]]: flagged list indexing as language-level gap
- [[Anaconda]]: flagged 0/61 golden pass rate
- [[Boa]]: flagged undisclosed binary corruption
