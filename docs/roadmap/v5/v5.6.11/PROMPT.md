# v5.6.11 Execution Prompt — Ve.4 close (match-arm verifier error)

> Read `PLAN.md` first. Single-focus release: close the match-arm
> verifier error blocking the full self-compile fixed-point.
>
> Estimated: 1–2 sessions (~3–5 hours). Investigation-first per
> v5.6.9's culebra-vs-eprint lesson: instrument trace points,
> identify the precise pass, apply targeted fix.

---

## Read before starting

1. `docs/roadmap/v5/v5.6.11/PLAN.md` — this release's plan.
2. `docs/roadmap/v5/v5.6.9/SESSION_REPORT.md` — Ve.3 closure +
   Ve.4 opening. Note especially §"Ve.4 — match-arm verifier
   error (newly opened)" for the reproducer details.
3. `docs/roadmap/v5/v5.6.10/SESSION_REPORT.md` — for the
   eprint instrumentation pattern that closed Ve.3.
4. `docs/known_issues.md` Ve.4 row — symptom + reproduction
   conditions.
5. `mapanare/self/lower.mn` match-arm lowering functions
   (`build_match_arms`, `lower_match_arm`).
6. `mapanare/self/mir_opt.mn` candidate passes
   (`dead_block_elim_function`, `inline_small_functions`,
   `clone_instr_for_inline` Branch case).
7. `mapanare/self/mir.mn::verify_function` — where the verifier
   error originates.

---

## Environment

**WSL2 required**. All commits land on `dev`. Tagging + pushing
requires explicit user approval.

`ulimit -s unlimited` is required for any `mnc-stage2 mnc_all.mn`
run — under the default 8 MB stack the SIGSEGV masks the
verifier error.

---

## GitNexus pre-flight (MANDATORY before edit)

```bash
npx gitnexus analyze
```

```
gitnexus_impact({target: "build_match_arms", direction: "upstream"})
gitnexus_impact({target: "dead_block_elim_function", direction: "upstream"})
gitnexus_impact({target: "clone_instr_for_inline", direction: "upstream"})
gitnexus_impact({target: "inline_small_functions", direction: "upstream"})
gitnexus_impact({target: "verify_function", direction: "upstream"})
gitnexus_query({query: "match arm basic block lowering empty"})
```

`build_match_arms` and the mir_opt passes are HIGH-impact (consumed
by every function compilation). Treat as load-bearing.

---

## Phase 0 — Reproducer + baseline (~15 min)

```bash
echo "5.6.11" > VERSION
make build-rt

# Snapshot v5.6.10 baseline state
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1 \
    2>&1 | tee /tmp/v5.6.11-goldens-before.log
grep -c "^PASS" /tmp/v5.6.11-goldens-before.log    # expect 64

mapanare/self/mnc-stage1 mapanare/self/mnc_all.mn > /tmp/stage2-v5.6.11-before.ll
wc -l /tmp/stage2-v5.6.11-before.ll                # expect ~216,932 lines (v5.6.10)
llvm-as /tmp/stage2-v5.6.11-before.ll -o /dev/null && echo OK

# Build a stage2 binary from stage2.ll
clang -O2 /tmp/stage2-v5.6.11-before.ll \
    runtime/native/libmapanare_rt.a -lpthread -lm -ldl \
    -o /tmp/mnc-stage2-v5.6.10
```

Create the reproducer:
```mn
// /tmp/p3.mn
enum Op { Add, Sub }
fn apply(o: Op) -> Int {
    match o {
        Op::Add => { return 1 },
        Op::Sub => { return 2 }
    }
}
fn main() { print(str(apply(Op::Add))) }
```

Verify Ve.4 reproduces:
```bash
ulimit -s unlimited
/tmp/mnc-stage2-v5.6.10 /tmp/p3.mn 2>&1 | head -10
# Expected: error: MIR verifier detected malformed IR before emission:
#            apply::match_arm2: block has no instructions
```

Create the v5.6.11 directory + commit:
```bash
git add VERSION docs/roadmap/v5/v5.6.11/PLAN.md \
    docs/roadmap/v5/v5.6.11/PROMPT.md
git commit -m "v5.6.11: version bump — Ve.4 close planning"
```

---

## Phase 1 — Instrumentation (~30 min)

Add `__mn_str_eprint` calls at trace points. Per v5.6.9's lesson,
keep instrumentation tight — 4–6 points should be enough to
isolate the failure.

### 1.1 — `lower.mn::build_match_arms` (or `lower_match_arm`)

Trace what gets emitted for each arm:

