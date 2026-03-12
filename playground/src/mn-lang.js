/**
 * CodeMirror 6 language support for Mapanare (.mn files).
 * Simple StreamLanguage-based syntax highlighting.
 */

import { StreamLanguage } from "@codemirror/language";

const keywords = new Set([
  "fn", "let", "mut", "if", "else", "while", "for", "in", "return",
  "match", "struct", "enum", "agent", "pipe", "signal", "stream",
  "import", "from", "pub", "extern", "impl", "trait", "type",
  "spawn", "send", "sync", "handle", "true", "false", "None",
  "Some", "Ok", "Err",
]);

const builtins = new Set([
  "println", "print", "len", "str", "int", "float", "push", "pop",
  "map", "filter", "reduce", "range",
]);

const types = new Set([
  "Int", "Float", "Bool", "String", "Char", "Void",
  "List", "Map", "Option", "Result", "Signal", "Stream",
  "Channel", "Tensor", "Fn",
]);

function tokenize(stream, state) {
  // Skip whitespace
  if (stream.eatSpace()) return null;

  // Line comment
  if (stream.match("//")) {
    stream.skipToEnd();
    return "lineComment";
  }

  // Triple-quoted string
  if (stream.match('"""')) {
    state.inTripleString = true;
    while (!stream.eol()) {
      if (stream.match('"""')) {
        state.inTripleString = false;
        return "string";
      }
      stream.next();
    }
    return "string";
  }

  // Continue triple-quoted string
  if (state.inTripleString) {
    while (!stream.eol()) {
      if (stream.match('"""')) {
        state.inTripleString = false;
        return "string";
      }
      stream.next();
    }
    return "string";
  }

  // String
  if (stream.match('"')) {
    while (!stream.eol()) {
      const ch = stream.next();
      if (ch === "\\") {
        stream.next(); // skip escaped char
      } else if (ch === '"') {
        return "string";
      }
    }
    return "string";
  }

  // Char literal
  if (stream.match("'")) {
    if (stream.match("\\")) stream.next();
    else stream.next();
    stream.eat("'");
    return "string";
  }

  // Numbers
  if (stream.match(/^0x[0-9a-fA-F_]+/) ||
      stream.match(/^0b[01_]+/) ||
      stream.match(/^0o[0-7_]+/) ||
      stream.match(/^[0-9][0-9_]*(\.[0-9_]+)?([eE][+-]?[0-9_]+)?/)) {
    return "number";
  }

  // Operators
  if (stream.match("|>") || stream.match("->") || stream.match("=>") ||
      stream.match("::") || stream.match("==") || stream.match("!=") ||
      stream.match("<=") || stream.match(">=") || stream.match("&&") ||
      stream.match("||") || stream.match("${")) {
    return "operator";
  }

  if (stream.match(/^[+\-*/%=<>!&|^~?@#]/)) {
    return "operator";
  }

  // Brackets
  if (stream.match(/^[(){}\[\]]/)) {
    return "bracket";
  }

  // Punctuation
  if (stream.match(/^[,;:.]/)) {
    return "punctuation";
  }

  // Identifier / keyword
  if (stream.match(/^[a-zA-Z_][a-zA-Z0-9_]*/)) {
    const word = stream.current();
    if (keywords.has(word)) return "keyword";
    if (builtins.has(word)) return "variableName.standard";
    if (types.has(word)) return "typeName";
    return "variableName";
  }

  // Consume unrecognized character
  stream.next();
  return null;
}

export const mnLanguage = StreamLanguage.define({
  startState() {
    return { inTripleString: false };
  },
  token: tokenize,
  languageData: {
    commentTokens: { line: "//" },
    closeBrackets: { brackets: ["(", "[", "{", '"'] },
  },
});
