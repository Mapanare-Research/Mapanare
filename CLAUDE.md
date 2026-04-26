# CLAUDE.md

Guidance for Claude Code working in this repository.

## Project Overview

Mapanare is an AI-native compiled language with first-class agents,
signals, streams, and tensors. Compiles to LLVM IR (primary) and C
(fallback via gcc). WebAssembly backend for browser/server targets.
Self-hosted compiler is 38,000+ lines of `.mn` across 10 modules in
`mapanare/self/`. The compiler compiles itself —
`bash scripts/build_from_seed.sh` builds from source with no Python.

**Current version:** see `VERSION` file.

## Current Version & Roadmap

Most recent releases (last 6). Full history at
`docs/roadmap/ROADMAP.md`:

- **v5.7.0** (shipped) — **Sh.7 + B CLOSED — 66/66 — first
  time in project history.** Closes the final two parity gaps
  for full-corpus self-hosting. **Sh.7** (closure-typed
  parameters): four self-hosted changes — `parser.mn`'s
  `FAT_ARROW` handler now extracts multi-param lambdas from
  `(a, b) => ...` (was: only single-`Ident` LHS), closing the
  "Undefined variable 'a'" pre-condition; `lower.mn::lower_call_by_name`
  routes calls through fn-typed locals via indirect-call SSA
  name (`lookup_var(fn_name)` → if `addr.ty.kind == TK_FN()`
  then emit `Load` + `Call(dest, "%loaded_val", args)`),
  mirroring Python `_lower_call(Identifier)` v4.103.0 docket
  #5; `emit_llvm_ir.mn::emit_call_ir` / `emit_call_void`
  recognise `%`-prefixed callees and emit
  `call <ret> %fn(<args>)` without the `@` prefix; `mir_opt.mn`'s
  `clone_instr_for_inline` and `replace_uses_in_instr` rename
  Call's `fn_name` when it's an SSA value (closes the
  inliner's dangling-reference issue). Plus a parity-shaping
  follow-on: `lower_lambda` numbers lambdas after the
  `tmp_counter` at creation time (matching Python's
  `_fresh_tmp("lambda")`); `scripts/test_native.py` compares
  lambda functions by COUNT (not name) since lambda names are
  arbitrary intermediates derived from the lowerer's tmp
  counter. **B** (or-pattern + `None` identifier in Python
  bootstrap): `_is_enum_variant_name` short-circuits to True
  for built-in `None`/`Some`/`Ok`/`Err` (was: only walked
  user-defined enums, treating `None` as a fresh binding name);
  `Identifier("None")` resolves to `Option` in both
  `_infer_expr` (semantic) and `_lower_identifier` (lower) —
  mirrors self-hosted v4.134.0 Sh.12 fix. Self-hosted
  `bind_pattern` doesn't have the over-strict check (just
  binds from the first alt) — no mirror needed. **Hero metric**:
  Goldens **65/66 → 66/66** — first ever 100% native pass.
  Re-blessed `tests/golden/51_match_guards_and_or.ref.ll` (2
  fns, 298 lines). New tests: 5 in
  `test_or_pattern_guards.py` + 3 in
  `test_closure_typed_params.py`. **Metrics**: stage2.ll
  **217,879 lines / 943 defines** (+0.28% vs v5.6.13);
  `llvm-as` clean; **goldens 66/66**; non-bootstrap pytest
  **5,606 passed / 0 failed**; bootstrap pytest **225 passed /
  0 failed** (was 13 baseline including 51); fixed-point
  **NEAR FIXED POINT** preserved (4 diff lines / 217,879 =
  0.002%, all VERSION metadata); ASan UAF **65 CLEAN /
  0 ASAN_ERROR / 1 CRASH_NO_ASAN**; valgrind **0 ERRORS /
  66 WARNINGS_ONLY**; LSan baseline gate **PASS** with
  improvement (62_list_output 13 → 9 leaked objects);
  `make lint` clean; `check_struct_registry.py` 23/23/91
  clean. `known_issues.md` Sh.7 row → CLOSED v5.7.0;
  `PARITY_GAPS.md` Sh.7 row → Historical. The closure arc
  closes; every test in the corpus that defines
  "self-hosting" now passes through `mnc-stage1`. La Culebra
  Se Muerde La Cola — across the whole 66-test corpus. Next:
  v5.7.1 (SPEC + docs polish, pre-panel); v5.8.0 (RE-PANEL,
  target 9.7+); v6.0 (borrow checker → Rt.04). See
  `docs/roadmap/v5/v5.7.0/SESSION_REPORT.md`.
- **v5.6.13** (shipped) — **Layer 1 cleanup — destination
  passing extended to struct let-bindings; v5.6.x arc remains
  complete.** Optional cleanup release per v5.6.13 PLAN's
  decision tree (v5.6.12 sanitizer matrix all clean → user
  chose "Ship Layer 1 ext only" path). Extends v5.6.12's
  destination-passing pattern from List let-bindings to
  **Struct** let-bindings, eliminating the duplicate `.si`
  scratch alloca that `emit_struct_init` /
  `emit_struct_init_from_values` created for every struct
  constructor call. New helper
  `lower_struct_new_into(st, struct_name, arg_exprs, dest_name)`
  parallel to v5.6.12's `lower_list_typed_into`. The parser
  encodes `let foo: Foo = new Foo {...}` as
  `Call(Ident("__new_Foo"), [val1, val2, ...])` (see
  parser.mn::parse_struct_construct); `lower_call_by_name`
  unwraps `__new_X` calls into `Instruction::StructInit` with
  a fresh-tmp dest. For let-bindings, `lower_let` detects this
  pattern up front and routes through `lower_struct_new_into`,
  pre-computing the var's binding name `%foo<N>` and skipping
  its own post-emit `Alloca` + `Store` entirely. The emit-side
  `dn + ".si"` → `dn + ".addr"` rename in `emit_struct_init`
  and `emit_struct_init_from_values` means the renamed scratch
  IS the let's binding alloca for destination-passed dests —
  one alloca instead of (.si scratch + .addr binding) and one
  fewer load+store at the let boundary. **Hero metric**:
  `.si = alloca` site count in stage2.ll **240 → 0**. Net
  struct allocas **2,206 → 2,113 (−93)** (eliminating the .si
  scratch entirely). **What does NOT ship**: Layer 1 extension
  to enum + map let-bindings (SKIPPED after empirical analysis
  — `emit_enum_init` and `emit_map_init` produce purely
  register insertvalue chains with no `.si`-equivalent scratch
  alloca; destination passing yields net-zero IR savings for
  those, just shifts the Store from lower_let into the emit
  function). Layer 2 (move-on-assignment) NOT shipped — PLAN
  §D3 gated on observed share-mutate leak; v5.6.12 sanitizer
  sweep surfaced none. Per "no cheap shit": Layer 2 stays
  conditional v5.6.14+ work IF a leak surfaces. **Metrics**:
  stage2.ll **216,842 → 217,268 lines (+0.20%)** — modest
  growth from the new helper's ~80 LOC of self-hosted source
  emitting non-struct allocas (~157 net new) that slightly
  outweigh the 93-net struct alloca savings; well within the
  PROMPT 1% budget. `llvm-as` clean; goldens **64/66
  preserved** (same 2 pre-existing fails: 51 B, 64 Sh.7);
  fixed-point **NEAR FIXED POINT** (4 diff lines / 217,268 =
  0.002%, all VERSION metadata, identical structural result
  to v5.6.12); ASan UAF **65 CLEAN / 0 ASAN_ERROR /
  1 CRASH_NO_ASAN**; valgrind **0 ERRORS /
  66 WARNINGS_ONLY**; LSan baseline gate **PASS** (no
  regressions vs v5.4.2 baseline; same 3 LEAKs as v5.6.12:
  39_gpu_detect, 40_gpu_tensor, 62_list_output);
  non-bootstrap pytest 0 failures; `make lint` clean;
  `check_struct_registry.py` 23/23/91 clean. No
  `known_issues.md` edits required (preventive cleanup, no
  new or closed dockets — this is structural hygiene, not a
  bug fix). The v5.6.x closeout arc remains complete; the
  only v6.0 carry is Rt.04 (multi-level alias analysis,
  struct→list→string depth-2) from v5.6.6. Decision-tree
  result: v5.6.12 sanitizer matrix all clean; no NEW
  share-mutate leak (the 62_list_output baseline was
  pre-existing Rt.04 already deferred to v6.0); user chose
  "Ship Layer 1 ext only" per PLAN §"Decision tree" —
  preventive cleanup with no observable bug pressure. Next:
  v5.7.0 (Sh.7 + B or-pattern → 66/66); v5.7.1 (SPEC docs
  polish); v5.8.0 (RE-PANEL); v6.0 (borrow checker → Rt.04).
  See `docs/roadmap/v5/v5.6.13/SESSION_REPORT.md`.
- **v5.6.12** (shipped) — **Lk.1 + Ve.2 CLOSED — destination
  passing for List let-bindings; the v5.6.x closeout arc is
  complete.** Closes Lk.1 (alloca-aliasing leak in inline
  list-get/push pattern, opened v5.6.10) at its structural
  root cause via destination-passing semantics in
  `lower.mn::lower_let`. New helper
  `lower_list_typed_into(st, elements, hint, dest_name)`
  accepts a caller-supplied dest name; when value is a list
  literal with an annotated element type, `lower_let`
  pre-computes the var's alloca name (e.g. `%indices0.addr`)
  and lowers the `ListInit` directly into it — no scratch
  `%t<N>.addr`, no `Store(%var.addr, %t<N>)` copy. The
  emitter's `dn + ".addr"` convention then derives the same
  alloca name as the let var: one alloca, one tracking
  entry, no copy. Mirrors rustc's `PlaceRef`-based codegen
  (result-location semantics). With Lk.1 closed at the source,
  the v5.6.10 scalar gate is applied in the same release:
  `if elem_ty.kind == TK_UNKNOWN() { if elem_sz_n < 384 {
  elem_sz_n = 384 } }` replaces the unconditional 384-byte
  floor in `emit_list_init`'s scalar branch. Known scalar
  elem_ty (Int=8, Float=8, Bool=8, ptr=8) gets exact LLVM size;
  UNKNOWN keeps the defensive floor. Closes all 7 Ve.2 residual
  `__mn_list_new(i64 384)` sites in `expr_tensor_shape`,
  `instr_tensor_shape`, `parse_tensor_lit` ×2,
  `new_lower_state`, `new_emit_state`, `build_match_arms`.
  **Hero metrics**: `__mn_list_new(i64 384)` site count
  **7 → 0** in stage2.ll; `65_list_int_indexing` LSan
  **CLEAN** (was: would leak 80 bytes if the scalar gate were
  applied without Lk.1 closure — exactly the v5.6.10 revert
  decision now reversed); fixed-point **NEAR FIXED POINT**
  preserved (4 diff lines / 216,842 = 0.002%, all VERSION
  metadata). **Adjacent finding** — 62_list_output's
  pre-existing Rt.04 leak became visible: with the duplicate
  alloca eliminated, LSan's "still reachable" heuristic no
  longer finds a stale stack pointer aliasing into the heap
  buffer, so the 144-byte list buffer (with 9 strings inside)
  is correctly reported as a direct leak. The leak source is
  unchanged (struct→list→string depth-2 alias from v5.6.6
  Rt.04 RESCOPE); LSan baseline TSV refreshed 9 obj/141 B
  → 13 obj/346 B. Closing the underlying Rt.04 leak requires
  multi-level alias analysis — v6.0 borrow-checker scope.
  Mirrors the v5.6.10 LSan-heuristic-shift pattern. **Layer 2
  (move on assignment)** is NOT in this release — no
  share-mutate leak in the corpus, so per "no cheap shit"
  Layer 2 is conditional v5.6.13+ work IF a leak surfaces.
  **Metrics**: stage2.ll **217,273 → 216,842 lines (−0.20%)** —
  DECREASED (eliminated duplicate allocas + stores compensate
  for any growth elsewhere); `llvm-as` clean; goldens **64/66
  preserved** (same 2 pre-existing fails: 51 B, 64 Sh.7);
  ASan UAF **65 CLEAN / 0 ASAN_ERROR / 1 CRASH_NO_ASAN**;
  valgrind **0 ERRORS / 66 WARNINGS_ONLY**; LSan baseline
  gate **PASS**; non-bootstrap pytest **5598 passed** (the
  parallel pytest run flagged 2 test-isolation flakes
  unrelated to the changes — both pass when run individually
  or under `-p no:xdist`); `make lint` clean;
  `check_struct_registry.py` 23/23/91 clean.
  `known_issues.md` Lk.1 + Ve.2 rows flipped to CLOSED v5.6.12;
  `PARITY_GAPS.md` Lk.1 row updated CLOSED. The closeout arc
  completes: v5.6.5 (Ve.1) → v5.6.6 (Rt.04 RESCOPED) → v5.6.7
  (Ve.2 PARTIAL) → v5.6.8 (Ve.3 investigation) → v5.6.9
  (Ve.3 CLOSED; Ve.4 OPENED) → v5.6.10 (Ve.2 FURTHER PARTIAL
  + struct_byte_size + culebra; Lk.1 OPENED) → v5.6.11 (Ve.4
  CLOSED) → **v5.6.12 (Lk.1 + Ve.2 CLOSED; v5.6.x arc
  genuinely complete)**. The only remaining v6.0 carry from
  any v5.6.x release is Rt.04 (multi-level alias analysis,
  struct→list→string depth 2), with its own scoping rationale
  from v5.6.6. Next: v5.7.0 (Sh.7 + B or-pattern → 66/66);
  v5.7.1 (SPEC docs polish); v5.8.0 (RE-PANEL); v6.0 (borrow
  checker → Rt.04). See
  `docs/roadmap/v5/v5.6.12/SESSION_REPORT.md`.
