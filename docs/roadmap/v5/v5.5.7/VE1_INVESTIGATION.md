# Ve.1 Investigation — v5.5.7 (2026-04-24)

> **Verdict:** Real heap-buffer-overflow bug in `parse_fn_body`
> (self-hosted parser). Predates async work. Not fixable in
> v5.5.7 scope without parser surgery — defer to a dedicated
> micro-release.

---

## Current state at v5.5.7 HEAD

```
[Stage 0] mnc-stage1: 5,446,816 bytes — OK
[Stage 1] stage1 → stage2.ll: 194,799 lines, llvm-as OK
          mnc-stage2 link: 3,913,296 bytes — OK
[Stage 2] mnc-stage2 mnc_all.mn → stage3.ll: 0 lines (segfault)
          exit code: 139 (SIGSEGV)
```

Same surface as v5.4.4 → v5.5.6: stage1 + stage2.ll clean,
stage3.ll empty.

Stack ulimit raised to 64 MB and unlimited — does not change
the outcome (rules out pure deep-recursion).

---

## Crash characterisation

`strace -f` on `mnc-stage2 mnc_all.mn`:

```
SIGSEGV {si_signo=SIGSEGV, si_code=SEGV_MAPERR,
         si_addr=0x7ffecc507fd8}
```

Address sits in the stack region (0x7ffe...) but the access
is to an unmapped page. Combined with the negative ulimit
result, this is a **wild-pointer dereference**, not a stack
overflow.

---

## Reproducer minimisation

| Input | mnc-stage2 outcome |
|---|---|
| `mapanare/self/mir.mn` (1.0K LOC) | exit 1 (no crash) |
| `mapanare/self/lower.mn` (3.6K LOC) | **segfault** |
| `mapanare/self/emit_llvm.mn` (4.8K LOC) | segfault |
| `mapanare/self/mnc_all.mn` (full 14K LOC) | segfault |

`lower.mn` is the smallest crashing input. Stable repro for
forensics.

---

## Root-cause forensics (valgrind on `mnc-stage2 lower.mn`)

```
Invalid write of size 8
   at 0x419DC6: parse_fn_body
   by 0x4197F7: parse_fn_params
   by 0x41968F: parse_fn_def
   by 0x4179AC: parse_definition
   by 0x4171F4: parse
   by 0x794C46: compile
   by 0x7989EC: mn_main
 Address 0x7a3c980 is 0 bytes after a block of size 256 alloc'd
   at malloc
   by 0x419D42: parse_fn_body
   ...

Total: 154,355 errors from 42 contexts
       definitely lost: 47.4 MB / 577K blocks
```

**The bug:** `parse_fn_body` allocates a 256-byte block
(likely a `List<X>` backing storage of 32 × 8-byte pointers),
then writes 8 bytes immediately past the end of it. Classic
off-by-one or missing capacity-grow path on push.

The 256 = 32 × 8 strongly suggests the runtime's `List`
default-initial-capacity is 32, and the push path doesn't
realloc before the 33rd push. v3.37.0 ("Araguato: safe list
growth") supposedly fixed list growth, but the bug remains
visible at scale. Possibilities:

1. v3.37.0 fixed *one* call site; another path still writes
   directly into the backing array without going through the
   safe-grow helper.
2. The fix landed but a later refactor reverted it on this
   path.
3. The 256-byte block is a fixed-capacity buffer (not a
   growable List) that's structurally wrong.

The 154K errors / 42 contexts indicates the bug fires from
many call sites, all routing through `parse_fn_body` and its
descendants. This is consistent with "every fn definition
parsed past the 32nd in any input ≥ ~3.6K LOC".

---

## Comparison to v5.4.4 original notes

v5.4.4 SESSION_REPORT noted:
> "Ve.1 regressed: stage2.ll llvm-as OK but mnc-stage2
> segfaults before stage3 emission (previously crashed on
> teardown with non-empty stage3)."

v5.5.7's stage2.ll:
- 194,799 lines (vs v5.4.4 ~163K)
- llvm-as OK (preserved)
- 907 defines (+1 vs v5.5.6 = `module_has_async`; +1 vs v5.4.4 baseline)

The bug character has not shifted between v5.4.4 and v5.5.7.
Same call chain, same offset class, same 256-byte buffer.

---

## Classification (per PLAN.md §7.3)

| Category | Match? |
|---|---|
| (a) Same bug still open | **YES — confirmed unchanged** |
| (b) Bug has shifted | No |
| (c) Fixable in v5.5.7 scope | **No — requires parser/list-growth surgery** |
| (d) Fixable BY async work | **No — orthogonal to coroutines** |
| (e) Unrelated, separate arc | **YES — list-growth or parse_fn_body off-by-one** |

---

## Recommendation

**Defer to a dedicated v5.5.7.1 (or v5.7.x parser-cleanup arc).**

Required work (~1 session):

1. Add ASan instrumentation to mnc-stage1 and trace the
   first invalid write — identify whether the 256-byte block
   is a `List<Decorator>`, `List<Param>`, or a different
   container.
2. Audit the runtime's `__mn_list_push` (or equivalent) for
   the capacity-grow contract. Compare against the Python
   bootstrap's `list.append`.
3. Either (a) fix the realloc bug in `mapanare_runtime.c`,
   or (b) fix the parser to use a known-safe list helper.
4. Validate by re-running `verify_fixed_point.sh --keep` and
   confirming stage3.ll is non-empty + matches stage2.ll.

This work is bounded (one bug, one surgery) and tractable —
just not v5.5.7's stabilization scope.

---

## What v5.5.7 ships re: Ve.1

- This investigation report.
- No code change.
- `docs/known_issues.md` Ve.1 entry preserved.
- Risk register entry: open since v5.4.4, root cause
  identified, fix deferred.

stage2.ll llvm-as remains the available gate. stage3
verification unblocks once the parser bug is fixed.
