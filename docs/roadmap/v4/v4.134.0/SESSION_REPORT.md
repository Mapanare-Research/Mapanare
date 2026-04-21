# v4.134.0 Session Report — Sh.11 closed (by inheritance) + Sh.12 fixed: STRICT FIXED POINT REACHED

> **First strict 3-stage fixed point in the v4.x recovery arc.**
> Phase 1 verified Sh.11 (`lower_expr` SIGSEGV) was already closed
> by the v4.131.0 + v4.132.0 Sh.2 arc. Phase 2 narrowed a NEW
> blocker (Sh.12: `Ident("None")` undef in IR) to 6 self-hosted
> lowerer lines. Post-fix: stage2.ll == stage3.ll, byte-identical,
> 108,397 lines, 0 diff, MD5 match.

## Headline

**Strict 3-stage fixed point: REACHED.** stage2.ll md5
`0c00ad07fee94f98bb350b359395843b` == stage3.ll md5 (same), 108,397
lines, 0 diff. La Culebra Se Muerde La Cola. First time in the v4.x
recovery arc.

**Sh.11**: closed by Sh.2 arc (no v4.134.0 work needed beyond
verification). **Sh.12**: opened and closed in this release — 6
logic lines + 9-line comment in `mapanare/self/lower.mn`.

**Verification (no regression vs v4.132.0 / v4.133.0 baselines)**:

| Gate | v4.133.0 baseline | v4.134.0 | Δ |
|---|---|---|---|
| Strict 3-stage fixed point | blocked (Sh.11 ostensibly + Sh.12 latent) | **REACHED, 0 diff** | unblocked |
| Goldens through `mnc-stage1` | 53 / 65 | 53 / 65 | 0 |
| Valgrind ERRORS | 5 (all Ge.1) | 5 (all Ge.1) | 0 |
| Valgrind WARNINGS_ONLY | 60 | 60 | 0 |
| ASan ASAN_ERROR | 0 | 0 | 0 |
| ASan CLEAN | 54 | 54 | 0 |
| ASan CRASH_NO_ASAN | 11 (Sh.4/6/7 feature gaps) | 11 (same) | 0 |
| Pytest bootstrap | 13 fail / 212 pass | 13 fail / 212 pass | 0 |
| Pytest non-bootstrap | 0 fail / 5,109 pass | 0 fail / 5,109 pass | 0 |
| `mnc-stage1` size | 3,472,528 | 3,480,720 | +8,192 (+0.24%) |
| `libmapanare_rt.a` | unchanged | unchanged (runtime untouched) | byte-identical |

## What shipped

### Phase 1 — Sh.11 verification (no work, just measurement)

Per PROMPT.md outcome (a). Re-ran `bash scripts/verify_fixed_point.sh
--keep` against post-v4.132.0 head:

```
[Stage 1] stage1 compiles mnc_all.mn → stage2.ll
  stage2.ll: 108355 lines
  llvm-as: FAIL
llvm-as: /tmp/stage2.ll:20711:19: error: use of undefined value '%None8'
  store {i1, ptr} %None8, ptr %guard9.addr
                  ^
```

