# Rattler v4.106.0 Review — LLVM / codegen

## Score: 7.8 / 10
## Verdict: PASS WITH NOTES

## Context: v4.99.0 → v4.106.0

At v4.99.0 I gave **6.5 / 10 NEEDS WORK** with tagged-pointer UB in
`mapanare_core.c` as the headline blocker, plus list-indexing drop-glue
and missing scheduler exports. Phase A (v4.100.0–v4.103.0) addressed
all three. Phase B (v4.104.0–v4.105.0) re-ran everything under
`llvm-as`, `opt -O2`, `llc`, valgrind, ASan, and TSan. I am grading on
what I re-verified, not what the session reports claimed.

## Fix-by-fix grading

### Item #1 — Tagged-pointer UB (v4.100.0) — **CLOSED**

Confirmed structurally removed. `grep` on
`runtime/native/mapanare_core.{c,h}` for `mn_tag_heap|mn_untag_heap|mn_is_heap`
returns only three hits, all comments describing the old scheme.
`MnString` at `mapanare_core.h:57-61` is now:
```c
typedef struct {
    const char *data;
    uint64_t    len     : 63;
    uint64_t    is_heap : 1;
} MnString;
```
ABI preserved at 16 bytes (same `{ptr, i64}` eightbyte layout). 20
live `is_heap` call sites in `mapanare_core.c` (L409–L1384) use the
bitfield directly. This is a real structural fix, not a workaround.

### Item #2 — List indexing drop glue (v4.101.0 + v4.103.0) — **CLOSED**

`_move_resource` appears 12× in `mapanare/emit_llvm_text.py` (6 sites,
caller+callee pairs). Goldens went 0/61 → 16/62 → **21/64**.

### Item #3 — Async scheduler linking (v4.102.0) — **CLOSED**

`libmapanare_rt.a` re-built, runs, valgrind-clean, TSan-clean. Not
my primary turf but I have no complaint with the IR/linking story.

### Item #4 — `else`/`sino` (v4.103.0) — **CLOSED**

`63_else_sino.mn` reproduced end-to-end through `-O2`: correct output.

### Item #5 — Closure type annotations (v4.103.0) — **INCOMPLETE**

This is the serious finding, and the PRE_PANEL_AUDIT under-diagnosed
it as "opt -O2 miscompiles typed-closure." **It is not an opt miscompile.
The emitter is producing malformed IR that llvm-as fails to reject** (a
pre-LLVM-15 typed-pointer verifier would have caught it; opaque `ptr`
lets it through).

Reproduced with the exact harness command:
```
$ /tmp/r_bin         # opt -O2 pipeline
10
-3
20
10                   # should be 15
$ /tmp/r_bin_noopt   # no opt
10
-3
20
15                   # correct
```

Root cause (direct IR inspection of `/tmp/r.ll`):

- 1-arg lambdas (`lambda0`, `lambda2`) emit correctly:
  `define internal i64 @lambda0(ptr %__env_ptr, i64 %x)`.
- **The 2-arg lambda `lambda4` (the `sum` closure) emits:**
  `define internal void @lambda4(ptr %__env_ptr, ptr %a, ptr %b)` —
  `ptr` params (should be `i64`), **`void` return (should be `i64`)**.
  The body does `ptrtoint ... add ... store i64 %i.4, ptr %t0.a.5`
  and then `ret void` — the computed sum is never returned.
- Call site at line 196 of `/tmp/r.ll`:
  `%ccr.55 = call i64 %cfn.53(ptr %cen.54, i64 %l.51, i64 %l.52)` —
  caller passes `i64, i64` and expects `i64` back.

At `-O0` the signature mismatch accidentally works: x86_64 passes both
`i64` and `ptr` in registers, the callee's `ptrtoint` rehydrates the
value, and the return-value register happens to still hold the sum.
At `-O2`, the inliner/arg-promoter sees the function actually returns
`void` and propagates the previous `double(10) = 10` constant into
`%ccr.55`. The "miscompile" is the optimizer being correct about
garbage IR.

