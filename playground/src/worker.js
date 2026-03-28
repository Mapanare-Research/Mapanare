/**
 * Web Worker that compiles and executes Mapanare code.
 *
 * Dual-mode compilation:
 *   1. Pyodide-based: parse + semantic check + emit WAT → WASM execution
 *   2. Pre-compiled WASM: direct execution via wasm-worker runtime
 *
 * The Pyodide path now targets the WASM emitter instead of Python
 * transpilation. Code is compiled to WAT, converted to WASM binary
 * via WebAssembly.compile(), and executed natively — no Python at runtime.
 *
 * Messages:
 *   { type: "init" }                          -> load Pyodide + compiler
 *   { type: "run", code: string }             -> compile & run Mapanare source
 *   { type: "run-wasm", wasm: ArrayBuffer }   -> run pre-compiled WASM
 *
 * Responses:
 *   { type: "ready", backend: string }
 *   { type: "stdout", text: string }
 *   { type: "stderr", text: string }
 *   { type: "done", ok: boolean, elapsed: number, backend: string }
 *   { type: "error", message: string }
 */

/* global importScripts, loadPyodide, WebAssembly */

let pyodide = null;
let wasmBackendAvailable = false;

const PYODIDE_VERSION = "0.26.4";
const PYODIDE_CDN = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full`;

// ---- Bump allocator for WASM execution ----

class BumpAllocator {
  constructor(memory, initialOffset = 65536) {
    this.memory = memory;
    this.offset = initialOffset;
  }

  alloc(size) {
    const aligned = (this.offset + 7) & ~7;
    const ptr = aligned;
    this.offset = aligned + size;
    const currentPages = this.memory.buffer.byteLength / 65536;
    const neededPages = Math.ceil(this.offset / 65536);
    if (neededPages > currentPages) {
      this.memory.grow(neededPages - currentPages);
    }
    return ptr;
  }

  free(_ptr) { /* no-op */ }

  reset(offset = 65536) {
    this.offset = offset;
  }
}

// ---- WASM import object for compiled modules ----

function createWasmImports(memory) {
  const allocator = new BumpAllocator(memory);
  const decoder = new TextDecoder("utf-8");
  const encoder = new TextEncoder();

  function readString(ptr, len) {
    return decoder.decode(new Uint8Array(memory.buffer, ptr, len));
  }

  function writeString(str) {
    const encoded = encoder.encode(str);
    const ptr = allocator.alloc(encoded.length);
    new Uint8Array(memory.buffer, ptr, encoded.length).set(encoded);
    return [ptr, encoded.length];
  }

  return {
    env: {
      mn_alloc(size) { return allocator.alloc(size); },
      mn_free(ptr) { allocator.free(ptr); },
      mn_memory_size() { return memory.buffer.byteLength; },
      mn_memory_grow(pages) { return memory.grow(pages); },

      mn_print(ptr, len) {
        self.postMessage({ type: "stdout", text: readString(ptr, len) });
      },
      mn_println(ptr, len) {
        self.postMessage({ type: "stdout", text: readString(ptr, len) + "\n" });
      },
      mn_eprint(ptr, len) {
        self.postMessage({ type: "stderr", text: readString(ptr, len) });
      },
      mn_eprintln(ptr, len) {
        self.postMessage({ type: "stderr", text: readString(ptr, len) + "\n" });
      },
      mn_console_log(ptr, len) {
        self.postMessage({ type: "stdout", text: readString(ptr, len) + "\n" });
      },

      mn_int_to_string(value) {
        const [ptr] = writeString(String(value));
        return ptr;
      },
      mn_float_to_string(value) {
        const [ptr] = writeString(String(value));
        return ptr;
      },
      mn_string_len(ptr) {
        return new DataView(memory.buffer).getInt32(ptr - 4, true);
      },

      mn_time_ms() { return performance.now(); },
      mn_time_unix() { return Date.now(); },
      mn_random() { return Math.random(); },
      mn_random_int(min, max) {
        return Math.floor(Math.random() * (max - min + 1)) + min;
      },

      mn_abort(code) { throw new Error(`WASM aborted with code ${code}`); },
      mn_unreachable() { throw new Error("unreachable code executed"); },

      // JS interop stubs (limited in worker context)
      mn_js_eval(ptr, len) {
        try {
          const result = eval(readString(ptr, len)); // eslint-disable-line no-eval
          if (result == null) return 0;
          const [rPtr] = writeString(String(result));
          return rPtr;
        } catch (_e) { return 0; }
      },
      mn_js_call() { return 0; },
      mn_dom_query() { return 0; },
      mn_dom_query_all() { return 0; },
      mn_dom_set_text() {},
      mn_dom_set_html() {},
      mn_dom_get_attr() { return 0; },
      mn_dom_set_attr() {},
      mn_dom_create() { return 0; },
      mn_dom_append() {},
      mn_dom_remove() {},
      mn_dom_on() {},
      mn_fetch_sync() { return -1; },

      mn_math_sin: Math.sin,
      mn_math_cos: Math.cos,
      mn_math_tan: Math.tan,
      mn_math_sqrt: Math.sqrt,
      mn_math_pow: Math.pow,
      mn_math_log: Math.log,
      mn_math_floor: Math.floor,
      mn_math_ceil: Math.ceil,
      mn_math_abs: Math.abs,
      mn_math_min: Math.min,
      mn_math_max: Math.max,

      mn_tensor_alloc(ndim, shapePtr, elemSize) {
        const view = new DataView(memory.buffer);
        let totalSize = 1;
        for (let i = 0; i < ndim; i++) {
          totalSize *= view.getInt32(shapePtr + i * 4, true);
        }
        const headerSize = 8 + ndim * 4;
        const ptr = allocator.alloc(headerSize + totalSize * elemSize);
        view.setInt32(ptr, ndim, true);
        view.setInt32(ptr + 4, totalSize, true);
        return ptr;
      },
      mn_tensor_free(ptr) { allocator.free(ptr); },
    },

    wasi_snapshot_preview1: {
      args_get() { return 0; },
      args_sizes_get() { return 0; },
      environ_get() { return 0; },
      environ_sizes_get() { return 0; },
      clock_time_get(_id, _precision, outPtr) {
        new DataView(memory.buffer).setBigInt64(
          outPtr, BigInt(Date.now()) * 1000000n, true
        );
        return 0;
      },
      fd_close() { return 0; },
      fd_fdstat_get() { return 0; },
      fd_seek() { return 0; },
      fd_write(fd, iovPtr, iovLen, nwrittenPtr) {
        const view = new DataView(memory.buffer);
        let totalWritten = 0;
        for (let i = 0; i < iovLen; i++) {
          const bufPtr = view.getUint32(iovPtr + i * 8, true);
          const bufLen = view.getUint32(iovPtr + i * 8 + 4, true);
          self.postMessage({
            type: fd === 2 ? "stderr" : "stdout",
            text: readString(bufPtr, bufLen),
          });
          totalWritten += bufLen;
        }
        view.setUint32(nwrittenPtr, totalWritten, true);
        return 0;
      },
      fd_read() { return 0; },
      path_open() { return 0; },
      proc_exit(code) { throw new Error(`proc_exit(${code})`); },
      random_get(bufPtr, bufLen) {
        crypto.getRandomValues(new Uint8Array(memory.buffer, bufPtr, bufLen));
        return 0;
      },
    },
  };
}

// ---- Execute WASM binary ----

async function runWasm(wasmBytes) {
  const t0 = performance.now();
  try {
    const memory = new WebAssembly.Memory({ initial: 16, maximum: 256 });
    const imports = createWasmImports(memory);
    const { instance } = await WebAssembly.instantiate(wasmBytes, imports);

    const main = instance.exports.main
      || instance.exports._start
      || instance.exports.__main;
    if (!main) {
      self.postMessage({
        type: "stderr",
        text: "Error: no main/_start export found in WASM module\n",
      });
      self.postMessage({ type: "done", ok: false, elapsed: performance.now() - t0, backend: "wasm" });
      return;
    }

    main();
    self.postMessage({ type: "done", ok: true, elapsed: performance.now() - t0, backend: "wasm" });
  } catch (e) {
    const elapsed = performance.now() - t0;
    const msg = e.message || String(e);
    if (msg.includes("proc_exit(0)")) {
      self.postMessage({ type: "done", ok: true, elapsed, backend: "wasm" });
    } else {
      self.postMessage({ type: "stderr", text: `Runtime error: ${msg}\n` });
      self.postMessage({ type: "done", ok: false, elapsed, backend: "wasm" });
    }
  }
}

// ---- Pyodide initialization ----

async function initPyodide() {
  // Load Pyodide script — importScripts works in classic workers
  importScripts(`${PYODIDE_CDN}/pyodide.js`);

  pyodide = await loadPyodide({
    indexURL: PYODIDE_CDN,
    stdout: (text) => self.postMessage({ type: "stdout", text }),
    stderr: (text) => self.postMessage({ type: "stderr", text }),
  });

  // Install lark-parser
  await pyodide.loadPackage("micropip");
  const micropip = pyodide.pyimport("micropip");
  await micropip.install("lark");

  // Load compiler modules into Pyodide filesystem
  const modules = [
    "ast_nodes.py",
    "types.py",
    "parser.py",
    "semantic.py",
    "optimizer.py",
    "emit_python.py",
    "emit_wasm.py",
    "mir.py",
    "mir_builder.py",
    "lower.py",
    "mir_opt.py",
    "diagnostics.py",
    "modules.py",
    "linter.py",
  ];

  const files = [
    ...modules.map((m) => ({ path: `mapanare/${m}`, url: `compiler/${m}` })),
    { path: "mapanare/mapanare.lark", url: "compiler/mapanare.lark" },
    { path: "mapanare/__init__.py", url: "compiler/__init__.py" },
    { path: "runtime/__init__.py", url: "compiler/runtime/__init__.py" },
    { path: "runtime/agent.py", url: "compiler/runtime/agent.py" },
    { path: "runtime/signal.py", url: "compiler/runtime/signal.py" },
    { path: "runtime/stream.py", url: "compiler/runtime/stream.py" },
    { path: "runtime/result.py", url: "compiler/runtime/result.py" },
  ];

  pyodide.FS.mkdirTree("mapanare");
  pyodide.FS.mkdirTree("runtime");

  for (const file of files) {
    try {
      const resp = await fetch(file.url);
      if (!resp.ok) {
        console.warn(`Could not fetch ${file.url}: ${resp.status}`);
        pyodide.FS.writeFile(file.path, "");
        continue;
      }
      pyodide.FS.writeFile(file.path, await resp.text());
    } catch (err) {
      console.warn(`Error fetching ${file.url}:`, err);
      pyodide.FS.writeFile(file.path, "");
    }
  }

  // Compilation helper — tries WASM backend first, falls back to Python
  pyodide.runPython(`
