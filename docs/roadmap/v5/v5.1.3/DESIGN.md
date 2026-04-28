# Own.1 Phase 1 — Design Document

> **Decision: annotation, not inference. Split: workaround now, Move
> instruction deferred.**
>
> Session 1 (2026-04-22). Pre-code design phase.

---

## 1. Critical Finding: No Drop-Glue in Self-Hosted Emitter

The PLAN.md and execution prompt assume `emit_llvm.mn` has an
`emit_drop_glue` function that walks live locals at function epilogue
and emits free calls. **This does not exist.**

| Feature | Python emitter (`emit_llvm_text.py`) | Self-hosted emitter (`emit_llvm.mn`) |
|---------|--------------------------------------|--------------------------------------|
| Drop-glue at return | `_emit_drop_glue` (line 1576, ~50 lines + 5 per-kind helpers) | **None** — bare `ret` instruction |
| Move tracking | `_move_resource` (line 1380) + `_do_call` blanket-move (line 3882) | **None** |
| Ownership slots | `_str_slots`, `_list_vars`, `_boxed_slots`, `_local_closures`, `_map_vars`, `_signal_vars`, `_stream_vars`, `_tensor_vars` | **None** |
| EmitState fields | 8 per-function tracking dicts (reset at `_emit_fn` line 2158) | 11 fields total, zero ownership-related (`emit_llvm.mn:58-70`) |

**Consequence:** The execution prompt's "in `emit_drop_glue`, filter
out moved locals" cannot be implemented as written. There is no
`emit_drop_glue` to filter.

The design space IS wider than expected. Per the execution prompt:
> "If the design space reveals itself wider than expected in Phase 1,
> **split the release**: ship the detection mechanism only, defer the
> retrofit to v5.1.4."

---

## 2. Current Safety State

### Why the bug hasn't manifested

Both paths are currently **safe** for different reasons:

**Python emitter path (bootstrap compiling `*.mn`):**
- `_do_call` at line 3882 already moves EVERY argument to EVERY user
  function call. When `register_struct` calls `new_struct_info(name, fields)`,
  `fields` is removed from `_list_vars` and its tracking slot is zeroed.
  Drop-glue at `return s` skips it. Safe by construction.

**Self-hosted emitter path (`mnc-stage1` compiling `*.mn`):**
- No drop-glue exists. At `return s`, the bare `ret` instruction fires.
  No free calls are emitted for ANY local. The backing buffers are still
  referenced by the module state via the `StructInfo`/`EnumInfo` that was
  pushed. No double-free. But also no cleanup of non-transferred locals
  (minor leak of list headers for locals that alias transferred data).

### The hazard

When the self-hosted emitter eventually adds drop-glue (required for
parity with the Python emitter — currently a systemic divergence, not
just these two functions), `register_struct` and `register_enum` will
become double-free sites unless move tracking is in place first.

The Cb.7 workaround (manually zeroing locals after push) is applied at
monomorphization sites (`lower.mn:1795-1798`, `lower.mn:1993-1998`) but
NOT at the top-level registration sites (`register_struct` line 330,
`register_enum` line 357). This inconsistency is what Viper has flagged
for 28 releases.

---

## 3. Decision: Annotation vs Inference

**Decision: Annotation (`@takes_ownership`).** But deferred to v5.1.4.

Rationale:
- Annotation is simpler and explicit — no dataflow analysis needed.
- But annotation requires parser recognition of `@takes_ownership` on
  function parameters, which the self-hosted grammar doesn't support.
  Adding it requires touching `lexer.mn`, `parser.mn`, `semantic.mn`,
  `mir.mn`, `lower.mn`, and `emit_llvm.mn` — plus the Python mirrors.
- The self-hosted emitter has no drop-glue to filter, making the full
  annotation infrastructure dead code until drop-glue is added.
- The Cb.7 workaround (zero-after-push) achieves the same safety
  guarantee with 6 lines of code and no infrastructure changes.

