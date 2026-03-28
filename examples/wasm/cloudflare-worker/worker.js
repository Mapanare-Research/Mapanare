/**
 * Cloudflare Worker entry point — loads the Mapanare-compiled WASM module
 * and routes HTTP requests to the handle_request function.
 */

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const method = request.method;
    const path = url.pathname;

    try {
      // Instantiate the WASM module with minimal imports
      const instance = await WebAssembly.instantiate(env.WASM_MODULE, {
        env: {
          // Memory provided by Cloudflare runtime
          memory: new WebAssembly.Memory({ initial: 256 }),
        },
      });

      const exports = instance.exports;

      // Allocate strings in WASM memory and call handle_request
      const encoder = new TextEncoder();
      const decoder = new TextDecoder();

      // Write method string to WASM memory
      const methodBytes = encoder.encode(method);
      const methodPtr = exports.__mn_alloc(methodBytes.length + 8);
      const mem = new Uint8Array(exports.memory.buffer);

      // Write length-prefixed string (Mapanare string layout: {ptr, len})
      new DataView(exports.memory.buffer).setInt32(methodPtr, methodBytes.length, true);
      mem.set(methodBytes, methodPtr + 8);

      // Write path string
      const pathBytes = encoder.encode(path);
      const pathPtr = exports.__mn_alloc(pathBytes.length + 8);
      new DataView(exports.memory.buffer).setInt32(pathPtr, pathBytes.length, true);
      mem.set(pathBytes, pathPtr + 8);

      // Call the Mapanare handler
      const resultPtr = exports.handle_request(methodPtr, pathPtr);

      // Read result string from WASM memory
      const resultLen = new DataView(exports.memory.buffer).getInt32(resultPtr, true);
      const resultBytes = mem.slice(resultPtr + 8, resultPtr + 8 + resultLen);
      const body = decoder.decode(resultBytes);

      return new Response(body, {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    } catch (err) {
      return new Response(JSON.stringify({ error: err.message }), {
        status: 500,
        headers: { "Content-Type": "application/json" },
      });
    }
  },
};
