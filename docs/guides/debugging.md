# Debugging Mapanare Programs with gdb and lldb

This guide shows how to debug compiled Mapanare programs using standard native debuggers. Mapanare emits DWARF debug information when compiled with the `-g` flag, so gdb and lldb can map machine code back to your `.mn` source lines.

**Prerequisites:** gdb (Linux/WSL) or lldb (macOS). LLVM toolchain installed.

---

## 1. Compiling with Debug Info

Pass `-g` to emit DWARF metadata in the generated LLVM IR:

```bash
# Emit IR with debug info
mapanare emit-llvm -g myprogram.mn -o myprogram.ll

# Compile to native binary (keep debug info with -g)
llvm-as myprogram.ll -o myprogram.bc
llc -filetype=obj -relocation-model=pic myprogram.bc -o myprogram.o
clang -g myprogram.o -L runtime/native -lmapanare_rt -lm -lpthread -ldl -o myprogram
```

The `-g` flag adds `DICompileUnit`, `DISubprogram`, and `DILocation` metadata to every function and instruction. Without `-g`, the binary has no source-level mapping and the debugger can only show assembly.

---

## 2. Starting a Debug Session

### gdb (Linux/WSL)

```bash
gdb ./myprogram
```

### lldb (macOS)

```bash
lldb ./myprogram
```

Both debuggers will load the DWARF sections and recognize your `.mn` source file.

---

## 3. Setting Breakpoints

### By function name

Mapanare functions are emitted with their source names:

```
(gdb) break main
(gdb) break fib
(gdb) break compute_sum
```

```
(lldb) breakpoint set --name main
(lldb) breakpoint set --name fib
```

### By source line

If the binary was compiled with `-g`:

```
(gdb) break myprogram.mn:5
```

```
(lldb) breakpoint set --file myprogram.mn --line 5
```

### By condition

```
(gdb) break fib if n == 10
```

---

## 4. Running and Stepping

### Run the program

```
(gdb) run
(gdb) run arg1 arg2
```

```
(lldb) run
(lldb) run arg1 arg2
```

### Step through code

| Action | gdb | lldb |
|--------|-----|------|
| Step into (next source line) | `step` / `s` | `step` / `s` |
| Step over (skip function calls) | `next` / `n` | `next` / `n` |
| Step out (finish current function) | `finish` | `finish` |
| Continue to next breakpoint | `continue` / `c` | `continue` / `c` |

---

## 5. Inspecting Variables

Mapanare variables are emitted as LLVM allocas with their source names:

```
(gdb) print x
(gdb) print result
(gdb) info locals
```

```
(lldb) frame variable
(lldb) frame variable x
(lldb) p x
```

### Strings

Mapanare strings are `{ptr, i64}` structs (pointer + length). To inspect:

```
(gdb) print *(char**)&msg
(gdb) x/s *(char**)&msg
```

### Structs

Struct fields are accessible by index since LLVM lowers them to unnamed struct types:

```
(gdb) print point
(gdb) print point.x
```

---

## 6. Backtraces

When a program crashes, the backtrace shows the call stack:

```
(gdb) bt
```

```
(lldb) bt
```

Example output:

```
#0  fib (n=0) at fib.mn:3
#1  fib (n=1) at fib.mn:5
#2  fib (n=2) at fib.mn:5
#3  main () at fib.mn:9
```

With `-g`, each frame shows the `.mn` filename and line number.

---

## 7. Debugging Async Code

Async functions are lowered to LLVM coroutines. After CoroSplit, each async function becomes three functions:

| Function | Purpose |
|----------|---------|
| `compute` | Ramp function (runs until first suspend) |
| `compute.resume` | Resume function (dispatches to continuation) |
| `compute.destroy` | Cleanup function (frees coroutine frame) |

### Setting breakpoints in async functions

```
(gdb) break compute
(gdb) break compute.resume
```

### Inspecting coroutine state

The coroutine frame contains spilled variables and a suspend index:

```
(gdb) print *(struct compute.Frame*)handle
```

The suspend index (field 2, type `i8`) indicates which `await` point the coroutine is paused at:
- 0 = before first `await`
- 1 = after first `await`
- etc.

---

## 8. Crash Debugging with Valgrind

Valgrind detects memory errors in compiled Mapanare programs:

```bash
valgrind --leak-check=full ./myprogram
```

Common findings:
- **Invalid read/write**: usually a struct field access at the wrong offset. Use `ir_doctor.py structmap` to map byte offsets to field names.
- **Uninitialised value**: a variable used before assignment. Check the alloca initialization in the IR.
- **Definitely lost**: heap memory not freed. Check drop glue emission for the function.

### Mapping crash offsets to struct fields

The `ir_doctor.py` tool maps valgrind byte offsets to Mapanare struct fields:

```bash
python scripts/ir_doctor.py valgrind-map ./myprogram test.mn
python scripts/ir_doctor.py structmap MyStruct --offset 24
```

---

## 9. Tips and Tricks

### Print LLVM IR for a function

```bash
python scripts/ir_doctor.py extract main.ll my_function
```

### Check if your IR is valid

```bash
llvm-as myprogram.ll -o /dev/null
```

If `llvm-as` reports errors, the emitter produced invalid IR. File a bug.

### Compile with optimizations disabled

For easier debugging, compile at `-O0`:

```bash
mapanare emit-llvm -g -O0 myprogram.mn -o myprogram.ll
```

`-O0` disables constant folding, DCE, and copy propagation, so every variable and expression is visible in the debugger.

### Use the integration test harness

The v4.77.0 integration harness runs your program through the full pipeline:

```bash
pytest tests/integration/test_golden_pipeline.py -k "my_test" -v
```

This catches IR validation errors, optimization failures, link errors, and runtime crashes in one command.

---

## See Also

- [SPEC.md](../SPEC.md) section 29 for async/await formal semantics
- [DWARF Implementation](../roadmap/v4/v4.62.0/) for the Arc 7 DWARF debug info work
- `python scripts/ir_doctor.py --help` for all IR diagnostic tools
- `python scripts/ir_doctor.py valgrind-map --help` for crash analysis
