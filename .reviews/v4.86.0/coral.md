# Coral — Language Design Review (Arc 11)

**Grade: 9/10**
**Verdict: PASS**

## Assessment

**Integer overflow semantics (nsw):** Correct. Mapanare defines signed integer overflow as undefined behavior, matching C and Rust. The `nsw` flag on add/sub/mul is semantically accurate. The SPEC does not explicitly define overflow behavior yet — a future SPEC update should formalize this.

**willreturn semantics:** Semantically defensible. Mapanare has no `loop {}` construct (bounded-for is the only loop primitive). `while` loops can theoretically run forever, but that produces UB (the stack will eventually overflow or the OS will kill the process). Treating non-termination as UB is the same position as C11 and Rust.

**noalias + TBAA + the type system:** The coarse TBAA tree (int/float/ptr/bool) correctly reflects Mapanare's type system. Integer and float loads cannot alias. Pointer loads can alias other pointer loads (correctly, since Mapanare has no ownership system). The noalias on sret is orthogonal to the type system — it's a calling convention property, not a language property.

**The Arc 11 thesis was wrong but the arc was right.** The measurement-first approach (v4.82.0 baseline before any changes) is the correct engineering discipline. The honest negative result proves the methodology works — it caught a wrong hypothesis early instead of letting it propagate through multiple arcs.

## Score justification

9/10 — the annotations are semantically correct and consistent with the language's UB model. The measurement discipline is exemplary. One point reserved because the SPEC should formally define overflow behavior (currently implicit).
