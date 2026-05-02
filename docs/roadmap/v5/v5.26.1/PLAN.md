# v5.26.1 — Eu.1..Eu.4 — close the v5.26.0-deferred LINK_FAIL bug classes

**Status:** PLANNING
**Breaking:** No.
**Prerequisite:** v5.26.0 shipped (Mb.7 + Mb.9 closed; Mb.\* arc
done; the 4 deferred LINK_FAIL bug classes are tracked as
`xfail(strict)` in `tests/llvm/test_async_link.py`).
**Estimated effort:** 1–2 sessions (~6–10 hours; 4 small-but-
distinct codegen investigations, similar shape to Mb.7 each).
**Arc context:** Opens the **Eu.\*** arc (enum-payload codegen
closures). The bug classes were surfaced by v5.26.0's Phase 0
audit when re-running the link contract on the 9 goldens the
v5.23.1 SESSION_REPORT had grouped under one supposed root cause.
Each bug is structurally distinct; bundling investigations risks
confusing diff signals (per the v5.26.0 PROMPT discipline that
already split Mb.7 from Mb.9 for the same reason).

---

## Why this exists

The v5.23.1 SESSION_REPORT claimed 9 LINK_FAIL goldens
(47/48/49/51/55–59) shared the i64/i1 tag-emit bug. v5.26.0
Phase 0 audit re-ran the link contract through `clang -c` and
found:

* **Goldens 55–59** (the async cluster) **never had** the bug —
  they don't use try-operator and don't go through
  `emit_enum_tag → Branch`. They link cleanly both pre- and
  post-Mb.7.
* **Golden 47** had the i64/i1 bug AND a separate
  `emit_unwrap` Result-payload bug. Mb.7 closed the leading
  site at v5.26.0; the second site is **Eu.1**.
* **Goldens 48/49/51** fail for distinct reasons unrelated to
  Mb.7. They are **Eu.2 / Eu.3 / Eu.4**.

