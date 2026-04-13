# Viper — Memory Safety Lens

**Grade: 9/10** | **Verdict: PASS**

## Assessment

My v4.71.0 concerns (Future leak, box leak) are addressed. `block_on` calls
`coro.destroy` + `free(box)` + `free(future)`. The cleanup path is correct.

The inline-resume model simplifies lifetime analysis: each coroutine runs
to completion synchronously, so no frame survives beyond its `block_on` call.
No use-after-free, no dangling handles.

## Specific findings

1. **PASS**: Future struct freed after value extraction (v4.71.0 item #1 — FIXED).
2. **PASS**: Return value box freed after extraction (v4.71.0 item #2 — FIXED).
3. **PASS**: `coro.destroy` called in `block_on` — frame cleanup guaranteed.
4. **NOTE**: In the inline-resume await model, the inner coroutine's frame
   is not freed at the await site — it's freed when the inner's `block_on`
   (implicit in the resume loop) completes. This is correct but means
   nested awaits accumulate frames on the C stack. Deep await chains could
   stack overflow. Document in v5.x risk register.
5. **PASS**: `57_real_await.mn` has 4 coroutine frames (fetch_a/b/c + fanout)
   — all allocated and freed cleanly.
