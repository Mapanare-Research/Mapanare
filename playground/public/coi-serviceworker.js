/*! coi-serviceworker v0.1.7 - Guido Zuidhof / nicolo-ribaudo, licensed under MIT */
/*
 * This service worker adds Cross-Origin-Opener-Policy and
 * Cross-Origin-Embedder-Policy headers to all responses, enabling
 * SharedArrayBuffer on hosts (like GitHub Pages) that don't support
 * custom response headers. Required for Pyodide.
 */
if (typeof window === "undefined") {
  // Service worker context
  self.addEventListener("install", () => self.skipWaiting());
  self.addEventListener("activate", (e) => e.waitUntil(self.clients.claim()));
  self.addEventListener("fetch", (e) => {
    if (
      e.request.cache === "only-if-cached" &&
      e.request.mode !== "same-origin"
    ) {
      return;
    }
    e.respondWith(
      fetch(e.request).then((res) => {
        if (res.status === 0) return res;
        const headers = new Headers(res.headers);
        headers.set("Cross-Origin-Embedder-Policy", "credentialless");
        headers.set("Cross-Origin-Opener-Policy", "same-origin");
        return new Response(res.body, {
          status: res.status,
          statusText: res.statusText,
          headers,
        });
      })
    );
  });
} else {
  // Window context — register the service worker
  (async () => {
    if (!window.crossOriginIsolated) {
      const reg = await navigator.serviceWorker.register(
        window.document.currentScript.src
      );
      if (reg.active && !navigator.serviceWorker.controller) {
        window.location.reload();
      } else if (!reg.active) {
        reg.addEventListener("updatefound", () => {
          reg.installing.addEventListener("statechange", (evt) => {
            if (evt.target.state === "activated") {
              window.location.reload();
            }
          });
        });
      }
    }
  })();
}