```mn
fn build_match_arms(...) -> MatchBuildResult {
    ...
    for arm_idx in 0..len(arms) {
        let arm: MatchArm = arms[arm_idx]
        // ... existing arm body lowering ...

        // v5.6.11 Ve.4 instrumentation
        let arm_label: String = "match_arm" + toString(arm_idx + 1)
        __mn_str_eprint("DBG lower arm: label=" + arm_label
            + " bb_idx=" + toString(s.current_block_idx)
            + " ninstrs=" + toString(len(s.fn_blocks[s.current_block_idx].instructions))
            + "\n")
    }
    ...
}
```

### 1.2 — `mir_opt.mn::dead_block_elim_function`

```mn
fn dead_block_elim_function(blocks: List<BasicBlock>) -> List<BasicBlock> {
    __mn_str_eprint("DBG dead_block_elim: in_count=" + toString(len(blocks)) + "\n")
    let mut keep: List<BasicBlock> = []
    for bb in blocks {
        let kept: Bool = should_keep_block(bb, blocks)
        if !kept {
            __mn_str_eprint("DBG dead_block_elim: removing label=" + bb.label
                + " ninstrs=" + toString(len(bb.instructions)) + "\n")
        }
        if kept { keep.push(bb) }
    }
    __mn_str_eprint("DBG dead_block_elim: out_count=" + toString(len(keep)) + "\n")
    return keep
}
```

### 1.3 — `mir_opt.mn::clone_instr_for_inline` Branch arm

```mn
match instr {
    Branch(label) => {
        __mn_str_eprint("DBG clone_inst Branch: target=" + label + "\n")
        ...
    },
    ...
}
```

### 1.4 — `mir_opt.mn::inline_small_functions`

```mn
fn inline_small_functions(...) -> ... {
    for callee in candidates {
        __mn_str_eprint("DBG inline: caller=" + caller_name
            + " callee=" + callee.name
            + " body_blocks=" + toString(len(callee.blocks)) + "\n")
        ...
    }
}
```

### 1.5 — `mir.mn::verify_function`

```mn
fn verify_function(fn: MIRFunction) -> List<VerifyError> {
    let mut errors: List<VerifyError> = []
    for bb in fn.blocks {
        __mn_str_eprint("DBG verify: fn=" + fn.name + " label=" + bb.label
            + " ninstrs=" + toString(len(bb.instructions)) + "\n")
        if len(bb.instructions) == 0 {
            errors.push(new_verify_error(fn.name, bb.label, "block has no instructions"))
        }
    }
    return errors
}
```

### 1.6 — Rebuild and run

```bash
bash scripts/concat_self.sh && python3 scripts/build_stage1.py 2>&1 | tail -3

# Build stage2 binary with instrumented stage1
mapanare/self/mnc-stage1 mapanare/self/mnc_all.mn > /tmp/stage2-instrumented.ll
clang -O2 /tmp/stage2-instrumented.ll \
    runtime/native/libmapanare_rt.a -lpthread -lm -ldl \
    -o /tmp/mnc-stage2-instrumented

# Run on reproducer
ulimit -s unlimited
/tmp/mnc-stage2-instrumented /tmp/p3.mn 2> /tmp/p3-trace.txt
echo "RC=$?"
head -100 /tmp/p3-trace.txt
```

The trace should show, for each match arm:
1. `DBG lower arm: ... ninstrs=N` — N > 0 (arm is populated at lower time)
2. `DBG dead_block_elim: removing label=match_arm2 ninstrs=N` — if this
   appears, dead_block_elim is the culprit.
3. `DBG inline: ...` — if a function with match gets inlined right
   before the verifier fails, inline is the culprit.
4. `DBG verify: ... ninstrs=0` — confirms which arm is empty at
   verify time.

---

## Phase 2 — Identify the culprit pass (~30 min)

Read the trace and identify the transition where an arm goes from
`ninstrs=N` to `ninstrs=0`.

Three likely outcomes:

### Outcome A: Empty at lower time

Arm is empty even at `lower arm` trace. Bug is in
`build_match_arms` or `lower_match_arm`. Fix is in lower.mn.

### Outcome B: Empty after `dead_block_elim_function`

Arm is populated at lower time but empty after the pass. Bug is
in the pass's predecessor model — match-arm BBs have implicit
predecessors via the dispatcher's switch labels, not explicit
edges.

Fix shape:
```mn
fn dead_block_elim_function(blocks: List<BasicBlock>) -> List<BasicBlock> {
    let mut keep: List<BasicBlock> = []
    for bb in blocks {
        // v5.6.11 Ve.4 — match-arm BBs are reached via switch labels
        // in the dispatcher, not explicit Branch edges. Keep them.
        if bb.label.starts_with("match_arm") {
            keep.push(bb)
            continue
        }
        if has_predecessor(bb, blocks) {
            keep.push(bb)
        }
    }
    return keep
}
```

