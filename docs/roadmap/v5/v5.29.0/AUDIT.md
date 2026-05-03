# v5.29.0 — AUDIT (Phase 0 pre-flight evidence)

**Status:** Phase 0 complete; Mb.10 fix authorized.
**Pre-flight commands:** see PLAN.md Phase 0.

---

## Mb.10 — `__mn_indent_to_braces` Win64 ABI gap

### Asymmetry between Python and self-host emitters

| Emitter | Routing for `__mn_indent_to_braces`? | Source location |
|---|---|---|
| Python `emit_llvm_text.py` | ✅ YES | line 3632 (added v5.23.1 Mb.1) |
| Self-host `emit_llvm.mn` | ❌ **NO** | (no `if fn_name == "__mn_indent_to_braces"` branch in `emit_mir_call`) |

**grep evidence (self-host has declarations + attribute + tracking
hint, but no `emit_mir_call` routing):**

```
$ grep -n '__mn_indent_to_braces' mapanare/self/emit_llvm.mn
939:    if name == "__mn_indent_to_braces" { return " nounwind willreturn" }
1150:    s = declare_runtime_fn(s, "__mn_indent_to_braces", llvm_string(), llvm_string())
1158:    // as __mn_indent_to_braces).
3778:    // the v5.23.1 Mb.1 pattern for `__mn_indent_to_braces`. Once
4494:    if fn_name == "__mn_indent_to_braces" { return true }
```

The Mb.9 Python comment at line 3778 even *names* the missing
routing as the pattern Mb.9 mirrored — but Mb.9's author only added
the routing for `__mn_count_user_brace_block_openers` and
`__mn_emit_brace_deprecation_warning` (lines 3781–3786), not for the
parent function.

**grep evidence (Python emitter has the routing):**

```
$ grep -n '__mn_indent_to_braces' mapanare/emit_llvm_text.py
3614:        # v5.23.1 Mb.1: V.9 lifecycle leak — __mn_indent_to_braces returns
3626:        # parse() does `let preprocessed = __mn_indent_to_braces(source);
3632:        if fn == "__mn_indent_to_braces" and args:
3634:            r = self._rt("__mn_indent_to_braces", STR, [STR], [(a, STR)])
3641:        # `__mn_indent_to_braces` handler above exists — without it
```

### IR call-site shape (current — Linux SysV; bug latent)

From `/tmp/stage2.ll` (the v5.28.0 baseline, captured by
`bash scripts/verify_fixed_point.sh --keep`):

```llvm
declare {ptr, i64} @__mn_indent_to_braces({ptr, i64}) nounwind willreturn
...
if_merge2:
  %source_val10 = load {ptr, i64}, ptr %source.addr
  %t11 = call {ptr, i64} @__mn_indent_to_braces({ptr, i64} %source_val10)
  store {ptr, i64} %t11, ptr %str_track.269
```

On Linux SysV the call is by-value `{ptr, i64}`, declaration is also
by-value `{ptr, i64}` — no mismatch from the ABI's perspective; the
SysV calling convention passes 16-byte aggregates in registers
regardless of declared shape. Goldens 95/95 PASS on Linux,
masking the bug for 5 releases (v5.23.1 → v5.28.0).

### Same call site on Win64 (the bug)

`win64_rewrite_decl_params` (`mapanare/self/emit_llvm.mn`)
rewrites the **declaration** parameter from `{ptr, i64}` to `ptr`
when targeting Win64 (8-byte byref threshold). The user-call
fallthrough path uses `is_byref_type_st` (64-byte threshold) for
the **call site**, so on Win64 the call still emits the struct
by-value while the declaration expects `ptr` — gcc lowers
`MnString source` per Win64 ABI as pass-by-hidden-pointer
(rcx = pointer to caller-stack copy), but rcx actually contains
the struct's first 8 bytes (the `data` pointer of MnString).
Bogus pointer → SIGSEGV the moment the function tries to read
`source.len` field.

Reproduced in publish run #50:
```
0x00007ff7562e7edd in mnc-win-x64!__mn_indent_to_braces ()
=== Wb.1.dx: mnc-stage2 exited 139; capturing diagnostics ===
```

### Comparison with Mb.9-routed sibling (correct pattern)

`__mn_count_user_brace_block_openers` already routes through
`emit_rt_call` (Mb.9, line 3781-3783):

```llvm
%source_val0 = load {ptr, i64}, ptr %source.addr
%t1 = call i64 @__mn_count_user_brace_block_openers({ptr, i64} %source_val0)
```

On Linux: same `{ptr, i64}` shape (no visible difference here).
On Win64: `emit_rt_call` uses `win64_sarg_rewrite_args` (8-byte
threshold, matching `win64_rewrite_decl_params`), so the call
site emits `ptr sarg.N` matching the declaration's `ptr`. No
ABI mismatch.

Mb.10's fix mirrors this routing for `__mn_indent_to_braces`.

### Insertion point for Mb.10.A edit

`mapanare/self/emit_llvm.mn`, immediately after line 3786 (the
end of the v5.26.0 Mb.9 `__mn_emit_brace_deprecation_warning`
routing block), before the chr/ord builtins block at line 3789.

Mirrors the existing Mb.9 routing shape and the v5.23.1 Mb.1
Python contract:

```mapanare
if fn_name == "__mn_indent_to_braces":
    let as_itb: String = llvm_string() + " " + args[0].name
    return emit_rt_call(st, dn, llvm_string(), "__mn_indent_to_braces", as_itb)