**Phase 1 (v5.1.3):** Ship the Cb.7 workaround at `register_struct`
and `register_enum`. This is "detection mechanism only" — we've
identified the sites, neutralized them, and documented the design.

**Phase 2 (v5.1.4+):** Add drop-glue to the self-hosted emitter,
`Move` instruction to MIR, `@takes_ownership` recognition, and
`moved_locals` filtering. This is the "retrofit."

---

## 4. What v5.1.3 Ships

### 4a. Cb.7 workaround applied to register_struct (lower.mn:324-330)

Before:
```mapanare
let info: StructInfo = new_struct_info(data.name, fields)
s.module = module_push_struct(s.module, info)
let sfi: StructFieldInfo = new_struct_field_info(data.name, field_names, field_types)
let mut sf_lst: List<StructFieldInfo> = s.struct_fields
sf_lst.push(sfi)
s.struct_fields = sf_lst
return s
```

After:
```mapanare
let info: StructInfo = new_struct_info(data.name, fields)
s.module = module_push_struct(s.module, info)
let sfi: StructFieldInfo = new_struct_field_info(data.name, field_names, field_types)
let mut sf_lst: List<StructFieldInfo> = s.struct_fields
sf_lst.push(sfi)
s.struct_fields = sf_lst
// Own.1 (v5.1.3): clear moved-ownership locals.
// Mirrors Cb.7 pattern at monomorphize sites (lines 1795-1798).
// fields/field_names/field_types ownership moved into module via
// info and sfi. Zero headers so future drop-glue won't double-free.
fields = []
field_names = []
field_types = []
return s
```

### 4b. Cb.7 workaround applied to register_enum (lower.mn:350-357)

Before:
```mapanare
let info: EnumInfo = new_enum_info(data.name, variants)
s.module = module_push_enum(s.module, info)
let evn: EnumVariantNames = new_enum_variant_names(data.name, variant_names)
let mut ev_lst: List<EnumVariantNames> = s.enum_variants
ev_lst.push(evn)
s.enum_variants = ev_lst
return s
```

After:
```mapanare
let info: EnumInfo = new_enum_info(data.name, variants)
s.module = module_push_enum(s.module, info)
let evn: EnumVariantNames = new_enum_variant_names(data.name, variant_names)
let mut ev_lst: List<EnumVariantNames> = s.enum_variants
ev_lst.push(evn)
s.enum_variants = ev_lst
// Own.1 (v5.1.3): clear moved-ownership locals.
// Mirrors Cb.7 pattern at monomorphize sites (lines 1997-1998).
variants = []
variant_names = []
return s
```

### 4c. Python bootstrap — no changes needed

The Python emitter already handles this via `_do_call`'s blanket
move-on-call (line 3882). Verification only — no code changes.

### 4d. DESIGN.md (this document)

Documents the full design for the Move instruction and @takes_ownership
annotation for v5.1.4+.

---

## 5. Future Design: Move Instruction + @takes_ownership (v5.1.4+)

### 5a. MIR Move instruction

Add `Move(Value)` variant to `Instruction` enum in `mir.mn` (line 227)
and `Move` dataclass to `mir.py` (after `Phi` at line 754).

Semantics: marks a local as moved. The emitter adds it to a
`moved_locals` set and skips it during drop-glue.

### 5b. @takes_ownership annotation

Compiler-internal attribute on function parameters. Not user-facing.
When the lowerer sees a call to a function whose parameter is annotated
`@takes_ownership`, it emits `Move(arg_value)` before the `Call`
instruction.

Recognition sites in `lower.mn`:
- `lower_call_by_name` (line 2197+): the general function-call path
- Needs callee parameter metadata lookup

### 5c. EmitState.moved_locals

Add `moved_locals: List<String>` to `EmitState` (line 70). Reset per
function. Populated by `Move` instruction handler. Consulted by
drop-glue (once it exists).

### 5d. Drop-glue for self-hosted emitter

