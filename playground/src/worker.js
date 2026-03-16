/**
 * Web Worker that runs Pyodide to compile and execute Mapanare code.
 *
 * Messages:
 *   { type: "init" }                -> load Pyodide + compiler
 *   { type: "run", code: string }   -> compile & run Mapanare source
 *
 * Responses:
 *   { type: "ready" }
 *   { type: "stdout", text: string }
 *   { type: "stderr", text: string }
 *   { type: "done", ok: boolean, elapsed: number }
 *   { type: "error", message: string }
 */

/* global importScripts, loadPyodide */

let pyodide = null;

const PYODIDE_VERSION = "0.26.4";
const PYODIDE_CDN = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full`;

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

  // Load the compiler modules into Pyodide's filesystem
  // We fetch them from the bundled /compiler/ directory
  const modules = [
    "ast_nodes.py",
    "types.py",
    "parser.py",
    "semantic.py",
    "optimizer.py",
    "emit_python.py",
    "diagnostics.py",
    "modules.py",
    "linter.py",
  ];

  // Also need the grammar file
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

  // Create directory structure
  pyodide.FS.mkdirTree("mapanare");
  pyodide.FS.mkdirTree("runtime");

  for (const file of files) {
    try {
      const resp = await fetch(file.url);
      if (!resp.ok) {
        console.warn(`Could not fetch ${file.url}: ${resp.status}`);
        // Write empty file to avoid import errors
        pyodide.FS.writeFile(file.path, "");
        continue;
      }
      const content = await resp.text();
      pyodide.FS.writeFile(file.path, content);
    } catch (err) {
      console.warn(`Error fetching ${file.url}:`, err);
      pyodide.FS.writeFile(file.path, "");
    }
  }

  // Set up the compilation + execution helper
  pyodide.runPython(`
import sys
import io
import traceback

def _mn_compile_and_run(source):
    """Compile Mapanare source to Python and execute it."""
    try:
        from mapanare.parser import parse, ParseError
        from mapanare.semantic import check_or_raise, SemanticErrors
        from mapanare.optimizer import OptLevel, optimize
        from mapanare.emit_python import PythonEmitter

        # Parse
        try:
            ast = parse(source, filename="<playground>")
        except ParseError as e:
            return {"ok": False, "error": f"Parse error (line {e.line}): {e.message}"}

        # Semantic check
        try:
            check_or_raise(ast, filename="<playground>")
        except SemanticErrors as e:
            msgs = []
            for err in e.errors:
                msgs.append(f"Error (line {err.line}): {err.message}")
            return {"ok": False, "error": "\\n".join(msgs)}

        # Optimize
        ast, _ = optimize(ast, OptLevel.O0)

        # Emit Python
        emitter = PythonEmitter()
        python_code = emitter.emit(ast)

        # Execute
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

  self.postMessage({ type: "ready" });
}

async function runCode(code) {
  if (!pyodide) {
    self.postMessage({ type: "error", message: "Pyodide not initialized" });
    return;
  }

  const t0 = performance.now();

  try {
    pyodide.globals.set("_mn_source", code);
    const resultProxy = pyodide.runPython("_mn_compile_and_run(_mn_source)");
    const result = resultProxy.toJs({ dict_converter: Object.fromEntries });

    if (result.ok) {
      if (result.stdout) {
        self.postMessage({ type: "stdout", text: result.stdout });
      }
      if (result.stderr) {
        self.postMessage({ type: "stderr", text: result.stderr });
      }
    } else {
      if (result.stdout) {
        self.postMessage({ type: "stdout", text: result.stdout });
      }
      self.postMessage({ type: "stderr", text: result.error });
    }

    const elapsed = performance.now() - t0;
    self.postMessage({ type: "done", ok: result.ok, elapsed });
  } catch (err) {
    const elapsed = performance.now() - t0;
    self.postMessage({ type: "stderr", text: `Internal error: ${err.message || err}` });
    self.postMessage({ type: "done", ok: false, elapsed });
  }
}

self.onmessage = async (e) => {
  const msg = e.data;
  if (msg.type === "init") {
    try {
      await initPyodide();
    } catch (err) {
      self.postMessage({
        type: "error",
        message: `Failed to initialize Pyodide: ${err.message || String(err)}`,
      });
    }
  } else if (msg.type === "run") {
    await runCode(msg.code);
  }
};
