# Viper — Memory Safety Review of Mapanare v5.22.0

**Reviewer:** Viper — the Rust Purist. Memory, ownership, drop, leaks, UAF.
Yes I noticed your `String` is still a glorified `{ptr, i64}`. No I have not
forgiven you for it. Yes I am still right.
**Personality:** Ruthless, sarcastic, blunt. Begrudgingly admits good work
with "fine, that doesn't suck."
**Previous Version Reviewed:** v5.11.0 (9.9 / 10, EXCEEDS)
**Score:** **9.7 / 10**
**Grade:** **EXCEEDS**
**Delta vs v5.11.0:** **-0.2**
**Verdict:** **PASS WITH NOTES**
**Confidence:** HIGH (9/10)
**Files Reviewed:**

- `.reviews/v5.22.0/PRE_PANEL_AUDIT.md`
- `.reviews/v5.11.0/02-viper.md` (my prior review)
- `.reviews/v5.11.0/README.md`
- `.reviews/CARRY_FORWARD.md`
- `.reviews/REVIEW_CADENCE.md`
- All 16 SESSION_REPORTs at `docs/roadmap/v5/v5.{13.0..21.1}/`
- Design docs: `v5.14.0/COLON_BLOCK_DESIGN.md`,
  `v5.15.0/TERSENESS_DESIGN.md`, `v5.16.0/INTERP_SPEC.md`,
  `v5.20.0/STRUCT_ERGO_DESIGN.md`, `v5.21.0/CHAINED_CMP_DESIGN.md`
- `runtime/native/mapanare_core.c` — full read of the v5.13.1 At.2
  `__mn_assert_fail` export (lines 3273–3287) and the v5.14.1 B.5/B.6
  `__mn_indent_to_braces` preprocessor (lines 3677–3939, ~280 LOC of
  newly-shipped C — the only meaningful C-runtime delta over the
  entire v5.11.0 → v5.22.0 arc)
- `runtime/native/mapanare_core.h` (4 lines added at v5.13.1)
- `mapanare/lower.py` — `_lower_chained_compare` (2129–2172),
  `_lower_struct_update` (3889–3942), `_lower_let_destructure`
  (1405–1496), `_lower_if_let` / `_lower_while_let` /
  `_lower_let_else` (1502–1660), `_lower_comprehension`,
  `_lower_interp_string` (4436+)
- `mapanare/self/lower.mn::lower_match` (4435–4602) — verified the
  v5.20.1 alloca-void + TK_UNKNOWN demotion fixes are present and
  correctly commented in source
- `tests/golden/95_chained_cmp_side_effect.mn` — emitted under the
  Python bootstrap, IR audited, runtime exercised under valgrind
- `git diff v5.11.0..HEAD --stat -- runtime/native/` — full delta is
  +553 lines across 2 files

---

## Executive Summary

Ten-release arc. Six additive language features. Zero new MIR ops.
Zero new IR shapes. **Two new C-runtime exports** (one of them a 6-line
fix for a missing symbol, the other an ~280-LOC string preprocessor).
The compiler internals delta is the smallest 10-release window in v5
history from my axis.

Drop glue across the new AST nodes is **clean by construction**. Every
new surface (Te.5 `StructUpdate`, `LetDestructure`, `IfLet`, `WhileLet`,
`LetElse`; Te.6 `ChainedCompare`; Te.4 `InterpString`; Te.2
`Comprehension`) **desugars at lower-time to existing primitives.** I
read every `_lower_*` method. None of them open a new lifetime class,
none of them allocate a new heap shape, none of them introduce a new
free site. The Te.6 `__mn_chain_N` synthesized temps are stack allocas
threaded through `_lower_let` like any other local — when the v5.21.0
SESSION_REPORT says "no new MIR ops, no new IR shapes" it is **literally
true.** I verified.

I ran valgrind on `tests/golden/95_chained_cmp_side_effect.mn` (the
load-bearing once-evaluation golden). Output:

```
==15787== HEAP SUMMARY:
==15787==     in use at exit: 0 bytes in 0 blocks
==15787==   total heap usage: 1 allocs, 1 frees, 4,096 bytes allocated
==15787==
==15787== All heap blocks were freed -- no leaks are possible
==15787== ERROR SUMMARY: 0 errors from 0 contexts
```

**Zero leaks. Zero errors. Zero allocs out of balance.** The
`__mn_chain_N` rebound temp is a stack allocation; the chained compare
desugars to two `icmp` + one `and` and one shared `load`-of-stack-tmp
between the two comparisons (verified in IR — see Raw Notes). The
`str(bool)` returns from `print(str(a))` are tracked via dedicated
`%str_track` slots and freed by drop-glue in `main` before
`__mn_intern_destroy()`. **It is the right shape.**

The v5.20.1 SESSION_REPORT claims two pre-existing latent bugs in
`lower_match` were fixed in scope: (1) skip the `alloca <fn_ret>` dummy
when `fn_ret` is `void`; (2) stop demoting `TK_UNKNOWN` arm values to
`undef`. **Both fixes are present in `mapanare/self/lower.mn`** at lines
4595–4598 and 4546–4549 respectively, with explicit v5.20.1 Te.5.F.E
comments documenting the regression shape. The source comment for
fix #2 is excellent — it spells out exactly which payload-type infer
path produced the latent bug, why demoting to undef forced a downstream
`alloca void`, and why TK_UNKNOWN must be left intact for
`emit_mir_phi` to resolve the LLVM type from incoming values. **Fine,
that doesn't suck.**