Each bug is silently hidden by the test_native.py harness because
it compares Python and self-host IR rather than running an actual
link cycle (the harness blind spot — fixing this is v5.27.0+
material, not Eu.\*'s scope).

The v5.26.0 SESSION_REPORT names each bug class precisely; the
xfail markers in `tests/llvm/test_async_link.py::test_deferred_link_failures`
encode the contract a v5.26.1 fix must satisfy:

| Eu # | Golden | Brief class | Sites |
|---|---|---|---|
| Eu.1 | 47_try_operator | `emit_unwrap` Result Ok-payload extraction does single `extractvalue` at field 1 (returns inner aggregate `{Ok_ty, Err_ty}`); needs second `extractvalue` at field 0 of inner. | `mapanare/emit_llvm_text.py::_do_unwrap` + `mapanare/self/emit_llvm.mn::emit_unwrap` |
| Eu.2 | 48_match_nested_exhaustive | Result literal construction emits three disagreeing types in the `insertvalue` chain (outer `{i1, {ptr, ptr}}`, inner `{i64, ptr}` — neither is the canonical `{i64, {ptr, i64}}` for `Result<Int, String>`). | enum-init lowering + emit |
| Eu.3 | 49_match_guards | match on `Int` subject emits `extractvalue i64 %n, 0` (i64 is not aggregate). Match-on-primitive lowering surface — should bypass `EnumTag` and treat Int as the tag value directly. | match lowering for non-enum subjects |
| Eu.4 | 51_match_guards_and_or | match with or-pattern + guards emits 4× `i64 1` cases in `switch` (every `Some`-arm gets the same tag). Or-pattern lowering surface — needs decision-tree-style fall-through, not parallel switch cases. | or-pattern + guard interaction in match lowering |

All four sit on the Result/Option/match codegen surface. The
shape is similar enough that one release can absorb all four with
small-and-surgical fixes (~5–15 LOC each), but **each needs its
own Phase 0 audit** to nail the exact emit/lower site before code
edits land. Don't shortcut.

---

## Goals

1. **Eu.1.A–Eu.1.B** Phase 0 root-cause for `emit_unwrap` on
   Result; surgical fix to extract the Ok payload at field 0 of
   the inner aggregate. Both Python and self-host emitters.
2. **Eu.2.A–Eu.2.B** Phase 0 root-cause for the 3-way insertvalue
   type disagreement at Result literal construction; surgical fix
   to align the outer/inner/payload types canonically.
3. **Eu.3.A–Eu.3.B** Phase 0 root-cause for match-on-Int; the
   lowerer should not emit `EnumTag` against a primitive subject
   — just use the value as the switch tag directly.
4. **Eu.4.A–Eu.4.B** Phase 0 root-cause for or-pattern duplicate
   switch cases; align with Python's match decision-tree pattern
   so or-pattern arms with guards don't collapse onto a single
   `i64 1` case.
5. **Eu.5** Flip the four `xfail` markers in
   `tests/llvm/test_async_link.py::test_deferred_link_failures`
   to PASS by removing the `pytest.xfail(reason)` line. Each test
   then runs `_compile_link_run` end-to-end; goldens 47/48/49/51
   move LINK_FAIL → PASS.
6. **Eu.6** Strict 3-stage fixed point preserved (or one-time
   documented line-count delta from the new emit paths).
7. **Eu.7** Goldens 95/95 still PASS through the harness.

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Eu.1.A** | HIGH (investigation) | **Phase 0 root-cause for golden 47.** Mb.7 fix moves the link error from line 229 (i64/i1) to line 235 (`store i64 %t3, ptr %v4.addr` where `%t3 = extractvalue ..., 1` is the inner `{i64, {ptr, i64}}` aggregate). Compare Python `_do_unwrap` (single extractvalue at index 1) vs the canonical Result Ok-payload shape (extract field 1 then field 0 of inner). Document in `docs/roadmap/v5/v5.26.1/AUDIT.md`. | 1.5h |
| **Eu.1.B** | HIGH | **Fix `emit_unwrap` on Result.** For `TK_RESULT` subjects, do TWO `extractvalue` ops: field 1 of outer (inner aggregate `{Ok_ty, Err_ty}`), then field 0 of inner (Ok payload). For `TK_OPTION` keep the existing universal-erasure path. Mirror the fix in both `mapanare/emit_llvm_text.py::_do_unwrap` and `mapanare/self/emit_llvm.mn::emit_unwrap`. Validate golden 47 links + runs cleanly. | 1h |
| **Eu.2.A** | HIGH (investigation) | **Phase 0 root-cause for golden 48.** The native IR shows three disagreeing types in one `insertvalue` chain: outer `{i1, {ptr, ptr}}`, inner `{i64, ptr}`, payload `{i64, {ptr, i64}}`. Python's likely showing the same shape (test_native.py won't catch it). Identify whether the bug is in (a) Result-type lowering picking the wrong inner shape, (b) `emit_enum_init` forming the inner aggregate with the wrong field types, or (c) Result-arg passing to `classify(x: Result<Int, String>)` casting through a wrong layout. Most likely (b). | 2h |
| **Eu.2.B** | HIGH | **Fix the Result-literal type chain.** Likely a `resolve_type` / Result-type-args-to-fields mapping bug. Fix at the source so all three insertvalue lines agree on `{i64, {ptr, i64}}`. Both emitters. | 1h |
| **Eu.3.A** | MEDIUM (investigation) | **Phase 0 root-cause for golden 49.** `match n: x if x < 0 => ...` where `n: Int`. Native IR has `%tag1 = extractvalue i64 %n_val0, 0` — the lowerer is treating Int subjects like enum subjects and emitting `EnumTag`. Locate the lowerer site that should branch on subject kind: emit `EnumTag` for enums, but for primitives just use the value directly (`switch i64 %subject`). | 1h |
| **Eu.3.B** | MEDIUM | **Fix match-on-Int lowering.** When the match subject is a primitive type (`TK_INT`, `TK_BOOL`, `TK_STRING`, etc.), skip `EnumTag` emission and route the subject value into the `Switch` directly (or use `BinOp(EQ)` chain for non-i64 cases). Both Python and self-host lowerers. | 1.5h |
| **Eu.4.A** | MEDIUM (investigation) | **Phase 0 root-cause for golden 51.** `match opt: Some(0) \| None => ...; Some(x) if x > 0 && x < 10 => ...; ...` lowers to `switch i64 %tag, ... [i64 1, ...; i64 1, ...; i64 1, ...; i64 1, ...]` — 4 duplicate cases for `Some` (tag=1). Identify whether the bug is in (a) the lowerer flattening or-pattern arms into separate switch entries (instead of routing them via decision-tree fall-through), or (b) the lowerer not recognizing that guards mean the switch case can't statically dispatch (and should emit a sequential test cascade instead). | 2h |
| **Eu.4.B** | MEDIUM | **Fix the or-pattern + guard match shape.** Likely needs the lowerer to either (a) merge or-pattern arms into a single switch case with internal sequential checks, or (b) emit a decision tree that hits each `Some`-arm in order with its guard. Mirrors a v4.79.0-era P3 fix; the SESSION_REPORT for that release names "decision-tree rebuild on guard failure" as the proper Python path. The self-host already has a "jump-to-next" approximation; v5.26.1 either ports the full decision-tree pattern or extends the jump-to-next logic to handle or-patterns. | 2h |
| **Eu.5** | LOW (mechanical) | **Flip the xfail markers.** Remove the `pytest.xfail(reason)` line from each of the four entries in `test_async_link.py::test_deferred_link_failures`. The test body already calls `_compile_link_run`; once each golden links + runs cleanly, the tests transition from XFAIL to PASS automatically. Verify all 4 PASS at HEAD. | 15 min |
| **Eu.6** | LOW | **Stage2/3 fixed point.** After all four fixes land, regenerate `mnc_all.mn`, build stage1, validate stage2.ll == stage3.ll. Document any line-count delta. Expected: <500-line delta (each fix adds 1–3 instructions per affected emit site; total emit volume ~100–200 fresh lines). | 30 min |
| **Eu.7** | LOW | **Update tests/golden/BENCHMARKS.md.** Goldens 47/48/49/51 transition from PASS-with-broken-IR to PASS-with-linkable-IR; the harness label stays PASS. The change is informational. Optional: add a comment in BENCHMARKS.md noting the link-clean status to document the v5.26.1 closure. | 15 min |

