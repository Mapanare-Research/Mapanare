/**
 * Mapanare Playground — main application entry point.
 *
 * Sets up CodeMirror editor, Pyodide web worker, examples dropdown,
 * share functionality, and panel resizing.
 */

import { EditorState } from "@codemirror/state";
import { EditorView, keymap, lineNumbers, highlightActiveLine, highlightActiveLineGutter } from "@codemirror/view";
import { defaultKeymap, history, historyKeymap } from "@codemirror/commands";
import { bracketMatching, indentOnInput } from "@codemirror/language";
import { closeBrackets, closeBracketsKeymap } from "@codemirror/autocomplete";
import { mnLanguage } from "./mn-lang.js";
import { EXAMPLES } from "./examples.js";

// ---- Theme (Tokyo Night inspired) ----

const playgroundTheme = EditorView.theme({
  "&": {
    backgroundColor: "#24283b",
    color: "#c0caf5",
  },
  ".cm-content": {
    caretColor: "#7aa2f7",
    fontFamily: "'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace",
  },
  ".cm-cursor": {
    borderLeftColor: "#7aa2f7",
  },
  "&.cm-focused .cm-selectionBackground, .cm-selectionBackground": {
    backgroundColor: "rgba(122, 162, 247, 0.2)",
  },
  ".cm-activeLine": {
    backgroundColor: "rgba(122, 162, 247, 0.06)",
  },
  ".cm-gutters": {
    backgroundColor: "#1f2133",
    color: "#565f89",
    borderRight: "1px solid #3b4261",
  },
  ".cm-activeLineGutter": {
    backgroundColor: "#24283b",
  },
  // Syntax highlighting via tags
  ".ͼb": { color: "#bb9af7" },      // keyword
  ".ͼc": { color: "#9ece6a" },      // string
  ".ͼd": { color: "#ff9e64" },      // number
  ".ͼe": { color: "#565f89" },      // comment
  ".ͼm": { color: "#7aa2f7" },      // variableName
  ".ͼi": { color: "#2ac3de" },      // typeName
  ".ͼl": { color: "#89ddff" },      // operator
  ".ͼn": { color: "#c0caf5" },      // bracket
  ".ͼo": { color: "#7dcfff" },      // function/builtin
});

// ---- Editor setup ----

const initialCode = EXAMPLES[0].code;

const state = EditorState.create({
  doc: initialCode,
  extensions: [
    lineNumbers(),
    highlightActiveLine(),
    highlightActiveLineGutter(),
    history(),
    bracketMatching(),
    closeBrackets(),
    indentOnInput(),
    mnLanguage,
    playgroundTheme,
    keymap.of([
      ...closeBracketsKeymap,
      ...defaultKeymap,
      ...historyKeymap,
      {
        key: "Ctrl-Enter",
        mac: "Cmd-Enter",
        run: () => { runCode(); return true; },
      },
    ]),
    EditorView.updateListener.of((update) => {
      if (update.docChanged) {
        // Clear stale share URL when code changes
        clearShareHighlight();
      }
    }),
  ],
});

const editorEl = document.getElementById("editor");
const view = new EditorView({ state, parent: editorEl });

// ---- Worker ----

const worker = new Worker(new URL("./worker.js", import.meta.url));
const statusEl = document.getElementById("status");
const outputEl = document.getElementById("output");
const btnRun = document.getElementById("btn-run");
let ready = false;

worker.onmessage = (e) => {
  const msg = e.data;
  switch (msg.type) {
    case "ready":
      ready = true;
      statusEl.textContent = "Ready";
      statusEl.className = "status ready";
      btnRun.disabled = false;
      // If there's code in the URL hash, load it
      loadFromHash();
      break;
    case "stdout":
      appendOutput(msg.text, "out-stdout");
      break;
    case "stderr":
      appendOutput(msg.text, "out-error");
      break;
    case "done":
      appendOutput(
        `\n--- ${msg.ok ? "OK" : "FAILED"} (${msg.elapsed.toFixed(0)}ms) ---`,
        msg.ok ? "out-info" : "out-warn"
      );
      btnRun.disabled = false;
      statusEl.textContent = "Ready";
      statusEl.className = "status ready";
      break;
    case "error":
      appendOutput(msg.message, "out-error");
      statusEl.textContent = "Error";
      statusEl.className = "status error";
      btnRun.disabled = false;
      break;
  }
};