The closure-type fix in `lower.py` (`FnType → MIRType(FN)`, typed-var
calls → `ClosureCall`, all lambdas → `ClosureCreate`) is wired at the
call side but the **lambda-body emitter does not use the parameter
types when lowering closures with arity ≥ 2**. 1-arg works because a
different code path handles it. I would not call Docket #5 closed.

### Other IR-level findings

- **Div.1** (stage1 `?`-op stores `{ptr, i64}` into `i64` slot): real,
  HIGH, unfixed.
- **Div.2** (bootstrap `?`-op emits invalid IR): reproduced —
  `/tmp/47.ll:93:13 error: '%uw.11' defined with type '{ i64, { ptr,
  i64 } }' but expected 'i64'`. Latent since v4.33.0, HIGH.
- **Div.3** (Option ABI `{i1,i64}` vs `{i1,ptr}`): MEDIUM, will block
  fixed-point self-compilation.
- `llvm-as mapanare/self/main.ll` validates (exit 0). Compiler does
  emit valid IR for the self-hosted module.

These three items plus the closure-body bug mean the Python emitter
has at least four distinct paths that produce verifier-accepted but
semantically wrong IR. That's a pattern — not a one-off.

## Findings

- `runtime/native/mapanare_core.h:57-61` — `MnString` bitfield is the
  real fix.
- `mapanare/emit_llvm_text.py` — 2-arg lambda body emission ignores
  closure parameter types and return type; emits `void` return and
  `ptr` parameters.
- `/tmp/r.ll:54` — `define internal void @lambda4(ptr, ptr, ptr)` is
  the smoking gun.
- PRE_PANEL_AUDIT Claim 10 is correct that "64_closure_typed wrong
  under -O2" but its stated root-cause ("opt inlining + argument
  promotion miscompile") is wrong. Root cause is our emitter; opt
  merely exposes it.
- v4.104.0 Claim 13's "60/64 PASS" is exit-code PASS — the integration
  harness doesn't diff stdout. At least one test (64_closure_typed)
  is silent-PASS with wrong output. Others may be too.

## Docket items I would open

| # | Item | Severity |
|---|---|:---:|
| Rt.1 | Emitter emits `void @lambdaN(ptr, ptr, ptr)` for 2-arg typed closures — wrong signature, UB under `opt -O2` | **HIGH** |
| Rt.2 | Integration harness does not diff stdout vs bootstrap — silent wrong-output is graded PASS | HIGH |
| Rt.3 | Audit `emit_llvm_text.py` lambda-body path for all arities + return types; add IR-verifier assertion on every `define` | MEDIUM |
| Rt.4 | Add `-Xclang -verify`-style golden (or at minimum `opt -passes=verify`) to CI that catches typed-pointer mismatches in the opaque-pointer era | MEDIUM |

## Grade justification

The v4.99.0 6.5 / 10 was driven by one CRITICAL (tagged-pointer UB) and
two HIGHs (list indexing, scheduler linking). All three are genuinely
closed with evidence I re-verified. That alone justifies +1.5 to
8.0. The closure-types fix claimed as HIGH-closed is **incomplete**:
the 2-arg typed-closure body emission is malformed IR that *already*
exists on `dev` at v4.106.0, produces wrong output under `-O2`, and
the verification harness missed it because it checks exit codes, not
output. That's a -0.2 for a latent HIGH on my turf that the Phase B
panel's own pre-audit surfaced but the SESSION_REPORT did not. I
cannot give clean PASS while that stands. To move to 8.5+ I need:
(a) Rt.1 fixed with a golden that actually compares stdout, (b) Div.1
and Div.2 closed or downgraded with a concrete plan.

## One-line summary

Tagged-pointer UB genuinely dead; two-arg typed closures are
malformed IR that -O2 miscompiles, harness silently passed it — 7.8 /
10 PASS WITH NOTES.