Stage1 ran to completion — no SIGSEGV in `lower_expr`. The Sh.11
crash that v4.128.0 opened is **closed as a side-effect of the Sh.2
arc** (v4.131.0 LIST + v4.132.0 STR extracted-alias drop-glue
fixes). This was the v4.126.0 triage hypothesis ("L-family
lower_expr crashes are same family as Sh.2") and PLAN.md Phase 1's
expected outcome ("likely outcome given the overlap").

But the IR was malformed. New blocker discovered.

### Phase 2 — Sh.12 narrowing (4 minutes of grep)

The error site, `parser.mn::parse_match_arm_item`, contains:

```mn
let mut guard: Option<Expr> = None
```

Trace through self-hosted pipeline:

| File:line | What happens |
|---|---|
| `lexer.mn:101,161` | `KW_NONE` only matches lowercase `none`/`nada`. Capital `None` → `NAME` token. |
| `parser.mn:1989` | `NAME` parses as `Expr::Ident("None")`. |
| `lower.mn:1304` `lower_identifier("None")` | Falls through var lookup → const lookup → `is_enum_variant` (built-in `Option` is *not* registered in `LowerState.enum_variants`) → "Unknown — emit placeholder": `make_value(mir_unknown(), "None")` → `%None<N>`, `Const(value, mir_unknown(), "")`. |
| `emit_llvm.mn:896` `emit_const` | Cases for VOID/STRING/BOOL/INT/FLOAT/STRUCT/FN. **No case for TK_UNKNOWN.** Returns without emitting. SSA value `%None<N>` is referenced (in subsequent stores) but never defined. |

The Python emitter masks the same lowerer gap via a catch-all in
`mapanare/emit_llvm_text.py:2558` (`elif v is None: zero-init`).
Self-hosted has no analog. Python bootstrap therefore produced
valid (if unusual) IR; self-hosted produced undef.

### Phase 3 — Sh.12 fix (Shape B, self-hosted lowering)

Six logic lines (plus 9-line comment) at the top of
`mapanare/self/lower.mn::lower_identifier`:

```mn
if name == "None" {
    let r_none: LowerResult = make_value(st, mir_option(), "tnone")
    let s_none: LowerState = emit_instr(r_none.state, Instruction::WrapNone(r_none.value, mir_option()))
    return new_lower_result(r_none.value, s_none)
}
```

Mirrors the existing `KW_NONE → Expr::NoneLit` lowering at
`lower.mn:1196`. Both spellings now produce identical IR.

**Why not fix the lexer**: Mapanare keywords are otherwise lowercase
across both English (`none`) and Spanish (`nada`) bindings;
capitalizing `None` would be an asymmetric exception. The semantic
checker at `semantic.mn:584` already treats `Ident("None")` as a
constructor returning `Option`, so fixing the lowerer to match the
semantic checker is the consistent-direction fix.

**Why not the emit_const catch-all**: A `TK_UNKNOWN` zero-init in
`emit_const` would close this undef but at the cost of masking
other missing-lowering bugs the same way Python's catch-all does.
Fixing the lowerer at the source leaves the emitter loud about
unhandled types — future divergences of this shape will produce
`llvm-as` failures rather than silent zero-fills.

### Phase 4 — Re-run fixed-point (the result)

```
$ bash scripts/verify_fixed_point.sh --keep
=== Three-Stage Fixed Point Verification ===

[Stage 0] Using existing stage1: mapanare/self/mnc-stage1
  stage1: 3480720 bytes
[Stage 1] stage1 compiles mnc_all.mn → stage2.ll
  stage2.ll: 108397 lines
  llvm-as: OK
  Building mnc-stage2... OK (2637816 bytes)
[Stage 2] stage2 compiles mnc_all.mn → stage3.ll
  note: mnc-stage2 exited with code 10
  (teardown crash is a known issue tracked for v4.30.0; the script
   still validates that stage3.ll is non-empty and llvm-valid below)
  stage3.ll: 108397 lines
  llvm-as: OK

[Verify] Fixed point: diff stage2.ll stage3.ll
  ✓ FIXED POINT REACHED
  stage2.ll == stage3.ll (108397 lines, 0 diff)

=== La Culebra Se Muerde La Cola ===
```

`md5sum`:

```
0c00ad07fee94f98bb350b359395843b  /tmp/stage2.ll
0c00ad07fee94f98bb350b359395843b  /tmp/stage3.ll
```

Script exit `0`. **First strict 3-stage byte-identical fixed point
in the v4.x recovery arc.**

The mnc-stage2 exit code 10 is the v4.30.0-known teardown crash —
IR is fully flushed and valid; cleanup-path bug only. Out of scope
for this release (open since v4.30.0; low-priority because IR is
correct).

## Exit-criteria scorecard

| # | Check | Target | Stretch | Result | Status |
|---|---|---|---|---|---|
| 1 | Sh.11 reproduces or not | determined | — | **closed by Sh.2 arc** (verified Phase 1) | ✅ |
| 2 | Strict 3-stage runs to completion | yes | stage2 == stage3 | **stage2 == stage3, byte-identical** | ✅ stretch hit |
| 3 | Fixed-point diff metric published | yes | ≤ 5,000 lines | **0 lines** | ✅ stretch crushed |
| 4 | Goldens regression | 53+/65 | — | 53/65 | ✅ |
| 5 | Sanitizer regression | v4.132.0 baseline | — | byte-identical (vg 0/60/5, asan 54/0/11) | ✅ |
| 6 | Pytest regression | v4.133.0 baseline | — | bootstrap byte-identical; non-bootstrap byte-identical | ✅ |

## Carry-forward

| Docket | Status | Disposition |
|---|---|---|
| Sh.11 (`lower_expr` SIGSEGV) | **CLOSED** by Sh.2 arc | confirmed this release |
| Sh.12 (`Ident("None")` undef) | **CLOSED** | this release |
| Sh.2 (extracted-alias drop-glue) | CLOSED v4.131.0/v4.132.0 | — |
| An.1 (deterministic test failures) | CLOSED v4.133.0 | — |
| Ge.1 (generics-init class) | OPEN | v5.x — 5 valgrind ERRORS unchanged |
| ABI.1 (24-byte enum sret residual) | OPEN | v5.x |
| Sh.4/5/6/7 (feature gaps) | OPEN | v5.x |
| Teardown crash (mnc-stage2 exit 10) | OPEN since v4.30.0 | low-priority — IR is correct |
| Bn.1, Rt.2, Rt.3, Ch.1, Tm.1, An.2, TR.1 | OPEN per v4.133.0 SR | v5.x |

## Diff stat

```
mapanare/self/lower.mn                                   | +15 -0 (lower_identifier: bare "None" → WrapNone)
mapanare/self/mnc_all.mn                                 | regenerated (concat_self.sh)
mapanare/self/main.ll                                    | regenerated (build_stage1.py)
mapanare/self/mnc-stage1                                 | rebuilt (3,472,528 → 3,480,720 bytes)
docs/roadmap/v4/v4.134.0/FIXEDPOINT.md                   | new
docs/roadmap/v4/v4.134.0/SESSION_REPORT.md               | new
docs/roadmap/v4/v4.134.0/asan-summary.tsv                | new
docs/roadmap/v4/v4.134.0/valgrind-summary.tsv            | new
CHANGELOG.md                                             | <release entry appended>
VERSION                                                  | 4.134.0 → 4.135.0
docs/roadmap/v4/README.md, ROADMAP.md                    | status updates
```

1 self-hosted source change (15 lines). No Python emitter changes.
No C runtime changes. `libmapanare_rt.a` byte-identical.

## What this release does NOT do

- Touch the Ge.1 generics-init class (5 valgrind ERRORS unchanged).
- Touch the v4.30.0 mnc-stage2 teardown crash (exit code 10 still
  benign; IR is correct).
- Touch ABI.1, Sh.4/5/6/7, or any v5.x-track docket.
- Run the panel.

## Next

- **v4.135.0** — Pre-panel refresh (4th flaky audit, fresh
  valgrind/ASan, benchmark refresh, MEASUREMENTS.md finalization
  with the strict-fixed-point number replacing the proxy).
- **v4.136.0** — THE PANEL (v5 gate attempt 3). Cobra's v4.99.0
  blocker ("self-hosted compiler that cannot reach 3-stage fixed
  point is not v5.0.0 material") is now closed.
