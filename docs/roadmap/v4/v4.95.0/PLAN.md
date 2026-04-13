# Mapanare v4.95.0 — String Allocation Pathology Fix

> **Arc 13 release 4.** Reviewer Mamba flagged the O(n^2) string
> concatenation pathology in the v4.51.0 panel: repeated
> `s = s + chunk` in a loop allocates N intermediate strings, each
> copied from the previous. This shows up prominently in the AI stdlib
> (`stdlib/ai/llm.mn`, `stdlib/ai/embedding.mn`) where JSON request
> bodies are built by string concatenation. v4.95.0 ships
> `StringBuilder` in the C runtime, wires it into the lowerer for
> automatic loop-concat optimization, and refactors the AI stdlib
> to eliminate the pathology.

**Status:** DONE
**Breaking:** No
**Prerequisite:** v4.94.0
**Delta review:** No
**Full panel:** No (v4.96.0)
**Estimated work:** 1 sprint
**Theme:** Kill the O(n^2) string concat. StringBuilder in the runtime, automatic detection in the lowerer.

---

## Scope

The pathology is simple and devastating: every `s = s + x` in a loop
creates a new string of length `len(s) + len(x)`, copies `len(s)` bytes
from the old string, copies `len(x)` bytes from x, and frees (or
abandons to the arena) the old string. After N iterations, total bytes
copied = O(N^2). For the AI stdlib's JSON body builder with 50+ fields,
this means ~1,250 unnecessary string copies per LLM API call.

The fix has three layers:

1. **C runtime `StringBuilder`** — an exponential-growth byte buffer.
   Start at 64 bytes, double on overflow. Append is amortized O(1).
   `sb_to_string()` produces a final immutable Mapanare string. Total
   bytes copied = O(N) for N appends.

2. **MIR lowerer optimization** — detect `str = str + x` patterns inside
   loops and replace the sequence with StringBuilder operations:
   `sb_create()` before the loop, `sb_append(x)` inside the loop,
   `sb_to_string()` after the loop. This is a peephole optimization in
   `lower.py` (or `mir_opt.py`), not a language-level feature.

3. **Explicit `StringBuilder` type** — expose `StringBuilder` in the
   stdlib for cases where the automatic detection misses a pattern or
   the programmer wants explicit control. Methods: `new()`, `append(s)`,
   `to_string()`.

4. **AI stdlib refactoring** — rewrite the JSON body builders in
   `stdlib/ai/llm.mn` and `stdlib/ai/embedding.mn` to use StringBuilder.
   This is the primary user-facing impact: LLM API calls become faster.

---

## Phase 1 — Audit string concat patterns

- [ ] Grep the entire codebase for `str + str` in loops:
  - `stdlib/ai/llm.mn` — JSON body building for chat/completion API calls
  - `stdlib/ai/embedding.mn` — JSON body building for embedding API calls
  - `stdlib/ai/rag.mn` — context assembly
  - Any other stdlib or example files with loop-based string building
- [ ] Document each instance with line numbers, estimated loop iteration count, and severity
- [ ] Write findings to `docs/roadmap/v4/v4.95.0/STRING_AUDIT.md`

## Phase 2 — StringBuilder in C runtime

- [ ] Add to `runtime/native/mapanare_core.c`:
  ```c
  typedef struct mapanare_string_builder {
      char    *buf;       // heap-allocated buffer
      int64_t  len;       // current content length
      int64_t  cap;       // allocated capacity
  } mapanare_string_builder_t;

  mapanare_string_builder_t* mapanare_sb_create(void);
  void mapanare_sb_append(mapanare_string_builder_t *sb, const char *str, int64_t len);
  mapanare_string_t mapanare_sb_to_string(mapanare_string_builder_t *sb);
  void mapanare_sb_destroy(mapanare_string_builder_t *sb);
  ```
- [ ] Initial capacity: 64 bytes. Growth: double on overflow (amortized O(1) append).
- [ ] `sb_to_string()` transfers ownership of the buffer (no copy if buffer is the right size) or copies to a right-sized allocation.
- [ ] `sb_destroy()` frees the buffer (for error paths where `to_string()` is never called).
- [ ] C-level unit tests:
  - Append 10,000 short strings, verify final string content and length
  - Verify no memory leaks (valgrind)
  - Verify exponential growth (capacity after N appends is O(N), not O(N^2))

## Phase 3 — Wire StringBuilder into MIR lowering

- [ ] In `mapanare/lower.py` or `mapanare/mir_opt.py`, add a loop-concat detection pass:
  - Pattern: `%s = call @mapanare_string_concat(%s, %x)` inside a loop where `%s` is the loop-carried variable
  - Replacement: `sb = sb_create()` before loop, `sb_append(sb, %x)` inside loop, `%s = sb_to_string(sb)` after loop
  - Emit the StringBuilder calls as MIR `CALL` instructions targeting the C runtime functions
