# Mapanare v5.6.11 — "Ve.4 close — match-arm verifier error"

> **Final v5.6.x closeout release.** v5.6.9 closed Ve.3 and surfaced
> Ve.4: match-arm lowering produces empty BasicBlocks in the
> self-hosted compiled lowerer. The MIR verifier rejects with
> `<fn>::match_arm<N>: block has no instructions` before stage3 IR
> emission can begin. v5.6.10 deliberately deferred Ve.4 to bundle
> Ve.2 residuals + struct_byte_size + culebra baseline; v5.6.11
> closes Ve.4 and re-evaluates the full self-compile fixed-point.

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v5.6.10 shipped (Ve.2 partial closure 18 → 7 sites;
struct_byte_size hardened; culebra baseline frozen; Lk.1 opened).
**Estimated work:** 1–2 sessions (~3–5 hours).
**Owner docket:** Ve.4 (opened v5.6.9, deferred from v5.6.10).

---

## Why this release exists

### Ve.4 is the last v5.6.x blocker

Per `docs/known_issues.md` Ve.4 row:

> match-arm lowering produces empty BasicBlocks in self-hosted
> compiled lowerer. With Ve.3 closed, `mnc-stage2 mnc_all.mn` and
> any 2-arm-match test program hit `<fn>::match_arm<N>: block has
> no instructions` MIR verifier error before stage3 emission.
> Reproduces on the **original v5.6.8 binary** — confirms this bug
> existed in v5.6.8 but was masked by Ve.3's earlier OOM.

Closing Ve.4 unblocks:
1. `mnc_all.mn → stage3.ll` non-empty IR (currently 0 lines).
2. `verify_fixed_point.sh` strict-or-near comparison vs stage2.ll.
3. The v5.7.0 closure-typed work (which depends on
   semantic.mn's match expressions compiling correctly through
   the self-hosted pipeline).

### What's already known

From v5.6.9 SESSION_REPORT and Phase 0 of v5.6.10:

- **Reproducer**: `/tmp/p3.mn` — a 2-arm enum match like:
  ```mn
  enum Op { Add, Sub }
  fn apply(o: Op) -> Int {
      match o {
          Op::Add => { return 1 },
          Op::Sub => { return 2 }
      }
  }
  fn main() { print(str(apply(Op::Add))) }
  ```
- **Symptom**: `mnc-stage2 /tmp/p3.mn` → MIR verifier rejects with
  `apply::match_arm2: block has no instructions`.
- **Stack overflow caveat**: under default 8 MB stack,
  `mnc-stage2` SIGSEGVs at a stack address before the verifier
  fires. `ulimit -s unlimited` is required to surface the actual
  cause.
- **Python-built stage1 is correct**: goldens 64/66 pass through
  the Python pipeline. The bug is in how stage1 compiled the
  self-hosted lowerer's match-arm-handling code into stage2.ll —
  the source code in `mapanare/self/lower.mn` is correct.
- **Reproduces on v5.6.8 binary**: the bug is pre-existing,
  masked by Ve.3 until v5.6.9 closed it.

### Active hypothesis

A MIR pass post-lowering (likely `dead_block_elim_function` or
an interaction with `inline_small_functions` in `mir_opt.mn`)
drops instructions from match arms whose body is a single tail
expression (`return X`, `Some(X)`, etc.). The Python bootstrap's
mir_opt doesn't have this bug; the self-hosted version compiled
into stage2.ll does.

Possible mechanisms:
- **`dead_block_elim_function`** sees a basic block with no
  predecessors and removes it; if the match dispatch's case
  arrows reference it via switch labels (not edges), the pass
  may incorrectly classify it as dead.
- **`inline_small_functions`** clones a function body that
  contains a match; the clone path may drop instructions from
  arms whose body is a single tail expression because the inline
  rewriter doesn't preserve the dispatcher's switch references.
- **Match-arm lowering in `lower.mn` itself** may emit instructions
  that get correctly stored in MIR but lost during stage1's
  IR emission (alloca-aliasing or store-after-free in the BasicBlock
  list).

