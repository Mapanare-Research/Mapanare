/**
 * wasm-runtime.js — Native WASM runtime for Mapanare programs.
 *
 * Replaces the Pyodide-based worker with a native WASM execution engine.
 * Mapanare programs compiled to .wasm via `mapanare emit-wasm --binary`
 * can be loaded and executed directly in the browser.
 *
 * Provides the JS-side imports that Mapanare WASM modules expect:
 *   - env.mn_print(ptr, len)       — print string from linear memory
 *   - env.mn_println(ptr, len)     — print + newline
 *   - env.mn_alloc(size) -> ptr    — bump allocator
 *   - env.mn_free(ptr)             — no-op (arena cleanup)
 *   - env.mn_time_ms() -> f64      — current time in milliseconds
 *   - env.mn_random() -> f64       — random float [0, 1)
 *   - env.mn_abort(code)           — abort execution
 *   - env.mn_js_eval(ptr, len)     — evaluate JS string
 *   - env.mn_dom_query(ptr, len)   — document.querySelector
 *   - env.mn_dom_set_text(h, p, l) — set element textContent
 *   - env.mn_console_log(ptr, len) — console.log from WASM
 *   - env.mn_fetch(ptr, len)       — fetch URL (async via shared buffer)
 */

/**
 * WASM memory bump allocator state.
 * Tracks the current allocation pointer within WASM linear memory.
 */
class BumpAllocator {
  constructor(memory, initialOffset = 65536) {
    this.memory = memory;
    this.offset = initialOffset; // Start after 64KB reserved for stack/data
  }

  alloc(size) {
    // Align to 8 bytes
    const aligned = (this.offset + 7) & ~7;
    const ptr = aligned;
    this.offset = aligned + size;

    // Grow memory if needed
    const currentPages = this.memory.buffer.byteLength / 65536;
    const neededPages = Math.ceil(this.offset / 65536);
    if (neededPages > currentPages) {
      this.memory.grow(neededPages - currentPages);
    }

    return ptr;
  }

  free(_ptr) {
    // No-op — arena cleanup happens on module teardown
  }

  reset(offset = 65536) {
    this.offset = offset;
  }
}

/**
 * DOM handle registry — maps integer handles to DOM elements.
 * WASM cannot hold JS object references, so we use integer handles.
 */
class HandleRegistry {
  constructor() {
    this.handles = new Map();
    this.nextHandle = 1;
  }

  register(obj) {
    const handle = this.nextHandle++;
    this.handles.set(handle, obj);
    return handle;
  }

  get(handle) {
    return this.handles.get(handle) || null;
  }

  release(handle) {
    this.handles.delete(handle);
  }

  clear() {
    this.handles.clear();
    this.nextHandle = 1;
  }
}

/**
 * Create the import object for a Mapanare WASM module.
 *
 * @param {WebAssembly.Memory} memory - The WASM linear memory
 * @param {object} callbacks - Output callbacks
 * @param {function} callbacks.onStdout - Called with stdout text
 * @param {function} callbacks.onStderr - Called with stderr text
 * @returns {object} The imports object for WebAssembly.instantiate
 */
