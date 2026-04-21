# Debugging Mapanare Programs

> **v4.116.0 correction.** Earlier editions of this guide opened with
> *"Mapanare emits DWARF debug information when compiled with the `-g`
> flag"*. That is not true today and was flagged by the v4.26.0 panel
> (Rattler #4). **DWARF emission is deferred to v5.x**; see SPEC §21.3.
> Until then, `-g` is accepted for forward compatibility but the
> emitted IR and linked binary contain no DWARF metadata; `gdb` / `lldb`
> will show only machine-level frames for Mapanare functions. This guide
> now focuses on what actually works: valgrind, AddressSanitizer,
> ThreadSanitizer, `ir_doctor.py`, Culebra, and the integration-test
> harness.

**Prerequisites:**

- `clang` and LLVM 18.x (for `llvm-as`, `opt`, `llc`)
- `valgrind` (Linux / WSL — primary memory-debugging tool)
- `gdb` or `lldb` (for machine-level inspection only, until DWARF lands)
- Python 3.11+ (for `ir_doctor.py`)
- Optional: [Culebra](https://github.com/Mapanare-Research/Culebra) for IR-level diagnostics

---

## 1. The Native-Binary Pipeline

Every Mapanare program becomes a native ELF/Mach-O binary via:

```bash
# Emit LLVM IR
python3 -m mapanare emit-llvm program.mn -o /tmp/program.ll

# Link against the C runtime
clang /tmp/program.ll \
      -L runtime/native -lmapanare_rt \
      -lpthread -lm -ldl \
      -o /tmp/program

# Run
/tmp/program
```

For debugging, compile the **runtime** with `-g` (the default
`runtime/native/Makefile` already does). The Mapanare side has no
DWARF, but runtime frames in crash backtraces will be fully symbolic.

For optimised-out variable inspection, drop `-O0`:

```bash
clang -O0 /tmp/program.ll -L runtime/native -lmapanare_rt -lpthread -lm -ldl -o /tmp/program
```

---

## 2. Valgrind — Primary Memory-Error Tool

Valgrind is the primary memory-debugging tool for Mapanare today. It
does not need DWARF to be useful: it reports byte offsets into the
struct or heap object where the error occurred.

```bash
valgrind --leak-check=full --track-origins=yes /tmp/program
```

Common findings:

| Finding | Usual cause | What to do |
|---|---|---|
| **Invalid read/write** | Struct field access at the wrong offset | Map offset to field with `ir_doctor.py valgrind-map` |
| **Uninitialised value** | Alloca used before store | Check the alloca's first use in the IR |
| **Conditional jump depends on uninitialised** | Same as above, but inside a branch | Same fix |
| **Definitely lost** | Heap memory without a free | Check drop-glue emission in the emitter |
| **Mismatched free / delete / delete[]** | Arena-allocated memory freed with `free` | Arena-backed lists and strings use `__mn_arena_free`, not `free` |

### Mapping valgrind offsets to Mapanare struct fields

When valgrind reports `Invalid read of size 8 at 0x... inside foo+0x20`,
`ir_doctor.py` can resolve the 0x20 offset to a named field of a
Mapanare struct:

```bash
python scripts/ir_doctor.py valgrind-map ./mapanare/self/mnc-stage1 tests/golden/07_enum_match.mn
python scripts/ir_doctor.py structmap LowerState --offset 176
python scripts/ir_doctor.py structmap             # list all structs + sizes
```

See [`scripts/ir_doctor.py --help`](../../scripts/ir_doctor.py) for the
full command surface.

---

## 3. AddressSanitizer (ASan) — Fast Heap-UAF Detector

ASan is orders of magnitude faster than valgrind for heap
use-after-free and buffer overflow detection. It is wired into the
`sanitizers.yml` CI workflow as of v4.105.0.

```bash
# Rebuild the runtime with ASan
make -C runtime/native clean
CFLAGS="-fsanitize=address -fno-omit-frame-pointer -g" make -C runtime/native libmapanare_rt_asan.a

# Link against the ASan runtime
clang -fsanitize=address /tmp/program.ll \
      -L runtime/native -lmapanare_rt_asan \
      -lpthread -lm -ldl \
      -o /tmp/program_asan

# Run
/tmp/program_asan
```

ASan reports heap-UAF, global-buffer-overflow, and stack-buffer-overflow
with the runtime frames fully symbolic (the runtime is compiled with
`-g`). The Mapanare side will still appear as machine-level frames.

## 4. ThreadSanitizer (TSan) — Data-Race Detector

TSan detects data races between threads, which matter for agent-heavy
and async programs.

```bash
CFLAGS="-fsanitize=thread -g" make -C runtime/native libmapanare_rt_tsan.a
clang -fsanitize=thread /tmp/program.ll \
      -L runtime/native -lmapanare_rt_tsan \
      -lpthread -lm -ldl \
      -o /tmp/program_tsan
/tmp/program_tsan
```

As of v4.105.0, the three async goldens (`55`/`56`/`57`) are TSan-clean.
If you add an async or agent-heavy program and TSan fires, file it
against the relevant `Vg.*` or `As.*` docket items (see the carry-
forward ledger).

---

## 5. IR-Level Diagnostics with `ir_doctor.py`

`scripts/ir_doctor.py` is the primary per-function diagnostic for
self-hosted compiler bugs. It runs `llvm-as` validation, detects
structural pathologies (ALLOCA_ALIAS, EMPTY_SWITCH, MISSING_PERCENT,
DUPLICATE_CASE, PHI_UNDEF_REF, RET_TYPE_MISMATCH, LOOP_PUSH), and tracks
baselines so reruns show delta.

Frequently useful commands:

```bash
# Validate and audit the self-hosted compiler IR
python scripts/ir_doctor.py audit mapanare/self/main.ll

# Per-function metrics table, top 15
python scripts/ir_doctor.py --top 15 table mapanare/self/main.ll

# Extract one function's IR
python scripts/ir_doctor.py extract mapanare/self/main.ll emit_fn

# Compare bootstrap and stage1 output on one golden
python scripts/ir_doctor.py diff tests/golden/07_enum_match.mn

# Validate string-constant byte counts
python scripts/ir_doctor.py strings mapanare/self/main.ll

# Run valgrind on a crash, auto-map offsets to struct fields
python scripts/ir_doctor.py valgrind tests/golden/11_closure.mn
```

Full help: `python scripts/ir_doctor.py --help`.

---

## 6. Template-Driven Diagnostics with Culebra

Culebra (v2.0.0) runs 49 templates across ABI, IR, Binary, Bootstrap,
and C categories against `.ll` and `.c` files. The IR templates catch
known pathologies before they reach a test run; the C templates cover
generated-C output from `emit_c.py`.

```bash
# Full scan with autofix preview
culebra scan mapanare/self/main.ll --autofix --dry-run

# Triage findings (groups by root cause, dedup)
culebra triage mapanare/self/main.ll --brief

# Per-function metric comparison between stage outputs
culebra compare stage1.ll stage2.ll --metric calls

# Baseline + diff (for iterative fixing)
culebra baseline save mapanare/self/main.ll
culebra baseline diff mapanare/self/main.ll

# Per-session debugging journal
culebra journal add "fixing PHI-zeroinit in lower_fn" --action bug --tags phi
culebra journal show
```

See the `culebra-scan` skill (`/culebra-scan`) for the repo-standard
entry point, and [Culebra on crates.io](https://crates.io/crates/culebra) for the full command reference.

---

## 7. Debugging Async Code

Async functions lower to LLVM switched-resume coroutines. After
CoroSplit, each async fn becomes three LLVM functions:

| Function | Purpose |
|----------|---------|
| `foo` | Ramp — runs until first suspend |
| `foo.resume` | Resume — dispatches to the continuation for each `await` point |
| `foo.destroy` | Cleanup — frees the coroutine frame |

Without DWARF, you debug async programs by:

1. **valgrind / ASan** for memory errors inside the coroutine frame.
2. **`culebra extract`** to pull the ramp and resume IR for a given async fn.
3. **Printf-style logging** inside the async body — `__mn_file_write` works
   inside `async fn`, so you can log to a file from any `await` stage.

The coroutine frame prefix (from v4.113.0) is documented in
`runtime/native/mapanare_runtime.c:1539`:

```c
typedef struct {
    void (*resume_fn)(void*);
    void (*destroy_fn)(void*);
} mn_coro_frame_prefix_t;
```

`mn_coro_is_done(handle)` returns true when `handle[0] == NULL` — LLVM's
final-suspend representation. Inspecting this from a debugger requires
casting the opaque pointer to `mn_coro_frame_prefix_t*` manually.

---

## 8. Machine-Level `gdb` / `lldb` (Limited Without DWARF)

With no DWARF for Mapanare functions, source-level breakpoints by line
do not work. You can still:

### Break on a Mapanare function by LLVM name

LLVM exports Mapanare functions with their source name, so:

```
(gdb) break main
(gdb) break fib
(gdb) run
```

will stop at the native entry point. Variables appear as raw registers
and stack slots; there is no `print x` for Mapanare locals until DWARF
lands.

### Backtraces

Backtraces show function names for Mapanare-defined functions, and full
symbolic frames for runtime frames (the C runtime is built with `-g`):

```
(gdb) bt
#0  __mn_list_push_rc (list=0x..., val=...) at mapanare_runtime.c:2134
#1  fib () at /tmp/program   <-- no file:line without DWARF
#2  main () at /tmp/program
```

When a Mapanare frame is implicated, fall back to:

- `ir_doctor.py extract` the function's IR
- `culebra extract` the same, with syntax highlighting
- Valgrind for memory errors
- Printf-style logging

---

## 9. Integration Test Harness

The v4.77.0 integration harness runs a program through the full pipeline
— emit-llvm → llvm-as → opt → llc → clang → run — and catches IR
validation, optimisation, link, and runtime errors in one command.

```bash
pytest tests/integration/test_golden_pipeline.py -k "my_test" -v
```

The v4.104.0 ship added `llvm-as` as a hard gate: any emitter change
that produces IR `llvm-as` rejects will fail this test suite before CI
runs.

---

## 10. When to Use What

| Symptom | Try first |
|---|---|
| Segfault or invalid read/write | `valgrind --track-origins=yes` |
| Heap-UAF suspected | ASan build |
| Race condition / thread hang | TSan build |
| Wrong output but no crash | Integration harness, `ir_doctor.py diff` |
| IR `llvm-as` rejects | `ir_doctor.py audit`, then `culebra scan` |
| Self-hosted compiler crash on one file | `ir_doctor.py valgrind-map <file>` |
| Pre-existing bug suspected | `culebra baseline diff` against last known good |
| Async-specific issue | Printf logging + `culebra extract fn.resume` |

---

## See Also

- [SPEC.md §21.3](../SPEC.md#213-debug-info-dwarf--deferred-to-v5x) — DWARF deferral rationale
- [SPEC.md §29](../SPEC.md#29-futures-and-asyncawait) — async/await semantics
- [`docs/guides/async.md`](async.md) — async mental model
- [`docs/cookbook/async.md`](../cookbook/async.md) — async recipes with native compilation
- `python scripts/ir_doctor.py --help` — all IR diagnostics
- `culebra --help` — all Culebra commands
- `tests/integration/test_golden_pipeline.py` — end-to-end pipeline harness (v4.77.0+)
- `runtime/native/mapanare_runtime.c` — the C runtime (built with `-g` by default)