The largest piece of deferred work. Requires:
- Per-function ownership tracking (parallel to Python's 8 tracking dicts)
- Escape analysis for return values (parallel to `_emit_drop_glue_collect_ret_ptrs`)
- Per-kind free-call emission (strings, lists, maps, closures, boxed, signals, streams, tensors)
- Integration with `emit_mir_return`

Estimated: 200-400 lines of Mapanare in `emit_llvm.mn`. This is the
piece that makes `moved_locals` actually useful.

### 5e. Tagged call sites

When @takes_ownership is implemented, these functions should have their
`entry`/`info` parameters tagged:

| Function | Parameter | Location |
|----------|-----------|----------|
| `module_push_struct` | `info: StructInfo` | `lower.mn:2652` |
| `module_push_enum` | `info: EnumInfo` | `lower.mn:2658` |
| `emit_state_push_function` | likely same pattern | TBD |
| `register_trait` | if same build-push-return pattern | TBD audit |
| `register_impl` | if same build-push-return pattern | TBD audit |

An audit of all `module_push_*` and `*_push_*` functions should be
done at v5.1.4 time.

---

## 6. Fixed-Point Impact

The Cb.7 workaround adds `ListInit` instructions (empty list creation)
to the MIR for `register_struct` and `register_enum`. When the Python
bootstrap compiles `lower.mn`:
- New `__mn_list_create` calls appear in the stage1 binary's code
  for `register_struct` and `register_enum`
- The Python emitter's `_do_call` has already moved the old values,
  so the new empty-list assignments just create fresh empties that
  drop-glue cleans up — no semantic change
- The stage1 binary is different (new instructions), so stage2.ll
  will differ from the pre-change stage2.ll
- But stage2.ll == stage3.ll should hold: both are produced by the
  same stage1 binary with the same input

**Risk: LOW.** The workaround does not change any emitter behavior —
only the lowerer source. The emitter produces the same output for
the same MIR regardless of whether register_struct zeros its locals.

---

## 7. Risks

**Risk 1 — The Cb.7 workaround creates new leaks in self-hosted path.**
The `fields = []` creates a fresh empty list that goes out of scope
at `return` without cleanup (since the self-hosted emitter has no
drop-glue). This is a minor leak (~40 bytes per struct registration).
The pre-existing state also leaked the list headers. Net change: same
class of leak, different (smaller) value leaked. Acceptable.

**Risk 2 — Fixed-point breaks.**
The workaround adds instructions to `register_struct`/`register_enum`.
This changes the stage1 binary, which changes stage2.ll. But
stage2==stage3 should hold since both are produced by the same binary.
**Mitigation:** `bash scripts/verify_fixed_point.sh --keep` before
shipping.

**Risk 3 — Valgrind finds new issues.**
The workaround changes allocation patterns in the compiler binary
(new empty-list-create + old-list-header now dangling). This could
surface new valgrind warnings.
**Mitigation:** full valgrind sweep on all goldens.

---

## 8. Relationship to Panel Scores

Viper's Own.1 ceiling argument (v4.144.0, v4.154.0):
- **Specific complaint:** `register_struct`/`register_enum` latent UAF
- **General complaint:** no borrow checker in the language

This release addresses the specific complaint. The Cb.7 workaround
neutralizes the specific sites. The DESIGN.md documents the path to
the Move instruction infrastructure.

For the v5.3.0 panel, Viper should see:
- Own.1 specific sites closed (Cb.7 workaround applied)
- Own.1 design documented for the general case
- The 9.6 ceiling may shift to ~9.7 (specific closure) but the general
  borrow-checker argument stands until v6.0

---

## 9. Summary

| Item | v5.1.3 (this release) | v5.1.4+ (deferred) |
|------|-----------------------|--------------------|
| Cb.7 workaround at register_struct/register_enum | **Ships** | N/A |
| `Move` instruction in MIR | Deferred | Ships |
| `@takes_ownership` annotation | Deferred | Ships |
| `moved_locals` in EmitState | Deferred | Ships |
| Drop-glue in self-hosted emitter | Deferred | Ships (largest piece) |
| Python emitter changes | None needed | Handle Move instruction |
| DESIGN.md | **Ships** | Updated |