---

## Phase plan

### Phase 1 — Eu.1 (golden 47, the Mb.7 follow-on)

```bash
# Reproduce the post-Mb.7 link error
mkdir -p /tmp/v5261
./mapanare/self/mnc-stage1 emit-llvm tests/golden/47_try_operator.mn > /tmp/v5261/47.ll
clang /tmp/v5261/47.ll runtime/native/libmapanare_rt.a -lm -lpthread -ldl -o /tmp/v5261/47 2>&1 | head -5
# expected: '%t3' defined with type '{ i64, { ptr, i64 } }' but expected 'i64' at line 235

# Compare with Python's emission
python3 -m mapanare emit-llvm tests/golden/47_try_operator.mn -o /tmp/v5261/47_py.ll
diff /tmp/v5261/47.ll /tmp/v5261/47_py.ll | head -30
```

The expected fix in Python (`mapanare/emit_llvm_text.py::_do_unwrap`):

```python
def _do_unwrap(self, i: Unwrap) -> None:
    v, t = self._get(i.val)
    if i.val.ty.kind == TypeKind.RESULT:
        # Eu.1: extract inner {Ok_ty, Err_ty} aggregate, then Ok payload at field 0.
        inner = self._f("uw_inner")
        self._L(f"{inner} = extractvalue {t} {v}, 1")
        # Resolve inner type from val.ty.type_info.args
        ok_ty = self._rty(MIRType(i.val.ty.type_info.args[0]))
        err_ty = self._rty(MIRType(i.val.ty.type_info.args[1]))
        inner_ty = f"{{ {ok_ty}, {err_ty} }}"
        r = self._f("uw")
        self._L(f"{r} = extractvalue {inner_ty} {inner}, 0")
        dt = ok_ty
        self._put(i.dest, r, dt)
        return
    # Existing path (Option / generic) unchanged
    r = self._f("uw")
    self._L(f"{r} = extractvalue {t} {v}, 1")
    dt = self._rty(i.dest.ty) if i.dest.ty.kind != TypeKind.UNKNOWN else PTR
    self._put(i.dest, r, dt)
```

Self-host mirror in `mapanare/self/emit_llvm.mn::emit_unwrap`
(parallel — extract field 1 then field 0 for `TK_RESULT`).

Validation:
```bash
python scripts/build_stage1.py
clang /tmp/v5261/47.ll runtime/native/libmapanare_rt.a -lm -lpthread -ldl -o /tmp/v5261/47
/tmp/v5261/47
# expected output: "ok: 50\nfailed\n" (or similar, per golden)
```

### Phase 2 — Eu.2 (golden 48)

The Result literal `Ok(42)` for `Result<Int, String>` should
construct `{i1 1, {i64 42, undef}}` matching the canonical
`{i1, {i64, {ptr, i64}}}`. Native IR currently shows three
disagreeing widths. Audit `emit_enum_init` / `_do_enum_init` for
Result and find where the type chain breaks. Mirror the fix in
both emitters.

### Phase 3 — Eu.3 (golden 49)

Subject is `n: Int`. Lowerer emits `EnumTag` (which then emits
`extractvalue i64 %n, 0`). The fix: in match lowering, branch
on subject kind. For primitive subjects, skip `EnumTag` and
hand the subject value to `Switch` directly. Search lower.mn /
lower.py for the match lowering function (`lower_match` /
`_lower_match_expr`) and add the primitive-subject path.

### Phase 4 — Eu.4 (golden 51)

`match opt: Some(0) | None => ...; Some(x) if x > 0 && x < 10
=> ...; ...` — four arms all using `Some`. Currently switches
4× on `i64 1`. Fix: either decision-tree (each arm gets its own
arm block, guards check internally, fall-through to next arm on
failure) or merged-case-with-internal-sequential-test. The
v4.79.0 SESSION_REPORT names "decision-tree rebuild on guard
failure" as the canonical Python path; the self-host had a
"jump-to-next" approximation. v5.26.1 either ports the full
decision-tree to the self-host or extends the existing
machinery to handle or-patterns.

