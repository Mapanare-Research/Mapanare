# Mapanare v4.79.0 — Close Carry-Forward Items P2, P3, P6

> **Arc 10 release 3.** The final Mapanare-owned carry-forward items.
> P2 (pattern_matching.py zero unit tests), P3 (self-hosted guard
> fall-through divergence), and P6 (unreachable-arm warning zero test
> coverage) all trace back to the v4.36.0 panel. After this release,
> the carry-forward ledger shows 0 Mapanare-owned open items.

**Status:** DONE
**Breaking:** No
**Prerequisite:** v4.78.0
**Delta review:** No
**Full panel:** No (v4.81.0)
**Estimated work:** 1 sprint
**Theme:** Zero out the carry-forward ledger. Every Mapanare-owned item closed.

---

## Scope

Three pattern-matching-related items have been open since the v4.36.0 panel (Arc 1). All three are MEDIUM severity, all have been deferred through Arc 7 and beyond because they are latent for the current test corpus. v4.79.0 closes all three:

**P2** — `mapanare/pattern_matching.py` has zero dedicated unit tests. The module implements the Maranget decision-tree algorithm for exhaustiveness checking, pattern compilation, and guard lowering. It was rewritten in v4.34.0 (A6 closure) but never got its own test file. Target: a dedicated `tests/semantic/test_pattern_matching.py` with >=90% line coverage of the module.

**P3** — The self-hosted `lower.mn` match lowering diverges from the Python `lower.py` for guarded patterns. The Python pipeline uses a decision-tree approach (via `pattern_matching.py`); the self-hosted pipeline uses a jump-to-next approach for guards that falls through differently when the guard is false. The divergence is latent for the current test corpus but could produce wrong code for complex guard expressions. Fix: align the self-hosted guard lowering with the Python pipeline's decision-tree behavior.

**P6** — The unreachable-arm warning path in `semantic.py` (or `pattern_matching.py`) has zero test coverage. The warning fires when a match arm can never be reached because prior arms already cover all cases. No test verifies this warning is emitted. Fix: add tests that trigger unreachable-arm detection and verify the warning.

## Phase 1 — P2: Unit tests for pattern_matching.py

- [ ] Create `tests/semantic/test_pattern_matching.py`
- [ ] Test coverage targets (each is a separate test function):
  - Simple literal patterns (Int, String, Bool)
  - Variable binding patterns
  - Wildcard (`_`) patterns
  - Struct destructuring patterns
  - Enum variant patterns (with and without payloads)
  - Nested patterns (struct inside enum, enum inside struct)
  - Or-patterns (`A | B => ...`)
  - Guard expressions (`x if x > 0 => ...`)
  - Exhaustiveness checker: complete match (no warning), incomplete match (error)
  - Exhaustiveness checker: redundant arm detection
  - Wildcard-only match (trivially exhaustive)
  - Multiple wildcards (only first reachable)
- [ ] Run `pytest tests/semantic/test_pattern_matching.py -v --cov=mapanare.pattern_matching --cov-report=term-missing`
- [ ] Target: >=90% line coverage of `mapanare/pattern_matching.py`

## Phase 2 — P3: Fix self-hosted guard fall-through divergence

- [ ] Identify the divergence: write a `.mn` test case with a guarded pattern that falls through differently between Python and self-hosted:
  ```mapanare
  fn classify(x: Int) -> String {
      match x {
          n if n > 100 => return "big"
          n if n > 0 => return "positive"
          0 => return "zero"
          _ => return "negative"
      }
  }
  ```
- [ ] Compile with Python bootstrap and capture IR for the match lowering
- [ ] Compile with mnc-stage1 and capture IR for the match lowering
- [ ] `culebra diff` or manual diff to identify the structural divergence
- [ ] Fix `mapanare/self/lower.mn` — align guard fall-through with the decision-tree approach:
  - When a guard evaluates to false, control should jump to the next decision-tree node, not fall through to the next arm sequentially
  - This may require threading the "next candidate" label through the guard emission
- [ ] Rebuild: `bash scripts/rebuild.sh`
- [ ] Verify: the two IR outputs are now structurally equivalent for guarded patterns

## Phase 3 — P6: Unreachable-arm warning test coverage

