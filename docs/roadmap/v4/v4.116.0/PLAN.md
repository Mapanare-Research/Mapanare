# Mapanare v4.116.0 — Documentation Batch

> **Phase E release 2.** Close all documentation gaps flagged across
> panels. The README has stale performance claims. The SPEC has drifted
> since v4.31.0. The async cookbook references only the Python bootstrap.
> The debugging guide predates DWARF support. There is no getting
> started guide. This release fixes all of that without changing a
> single line of compiler or runtime code.

**Status:** DONE (2026-04-14)
**Breaking:** No
**Prerequisite:** v4.115.0
**Delta review:** No
**Full panel:** No (v4.120.0)
**Estimated work:** 1 sprint
**Theme:** Make the docs match the code. Zero code changes.
**Session log:** `docs/roadmap/v4/v4.116.0/SESSION_REPORT.md`
**Decisions taken:** SPEC sync was flagged sections + spot-check (Decision 1, default); getting-started targets developers familiar with compiled languages (Decision 2, default); code verification covered updated/created docs only (Decision 3, default); existing `docs/getting-started.md` tutorial preserved as the language-feature tour, new `docs/guides/getting_started.md` is the practical build walk.

---

## Scope

Documentation has been a recurring complaint across panels. Boa has flagged it in every review since v4.82.0. The specific gaps:

1. **README.md** -- performance section references pre-Phase C numbers. No mention of the 5-language benchmark. Stale claims about binary status pre-Phase A.
2. **SPEC.md** -- has not been synced with the language since v4.31.0. Missing: futures (v4.80.0), keyword collision space (v4.113.0), bilingual keywords (v3.0.0).
3. **Async cookbook** -- `docs/cookbook/async.md` only shows Python bootstrap examples. v4.115.0 proved native async works; the cookbook must reflect that.
4. **Debugging guide** -- `docs/guides/debugging.md` predates DWARF debug info support. No native binary debugging workflow.
5. **Getting started guide** -- does not exist. A new user has no entry point.

This release writes or refreshes all five documents and verifies every code example compiles and runs.

## Phase 1 -- README.md update

- [ ] Read `README.md` -- identify stale claims in the performance section
- [ ] Update performance section with Phase C numbers (5-language comparison from v4.107.0)
- [ ] Add note about native binary status: working post-Phase A, 64/64 golden, fixed-point achieved in Phase D
- [ ] Remove or correct any claims about features that don't work yet
- [ ] Update the "quick start" section if it references outdated commands
- [ ] Verify all shell commands in the README actually work

## Phase 2 -- SPEC.md sync

- [ ] Read `docs/SPEC.md` -- identify sections that have drifted from current language state
- [ ] Update or add section on futures/async: `async fn`, `await`, `block_on` semantics (from v4.80.0)
- [ ] Update or add section on keyword collision space: reserved words, bilingual equivalents (from v4.113.0)
- [ ] Update or add section on bilingual keywords: `fn`/`funcion`, `let`/`sea`, `if`/`si`, etc. (from v3.0.0)
- [ ] Verify type system section matches `mapanare/types.py` (25 TypeKinds)
- [ ] Verify operator precedence table matches `mapanare/mapanare.lark` (13 levels)
- [ ] Verify struct, enum, trait, impl sections match current grammar and semantics
- [ ] Mark any SPEC sections as "planned" for features not yet implemented

## Phase 3 -- Async cookbook refresh

- [ ] Read `docs/cookbook/async.md` (if it exists) or create it
- [ ] Add native compilation examples from v4.115.0:
  - File I/O async example with `mnc` compilation commands
  - TCP/HTTP async example with compilation commands
- [ ] Show the full workflow: write `.mn` -> compile with `mnc` -> link -> run
- [ ] Document what works natively vs what still requires the Python bootstrap
- [ ] Include error handling patterns with `Result<T, E>` in async contexts

## Phase 4 -- Debugging guide refresh