The PLAN scopes investigation across all three. The fix shape
depends on which mechanism fires.

---

## Scope

### What ships

#### 9.11a — Ve.4 reproducer + instrumentation (~30 min)

1. Create `/tmp/p3.mn` with a minimal 2-arm enum match.
2. Verify reproduction:
   ```bash
   ulimit -s unlimited
   mapanare/self/mnc-stage2 /tmp/p3.mn 2>&1 | head -20
   # Expected: error: MIR verifier detected malformed IR before emission:
   #            apply::match_arm2: block has no instructions
   ```
3. Instrument with `__mn_str_eprint`:
   - `lower.mn::lower_match_arms` — what instructions are added
     to each arm's BasicBlock at lower time (block label, instr
     count, kinds).
   - `mir_opt.mn::dead_block_elim_function` — which blocks get
     removed.
   - `mir_opt.mn::clone_instr_for_inline` Branch arm — what gets
     cloned for inlined match arms.
   - `mir_opt.mn::inline_small_functions` — which fns get inlined
     and what blocks they produce.
   - `mir.mn::verify_function` — log block label + instr count
     just before the verifier rejects.

#### 9.11b — Identify which pass empties the arm (~60 min)

Run the instrumented stage1 → stage2 → stage2 binary on `/tmp/p3.mn`
and trace:

1. **At lower time**: are the match arm BBs populated correctly?
   Expected: each arm has at least 1 instruction (the body's
   `Return(Some(...))`).

2. **At MIR after lowering, before opt**: still populated?
   Expected: same as lower time.

3. **After `dead_block_elim_function`**: still populated?
   If empty, this is the culprit.

4. **After `inline_small_functions`**: still populated?
   If empty after inline but populated before, this is the culprit.

5. **At verify time**: which arm is empty? Which fn?

The trace will isolate the pass. Three likely paths:

| Pass | Likely fix shape |
|---|---|
| `dead_block_elim_function` | Skip arm BBs (whose label starts with `match_arm`) from the pass, OR add the dispatcher's switch references as proper predecessors. |
| `clone_instr_for_inline` | Preserve the dispatcher's switch labels as predecessor edges in the clone. |
| `inline_small_functions` | Don't inline functions containing match expressions, OR fix the inline rewriter to preserve match dispatch. |
| `lower.mn` match-arm emission | Add the missing instructions; preserve via stage1 emit. |

#### 9.11c — Apply targeted fix (~60 min)

The fix shape depends on 9.11b's findings. Examples:

**If `dead_block_elim_function`**:
```mn
fn dead_block_elim_function(fn_blocks: List<BasicBlock>) -> List<BasicBlock> {
    // v5.6.11 — skip match-arm blocks. Their predecessors are
    // the dispatcher's switch case labels, not control-flow edges.
    let mut keep: List<BasicBlock> = []
    for bb in fn_blocks {
        if bb.label.starts_with("match_arm") || has_predecessor(bb, fn_blocks) {
            keep.push(bb)
        }
    }
    return keep
}
```

**If `clone_instr_for_inline`**:
Add a Branch case for `MatchDispatch` (or whatever the dispatcher
emits as) that clones its switch labels into the inlined function's
fresh-name namespace.

**If `lower.mn`**: the match-arm body wasn't fully emitted in the
first place — find the missing `emit_instr` call.

#### 9.11d — Verify fix on reproducer + goldens (~30 min)

```bash
mapanare/self/mnc-stage2 /tmp/p3.mn > /tmp/p3.ll
echo "RC=$?"
llvm-as /tmp/p3.ll -o /dev/null && echo "p3 llvm-as OK"

# 2-arm match should now produce non-empty IR for both arms
grep -A 3 "match_arm" /tmp/p3.ll
```

Run goldens:
```bash
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1
# expect 64/66 preserved
```

#### 9.11e — Re-evaluate fixed-point (~15 min)

```bash
ulimit -s unlimited
bash scripts/verify_fixed_point.sh --keep
# Expected: STRICT or NEAR
# (was: stage3 SIGSEGV at default stack, MIR verifier error
#  under unlimited stack)
```

