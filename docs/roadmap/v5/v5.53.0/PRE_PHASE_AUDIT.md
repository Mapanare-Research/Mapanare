# v5.53.0 PRE_PHASE_AUDIT — Sf.\* + Te.3.F

**Status:** AUDIT COMPLETE
**Audited at:** 2026-05-15
**Audited against:** dev branch HEAD (VERSION 5.52.0; STRICT baseline
246,347 lines / 0 diff per v5.52.0 SESSION_REPORT).

This audit is **gating** for Phase 1+. Two dockets, four critical
decisions per the prompt. Each decision is locked below with the
empirical evidence that drove it.

---

## TL;DR — load-bearing reversals

| Docket | PLAN hypothesis | Phase 0 empirical finding | Decision |
|---|---|---|---|
| **Sf.\*** | Bug in `_lower_struct_update` base-temp synthesis (lines 1427-1497 or 5095+); ≤ 30 LOC lowerer fix | **Hypothesis wrong.** Python-bootstrap IR for `82_struct_update.mn` is structurally correct (per IR dump under `target triple = "x86_64-w64-windows-gnu"`); the surfaced symptom is a Win64-ABI mismatch on `__mn_str_free` drop-glue, NOT struct-update lowering. Three call sites in `emit_llvm_text.py` bypass the `_rt` helper's Win64 sarg lowering. **No clang on local Windows machine to compile + run the IR end-to-end.** Sizing for the actual fix: ~30 LOC Python emitter + ~40 LOC self-host `emit_llvm.mn` mirror ≈ 70 LOC. | **SPLIT to v5.53.1.** Cannot verify a Win64-only fix without a Win64 clang toolchain locally; speculative changes that compile & lint clean on Linux but don't actually close the bug violate falsifiability discipline (per v5.46.0 Lf.\* / v5.49.0 Wn.\* precedent — fix tied to a recorded crash signature). PLAN.md Risk #1 explicitly anticipated this case. |
| **Te.3.F** | ~11 first-party nested-stmt-block residuals (10 lexer.mn + 1 lower.mn); recursive formatter extension migrates all of them; ~30 LOC + tests | **11 confirmed, but only 7 are migrate-able under v5.48.0 grammar.** Single-line chained `else:` continuation form (`if X: a else: b`) does NOT parse — `else` is rejected in expression context after the colon-form body. Affects 4 of 11 sites: lexer.mn 267/276/285 (chained-if-else with nested else-branch) and lower.mn:4843 (single-arm outer + chained-if-else inner). | **Reduced scope.** Te.3.F.1 migrates 7 pure-nested-2 sites (lexer.mn 191/192/196/212/213/371/386). Brace surface drops 25 → ~18 (~28% reduction). The 4 chained-if-else cases need a single-line `else:` continuation grammar rule — defer to v6.0 PLAN input. Te.3.F formatter recursion still ships; counter-factual remains the 7-site delta. |

---

## Critical Decision 1 — Sf.\* root-cause localization

**PLAN.md prediction:** Bug in `mapanare/lower.py:1427-1497` (base-temp
synthesis) or `mapanare/lower.py:5095+` (`_lower_struct_update`'s
per-field GEP/load). Sized at ≤ 30 LOC; > 50 LOC = split.

**Phase 0 evidence:**

1. **IR inspection of Python-bootstrap output for 82_struct_update.mn**
   under the actual failing target triple
   (`x86_64-w64-windows-gnu` — autodetected by `python -m mapanare
   emit-llvm` on this Windows machine) shows structurally-correct IR:

   ```llvm
   %t7.a.23 = alloca {i64, i64, i64}, align 8
   store {i64, i64, i64} zeroinitializer, ptr %t7.a.23  ; ← zero-init
   ; ... per-field stores 99, 2, 3 via the synthesized ConstructExpr
   %si.22 = insertvalue {i64, i64, i64} %si.20, i64 %l.21, 2
   store {i64, i64, i64} %si.22, ptr %t7.a.23           ; ← full 24-byte write
   ```

   The synthesized base-temp `%t3.a.9` is zero-init then fully written
   from the struct constructor. The per-field GEPs into `%t3` (the
   `..p1` source) use the correct
   `getelementptr inbounds {i64, i64, i64}, ptr %t3.a.9, i32 0, i32 N`
   stride and width. **There is no uninitialized read on the lowerer
   side.** The PLAN hypothesis cannot be reproduced via IR analysis.

