# v4.134.0 — Strict 3-Stage Fixed Point: REACHED

> First strict 3-stage fixed point in the v4.x recovery arc.
> Stage2.ll == Stage3.ll, byte-identical, 108,397 lines, 0 diff,
> matching MD5 hashes.

## Headline

```
stage2.ll: 108,397 lines  md5 = 0c00ad07fee94f98bb350b359395843b
stage3.ll: 108,397 lines  md5 = 0c00ad07fee94f98bb350b359395843b
diff -q  : (no output) — files are byte-identical
diff | wc: 0 lines
```

`scripts/verify_fixed_point.sh --keep` reports:

```
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

Script exit: `0`.

## What changed since v4.128.0

| Release | Strict 3-stage status | Proxy diff (Python vs stage1, 39 goldens) |
| --- | --- | --- |
| v4.127.0 | blocked (Sh.8 self-hosted None/Some/Ok constructor reg) | 9,971 lines |
| v4.128.0 | blocked (**Sh.11** lower_expr SIGSEGV in mnc_all.mn) | 9,425 lines |
| v4.131.0 | blocked (Sh.11 still presumed) | not measured |
| v4.132.0 | blocked (Sh.11 still presumed) | not measured |
| v4.133.0 | **partial unblock** — Sh.11 SIGSEGV closed by Sh.2 arc, stage1 produces 108,355 lines, but `%None8` undef makes IR llvm-as-invalid | not measured |
| v4.134.0 | **REACHED** — stage2.ll == stage3.ll, 108,397 lines, 0 diff | not measured (proxy now subsumed by strict metric) |

## Phase 1 finding: Sh.11 closed by the Sh.2 arc

Phase 1 of the v4.134.0 PROMPT was a verification step: re-run
`scripts/verify_fixed_point.sh` on top of post-v4.132.0 head. The
`lower_expr` SIGSEGV that v4.128.0 opened as Sh.11 **does not
reproduce** — stage1 ran to completion on `mnc_all.mn`, producing
108,355 lines of IR. The Sh.2 arc (v4.131.0 LIST + v4.132.0 STR
extracted-alias drop-glue fixes) closed the upstream UAF that was
manifesting as the lower_expr crash. **Sh.11 is closed as a
side-effect of v4.131.0 + v4.132.0**, no v4.134.0 work required to
close it.

## Phase 2 finding: Sh.12 (new docket, opened and closed this release)

The post-Sh.11 stage1 output failed `llvm-as` validation:

```
llvm-as: /tmp/stage2.ll:20711:19: error: use of undefined value '%None8'
  store {i1, ptr} %None8, ptr %guard9.addr
                  ^
```

Root cause traced through:

1. `mapanare/self/lexer.mn:101,161` — `KW_NONE` token only matches
   lowercase `none` / `nada`. Capital `None` (used throughout
   `mnc_all.mn`, e.g. `parser.mn:2063` `let mut guard: Option<Expr> =
   None`) tokenizes as `NAME`.
2. `mapanare/self/parser.mn:1989` — `NAME` tokens parse as
   `Expr::Ident(name)`.
3. `mapanare/self/lower.mn:1304` `lower_identifier("None")` — falls
   through past var lookup, module-const lookup, and
   `is_enum_variant` (built-in `Option::None` is **not** registered
   in `LowerState.enum_variants`) to the final
   "Unknown — emit placeholder" branch:
   ```mn
   let r_unk = make_value(st, mir_unknown(), name)        // %None<N>
   let s_unk = emit_instr(Instruction::Const(r_unk.value, mir_unknown(), ""))
   ```
4. `mapanare/self/emit_llvm.mn:896` `emit_const` — has cases for
   `TK_VOID`, `TK_STRING`, `TK_BOOL`, `TK_INT`, `TK_FLOAT`,
   `TK_STRUCT`, `TK_FN` — and **no case for `TK_UNKNOWN`**. Falls
   through to `// Unknown type — no-op` and returns. The SSA value
   `%None8` is never defined, even though the `Const` MIR
   instruction was emitted.

The Python emitter masks the same lowerer gap via a catch-all in
`mapanare/emit_llvm_text.py:2558`:

```python
elif v is None:
    ty = self._rty(i.ty)
    self._put(i.dest, _zero(ty), ty)
```

— a zero-init of the resolved type. Self-hosted `emit_const` has no
analog. The Python bootstrap therefore produces valid (if
semantically unusual) IR for `Ident("None")`; the self-hosted
emitter produces undef.