- **v5.6.11** (shipped) — **Ve.4 CLOSED — full self-compile
  fixed-point restored after 7 releases.** The v5.6.4-era
  blocker that broke `verify_fixed_point.sh` since v5.6.4 is
  closed; the full self-compile cycle now produces stage2.ll
  == stage3.ll within tolerance (NEAR FIXED POINT, 0.002%
  diff = VERSION metadata only). Root cause: `emit_index_get`
  / `emit_index_set` inline fast paths for i64/double/ptr
  element types emitted `getelementptr inbounds i64, ptr
  %data, i64 %idx` (a constant 8-byte stride), while
  `__mn_list_push` writes used the runtime `elem_size` field
  from the list struct (= 384 for the 7 Ve.2 residual
  `List<Int> = []` floor sites). Specifically `build_match_arms`
  allocated `indices` with `__mn_list_new(i64 384)`; the
  second push wrote 8 bytes of i64 + 376 bytes of stack
  spillage at byte offset 384, while the inline-GEP-i64 read
  at byte offset 8 returned the FIRST push's intra-buffer
  spillage (a heap-pointer-shaped Int garbage value).
  Caller's `set_block(s, garbage)` then made `emit_instr`'s
  `idx < len(fn_blocks)` bounds check silently no-op every
  instruction in the second match arm. `apply::match_arm2:
  block has no instructions` was the visible verifier error.
  **Fix**: 14 LOC across two symmetric emit sites
  (`emit_index_get` line ~2570, `emit_index_set` line
  ~2655) — load `list.elem_size` (struct field 3) at runtime,
  compute `offset = idx * elem_size`, then `getelementptr
  inbounds i8, ptr %data, i64 %offset`. SROA elides the
  runtime load when elem_size is a known constant; for the
  7 floor sites it correctly produces a 384-byte stride
  matching the push. **Hero metric**: `verify_fixed_point.sh`
  reaches NEAR (4 diff lines / 217,273 = 0.002%) for the
  first time since v5.6.4 — `mnc-stage2 mnc_all.mn` now
  produces non-empty stage3.ll byte-identical to stage2.ll
  (modulo VERSION). Reproducer (`/tmp/p3.mn`, 2-arm enum
  match) was 0 lines + verifier error; now 225 lines
  `llvm-as`-clean IR (binary correctly outputs `8` for
  `apply(Op::Add, 5, 3)`). **Investigation** followed
  v5.6.9's "eprint over culebra" lesson: 5 strategically
  -placed `__mn_str_eprint` traces inside `build_match_arms`
  and the optimizer pipeline isolated the failure mode in
  one rebuild cycle. The opt-time `ve4_dump_match_arms`
  helper showed `match_arm2 ninstrs=0` at p0-input
  (immediately after lowering) — ruled out all optimizer
  passes, focused investigation on the lower-time list
  construction. The build-end trace confirmed
  `indices[1]=garbage` was already corrupt inside
  `build_match_arms`. Per-iteration field-2 trace showed
  `s.current_block_idx=2` was correct right before the push
  but garbage immediately after — the bug was in the push,
  not the read. IR inspection of stage2.ll exposed the
  `__mn_list_new(i64 384)` allocation and the elem_size
  mismatch in the inline-GEP-i64 read pattern. **Per PROMPT
  D2** ("Fix at the precise location, not broadly"): the
  read-side fix is the smallest change that closes Ve.4
  without surfacing or closing Lk.1 (allocations remain at
  elem_size=384 for the 7 residual sites; only the
  read/write strides are made consistent). The principled
  fix (Ve.2 closure + Lk.1 closure + drop the floor
  entirely) is v6.0 borrow-checker scope. **Metrics**:
  stage2.ll **216,932 → 217,273 lines (+0.16%)**, well
  within the 3% PROMPT budget; `llvm-as` clean; goldens
  **64/66 preserved** (same 2 pre-existing fails: 51 B, 64
  Sh.7); ASan UAF **65 CLEAN / 0 ASAN_ERROR / 1
  CRASH_NO_ASAN**; valgrind **0 ERRORS / 66
  WARNINGS_ONLY**; LSan baseline gate **PASS** (no
  regressions vs v5.4.2 baseline; same 3 LEAKs as v5.6.10:
  39_gpu_detect, 40_gpu_tensor, 62_list_output);
  non-bootstrap pytest **5593 passed**, 116 skipped, 9
  xfailed; `make lint` clean; `check_struct_registry.py`
  23/23/91 clean. `known_issues.md` Ve.4 row flipped to
  CLOSED v5.6.11. The closeout arc completes:
  v5.6.5 (Ve.1) → v5.6.6 (Rt.04 RESCOPED) → v5.6.7 (Ve.2
  PARTIAL) → v5.6.8 (Ve.3 investigation) → v5.6.9 (Ve.3
  CLOSED; Ve.4 OPENED) → v5.6.10 (Ve.2 FURTHER PARTIAL +
  struct_byte_size + culebra; Lk.1 OPENED) → **v5.6.11
  (Ve.4 CLOSED; full self-compile fixed-point restored)**.
  All v5.6.x dockets resolved or appropriately deferred.
  Next: v5.7.0 (Sh.7 + B or-pattern → 66/66); v5.7.1
  (SPEC docs polish); v5.8.0 (RE-PANEL); v6.0 (borrow
  checker → Lk.1 + Rt.04). See
  `docs/roadmap/v5/v5.6.11/SESSION_REPORT.md`.
- **v5.6.10** (shipped) — **Self-host hardening — Ve.2
  partial closure 18 → 7 sites; struct_byte_size hardened;
  culebra baseline frozen; new Lk.1 opened.** Three bundled
  hardening items closing the v5.6.x arc. **Ve.2 residuals**:
  `lower_assign_list_hint(st, target, value)` ports v5.6.7's
  `lower_let_list_hint` pattern to assignment, threading the
  variable's alloca elem_ty into `lower_list_typed` for
  `xs = []` reassignments — closes 10 sites in `register_struct`
  ×3, `register_enum` ×2, `try_monomorphize_struct` ×3,
  `try_monomorphize_enum` ×2. Plus 1 site closed via a typed
  `let empty_extras: List<Expr> = []` binding in `lower_pipe`'s
  `ident` arm. Net 11 sites closed; 7 remain (`List<Int>`
  empty-let bodies in 6 functions). An `emit_list_init` scalar
  gate (use `llvm_type_size` directly when `elem_ty.kind !=
  TK_UNKNOWN()`) was attempted to close all 7 residuals but
  REVERTED after surfacing **Lk.1** (alloca-aliasing leak in
  inline list-get/push pattern): drop-glue tracks the ListInit
  destination alloca (`%t0.addr`) but mutating pushes write
  back to a separate var-binding alloca (`%arr1.addr`); at
  function exit, `__mn_list_free(ptr %t0.addr)` is a no-op
  while the buffer at `%arr1.addr` is never freed. The same
  code path was present at v5.6.9 baseline but masked by the
  384-byte floor — at elem_size=384 the buffer is 3088 B and
  LSan's "still reachable" heuristic finds a stack pointer
  aliasing into the larger region; at elem_size=8 the 80-B
  buffer escapes that aliasing and the leak surfaces. Lk.1 is
  same shape as Rt.04 (multi-level alias); fix needs
  alloca-aliasing tracking in drop-glue, not a sizing change
  — v6.0 borrow-checker scope. **`struct_byte_size` patch**:
  re-applies v5.6.8's deferred patch (1-LOC body change to
  `return llvm_sizeof_st(st, ty)`) now that Ve.3 is closed.
  Replaces the legacy `llvm_aggregate_size(entry.llvm_type)`
  walk — which counts ALL commas including those inside nested
  aggregates like `{ptr, i64}` — with the v5.6.5-introduced
  recursive resolver that uses `lookup_struct_field_types`
  (skipping empty-fields stub entries from
  `register_internal_struct`) and 8-byte aligns each field.
  Result: correct sizes (Value 24 → 80; MIRType 24 → 64;
  EmitState 152 → 752). Downstream `use_sret_return` and
  `is_byref_type_st` now classify functions correctly — more
  functions with > 16-byte returns switch to sret. stage2.ll
  grows 201,743 → 216,932 lines (+7.46%, within the v5.6.10
  PROMPT 8% budget); growth driver is more sret prologues +
  post-call extracts, not real complexity. Per PROMPT D2 the
  patch is gated on full sanitizer + golden + fixed-point
  gates passing post-Ve.3 — verified clean (initial Phase 2
  run flagged LSan regression but was actually the scalar
  gate, not struct_byte_size; re-applied post-revert showed
  all gates green). **Culebra baseline frozen**: 5 root
  causes, 15755 findings, 2 critical (`function-count-drop`=941,
  `return-type-divergence`=37) — same critical pattern as
  v5.6.9 (940 + 37). No NEW critical findings (PROMPT exit
  criterion #13 met). The +4340 finding delta vs v5.6.9
  reflects stage2.ll's +7.5% growth — text-pattern templates
  match more text in a larger IR, not real regressions.
  Artifacts at `docs/roadmap/v5/v5.6.10/culebra/` (triage,
  progress, compare, audit, strings, check, baseline-delta);
  journal at `docs/roadmap/v5/v5.6.10/culebra-journal.jsonl`
  with 5 milestone entries. Metrics: stage2.ll 216,932 lines
  / `llvm-as` clean; goldens **64/66 preserved** (same 2
  pre-existing fails: 51 B, 64 Sh.7); ASan UAF 65 CLEAN /
  0 ASAN_ERROR / 1 CRASH_NO_ASAN; valgrind 0 ERRORS /
  66 WARNINGS_ONLY; LSan baseline gate **PASS** (no
  regressions vs v5.4.2 baseline; 50 CLEAN / 3 LEAK = same
  39_gpu_detect, 40_gpu_tensor, 62_list_output as v5.6.9);
  non-bootstrap pytest **5590 passed**, 116 skipped, 9
  xfailed; `make lint` clean; `check_struct_registry.py`
  23/23/91 clean. `known_issues.md` Ve.2 row updated to
  PARTIAL v5.6.10 with Lk.1 dependency; new Lk.1 row added.
  PROMPT directive followed: "if any sanitizer regresses,
  REVERT" (the scalar gate was reverted; the
  `lower_assign_list_hint` and `lower_pipe` fixes shipped
  clean). The closeout arc v5.6.5 (Ve.1) → v5.6.6 (Rt.04
  RESCOPED) → v5.6.7 (Ve.2 PARTIAL) → v5.6.8 (Ve.3
  investigation) → v5.6.9 (Ve.3 CLOSED; Ve.4 OPENED) →
  **v5.6.10 (Ve.2 FURTHER PARTIAL + struct_byte_size +
  culebra)** continues with v5.6.11 (Ve.4 close); v5.7.0
  (Sh.7 + B or-pattern → 66/66); v5.7.1 (SPEC docs polish);
  v5.8.0 (RE-PANEL); v6.0 (borrow checker → Lk.1 + Rt.04).
  See `docs/roadmap/v5/v5.6.10/SESSION_REPORT.md` for the
  full trace, including the Lk.1 investigation and the
  Phase 1B revert decision.