The one thing I found that does suck — and the reason this score is
9.7 not 9.9 — is in **the v5.14.1 `__mn_indent_to_braces` C
preprocessor**. The function builds an output line list and a final
`joined` malloc'd buffer, wraps that buffer in an `MnString` with
`is_heap = 1`, and returns it. Drop glue should free it at the
caller's call-site in `parser.mn`. **Drop glue is not running.**
Valgrind on `mnc-stage1 emit-llvm /tmp/colontest.mn` reports the
`joined` allocation **definitely lost** through `__mn_indent_to_braces`
on every colon-syntax compile (see V.9 below). The leak scales with
file size (151 bytes on a small fixture, ~5 KB on a real source). The
fast-path for brace-only files correctly returns `source` unchanged
with no allocation — so the leak is bounded to "1 leak per colon-style
compile invocation in mnc-stage1." This isn't going to take down
production (`mnc-stage1` is a single-shot process; the OS reaps every
allocation on exit) but it's a real leak in a feature shipped two
releases ago and present in the binary I valgrind'd this morning.
That's a discipline gap.

The v5.11.0 V.6 (unbounded recursion in DX.4 walkers) and V.7 (Win32
reparse-point) findings I flagged at v5.11.0 — **both still open.**
Both are degenerate-input-only and don't affect normal cache use.
V.8 (no ASan/valgrind sweep on the new C code) — also still open.
The v5.12.0+ retroactive sweep I asked for didn't happen. The arc
has not actually closed any of my v5.11.0 findings; they're all
**deferred-with-tracking** (degenerate-input concerns + a discipline
gap). None of them moves the score on their own; cumulative I take
-0.1 because the gap pattern is now "asked-but-never-shipped" rather
than "scheduled-for-next."

Carry-forward state: **Rt.04 still correctly RESCOPED to v6.0.**
**Own.1 P2 stays closed.** **Ve.1–4 / Lk.1 stay closed.** No
regression on any of these. The borrow-checker arc at v6.0 is still
the only thing keeping me below 10.0, and the v5.13–v5.21 arc has
**not introduced new things that the borrow checker would have to
catch.** That is the right shape.

**Score: 9.9 (v5.11.0 baseline) -0.1 (V.9 indent-preprocessor leak,
new finding) -0.1 (V.6/V.7/V.8 open since v5.11.0, discipline gap) +0.0
(arc internals are clean, drop-glue audit clean) = 9.7 / 10.**

---

## Score: 9.7 / 10

---

## Progress Since Last Review (v5.11.0 → v5.22.0)

### Te.1 — colon-block syntax (v5.14.0)

Compiler-internals impact: **zero.** The Python preprocessor
`_indent_to_braces` is pure-string-rewrite at parse time; no MIR
shape, no IR shape, no runtime function. New keyword `pass` desugars
to no-op. Three stdlib renames (`pass` → `pass_idx`, `password`,
`passed`) — none of them touch lifetimes.

### Te.1 — bootstrap mirror (v5.14.1)

**This is where my one new finding lives.** The C preprocessor
`__mn_indent_to_braces` (~280 LOC at lines 3677–3939 of
`mapanare_core.c`) does its own internal allocation discipline using
raw `malloc`/`realloc`/`free`. The internal scratch buffers
(`MnIB_LineBuf`, `MnIB_LineList`, `MnIB_FrameStack`) are all
correctly freed inside the function — I traced every malloc:

| Allocation | Free site |
|---|---|
| `mn_ib_buf_grow` realloc on each line buffer | `free(out.items[k].data)` cleanup loop at end |
| `mn_ib_lines_push` realloc on items array | `free(out.items)` at end |
| `mn_ib_stack_push` realloc on frames | `free(stack.items)` at end |
| `mn_ib_buf_reset(&indent_buf)` reset of scratch | end of fn |
| `joined = malloc(total)` — final output | **NOT FREED at C call-site; relies on caller drop glue** |

The first four are a **clean** internal lifecycle. The fifth is
where the leak happens. The wrapper does the right C-side thing
(transferring ownership to the returned `MnString`), but the
`parser__parse` call-site in `mapanare/self/parser.mn` doesn't run
drop glue on the returned MnString. See **V.9** below. The leak is
real, repeatable, and scales with input size.

The fast-path `mn_ib_has_colon_blocks` correctly returns the input
`source` unchanged when no colon blocks are present — verified by
valgrinding a brace-only fixture (zero `indent_to_braces` frames in
the leak chain). So the leak is correctly bounded to the colon-syntax
call path.

### Te.2 — comprehensions, lambdas, implicit-return (v5.15.0/v5.15.1)