If STRICT or NEAR, this is the v5.6.11 hero metric: the full
self-compile fixed-point is restored after 7 releases (v5.6.4 →
v5.6.11) of being broken.

#### 9.11f — Sanitizer + lint gate (~30 min)

Per the v5.6.10 PROMPT D2 pattern (any sanitizer regression →
revert):

```bash
ASAN_OUTDIR=/tmp/asan-v5.6.11 bash scripts/run_asan_goldens.sh
# expect 0 ASAN_ERROR

VG_OUTDIR=/tmp/vg-v5.6.11 bash scripts/valgrind_all_goldens.sh
# expect 0 ERRORS

ASAN_LEAK_OUTDIR=/tmp/asan-leak-v5.6.11 bash scripts/run_asan_leak_goldens.sh
python3 scripts/check_leak_summary.py /tmp/asan-leak-v5.6.11/asan-leak-summary.tsv
# expect PASS

python3 -m pytest tests/ --ignore=tests/bootstrap -q --tb=no
make lint
python3 scripts/check_struct_registry.py
```

#### 9.11g — Documentation (~30 min)

- `docs/roadmap/v5/v5.6.11/SESSION_REPORT.md` — full trace +
  hypothesis matrix + per-phase gate results.
- `docs/known_issues.md` — flip Ve.4 row to **CLOSED v5.6.11**.
- `docs/roadmap/v5/PARITY_GAPS.md` — move Ve.4 to Historical.
- `CLAUDE.md` — v5.6.11 entry; "Current baseline" → 5.6.11;
  Planned section: drop v5.6.11 (now shipped), highlight v5.7.0
  as next.
- `docs/roadmap/ROADMAP.md` — v5.6.11 "Where We Are" stanza.

### What does NOT ship

- **Lk.1 closure** — alloca-aliasing in inline list-get/push.
  v6.0 borrow-checker scope per v5.6.10 known_issues.md.
- **Ve.2 residual 7 sites** — block on Lk.1.
- **Floor branch removal** — depends on Ve.2 residual closure.
- **Sh.7 / B closure work** — v5.7.0.
- **noalias on byref params** — tracked separately.

---

## Exit criteria

1. `mnc-stage2 /tmp/p3.mn` produces non-empty `llvm-as`-clean IR
   for the 2-arm enum match (was: 0 lines, MIR verifier error).
2. `mnc-stage2 mnc_all.mn` produces non-empty stage3.ll (was:
   SIGSEGV under default stack; verifier error under unlimited
   stack).
3. `verify_fixed_point.sh --keep` reaches STRICT or NEAR
   (preferably STRICT — the v4.134.0 baseline).
4. Goldens 64/66 preserved (no regressions on the same 2
   pre-existing fails: 51_match_guards_and_or B, 64_closure_typed
   Sh.7).
5. stage2.ll growth ≤ 3% vs v5.6.10 (216,932 lines). The fix
   shape depends on 9.11b but expected to be a small targeted
   change.
6. ASan UAF sweep: 65 CLEAN / 0 ASAN_ERROR / 1 CRASH_NO_ASAN
   (matches v5.6.10 baseline).
7. Valgrind sweep: 0 ERRORS / 66 WARNINGS_ONLY (matches v5.6.10).
8. LSan baseline gate: PASS (no regressions vs v5.4.2 baseline;
   62_list_output stays at 9 / 141 B per Rt.04 v5.6.6 RESCOPE;
   65_list_int_indexing stays CLEAN per Lk.1 deferral).
