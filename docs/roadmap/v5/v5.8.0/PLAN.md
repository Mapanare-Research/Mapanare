# Mapanare v5.8.0 — "Sh.7 + B: Closure-Typed + Or-Pattern Fix — 66/66"

> **Close the last 2 failing goldens.** Sh.7 (closure-typed parameters
> in self-hosted `semantic.mn`/`lower.mn`) + B (bootstrap-also-fails
> `51_match_guards_and_or` or-pattern binding-set check). Drives native
> goldens to **66/66** — first time in project history.

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v5.7.0 shipped (Sh.6 tensor closed; v5.5.0–v5.7.0
closed Sh.2/Sh.4/Sh.6 respectively)
**Estimated work:** 1–2 sessions (~3–5 hours). Smallest of the
feature-parity arc.
**Owner dockets:** Sh.7 (opened v4.111.0) + B (opened v4.104.0)

---

## Why this release exists

### The two remaining goldens

From `docs/roadmap/v4/v4.126.0/GOLDEN_TRIAGE.md`:

**Sh.7 — closure-typed (1 test):**

| Test | Error |
|---|---|
| `64_closure_typed` | `Undefined variable 'a'`, `Type mismatch: declared type <fn> but initial value is <fn>` |

Root cause: self-hosted `semantic.mn` and `lower.mn` don't resolve
closure-capture parameters. Python fix landed v4.103.0 (dockets #4,
#5) and has not been mirrored.

**B — bootstrap-also-fails (1 test):**

| Test | Error |
|---|---|
| `51_match_guards_and_or` | `or-pattern alternatives must bind the same names: extra ['None']` |

Root cause: Python bootstrap's semantic check rejects a valid pattern.
The harness can't establish a reference IR for a test the bootstrap
itself rejects. Fixing this is a *Python*-side fix, not a self-hosted
port.

### What 66/66 means

First release in Mapanare's history where `mnc-stage1` passes every
golden test. Closes the final parity gap between Python bootstrap and
self-hosted compiler for the golden corpus. Does NOT mean the
self-hosted compiler is feature-complete — LICM (Li.1), some runtime
deprecations, and v6.0-era work remain. But for the specific test
corpus that defines "self-hosting," we'll be at 100%.

---

## Scope

### What ships

#### 8.0a — Sh.7: closure-typed parameters

Two parts:

**Python reference** (`mapanare/lower.py` + `mapanare/semantic.py`):
the v4.103.0 fix resolved closure-capture parameters — when a closure
is passed as a function argument and then invoked, the callee must
know the closure's captured-env type signature to generate correct
env-pointer loads. Grep:

```bash
grep -n "closure.*param\|capture.*param\|ClosureParam" mapanare/semantic.py \
  mapanare/lower.py
```

**Self-hosted port** (`mapanare/self/semantic.mn` +
`mapanare/self/lower.mn`): mirror the resolution pattern. Estimated
~80 LOC total.

#### 8.0b — B: or-pattern binding-set fix

The failing case is syntactically:

```mapanare
match opt {
    Some(x) | None => { ... }
    _ => { ... }
}
```

The Python check at `mapanare/semantic.py` (grep for `or-pattern
alternatives must bind the same names`) is too strict. It flags the
binding-set mismatch `{x}` vs `{}` as an error when the correct
behavior is: an or-pattern is valid only if it binds the **same**
names, but the fix is making the diagnostic apply correctly — the
specific `51_match_guards_and_or.mn` case has a guard condition that
the current check is confused by.

Grep:

```bash
grep -n "or-pattern\|or_pattern" mapanare/semantic.py
cat tests/golden/51_match_guards_and_or.mn
```

**Python-side fix.** After fixing, re-generate the reference IR:

```bash
python3 scripts/test_native.py --bless --filter 51_match_guards_and_or
```

Then mirror the fix into `mapanare/self/semantic.mn` if the
self-hosted compiler has the same overly-strict check (likely yes,
since self-hosted was ported from Python).

#### 8.0c — Celebrate

A 66/66 badge in README. Post-release note somewhere visible.

**Expected LOC:**

| File | ~LOC |
|---|---:|
| `mapanare/semantic.py` — or-pattern check | ~15 |
| `mapanare/lower.py` — closure-typed resolution (if not already complete) | ~30 |
| `mapanare/self/semantic.mn` — mirror both fixes | ~70 |
| `mapanare/self/lower.mn` — closure-typed resolution | ~50 |
| **Total** | **~165** |

### What does NOT ship

- **New closure features.** Only the parity fix.
- **New pattern-matching features.** Only the or-pattern check fix.
- **LICM (Li.1).** Deferred per CLOSEOUT_ARC.md.
- **Own.1 Phase 3 / full borrow checker.** v6.0 scope.

---

## Exit criteria

1. **66/66 native goldens** via `mnc-stage1`.
2. `51_match_guards_and_or` passes both bootstrap and mnc-stage1.
3. `64_closure_typed` passes mnc-stage1.
4. Strict 3-stage fixed-point holds.
5. Non-bootstrap pytest 0 failures (down from "byte-identical failure
   set" to actually 0).
6. `make lint` clean.
7. `PARITY_GAPS.md` moves Sh.7 to Historical; or-pattern fix listed
   in release notes.
8. README goldens badge updated to 66/66.

---

## Design decisions

### D1 — Python fix first, then self-hosted mirror

The B (or-pattern) fix touches `mapanare/semantic.py`. The
self-hosted mirror may pre-date the broken check — verify before
editing. If yes, mirror. If no, only Python changes.

### D2 — Closure-typed port follows v4.103.0 pattern

v4.103.0 dockets #4 and #5 documented the Python fix. Mirror both
directly to self-hosted.

### D3 — Re-bless the 51 reference

After fixing Python semantic, the reference IR for
`51_match_guards_and_or` changes. Re-run
`scripts/test_native.py --bless --filter 51_match_guards_and_or`.

### D4 — Tests

- Existing goldens 51 + 64 cover the fixes.
- Add a parser+semantic test `tests/semantic/test_or_pattern_guards.py`
  with 5+ cases proving the check accepts valid patterns and still
  rejects binding-set mismatches.
- Add a semantic test for closure-typed params:
  `tests/semantic/test_closure_typed_params.py` with 3+ cases.

---

## Risks

- **R1 — Python or-pattern fix is non-trivial.** The check might be
  load-bearing for other tests. Verify full pytest 0 failures after
  the fix.
- **R2 — Fixed-point breaks.** New emission in semantic for
  closure-typed. Mitigation: `verify_fixed_point.sh --keep`.
- **R3 — 51's new reference IR may be unstable.** If Python's fix
  produces IR that's not byte-equal across runs, the harness will
  keep failing. Test `test_native.py --bless` stability first.

---

## What NOT to do

- Do not add new pattern-matching syntax or semantics.
- Do not "improve" the or-pattern check beyond fixing the 51 case.
  Minimal surgical fix.
- Do not defer the README 66/66 update — the badge is the
  human-visible signal that the closure arc completed.
- Do not amend the v5.5.0/v5.6.0/v5.7.0 plans retroactively. This
  release stands on its own.
