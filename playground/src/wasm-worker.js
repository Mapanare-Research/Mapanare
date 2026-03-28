/**
 * Web Worker for native WASM execution of Mapanare programs.
 *
 * This worker loads pre-compiled .wasm binaries and executes them
 * using the native WASM runtime (wasm-runtime.js), replacing the
 * Pyodide-based approach for compiled programs.
 *
 * Messages:
 *   { type: "init" }                          -> initialize runtime
 *   { type: "run-wasm", wasm: ArrayBuffer }   -> run pre-compiled WASM
 *   { type: "run", code: string }             -> compile via API + run WASM
 *
 * Responses:
 *   { type: "ready" }
 *   { type: "stdout", text: string }
 *   { type: "stderr", text: string }
 *   { type: "done", ok: boolean, elapsed: number }
 *   { type: "error", message: string }
 */

/* global WebAssembly */

// Import the runtime functions inline (worker cannot use ES modules in all browsers)
// The runtime is bundled by the build tool

let runtimeReady = false;

/**
 * Simple bump allocator for WASM linear memory.
 */
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

  free(_ptr) {
    // No-op
  }

  reset(offset = 65536) {
    this.offset = offset;
  }
}

/**
 * Create import object for WASM instantiation within this worker.
 */
function createWorkerImports(memory) {
  const allocator = new BumpAllocator(memory);
  const decoder = new TextDecoder("utf-8");
  const encoder = new TextEncoder();

  function readString(ptr, len) {
    const bytes = new Uint8Array(memory.buffer, ptr, len);
    return decoder.decode(bytes);
  }

  function writeString(str) {
    const encoded = encoder.encode(str);
    const ptr = allocator.alloc(encoded.length);
    const target = new Uint8Array(memory.buffer, ptr, encoded.length);
    target.set(encoded);
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
        const [ptr, _len] = writeString(String(value));
        return ptr;
      },
      mn_float_to_string(value) {
        const [ptr, _len] = writeString(String(value));
        return ptr;
      },
      mn_string_len(ptr) {
        const view = new DataView(memory.buffer);
        return view.getInt32(ptr - 4, true);
      },

      mn_time_ms() { return performance.now(); },
      mn_time_unix() { return Date.now(); },
      mn_random() { return Math.random(); },
      mn_random_int(min, max) {
        return Math.floor(Math.random() * (max - min + 1)) + min;
      },

      mn_abort(code) {
        throw new Error(`WASM aborted with code ${code}`);
      },
      mn_unreachable() {
        throw new Error("unreachable code executed");
      },

      // JS interop stubs for worker context (limited — no DOM)
      mn_js_eval(ptr, len) {
        const code = readString(ptr, len);
        try {
          const result = eval(code); // eslint-disable-line no-eval
          if (result === undefined || result === null) return 0;
          const [rPtr, _rLen] = writeString(String(result));
          return rPtr;
        } catch (_e) { return 0; }
      },
      mn_js_call() { return 0; },

      // DOM stubs (not available in worker)
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

      mn_fetch_sync(urlPtr, urlLen, outPtrPtr) {
        const url = readString(urlPtr, urlLen);
        try {
          const xhr = new XMLHttpRequest();
          xhr.open("GET", url, false);
          xhr.send();
          if (xhr.status >= 200 && xhr.status < 300) {
            const [ptr, len] = writeString(xhr.responseText);
            const view = new DataView(memory.buffer);
            view.setInt32(outPtrPtr, ptr, true);
            return len;
          }
          return -1;
        } catch (_e) { return -1; }
      },

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
        const dataSize = totalSize * elemSize;
        const ptr = allocator.alloc(headerSize + dataSize);
        view.setInt32(ptr, ndim, true);
        view.setInt32(ptr + 4, totalSize, true);
        const data = new Uint8Array(memory.buffer, ptr + headerSize, dataSize);
        data.fill(0);
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
        const view = new DataView(memory.buffer);
        view.setBigInt64(outPtr, BigInt(Date.now()) * 1000000n, true);
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
          const text = readString(bufPtr, bufLen);
          const msgType = fd === 2 ? "stderr" : "stdout";
          self.postMessage({ type: msgType, text });
          totalWritten += bufLen;
        }
        view.setUint32(nwrittenPtr, totalWritten, true);
        return 0;
      },
      fd_read() { return 0; },
      path_open() { return 0; },
      proc_exit(code) {
        throw new Error(`proc_exit(${code})`);
      },
      random_get(bufPtr, bufLen) {
        const buf = new Uint8Array(memory.buffer, bufPtr, bufLen);
        crypto.getRandomValues(buf);
        return 0;
      },
    },
  };
}

/**
 * Run a pre-compiled WASM binary.
 */
async function runWasm(wasmBytes) {
  const t0 = performance.now();

  try {
    const memory = new WebAssembly.Memory({ initial: 16, maximum: 256 });
    const imports = createWorkerImports(memory);
    const { instance } = await WebAssembly.instantiate(wasmBytes, imports);

    const exportedMemory = instance.exports.memory || memory;
    // Re-bind if module exports its own memory
    if (instance.exports.memory) {
      imports.env.mn_memory_size = () => exportedMemory.buffer.byteLength;
    }

    const main = instance.exports.main || instance.exports._start || instance.exports.__main;
    if (!main) {
      self.postMessage({
        type: "stderr",
        text: "Error: No main/_start export found in WASM module\n",
      });
      self.postMessage({ type: "done", ok: false, elapsed: performance.now() - t0 });
      return;
    }

    main();
    self.postMessage({ type: "done", ok: true, elapsed: performance.now() - t0 });
  } catch (e) {
    const elapsed = performance.now() - t0;
    const msg = e.message || String(e);
    // proc_exit(0) is normal termination
    if (msg.includes("proc_exit(0)")) {
      self.postMessage({ type: "done", ok: true, elapsed });
    } else {
      self.postMessage({ type: "stderr", text: `Runtime error: ${msg}\n` });
      self.postMessage({ type: "done", ok: false, elapsed });
    }
  }
}

self.onmessage = async (e) => {
  const msg = e.data;

  if (msg.type === "init") {
    runtimeReady = true;
    self.postMessage({ type: "ready" });
  } else if (msg.type === "run-wasm") {
    if (!runtimeReady) {
      self.postMessage({ type: "error", message: "Runtime not initialized" });
      return;
    }
    await runWasm(msg.wasm);
  } else if (msg.type === "run") {
    // For source code, we still need the Pyodide-based compilation
    // or a server-side compilation API
    self.postMessage({
      type: "stderr",
      text: "Source compilation in browser requires the Pyodide worker.\n" +
            "Use 'mapanare emit-wasm --binary <file>.mn' to pre-compile.\n",
    });
    self.postMessage({ type: "done", ok: false, elapsed: 0 });
  }
};