### Outcome C: Empty after `inline_small_functions`

Arm is populated before inline but empty after. Bug is in the
inline rewriter's handling of match dispatch.

Fix shape: skip inlining for functions containing match arms,
OR add proper dispatch-rewriting in `clone_instr_for_inline`.

The simplest gate (matches v5.5.4's pattern for async fns):
```mn
fn should_inline(callee: MIRFunction) -> Bool {
    // ... existing checks ...
    // v5.6.11 Ve.4 — match-arm dispatch breaks the inline rewriter.
    // Skip until v6.0 borrow checker covers MIR-level alias analysis.
    if has_match_arm_blocks(callee) { return false }
    return true
}
```

### Outcome D: Source code is correct, stage1's IR emission is buggy

If trace shows the source-level pass logic is correct but stage2.ll's
compiled version of the pass produces empty arms, the bug is in
`emit_llvm.mn` for whichever construct the pass uses (likely
`for bb in blocks` iteration over `List<BasicBlock>`). This is
a harder fix in the emitter rather than mir_opt.

---

## Phase 3 — Apply targeted fix (~60 min)

Edit the precise location identified in Phase 2. Mirror the
v5.6.9 / v5.6.6 RESCOPE pattern: minimal diff, comprehensive
comment explaining the bug and fix.

```mn
// v5.6.11 Ve.4 — <one-sentence bug summary>
//
// Background: <2-3 sentences on the mechanism>.
//
// Fix: <1-2 sentences on the change>.
//
// Cost: <if any — leak vs UAF tradeoff, IR growth, etc.>.
```

Remove instrumentation:
```bash
grep -n "DBG.*Ve.4\|__mn_str_eprint" mapanare/self/lower.mn mapanare/self/mir_opt.mn mapanare/self/mir.mn
# Remove all hits before commit
```

Rebuild:
```bash
bash scripts/concat_self.sh && python3 scripts/build_stage1.py 2>&1 | tail -3

mapanare/self/mnc-stage1 mapanare/self/mnc_all.mn > /tmp/stage2-v5.6.11.ll
echo "stage2.ll lines: $(wc -l < /tmp/stage2-v5.6.11.ll)"
llvm-as /tmp/stage2-v5.6.11.ll -o /dev/null && echo OK
```

Build stage2 binary and re-test reproducer:
```bash
clang -O2 /tmp/stage2-v5.6.11.ll \
    runtime/native/libmapanare_rt.a -lpthread -lm -ldl \
    -o /tmp/mnc-stage2-v5.6.11

ulimit -s unlimited
/tmp/mnc-stage2-v5.6.11 /tmp/p3.mn > /tmp/p3.ll 2>&1
echo "RC=$?"
echo "Lines: $(wc -l < /tmp/p3.ll)"
llvm-as /tmp/p3.ll -o /dev/null && echo "p3 llvm-as OK"

# Should show non-empty match arm BBs
grep -A 2 "match_arm" /tmp/p3.ll | head -30
```

Expected: `RC=0`, `llvm-as OK`, both match arms have instructions.

---

## Phase 4 — Goldens + fixed-point gate (~15 min)

```bash
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1 \
    2>&1 | tee /tmp/v5.6.11-goldens-after.log
diff /tmp/v5.6.11-goldens-before.log /tmp/v5.6.11-goldens-after.log | head
# expect: only timing variation; same 64/66
```

Hero metric — fixed-point:
```bash
ulimit -s unlimited
bash scripts/verify_fixed_point.sh --keep 2>&1 | tee /tmp/v5.6.11-fp.log
tail -10 /tmp/v5.6.11-fp.log
# Expected: STRICT or NEAR (was: stage3 SIGSEGV / verifier error)
```

If FIXED-POINT REACHED, this is the v5.6.11 release-defining
metric. Document it prominently.

---

## Phase 5 — Sanitizer gate (~30 min)

```bash
# Rebuild ASan binary
bash scripts/build_asan.sh 2>&1 | tail -3

# Run all three sweeps in parallel
ASAN_OUTDIR=/tmp/asan-v5.6.11 bash scripts/run_asan_goldens.sh &
VG_OUTDIR=/tmp/vg-v5.6.11 bash scripts/valgrind_all_goldens.sh &
ASAN_LEAK_OUTDIR=/tmp/asan-leak-v5.6.11 bash scripts/run_asan_leak_goldens.sh &
wait

awk '$2 == "ASAN_ERROR"' /tmp/asan-v5.6.11/asan-summary.tsv | wc -l   # expect 0
awk '$2 == "ERROR"' /tmp/vg-v5.6.11/valgrind-summary.tsv | wc -l       # expect 0
python3 scripts/check_leak_summary.py \
    /tmp/asan-leak-v5.6.11/asan-leak-summary.tsv 2>&1 | tail -3
# expect PASS

python3 -m pytest tests/ --ignore=tests/bootstrap -q --tb=no 2>&1 | tail -3
make lint 2>&1 | tail -3
python3 scripts/check_struct_registry.py 2>&1 | tail -2
```

Per PROMPT D2: if any sanitizer regresses, REVERT. (Same gate
discipline as v5.6.10.)

---

## Phase 6 — Documentation (~30 min)

- `docs/roadmap/v5/v5.6.11/SESSION_REPORT.md` — write per the
  v5.6.10 SESSION_REPORT template. Cite the exact trace lines
  showing the bad transition. If fixed-point reached, lead with
  that as the hero metric.
- `docs/known_issues.md` — flip Ve.4 row to **CLOSED v5.6.11**.
  Update the header date.
- `docs/roadmap/v5/PARITY_GAPS.md` — move Ve.4 to Historical.
- `CLAUDE.md` — v5.6.11 entry; "Current baseline" → 5.6.11;
  Planned section: drop v5.6.11; highlight v5.7.0 (Sh.7 + B
  or-pattern → 66/66) as next.
- `docs/roadmap/ROADMAP.md` — v5.6.11 "Where We Are" stanza,
  prepended.
- `docs/roadmap/v5/CLOSEOUT_ARC.md` — note v5.6.x arc fully
  closed (all v5.6.x dockets resolved or deferred to v6.0).

---

## Ready-to-ship checklist

- [ ] `VERSION` reads `5.6.11`
- [ ] `mnc-stage2 /tmp/p3.mn` produces non-empty `llvm-as`-clean IR
- [ ] `mnc-stage2 mnc_all.mn` produces non-empty stage3.ll
- [ ] `verify_fixed_point.sh --keep` reaches STRICT or NEAR
- [ ] Harness 64/66 preserved
- [ ] stage2.ll growth ≤ 3% vs v5.6.10
- [ ] `llvm-as` clean
- [ ] Valgrind 0 ERRORS / 66 WARNINGS_ONLY
- [ ] ASan UAF 0 ASAN_ERROR / 65 CLEAN / 1 CRASH_NO_ASAN
- [ ] LSan baseline gate PASS
- [ ] Non-bootstrap pytest 0 failures
- [ ] `make lint` clean
- [ ] `check_struct_registry.py` 23/23/91 clean
- [ ] All instrumentation `__mn_str_eprint` calls removed
- [ ] `known_issues.md` Ve.4 row → CLOSED v5.6.11
- [ ] `PARITY_GAPS.md` moves Ve.4 to Historical
- [ ] SESSION_REPORT written
- [ ] CLAUDE.md + ROADMAP.md entries added
- [ ] No `/tmp/*` artifacts committed

---

## Commit + tag + push

```bash
git diff --cached --stat
gitnexus_detect_changes({scope: "staged"})

git commit -m "$(cat <<'EOF'
v5.6.11: Ve.4 CLOSED — match-arm verifier error

<Insert hero metric here, e.g.:>
Closes the v5.6.4-era self-compile fixed-point blocker. Root cause:
<X> — <bug summary>. Fix: <Y> — <change summary>.

Hero metric: verify_fixed_point.sh STRICT/NEAR (was: stage3.ll empty
since v5.6.4). The full self-compile cycle now produces matching
stage2.ll == stage3.ll within tolerance.

Goldens 64/66 preserved; full sanitizer gate clean; LSan baseline
unchanged. v5.6.x arc fully closed.

What's next: v5.7.0 — Sh.7 closure-typed + B or-pattern → 66/66.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"

# Tag + push require explicit user approval
```

After push:
```bash
npx gitnexus analyze
```

---

## What NOT to do

- Do not bundle Lk.1 closure. v6.0 scope.
- Do not bundle Ve.2 residual closure. Blocked by Lk.1.
- Do not broaden the v5.6.9 emit_drop_glue conservatism gate
  (the `boxed_owned`-only condition); broadening reproduces Ve.4.
- Do not skip the fixed-point gate. The hero metric is restoring
  strict-or-near fixed-point.
- Do not commit `/tmp/*` files.
- Do not tag without user approval.
- Do not push without user approval.
- Do not chase culebra false positives.
- Do not ship the fix without full sanitizer + lint gate.
- Do not leave `__mn_str_eprint` instrumentation in source.