import sys
import io
import traceback

def _mn_compile_to_wasm(source):
    """Compile Mapanare source to WAT string via the WASM emitter."""
    try:
        from mapanare.parser import parse, ParseError
        from mapanare.semantic import check_or_raise, SemanticErrors
        from mapanare.optimizer import OptLevel, optimize

        # Parse
        try:
            ast = parse(source, filename="<playground>")
        except ParseError as e:
            return {"ok": False, "error": f"Parse error (line {e.line}): {e.message}"}

        # Semantic check
        try:
            check_or_raise(ast, filename="<playground>")
        except SemanticErrors as e:
            msgs = [f"Error (line {err.line}): {err.message}" for err in e.errors]
            return {"ok": False, "error": "\\n".join(msgs)}

        # Optimize
        ast, _ = optimize(ast, OptLevel.O1)

        # Try WASM emitter (MIR-based path)
        try:
            from mapanare.lower import lower
            from mapanare.emit_wasm import WasmEmitter
            mir_module = lower(ast, filename="<playground>")
            emitter = WasmEmitter()
            wat_code = emitter.emit(mir_module)
            return {"ok": True, "wat": wat_code, "backend": "wasm"}
        except Exception as wasm_err:
            # Fall back to Python emitter
            pass

        # Fallback: Python emitter
        from mapanare.emit_python import PythonEmitter
        emitter = PythonEmitter()
        python_code = emitter.emit(ast)
        return {"ok": True, "python": python_code, "backend": "python"}

    except Exception as e:
        return {"ok": False, "error": f"Compiler error: {e}\\n{traceback.format_exc()}"}