```

`emit_rt_call` signature (line 629): `(st, dn, ret_ty, fn_name,
args_text)` — same shape as Mb.9's `__mn_count_user_brace_block_openers`
call at line 3783, only the return type differs (`llvm_string()`
i.e. `{ptr, i64}` MnString here, vs `"i64"` for the counter).

---

## Pre-flight verification (commands run)

### 1. v5.28.0 HEAD state

```
$ cat VERSION
5.28.0

$ git log --oneline -3
f119c43 Replace fixed sleeps with polling in tests   ← Pv.8 already shipped
bc3bc7b Parameterize runtime archive; update GitNexus ← Pv.7 already shipped
441ece0 Release v5.28.0: RE-PANEL ...
```

### 2. Pv.7 sandbox in place (Makefile lines 205-208)

```
$ grep -n 'SANDBOX' Makefile | head -10
205:	@SANDBOX=runtime/native/.libmapanare_rt.cbt-tmp.a; \
206:	rm -f $$SANDBOX; \
207:	$(MAKE) -s build-rt RT_OUTPUT=$$SANDBOX >/dev/null && \
208:	mv -f $$SANDBOX runtime/native/libmapanare_rt.a
```

### 3. Pv.8 polling helpers committed (f119c43)

```
$ grep -cE 'wait_for_agent_state|wait_for_messages_processed|wait_for_agent_recv|wait_for_counter|test_sleep_ms' tests/native/test_c_runtime.c
19
```

`f119c43` (already on dev) added 4 helpers + converted 7 call
sites; `git show --stat f119c43` shows
`tests/native/test_c_runtime.c | 162 ++++++++++++++++----------`
(101 insertions, 61 deletions). Pv.8 is **committed**, not
uncommitted as PROMPT/PLAN drafted; v5.29.0 documents the
already-shipped fix.

### 4. v5.28.0 fixed-point baseline

```
$ bash scripts/verify_fixed_point.sh --keep
[Stage 1] stage1 compiles mnc_all.mn → stage2.ll
  stage2.ll: 241842 lines
  llvm-as: OK
  Building mnc-stage2... OK (5562872 bytes)
[Stage 2] stage2 compiles mnc_all.mn → stage3.ll
  stage3.ll: 241842 lines
  llvm-as: OK
[Verify] Fixed point: diff stage2.ll stage3.ll
  ~ NEAR FIXED POINT
  4 diff lines out of 241842 (0.002%)
241842c241842
< !0 = !{!"5.27.0"}
---
> !0 = !{!"5.28.0"}
```

The 1-line content drift is the expected v5.9.0 DX.2 artifact:
`mnc-stage1` was linked against a v5.27.0 runtime when last built
(see `ls -la mapanare/self/mnc-stage1` → May 2 04:26); after the
Mb.10 fix lands and `build_stage1.py` re-links stage1 against the
current runtime, both stage2.ll and stage3.ll will embed the same
version string. Strict 0-line diff preserved by construction
between the two stages of a single build.

### 5. Goldens baseline 95/95

```
$ python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1
...
All 95 tests passed in 17.7s
```

---

## Pv.7 evidence (race-window measurement)

To be captured in Phase 4. Re-run `bc3bc7b`'s race test:

```bash
RT=runtime/native/libmapanare_rt.a
(for i in $(seq 1 200); do
    if [ ! -f "$RT" ]; then echo "MISSING at iter $i"; fi
    sleep 0.02
done) &
WATCHER=$!
sleep 0.1
make -s clean-build-test 2>&1 | tail -3
wait $WATCHER
# expected: 0 MISSING reports across 200 polls (4-second window)
```

## Pv.8 evidence (falsifiability round-trip)

To be captured in Phase 4. Stash `f119c43`'s diff against the
test_c_runtime.c file currently at HEAD, run the suite 5×, watch
flake rate climb on a loaded runner; restore, run 5× again, all
pass.