2. **Where `9223372036854775802` (`INT64_MAX - 5`) actually comes from.**
   Searching the C runtime for the `integer overflow in %lld + %lld`
   format string (`runtime/native/mapanare_core.c:174-186`) lands on
   `mn_checked_add`. The `82_struct_update.mn` source has **zero
   user-level `+` operations**. The checked-add must therefore fire
   inside a runtime path. Likely candidate: `__mn_str_free` reads
   `len_with_heap_bit` as garbage on Win64 because of an ABI mismatch
   between caller and callee at the IR level. The unfreed string leaks
   into a downstream allocation length calculation that uses checked
   arithmetic.

3. **The Win64-ABI mismatch on `__mn_str_free`.** The C runtime
   (`runtime/native/mapanare_core.c:957-964`, v5.8.3 Wb.1) explicitly
   declares:

   > `__mn_str_free` takes decomposed `(data, len_with_heap_bit)`
   > instead of `MnString` by value. Win64 ABI passes 16-byte structs
   > by hidden pointer in %rcx, but LLVM lowers IR-level `{ptr, i64}`
   > aggregate args by decomposing into two registers — same shape as
   > SysV.

   So the C runtime signature is **`void __mn_str_free(const char *,
   int64_t)`** — two scalars. But the Python emitter at
   `emit_llvm_text.py:1881` declares it via
   `self._ensure("__mn_str_free", VOID, [STR])` (one aggregate arg),
   and call sites at lines **1794** and **2015** emit
   `call void @__mn_str_free({ptr, i64} %v)` (aggregate-by-value)
   directly — **bypassing `_rt`'s Win64 ABI lowering** (lines
   1695-1722). On SysV the aggregate decomposes into rdi+rsi by
   coincidence matching `(const char*, int64_t)`; on Win64 the
   aggregate becomes sarg (hidden ptr in rcx), and the C function
   reads garbage from rdx for `len_with_heap_bit`.

4. **The self-host emitter has the same bypass.**
   `mapanare/self/emit_llvm.mn` has four sites that emit the
   aggregate-by-value form (lines 4660, 4840, 4844, 4990) plus the
   declaration at line 1101 (`declare_runtime_fn(s, "__mn_str_free",
   "void", llvm_string())`). Sf.3 would need a mirror.

5. **A third call site shows the same pattern.** Line 5583 emits
   `call {ptr, i64} @__mn_str_concat({ptr, i64} %a, {ptr, i64} %b)`
   bypassing `_rt`. This implies a CLASS of similar `_rt`-bypasses
   that the v5.49.0 Wn.\* registry didn't touch — none of these have
   `_RUNTIME_FN_SIGS` entries.

**Sizing estimate (if fix attempted in v5.53.0):**

| Site | LOC |
|---|---:|
| `emit_llvm_text.py::_track_string` line 1791-1794 | ~10 |
| `emit_llvm_text.py::_emit_drop_glue_strings` line 2015 | ~5 |
| `emit_llvm_text.py::_ensure` decl at 1881 (signature change) | ~3 |
| `_RUNTIME_FN_SIGS` registration for `__mn_str_free` | ~3 |
| `mapanare/self/emit_llvm.mn` mirror across 4 sites + decl | ~30 |
| Tests: `tests/llvm/test_str_free_abi.py` Win64-IR-shape gate | ~50 |
| **Total** | **~100** |

This exceeds PLAN.md's 50-LOC bundle threshold. More importantly:
**without a Win64 clang locally available, the fix cannot be verified
end-to-end.** A Linux test that asserts "no `{ptr, i64} @__mn_str_free`
call sites under `x86_64-w64-windows-gnu` triple" is necessary but
not sufficient — the actual runtime smoke must pass on Win64 to
close the bug, and that requires either CI or a local Win64 build.

**Self-host mirror need:** YES. The Python lowerer hypothesis would
have been Python-only; the actual root cause is in the emitter and
the self-host emitter has the same bypass.

**Decision:** **SPLIT Sf.\* to v5.53.1.** Document the actual root
cause + fix recipe in the v5.53.1 PLAN so the v5.53.1 session begins
with the localized fix site, not another root-cause hunt.

The PLAN.md Risk #1 mitigation explicitly authorizes this:

> if > 50 LOC, split Sf.\* to v5.53.1 and ship Te.3.F alone in v5.53.0

The empirical sizing (~100 LOC) and the verification-blocker
(no Win64 clang) both push to split.

---

## Critical Decision 2 — Sf.\* self-host parity