- [ ] Add tests to `tests/semantic/test_pattern_matching.py` (or a separate `tests/semantic/test_unreachable_arm.py`):
  - Match with a wildcard followed by another arm -> warning on the arm after wildcard
  - Match with two identical literal arms -> warning on the second
  - Match with an enum that covers all variants, followed by a wildcard -> warning on wildcard
  - Match with a guard (guard arms are never unreachable because guards can be false)
  - Verify the warning message contains the arm location (line number)
- [ ] Ensure warnings are captured in test output (may need to check stderr or diagnostic collector)
- [ ] At least 5 test cases covering different unreachable-arm scenarios

## Phase 4 — Rebuild + golden

- [ ] Full rebuild: `bash scripts/rebuild.sh full`
- [ ] Golden tests: all pass (57 or 58 depending on whether v4.78.0 added one)
- [ ] Integration tests (v4.77.0 harness): no regressions
- [ ] `pytest tests/semantic/test_pattern_matching.py -v` — all pass
- [ ] Coverage report shows >=90% for `pattern_matching.py`

## Phase 5 — Update CARRY_FORWARD.md

- [ ] Mark P2 as CLOSED with evidence: "v4.79.0 — `tests/semantic/test_pattern_matching.py` with N tests, >=90% line coverage"
- [ ] Mark P3 as CLOSED with evidence: "v4.79.0 — guard fall-through aligned in `lower.mn`; IR diff shows structural equivalence on guarded patterns"
- [ ] Mark P6 as CLOSED with evidence: "v4.79.0 — 5+ unreachable-arm warning tests in `test_pattern_matching.py` or `test_unreachable_arm.py`"
- [ ] Verify: the only remaining open items are A5 (Culebra-external) and A10 (accepted grammar gap, not a bug)
- [ ] Add summary note: "As of v4.79.0, 0 Mapanare-owned items remain open."

## Phase 6 — LOW sweep + closeout

- [ ] Standard LOW sweep
- [ ] `VERSION` bumped in final commit
- [ ] `CHANGELOG.md [4.79.0]` entry — "Carry-forward ledger at zero: P2, P3, P6 closed. 0 Mapanare-owned open items remain."
- [ ] `SESSION_REPORT.md` written

---

## Exit criteria (10 items)

| # | Check | Evidence |
|---|---|---|
| 1 | P2: `tests/semantic/test_pattern_matching.py` exists | `ls` |
| 2 | P2: >=90% line coverage of `pattern_matching.py` | `--cov-report` output |
| 3 | P3: guard fall-through divergence eliminated | IR diff between Python and self-hosted shows structural equivalence |
| 4 | P3: guarded-pattern golden test passes through both pipelines | test log |
| 5 | P6: >=5 unreachable-arm warning tests pass | `pytest -v` output |
| 6 | P6: warnings verified to contain location information | test assertions |
| 7 | CARRY_FORWARD.md: P2, P3, P6 marked CLOSED | diff |
| 8 | CARRY_FORWARD.md: 0 Mapanare-owned items remain | manual audit |
| 9 | Golden tests all pass | test log |
| 10 | `make test` + `make lint` pass | CI log |

---

## What this release does NOT do

- **Close A5** — Culebra-external. Not Mapanare's to fix.
- **Close A10** — accepted grammar gap (bounded-for sentinels as pseudo-while). Not a bug.
- **New features** — pure test + fix work.
- **Rewrite the pattern matching module** — only add tests and fix the divergence. The Maranget implementation from v4.34.0 is correct; it just lacked tests.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| P3 divergence is deeper than a fall-through issue | medium | medium | Start by characterizing the divergence precisely with IR diffs. If the fix is large, scope to the common cases and track edge cases |
| 90% coverage target requires testing internal helpers that are hard to unit test | medium | low | Cover the public API first; use integration-style tests (compile a .mn snippet, check the lowered output) for internal paths |
| Unreachable-arm detection is not wired in the current codebase | low | medium | Check if the code path exists first. If not, implement it as part of P6 (the item says "zero test coverage", implying the path exists but is untested) |
| P3 fix in `lower.mn` requires self-hosted rebuild that breaks other goldens | medium | high | Run full golden suite after every incremental change; revert if regressions appear |

---

## After v4.79.0

v4.80.0 is the documentation release: async cookbook, SPEC Futures section, gdb tutorial. Addresses recurring Boa panel feedback. The carry-forward ledger is at zero, so v4.80.0 can focus entirely on docs without guilt.