- [ ] Alternatively: if automatic detection is too fragile, expose `StringBuilder` as a builtin type in the semantic pass and let the programmer opt in
- [ ] Add MIR-level test: verify the optimization fires on a simple loop-concat pattern
- [ ] Add MIR-level test: verify the optimization does NOT fire on non-loop string concat (single `a + b` should still be a regular concat)

## Phase 4 — Refactor AI stdlib

- [ ] `stdlib/ai/llm.mn`:
  - Replace JSON body building loops with StringBuilder
  - `fn build_chat_body(messages: List<Message>, model: String) -> String` — use `sb.append()` for each field
  - Verify output is byte-identical to the old implementation (JSON format unchanged)
- [ ] `stdlib/ai/embedding.mn`:
  - Same treatment for embedding request body building
- [ ] `stdlib/ai/rag.mn`:
  - If context assembly uses loop concat, refactor
- [ ] Integration test: verify API request bodies are identical before/after refactoring

## Phase 5 — Benchmark before/after

- [ ] Create `benchmarks/string/string_concat_loop.mn`:
  - Concatenate "hello" 10,000 times in a loop using `s = s + "hello"`
  - Print final length (50,000) and wall time
- [ ] Run the benchmark on the OLD code (before StringBuilder) — record as baseline
- [ ] Run the benchmark on the NEW code (with StringBuilder optimization or explicit StringBuilder) — record as optimized
- [ ] Compute speedup ratio. Target: >= 5x improvement on 10K iterations.
- [ ] Also benchmark with 100K iterations to verify O(N) vs O(N^2) scaling
- [ ] Record results in `benchmarks/string/STRING_RESULTS.md`

## Phase 6 — LOW sweep + closeout

- [ ] Grep for `TODO(v4.95)` or unfinished items
- [ ] Golden suite: 59/59 pass
- [ ] `make test` passes — no regressions
- [ ] `make lint` passes
- [ ] Standard closeout: `VERSION`, `CHANGELOG.md`, `SESSION_REPORT.md`

---

## Exit criteria (9 items)

| # | Check | Evidence |
|---|---|---|
| 1 | `mapanare_sb_create/append/to_string/destroy` exist in C runtime | `grep mapanare_sb_create runtime/native/mapanare_core.c` |
| 2 | StringBuilder C unit tests pass (10K appends, no leaks) | valgrind log |
| 3 | Loop-concat optimization fires in lowerer OR `StringBuilder` type exposed | MIR test output |
| 4 | `stdlib/ai/llm.mn` refactored — no O(n^2) concat in loops | code diff |
| 5 | `stdlib/ai/embedding.mn` refactored | code diff |
| 6 | Benchmark shows >= 5x improvement on 10K string concat loop | `STRING_RESULTS.md` |
| 7 | Benchmark shows O(N) scaling (100K iterations < 10x cost of 10K iterations) | `STRING_RESULTS.md` |
| 8 | Golden 59/59 pass | `python scripts/test_native.py` |
| 9 | `make test` + `make lint` pass | CI log |

---

## What this release does NOT do

- **Rope data structure** — StringBuilder uses a flat buffer with
  exponential growth. A rope (tree of string fragments) is an
  alternative for very large strings but adds complexity. Future work
  if StringBuilder proves insufficient.
- **String interning changes** — the string intern table
  (`mapanare_intern_string`) is unchanged. StringBuilder produces
  regular strings, not interned strings.
- **Regex or format strings** — no `fmt!()` or string interpolation.
  Those are language features, not runtime optimizations.
- **Self-hosted emitter changes** — `emit_llvm.mn` is not updated.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Automatic loop-concat detection is too fragile (misses patterns or fires incorrectly) | medium | medium | Ship the explicit `StringBuilder` type as fallback. Refactor AI stdlib by hand regardless. Automatic detection is a nice-to-have. |
| StringBuilder buffer growth wastes memory on small strings | low | low | Initial capacity is 64 bytes — small strings never touch StringBuilder. The optimization only fires in loops. |
| `sb_to_string()` copies the buffer (defeating the purpose) | low | medium | Transfer ownership when possible: if `sb.len == sb.cap`, the buffer IS the string. Otherwise, realloc to right size. |
| AI stdlib refactoring changes JSON output format | low | high | Byte-level comparison test: old output vs new output must match exactly. |
| Performance regression for non-loop string concat | low | medium | The optimization only fires for loop-carried `str = str + x`. Regular concat is unchanged. Benchmark single `a + b` to verify. |

---

## After v4.95.0

v4.96.0 is the Arc 13 panel release. The 7 reviewers grade the full arc: real suspension (v4.92.0), multi-threaded scheduler (v4.93.0), async benchmarks (v4.94.0), and the string fix (v4.95.0). Special attention from Mamba on the string pathology fix and scheduler C quality, and from Viper on memory safety across the real suspension and multi-threaded paths.
