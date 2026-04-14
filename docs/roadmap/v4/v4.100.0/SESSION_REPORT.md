# v4.100.0 Session Report — 2026-04-13

## Verdict

**Partial.** The root cause called out by the v4.99.0 panel
(tagged-pointer UB in `mn_tag_heap`) is structurally gone. The
downstream effect the panel attributed to it — garbled output from
`mnc-stage1` — persists and is confirmed to be a **different** bug,
present in the pristine v4.99.0 binary too. PLAN.md exit criteria
1–4 met; 5–9 not met. Release lands with an honest acknowledgment
rather than a claimed fix.

## What shipped

### Tagged-pointer UB removed (structural)

- `MnString` layout in `runtime/native/mapanare_core.h`:

  ```c
  typedef struct {
      const char *data;
      uint64_t    len     : 63;
      uint64_t    is_heap : 1;
  } MnString;
  ```

  Same 16 bytes as before; the heap flag rides in bit 63 of the
  second eightbyte via a C bitfield. The data pointer is now always
  a valid pointer, so LLVM's pointer-provenance analysis has nothing
  to exploit.

- Removed the three inline helpers `mn_tag_heap`, `mn_is_heap`,
  `mn_untag` from `mapanare_core.c`. Every construction site in
  the runtime sets `s.is_heap = 1` (for heap-allocated strings) or
  `s.is_heap = 0` (for `.rodata`/static). Every check site reads
  `s.is_heap` directly.

- Dropped the manual `(uintptr_t)ptr & ~1` untag idiom from
  `mapanare_internal.h`, `mapanare_io.c`, `mapanare_html.c`. The
  data pointer no longer needs masking.

- Python ctypes binding (`mapanare/bind.py`) updated: `_MnString`
  exposes `len` and `is_heap` via properties that decode the
  bitfield; the dereference path reads the pointer directly.

- Self-hosted emitter (`mapanare/self/emit_llvm.mn`): the one place
  that reads `.len` via `extractvalue { ptr, i64 }, 1` now masks
  bit 63 (`and i64 %raw, 9223372036854775807`). The Python
  bootstrap routes `.len` through `__mn_str_len`, which reads the
  bitfield on the C side and therefore already returns the masked
  length.

- `runtime/native/libmapanare_rt.a` rebuilt against the new runtime.
  `tests/bind/test_python_binding.py::test_greet_string_round_trip`
  passes — that test was the v4.25.0 regression canary for exactly
  this UB.

### Deviation from plan (intentional)

The plan said "add `int8_t is_heap` field to `MnString`". Doing
that grows the struct from 16 → 24 bytes and crosses the SysV
AMD64 register-vs-memory boundary — every call site passing or
returning `MnString` would need to switch to `byval`/`sret`
calling convention. Empirical confirmation with a minimal repro
(C callee compiled to `ptr sret(%MnString)`, LLVM IR caller using
`call { ptr, i64, i8 }` without the attribute): segfault on
return. Fixing this in the emitter would be a multi-phase rewrite
of the Python and self-hosted LLVM emitters, far outside a Phase A
release. The bitfield encoding is an equivalent fix for the
UB — the flag is no longer in a pointer field LLVM reasons about —
without the ABI cliff. The plan's risk register already flagged
"MnString layout change breaks ABI" as medium-likelihood /
high-impact; the bitfield is the mitigation.

## What did not ship

### mnc-stage1 at -O2 still produces corrupted output

Running `./mapanare/self/mnc-stage1 tests/golden/01_hello.mn`
yields output where every declaration line is prefixed with 16
bytes of garbage:

```
0a 11 1a 63 d1 11 7f 00  00 76 22 ea 7a b1 e0 4b b0
                                                  36 34 20 7d  | ...      ... 64 } |
```

The garbage is structured: the first 8 bytes of each block look
like user-space pointers (`0x00007f...`), the second 8 bytes
repeat across blocks — exactly the pattern of a 16-byte MnString
struct (`{ data, len }`) being memcpy'd into an output buffer
where the string's data bytes should be.

**This is not the bug the plan targeted.** Confirmed by stashing
every v4.100.0 change, rebuilding `mnc-stage1` from the pristine
v4.99.0 source, and observing the **same** 16-byte-prefix
corruption at both -O2 and -O0. The tagged-pointer UB was a real
bug (LLVM's provenance machinery is allowed to assume a
`const char *` with bit 0 set isn't a valid pointer), but it was
not the source of the garbled output the panel reported.

Plausible culprits for follow-up:

- The `List<String>` storage layout in the self-hosted compiler.
  Elements are stored by value (16 bytes each). If somewhere the
  element pointer (`&s` on the stack) is being written to the
  concat buffer instead of `s.data`, we'd see exactly this
  pattern.
- `__mn_str_concat` in the self-hosted emitter's emission path
  for concat chains. The runtime C `__mn_str_concat` is known-good
  (unit-tested by `test_greet_string_round_trip`), so the bug is
  more likely in emitted IR than in the runtime.
- The `join("\n", st.lines)` call that produces the final IR text.
  Bug plausibly in how the emitter builds or stores the list
  before the join.

Recommend v4.101.0 start by instrumenting `st.lines` push
order in the self-hosted emitter and diffing against the Python
bootstrap's accumulated lines for the same input. The bytes are
structured; the bug should fall out of an alignment check.

### Exit criteria

| # | Check | Status |
|---|---|---|
| 1 | `is_heap` field in `MnString` | ✅ (as bitfield) |
| 2 | `mn_tag_heap` removed | ✅ |
| 3 | `mn_is_heap` / `mn_untag` removed or replaced | ✅ |
| 4 | All callers updated | ✅ |
| 5 | `mnc-stage1` compiles with `-O2` | ✅ (compiles, output still garbled) |
| 6 | String output not garbled | ❌ (pre-existing bug) |
| 7 | Golden pass count recorded | ❌ (test runner blocked on #6) |
| 8 | Valgrind clean on string test | ⏸ (blocked on #6) |
| 9 | ASan clean on string test | ⏸ (blocked on #6) |

## Session data

- Runtime C files compile clean at -O2 with `-Wall -Werror`:
  `mapanare_core.c`, `mapanare_io.c`, `mapanare_html.c`,
  `mapanare_db.c`, `mapanare_runtime.c`.
- `scripts/build_stage1.py` links the new runtime into `mnc-stage1`
  successfully at -O2.
- `tests/bind/test_python_binding.py` (7 tests): all pass after
  rebuilding `libmapanare_rt.a`.
- Broader `pytest tests/` run showed 76 failures on a 5309-test
  corpus; most are pre-existing (black/ruff/mypy formatter drift
  flagged `59 files would be reformatted`, unrelated to v4.100.0)
  or dependent on the same self-hosted bug documented above.

## Decision for v4.101.0

Docket item #1 (tagged-pointer UB) is **partially closed**: the
structural UB is gone, but the observable downstream failure the
panel flagged requires a separate investigation. Recommend that
v4.101.0 either:

1. Diagnose the self-hosted output corruption directly (the 16-byte
   prefix pattern is a clear fingerprint), OR
2. Move on to docket item #2 (list indexing) as scheduled and tackle
   the self-hosted emitter bug in a focused release later.

Either is defensible; option (1) unblocks golden-test verification
earlier but option (2) keeps the panel docket moving.