worker.postMessage({ type: "init" });
btnRun.disabled = true;

// ---- Actions ----

function runCode() {
  if (!ready) return;
  const code = view.state.doc.toString();
  if (!code.trim()) return;

  outputEl.textContent = "";
  btnRun.disabled = true;
  statusEl.textContent = "Running...";
  statusEl.className = "status";

  worker.postMessage({ type: "run", code });
}

function appendOutput(text, className) {
  const span = document.createElement("span");
  span.className = className || "";
  span.textContent = text;
  outputEl.appendChild(span);
  outputEl.scrollTop = outputEl.scrollHeight;
}

// ---- Examples dropdown ----

const examplesSelect = document.getElementById("examples");

EXAMPLES.forEach((ex, i) => {
  const opt = document.createElement("option");
  opt.value = String(i);
  opt.textContent = ex.name;
  examplesSelect.appendChild(opt);
});

examplesSelect.addEventListener("change", () => {
  const idx = parseInt(examplesSelect.value, 10);
  if (isNaN(idx)) return;
  const example = EXAMPLES[idx];
  if (!example) return;

  view.dispatch({
    changes: { from: 0, to: view.state.doc.length, insert: example.code },
  });
  outputEl.textContent = "";
});

// ---- Share ----

const btnShare = document.getElementById("btn-share");

btnShare.addEventListener("click", () => {
  const code = view.state.doc.toString();
  const encoded = btoa(unescape(encodeURIComponent(code)));
  const url = `${window.location.origin}${window.location.pathname}#code=${encoded}`;

  navigator.clipboard.writeText(url).then(
    () => showToast("Link copied to clipboard!"),
    () => {
      // Fallback: update URL bar
      window.location.hash = `code=${encoded}`;
      showToast("Link updated in address bar");
    }
  );
});

function loadFromHash() {
  const hash = window.location.hash;
  if (!hash.startsWith("#code=")) return;
  try {
    const encoded = hash.slice(6);
    const code = decodeURIComponent(escape(atob(encoded)));
    view.dispatch({
      changes: { from: 0, to: view.state.doc.length, insert: code },
    });
    examplesSelect.value = "";
  } catch {
    // Invalid hash, ignore
  }
}

function clearShareHighlight() {
  // no-op for now; could be used to dim the share button
}

// ---- Toast ----

function showToast(message) {
  const existing = document.querySelector(".toast");
  if (existing) existing.remove();

  const toast = document.createElement("div");
  toast.className = "toast";
  toast.textContent = message;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 2000);
}

// ---- Clear button ----

document.getElementById("btn-clear").addEventListener("click", () => {
  outputEl.textContent = "";
});

// ---- Gutter resize ----

const gutter = document.getElementById("gutter");
const panelEditor = document.querySelector(".panel-editor");
const panelOutput = document.querySelector(".panel-output");

let isDragging = false;

gutter.addEventListener("mousedown", (e) => {
  isDragging = true;
  gutter.classList.add("dragging");
  e.preventDefault();
});

document.addEventListener("mousemove", (e) => {
  if (!isDragging) return;
  const container = document.querySelector("main");
  const rect = container.getBoundingClientRect();
  const fraction = (e.clientX - rect.left) / rect.width;
  const clamped = Math.max(0.2, Math.min(0.8, fraction));
  panelEditor.style.flex = `${clamped}`;
  panelOutput.style.flex = `${1 - clamped}`;
});

document.addEventListener("mouseup", () => {
  isDragging = false;
  gutter.classList.remove("dragging");
});

// ---- Run button ----

btnRun.addEventListener("click", runCode);

// ---- Expose for debugging ----

window.__mnPlayground = { view, worker, runCode };