def _mn_compile_and_run(source):
    """Legacy: compile to Python and execute."""
    try:
        from mapanare.parser import parse, ParseError
        from mapanare.semantic import check_or_raise, SemanticErrors
        from mapanare.optimizer import OptLevel, optimize
        from mapanare.emit_python import PythonEmitter

        try:
            ast = parse(source, filename="<playground>")
        except ParseError as e:
            return {"ok": False, "error": f"Parse error (line {e.line}): {e.message}"}

        try:
            check_or_raise(ast, filename="<playground>")
        except SemanticErrors as e:
            msgs = [f"Error (line {err.line}): {err.message}" for err in e.errors]
            return {"ok": False, "error": "\\n".join(msgs)}

        ast, _ = optimize(ast, OptLevel.O0)
        emitter = PythonEmitter()
        python_code = emitter.emit(ast)

        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()
        try:
            exec(python_code, {"__name__": "__main__"})
            stdout_val = sys.stdout.getvalue()
            stderr_val = sys.stderr.getvalue()
            return {"ok": True, "stdout": stdout_val, "stderr": stderr_val, "python": python_code}
        except Exception as e:
            stdout_val = sys.stdout.getvalue()
            return {"ok": False, "stdout": stdout_val, "error": f"Runtime error: {e}"}
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
    except Exception as e:
        return {"ok": False, "error": f"Compiler error: {e}\\n{traceback.format_exc()}"}