Moot under the v5.53.1 split. **For v5.53.1's record:** self-host
DOES have the bug; mirror is required. Four call sites in
`mapanare/self/emit_llvm.mn` (lines 4660, 4840, 4844, 4990) +
declaration at line 1101.

---

## Critical Decision 3 — Te.3.F empirical recount

**PLAN.md said:** 10 in lexer.mn + 1 in lower.mn = 11.
**CLAUDE.md hinted:** "17 lexer.mn predicates" (speculative).

**Empirical count (grep `if .* \{ if .* \{` against first-party `.mn`):**

| File | Sites | Comment |
|---|---:|---|
| `mapanare/self/lexer.mn` | **10** | lines 191, 192, 196, 212, 213, 267, 276, 285, 371, 386 |
| `mapanare/self/lower.mn` | **1** | line 4843 |
| `mapanare/self/mnc_all.mn` | 11 | cascade — regenerates after migration |
| **Total first-party** | **11** | matches PLAN.md exactly |

The CLAUDE.md "17" was speculation; PLAN.md's 11 is correct.

### Per-shape classification

| Shape | Sites | Migrate-able under v5.48.0 grammar? |
|---|---|---|
| **Pure-nested-2** (`if A { if B { stmt } }`) | lexer 191, 192, 196, 212, 213, 371, 386 (7 sites) | **YES** |
| **Single-arm outer + if-else inner** (`if A { if B { s1 } else { s2 } }`) | lower.mn:4843 (1 site) | **NO** — body chained `else:` not accepted |
| **Outer if-else + inner-in-else-branch** (`if A { s1 } else { if B { s2 } }`) | lexer 267 (1 site) | **NO** — outer chained `else:` not accepted |
| **Outer if-else + 3-level chained in else** (`if A { ... } else { if B { ... } else { if C { ... } } }`) | lexer 276 (1 site) | **NO** |
| **Mixed nested+chained (3-level)** (`if A { if B { s1 } else { if C { s2 } } } else { s3 }`) | lexer 285 (1 site) | **NO** |

**7 of 11 migrate-able under v5.48.0 grammar.** The 4 chained cases
all require a single-line `else:` continuation rule that v5.48.0
does NOT support (verified empirically below).

---

## Critical Decision 4 — Te.3.F recursion direction + chained-grammar probe

### Probe 1 — pure-nested-2 colon form parses to same AST

```python
brace = 'fn f(ch: String) -> Bool:\n    if ch >= "a" { if ch <= "z" { return true } }\n    return false\n'
colon = 'fn f(ch: String) -> Bool:\n    if ch >= "a": if ch <= "z": return true\n    return false\n'
assert parse(brace) == parse(colon)  # AST EQUAL ✓
```

Pure-nested-2 round-trip is sound. The recursion direction can be
either top-down (migrate outer first, then walk inner) or inside-out
(migrate inner first, then re-check outer). **Inside-out is the
natural fit** for the existing `_migrate_one_line_stmt_block` because
the line-363 `body_shadow has '{' or '}'` reject is what gates the
outer migration — recursively migrating the body resolves the gate.

### Probe 2 — chained-if-else single-line colon form

```python
src = 'fn f(b: Bool) -> String:\n    if true: if b: return "T" else: return "F"\n    return ""\n'
parse(src)
# ParseError: <input>:2:36: Unexpected 'else' — expected '#{', '(', ';', '[', 'agent', ...
```

**The colon form `if X: a else: b` does NOT parse.** `else` is
rejected because the grammar treats the colon-form body as a
non-block statement; the trailing `else` has nothing to attach to.

### Probe 3 — colon-form `if` followed by colon-form `else if` on next line

```python
src = 'fn f(hc: String) -> String:\n    if hc == "0": return "Z"\n    else if hc != "_": return "X"\n    return "Y"\n'
parse(src)
# ParseError: <input>:3:10: Unexpected 'if' — expected ';', '}', newline
```

Even multi-line `else if X: stmt` following a single-line
`if Y: stmt` fails — confirmed by the prose comment on
`tests/test_single_line_colon_blocks.py::test_else_if_single_line_terminating`:

> Single-line `else if x: stmt` is supported as the terminator of an
> if-chain. **Further continuations (a trailing `else`) on subsequent
> lines do NOT attach** because the brace stream emits the single-line
> as a fully-closed inline block.

By construction, a colon-form-closed `if` cannot be extended with
chained `else` continuations.

### Decision