- [ ] Read `docs/guides/debugging.md` (if it exists) or create it
- [ ] Add DWARF debug info section: how mnc-stage1 emits debug info, how to use it with gdb/lldb
- [ ] Document the native binary debugging workflow:
  - Compile with debug info: `mnc --debug source.mn`
  - Run under gdb: `gdb ./binary`
  - Set breakpoints on Mapanare functions
  - Inspect Mapanare structs in gdb
- [ ] Document valgrind workflow for memory debugging
- [ ] Document `ir_doctor.py` and `culebra` for IR-level debugging
- [ ] Include common debugging scenarios and their solutions

## Phase 5 -- Getting started guide

- [ ] Write `docs/guides/getting_started.md`:
  - Prerequisites: LLVM, clang, Python 3.11+ (for bootstrap)
  - Installation: `make install`
  - Write hello.mn:
    ```mapanare
    fn main() {
        print("Hello, Mapanare!")
    }
    ```
  - Compile with Python bootstrap: `mapanare build hello.mn`
  - Compile with native compiler: `mnc hello.mn`
  - Run: `./hello`
  - Next steps: links to SPEC, cookbook, examples/

## Phase 6 -- Verify all code examples

- [ ] Extract every code block from all updated/created docs
- [ ] Compile each through the Python bootstrap (at minimum)
- [ ] Compile each through mnc-stage1 where applicable
- [ ] Fix any examples that don't compile
- [ ] Document any examples that only work through one pipeline

## Phase 7 -- LOW sweep + closeout

- [ ] Standard LOW sweep
- [ ] `VERSION` bumped in final commit
- [ ] `CHANGELOG.md [4.116.0]` entry
- [ ] `SESSION_REPORT.md` written

---

## Exit criteria (9 items)

| # | Check | Evidence |
|---|---|---|
| 1 | README.md performance section updated with Phase C numbers | diff |
| 2 | README.md stale claims removed or corrected | diff |
| 3 | SPEC.md synced: futures, keyword collision space, bilingual keywords | diff |
| 4 | Async cookbook refreshed with native compilation examples | file updated/created |
| 5 | Debugging guide updated with DWARF + native binary workflow | file updated/created |
| 6 | Getting started guide written | `docs/guides/getting_started.md` exists |
| 7 | All code examples in docs compile and run | verification log |
| 8 | No broken links in updated docs | link check |
| 9 | Standard closeout clean | CI green |

---

## What this release does NOT do

- **Change the compiler** -- zero modifications to any `.py` or `.mn` file in `mapanare/` or `mapanare/self/`.
- **Change the runtime** -- zero modifications to any `.c` or `.h` file in `runtime/`.
- **Add features** -- documentation only. If a feature is missing, document that it's missing.
- **Write tutorials** -- guides and cookbooks are reference-oriented, not tutorial-oriented.
- **Run a panel** -- Phase E has no panel. The next panel is v4.120.0.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| SPEC drift is larger than expected, requires multi-day effort | medium | medium | Focus on the three flagged sections first (futures, keywords, bilingual). Other drift becomes v5 documentation work. |
| Code examples in docs don't compile due to language changes since they were written | medium | medium | Phase 6 explicitly catches this. Fix the examples, not the compiler. |
| Getting started guide requires features that don't work end-to-end | low | high | Test every step on a clean checkout before committing the guide. |
| README performance numbers are worse than expected when re-measured | low | low | Use the Phase C numbers as-is. This release measures nothing new. |
| Debugging guide references DWARF features that are incomplete | medium | medium | Document what works. Be explicit about limitations. |

---

## After v4.116.0

v4.117.0 hardens the test suite: ASan CI gate, TSan CI gate, flaky test audit, coverage report, integration test hardening. After Phase E, Phase F begins: v4.118.0 is the final cross-language benchmark, v4.119.0 is the retrospective, and v4.120.0 is the panel -- the v5 gate (attempt 2).
