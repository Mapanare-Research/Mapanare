# Mapanare v3.41.0 — "Culebrita" (IO Foundation)

> Wire the existing C runtime into native binaries.
> mapanare_io.c has 49KB of TCP, TLS, crypto, regex, file I/O.
> It's just not linked. Fix that.

**Status:** DONE
**Breaking:** No
**Theme:** IO Foundation — link what's already written

---

## The Problem

`mapanare_core.c` is linked into native binaries. `mapanare_io.c` is not.
This means native binaries can print and do basic file read/write, but
cannot use TCP, TLS, regex, crypto, or extended file I/O — even though
all that code is already written and compiled.

There is also no `read_line()` function. You literally cannot read stdin.

---

## Checklist

### 1. Build System — Link mapanare_io.c

- [x] `scripts/build_stage1.py`: compile `mapanare_io.c` to `mapanare_io.o`
- [x] Add `mapanare_io.o` to the linker step (alongside `mapanare_core.o`)
- [x] Link flags: `-lssl -lcrypto` (or dlopen — already handled in mapanare_io.c)
- [x] Link flags: `-lpcre2-8` (or dlopen — already handled)
- [x] Verify with `nm mnc-stage1 | grep __mn_tcp` — symbols present
- [x] Update `.github/workflows/ci.yml` native job to compile `mapanare_io.c`
- [x] ASan + TSan on mapanare_io.c

### 2. Stdin — read_line()

- [x] Add `__mn_read_line` to `runtime/native/mapanare_core.c`
- [x] Add `__mn_read_line` to `mapanare_core.h`
- [x] Register `read_line` in `mapanare/types.py` BUILTIN_FUNCTIONS
- [x] Handle in `mapanare/semantic.py` — auto-registered via BUILTIN_FUNCTIONS
- [x] Emit call in `mapanare/emit_llvm_text.py`
- [x] Register in `mapanare/self/semantic.mn` (self-hosted compiler)

### 3. Fix Disabled File I/O

- [x] Add `__mn_file_append(path, content)` to `mapanare_core.c`
- [x] Add `__mn_dir_list_strings(path)` to `mapanare_core.c` — returns `MnList` of `MnString`
- [x] Enable `append_file` in `stdlib/fs.mn` using the new C function
- [x] Enable `list_dir` in `stdlib/fs.mn` using `__mn_dir_list_strings`
- [x] Enable `walk` built on working `list_dir`

### 4. LLVM Emitter — Declare IO Functions

- [x] Add to `_RUNTIME_FN_ATTRS` in `emit_llvm_text.py`:
  - `__mn_read_line`, `__mn_file_append`, `__mn_dir_list_strings`
  - `__mn_file_exists`, `__mn_file_remove`, `__mn_file_size`, `__mn_file_mtime`
  - `__mn_dir_create`, `__mn_dir_remove`, `__mn_file_rename`, `__mn_file_copy`
  - `__mn_realpath`, `__mn_tmpfile_path`
- [x] High-level builtins: `read_line`, `read_file`, `write_file`, `append_file`, `file_exists`, `list_dir`
- [x] IO functions auto-declared via `_ensure()` when referenced

### 5. Golden Tests

- [x] `tests/golden/34_file_io.mn` — read/write/append/exists/list_dir (35/35 pass)
- [x] `tests/golden/35_stdin.mn` — read_line + concat + print (35/35 pass)
- [x] Both pass through Python bootstrap AND mnc-stage1

### 6. Validation

- [x] 35/35 golden tests pass (bootstrap + stage1)
- [x] Native binary: `echo "Juan" | ./test35` → `Hello, Juan!`
- [x] Native binary: file I/O (write/read/append/list_dir) works
- [x] All IO symbols linked: `nm mnc-stage1 | grep __mn_tcp` confirmed

---

## Exit Criteria

```bash
# This program compiles and runs:
# file_demo.mn
fn main() {
    write_file("test.txt", "hello world")
    let content = read_file("test.txt")
    print(content)

    let name = read_line()
    print("Hello, " + name + "!")

    let files = list_dir(".")
    print(str(files.length()) + " files found")
}
```

```bash
echo "Juan" | mnc run file_demo.mn
# Output:
# hello world
# Hello, Juan!
# 15 files found
```