### Fix

Six logic lines (plus a 9-line comment) at the top of
`mapanare/self/lower.mn::lower_identifier`:

```mn
if name == "None" {
    let r_none: LowerResult = make_value(st, mir_option(), "tnone")
    let s_none: LowerState = emit_instr(r_none.state, Instruction::WrapNone(r_none.value, mir_option()))
    return new_lower_result(r_none.value, s_none)
}
```

Mirrors the `KW_NONE → Expr::NoneLit` lowering already at
`lower.mn:1196`. Both spellings now produce identical
`Instruction::WrapNone(value, mir_option())` output.

### Why not fix in the lexer

Adding capital `None` to `keyword_token_type` would also work, but
two reasons against:

- Mapanare keywords are otherwise lowercase across both English and
  Spanish bindings (`none`/`nada`, `some` is not a keyword either).
  Capitalizing `None` would be an asymmetric exception.
- The semantic checker at `mapanare/self/semantic.mn:584` already
  treats `Ident("None")` as a constructor (`return
  new_infer_result(make_type("Option"), st)`), so the type system
  expects `None` as an identifier. Fixing the lowerer to match the
  checker is the consistent-direction fix.

### Why not the emit_const catch-all

A `TK_UNKNOWN` zero-init in `emit_const` would close the immediate
undef but at the cost of masking other missing-lowering bugs the
same way Python's catch-all does. Fixing the lowerer at the source
of the problem (the `Ident("None")` resolution) leaves
`TK_UNKNOWN` Const as a meaningful no-op, so future divergences
of this shape produce loud `llvm-as` failures rather than silent
zero-fills.

## Diff between Python bootstrap and stage1/2/3

Not measured this release. The v4.128.0 proxy metric (9,425 line
diff between Python-bootstrap output and `mnc-stage1` output on 39
passing goldens) is now subsumed by the strict 3-stage metric: the
self-hosted compiler is **bit-stable on its own source**.

The Python bootstrap currently fails to emit `mnc_all.mn` directly
via `python3 -m mapanare emit-llvm` due to a semantic-check
arity-mismatch (`parse_expr expects 4, got 3`) that is pre-existing
and unrelated to v4.134.0; the bootstrap path used by
`scripts/build_stage1.py` bypasses the CLI entry point and is
unaffected. Investigating that arity gap is out of scope for this
release.

## What this fixed-point result means for the v4.136.0 panel

The v4.99.0 panel (Cobra) flagged "no fixed-point self-compilation"
as a v5 blocker. The v4.120.0 panel reaffirmed it. The v4.128.0
proxy metric was a partial answer — informative but not strict.

**v4.134.0 closes the strict-fixed-point question.** The compiler
compiles itself. The output of compiling the source with stage1 is
byte-identical to the output of compiling the source with stage2.
La Culebra Se Muerde La Cola.

Remaining open dockets (v4.135.0 + v4.136.0 carry-forward):

| Docket | Status | Disposition |
| --- | --- | --- |
| Sh.11 (lower_expr SIGSEGV) | **CLOSED** by Sh.2 arc | this release confirmed |
| Sh.12 (`Ident("None")` undef) | **CLOSED** | this release |
| Ge.1 (generics-init class) | OPEN | v5.x |
| An.1 (deterministic test failures) | CLOSED v4.133.0 | — |
| ABI.1 (24-byte enum sret residual) | OPEN | v5.x |
| Sh.4/5/6/7 (feature gaps) | OPEN | v5.x |
| Teardown crash (mnc-stage2 exit code 10) | OPEN since v4.30.0 | low-priority — IR is correct, crash is in cleanup |

## Artifacts

- Stage2 IR: `/tmp/stage2.ll` (108,397 lines, md5 0c00ad07...)
- Stage3 IR: `/tmp/stage3.ll` (108,397 lines, md5 0c00ad07...)
- Stage2 binary: `/tmp/mnc-stage2` (2,637,816 bytes)
- Stage1 binary: `mapanare/self/mnc-stage1` (3,480,720 bytes,
  +8,192 bytes vs v4.133.0 from the 6 logic lines + new comment +
  IR re-emission cascade)
- Run logs: `/tmp/v4134_fp_run.log` (pre-fix, llvm-as FAIL),
  `/tmp/v4134_fp_run2.log` (post-fix, FIXED POINT REACHED)