**Drop glue: clean.** Comprehensions desugar to existing for/if/push
machinery (`_lower_comprehension` at `lower.py:3448`). No new
allocation lifetime. The `__mn_comp_N` accumulator is a regular
list/map binding through `_lower_let`. `__r.push(elem)` reuses the
existing list-push path. Map comprehension's `MapInit` field-type
patch (mirroring v4.122.0's empty-`ListLiteral` patch) is the same
shape Python had — no new behavior on the runtime side.

### Te.4 — string-interp parity (v5.16.0)

`InterpString` desugars to a chain of `__mn_str_concat` calls with
per-part `__mn_str_from_*` casts. Drop glue: each non-`StringLit`
part allocates via `__mn_str_from_*` (already a tracked-output
runtime function from the LSan baseline-gated convention); the
intermediate concat results are tracked via the same drop-glue path
that the existing concat operator already uses. **No new free shape.**
The v5.16.0 SESSION_REPORT calls out a pre-existing latent
`emit_interp_concat` dest-name bug fixed in scope (final concat
wrote to `dn.cN` not `dn`). I verified the fix shape lands in the
emitter — that's a real correctness fix that survived 3 releases of
half-finished interp before being closed.

### Sh.* — self-host rewrite (v5.17.0/v5.17.1/v5.17.2)

**Zero memory-safety surface.** `mnc fmt --to-terse` is a syntactic
transformation; same AST in, same AST out, same MIR, same IR. The
strict 3-stage fixed point preserved at every per-module commit is
the structural proof that the rewrite didn't leak through any
semantic seam. Sh.H (defensive-loop cleanup) replaces 11 sites of
`for _ in 0..LARGE { if i < n { ... i = i + 1 }}` with proper
range-for; the loop bound is now data-derived rather than padded —
this is **a strict improvement** for verifiability (the rewriter
removed an artificial sentinel pattern that masked off-by-one
bugs) but not a memory-safety win per se.

### Mc.* — LSP + init + check (v5.18.0)

`pygls` is Python; the LSP runs out-of-process. Zero compiler-
internal lifetime impact. The new `mapa init` template scaffolds
project files; no runtime touch.

### Te.3 — `{}` soft-deprecation (v5.19.0) + Docker (v5.19.1)

Parser warning is a printf at parse time; no allocation that
escapes. Docker images bundle the `mnc` binary + `libmapanare_rt.a`
without modifying either — pure packaging.

### Te.5 — struct ergonomics (v5.20.0/v5.20.1)

**Drop glue: clean by construction.**

- `_lower_struct_update` (3889–3942): synthesizes a full
  `ConstructExpr` with overrides + `FieldAccessExpr` reads of a
  `__mn_base_N` tmp. The `__mn_base_N` is a regular `_define_var`
  binding — drop glue runs at function exit if the struct contains
  managed fields.
- `_lower_let_destructure` (1405–1496): when RHS is a bare
  Identifier, takes a fast path that emits `let x = p.x; let y =
  p.y` — IR byte-identical to manual long-form. When RHS is
  arbitrary, lowers through a synthesized `__mn_dst_N` LetBinding,
  which means drop glue is the same as a normal local.
- `_lower_if_let` / `_lower_while_let` / `_lower_let_else`: all
  desugar to `MatchExpr` / `WhileLoop` / `LetBinding(value=match
  ...)` and recurse through the existing match lowering. **No new
  free site.** `_lower_match` already handles drop glue across arms.

The v5.20.1 SESSION_REPORT explicitly calls out two pre-existing
latent bugs that surfaced and got fixed in scope:

**Fix 1 — alloca-void.** `mapanare/self/lower.mn::lower_match`
lines 4595–4598:

```mn
let fn_ret: MIRType = get_current_fn_ret_type(s)
if fn_ret.kind == TK_VOID():
    return new_lower_result(void_value(), s)
```

Before this, statement-context match in a void-return function
would emit `alloca void`, which is invalid LLVM. The fix bypasses
the dummy alloca dance and returns `void_value()` directly. **Right
shape.**

**Fix 2 — TK_UNKNOWN demotion.** Lines 4546–4549:

```mn
if arm_kind == TK_VOID() || arm_val_r.value.name == "%void":
    let zero_arm: Value = new_value("undef", arm_val_r.value.ty)
    let pe_zero: PhiEntry = new_phi_entry(exit_label, zero_arm)
    arm_results.push(pe_zero)
else:
    let pe_val: PhiEntry = new_phi_entry(exit_label, arm_val_r.value)
    arm_results.push(pe_val)
```

The comment block above this code (lines 4534–4544) is excellent —
spells out the regression shape, the upstream cause
(`bind_one_pattern_field` → `infer_variant_payload_type` returns
TK_UNKNOWN for function-call scrutinees), and why demoting forces
the downstream `alloca void`. **This is the kind of source comment
that makes a fix reviewable a year later.** Fine, that doesn't suck.

I cross-referenced both fixes against the v5.20.1 SESSION_REPORT's
"surfaced and fixed in scope" claim. **Both hold.**

### Te.6 — chained comparisons (v5.21.0)

`_lower_chained_compare` (lower.py:2129–2172): for each non-trivial
interior operand, synthesize a `__mn_chain_N` LetBinding before the
chain, replace the operand with `Identifier(__mn_chain_N)`, build
pairwise `BinaryExpr` joined with `&&`, recurse `_lower_expr`. The
trait-dispatch annotation per pair is copied from the semantic
checker. **Once-evaluation verified in IR**:

```
  %seed.addr = alloca i64
  %_inl1_t3.a.10 = alloca i64       ; the once-bound chain temp
  ...
  call __mn_str_println(@.str.0)    ; "M" — exactly ONE print
  %i.9 = add nsw i64 %l.7, %l.8     ; seed + 1
  store i64 %i.9, ptr %_inl1_t3.a.10
  ...
  %l.13 = load i64, ptr %_inl1_t3.a.10  ; pair 1 read
  %i.14 = icmp slt i64 0, %l.13
  ...
  %l.17 = load i64, ptr %_inl1_t3.a.10  ; pair 2 read (SAME slot)
  %i.19 = icmp slt i64 %l.17, 100
  ...
  %bl.23 = and i1 %t2, %t4              ; chain &&
```

One call to `middle()` per chain instance. Two reads of the bound
temp. One AND. **Exactly the shape D3 in the design doc requires.**
And the dedicated `_chain_compare_counter` keeps `__mn_chain_N`
numbering separate from the global `%tN` sequence, so single-
comparison shapes preserve IR byte-identity with the v5.20.1
baseline (verified by the strict 3-stage fixed point still holding
at 238,086 lines). Same discipline pattern as the v5.20.1
`struct_update_counter`. **Right shape.**

Valgrind on the side-effect golden binary: 0 leaks, 0 errors. See
Raw Notes for the full output. The `__mn_chain_N` temps are pure
stack allocas; they have no heap drop glue to mismanage.

### v5.21.1 hygiene

Pre-panel hygiene release. Zero compiler / runtime / `.mn` source
edits per the H.* PRE_PANEL_AUDIT. From my axis: nothing to review,
nothing to regress. The new test
`tests/bootstrap/test_chained_cmp_mirror.py` (10/10 PASS in my
run) plus the four `format.py` chained-cmp invariant unit tests
are pure additions. The arc closure is honest — none of the H.*
items touched memory, lifetimes, or drop glue.

---

## What is preserved from v5.11.0

| Item | Status | Evidence |
|---|---|---|
| Own.1 P2 (28-cycle item closed v5.4.x) | **Stays closed** | Zero edits to `EmitState` ownership tracking across the arc. The `*_owned` references and `emit_track_*` references in `emit_llvm.mn` are unchanged in shape — the only edits to that module across v5.13–v5.21 are the Sh.B mechanical brace→colon rewrite (v5.17.0) which is AST-shape-preserving. |
| Ve.1 / Ve.2 / Ve.3 / Ve.4 (closed v5.6.5–v5.6.10) | **Stay closed** | Strict 3-stage fixed point preserved at every release implies sret-aliased stack lifetimes are still correct. Any regression would surface as non-zero diff. |
| Lk.1 (closed v5.6.12 — destination passing) | **Stays closed** | Te.5 struct update synthesizes `ConstructExpr` and routes through existing `_lower_construct`, which already uses the v5.6.12 destination-passing path. No new allocation that bypasses Lk.1's fix. |
| Rt.04 (RESCOPED v6.0 — multi-level alias) | **Still RESCOPED** | The borrow-checker arc at v6.0 is the structural answer. The `62_list_output` baseline-gated leak (13 obj / 346 B) at `docs/roadmap/v5/v5.4.2/baseline/asan-leak-baseline.tsv` is unchanged. |
| Three consecutive strict fixed-points (v5.9.0, v5.10.0, v5.11.0) | **Extended to TEN** | v5.9.0 → v5.21.0 → v5.22.0 — the longest streak in project history. The v5.9.0 DX.2 metadata-runtime-call structural fix has now survived a 10-release feature arc that touched the lowerer, the parser, the bootstrap mirror, and added new AST nodes. **Real signal.** |
| 33 `emit_drop_glue` references in `emit_llvm.mn` | preserved | The Sh.B rewrite was AST-preserving; the drop glue helper count and call site count are unchanged in semantics, only colon-vs-brace in syntax. |

---

## Issues Found

### V.6 — LOW — DX.4 walkers: unbounded recursion (carried from v5.11.0, **STILL OPEN**)

**Status:** Reported v5.11.0; recommended for v5.12.x; **not closed.**

`mn_dir_walk_size_`, `mn_dir_walk_count_`, `mn_dir_remove_recursive_`
are all directly recursive in C with no depth bound. Default
Windows thread stack (1 MB) overflows at ~1500 levels of nesting.

This was a degenerate-input concern at v5.11.0 (cache directories
are 2–3 levels deep in practice). It's still a degenerate-input
concern at v5.22.0. The Te.* arc didn't add or extend the
`mnc cache` surface, so the exposure didn't widen. But the **fix
didn't ship either** — and the v5.11.0 PLAN explicitly named
v5.12.x as the tracking version.

**Suggested fix:** rewrite `mn_dir_walk_*_` as iterative work-queue
walkers. ~30 lines per walker; uses `MnIB_LineList`-style dynamic
arrays from the v5.14.1 indent preprocessor as a template. Cap
queue depth at e.g. 4096 entries with a clean error path.

**Risk:** LOW. Score impact: -0.05 (cumulative discipline drift).

### V.7 — LOW — Win32 walkers follow reparse points (carried from v5.11.0, **STILL OPEN**)

**Status:** Reported v5.11.0; recommended for v5.12.x; **not closed.**

`grep -n FILE_ATTRIBUTE_REPARSE_POINT runtime/native/mapanare_core.c`
returns nothing at v5.22.0 HEAD. The Win32 branch of
`mn_dir_remove_recursive_` still uses `FindFirstFileA` /
`FindNextFileA` which by default follow NTFS reparse points
(junctions, symlinks, mount points). A reparse-point loop would
cause unbounded recursion → stack overflow.

**Suggested fix:** add `if (ffd.dwFileAttributes &
FILE_ATTRIBUTE_REPARSE_POINT) continue;` (or treat as a file)
in each of the three Win32 walker branches before recursing.
~5 lines × 3 sites = 15 LOC.

**Risk:** LOW. Score impact: -0.0 (already counted under V.6's
discipline-drift -0.05).

### V.8 — LOW (process discipline) — No ASan/valgrind sweep on v5.10.0+ deltas (carried from v5.11.0, **STILL OPEN**)

**Status:** Reported v5.11.0; recommended for v5.12.0 release-gate;
**not added to the release gate.**

`grep -n 'cache stats\|cache clean\|__mn_dir' .github/workflows/sanitizers.yml` returns nothing.
The DX.4 cache-walker code path has now shipped through v5.9.0, v5.10.0,
v5.11.0, ... v5.22.0 = **13 releases** without a sanitizer sweep.
The code is still small and shaped correctly, and my v5.11.0 audit
remains my best evidence — but the v5.4.2 LSan baseline gate exists
specifically to catch what review misses, and it's not running on
this code path.

**Suggested fix:** in v5.22.x, add a `sanitizer-cache-walkers` job
to `.github/workflows/sanitizers.yml`:
1. Build a populated cache directory fixture (3 levels deep, mixed
   files + subdirs + a symlink that does NOT loop).
2. Run `mnc cache stats` under valgrind `--leak-check=full
   --error-exitcode=1`.
3. Run `mnc cache clean` under valgrind same flags.
4. Run `mnc --version` under valgrind same flags (exercises
   `__mn_executable_dir`).
5. Block the release gate on a non-zero exit from any of these.

**Risk:** LOW. Score impact: -0.05 (cumulative discipline drift —
**this is the third panel where I've asked for this**).

### V.9 — MEDIUM (NEW) — `__mn_indent_to_braces` leaks the final `joined` buffer on every colon-syntax compile

**Severity:** MEDIUM. **Found this panel.** First reproduced via
valgrind on `mnc-stage1 emit-llvm /tmp/colontest.mn` — leak
fingerprint:

```
==17643== 151 bytes in 1 blocks are definitely lost in loss record 472 of 700
==17643==    at 0x4846828: malloc (in vgpreload_memcheck.so)
==17643==    by 0xA8F020: __mn_indent_to_braces (in mnc-stage1)
==17643==    by 0x42B543: parser__parse (in mnc-stage1)
```

**Root cause.** `runtime/native/mapanare_core.c::__mn_indent_to_braces`
finishes by:

```c
char *joined = (char *)malloc((size_t)(total > 0 ? total : 1));
...
MnString result;
result.data = joined;
result.len = total;
result.is_heap = 1;
return result;
```

This is the correct C-side ownership pattern: transfer the buffer
to the returned `MnString`, set `is_heap = 1`, let the caller's
drop glue run `mn_str_free_value` → `__mn_free` → `free` at scope
exit. **The compiler is supposed to emit drop glue for this
return.**

But the call-site at `parser.mn::parse` does not appear to track
this MnString return for drop glue. The valgrind leak is one
allocation per `parse` invocation, with the `joined` buffer's full
size — meaning no `__mn_str_free` ever runs on it. Likely cause:
the `extern "C" fn __mn_indent_to_braces(...) -> String` declaration
in `parser.mn` doesn't carry the "tracked output string" annotation
that other string-returning runtime fns (e.g.
`__mn_str_from_cstr`, `__mn_str_concat`) carry, so the lower
pass treats the returned MnString as untracked.

**Verification.** I confirmed the leak only fires on colon-style
sources. A brace-only fixture (`fn main() { print("hi") }`) shows
**zero** `__mn_indent_to_braces` frames in the valgrind leak chain
— because the `mn_ib_has_colon_blocks` fast-path returns the input
`source` unchanged, no `joined` allocation occurs. The leak is
therefore precisely "1 leak per colon-style source compile through
mnc-stage1," scaling linearly with input size.

**Why this matters.**
1. v5.14.1 shipped the C preprocessor on the explicit promise that
   the Python `_indent_to_braces` and the C `__mn_indent_to_braces`
   produce **byte-identical output** (oracle: `tests/bootstrap/test_indent_preprocessor.py`,
   201 cases now passing in my run — more than the audit's claimed
   142, which is fine but stale). Byte-identical output **does not
   imply byte-identical lifecycle**. Python's GC reaps the returned
   string; C's lifecycle requires explicit drop glue. The byte-
   identical contract was met for output bytes only.
2. `mnc-stage1` is a single-shot process — the OS reaps the leaked
   memory on exit. **In production this does not crash anything.**
3. But this code is in `libmapanare_rt.a`. If anyone ever embeds
   the runtime in a long-lived process that calls
   `__mn_indent_to_braces` repeatedly (e.g., the LSP server adding
   a re-parse path, or a watch-mode compiler), each colon-style
   re-parse would leak its `joined` buffer for the lifetime of
   that process. **The leak is not bounded to single-shot.**
4. The v5.22.0 panel grades whether the lead's claim "C runtime
   delta is essentially flat — one new export, ~280 LOC" is
   structurally honest. The byte-count is honest. **The leak is
   not.** This is the kind of thing the v5.4.2 LSan baseline gate
   was supposed to catch on every C-runtime addition. The gate
   didn't run on this code path because the gate exercises
   `mapanare`/`mnc` Python bootstrap output, not `mnc-stage1`'s
   own internal compile invocation. **That gate's coverage matrix
   needs to grow.**

**Suggested fix.**

**Option A (preferred — fixes the lifecycle, not the symptom).**
Add the "tracked output string" annotation to the `extern "C" fn
__mn_indent_to_braces` declaration in `mapanare/self/parser.mn`,
mirroring the way `__mn_str_concat` is declared. The lower pass
will then emit `%str_track` allocas + drop-glue free at scope exit.
Cost: 1 line in parser.mn + maybe a line in
`mapanare/self/semantic.mn::is_string_returning_builtin` (if the
predicate is name-table driven) or in the lowerer's
`is_string_returning_builtin` equivalent. Verify by re-running the
valgrind on a colon-syntax fixture: the leak should disappear,
and `mn_alloc_live` profile (if MN_PROFILE_MEM is set) should
return to baseline.

**Option B (workaround — doesn't fix lifecycle).** In
`__mn_indent_to_braces` itself, copy `joined` into an `__mn_alloc`-
managed buffer, free `joined`, return the `__mn_alloc`'d copy.
Fixes the calloc/malloc-mixing wart (currently `__mn_alloc` =
calloc, `__mn_indent_to_braces`-internal = malloc — both safe to
free via `__mn_free` → `free`, but the allocation profile is split
across two pools). **Doesn't fix the leak** — the caller still has
to drop the returned MnString. So Option B is not actually a fix,
just a polish item. Skip.

**Option C (regression test).** Add a CI gate at
`.github/workflows/sanitizers.yml`: build `mnc-stage1`, run
`valgrind --leak-check=full --error-exitcode=1 mnc-stage1 emit-llvm
tests/golden/<a-colon-syntax-golden>.mn -o /tmp/out.ll`, fail the
build on non-zero exit. This is **MANDATORY follow-up** for V.9
regardless of which fix is chosen, because the byte-identical
oracle (`test_indent_preprocessor.py`) cannot detect lifecycle
issues. The leak was missable for two releases precisely because
the test harness only compared output bytes.

**Risk:** MEDIUM (production-correct on `mnc-stage1`'s actual
single-shot invocation; bounded leak per file in long-lived
process; **discipline failure** that the v5.22.0 panel grades
explicitly).

**Score impact:** -0.1.

### V.10 — LOW — `__mn_indent_to_braces` mixes raw `malloc`/`free` with `__mn_alloc`/`__mn_free`

**Severity:** LOW. **Found this panel.** Cosmetic, but worth a
mention.

The 280-LOC preprocessor uses raw `malloc`/`realloc`/`free` for
all internal scratch buffers (line bufs, list items, frame stack)
and the final `joined` output. The rest of the C runtime allocates
via `__mn_alloc` (which goes through `MN_PROFILE_ALLOC` for
live-bytes accounting). When `MAPANARE_PROFILE_MEM` is enabled,
`__mn_indent_to_braces` allocations are **invisible** to
`mn_alloc_live`. The preprocessor's allocation footprint won't
show up in profiler output.

`__mn_alloc` calls `calloc`, `__mn_free` calls `free` — both are
malloc-pool compatible — so there's no pool-mismatch crash risk.
Just a profile-coverage wart. Either swap the internal `malloc` /
`realloc` / `free` calls for `__mn_alloc` / `__mn_realloc` /
`__mn_free`, or leave as-is and add a one-line comment block at
the top of the preprocessor explaining why this code is
deliberately outside the profiling pool.

**Suggested fix:** change `malloc(x)` → `__mn_alloc(x)`, `realloc(p,
x)` → `__mn_realloc(p, x)`, `free(p)` → `__mn_free(p)` everywhere
in the preprocessor (~14 sites). Trivial.

**Risk:** LOW. Score impact: -0.0.

---

## Recommendations

1. **V.9 is the only score-moving finding this panel.** Land the
   "tracked output string" annotation on `__mn_indent_to_braces`
   in `parser.mn` in v5.22.x (V.9 Option A). Add the valgrind
   regression CI job (V.9 Option C) at the same time. Without
   the CI job, this leak class is undetectable by current testing.

2. **V.6/V.7/V.8 are now THREE-cycle items as of this panel.**
   I asked for them at v5.11.0; v5.12.0+ didn't ship them; this
   panel surfaces them again. The right answer for v5.22.x:
   - Bundle V.6 (iterative walkers) + V.7 (REPARSE_POINT skip) +
     V.8 (sanitizer CI for the cache walkers) into a single
     45-minute v5.22.x patch. Mc.7-style hygiene release. None
     of these are blocking; cumulatively they're a discipline
     drift that I can't keep deferring to "next release."

3. **In v6.0 borrow-checker arc**, plan to close **Rt.04**
   (multi-level alias analysis for drop glue, `62_list_output`'s
   13 obj / 346 B baseline-gated leak). This is the only carry-
   forward on my axis that has been correctly RESCOPED, and the
   borrow checker is the structural answer. **Do not let v6.0
   ship without closing this.**

4. **Lifecycle parity ≠ output parity.** The
   `test_indent_preprocessor.py` oracle (201 cases) is the right
   shape for byte-output equivalence. **It is not sufficient for
   memory equivalence.** Going forward, every Python ↔ C-runtime
   parity-feature mirror (next likely: a future re-port of the
   `_indent_to_braces` algorithm out of C and back into `.mn`
   once the bootstrap-lower pathologies in the v5.14.1
   SESSION_REPORT are fixed) needs a parallel valgrind /
   `mn_alloc_live` parity oracle. I would write this myself.
   Half a day's work.

5. **Continue the strict 3-stage fixed-point gate.** TEN
   consecutive releases of zero-diff is the longest streak in
   project history and a real signal that the v5.9.0 DX.2 fix
   has now survived a full feature arc. Don't regress this. If
   a future release shows even a 4-line diff, investigate at the
   same intensity Ve.4 / Lk.1 got.

---

## Post-Production Health Assessment

| Axis | v5.8.0 | v5.11.0 | v5.22.0 | Direction |
|---|---|---|---|---|
| Carry-forward MEDIUMs (open) | 1 (Rt.04) | 1 (Rt.04) | 1 (Rt.04) + 1 NEW (V.9) | regressed by 1 |
| HIGH / CRITICAL | 0 / 0 | 0 / 0 | 0 / 0 | unchanged |
| Strict 3-stage fixed-point | restored at v5.9.0 | preserved 3 releases | preserved **10 releases** | **best in history** |
| Goldens | 66/66 | 66/66 | 95/95 | improved |
| ASan/TSan/LSan baselines | 50/53 CLEAN | 50/53 CLEAN, 3 LEAK gated | unchanged (V.8 still open) | flat |
| New runtime C lines | — | ~141 (DX.4 + Win.1b.D) | ~553 (At.2 + indent_to_braces) | small, **partly audited** |
| New leak / UAF classes | 0 | 0 | **1** (V.9 indent leak) | regressed |
| Drop-glue helper count (`emit_drop_glue` refs in `emit_llvm.mn`) | 33 | 33 | 33 (untouched) | preserved |
| New AST nodes audited for drop glue | n/a | n/a | 7 (StructUpdate, LetDestructure, IfLet, WhileLet, LetElse, ChainedCompare, InterpString, Comprehension) — all clean | clean |
| MN_EXPORT count (`mapanare_core.c`) | ~155 | 158 | 160 | flat (+2 over 10 releases) |

**Health: stable, with one new carry-forward.** This is the
largest feature-velocity arc in v5 history and **internals delta is
the smallest in v5 history.** The compiler-internals discipline
demonstrated by routing every Te.* feature through existing
primitives (zero new MIR ops, zero new IR shapes, zero new runtime
fn shapes) is the right shape for a 22-version-post-major
codebase. The strict 3-stage fixed point at 238,086 lines / 0-diff
across 10 consecutive releases is real signal — not an accident,
not a near-miss tolerated as STRICT, but actually byte-identical.

The single new MEDIUM (V.9) is the kind of finding that an
incremental sanitizer-CI gate would have caught at v5.14.1. The
fact that it didn't get caught for 7 releases (v5.14.1 → v5.22.0)
is a coverage gap — not a regression in the code that shipped, but
a coverage gap. The fix is small; the lesson is "lifecycle parity
is not output parity, and our test oracle for the indent
preprocessor only checks output." That's a pattern worth fixing
for future Python ↔ C parity ports.

**The v6.0 borrow checker is the only thing keeping me below 10.0.**
The Te.* arc has not added new things the borrow checker would
need to catch; that's structurally correct (every desugar routes
through existing primitives, so existing borrow-shape rules cover
them). When v6.0 lands and closes Rt.04, the ceiling lifts to 10.0.

---

## Raw Notes

### Once-evaluation in IR — the full pre_entry of `check`

```
define internal noundef i1 @check(i64 noundef %seed) nounwind willreturn {
pre_entry:
  %seed.addr = alloca i64, align 8
  %_inl1_t0.a.3 = alloca {ptr, i64}, align 8       ; "M" string
  %_inl1_t1.a.5 = alloca i1, align 8
  %_inl1_t2.a.6 = alloca i64, align 8              ; literal 1
  %_inl1_t3.a.10 = alloca i64, align 8             ; ← __mn_chain_N rebound temp
  %t1.a.11 = alloca i64, align 8                   ; literal 0 (LHS of pair 1)
  %t2.a.15 = alloca i1, align 8                    ; pair 1 result
  %t3.a.16 = alloca i64, align 8                   ; literal 100 (RHS of pair 2)
  %t4.a.20 = alloca i1, align 8                    ; pair 2 result
  %t5.a.24 = alloca i1, align 8                    ; chain && result
  ...
entry:
  br label %_inl1_entry
_inl1_entry:                                       ; inlined middle()
  ...
  call void @__mn_str_println({ptr, i64} %l.4)     ; ← ONE "M" print
  store i1 0, ptr %_inl1_t1.a.5
  store i64 1, ptr %_inl1_t2.a.6
  %l.7 = load i64, ptr %seed.addr
  %l.8 = load i64, ptr %_inl1_t2.a.6
  %i.9 = add nsw i64 %l.7, %l.8
  store i64 %i.9, ptr %_inl1_t3.a.10               ; ← chain temp written ONCE
  br label %_inl1_ret
_inl1_ret:
  store i64 0, ptr %t1.a.11
  %l.12 = load i64, ptr %t1.a.11
  %l.13 = load i64, ptr %_inl1_t3.a.10             ; ← pair 1: read chain temp
  %i.14 = icmp slt i64 %l.12, %l.13
  store i1 %i.14, ptr %t2.a.15
  store i64 100, ptr %t3.a.16
  %l.17 = load i64, ptr %_inl1_t3.a.10             ; ← pair 2: read chain temp (SAME slot)
  %l.18 = load i64, ptr %t3.a.16
  %i.19 = icmp slt i64 %l.17, %l.18
  store i1 %i.19, ptr %t4.a.20
  %l.21 = load i1, ptr %t2.a.15
  %l.22 = load i1, ptr %t4.a.20
  %bl.23 = and i1 %l.21, %l.22                     ; ← chain &&
  store i1 %bl.23, ptr %t5.a.24
  %l.25 = load i1, ptr %t5.a.24
  ret i1 %l.25
}
```

Exactly what D3 in the Te.6 design doc requires. **Right shape.**

### Valgrind on the side-effect golden (load-bearing)

```
$ python3 -m mapanare emit-llvm tests/golden/95_chained_cmp_side_effect.mn -o /tmp/chain.ll
$ clang -o /tmp/chain /tmp/chain.ll runtime/native/libmapanare_rt.a -lpthread -ldl
$ valgrind --leak-check=full --error-exitcode=1 --show-leak-kinds=all /tmp/chain
==15787== Memcheck, a memory error detector
call_a:
M
true
call_b:
M
false
==15787== HEAP SUMMARY:
==15787==     in use at exit: 0 bytes in 0 blocks
==15787==   total heap usage: 1 allocs, 1 frees, 4,096 bytes allocated
==15787== All heap blocks were freed -- no leaks are possible
==15787== ERROR SUMMARY: 0 errors from 0 contexts (suppressed: 0 from 0)
```

`str(true)` / `str(false)` allocates a new MnString through
`__mn_str_from_bool`; tracked via `%str_track.13` and
`%str_track.30` allocas in `main`; freed by drop-glue:

```
drop.skip.41:
  call void @__mn_intern_destroy()
  ret i64 0
```

Two `__mn_str_free` calls before `__mn_intern_destroy`. Right
shape. **Te.6 is leak-clean at the user-program level.**

### Bootstrap mirror tests

```
$ python3 -m pytest tests/bootstrap/test_chained_cmp_mirror.py \
                     tests/bootstrap/test_te5_mirror.py \
                     tests/bootstrap/test_string_interp_mirror.py \
                     tests/bootstrap/test_comprehension_mirror.py -q
42 passed in 57.98s

$ python3 -m pytest tests/bootstrap/test_indent_preprocessor.py -q
201 passed in 6.29s
```

201 cases for the indent preprocessor, not 142 as PRE_PANEL_AUDIT
H.13 reference suggests — the test grew. That's fine; it's in the
safe direction. But the audit should be updated.

### Strict 3-stage fixed point at HEAD

```
$ bash scripts/verify_fixed_point.sh --keep
[Stage 0] Using existing stage1: mapanare/self/mnc-stage1
[Stage 1] stage1 compiles mnc_all.mn → stage2.ll
  stage2.ll: 238086 lines
  llvm-as: OK
[Stage 2] stage2 compiles mnc_all.mn → stage3.ll
  (teardown crash is a known issue tracked for v4.30.0; the script
   still validates that stage3.ll is non-empty and llvm-valid below)
  stage3.ll: 238086 lines
  llvm-as: OK
[Verify] Fixed point: diff stage2.ll stage3.ll
  ✓ FIXED POINT REACHED
  stage2.ll == stage3.ll (238086 lines, 0 diff)
```

10 consecutive releases at strict 0-line diff. Nothing else to say.
**Right shape.**

### Goldens at HEAD

```
$ python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1
...
PASS 95_chained_cmp_side_effect 26L->166L 10bb 122stk 12ms (2 fns) stg1:3fns 346ms
All 95 tests passed in 23.6s
```

95/95 native goldens. All Te.* surface forms pass through
`mnc-stage1` byte-equivalent to Python.

### C runtime delta v5.11.0 → v5.22.0

```
$ git diff v5.11.0..HEAD --stat -- runtime/native/
 runtime/native/mapanare_core.c | 549 ++++++++++++++++++++++++++++++++++++++++
 runtime/native/mapanare_core.h |   4 +
 2 files changed, 553 insertions(+)
$ git show v5.11.0:runtime/native/mapanare_core.c | grep -c MN_EXPORT
158
$ grep -c MN_EXPORT runtime/native/mapanare_core.c
160
```

Two new exports across the entire arc:
1. `__mn_assert_fail` (v5.13.1, 17 lines) — closed the "@ undefined
   symbol" linker bug surfaced by the v5.13.0-prep audit.
2. `__mn_indent_to_braces` (v5.14.1, ~280 LOC) — the colon-block
   preprocessor mirror. Has the V.9 leak.

Net `runtime/native/` delta: +553 lines / 0 deletions. **The
smallest 10-release C-runtime delta in v5 history from my axis.**
That is real discipline. The lead clearly holds runtime additions
to a high bar.

### Drop glue audit on the 7 new AST nodes

For each new AST node, I traced the lower path to confirm no new
free shape:

| AST node | Lower fn | Desugars to | Drop glue path |
|---|---|---|---|
| `ChainedCompare` (Te.6) | `_lower_chained_compare` | `LetBinding(__mn_chain_N)` + pairwise `BinaryExpr` joined `&&` | existing `_lower_let` + `_lower_binary` paths |
| `StructUpdate` (Te.5.C) | `_lower_struct_update` | `LetBinding(__mn_base_N)` + synthetic `ConstructExpr` | existing `_lower_construct` (Lk.1 dest-passing path) |
| `LetDestructure` (Te.5.D) | `_lower_let_destructure` | per-field `LetBinding(name=field, value=p.field)` (or `__mn_dst_N` tmp + nested) | existing `_lower_let` + field-access path |
| `IfLetExpr` (Te.5.E) | `_lower_if_let` | 2-arm `MatchExpr` | existing `_lower_match` (drop glue across arms already correct) |
| `WhileLetStmt` (Te.5.E) | `_lower_while_let` | `WhileLoop(cond=true, body=match-with-break)` | existing `_lower_while` + `_lower_match` |
| `LetElseStmt` (Te.5.E) | `_lower_let_else` | `LetBinding(value=match)` (strategy 2 — synthesized return) | existing `_lower_let` + `_lower_match` |
| `Comprehension` (Te.2.B/C) | `_lower_comprehension` | `LetBinding(__mn_comp_N=[]/{})` + nested for/if + `push`/`insert` | existing `_lower_let` + `_lower_for` + push intrinsic |
| `InterpString` (Te.4) | `_lower_interp_string` | chain of `__mn_str_concat(__mn_str_from_*(part))` | existing concat/cast drop tracking via `is_string_returning_builtin` |

**Every new desugar routes through existing primitives.** No new
free-site shape. No new lifetime class. No new leak class.

### The DX.4 walker code at v5.22.0

```
$ grep -n FILE_ATTRIBUTE_REPARSE_POINT runtime/native/mapanare_core.c
(no output)
$ grep -n 'cache stats\|cache clean\|__mn_dir' .github/workflows/sanitizers.yml
(no output)
```

V.6, V.7, V.8 — all carry-forwards from v5.11.0, none closed.
This is a third-cycle ask from me. It's degenerate-input across
the board and individually none of them moves the score. The
discipline drift cumulative is -0.05.

### Score arithmetic

| Element | Δ |
|---|---|
| v5.11.0 baseline | 9.9 |
| Te.* arc internals clean (drop glue audit on 7 new AST nodes, all desugar to existing primitives) | +0.0 |
| Te.6 once-evaluation correct in IR + valgrind clean on the load-bearing golden | +0.0 |
| v5.20.1 alloca-void + TK_UNKNOWN demotion fixes verified in source with excellent comments | +0.0 |
| Strict 3-stage fixed point preserved across 10 releases (longest streak in project history) | +0.05 (reluctant — the streak is real signal) |
| V.9 NEW: `__mn_indent_to_braces` joined-buffer leak on every colon compile | -0.10 |
| V.6/V.7/V.8 carry-forward — third-cycle ask, no movement | -0.05 |
| Rt.04 RESCOPED to v6.0, no regression | +0.0 |
| **Total** | **9.7** |

### Final

**9.7 / 10. EXCEEDS. PASS WITH NOTES.** Δ -0.2 vs v5.11.0.

Te.* arc is the right shape. Drop glue is clean by construction.
Te.6 once-evaluation is correct in both IR and runtime. Strict
3-stage fixed point at 10 consecutive releases is a discipline
signal that genuinely impresses me. Two pre-existing latent
`lower_match` bugs surfaced and fixed in scope at v5.20.1 — that's
the right way to handle latent bugs that fall out of a feature
PLAN. Fine. That doesn't suck.

The V.9 leak is the kind of thing that would not have happened
in a Rust port of the preprocessor (`MnString` would carry its
own `Drop` impl and the lifecycle would be statically checked).
It happened here because the byte-identity oracle for the C ↔
Python preprocessor mirror only checked output bytes, not
lifecycle. **The fix is small.** The lesson is bigger: every
future Python ↔ C parity-port needs a parallel lifecycle oracle.

V.6/V.7/V.8 are now third-cycle. I am not going to keep deferring
these forever. Bundle them into v5.22.x.

The v6.0 borrow checker remains the only path to 10.0. Te.* did
not add new things for the borrow checker to catch (which is
structurally correct), so the v6.0 plan is unchanged. **Get the
borrow checker in front of v6.0.**