export function createImports(memory, callbacks = {}) {
  const allocator = new BumpAllocator(memory);
  const handles = new HandleRegistry();
  const decoder = new TextDecoder("utf-8");
  const encoder = new TextEncoder();

  const onStdout = callbacks.onStdout || ((text) => process.stdout?.write?.(text) || console.log(text));
  const onStderr = callbacks.onStderr || ((text) => process.stderr?.write?.(text) || console.error(text));

  /**
   * Read a UTF-8 string from WASM linear memory.
   */
  function readString(ptr, len) {
    const bytes = new Uint8Array(memory.buffer, ptr, len);
    return decoder.decode(bytes);
  }

  /**
   * Write a UTF-8 string into WASM linear memory, returning [ptr, len].
   */
  function writeString(str) {
    const encoded = encoder.encode(str);
    const ptr = allocator.alloc(encoded.length);
    const target = new Uint8Array(memory.buffer, ptr, encoded.length);
    target.set(encoded);
    return [ptr, encoded.length];
  }

  return {
    env: {
      // --- Memory management ---
      mn_alloc(size) {
        return allocator.alloc(size);
      },

      mn_free(ptr) {
        allocator.free(ptr);
      },

      mn_memory_size() {
        return memory.buffer.byteLength;
      },

      mn_memory_grow(pages) {
        return memory.grow(pages);
      },

      // --- I/O ---
      mn_print(ptr, len) {
        const text = readString(ptr, len);
        onStdout(text);
      },

      mn_println(ptr, len) {
        const text = readString(ptr, len);
        onStdout(text + "\n");
      },

      mn_eprint(ptr, len) {
        const text = readString(ptr, len);
        onStderr(text);
      },

      mn_eprintln(ptr, len) {
        const text = readString(ptr, len);
        onStderr(text + "\n");
      },

      mn_console_log(ptr, len) {
        const text = readString(ptr, len);
        console.log(text);
      },

      // --- Builtins ---
      mn_int_to_string(value) {
        const str = String(value);
        const [ptr, len] = writeString(str);
        // Write length at ptr-8 (Mapanare string header: [len: i64][data...])
        return ptr;
      },

      mn_float_to_string(value) {
        const str = String(value);
        const [ptr, _len] = writeString(str);
        return ptr;
      },

      mn_string_len(ptr) {
        // Read string length from header
        const view = new DataView(memory.buffer);
        return view.getInt32(ptr - 4, true);
      },

      // --- Time ---
      mn_time_ms() {
        return performance.now();
      },

      mn_time_unix() {
        return Date.now();
      },

      // --- Random ---
      mn_random() {
        return Math.random();
      },

      mn_random_int(min, max) {
        return Math.floor(Math.random() * (max - min + 1)) + min;
      },

      // --- Control flow ---
      mn_abort(code) {
        throw new Error(`Mapanare WASM aborted with code ${code}`);
      },

      mn_unreachable() {
        throw new Error("Mapanare WASM: unreachable code executed");
      },

      // --- JavaScript interop ---
      mn_js_eval(ptr, len) {
        const code = readString(ptr, len);
        try {
          const result = eval(code); // eslint-disable-line no-eval
          if (result === undefined || result === null) return 0;
          if (typeof result === "number") return result;
          const str = String(result);
          const [rPtr, _rLen] = writeString(str);
          return rPtr;
        } catch (e) {
          onStderr(`js_eval error: ${e.message}\n`);
          return 0;
        }
      },

      mn_js_call(funcPtr, funcLen, argsPtr, argsLen) {
        const funcName = readString(funcPtr, funcLen);
        const argsJson = readString(argsPtr, argsLen);
        try {
          const args = JSON.parse(argsJson);
          const parts = funcName.split(".");
          let obj = globalThis;
          for (let i = 0; i < parts.length - 1; i++) {
            obj = obj[parts[i]];
          }
          const result = obj[parts[parts.length - 1]](...args);
          if (result === undefined || result === null) return 0;
          const str = JSON.stringify(result);
          const [rPtr, _rLen] = writeString(str);
          return rPtr;
        } catch (e) {
          onStderr(`js_call error: ${e.message}\n`);
          return 0;
        }
      },

      // --- DOM operations ---
      mn_dom_query(selectorPtr, selectorLen) {
        const selector = readString(selectorPtr, selectorLen);
        const el = document.querySelector(selector);
        if (!el) return 0;
        return handles.register(el);
      },

      mn_dom_query_all(selectorPtr, selectorLen) {
        const selector = readString(selectorPtr, selectorLen);
        const els = document.querySelectorAll(selector);
        // Return handle to the NodeList
        return handles.register(els);
      },

      mn_dom_set_text(handle, textPtr, textLen) {
        const el = handles.get(handle);
        if (el) {
          el.textContent = readString(textPtr, textLen);
        }
      },

      mn_dom_set_html(handle, htmlPtr, htmlLen) {
        const el = handles.get(handle);
        if (el) {
          el.innerHTML = readString(htmlPtr, htmlLen);
        }
      },

      mn_dom_get_attr(handle, namePtr, nameLen) {
        const el = handles.get(handle);
        if (!el) return 0;
        const name = readString(namePtr, nameLen);
        const value = el.getAttribute(name);
        if (!value) return 0;
        const [ptr, _len] = writeString(value);
        return ptr;
      },

      mn_dom_set_attr(handle, namePtr, nameLen, valuePtr, valueLen) {
        const el = handles.get(handle);
        if (el) {
          const name = readString(namePtr, nameLen);
          const value = readString(valuePtr, valueLen);
          el.setAttribute(name, value);
        }
      },

      mn_dom_create(tagPtr, tagLen) {
        const tag = readString(tagPtr, tagLen);
        const el = document.createElement(tag);
        return handles.register(el);
      },

      mn_dom_append(parentHandle, childHandle) {
        const parent = handles.get(parentHandle);
        const child = handles.get(childHandle);
        if (parent && child) {
          parent.appendChild(child);
        }
      },

      mn_dom_remove(handle) {
        const el = handles.get(handle);
        if (el && el.parentNode) {
          el.parentNode.removeChild(el);
        }
        handles.release(handle);
      },

      mn_dom_on(handle, eventPtr, eventLen, callbackIndex) {
        const el = handles.get(handle);
        if (!el) return;
        const event = readString(eventPtr, eventLen);
        el.addEventListener(event, (e) => {
          // Call back into WASM via the function table
          const table = instance?.exports?.__indirect_function_table;
          if (table) {
            const eventHandle = handles.register(e);
            table.get(callbackIndex)(eventHandle);
            handles.release(eventHandle);
          }
        });
      },

      // --- Fetch API ---
      mn_fetch_sync(urlPtr, urlLen, outPtrPtr) {
        // Synchronous fetch via XMLHttpRequest (blocking — use in worker only)
        const url = readString(urlPtr, urlLen);
        try {
          const xhr = new XMLHttpRequest();
          xhr.open("GET", url, false); // synchronous
          xhr.send();
          if (xhr.status >= 200 && xhr.status < 300) {
            const [ptr, len] = writeString(xhr.responseText);
            // Write pointer to outPtrPtr location
            const view = new DataView(memory.buffer);
            view.setInt32(outPtrPtr, ptr, true);
            return len;
          }
          return -1;
        } catch (_e) {
          return -1;
        }
      },

      // --- Math builtins ---
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

      // --- Tensor operations (CPU fallback in WASM) ---
      mn_tensor_alloc(ndim, shapePtr, elemSize) {
        const view = new DataView(memory.buffer);
        let totalSize = 1;
        const shape = [];
        for (let i = 0; i < ndim; i++) {
          const dim = view.getInt32(shapePtr + i * 4, true);
          shape.push(dim);
          totalSize *= dim;
        }
        // Allocate: header (4 + 4 + ndim*4) + data (totalSize * elemSize)
        const headerSize = 8 + ndim * 4;
        const dataSize = totalSize * elemSize;
        const ptr = allocator.alloc(headerSize + dataSize);

        // Write header: [ndim: i32][size: i32][shape: i32 * ndim]
        view.setInt32(ptr, ndim, true);
        view.setInt32(ptr + 4, totalSize, true);
        for (let i = 0; i < ndim; i++) {
          view.setInt32(ptr + 8 + i * 4, shape[i], true);
        }
        // Zero-fill data
        const data = new Uint8Array(memory.buffer, ptr + headerSize, dataSize);
        data.fill(0);

        return ptr;
      },

      mn_tensor_free(ptr) {
        allocator.free(ptr);
      },
    },

    // WASI preview 1 stubs (for wasm32-wasi target)
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
          if (fd === 1) onStdout(text);
          else if (fd === 2) onStderr(text);
          totalWritten += bufLen;
        }
        view.setUint32(nwrittenPtr, totalWritten, true);
        return 0;
      },
      fd_read() { return 0; },
      path_open() { return 0; },
      proc_exit(code) {
        throw new Error(`WASI proc_exit(${code})`);
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
 * Load and instantiate a Mapanare WASM module.
 *
 * @param {BufferSource|string} source - WASM binary (ArrayBuffer) or URL to .wasm file
 * @param {object} callbacks - Output callbacks { onStdout, onStderr }
 * @returns {Promise<{instance: WebAssembly.Instance, memory: WebAssembly.Memory, exports: object}>}
 */
export async function loadModule(source, callbacks = {}) {
  const memory = new WebAssembly.Memory({ initial: 16, maximum: 256 }); // 1MB-16MB
  const imports = createImports(memory, callbacks);

  let wasmBytes;
  if (typeof source === "string") {
    const resp = await fetch(source);
    wasmBytes = await resp.arrayBuffer();
  } else {
    wasmBytes = source;
  }

  const { instance } = await WebAssembly.instantiate(wasmBytes, imports);

  // If the module exports its own memory, use that instead
  const exportedMemory = instance.exports.memory || memory;

  return {
    instance,
    memory: exportedMemory,
    exports: instance.exports,
  };
}

/**
 * Load and run a Mapanare WASM module, calling its main/_start function.
 *
 * @param {BufferSource|string} source - WASM binary or URL
 * @param {object} callbacks - Output callbacks
 * @returns {Promise<{ok: boolean, elapsed: number, error?: string}>}
 */
export async function runModule(source, callbacks = {}) {
  const t0 = performance.now();
  try {
    const { exports } = await loadModule(source, callbacks);

    // Try standard entry points
    const main = exports.main || exports._start || exports.__main;
    if (!main) {
      return { ok: false, elapsed: performance.now() - t0, error: "No main/_start export found" };
    }

    main();
    return { ok: true, elapsed: performance.now() - t0 };
  } catch (e) {
    return { ok: false, elapsed: performance.now() - t0, error: e.message || String(e) };
  }
}

// Keep a reference to the current instance for DOM event callbacks
let instance = null;

/**
 * Set the current WASM instance (needed for indirect function table callbacks).
 */
export function setInstance(inst) {
  instance = inst;
}
