# Mapanare v4.140.0 — Self-hosted emitter parity (Cb.5 + SE.1)

> **The hardest release in the plan.** Port Rt.1 `_enum_inline`
> machinery from the Python emitter to `mapanare/self/emit_llvm.mn`,
> and apply the Sh.2 alias-vs-owner shape to MAP / SIGNAL / STREAM
> Copy paths (Sh.2-residual / SE.1).

**Status:** PLANNED
**Breaking:** Potentially (self-hosted stage1 and stage2 enum ABI
converge — existing .bc/.o produced by stage1 pre-v4.140 remain
compatible at source level; raw binaries compiled before the release
should be recompiled).
**Prerequisite:** v4.139.0 (Gr.2 closed — simplifies module-level
symbol work)
**Estimated work:** 1 long sprint. Consider splitting (see Risk #1).
**Theme:** The last emitter divergence between Python and self-hosted.

---

## Why this release

Two loud silences left by the v4.136.0 panel:

1. **Cb.5 (Cobra)**: Rt.1 inline-enum representation lives only in
   `mapanare/emit_llvm_text.py` (10 grep hits on `_enum_inline`);
   `mapanare/self/emit_llvm.mn` has zero. The fixed-point holds
   because both stages use the same self-hosted source — but
   stage1-compiled and stage2-compiled user binaries have incompatible
   enum ABI. Invisible until someone links stage1-compiled libraries
   against a stage2-compiled host, which WILL happen once v5.0.0
   ships and users start mixing compiler versions.
2. **Sh.2-residual / SE.1 (Rattler)**: the v4.131.0 + v4.132.0
   `_do_copy` fix tracks LIST and STRING but MAP / SIGNAL / STREAM
   still call `_track_container` unconditionally. No failing test
   today, but the same bug class is latent on three other container
   types.

Closing both removes the last known correctness divergence between
Python and self-hosted emitters, and gets Cobra to 9.0+ / Rattler to
9.2+ at the v4.143.0 panel.

---

## Scope

### Cb.5 — `_enum_inline` in self-hosted emitter (MEDIUM, main work)

Infrastructure needed in `mapanare/self/emit_llvm.mn`:

1. `_enum_inline` registry (mirrors Python's self-typed dict).
2. `_compute_enum_inline_slots(enum_ty)` → eligibility predicate:
   ≤ 2 payload fields, each ≤ 8 bytes, no self-ref.
3. `_type_fits_inline_slot(ty)` → per-field size check.
4. `_pack_to_i64(value, ty)` / `_unpack_from_i64(i64, ty)` →
   pack/unpack helpers.
5. Emit path: use `{i64, i64, ..., i64}` representation when
   eligible; keep `{i64, ptr}` + heap allocation otherwise.
6. Constructor + match sites updated.

Expected LOC: ~150-200 lines in `emit_llvm.mn`. Mirror Python file
as reference.

### SE.1 — Sh.2 shape for MAP / SIGNAL / STREAM (LOW)

In `mapanare/emit_llvm_text.py::_do_copy`, after the LIST + STR
branches (v4.131.0 + v4.132.0), add parallel branches for:
- MAP (`_map_slots` registry)
- SIGNAL (`_signal_slots`)
- STREAM (`_stream_slots`)

Each follows the same pattern: transfer tracking src→dest on
ownership transfer; untrack dest on alias.

### Cb.3 — mnc-stage2 `ulimit -s 65536` documentation (LOW)

Either (a) document the requirement in `docs/guides/getting_started.md`
native-mode prereqs section (added in v4.138.0), or (b) set stack
size internally via `setrlimit` call in `runtime/native/mapanare_runtime.c`
main wrapper.

Recommend (a) — runtime self-setrlimit is surprising and easy to get
wrong; documentation is the cleaner fix.

---

## Phase 1 — SE.1 (Sh.2-residual) — the easy half

This lands first to minimize regression risk while the harder Cb.5
work proceeds.

1. Locate `mapanare/emit_llvm_text.py::LLVMTextEmitter._do_copy` —
   LIST block ~2572-2591, STR block ~2600-2609.
2. After STR block, add MAP branch (same shape, `_map_slots`).
3. Add SIGNAL branch.
4. Add STREAM branch.
5. Unit tests for each in `tests/llvm/test_do_copy.py` (or create).
6. New goldens exercising MAP-aliased / SIGNAL-aliased / STREAM-
   aliased Copy paths.

## Phase 2 — Cb.5 groundwork: add registries

Add to `mapanare/self/emit_llvm.mn` the `EmitState` fields:

```mapanare
struct EmitState:
  # ... existing fields ...
  enum_inline: Map<String, InlineLayout>   # new
```

With `InlineLayout` struct:

```mapanare
struct InlineLayout:
  slot_count: Int
  field_sizes: List<Int>   # byte size per payload field
```

## Phase 3 — Cb.5 eligibility + layout

Port `_compute_enum_inline_slots(enum_ty)` / `_type_fits_inline_slot(ty)`:

```mapanare
fn compute_enum_inline_slots(st: EmitState, enum_ty: Type) -> Option<InlineLayout>:
  # Eligibility:
  #   - ≤ 2 payload fields
  #   - each field ≤ 8 bytes
  #   - no self-reference
  # Returns Some(layout) if inlineable, None otherwise.
  ...
```

Mirror Python `emit_llvm_text.py::_compute_enum_inline_slots` and
`_type_fits_inline_slot` line-for-line where possible.

## Phase 4 — Cb.5 pack/unpack helpers

`_pack_to_i64(value, ty)` / `_unpack_from_i64(i64, ty)`:

Each field's bytes shifted into position; zero-extension for unsigned,
sign-extension for signed ints, bitcast for floats.

## Phase 5 — Cb.5 use sites

Emit path in `emit_llvm.mn`:

- enum constructor: if `_enum_inline.get(enum_name)` is Some, emit
  `{i64, i64, ..., i64}` store; else existing `{i64, ptr}` + malloc.
- enum match / payload extract: emit extractvalue at inline slot
  index; else existing ptr load.
- enum deep-copy: if inline, just `load + store` the slot vector;
  else existing clone path.

## Phase 6 — Verify self-hosted enum ABI matches Python

```bash
# Compile the same program through Python and self-hosted
python3 -m mapanare emit-llvm tests/golden/07_enum_match.mn -o /tmp/py.ll
./mapanare/self/mnc-stage1 tests/golden/07_enum_match.mn > /tmp/sh.ll

# Structural diff of the enum type + constructor
culebra diff /tmp/py.ll /tmp/sh.ll --metric calls
# Expected: zero divergence on enum_match shape
```

## Phase 7 — Cb.3 docs

Add to `docs/guides/getting_started.md` native prereqs:

```markdown
### Stack size for mnc-stage2

`mnc-stage2` (the self-hosted compiler built from mnc-stage1's output)
requires a larger-than-default stack to compile `mnc_all.mn`:

    ulimit -s 65536   # 64 MiB stack

On systems where you cannot `ulimit` (Docker without `--ulimit`,
some CI runners), export `MAPANARE_STACK=64M` and the compiler driver
will spawn a child thread with the larger stack.
```

If (a) is chosen, no code change. If (b), add a driver thread in
`runtime/native/mapanare_runtime.c` main wrapper.

## Phase 8 — Full verify

```bash
python3 -m pytest tests/ --ignore=tests/bootstrap -q --tb=no
python3 -m pytest tests/bootstrap/ --tb=no -q

# Fixed-point md5 will change (self-hosted source changed); record new
bash scripts/verify_fixed_point.sh --keep
md5sum /tmp/stage2.ll /tmp/stage3.ll

# Goldens: 54 → 58 target (enum-using SE.1 goldens)
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1 2>&1 | tail -5

# Sanitizer sweeps — expect no new ERRORS
VG_OUTDIR=/tmp/vg bash scripts/valgrind_all_goldens.sh
bash scripts/run_asan_goldens.sh

# Benchmarks — enum_match perf delta between Python and self-hosted
# should now be negligible (both inline)
python3 benchmarks/cross_language/run_benchmarks.py --filter enum_match --runs 10
```

---

## Exit criteria

| # | Check | Required |
|---|---|---|
| 1 | `_enum_inline` machinery in `mapanare/self/emit_llvm.mn` | yes |
| 2 | Self-hosted enum layout matches Python structurally (culebra diff 0) | yes |
| 3 | Stage1-compiled + stage2-compiled enum binaries link cleanly (ABI parity) | yes |
| 4 | Fixed-point still holds (stage2 == stage3) after enum codegen change | yes |
| 5 | MAP / SIGNAL / STREAM Copy paths apply Sh.2 shape | yes |
| 6 | Sh.2-residual goldens all clean under valgrind + ASan | yes |
| 7 | Non-bootstrap pytest baseline hold | yes |
| 8 | Goldens ≥ 54/65 through mnc-stage1 (no regressions) | yes |
| 9 | Valgrind ≤ 5 ERRORS (Ge.1 residual) | yes |
| 10 | ASan 0 ASAN_ERROR | yes |
| 11 | Cb.3 — ulimit documented or set internally | yes |
| 12 | Cb.5, SE.1, Cb.3 CLOSED in DOCKET_LEDGER | yes |

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Cb.5 scope blows up — self-hosted emitter lacks support infra | **HIGH** | high | **Pre-plan a split: v4.140.0 ships SE.1 + Cb.3 + Cb.5 registries only; v4.140.5 or v4.141.0a ships Cb.5 full port.** Don't push through scope creep. |
| Fixed-point breaks mid-port (stage2 ≠ stage3 while code lands) | medium | high | Gate every sub-commit through `verify_fixed_point.sh`; don't commit intermediate states that diverge |
| Enum ABI change breaks existing compiled `.o` files | low | medium | Document in CHANGELOG; version-stamp enum representation if needed |
| MAP / SIGNAL / STREAM have different alias shapes than LIST / STR | medium | medium | Audit each one's runtime `__mn_*` free-glue before porting; adjust shape if different |

## What this release does NOT do

- Does not close Sh.4 / Sh.5 / Sh.6 / Sh.7 (self-hosted async /
  const / tensor / closure-typed feature gaps) — v5.x feature track.
- Does not close Ge.1 (generics-init uninit reads) — v4.142.0.
- Does not touch lint / An.2 — v4.141.0.
- Does not touch SPEC (done in v4.139.0).

## Score-impact forecast

Cobra 8.7 → 9.1; Rattler 8.9 → 9.1; small bonus to Viper (Sh.2 class
fully closed).
