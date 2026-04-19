# v4.152.0 E8 Hypothesis

> *"LLVM's -O2 pipeline subsumes most of what the four dormant MIR
> passes would do. Re-enabling them today will either (a) have zero
> effect (both stage2.ll and benchmarks byte-/perf-identical) or
> (b) shrink stage2.ll line count on a small subset of tests without
> changing runtime perf."*

## Per-pass predictions

### E8a — `strength_reduce` (mir_opt.mn:1238)

**v4.111.0 rationale:** "Corroborates with inline_small_functions in
producing MIR that the verifier rejects ('block has no instructions',
'block does not end with a terminator') on golden tests with
user-defined functions (03_function onward, 13 tests). Zero-ROI per
v4.109.0."

**v4.152.0 prediction: likely still zero-ROI.** The pass replaces
`x % 2^n` with `x & (2^n - 1)`. LLVM's `-instcombine` at -O2 does
exactly this transform on the LLVM IR. The v4.111.0 crash blame
("corroborates with inline_small_functions") suggests the crash was
caused by the inliner, not by strength_reduce itself. With the inliner
disabled, strength_reduce alone should be safe but produce
IR-identical output because LLVM's instcombine already covers this
pattern. The Python side has `strength_reduction` enabled (mir_opt.py
line 2390), so re-enabling restores parity. Expected outcome: safe,
zero-ROI, keep for parity.

### E8b — `inline_small_functions` (mir_opt.mn:1244)

**v4.111.0 rationale:** "Produces invalid MIR (blocks with corrupted
instructions list) that crashes lower__verify_block on golden tests
containing function calls. LLVM's own inliner subsumes this work at
-O2."

**v4.152.0 prediction: plausibly 5-15% compile-time save, but crash
risk remains.** The v4.111.0 crash was in the inliner's block
duplication logic, not in downstream passes. Post-Sh.2/Sh.8/Sh.11/Sh.12
closures fixed MIR invariants for *other* passes, but the inliner's
`rename_instructions` logic (mir_opt.mn:700-766) may still produce
invalid block structures on complex call patterns. LLVM's `-inline`
does subsume this at -O2, but MIR-level inlining could let constant
folding and DCE cascade earlier, shrinking the LLVM IR handed to clang.
The Python side has `inline_small_functions` enabled (mir_opt.py line
2382). Expected outcome: **either a modest win or an immediate crash**
— binary, no middle ground. If it crashes, roll back and open In.1.

### E8c — `licm` (mir_opt.mn:1251)

**v4.111.0 rationale:** "block_successors crashes on non-empty
instruction lists in some compile paths (known valgrind hot-frame since
v4.105.0, 14x crash site). v4.109.0 confirmed zero instruction-level
effect at -O2."

**v4.152.0 prediction: plausible stage2.ll shrink, no runtime delta.**
The `block_successors` crash was likely a list-access bug that the
Sh.2 arc (v4.131.0-v4.132.0) may have incidentally fixed — the
function walks `bb.instructions` and extracts branch targets. If the
crash is gone, LICM hoists loop-invariant MIR instructions to the
header, shrinking the loop body. LLVM's own LICM runs later, so
runtime perf won't change, but the LLVM IR clang processes will be
smaller → faster compile. The Python side has `licm` **also disabled**
(mir_opt.py line 2387: "LICM disabled — hoisting analysis needs
loop-carried value tracking"), so both sides are off. Parity holds
either way. Expected outcome: safe if the crash is fixed, modest
stage2.ll shrink, no runtime delta.

### E8d — `escape_analysis` (mir_opt.mn:1258)

**v4.111.0 rationale:** "escape_analysis_function crashes at +0x3f3
offset on tests with user-defined functions returning values. The pass
is scaffold, not production. Also noted as zero-ROI."

**v4.152.0 prediction: expected to stay off.** The pass marks
non-escaping allocations for stack promotion, but the downstream
emitter (`emit_llvm.mn`) doesn't act on the `alloc_kind=STACK`
annotation — there's no codegen path that emits `alloca` instead of
`malloc` based on this flag. The analysis itself is conservative and
correct (check_escape at mir_opt.mn:1129-1175 handles return, field_set,
index_set, call, agent_send), but the +0x3f3 crash suggests a
struct-field access bug in the compiled binary. With Ge.1 closed, the
crash *might* be gone, but even if so, the pass has no downstream
effect. The Python side has `escape_analysis_promotion` enabled
(mir_opt.py line 2395) — it does act on the annotation because the
Python emitter has the corresponding codegen. Expected outcome: crash
gone but zero-ROI; keep disabled, update comment.