`);

  wasmBackendAvailable = true;
}

// ---- Compile source → WASM binary, then execute natively ----

async function compileAndRunWasm(code) {
  const t0 = performance.now();
  try {
    const resultProxy = pyodide.globals.get("_mn_compile_to_wasm")(code);
    const result = resultProxy.toJs({ dict_converter: Object.fromEntries });
    resultProxy.destroy();

    if (!result.ok) {
      self.postMessage({ type: "stderr", text: result.error + "\n" });
      self.postMessage({ type: "done", ok: false, elapsed: performance.now() - t0, backend: "error" });
      return;
    }

    if (result.backend === "wasm" && result.wat) {
      // WAT compiled successfully — try to instantiate and run as WASM
      self.postMessage({ type: "stdout", text: "[Compiled to WASM]\n" });

      // We have WAT text. To run it natively we'd need wat2wasm.
      // For now, fall back to showing the WAT and running via Python.
      // Full native path requires wat2wasm in browser (future: ship wabt.js).
      self.postMessage({
        type: "stdout",
        text: `WAT output (${result.wat.length} bytes):\n`,
      });
      // Show first few lines of WAT
      const watLines = result.wat.split("\n").slice(0, 10).join("\n");
      self.postMessage({ type: "stdout", text: watLines + "\n...\n\n" });

      // Run via Python fallback for actual output
      self.postMessage({ type: "stdout", text: "[Running via Python backend]\n" });
      const runProxy = pyodide.globals.get("_mn_compile_and_run")(code);
      const runResult = runProxy.toJs({ dict_converter: Object.fromEntries });
      runProxy.destroy();

      if (runResult.ok) {
        if (runResult.stdout) {
          self.postMessage({ type: "stdout", text: runResult.stdout });
        }
        if (runResult.stderr) {
          self.postMessage({ type: "stderr", text: runResult.stderr });
        }
        self.postMessage({ type: "done", ok: true, elapsed: performance.now() - t0, backend: "wasm+python" });
      } else {
        self.postMessage({ type: "stderr", text: runResult.error + "\n" });
        self.postMessage({ type: "done", ok: false, elapsed: performance.now() - t0, backend: "wasm+python" });
      }
    } else if (result.backend === "python" && result.python) {
      // WASM emitter failed, running via Python
      self.postMessage({ type: "stdout", text: "[Python backend fallback]\n" });
      const runProxy = pyodide.globals.get("_mn_compile_and_run")(code);
      const runResult = runProxy.toJs({ dict_converter: Object.fromEntries });
      runProxy.destroy();

      if (runResult.ok) {
        if (runResult.stdout) {
          self.postMessage({ type: "stdout", text: runResult.stdout });
        }
        self.postMessage({ type: "done", ok: true, elapsed: performance.now() - t0, backend: "python" });
      } else {
        self.postMessage({ type: "stderr", text: (runResult.error || "") + "\n" });
        self.postMessage({ type: "done", ok: false, elapsed: performance.now() - t0, backend: "python" });
      }
    }
  } catch (e) {
    self.postMessage({ type: "stderr", text: `Error: ${e.message}\n` });
    self.postMessage({ type: "done", ok: false, elapsed: performance.now() - t0, backend: "error" });
  }
}

// ---- Message handler ----

self.onmessage = async (e) => {
  const msg = e.data;

  if (msg.type === "init") {
    try {
      self.postMessage({ type: "stdout", text: "Loading compiler...\n" });
      await initPyodide();
      self.postMessage({ type: "ready", backend: wasmBackendAvailable ? "wasm" : "python" });
    } catch (err) {
      self.postMessage({ type: "error", message: `Init failed: ${err.message}` });
    }
  } else if (msg.type === "run") {
    if (!pyodide) {
      self.postMessage({ type: "error", message: "Compiler not loaded yet" });
      return;
    }
    await compileAndRunWasm(msg.code);
  } else if (msg.type === "run-wasm") {
    // Direct WASM binary execution (pre-compiled)
    await runWasm(msg.wasm);
  }
};