**Te.3.F.1 scope:** 7 pure-nested-2 sites only. The recursion direction
is **inside-out** (`_migrate_one_line_stmt_block` recursively migrates
inner brace-blocks before re-checking outer). The 4 chained cases
defer to v6.0 PLAN (single-line `else:` continuation grammar rule).

---

## Risk re-assessment

| Risk | PLAN.md | Phase 0 update |
|---|---|---|
| Sf.\* fix wider than predicted | Mitigation: > 50 LOC → split | **Fired.** Split to v5.53.1. |
| Te.3.F recursion produces invalid output (else binding) | Mitigation: idempotence + AST tests | **Reduced** — the chained-if-else cases (where else-binding ambiguity could appear) are out of scope. The 7 pure-nested-2 cases have no `else`. AST-equivalence test in Probe 1 confirms soundness. |
| Self-host migration breaks STRICT | Mitigation: per-file checkpoint rebuild | **Unchanged** — migrating 7 sites across 1 file (lexer.mn only; lower.mn site is in the deferred 4) is light. Single-cluster rebuild after `mnc fmt`. |

---

## v5.53.0 reduced scope

| Phase | Status |
|---|---|
| **Phase 0** | DONE — this audit |
| **Phase 1 (Sf.1+Sf.2)** | **SPLIT to v5.53.1** |
| **Phase 2 (Sf.3)** | **SPLIT to v5.53.1** |
| **Phase 3 (Te.3.F.1)** | IN SCOPE — formatter recursive migration, inside-out, 7 sites |
| **Phase 4 (Te.3.F.2)** | IN SCOPE — `mapanare/self/lexer.mn` migration; STRICT gate at new baseline |
| **Phase 5 (Te.3.F.3)** | IN SCOPE — falsifiability anchor |
| **Phase 6 (Closeout)** | IN SCOPE — VERSION 5.52.0 → 5.53.0; CHANGELOG `### Added` for Te.3.F; CLAUDE.md release-notes entry naming both the Sf.\* split and the Te.3.F scope reduction; v5.53.1 PLAN drafted with the localized Sf.\* fix recipe |

**Brace surface delta target:** 25 → **18** (7 sites closed).
Original PLAN target was 25 → ~14 (11 sites); the 4-site deferral
moves the v6.0 hard-removal cut to need to address 18 first-party
residuals instead of 14, plus the chained-if-else grammar work.

**STRICT baseline:** preserved at v5.52.0's 246,347 lines after Te.3.F.2
landing; expected line delta from the 7-site migration is small
(each migration drops ~1 line by collapsing two openers into one
line, but `mnc_all.mn` regeneration may net slightly different —
documented in SESSION_REPORT.md after Phase 4 rebuild).

**v5.53.1 PLAN preview (for the v5.53.1 session input):**

- Sf.0: reproduce on Win64 (requires CI publish.yml smoke step or
  local Win64 clang).
- Sf.1: ABI fix at `emit_llvm_text.py` — change
  `_RUNTIME_FN_SIGS["__mn_str_free"] = (VOID, [PTR, I64])`; decompose
  at call sites (extractvalue + pass decomposed); route through
  `_rt` so Win64 sarg lowering applies uniformly OR (cleaner) keep
  decomposed signature and route through `_rt`.
- Sf.2: falsifiability — IR-shape gate asserting no
  `{ptr, i64} @__mn_str_free` under `x86_64-w64-windows-gnu` triple
  + Win64-only runtime smoke marked `pytest.mark.windows`.
- Sf.3: self-host mirror across the 4 sites + decl in
  `mapanare/self/emit_llvm.mn`.
- Sf.4: companion sweep — `__mn_str_concat` aggregate-by-value call
  at `emit_llvm_text.py:5583` has the same bypass shape; bundle if
  ≤ 30 additional LOC.

---

## Confidence

- **Te.3.F scope reduction:** HIGH. Three parser probes empirically
  rejected the chained-`else:` forms; the migrated form for
  pure-nested-2 is AST-equal.
- **Sf.\* split:** HIGH. PLAN.md hypothesis was inspectable against
  IR and disproven; the actual root cause is documented with file +
  line references and a fix recipe; the verification gap (no Win64
  clang locally) is acknowledged and routed to v5.53.1.
- **STRICT preservation under Te.3.F.2:** MEDIUM. The 7-site
  migration is light, but v5.50.0 surfaced two formatter bugs
  mid-implementation; Phase 4's rebuild-after-each-cluster
  discipline is the safety net.