9. Non-bootstrap pytest 0 failures (matches v5.6.10's 5590 passed).
10. `make lint` clean.
11. `check_struct_registry.py` 23/23/91 clean.
12. `docs/known_issues.md` Ve.4 row flipped to CLOSED v5.6.11.
13. `docs/roadmap/v5/PARITY_GAPS.md` moves Ve.4 to Historical.

---

## Design decisions

### D1 — Investigate before fixing

Three plausible mechanisms (`dead_block_elim_function`,
`clone_instr_for_inline`, `inline_small_functions`, lower.mn
emission). Each has a different fix shape. Per the user's "no
cheap shit" directive, instrument first to identify the precise
culprit; don't ship a speculative fix that papers over the wrong
mechanism.

The investigation strategy is the same one that closed Ve.3 in
v5.6.9: targeted `__mn_str_eprint` at trace points. Per v5.6.9
SESSION_REPORT's culebra-vs-eprint comparison, eprint
instrumentation gives a definitive answer in one rebuild cycle
(~2 minutes); culebra would have taken 40+ minutes for less
specificity.

### D2 — Fix at the precise location, not broadly

If `dead_block_elim_function` is the culprit, the fix is a
targeted skip for `match_arm` blocks — NOT a wholesale disable
of the pass. The pass is correct in general; only the match-arm
predecessor model is wrong.

Same logic for the other candidate paths.

### D3 — Fixed-point gate is the hero metric

Once Ve.4 closes, `verify_fixed_point.sh` should reach STRICT
(stage2.ll == stage3.ll) or NEAR (within DIFF_THRESHOLD). This
has been broken since v5.6.4 — restoring it is the v5.6.11
release-defining metric.

### D4 — Don't bundle Lk.1 work

Lk.1 (alloca-aliasing in inline list-get/push) is structurally
v6.0 work. Bundling it into v5.6.11 would risk a UAF surface
similar to v5.6.6's Rt.04 attempt. Defer to v6.0 borrow checker.

### D5 — Don't broaden the v5.6.10 emit_drop_glue conservatism

v5.6.9's Ve.3 fix gates drop-skip on `boxed_owned`. Broadening
to also gate on `str_owned` reproduced Ve.4 on programs as small
as a 2-arm match — confirming the broadening surfaces the same
underlying bug class. v5.6.11's fix should not require touching
the drop-glue gate.

---

## Risks

- **R1 — The bug is in lower.mn itself, not mir_opt.** If
  match-arm body emission is incomplete at lower time, the fix
  is in lower.mn — but stage1 (Python-built) lowers correctly,
  suggesting lower.mn's source is correct and the bug is in how
  stage1 compiled it. Mitigation: instrumentation at lower time
  rules in/out this path.
- **R2 — The bug is in stage1's IR emission of mir_opt code,
  not in mir_opt's source logic.** I.e., when stage1 compiles
  `dead_block_elim_function` (or wherever the bug is) into
  stage2.ll, the compiled IR has a subtle bug that surfaces
  only on match-arm-heavy inputs. This is harder — the fix
  would be in `emit_llvm.mn`, not `mir_opt.mn`. Mitigation:
  IR inspection of the suspect function in stage2.ll for any
  pattern that mismatches the source.
- **R3 — Closing Ve.4 surfaces a NEW bug** (e.g., now stage3.ll
  is non-empty but its IR has a different problem). Mitigation:
  full sanitizer + golden + fixed-point gate, same as v5.6.10.
- **R4 — The fix grows stage2.ll beyond the 3% budget.** A
  hypothetical broad change to the inliner could inflate IR
  significantly. Mitigation: scope the fix to the precise
  mechanism (D2); revert if growth exceeds budget without
  observable benefit (per v5.6.8 precedent).

---

## What NOT to do

- Do not bundle Lk.1 closure. v6.0 scope.
- Do not bundle Ve.2 residual closure. Blocked by Lk.1.
- Do not broaden the emit_drop_glue conservatism gate. v5.6.9's
  `boxed_owned`-only condition is the right shape; broadening
  reproduces Ve.4 (per v5.6.9 finding).
- Do not skip the fixed-point gate. The hero metric for v5.6.11
  is restoring strict-or-near fixed-point.
- Do not commit `/tmp/*` artifacts. Diagnostic outputs go in
  `docs/roadmap/v5/v5.6.11/`.
- Do not tag without user approval.
- Do not push without user approval.
- Do not add features. v5.6.x is closeout.