### Phase 5 — flip xfails + validation

```bash
# Edit tests/llvm/test_async_link.py — remove pytest.xfail(reason) line
# from each of the four test_deferred_link_failures entries.
$EDITOR tests/llvm/test_async_link.py

# Run the full async link suite
pytest tests/llvm/test_async_link.py -v
# expected: 10 passed, 0 xfailed (5 async cluster + 4 newly-fixed + 1 IR invariant)

# Goldens
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1
# expected: 95/95

# Fixed point
bash scripts/concat_self.sh
python3 scripts/build_stage1.py
bash scripts/verify_fixed_point.sh
# expected: stage2.ll == stage3.ll, line count change < 500 lines
```

### Phase 6 — closeout

Bump VERSION to 5.26.1, update CHANGELOG.md, update CLAUDE.md
release notes (mark Eu.\* arc CLOSED), write
`docs/roadmap/v5/v5.26.1/SESSION_REPORT.md`.

---

## Out of scope

- **Test harness link-cycle integration.** Adding a real
  `clang -c` step to `scripts/test_native.py` so future bugs
  surface at PASS time would close the structural blind spot
  that hid Eu.1..Eu.4 for 3 releases. Material for v5.27.0+;
  separate Phase 0 design.
- **Decision-tree match lowering rewrite (general).** Eu.4
  fixes the or-pattern + guard interaction surfaced by golden
  51; a fuller rewrite of match lowering to canonical decision
  trees is a multi-release effort, not v5.26.1's scope.
- **Result/Option representation refactor.** v5.26.0's Mb.7 +
  Eu.\* fixes accumulate atop the existing `{i1, {Ok_ty,
  Err_ty}}` representation. A canonical refactor (e.g.
  separate Result and Option types throughout the IR, no
  i1/i64 tag width oscillation) is v6.0+ surface.

---

## Risk

1. **Eu.2 may surface a deeper Result-type-args bug.** The
   3-way insertvalue mismatch suggests the type system's
   resolution of `Result<Int, String>` to its IR shape is
   inconsistent across emit sites. If the fix at one site
   produces the wrong shape elsewhere, Phase 0 must
   re-investigate. Mitigation: run the full goldens 95/95 after
   each fix; revert if any regression.
2. **Eu.4 may require porting decision-tree match lowering
   from Python to self-host.** The Python pipeline already does
   decision-tree rebuild on guard failure (`lower.py:3281-3290`
   per the v4.79.0 SESSION_REPORT); the self-host has a
   "jump-to-next" approximation. If or-patterns need the full
   decision tree, the port might exceed the 30-LOC ceiling.
   Mitigation: scope the self-host fix to or-pattern + guard
   specifically (not a general decision-tree rewrite).
3. **Stage2/3 fixed-point break.** Each fix adds emit
   instructions; the cumulative line-count delta could be
   non-trivial. Mitigation: contained per-site changes
   shouldn't perturb deterministic emission; if they do,
   document as expected and resume the streak from the new
   baseline.
4. **Bb.\* seed refresh trigger.** None of the four fixes
   change C-runtime call shapes (all are emitter-side
   adjustments). Seed refresh **NOT expected**; verify with
   `bash scripts/build_from_seed.sh` after Phase 5.

---

## Success criteria

- ✅ Goldens 95/95 with 4 previously-XFAIL goldens (47/48/49/51)
  now PASS through the link contract.
- ✅ `tests/llvm/test_async_link.py` passes 10/10 (no xfails;
  test_deferred_link_failures becomes a regular link contract).
- ✅ Strict 3-stage fixed point preserved (or documented
  one-time delta < 500 lines).
- ✅ `mnc_all.mn` regenerated; bootstrap from seed succeeds
  against the existing v5.10.0 seed (no Bb.\* refresh).
- ✅ No regression in the 91 previously-passing-and-linking
  goldens.

---

## Carry-forward delta

Closes:
- **Eu.1** — `emit_unwrap` Result Ok-payload double-extract bug
  (golden 47 follow-on from Mb.7).
- **Eu.2** — Result-literal insertvalue type chain mismatch
  (golden 48).
- **Eu.3** — match-on-Int emits EnumTag against primitive
  (golden 49).
- **Eu.4** — match or-pattern + guards collapse to duplicate
  switch cases (golden 51).
- **Eu.\* arc closeout** — every v5.26.0-deferred LINK_FAIL bug
  class closed.

No new opens (all four bug classes are pre-existing latent bugs
discovered by v5.26.0's Phase 0 audit; closing them retires the
v5.23.1 → v5.26.0 LINK_FAIL ledger).