- **v5.6.9** (shipped) — **Ve.3 ROOT CAUSE CLOSED; new
  Ve.4 opened.** Closes the v5.6.4-era stage2 runtime
  OOM/SIGSEGV at its source: `emit_drop_glue` for `List<Enum>`
  returns unconditionally freed every tracked heap-boxed
  payload via `@free(ptr)`, leaving dangling pointers in the
  returned list. `mir_opt::clone_instr_for_inline` returns
  `List<Instruction>` where Instruction is `%enum.Instruction
  = type {i64, ptr}` — `{tag, heap_box_ptr}` pairs whose
  payload_ptr IS one of the freed boxes. The single-level
  alias check in `drop_glue_boxed` compares against
  `ret_box_ptrs` (empty for list returns), so all boxes get
  freed. Caller dereferences dangling payloads via
  `instr_dest(inst)` and reads garbage Value names →
  `__mn_str_concat → llvm_alloca → __mn_alloc(garbage_size)`
  OOM. v5.6.8's "third Alloca" finding was the first
  inliner-cloned Alloca (`%_inl0_2_a.addr` from `add()`
  inlined into `main()`). Direct-lowerer Allocas returned via
  LowerState (a struct, conservatively skipped by
  `ret_ty_is_aggregate`) survived; inliner-cloned ones
  returned via `clone_instr_for_inline`'s List<Instruction>
  didn't. Same multi-level aliasing class as v5.6.6 Rt.04
  (List<String> nested in returned struct, 2 levels deep);
  fix matches v5.6.6's RESCOPE pattern — 25 LOC in
  `emit_llvm.mn:4763`: skip drops conservatively when
  `ret_ty == llvm_list_rt() && len(boxed_owned) > 0`. Cost:
  intermediate boxes NOT in returned list leak; accepted per
  v5.6.6 precedent (UAF prevention > leak prevention).
  Multi-level alias analysis is v6.0 borrow-checker scope.
  **Verification on reproducer**: `mnc-stage2 /tmp/p1.mn` was
  0-line OOM since v5.6.4 → now **215 lines `llvm-as` clean
  RC=0**. Trace instrumented at 4 points
  (`lower.mn::bind_fn_params`,
  `mir_opt::clone_instr_for_inline` Alloca branch,
  `emit_mir_by_kind` dispatch, `emit_alloca`) confirmed
  corruption first appears between clone_inst's push and
  dispatch's `instr_dest(inst)` read — incompatible with the
  v5.6.8 PLAN's hypotheses E (rename_value bug) or F (Value
  layout divergence). Hypothesis G (noalias on byref) hand-
  patched independently and ruled out (still OOMs with same
  signature). The fix path was identified by inspecting
  `clone_instr_for_inline`'s exit IR in stage2.ll — 48 calls
  to `@free(ptr)` with no `icmp eq ptr` aliasing checks.
  **What v5.6.9 does NOT close**: full self-compile fixed-
  point. `mnc-stage2 mnc_all.mn` segfaults at a stack address
  under default 8 MB stack; with `ulimit -s unlimited` the
  MIR verifier surfaces a SEPARATE pre-existing bug — empty
  BasicBlocks in match-arm lowering of the self-hosted
  compiled compiler, e.g. `expr_kind::match_arm2: block has
  no instructions`. Reproduces on the **original v5.6.8
  binary** with the same error on a 2-arm match test program
  — confirming v5.6.8's mnc_all.mn SIGSEGV was THIS bug
  surfacing as stack overflow, not Ve.3 itself. Goldens
  never tested stage2 binary on user code, so this stayed
  latent for releases. Tracked as new **Ve.4** in
  `docs/known_issues.md` for v5.6.10. Hypothesis: an MIR
  pass post-lowering (likely `dead_block_elim_function` or
  interaction with `inline_small_functions`) drops
  instructions from match arms whose body is a single tail
  expression. Broadening the v5.6.9 Ve.3 fix to also gate on
  `len(str_owned) > 0` reproduces the SAME match-arm error
  on programs as small as a 2-arm enum match — Ve.4 is
  independent of the fix's breadth. **Culebra honest
  assessment**: PLAN scoped culebra as primary diagnostic.
  In practice culebra v2.4.0 (a Windows PE32+ binary running
  through WSL interop) needed Windows-style paths (initial
  WSL-style paths hung silently for several minutes),
  `triage --brief` took **7m37s** on 207k-line stage2.ll
  (the `summary` subcommand never completed in 5+ minutes),
  and the loud `return-type-divergence` signal class (37
  critical hits) was a false positive flagging all
  aggregate-return runtime declarations (`__mn_str_concat`,
  `__mn_str_substr`, `__mn_list_new`, etc.) as if
  cross-stage divergent. The actual root cause was found via
  `__mn_str_eprint` instrumentation across 4 points + one
  `should_inline → return false` confirmation — total
  ~8 min including builds. Culebra's contribution:
  confirmed `function-count-drop` (940 hits) and
  `return-type-divergence` (37 hits) signal classes existed;
  let me skip Hypothesis F's deep investigation. v5.6.10+
  recommendations in SESSION_REPORT §Culebra: build a
  Linux-native binary; profile `triage` on 200k+ line IR;
  narrow the `return-type-divergence` template to confirmed
  cross-stage mismatches; add a drop-glue/lifetime template
  class. Metrics: stage2.ll **207,619 → 201,743 lines
  (−2.83%)**, `llvm-as` clean (reduction comes from skipping
  ~5,876 lines of drop-glue extracts/free calls in ~12
  list-returning functions); `mnc-stage1` 6,270,112 bytes
  identical strip-pruned size; goldens **64/66 preserved**
  (same 2 fails: 51_match_guards_and_or B + 64_closure_typed
  Sh.7); ASan UAF sweep 0 errors / 65 CLEAN / 1
  CRASH_NO_ASAN baseline; valgrind 0 errors / 66
  WARNINGS_ONLY; LSan baseline gate PASS (no leak
  regressions, 62_list_output unchanged at 9 / 141 B per
  Rt.04 v5.6.6 RESCOPE); non-bootstrap pytest 5584 passed;
  `make lint` clean; `check_struct_registry.py` 23/23/91
  clean. `known_issues.md` Ve.3 row → CLOSED v5.6.9; Ve.4
  row added. The closeout arc v5.6.5 (Ve.1) → v5.6.6 (Rt.04
  RESCOPED) → v5.6.7 (Ve.2 PARTIAL) → v5.6.8 (Ve.3
  investigation) → **v5.6.9 (Ve.3 CLOSED; Ve.4 OPENED)**
  continues with v5.6.10 (Ve.4 close + revisit
  struct_byte_size patch); v5.7.0 (Sh.7 + B or-pattern →
  66/66); v5.7.1 (SPEC docs polish); v5.8.0 (RE-PANEL).
  See `docs/roadmap/v5/v5.6.9/SESSION_REPORT.md` for the
  full trace, hypothesis matrix, and culebra retrospective.
