# Mapanare v3.44.0 — "Cunaguaro" (Real Examples)

> Every example in the repo compiles and runs. No fake shit.
> Transpilation works end-to-end: .py → .mn → native binary.

**Status:** DONE
**Breaking:** No
**Prerequisite:** v3.43.0 (agents native)

---

## The Problem

The `examples/` directory has GPU, mobile, and WASM examples that don't
compile. There are no examples of real CLI programs. The Python/PHP
transpiler works but nobody has tested transpile → compile → run end-to-end.

---

## Checklist

### 1. Fix or Remove Broken Examples

- [ ] Audit every `.mn` file in `examples/` — does `mnc emit-llvm` succeed?
- [ ] GPU examples (`examples/gpu/`): add `// NOTE: requires GPU backend (not yet functional)` header, or move to `examples/experimental/gpu/`
- [ ] Mobile examples: move to `examples/experimental/mobile/`
- [ ] WASM examples: verify `mapanare emit-wasm` works on each
- [ ] Package examples: verify `mnc emit-llvm` works on each

### 2. Add Real CLI Examples

Create `examples/cli/` with programs that compile and run:

- [ ] `calculator.mn` — Read math expressions from stdin, evaluate, print result
  - Supports: +, -, *, /, parentheses
  - Uses: `read_line()`, string parsing, recursion
- [ ] `file_search.mn` — Search files for a pattern (mini-grep)
  - Uses: `read_line()` for pattern, `list_dir()`, `read_file()`, `contains()`
- [ ] `word_count.mn` — Count words/lines/chars in a file (like `wc`)
  - Uses: `read_file()`, `split()`, `length()`
- [ ] `todo.mn` — Simple TODO app: add/list/remove tasks from a file
  - Uses: `read_line()`, `read_file()`, `write_file()`, `append_file()`

### 3. Add Network Examples

Create `examples/network/`:

- [ ] `http_fetch.mn` — Fetch a URL and print response body
- [ ] `url_checker.mn` — Read URLs from file, check each with HTTP GET, report status

### 4. Transpilation End-to-End

Create `examples/transpile/` with source files in other languages:

- [ ] `fibonacci.py` — Recursive Fibonacci in Python
  ```python
  def fibonacci(n):
      if n <= 1:
          return n
      return fibonacci(n - 1) + fibonacci(n - 2)

  for i in range(10):
      print(fibonacci(i))
  ```
- [ ] `hello.php` — PHP hello world with control flow
  ```php
  <?php
  function greet($name) {
      return "Hello, " . $name . "!";
  }
  for ($i = 0; $i < 5; $i++) {
      echo greet("World") . "\n";
  }
  ```
- [ ] `data_transform.py` — List processing with filter/map
- [ ] `string_utils.php` — String manipulation functions
- [ ] `README.md` — Instructions:
  ```
  # Transpile & Run
  mapanare transpile fibonacci.py    # → fibonacci.mn
  mnc run fibonacci.mn               # → prints Fibonacci numbers
  ```

**Verify the full pipeline for each:**
- [ ] `mapanare transpile fibonacci.py` → produces `fibonacci.mn`
- [ ] `mnc emit-llvm fibonacci.mn` → produces valid LLVM IR
- [ ] `llvm-as fibonacci.ll` → validates
- [ ] `mnc run fibonacci.mn` → prints correct output

### 5. Agent Examples

Create `examples/agents/`:

- [ ] `ping_pong.mn` — Two agents sending messages back and forth
- [ ] `worker_pool.mn` — Fan-out computation across multiple agents

### 6. Culebra Validation

- [ ] `culebra scan` on ALL example IR outputs — zero critical
- [ ] `culebra summary` — all examples score "healthy"

---

## Exit Criteria

```bash
# ALL of these work:
mnc run examples/cli/calculator.mn <<< "2 + 3 * 4"
mnc run examples/cli/word_count.mn README.md
mnc run examples/cli/todo.mn
mnc run examples/network/http_fetch.mn
mnc run examples/agents/ping_pong.mn

# Transpile pipeline:
mapanare transpile examples/transpile/fibonacci.py
mnc run fibonacci.mn
# Output: 0 1 1 2 3 5 8 13 21 34
```
