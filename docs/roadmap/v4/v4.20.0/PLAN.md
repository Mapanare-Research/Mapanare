# Mapanare v4.20.0 — Auto-Generated FFI Bindings

> One command generates Python, TypeScript, and Go bindings from .mn function signatures.

**Status:** DONE
**Breaking:** No
**Prerequisite:** v4.19.0

---

## The Goal

Make Mapanare libraries callable from other languages without writing glue
code. `mapanare bind --lang python module.mn` reads function signatures,
types, and struct definitions from `.mn` source and generates:

- **Python:** C extension module (`.so` / `.pyd`) via cffi or ctypes
- **TypeScript:** Type declarations (`.d.ts`) + WASM loader
- **Go:** cgo bindings (`.go` file with `// #cgo` directives)

This leverages two existing backends:
- **C backend** (`emit_c.py`) — generates the shared library that Python and Go call
- **WASM backend** (`emit_wasm.py`) — generates the `.wasm` module that TypeScript loads

The binding generator reads the AST (not IR), so it has full access to type
names, doc comments, and function signatures.

---

## Phase 1: Binding generator framework

- [ ] New module: `mapanare/bind.py`
- [ ] CLI: `mapanare bind --lang <python|ts|go> [--output DIR] source.mn`
- [ ] Parse the `.mn` file to AST
- [ ] Extract public API: functions, structs, enums (skip `_`-prefixed names)
- [ ] Build a `BindingSpec` dataclass: functions (name, args, return type),
      types (structs with fields, enums with variants)
- [ ] Wire into `cli.py` as a new subcommand

## Phase 2: Type mapping

- [ ] Define type mappings for each target language:

  | Mapanare | Python | TypeScript | Go |
  |----------|--------|------------|-----|
  | Int | int | number | int64 |
  | Float | float | number | float64 |
  | Bool | bool | boolean | bool |
  | String | str | string | string |
  | List<T> | list[T] | T[] | []T |
  | Map<K,V> | dict[K,V] | Map<K,V> | map[K]V |
  | Option<T> | T \| None | T \| null | *T |
  | Result<T,E> | T (raises on Err) | T (throws on Err) | (T, error) |
  | Struct | dataclass | interface | struct |
  | Enum | IntEnum | union type | iota const |

- [ ] Handle nested types recursively
- [ ] Handle generic types (List<List<Int>> etc.)

## Phase 3: Python bindings

- [ ] Compile `.mn` to shared library via C backend: `.mn -> .c -> .so`
- [ ] Generate cffi binding file with:
  - C function declarations (from the generated C header)
  - Python wrapper functions with type hints
  - Struct wrappers as dataclasses
  - Enum wrappers as IntEnum
  - Automatic string conversion (Mapanare String <-> Python str)
  - Result type: return value on Ok, raise exception on Err
- [ ] Generate `setup.py` / `pyproject.toml` for pip installation
- [ ] Test: compile `examples/bind/math_lib.mn`, call from Python
- [ ] Add test: `tests/bind/test_python_binding.py`

## Phase 4: TypeScript bindings

- [ ] Compile `.mn` to WASM via WASM backend: `.mn -> .wat -> .wasm`
- [ ] Generate `.d.ts` type declarations matching the API
- [ ] Generate WASM loader (`loader.ts`):
  - Instantiate WASM module
  - Memory management (allocate/free strings across boundary)
  - Async wrapper for functions that return Stream
- [ ] Generate `package.json` for npm
- [ ] Test: compile `examples/bind/math_lib.mn`, call from TypeScript
- [ ] Add test: `tests/bind/test_ts_binding.ts` (run via `npx tsx`)

## Phase 5: Go bindings

- [ ] Compile `.mn` to shared library via C backend: `.mn -> .c -> .so`
- [ ] Generate `.go` file with cgo directives:
  - `// #cgo LDFLAGS: -L. -lmodule`
  - `// #include "module.h"`
  - Go wrapper functions with proper types
  - String conversion (Go string <-> C string <-> Mapanare String)
  - Error handling: Result maps to Go's `(T, error)` pattern
- [ ] Test: compile `examples/bind/math_lib.mn`, call from Go
- [ ] Add test: `tests/bind/test_go_binding_test.go`

## Phase 6: Documentation and examples

- [ ] `examples/bind/math_lib.mn` — simple math functions for binding demo
- [ ] `examples/bind/data_types.mn` — structs, enums, Option, Result
- [ ] CLI help: `mapanare bind --help` with examples
- [ ] Update `docs/SPEC.md` with FFI binding section

---

## Exit Criteria

| Check | Required |
|-------|----------|
| `mapanare bind --lang python` generates working binding | YES |
| `mapanare bind --lang ts` generates working binding | YES |
| `mapanare bind --lang go` generates working binding | YES |
| Type mappings handle all primitive + container types | YES |
| Python binding callable from Python (tested) | YES |
| TypeScript binding callable from TS (tested) | YES |
| Go binding callable from Go (tested) | YES |
| String, Option, Result conversions work | YES |
| 40/40+ golden (existing tests unbroken) | YES |
| 11/11 stage2 | YES |
| Fixed-point preserved | YES |