- **v5.6.8** (shipped) — **Ve.3 INVESTIGATION-ONLY — stage2
  runtime OOM hypothesis space narrowed; bug NOT closed.**
  Documentation/investigation release; source code unchanged
  vs v5.6.7. The PLAN scoped Ve.3 closure for v5.6.8;
  empirical work showed the bug is deeper than the four
  enumerated hypotheses. **What was found:** `mnc-stage2`
  OOMs in `__mn_str_concat ← llvm_alloca ← emit_mir_by_kind`
  on the **third** `Instruction::Alloca` emitted for `p1.mn`
  — the first two (param slots `%a.addr`/`%b.addr` for `add`'s
  parameters) emit correctly; the third's `dest.name`
  (Value's field 0) is read as uninitialised memory while
  `dest.ty` (field 1, kind=TK_INT, name="Int") reads correctly
  on all three calls. `len(dest.name)` returns
  non-deterministic huge values across runs. Hypothesis A
  (payload-type builder divergence) ruled out by IR
  inspection — both `build_payload_type_from_values` and
  `build_payload_type_from_variant` produce
  `{ %struct.Value, %struct.MIRType }` for `Instruction::Alloca`.
  Hypothesis D (Python emitter bug) ruled out by
  `mnc-stage1-fromself` reproducing the OOM. **Adjacent finding:**
  `struct_byte_size` undercounts `%struct.Value` at 24 bytes (true
  size 80) — `llvm_aggregate_size` counts ALL commas in the inline
  llvm_type, including those inside nested aggregates, AND
  `register_internal_struct` pushes stub entries with
  llvm_type="%struct.X" (named form) that the forward search
  finds first. An experimental patch (delegate `struct_byte_size`
  to `llvm_sizeof_st`, which uses `lookup_struct_field_types`'s
  recursive resolution) gives correct sizes (Value→80, MIRType→64,
  EmitState→752) and triggers sret/byref correctly. With patch:
  stage2.ll grew 207,619 → 222,628 lines (+7.2%), llvm-as clean,
  goldens 64/66 preserved — but **dest.name is still corrupt on
  the third call, OOM persists**. Patch reverted; bug unrelated
  to ABI sizing. **Adjacent divergence noted but not load-bearing:**
  Python's emit_llvm_text.py adds `noalias` to byref struct
  parameters (`ptr noalias %dest.byref`); the self-hosted emitter
  does not. Pre-existing pattern, not a v5.6.x regression — but
  candidate to revisit if other v5.6.9+ paths fail. Active
  hypothesis for v5.6.9+: the inliner
  (`mir_opt::clone_instr_for_inline`'s Alloca branch) or lowerer
  produces the third Alloca with corrupt dest.name; OR Value's
  field-0 boundary in stage1-emitted IR has a layout interaction
  (named vs inline aggregate types, missing noalias) that the
  Python emitter avoids. Per "no cheap shit" directive: shipping
  the partial struct_byte_size fix would inflate stage2.ll 7%
  for no observable benefit and obscure the v5.6.9+ debugging
  surface. Metrics: `mnc-stage1` 6,270,128 bytes (rebuilt from
  unchanged source, identical to v5.6.7 strip-pruned size);
  stage2.ll 207,619 lines (no change vs v5.6.7); goldens 64/66
  preserved; `make lint` clean; `check_struct_registry.py`
  23/23/91 clean; valgrind/ASan/LSan baselines unchanged (no
  source changes to gate). Ve.3 row in `docs/known_issues.md`
  updated with full hypothesis matrix; Track field bumped to
  v5.6.9+. See `docs/roadmap/v5/v5.6.8/SESSION_REPORT.md` for
  the full investigation log including reproducer trace, gdb
  + asan + eprint instrumentation outputs, and per-hypothesis
  rule-out evidence. Pattern follows v5.6.6's "Rt.04 attempted
  + RESCOPED" — honest scoping over premature closure. What
  ships: VERSION bump + investigation docs + this CLAUDE.md
  entry. What does NOT ship: Ve.3 fix; non-empty stage3.ll;
  the experimental struct_byte_size patch.
- **v5.6.6** (shipped — post-v5.6.7 in git history; holds its
  planned slot in the version sequence) — **Rt.04 attempted +
  RESCOPED — single-level walk insufficient.** Empirically
  verifies that closing the 62_list_output leak (9 objs / 141 B)
  via a one-level `%struct.*` field walk is impossible: the
  resource lives at struct→list→string (depth 2), and the walk
  only sees depth 1. ASan reproduces a heap-use-after-free at
  every gate threshold attempted: N=8/M=50 (+10.3% stage2.ll
  growth, over PLAN's 3% budget); N=4/M=20 (+3.67%); N=4/M=10
  (+2.39%, under budget but UAF is real). Drop glue extracts the
  returned `List<String>` field as a list-alias but doesn't
  descend into the list to alias its String elements; the
  separately-tracked String slots whose data lives inside that
  list get freed prematurely → caller's `__mn_str_join` reads
  freed memory. Confirmed by ASan with full stack:
  `__mn_str_free → emit_drop_glue_strings`, then
  `memcpy → __mn_str_join → main`. The PLAN expected `St`'s 2
  fields to pass any gate above 2 — it did, but the leak's
  resource is at depth 2 inside that struct, not at the struct
  level. **What ships:** the `ret_ty_is_aggregate(ret_ty) →
  ret_ty_is_aggregate(st, ret_ty)` signature change, plumbing
  state through the one call site; gate body reverts to v5.4.4's
  conservative skip after empirical UAF verification at all three
  thresholds. **What does NOT ship:** 62_list_output leak fix
  (stays 9 objs / 141 B, baseline-gated); multi-level walk (v6.0
  borrow-checker scope); the actual gate logic. Metrics:
  stage2.ll 207,619 lines (effectively unchanged vs v5.6.7's
  207,616, 0% growth); `llvm-as` clean; goldens 64/66 preserved;
  `make lint` clean; `check_struct_registry.py` 23/23/91; ASan on
  `mnc_all.mn` 0 heap-buffer-overflow. Honest scoping per user
  "no cheap shit" directive — a UAF would be much worse than a
  documented leak. The v5.4.4 → v5.6.6 history shows the cost of
  single-level alias analysis on a language with non-refcounted
  leaf strings; the structural answer is ownership at the type
  level (borrow checker), scoped to v6.0. See
  `docs/roadmap/v5/v5.6.6/SESSION_REPORT.md`.
- **v5.6.7** (shipped) — **Ve.2 PARTIAL — lowerer empty-list
  elem_ty propagation + list_init dispatch fix.** Empty-list
  element type now propagates from `let` annotations: `let xs:
  List<String> = []` produces MIR with
  `elem_ty.kind=TK_STRUCT / name=String` instead of `TK_UNKNOWN
  / ""`. New `lower_list_typed(st, elements, hint)` helper
  accepts an explicit element-type hint; `lower_list` becomes a
  one-line wrapper delegating with `mir_unknown()` for backward
  compatibility. New `extract_list_elem_ty(st, te)` unwraps
  `Generic("List", [inner])` → inner MIRType; new
  `lower_let_list_hint(st, value, type_ann)` gates the pattern
  check. `lower_let` routes through `lower_list_typed` when the
  pattern matches — otherwise falls through to the generic
  `lower_expr` path. **Key collateral fix**:
  `emit_list_init_checked`'s struct-reinterpretation heuristic
  misfired on correctly-typed `List<Struct>` literals — when
  elem_ty.name matched a registered struct name, the heuristic
  dropped the ListInit and emitted a broken struct_init instead,
  leaving `%tN` undefined at every use site (`llvm-as` rejected
  with "use of undefined value"). Short-circuited when
  `dest.ty.kind == TK_LIST()` — the destination is definitively
  a list, so the struct-init path doesn't apply. Metrics:
  **`__mn_list_new(i64 384)` hardcoded fallback 387 → 18 sites
  (−95%)**; dynamic GEP-trick sizing 49 → ~400 sites (+8×);
  stage2.ll 207,616 lines (+0.28% vs v5.6.5, well within
  budget); `llvm-as` clean; goldens 64/66 preserved; ASan on
  full `mnc_all.mn` reports 0 heap-buffer-overflow; `make lint`
  clean; `check_struct_registry.py` 23/23/91 clean. **What NOT
  closed** — non-empty stage3.ll. The stage2 runtime OOM
  symptom (`__mn_str_concat` in `llvm_alloca` receives a
  garbage-length String) persists, same failure mode as v5.6.5
  but with narrower blast radius (only lists not routed through
  `lower_let` still hit the 384 floor). Tracked as new **Ve.3**
  in `docs/known_issues.md`; scoped for v5.6.8. Residual 18 ×
  384-byte floor sites come from empty-list literals in
  contexts that don't route through `lower_let` (struct field
  defaults, call arguments, return expressions) — v5.6.9+ scope
  after Ve.3 closure. See
  `docs/roadmap/v5/v5.6.7/SESSION_REPORT.md`.
- **v5.6.5** (shipped) — **Ve.1 primary fix + GEP-trick sizing
  refactor.** Root-causes the `parse_fn_body` heap-buffer-overflow
  (open since v5.4.4) NOT to the parser but to
  `llvm_type_size`'s hardcoded `256`-byte fallback for any
  `%struct.*` type. `FnDefData` is 264 bytes; every
  `Definition::FnDef(fd)` boxing overflowed by 8. Rather than patch
  FnDefData alone, this release rewrites the emission pipeline to
  defer ABI computation to LLVM's DataLayout via the GEP-trick
  (`ptrtoint ptr getelementptr (%T, ptr null, i32 1) to i64`) + typed
  field GEPs — the pattern Clang uses for opaque-size emission
  (see LLVM LangRef "Getelementptr", rustc `struct_gep`). Matches
  Python's `_do_enum_init` at `emit_llvm_text.py:4770-4809`.
  `emit_enum_init` + `emit_enum_payload` rewritten to build inline
  payload struct types and use typed GEPs for field offsets — LLVM
  computes both sizes and offsets at link time, no hand-rolled
  sizing. Two new helpers: `build_payload_type_from_values(st,
  payload)` and `build_payload_type_from_variant(st, enum_name,
  variant_name)`. Also fixes `lookup_struct_field_types` to skip
  empty `register_internal_struct` entries (which were shadowing
  real MIR entries for Value, MIRType, EmitState, LowerState — my
  original investigation thought these were the root cause but they
  turned out to be a separate, compounding bug). Adds new
  state-aware `llvm_sizeof_st(st, ty)` as a recursive registry-
  resolving size calculator for non-GEP fallback paths
  (`compute_payload_alloc_size`, `compute_field_offset`,
  `sum_field_sizes`, `compute_variant_field_offset`).
  `emit_list_init` gets a hybrid: GEP-trick for known element types
  (`%struct.*`, `%enum.*`, `{...}`), 384-byte floor for
  unknown/scalar. Metrics: stage2.ll **435 hardcoded malloc sites →
  2** (99.5% elimination); 72 dynamic GEP-trick sites → 505 (+7×);
  stage2.ll 207,039 lines (+0.78% vs v5.6.4's 205,446, within ±1%
  budget); `llvm-as` clean; goldens 64/66 preserved; ASan on full
  `mnc_all.mn` reports **0 heap-buffer-overflow errors** (was
  154,355 errors / 42 contexts at v5.6.4). `make lint` clean;
  `check_struct_registry.py` 23/23/91 clean; non-bootstrap pytest
  clean. Research-backed: reviewed LLVM DataLayout docs,
  `rustc_codegen_llvm/src/builder.rs` (struct_gep), Clang
  `ASTContext::getTypeInfoImpl`, Go `cmd/compile/internal/types/size.go`
  — the GEP-trick is the idiomatic choice for self-hosting
  compilers without their own layout engine. **What's NOT closed
  this release:** non-empty stage3.ll. Removing the 384-byte list
  floor exposed a pre-existing lowerer bug — `let xs: List<String>
  = []` lowers to MIR with `elem_ty.kind=TK_UNKNOWN`, which
  `resolve_mir_type` maps to `"i64"` → lists allocated with 8-byte
  element slots instead of the type's actual size. The 384-byte
  floor had been masking this across Span/Block/String/Param/
  Decorator/Stmt/FnDefData lists since v4.x (at ~24× memory
  overhead). **Tracked as new Ve.2 in `docs/known_issues.md`;
  scheduled for v5.6.7** as a focused lowerer-side fix (~1 session).
  After v5.6.7 lands, the 384 floor can be removed and the fixed-
  point test should produce non-empty stage3.ll. What NOT shipped:
  Ve.2 fix (deferred to v5.6.7 by user approval); Rt.04 work
  (still v5.6.6); Sh.7 (still v5.7.0). See
  `docs/roadmap/v5/v5.6.5/SESSION_REPORT.md`.
- **v5.6.4** (shipped) — **Own.1 Phase 3 — Rt.06 tensor drop-glue
  CLOSED.** Ports Python's `_tensor_vars` / `_emit_drop_glue_tensors`
  pair to the self-hosted emitter. Two new `EmitState` fields
  (`tensor_owned: List<String>` + `tensor_owned_source: List<String>`)
  parallel to the existing str/list/boxed triples — field-list
  parity gate clean at 23/23/91 (no new struct, `EmitState` +2
  fields). `emit_track_tensor` helper structurally parallel to
  `emit_track_boxed`: entry-block prelude slot alloca + null zero-
  init, store of tensor ptr post-alloc-emit, push onto
  `tensor_owned` / `_source` lists. Loop-depth free-before-store
  branch (v5.4.3 parity): when `st.loop_depth > 0`, prepend
  `load ptr, slot` + `call void @__mn_tensor_free(ptr %prev.tens.N)`
  before the store. Load-bearing for `53_linear_regression`'s 10-
  epoch loop × ~4 fresh tensors per iteration — without the pre-
  store free, 40+ tensors leak per run even with drop-glue at
  return. Null-tolerant `__mn_tensor_free` in C runtime
  (`if (!t) return`) makes first-iter a no-op. Dispatch: new
  `is_tensor_allocating_fn(fn_name)` predicate enumerating 22
  runtime fns (1 alloc + 1 slice + 8 broadcast +/- */÷ × f64/i64
  + 8 scalar + 4 reverse-scalar rsub/rdiv × f64/i64). Design call
  (PLAN §D2): post-emit injection in the generic
  `emit_mir_call` `Some(fe)` + `_` success branches, guarded on
  the predicate — v5.6.2 shipped correct IR for all 20 binop fns
  via the generic `find_function` + `emit_call_ir` path, so
  adding 20 dedicated branches (~160 LOC) just to attach a
  tracking call would duplicate validated emit logic. Direct
  injection at the two special-case sites: `emit_tensor_init`
  after the `__mn_tensor_alloc` emit line, and the
  `__mn_tensor_slice` branch (v5.6.3) after its final emit line.
  `emit_drop_glue_tensors(st, ret_tensor_ptrs)` helper
  structurally parallel to `emit_drop_glue_boxed`: `ptr` slot
  type, SSA prefix `t` (`%drop.tv.N` / `drop.tfree.N` /
  `drop.tskip.N` / `%drop.tmacc.N` / `%drop.tsame.N.K`), free fn
  `__mn_tensor_free`, shared `emit_or_reduce_ret_match` with
  `prefix="t"`. `emit_drop_glue_destroy` (v5.5.7 async cleanup)
  extended with a fourth unconditional tensor loop — SSA prefix
  `%drop.d.t.N` distinct from normal-exit siblings and
  destroy-path `%drop.d.{s,l,b}.N`. `emit_drop_glue` dispatcher:
  fast-path guard at `:4445` extended to include `len(tensor_owned)`;
  fourth `ret_tensor_ptrs: List<String>` list at `:4462`; dual-
  push at the two ptr escape sites (scalar ptr return and
  `%struct.*` one-level ptr-field walk) pushes the same SSA into
  both `ret_box_ptrs` and `ret_tensor_ptrs` — each per-resource
  helper alias-checks its own slot list, so the over-approximation
  is symmetric and safe (PLAN §D4): a tensor ret-val legitimately
  in both lists short-circuits both drops on the matching helper
  and the non-matching helper's slot list doesn't alias the ptr
  anyway, so no missed-free. Symmetric for boxed returns. Tail
  `s = emit_drop_glue_tensors(s, ret_tensor_ptrs)` after the
  existing boxed helper. Per-site verification on golden 52: 24
  tens_track slots, 6 `__mn_tensor_free` calls; golden 53: 28
  tens_track, 10 frees, 8 `prev.tens.*` loads inside the epoch
  loop. All 5 tensor goldens produce byte-identical v5.6.3
  output — track/free ratio ~1:4 because most slots get consumed
  inline (literals stored into list elements; binop intermediates
  immediately fed into the next binop). LSan sweep 50 CLEAN / 3
  LEAK (baseline) / 1 COMPILE_FAIL / 12 LINK_FAIL / 0 regressions
  — all 5 tensor goldens report 0 objs / 0 B. Baseline TSV at
  `docs/roadmap/v5/v5.4.2/baseline/asan-leak-baseline.tsv` flipped
  49/50/51/52/53 from COMPILE_FAIL-era to CLEAN, tightening the
  gate from "these goldens may leak" to "no tensor may leak at
  function exit." 39_gpu_detect / 40_gpu_tensor baseline refreshed
  from 3/49655 → 5/50212 to absorb WSL libvulkan.so.1 version
  drift (all 5 leak frames in libcuda / libvulkan, zero Mapanare
  code — environmental, orthogonal to Rt.06). Harness 64/66
  preserved (same 2 fails as v5.6.3: 51_match_guards_and_or B,
  64_closure_typed Sh.7). stage2.ll 205,446 lines (+1,148 vs
  v5.6.3's 204,298, +0.56% — well under the 2% PLAN §R3 budget)
  / 934 defines (+3: the three new helpers). llvm-as clean.
  Self-hosting preserved — mnc_all.mn has zero tensor calls, so
  the 4 new emit sites don't fire during stage2 emission but the
  12 runtime decls from v5.6.3 still get emitted plus the new
  tracking slots for the 3 new fns cost nothing. Valgrind 66
  WARNINGS_ONLY / 0 ERRORS preserved. ASan UAF 60 CLEAN / 6
  CRASH_NO_ASAN / 0 ASAN_ERROR preserved (same 6 bootstrap-
  C-backend failures on tensor builtins, orthogonal to LLVM path).
  Ve.1 persists (pre-existing from v5.4.4 — stage2 still segfaults
  compiling mnc_all.mn; same signature; not a v5.6.4 regression).
  Non-bootstrap pytest clean; `make lint` clean;
  `check_struct_registry.py` 23/23/91 clean. `known_issues.md`
  Rt.06 row flipped to **CLOSED v5.6.4**. `PARITY_GAPS.md` adds
  Own.1 Phase 3 row under memory-safety residuals. What NOT
  shipped: tensor move-on-assign (v6.0 borrow-checker); inter-
  procedural tensor-lifetime analysis; Ve.1 fix. What's next:
  v5.6.5+ close Rt.04 + diagnose Ve.1; v5.7.0 Sh.7 closure + B
  or-pattern → 66/66; v5.7.1 SPEC docs polish; v5.8.0 RE-PANEL.
  See `docs/roadmap/v5/v5.6.4/SESSION_REPORT.md`.
- **v5.6.3** (shipped) — **Sh.6 Phase 4 — tensor slicing +
  reductions; Sh.6 CLOSED.** Final Sh.6 release. Closes
  `52_tensor_slicing` end-to-end (first time the golden actually
  runs byte-identical to the expected output — it was previously
  a parse-error FAIL because `_` lexed as `NAME` and `a[0..2, _]`
  produced `error: Undefined variable '_'`) and promotes
  `53_linear_regression` from PASS-by-function-match to truly
  runtime-correct (`.sum()` on a tensor previously routed to a
  generic `call i64 @sum(ptr)` with `llvm-as` rejecting the i64-
  vs-double type mismatch at `%t47 = fmul double %t45, %t46`).
  Lexer: `keyword_token_type` in `lexer.mn:186` gains
  `if name == "_" { return "UNDERSCORE" }` — one-line change;
  `_foo` / `__bar` / `_1` keep their NAME token type since
  `scan_ident` collects `[_a-zA-Z0-9]+` and the check is exact-
  match. Consumer sites need zero edits — `parse_let_stmt` (1449),
  `parse_for_stmt` (1488), `parse_pattern_alt` (2126) all use
  `peek_value` which returns the string `"_"` regardless of token
  type, so throwaway bindings / wildcard patterns continue to
  parse. AST: new `IndexItem { kind: String, expr: Expr, start:
  Expr, end: Expr }` struct (kind ∈ scalar/range/wildcard; NoneLit
  marks unused fields), three constructors, and new
  `Expr::TensorSlice(Expr, List<IndexItem>)` variant with
  `expr_slice_obj` / `expr_slice_items` accessors. Parser: new
  `parse_index_item` helper in `parser.mn` classifies each
  subscript item with `parse_expr` invoked at `min_prec=7` so the
  binop loop's `..` handler (prec 6) short-circuits and we
  classify the item ourselves. 4 forms: UNDERSCORE → wildcard;
  RANGE prefix → `NoneLit..end`; expression with trailing RANGE →
  `start..` (if COMMA/RBRACKET next) or `start..end`; else scalar.
  LBRACKET branch in `parse_postfix` rewritten: items → `Expr::Index`
  (1 scalar) / `Expr::TensorIndex` (≥2 scalars) / `Expr::TensorSlice`
  (any non-scalar). 11 parser tests in
  `tests/parser/test_tensor_slice_wildcard.py`. Semantic:
  `infer_expr` gains a `"tensor_slice"` arm — walks items for
  diagnostic emission; result type is `sl_obj_r.type_info`
  (Tensor<T> preserved — rank tracking is a runtime concern).
  **Gotcha caught during rebuild:** initial loop variable `si`
  collided with the Spanish `si` keyword (lexer.mn:141 returns
  KW_IF); Python bootstrap parser saw `if si < n_items` as `if if
  < n_items`. Renamed to `sl_i` — `si` remains a valid if-keyword.
  Lower: three new helpers next to `tensor_elem_kind_of`
  (`lower.mn:2811`) — `is_tensor_reduction_method` (6-string lookup
  over sum/mean/max/min/argmax/argmin), `tensor_reduction_ret_ty`
  (argmax/argmin → Int, mean → Float always, sum/max/min → element-
  aware), `lower_tensor_slice` (~100 LOC: per-item start/end build;
  wildcard → `[0, tensor_shape_dim(obj, d)]`; scalar → `[k, k+1]`
  via BinOp::Add). `lower_method_call` gains reduction dispatch
  prepended after the `push` special case: guards on
  `obj.ty.kind == TK_TENSOR()`, builds
  `__mn_tensor_{method}_{f64,i64}`, forces `_f64` for mean.
  `lower_expr` routes `"tensor_slice"` to `lower_tensor_slice`.
  Flat-arg layout for slice: `[obj, s0, s1, ..., e0, e1, ..., rank]`
  matches Python's `lower.py::_lower_tensor_slice:2788-2835`. Emit:
  12 new `declare_runtime_fn` calls in `declare_all_runtime` — 11
  reductions + `__mn_tensor_slice` (`ptr, ptr, ptr, i64`). Reduction
  `get_fn_attrs` rows are `" nounwind readonly"` (pure over tensor
  data); slice is `" nounwind"` + `"noalias "` return-prefix (fresh
  heap). `emit_mir_call` special-case for `__mn_tensor_slice`
  (inserted before `__mn_tensor_set_i64_nd` block) unpacks the flat-
  arg layout into two `[ndim × i64]` allocas via gep+store, then
  emits `call noalias ptr @__mn_tensor_slice(ptr tensor, ptr
  starts_arr, ptr ends_arr, i64 rank)` — byte-identical to
  `emit_llvm_text.py:3669-3717`. `__mn_tensor_shape_dim` already
  declared at line 679 (v5.6.0). All 6 reduction fns +
  `__mn_tensor_slice` ship in
  `runtime/native/mapanare_gpu_builtins.c:647-753`; no runtime
  edits. Harness: 63/66 → **64/66** (52 closes; 53 was already
  PASS-by-function-match, now also runtime-correct). **Sh.6 now
  completely closed** — all 5 tensor goldens (49 literal, 50
  indexing, 51 broadcast, 52 slicing, 53 linear regression) run
  byte-identical to expected output. Golden 52 output: `15 3 5 1 4
  0 60 30 1 2 20 30 2 6`. Golden 53 output: `w = 1.96879 / b =
  0.560177 / converging` matches `w = <approaching 2.0>` / `b =
  <approaching 1.0>` / `converging`. stage2.ll 204,298 lines
  (+1.42% vs v5.6.2) / 931 defines (+11), `llvm-as` clean, self-
  hosting preserved (mnc_all.mn doesn't use the slice/reduction
  paths, so the 12 decls are emitted unconditionally but no call
  sites fire during stage2 emission). Non-bootstrap pytest 5564
  passed (+14 vs v5.6.2 — 11 new parser tests plus collateral from
  the VERSION macro bump); `make lint` clean;
  `check_struct_registry.py` 23/23/91 (+2 vs v5.6.2's 89 —
  `IndexItem` + `IndexItemResult`). ASan 0 ASAN_ERROR / 60 CLEAN /
  6 CRASH_NO_ASAN (same 6 as v5.6.2 — Python-bootstrap C-backend
  compile failures on tensor builtins, orthogonal to LLVM path).
  Ve.1 stage3 segfault persists (pre-existing from v5.4.4, not a
  v5.6.3 regression). Rt.06 tensor drop-glue gap now formally
  covers goldens 49/50/51/**52**/53 — emit_track_tensor hook
  remains v5.6.4+ scope. PARITY_GAPS.md: Sh.6 row flipped to
  CLOSED with v5.6.3 closure reference. known_issues.md: Sh.6 row
  also marked CLOSED v5.6.3. What's next: v5.6.4+ Rt.06 drop-
  glue, v5.7.0 Sh.7 closure + B or-pattern (closes 51/64 for
  66/66), v5.7.1 SPEC docs polish, v5.8.0 RE-PANEL. See
  `docs/roadmap/v5/v5.6.3/SESSION_REPORT.md`.
- **v5.6.2** (shipped) — **Sh.6 Phase 3 — tensor broadcast +
  scalar binops (+/-/*//), golden 51 closed end-to-end.** First
  release where `51_tensor_broadcast` runs byte-identical to the
  Python bootstrap (output `11 44 9 36 10 10 101 104 2 8 11 33`);
  v5.6.1 and earlier registered PASS only at function-match parity
  while emitting `llvm-as`-broken IR (`%t14 = add nsw i64 %ptr1,
  %ptr2` type mismatch — `lower_binary` fell through to the generic
  integer-add arm because no tensor branch existed). Semantic:
  no edits — `check_arithmetic_binary` at `semantic.mn:915` already
  routed `Tensor⊕Tensor/Int/Float` to `make_type("Tensor")`; element-
  type args flow through MIR `Value.ty.args` populated by
  `mir_tensor_of` in v5.6.0's `lower_tensor`. Lower: new
  `lower_tensor_binop` helper in `lower.mn` (+40 LOC) mirrors Python
  `lower.py::_lower_tensor_binop` (2843-2882). Dispatch in
  `lower_binary` above the `binop_from_str` fallthrough: both-tensor
  → `__mn_tensor_{op}_broadcast_{i64|f64}(lhs, rhs)`; tensor-scalar
  → `__mn_tensor_{op}_scalar_{ty}(lhs, rhs)`; scalar-tensor
  commutative (`+`, `*`) → `__mn_tensor_{op}_scalar_{ty}(rhs, lhs)`
  (swap to hit forward-scalar fn); scalar-tensor non-commutative
  (`-`, `/`) → `__mn_tensor_r{op}_scalar_{ty}(lhs, rhs)` (scalar
  first — matches `emit_llvm_text.py:3781`). Dest value typed
  `tensor_val.ty` so chained `((a + b) * c)` propagates element
  type through repeated dispatch. Helpers `tensor_op_suffix` (4-way
  `+/-/*//` → `add/sub/mul/div` map) and `is_tensor_value` (thin
  `TK_TENSOR` check) added alongside. Emit: 20 new runtime
  declarations in `declare_all_runtime` — 8 broadcast (`ptr, ptr →
  ptr`), 8 scalar (`ptr, double/i64 → ptr`), 4 reverse scalar
  (`double/i64, ptr → ptr`). Attr split fixed latent design gotcha:
  LLVM rejects `noalias` as a function attribute — it's a
  return-value prefix. Python splits at `emit_llvm_text.py:1298`;
  the self-hosted emitter's `declare_runtime_fn` already had the
  `if ret == "ptr"` guard for `get_fn_ret_prefix`, so 20 `"noalias "`
  entries went into the prefix fn and 20 `" nounwind"` entries went
  into the `get_fn_attrs` fn (the initial attempt using `" nounwind
  noalias"` in the fn-attr slot tripped `llvm-as: this attribute
  does not apply to functions`). Call-site routing unchanged —
  `emit_mir_call`'s generic `find_function` fallback picks up the
  declared `FnEntry` and emits through `emit_call_ir` with registered
  param types. Runtime untouched: all 20 `__mn_tensor_*_{broadcast,
  scalar,r*}_{f64,i64}` fns already shipped in
  `runtime/native/mapanare_gpu_builtins.c:549-720` (v4.44.0 +
  v4.47.0 rsub/rdiv add). Goldens harness 63/66 preserved at the
  count level but golden 51 flipped from function-match-PASS-but-
  broken-IR to actually-correct-and-PASS — same qualitative jump
  v5.6.1 made for golden 50. stage2.ll 201,442 lines (+0.78% vs
  v5.6.1) / 920 defines (+12), `llvm-as` clean, self-hosting
  preserved (mnc_all.mn has no tensor binops so the dispatch never
  fires during stage2 emission but the 20 decls are emitted
  unconditionally). Non-bootstrap pytest 5550 passed (+1 vs
  v5.6.1); `make lint` clean; `check_struct_registry.py` clean
  (23/23/89). Valgrind: 0 ERRORS / 66 WARNINGS_ONLY. ASan: 0
  ASAN_ERROR / 60 CLEAN / 6 CRASH_NO_ASAN (6 are Python-bootstrap
  C-backend compile failures on tensor builtins, not LLVM-path
  sanitizer issues). LSan on golden 51: 24 leaks / 672 B from
  `mapanare_tensor_alloc` — baseline-gated (base class COMPILE_FAIL
  → now LEAK is a forward step per `check_leak_summary.py`'s rules;
  mirrors the v5.6.0 → v5.6.1 pattern for goldens 49 / 50). Added
  Rt.06 row to `docs/known_issues.md` scoping tensor drop-glue
  (`emit_track_tensor` hook) to v5.6.4+. Ve.1 stage3 segfault
  persists (pre-existing from v5.4.4, not a v5.6.2 regression).
  What's next: v5.6.3 reductions + slicing (goldens 52/53), v5.6.4+
  Rt.06 drop-glue, v5.7.0 closure + or-pattern. See
  `docs/roadmap/v5/v5.6.2/SESSION_REPORT.md`.
- **v5.6.1** (shipped) — **Sh.6 Phase 2 — multi-dim tensor
  indexing (`a[i, j]`) + golden 50 closed end-to-end.** Second
  Sh.6 release; first where golden 50 runs byte-identical to the
  Python bootstrap (output `1 3 4 6 10 30 1 8 42 99 200`). Parser:
  `parse_postfix`'s `LBRACKET` branch rewritten from single-expr
  body into a bounded `COMMA` accumulator yielding `List<Expr>`;
  count==1 keeps `Expr::Index(left, idx)` so list / map / string
  single-subscript are byte-identical, count>=2 emits
  `Expr::TensorIndex(left, indices)` (AST variant pre-existed at
  `ast.mn:81` but was never wired). New accessors
  `expr_ti_obj` / `expr_ti_indices` in `ast.mn`. Semantic:
  `infer_expr` gains a `"tensor_index"` branch — walks operand +
  all indices for side-effect diagnostics; element type pulled
  from `Tensor<T>`'s T, defaulting to Float when unknown
  (mirrors Python `_lower_tensor_get` fallback). MIR: new
  `mir_tensor_of(elem)` helper attaches element type via
  `MIRType.args`; `resolve_mir_type` unchanged — TK_TENSOR still
  resolves to `ptr`, args inspected only at lower-time.
  `lower_tensor`'s result value now carries
  `mir_tensor_of(elem_type)` so `let`-bound tensors propagate
  Float/Int through to any later `a[i, j]` dispatch. Lower: new
  `lower_tensor_index_get(obj, indices)` emits
  `Call(__mn_tensor_get_{f64,i64}_nd, [obj, rank, i0, i1, ...])`
  (matches `lower.py::_lower_tensor_get` at 2750–2786);
  `lower_expr` gains a `"tensor_index"` dispatch; assignment target
  path gets a parallel `"tensor_index"` branch that lowers
  `d[i, j] = val` to `Call(__mn_tensor_set_{f64,i64}_nd, [obj,
  rank, i0, ..., val])` — no intermediate `IndexSet` MIR since the
  runtime owns tensor storage. Single-subscript-on-tensor
  foot-gun: `lower_index` gained a TK_TENSOR short-circuit so
  `b[0]` on a tensor routes to the same `_nd` runtime as multi-dim
  — without it the count==1 path fell through to list-shaped
  `IndexGet` and `llvm-as` rejected the `{ptr, i64, i64, i64, i64}`
  store against a bare tensor `ptr`. Emit: 4 new variadic runtime
  declarations `__mn_tensor_{get,set}_{f64,i64}_nd(ptr, i64, ...)`
  via `declare_runtime_fn` (the `...` in the params string passes
  through unchanged to valid LLVM varargs IR); 4 new
  `runtime_fn_attrs` rows (` nounwind` only — varargs intrinsics
  are conservative). 4 new branches in `emit_mir_call` each
  emitting the explicit function-type prefix form
  `call <ret> (ptr, i64, ...) @<fn>(<args>)` required by LLVM for
  varargs call-sites (mirrors `emit_llvm_text.py:3604-3641`); set
  path appends the value (`double` or `i64`) after the variadic
  index tail. **Closes golden 50_tensor_indexing end-to-end** —
  v5.6.0 counted 50 as PASS via function-name parity but the IR
  was incomplete; v5.6.1 is the first release where 50 actually
  executes. stage2.ll 199,883 lines (+1.0% vs v5.6.0) / 908
  defines, llvm-as clean, self-hosting preserved. 11 new parser
  tests in `tests/parser/test_tensor_multi_index.py` covering
  1D/2D/3D reads, Int tensor reads, assignment, single-subscript
  preservation for list/string/map, and chained `a[i][j]`.
  Non-bootstrap pytest 5549 passed (+19 vs v5.6.0 after `make
  build-rt` for the VERSION macro bump); `make lint` clean;
  `check_struct_registry.py` clean. Valgrind on 50: 5 tensor
  allocations leak at exit — pre-existing pattern (golden 49 under
  v5.6.0 leaks 5 tensor allocs identically), not a v5.6.1
  regression; tensor-lifetime drop glue is Own.1 follow-up scope.
  Ve.1 stage3 segfault persists (same signature as v5.6.0 —
  not a v5.6.1 regression). Goldens harness 63/66 preserved at
  the count level but golden 50 promoted from function-match
  parity to genuine correctness (49 + 50 now both truly pass).
  What's next: v5.6.2 broadcast (golden 51), v5.6.3 slicing +
  reductions (goldens 52/53), v5.7.0 closure + or-pattern
  (golden 64). See `docs/roadmap/v5/v5.6.1/SESSION_REPORT.md`.
- **v5.6.0** (shipped) — **Sh.6 Phase 1 — tensor literal parser +
  golden 49 closed.** First self-hosted tensor release. Grammar:
  `"Tensor"` becomes `KW_TENSOR` in `lexer.mn`; `parse_tensor_lit`
  rewritten from a 1D-only body shim into an iterative depth-stack
  walker supporting 2D/3D/… nested arrays
  `Tensor<T>[[1,2],[3,4]]` with row-major flattening + shape
  inference (mirrors `parser.py::tensor_literal + _walk`).
  Semantic: registers `tensor_rank/size/get_f64/get_i64/
  shape_dim/print` in `is_builtin_function` / `builtin_return_type`
  / `register_builtins` with correct Int/Float/Void ret types.
  Lowering: `lower_tensor` dest typed as `mir_tensor()` (was
  `mir_unknown()` → i64, causing ptr/i64 store mismatch);
  `lower_call_by_name` gets 6 tensor-builtin return-type branches
  so `str(tensor_get_f64(...))` routes through
  `__mn_str_from_float` not `_from_int`. Emission: declares the
  `__mn_tensor_*` runtime family (alloc, free, store_{f64,i64},
  get_{f64,i64}, rank, size, shape_dim, print_f64) with matching
  `runtime_fn_attrs`; `emit_tensor_init` rewritten from
  `inttoptr 0` stub to full `alloca [rank × i64] shape + store
  dims + __mn_tensor_alloc + __mn_tensor_store_*` pipeline; tensor
  builtins routed in `emit_mir_call` to their `__mn_tensor_*`
  equivalents. New MIR helper `mir_tensor()`;
  `resolve_mir_type(TK_TENSOR) → llvm_ptr()`. **Closes golden
  49_tensor_literal end-to-end** (mnc-stage1 compiles → llvm-as
  clean → lli output byte-identical to Python bootstrap:
  `1 3 1 3 2 6 1 6 2 3 3 8 1 8 3 20 -1 -2.5`). Goldens 50/51/52/53
  still fail — closing them needs multi-dim indexing (`a[i,j]`),
  tensor binops/broadcast, reduction methods (`.sum()`), range
  slicing (`a[0..2,_]`) — deferred to v5.6.1+. Two foot-guns caught
  in development: (1) `en` is a Mapanare keyword (Spanish "in")
  so `let en: String` binds as `<unknown>` and triggers spurious
  `"String + Option"` binop errors during self-compilation — fix:
  use `elem_val`/`elem_name` locally; (2) inline `list[i] = val`
  writes (emit_index_set's `ls.trap.N`/`ls.ok.N` blocks) disturb
  PHI predecessors in the enclosing function — pre-existing
  self-hosted-emitter bug latent until this release's nested-array
  walker triggered it; workaround wraps the list writes in three
  single-block helpers (`_tensor_pad_list` / `_tensor_set_at` /
  `_tensor_inc_at` in `parser.mn`) so the new blocks live inside
  the helper's CFG. Root-cause fix deferred. 18 new parser tests
  in `tests/parser/test_tensor_literals.py` covering 1D/2D/3D,
  Float/Int, trailing commas, negated elements, deep nesting,
  type annotations. stage2.ll 197,883 lines (+1.3% vs v5.5.7) /
  908 defines, llvm-as clean, self-hosting preserved;
  non-bootstrap pytest 5530 passed (after `make build-rt` for the
  VERSION macro bump); bootstrap pytest 225 passed; `make lint`
  clean; `check_struct_registry.py` clean. Ve.1 stage3 segfault
  persists (pre-existing from v5.5.7, confirmed by testing
  v5.5.7's own binary against its own source — same crash); not a
  v5.6.0 regression. Goldens harness 59/66 → 63/66 (function-match
  parity; genuine correctness close for 49 only). What's next:
  v5.6.1 multi-dim indexing (golden 50), v5.6.2 broadcast (golden
  51), v5.6.3 slicing + reductions (goldens 52/53), v5.7.0 closure
  + or-pattern (goldens 51/64). See
  `docs/roadmap/v5/v5.6.0/SESSION_REPORT.md`.
- **v5.5.7** (shipped) — **Sanitizer + fixed-point
  hardening.** Stabilization release for the v5.5.4–v5.5.6
  async coroutine pipeline. Two emit_llvm.mn changes (+93 /
  −19 LOC) plus a Ve.1 root-cause investigation. **Closes
  Rt.05 (the v5.5.5-deferred AwaitSuspend inner-coroutine
  leak)** by hoisting `%aw.hdl.ptr.N` GEP + `%aw.hdl.N` load
  from the `aw.drive.N` edge into the entry BB *before* the
  fast-path readiness branch. Now `%aw.hdl.N` dominates all
  three entries to `aw.ready.N` (fast-path direct,
  drive→check→ready, scheduler-resume→ready) so the cleanup
  trio is SSA-legal: `coro.destroy(%aw.hdl.N) +
  free(%aw.val.box.N) + free(%aw_fut)`. v4.102.0 foot-gun
  unaffected — handle is loaded *before* any scheduler
  activity, so the slot-1 clobber from the inner's
  final-suspend is irrelevant. **Adds destroy-path drop-glue
  helper** `emit_drop_glue_destroy(st)` — iterates
  `str_owned`/`list_owned`/`boxed_owned` unconditionally
  (still consults `moved_locals`) and wires into
  `coro.cleanup` before `llvm.coro.free`. No-op for the 5
  Sh.4 goldens (no heap-allocated locals in their async fns)
  but the correct foundation for future real-I/O async
  programs that may be cancelled mid-flight. SSA prefix
  `%drop.d.*.N` distinct from normal-exit `%drop.s|l|b.N`.
  **Full sanitizer matrix on 5 Sh.4 goldens:** valgrind 0
  errors / 0 leaks (e.g., 59_async_fanout = 36 allocs / 36
  frees / 0 in use at exit), ASan 0 errors, LSan 0 leaks,
  TSan 0 races on 56/57/58/59 under
  `MAPANARE_ASYNC_THREADS=4`. Compiler-side: valgrind 60
  CLEAN / 6 WARNINGS_ONLY / 0 ERRORS (vs 36 ERRORS baseline
  — every one closed); ASan 60 CLEAN / 6 CRASH_NO_ASAN
  (stage1-FAIL goldens) / 0 ASAN_ERROR; LSan 0 regressions
  vs v5.4.2 baseline. **Ve.1 root-caused but deferred:**
  valgrind on smallest crashing input (`lower.mn`,
  3.6K LOC; `mir.mn` 1.0K LOC does not crash) shows
  `parse_fn_body` writes 8 B 0-bytes-past a 256-byte
  malloc'd block — 154,355 errors / 42 contexts. 256 = 32 ×
  8 strongly implicates a `List<X>` default-capacity buffer
  whose realloc-on-push path is broken or bypassed. Predates
  async work; fix needs parser/list-growth surgery (~1
  session) — out of v5.5.7 scope. Tracked as
  `docs/known_issues.md` Ve.1; see
  `docs/roadmap/v5/v5.5.7/VE1_INVESTIGATION.md` for full
  forensics. stage2.ll 195,348 lines (+0.28% vs v5.5.6) /
  908 defines (+1 = `emit_drop_glue_destroy`), llvm-as
  clean, self-hosting preserved. Goldens harness 59/66
  preserved; non-bootstrap pytest 5511 passed (+3 vs v5.5.6
  — leak closures unblocked tests); bootstrap pytest 225
  passed; `make lint` clean. Risks R1–R4 from PLAN.md all
  mitigated or accepted-per-plan. Runtime unchanged. What's
  next: v5.5.7.1 Ve.1 fix (tractable, bounded); v5.5.8
  spawn/join + 60_async_multi_fanout golden (queue-pressure
  workload to exercise lazy-spawn); v5.5.9 PARITY_GAPS.md
  Sh.4 → Historical. See
  `docs/roadmap/v5/v5.5.7/SESSION_REPORT.md`.
- **v5.5.6** (shipped) — **Sh.4 Option B Phase 3 —
  scheduler-driven BlockOn + main lifecycle.** Replaces
  v5.5.4's synchronous `llvm.coro.resume` drive inside
  `BlockOn` with the real
  `__mn_coro_scheduler_register` + `__mn_coro_scheduler_run`
  pattern (mirrors `emit_llvm_text.py:5429-5441`). Injects
  `__mn_coro_scheduler_init(i32 0)` as the first buffered
  body line of async-aware main and
  `__mn_coro_scheduler_destroy()` before every main `ret`
  via a new `"i32_async"` `current_ret_type` sentinel
  (parallel to v5.5.4's `ASYNC_PTR:` pattern). Gated on a
  new free helper `module_has_async(module)` added to
  `emit_llvm.mn` instead of bumping the EmitState struct
  registry; threaded into `emit_mir_function` via a new
  `module: MIRModule` param (one call site updated in
  `emit_mir_module`). v4.102.0 handle-reload foot-gun
  preserved: `%bo.hdl.N` loaded BEFORE `scheduler_register`
  because the coroutine's final-suspend path overwrites
  slot 1 of the Future with the result box, so re-reading
  it afterwards would hand `coro.destroy` an 8-byte malloc'd
  int and segfault. **First release with real
  multi-threaded concurrency.** Combined with v5.5.5's
  scheduler-driven AwaitSuspend, all 5 Sh.4 goldens execute
  via the full Python-parity pipeline: 55→42, 56→43, 57→110,
  58→done, 59→220. `strace -f -e trace=clone3` on
  59_async_fanout shows 1 worker thread spawned for
  `MAPANARE_ASYNC_THREADS ≥ 2` (v5.1.4 lazy-spawn policy:
  `prime=1` pre-spawn + caller as worker 0; the
  `tasks > workers*8` lazy-spawn gate doesn't trigger on
  fast-completing tasks, so N≥3 doesn't produce more clones
  — stricter threading gate deferred to v5.5.8's
  `60_async_multi_fanout`). Valgrind 0 errors / 0 leaks on
  55_async_basic (5 allocs / 5 frees) — a STRICT improvement
  over v5.5.4 (which leaked `future` and `coro.mem`).
  `emit_llvm.mn` +60/−15 LOC. stage2.ll 194,799 lines
  (+0.13% vs v5.5.5) / 907 defines (+1 = `module_has_async`),
  `llvm-as` clean, self-hosting preserved (mnc_all.mn has no
  async decorators, so the helper returns false and no
  scheduler hooks emit into stage2). Goldens 59/66
  preserved; non-bootstrap pytest 5508 passed (after
  `make build-rt` to bump the VERSION macro in
  `libmapanare_rt.a`); bootstrap pytest 225 passed;
  `make lint` clean. Risks R1–R5 from PLAN.md all mitigated
  or not-observed. Runtime unchanged —
  `__mn_coro_scheduler_*` API complete since v5.1.4. What's
  next: v5.5.7 TSan/ASan sweep + Ve.1 investigation +
  coroutine-destroy drop-glue; v5.5.8 spawn/join +
  multi-fanout golden; v5.5.9 PARITY_GAPS.md Sh.4 →
  Historical. See `docs/roadmap/v5/v5.5.6/SESSION_REPORT.md`.
- **v5.5.5** (shipped) — **Sh.4 Option B Phase 2 —
  scheduler-driven AwaitSuspend.** Replaces v5.5.4's
  synchronous `llvm.coro.resume` drive inside
  `AwaitSuspend` with the real 6-block save/suspend/switch
  pattern mirroring `emit_llvm_text.py:5305-5372`. Fast-path
  readiness check → `aw.drive.N` (coro.resume inner once) →
  `aw.check.N` (re-check state) → `aw.suspend.N`
  (`__mn_coro_register_wait` + `llvm.coro.save` +
  `llvm.coro.suspend` + switch to `coro.ret`/`aw.resume.N`/
  `coro.cleanup`) → `aw.resume.N` → `aw.ready.N` (payload
  extract). All SSA names prefixed `aw.*.N` via `st.counter`.
  `emit_llvm.mn` `await_suspend` branch: +80 / −15 LOC.
  Post-opt CoroSplit now produces **outer** resume/destroy
  split pairs for every async fn with awaits: 56 ships
  `@outer.resume`/`@outer.destroy`, 57 ships
  `@fanout.resume`/`@fanout.destroy`, 58 ships
  `@process.resume`/`@process.destroy`, 59 ships
  `@fanout.resume`/`@fanout.destroy` — proving the outer
  coroutines really do have suspension points now (v5.5.4
  elided them because every resume was synchronous). PLAN.md
  §R5 predicted the 5 Sh.4 goldens might hang; reality —
  they all still execute correctly (55→42, 56→43, 57→110,
  58→done, 59→220) because the check-after-drive fast-path
  short-circuits: Sh.4 async fns return constants with no real
  I/O, so `future.state==1` is already true when `aw.check.N`
  runs, and control never reaches `aw.suspend.N` /
  `register_wait` / `coro.suspend` at runtime. CoroSplit
  still generates the suspend edge; it just never fires.
  Extended fast-path + no coro.destroy + no free in
  `aw.ready.N` matches the Python reference (structurally
  necessary: `%aw.hdl.N` is defined only on the drive edge,
  so it does not dominate ready from the fast-path or
  scheduler-resume edges — leak preferred over dominance
  violation). stage2.ll 194,553 lines (+501 vs v5.5.4, +0.26%)
  / 906 defines, llvm-as clean. Goldens 59/66 preserved;
  `make lint` clean; non-bootstrap pytest 5507 passed (after
  rebuilding `libmapanare_rt.a` for the version macro bump);
  bootstrap pytest 225 passed. BlockOn scheduler integration +
  `__mn_coro_scheduler_init` in main deferred to v5.5.6 —
  that's the release where the suspend path actually becomes
  load-bearing for non-trivial async programs. Risks R1-R5
  from PLAN.md all mitigated or observed-not-realized. See
  `docs/roadmap/v5/v5.5.5/SESSION_REPORT.md`.
- **v5.5.4** (shipped) — **Sh.4 Option B Phase 1 — real LLVM
  coroutines.** First real-coroutine release. Ships
  `presplitcoroutine` + full `@llvm.coro.id/begin/save/
  suspend/end` pipeline on async fns. `opt -O1` runs
  CoroSplit and produces `@foo.resume` + `@foo.destroy` split
  functions (verified). All 5 Sh.4 goldens execute correctly
  through the real LLVM coroutine ABI: 55→42, 56→43, 57→110,
  58→done, 59→220. Phase 0 empirical findings: (Q2) `llc
  -O2` alone crashes on coro intrinsics — `opt -O1 in.ll |
  llc -O2` pipeline required; (Q3) Ve.1 stage3 regression is
  orthogonal to async, stage2.ll remains llvm-as clean.
  Changes: `mir_opt.mn::should_inline` skips async fns (+9
  LOC); `emit_llvm.mn` (+~190 LOC) adds `is_async` gate to
  `emit_mir_function` (ptr return + presplitcoroutine attr +
  coro.entry prologue + pre_entry trampoline + coro.final/
  cleanup/ret epilogue), `emit_mir_return` rewrites `ret
  <ty> <val>` to box-payload store + `br %coro.final` via a
  `"ASYNC_PTR:"` prefix on `current_ret_type`, and
  `emit_mir_by_kind` replaces Option A's copy-based
  AwaitSuspend/BlockOn with real `llvm.coro.resume` + GEP +
  load + `llvm.coro.destroy` + free (bundled together
  because async fns now return `ptr` not the declared T).
  FnEntry registration bumped to ret_type="ptr" for async in
  both forward-declare and per-function sites. v4.102.0
  handle-reload foot-gun respected: handle loaded once pre-
  resume, reused for coro.destroy. Goldens 59/66 preserved;
  stage2.ll 194,052 lines / 906 defines, llvm-as clean;
  valgrind 0 errors on 55. Scheduler still declared but
  unused — v5.5.5 adds scheduler-driven await, v5.5.6 adds
  scheduler-driven block_on + main lifecycle. Risks R1-R7
  from DESIGN.md §6 all mitigated or deferred appropriately.
  See `docs/roadmap/v5/v5.5.4/SESSION_REPORT.md`.
- **v5.5.3** (shipped) — **Self-hosted coroutine emission
  design (docs-only).** Zero code changes. Ships one 480-line
  `DESIGN.md` that (1) re-validates v4.67.0 DESIGN.md against
  v5.5.x context, (2) surveys how Rust / Go / C++20 / Zig
  handle async and confirms LLVM switched-resume coroutines
  remain the correct choice, (3) maps the 6 remaining
  emitter-side gaps between v5.5.2's synchronous Option A
  stubs and full Python-parity coroutine emission, (4)
  specifies implementation phases v5.5.4 (inliner gate + async
  fn structural rewrite, ~155 LOC) → v5.5.5 (AwaitSuspend,
  ~90 LOC) → v5.5.6 (BlockOn + main scheduler lifecycle,
  ~80 LOC) → v5.5.7 (sanitizer hardening) → v5.5.8 (spawn +
  join + multi-fanout golden) → v5.5.9 (PARITY_GAPS.md Sh.4
  Historical + docs). User directive: "no cheap shit that
  bites us later" — Option A silently degrades any async fn
  with real I/O to single-threaded blocking. v5.5.4+ ships
  the real thing: `presplitcoroutine` attribute + full
  `@llvm.coro.id/size/begin/save/suspend/end` pipeline +
  `{i8 state, ptr payload}` Future struct + real scheduler
  drive via the existing C runtime API (which has been
  complete and TSan-clean since v5.1.4 — no runtime work
  needed). Risk register flags drop-glue × coroutine cleanup
  as HIGH; Ve.1 (stage3 segfault) noted as adjacent concern.
  Goldens 59/66 unchanged. See `docs/roadmap/v5/v5.5.3/`.
- **v5.5.2** (shipped) — **Sh.4 Phase 3 (Option A) — synchronous
  async emission.** Ships coroutine intrinsic + scheduler
  runtime declarations (17 decls total: 6 `__mn_coro_scheduler_*`
  + 11 `@llvm.coro.*` — unconditional, linker drops unused)
  and real emission for `AwaitSuspend` / `BlockOn` MIR variants
  as synchronous copies (`%dest = add i64 0, %future`). **Async
  fns stay as plain fns returning their declared type — no
  `presplitcoroutine`, no coroutine frame, no future struct.**
  All 5 Sh.4 goldens now llvm-as clean **and execute
  correctly**: 55_async_basic → 42, 56_async_await → 43,
  57_real_await → 110, 58_async_file_io → done, 59_async_fanout
  → 220. The tradeoff: Option A only works because every Sh.4
  golden uses `return <const>` async fns with no real
  suspension points. `mir_opt.mn::replace_uses_in_instr` +
  `clone_instr_for_inline` gain cases for `await_suspend` /
  `block_on` so the inliner properly renames the future operand
  when a call gets inlined into `block_on(...)`. Goldens harness
  59/66 unchanged; self-hosting preserved (stage2.ll 192,790
  lines / 906 defines, llvm-as clean). Valgrind 0 errors on
  55_async_basic. Option B (real coroutine wrapping) deferred
  to v5.5.3+ — that's where `presplitcoroutine` + future struct
  alloc + `ret → future.payload` rewrite + scheduler-driven
  `block_on` land, closing Sh.4 semantically for non-trivial
  async programs. See `docs/roadmap/v5/v5.5.2/`.
- **v5.5.1** (shipped) — **Sh.4 Phase 2 — MIR variants +
  lowerer.** Adds `AwaitSuspend(Value, Value)` + `BlockOn(Value,
  Value)` to `mir.mn::Instruction`, matching string-tag
  dispatch branches (`"await_suspend"` / `"block_on"`) in
  `instr_kind` + `instr_dest`, plus accessors for the future
  operand. New helper `fn_is_async(f: MIRFunction) -> Bool`
  scans the existing `decorators` list for `"async"` —
  non-invasive, no struct-layout change, no Reg.1 registry
  bump. The parser already stashes `async fn` as a `"async"`
  decorator (`parser.mn:797–798`); the helper is the
  authoritative check the v5.5.2 emitter will use to wrap the
  function body in a coroutine frame. `lower.mn` now emits
  `Instruction::AwaitSuspend(dest, inner)` for `await expr`
  (was a silent pass-through previously) and
  `Instruction::BlockOn(dest, args[0])` for `block_on(future)`
  (before monomorphization; mirrors `lower.py:1836–1845`).
  `emit_llvm.mn` gets stub handlers for both kinds that emit a
  comment line — prevents the `ERROR: unknown MIR instruction
  kind` stderr spam while keeping IR text stable and
  inspectable. Stub IR references undefined SSA names for
  dest; `llvm-as` still rejects — that's v5.5.2's fix.
  Goldens harness 59/66 unchanged (v5.5.0 already bumped it).
  Self-hosting preserved: stage1 compiles `mnc_all.mn` →
  191,802-line stage2.ll / 908 defines / 0 stderr. 7 FAIL
  unchanged. See `docs/roadmap/v5/v5.5.1/`.
- **v5.5.0** (shipped) — **Sh.4 Phase 1 — async builtin semantic
  registration.** Micro-release split: the original monolithic
  v5.5.0 plan (builtins + lower + emit + close Sh.4) re-scoped
  into v5.5.0 / v5.5.1 / v5.5.2. This release only touches
  `mapanare/self/semantic.mn` (+17 lines, 3 edits): adds
  `block_on` to `is_builtin_function`, `builtin_return_type`
  (returns `<unknown>` — type-inferred from the awaited
  `Future<T>`), and `register_builtins`; plus an explicit
  `"await"` case in `infer_expr` that recurses into the inner
  expression so errors inside `await foo()` are caught. 5 Sh.4
  goldens (55_async_basic through 59_async_fanout) advance past
  `mnc-stage1`'s semantic check and emit LLVM IR; the IR still
  contains an undeclared `call i64 @block_on(...)` and would
  fail `llvm-as` / not link. `scripts/test_native.py` compares
  stage1 against the Python bootstrap by function-count /
  function-name set (not IR validity, per v4.126.0 relaxation),
  so the harness PASS count flips **54/66 → 59/66** even though
  execution correctness is pending. `spawn` / `join` builtins
  deferred — the 5 goldens don't use them. 7 failures remain
  (Sh.6 × 5 tensor, Sh.7 × 1 closure, B × 1 bootstrap-fail);
  no regressions in the previously-passing 54. `v5.5.1` adds
  `BlockOn` / `AwaitSuspend` MIR variants + lowerer + Fn.is_async
  propagation; `v5.5.2` adds emitter coroutine intrinsic
  emission, scheduler init, and closes Sh.4 with sanitizer
  sweeps. See `docs/roadmap/v5/v5.5.0/`.
- **v5.4.4** (shipped) — **Own.1 Phase 2 — Move-aware drop-glue
  infrastructure; guard-lift deferred.** Three new `EmitState`
  fields (`str_owned_source`, `list_owned_source`, `boxed_owned_source`)
  parallel to the existing owner lists, carrying the bare SSA source
  name the slot was allocated for; registry 22/22 clean. Python
  mirror: `_local_strings_source` / `_local_boxed_source` /
  `_list_vars_source` lists + `_moved_locals: set[str]`. Lowerer Move
  emission in both `lower.mn` and `lower.py`: `Move(val)` fires after
  every resource-consuming op (list.push, map/list IndexSet,
  StructInit per field, EnumInit per payload, Some / Ok / Err, and
  MapInit literals). Drop-glue helpers rewritten to accept
  `List<String>` of ret-ptrs; `is_moved` check consults the parallel
  source array. Also fixes a latent `emit_fn` flush cap of 65536 that
  silently truncated large functions' drop-glue tail (raised to 1M).
  Guard-lift for `%struct.*` returns was implemented (one-level field
  walk extracting each escaping String/List/ptr) and reverted: the
  ~40 extractvalue lines per `%struct.EmitState`-returning call site
  inflated stage2.ll by 5× and triggered mnc-stage2 runtime segfault
  during lex of mnc_all.mn. v5.4.5+ re-lifts with a size gate.
  62_list_output stays LEAK; baseline unchanged from v5.4.3. Goldens
  54/66, UAF 55/11/0, valgrind 0 new ERRORS — all preserved.
  **Ve.1 regressed:** stage2.ll `llvm-as` OK but mnc-stage2 segfaults
  before stage3 emission (previously crashed on teardown with non-
  empty stage3). Not remediated this release. See
  `docs/roadmap/v5/v5.4.4/`.
- **v5.4.3** (shipped) — **Own.1 Phase 2 — close Rt.03 (loop-
  reassignment leaks).** Adds `EmitState.loop_depth: Int` (19th field,
  Reg.1 gate 24 → 25 clean) with matched push/pop around `for_body` /
  `while_body` / `mapfor_body` label emission in `emit_mir_basic_block`;
  Python `LLVMTextEmitter._loop_depth` + `_emit_fn` reset + push/pop
  around `for bb in fn.blocks` provide parity. `emit_track_string` /
  `_boxed` / `_closure` (self-hosted) + `_track_string` / `_track_boxed`
  / `_track_closure` (Python) prepend a `load {slot_ty}, slot` +
  `@__mn_str_free` / `@free` before the store when `loop_depth > 0`;
  outside loops the emission is byte-identical to v5.4.2. Zero-init in
  the entry-block prelude + null-tolerant runtime free fns make the
  first-iteration free a no-op. Closes Rt.03: 22_string_builder 6 objs
  / 19 B → CLEAN; baseline TSV refreshed; regression back to leaking
  now fails CI. D3 UAF risk (aliased copies + reassignment) did not
  materialize on the current corpus — UAF sweep byte-identical (55
  CLEAN / 0 ASAN_ERROR / 11 CRASH_NO_ASAN). Goldens 54/66 preserved;
  valgrind 66 WARNINGS_ONLY / 0 ERRORS preserved; leak sweep 45 CLEAN /
  3 LEAK (baseline-gated) / 11 COMPILE_FAIL / 7 LINK_FAIL / 0
  regressions. stage2.ll 169280 lines (+0.19% vs v5.4.2); `llvm-as`
  OK. `docs/known_issues.md` Rt.03 row flipped to CLOSED. See
  `docs/roadmap/v5/v5.4.3/`.
- **v5.4.2** (shipped) — **Own.1 Phase 2 — ASan leak-detection
  gate.** Flips `detect_leaks=1` across all 66 goldens via new
  `scripts/run_asan_leak_goldens.sh` (compile with `mnc-stage1`, `llc`
  to object, link with `libmapanare_rt.a` under `-fsanitize=address`,
  run under LSan). First sweep revealed 5 leak classes; 2 fixed by
  extending Phase 3.2's tracking hook with `is_string_returning_
  builtin(fn_name)` (13 Mapanare-level builtins whose MIR dest
  defaults to `mir_unknown()` in lower.mn's generic call path — 4
  goldens, 9 objs / 202 B) and adding `emit_track_boxed(ep)` in
  `emit_enum_init`'s boxed-payload branch (1 golden / 16 B).
  Suppressions (`scripts/asan_leak_suppressions.txt`, LSan format via
  `LSAN_OPTIONS`) trim libcuda cuInit; Mesa/Vulkan loader
  (`<unknown module>`) + loop-reassignment + struct-return
  intermediates are baseline-gated in `scripts/check_leak_summary.py`
  with PLAN.md §D3 / §D4 deferrals to v5.4.3. `make leak-check` +
  `.github/workflows/sanitizers.yml` leak-check job ratify the sweep
  as a merge gate. Goldens 54/66 preserved; UAF sweep 55/11
  preserved; valgrind 0 ERRORS preserved; leak sweep 44 CLEAN / 4
  LEAK (baseline-gated) / 11 COMPILE_FAIL / 7 LINK_FAIL / 0
  regressions. stage2.ll 168k lines (+1.8%); `llvm-as` OK. See
  `docs/roadmap/v5/v5.4.2/`.
- **v5.4.1** (shipped) — **Own.1 Phase 2 — make v5.4.0 drop-glue
  actually fire.** Populates v5.4.0's dormant owner lists with the
  shadow-slot architecture ported from Python. Three new `EmitState`
  fields (`entry_prelude_lines`, `entry_block_body`,
  `in_entry_block`) buffer the function body while `emit_track_*`
  can fire from any basic block; prelude flushes into the entry
  block at function close. Owner lists populated at `emit_mir_call`
  dispatch (runtime + user String returns), `emit_binop +` (String
  concat), `emit_interp_concat` (intermediates), `emit_list_init`
  (allocas hoisted + zero-init so they dominate all drop-glue
  loads). Drop-glue revised with per-slot `icmp eq ptr` +
  multi-block branch to skip frees that would alias the returned
  value (scalar String / List / ptr). Aggregate returns (struct /
  enum / Option / Result) conservatively skip all drops — UAF-safe,
  leaks until v5.4.2. Runtime free declarations landed. String
  literals intentionally NOT tracked (Python omits; rodata, is_heap=0
  no-ops, tracking each would explode IR quadratically). Goldens
  54/66; valgrind 0 new ERRORS; ASan 55 CLEAN / 11 CRASH_NO_ASAN
  unchanged; narrow leak test (`greet()`) reports 0 leaks under
  `detect_leaks=1`. stage2.ll 165k lines (+33% vs baseline, within
  R3 budget); stage2 `llvm-as` OK. See `docs/roadmap/v5/v5.4.1/`.
- **v5.4.0** (shipped) — **Own.1 Phase 2 — self-hosted drop-glue
  infrastructure.** Phase 0 baseline revealed all 11 Sh.2 tests
  already pass; release rescoped from "close 11 Sh.2 goldens" to
  "memory-correctness infrastructure, 0 new goldens". Ships: `Move`
  MIR variant (both emitters), four ownership slots in `EmitState`,
  three drop-glue helpers + `emit_drop_glue` dispatcher wired into
  `emit_mir_return`, Python `_do_move` routing to `_move_resource`,
  self-hosted `"move"` kind populating `moved_locals`. Goldens
  54/66 preserved; valgrind + ASan byte-identical to baseline.
  Owner-list population + lowerer Move emission + runtime free
  declarations deferred to v5.4.1. See `docs/roadmap/v5/v5.4.0/`.
- **v5.3.3** (shipped) — **SPEC + docs polish.** Zero compiler
  changes. SPEC §30 Package Management (manifest, install, lock,
  constraints, registry API). SPEC header 4.143.0 → 5.3.3 (27-release
  staleness closed). `examples/signals/counter.mn` signal demo. All
  three Coral LOW carry-forwards closed. Closeout arc complete.
  See `docs/roadmap/v5/v5.3.3/`.
### Planned / in-progress

- **v5.7.1** — SPEC + docs polish (pre-panel).
- **v5.8.0** — **RE-PANEL** (target 9.7+). Features first, panel last.
- **v6.0** — Borrow checker / multi-level alias analysis. Closes
  Rt.04 (multi-level drop-glue alias analysis, rescoped
  v5.6.6 — struct→list→string depth-2). The only remaining
  v5.6.x v6.0 carry now that v5.6.12 closed Lk.1 at the
  source via destination passing.

See `docs/roadmap/v5/CLOSEOUT_ARC.md` and
`docs/roadmap/v5/PARITY_GAPS.md`.

## Pre-Push Validation (MANDATORY)

Run the full validation suite before any commit/push. Mirrors CI.
Writes results to `error.log`.

```powershell
.\dev.ps1                  # Full validate: black + ruff + mypy + gcc + pytest + WAT
.\dev.ps1 validate -Watch  # Validate then watch
.\dev.ps1 test             # pytest only
.\dev.ps1 lint             # Linters only
.\dev.ps1 fmt              # Auto-format
.\dev.ps1 e2e              # End-to-end tests
.\dev.ps1 bench            # Benchmarks
```

The validate step includes **WAT emission** for `examples/wasm/*.mn`
— catches WASM CI failures locally. `pytest` alone is NOT sufficient.

Quick partial checks:

```bash
python -m mapanare emit-wasm examples/wasm/hello.mn -o /dev/null
black --check . && ruff check . && mypy mapanare/ runtime/
pytest tests/semantic/test_types.py -v
pytest tests/parser/ -v
```

## Commands

```bash
make install          # pip install -e ".[dev]"
make build            # pip install -e .
make test             # pytest tests/ -v  (add -n auto for parallel)
make lint             # ruff + black + mypy
make fmt              # black + ruff --fix
make benchmark        # python -m benchmarks.run_all
make clean            # Remove caches + egg-info
```

### Core workflows

```bash
# Golden test harness (WSL for stage1)
python scripts/test_native.py --stage1 mapanare/self/mnc-stage1

# Full rebuild cycle (WSL)
bash scripts/rebuild.sh              # concat + build + goldens

# Self-hosted fixed-point (WSL)
python scripts/build_stage1.py
bash scripts/verify_fixed_point.sh --keep
```

### Debug tooling

Full command reference: **`docs/guides/tools_reference.md`**.

- `python scripts/ir_doctor.py <cmd>` — per-function IR diagnostics,
  baselines, valgrind mapping, stage2 pipeline
- `python scripts/mir_trace.py <file.mn> <fn>` — trace type inference
  in the Python lowerer
- `culebra <cmd>` — 49+ templates for IR + C diagnostics (Rust binary,
  WSL)

## Testing the Native Compiler

Golden corpus at `tests/golden/*.mn` (66 programs). Reference IR at
`tests/golden/*.ref.ll`.

Workflow:
1. Edit `mapanare/self/*.mn` or `mapanare/emit_llvm_text.py`
2. `python scripts/build_stage1.py`
3. `python scripts/test_native.py --stage1 mapanare/self/mnc-stage1 -v`
4. Harness compares mnc-stage1 output against Python bootstrap —
   shows which functions are missing or different.

Every run updates `tests/golden/BENCHMARKS.md`. Commit to track
regressions.

**Current baseline (v5.7.0):** **66/66 — first time in project
history.** Sh.7 (closure-typed parameters) and B (or-pattern +
identifier `None` resolution) both closed in v5.7.0. The closure arc
is closed; every test in the corpus that defines "self-hosting" now
passes through `mnc-stage1`.

## Code Style

- **Black** (line length 100), **Ruff** (E, F, W, I), **MyPy** strict
- Target Python 3.11+ (bootstrap compiler)
- Dataclasses for AST nodes; type hints throughout

## Compiler Pipeline

```
.mn source
  → Lark LALR parser → AST (dataclasses)
  → Semantic checker
  → MIR lowering
  → MIR optimizer (O0–O3)
  → Emitter:
      ├→ emit_llvm_text.py  → LLVM IR (text)
      ├→ emit_c.py          → C source
      └→ emit_wasm.py       → WebAssembly (WAT/WASM)
```

Key modules in `mapanare/`:

| File | Role |
|---|---|
| `cli.py` | Entry point — command dispatch |
| `parser.py` | Lark transformer: parse tree → AST |
| `ast_nodes.py` | AST node definitions |
| `semantic.py` | Two-pass type checker + scope resolver |
| `mir.py` / `mir_builder.py` | MIR data + builder |
| `lower.py` | AST → MIR lowering |
| `mir_opt.py` | MIR optimizer passes |
| `emit_llvm_text.py` | LLVM IR generation |
| `emit_c.py` | C source generation |
| `emit_wasm.py` | WebAssembly (WAT) generation |
| `wasm_linker.py` | wasm-ld multi-module linking |
| `types.py` | **Single source of truth** for type system |
| `mapanare.lark` | LALR grammar, 13-level precedence |
| `tracing.py` | OpenTelemetry-compatible tracing |
| `diagnostics.py` | Rust-style structured error output |

## Runtime System

**Python runtime** (`runtime/`): `agent.py`, `signal.py`, `stream.py`,
`result.py`, `deploy.py`. **Legacy — being replaced by native .mn
stdlib.**

**Native C runtime** (`runtime/native/`): arena memory (no GC),
lock-free SPSC ring buffers, thread pool with work-stealing, coop
scheduler (mobile), agent lifecycle, TCP sockets, TLS (OpenSSL via
dlopen), file I/O, event loop (epoll/select), string interning,
memory profiling. Used by the LLVM backend.

## LLVM Backend Status

**Working:** functions, structs, enums, pattern matching, control
flow, type inference, generics, Result/Option, print, builtins, lists,
maps (Robin Hood), agents, signals (full reactivity), streams,
closures (env struct capture), traits, module imports, pipes,
multi-agent pipe definitions, string methods, GPU kernel dispatch.

**Not yet on LLVM:** tensor reshape, mutable views, stepped slices
(v5.x). Tensor surface stable since v4.45.0.

New LLVM features target `emit_llvm_text.py` (sole LLVM emitter).

## Type System (`mapanare/types.py`)

Single source of truth:
- `TypeKind` enum (25 kinds: INT, FLOAT, BOOL, STRING, LIST, MAP,
  OPTION, RESULT, SIGNAL, STREAM, AGENT, TENSOR, FN, etc.)
- `BUILTIN_FUNCTIONS`: print, println (deprecated), len, str, int,
  float, Some, Ok, Err, signal, stream
- `BUILTIN_CALL_MAP`: Mapanare → Python name mapping for emitters
- `PYTHON_TYPE_MAP`: Type → Python type mapping

## Self-Hosted Compiler (`mapanare/self/`)

10 modules, ~14,000 lines of Mapanare. Mirrors the Python bootstrap:

| Module | ~LOC | Role |
|---|---:|---|
| `ast.mn` | 781 | AST node definitions |
| `lexer.mn` | 575 | Tokenizer |
| `parser.mn` | 2,249 | Recursive descent parser |
| `semantic.mn` | 1,729 | Type checker + scope resolver |
| `mir.mn` | 791 | MIR data structures |
| `lower_state.mn` | 587 | Lowerer state |
| `lower.mn` | 3,602 | AST → MIR lowering |
| `emit_llvm_ir.mn` | 258 | LLVM type constants + IR builders |
| `emit_llvm.mn` | 3,206 | MIR → LLVM IR emitter |
| `main.mn` | 537 | Compiler driver |

**Patterns:** constructor functions (`let r: T = first_field; return
r`), state-threading, no struct literal syntax in grammar yet.

**Fixed-point:** NEAR (stage2.ll == stage3.ll except VERSION
placeholder). Strict hit at v4.134.0; currently NEAR per v5.3.2.

## Key Conventions

- Grammar: `mapanare/mapanare.lark` (bootstrap copy at `bootstrap/`)
- Emitters detect used features (agents/signals/streams) and import
  only as needed
- Builtins dispatched via `BUILTIN_CALL_MAP` in both emitters
- Self-hosted sources: `mapanare/self/*.mn`
- Language spec: `docs/SPEC.md` | Manifesto: `docs/manifesto.md` |
  RFCs: `docs/rfcs/`
- Roadmap: `docs/roadmap/ROADMAP.md` | Era READMEs:
  `docs/roadmap/v0/` → `docs/roadmap/v5/`
- Version: `VERSION` file
- Bootstrap frozen at v0.6.0 in `bootstrap/`

## Native-First Philosophy (v0.8.0+)

- **Stdlib in .mn:** new stdlib modules are `.mn`, compiled via LLVM.
  No more Python `.py` stdlib files.
- **C runtime as foundation:** OS primitives (sockets, TLS, file I/O)
  in C. Everything above (HTTP, JSON, routing) in Mapanare.
- **Test on LLVM:** every test runs on the LLVM backend.

## GPU / WASM / Mobile (v2.0.0)

- **GPU** — CUDA + Vulkan via dlopen; `@gpu`/`@cuda`/`@vulkan`
  annotations; PTX/SPIR-V codegen; `stdlib/gpu/`.
- **WASM** — `mapanare/emit_wasm.py` → WAT, `wasm_linker.py` for
  wasm-ld. Targets: `wasm32-unknown-unknown`, `wasm32-wasi`.
- **Mobile** — `aarch64-apple-ios`, `aarch64-linux-android`,
  `x86_64-linux-android`. Coop scheduler + smaller defaults (4 KB
  arenas, 256-slot rings, 4 K string intern cap).

## Ecosystem Packages

- **Dato** (`github.com/Mapanare-Research/dato`) — DataFrame package
  (pandas+numpy replacement), in .mn
- `net/crawl`, `security/scan`, `security/fuzz` — agents-based
- AI/LLM drivers: `stdlib/ai/` (LLM, embeddings, RAG)

## CI

GitHub Actions on push/PR to `dev`:
- **ci** — black → ruff → mypy → pytest. Matrix: Python 3.11/3.12
- **native** — C runtime: gcc, ASan, TSan
- **wasm** — WAT emit → wat2wasm → wasmtime WASI examples
- **android** — NDK cross-compile: ARM64 + x86_64 `.o` + ELF verify

5,400+ tests across the full pipeline.

## Skills (slash commands)

| Skill | Description |
|---|---|
| `/golden` | 15/15 golden suite through mnc-stage1 + llvm-as |
| `/stage2` | Compile self-hosted modules + validate stage2 IR |
| `/rebuild` | concat + build mnc-stage1 + run goldens |
| `/ir-audit` | LLVM IR pathology audit with baselines |
| `/valgrind-map` | Valgrind + auto-map offsets to struct fields |
| `/bump-version` | Bump VERSION, README, CHANGELOG, localized docs |
| `/code-review` | 7-reviewer panel review |
| `/create-pr` | PR title + description from commits |
| `/simplify` | Review + fix changed code |
| `/autoresearch` | Autonomous experiment loop |
| `/culebra-scan` | Culebra v2.0.0 — 49 templates (41 IR + 8 C) |

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **Mapanare** (28122 symbols, 61855 relationships, 300 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## When Debugging

1. `gitnexus_query({query: "<error or symptom>"})` — find execution flows related to the issue
2. `gitnexus_context({name: "<suspect function>"})` — see all callers, callees, and process participation
3. `READ gitnexus://repo/Mapanare/process/{processName}` — trace the full execution flow step by step
4. For regressions: `gitnexus_detect_changes({scope: "compare", base_ref: "main"})` — see what your branch changed

## When Refactoring

- **Renaming**: MUST use `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` first. Review the preview — graph edits are safe, text_search edits need manual review. Then run with `dry_run: false`.
- **Extracting/Splitting**: MUST run `gitnexus_context({name: "target"})` to see all incoming/outgoing refs, then `gitnexus_impact({target: "target", direction: "upstream"})` to find all external callers before moving code.
- After any refactor: run `gitnexus_detect_changes({scope: "all"})` to verify only expected files changed.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Tools Quick Reference

| Tool | When to use | Command |
|------|-------------|---------|
| `query` | Find code by concept | `gitnexus_query({query: "auth validation"})` |
| `context` | 360-degree view of one symbol | `gitnexus_context({name: "validateUser"})` |
| `impact` | Blast radius before editing | `gitnexus_impact({target: "X", direction: "upstream"})` |
| `detect_changes` | Pre-commit scope check | `gitnexus_detect_changes({scope: "staged"})` |
| `rename` | Safe multi-file rename | `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` |
| `cypher` | Custom graph queries | `gitnexus_cypher({query: "MATCH ..."})` |

## Impact Risk Levels

| Depth | Meaning | Action |
|-------|---------|--------|
| d=1 | WILL BREAK — direct callers/importers | MUST update these |
| d=2 | LIKELY AFFECTED — indirect deps | Should test |
| d=3 | MAY NEED TESTING — transitive | Test if critical path |

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/Mapanare/context` | Codebase overview, check index freshness |
| `gitnexus://repo/Mapanare/clusters` | All functional areas |
| `gitnexus://repo/Mapanare/processes` | All execution flows |
| `gitnexus://repo/Mapanare/process/{name}` | Step-by-step execution trace |

## Self-Check Before Finishing

Before completing any code modification task, verify:
1. `gitnexus_impact` was run for all modified symbols
2. No HIGH/CRITICAL risk warnings were ignored
3. `gitnexus_detect_changes()` confirms changes match expected scope
4. All d=1 (WILL BREAK) dependents were updated

## Keeping the Index Fresh

After committing code changes, the GitNexus index becomes stale. Re-run analyze to update it:

```bash
npx gitnexus analyze
```

If the index previously included embeddings, preserve them by adding `--embeddings`:

```bash
npx gitnexus analyze --embeddings
```

To check whether embeddings exist, inspect `.gitnexus/meta.json` — the `stats.embeddings` field shows the count (0 means no embeddings). **Running analyze without `--embeddings` will delete any previously generated embeddings.**

> Claude Code users: A PostToolUse hook handles this automatically after `git commit` and `git merge`.

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
