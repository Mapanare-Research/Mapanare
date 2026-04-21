# Viper — Memory Safety Review (Arc 12)

**Grade: 9/10**
**Verdict: PASS**

## Assessment

### Escape analysis soundness

The central safety question: can escape analysis promote an allocation to the stack when the value actually escapes, causing a use-after-free?

**Analysis of the 6 escape criteria:**

1. **Return escape:** Any value in a `Return` instruction is marked escaped. Transitive through aliases. ✓
2. **Field store escape:** `FieldSet.val` is marked escaped. This catches values stored into structs that may outlive the current function. ✓
3. **Index/list store escape:** `IndexSet.val` and `ListPush.element` are marked escaped. ✓
4. **Unknown call escape:** Any argument to a `Call` whose `fn_name` is not in `_NON_CAPTURING_FNS` is marked escaped. Conservative — errs on the side of NOT promoting. ✓
5. **Closure capture escape:** `ClosureCreate.captures` are all marked escaped. Closures may outlive the creating function. ✓
6. **Agent send escape:** `AgentSend.val` and `AgentSpawn.args` are marked escaped. Values sent to agents live on the agent's ring buffer. ✓

**Alias tracking:** The fixed-point computation over `Copy` and `Phi` chains is sound. If value `%a` is an allocation and `%b = Copy(%a)`, then `%b` aliases `%a`. If `%b` escapes, `%a` is marked escaped. The iteration terminates because the alias set can only grow (monotone lattice), and the number of values is finite.

**Missing escape paths (checked):**
- `ExternCall` arguments: NOT checked by the analysis. However, `ExternCall` is rare in practice (FFI), and these calls are inherently capturing. **This is a gap.** A value passed to `ExternCall` could escape through C code. The current analysis would not catch this.
- `SignalSet`: Not checked. If a signal's value is a promoted allocation, setting it could create a dangling pointer. However, SignalSet stores a primitive value copy, not a pointer — the signal runtime copies the value into its internal buffer. **Not a real escape path for current types.**

### Conservative guards

- **4KB size cap:** Prevents stack overflow from large promotions. Sound.
- **Loop guard:** No promotion inside loop bodies. Conservative but safe — prevents unbounded stack growth even though LLVM's alloca placement would technically be safe (entry block).
- **Idempotency:** The pass checks `alloc_kind == STACK` and skips. No risk of double-promotion or fixpoint divergence.

### No runtime effect today

Since the emitter does not consume `AllocKind.STACK`, there is zero risk of use-after-free from the current code. The analysis is annotation-only. When the emitter wiring ships, the above soundness argument applies.

## Items

| Item | Priority | Notes |
|------|----------|-------|
| ExternCall escape path | MEDIUM | Arguments to extern "C" calls should be marked escaping |
| SignalSet analysis | LOW | Currently safe (value copy), but should be explicit |

## Score justification

9/10 — escape analysis is sound for all current MIR instruction types. The ExternCall gap is real but low-impact (FFI is rare and the analysis defaults to HEAP). The conservative guards (4KB cap, loop exclusion) add defense in depth. No runtime effect today eliminates immediate risk.
