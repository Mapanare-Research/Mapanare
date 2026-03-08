# Bootstrap Compiler

This directory contains a frozen copy of the Python-based Mapanare compiler.
It is used to bootstrap the self-hosted compiler written in Mapanare itself
(see `mapa/self/*.mn`).

## Bootstrap Chain

1. **Stage 0 (this directory):** Python compiler compiles `.mn` files
2. **Stage 1:** Python compiler compiles `mapa/self/*.mn` → LLVM IR
3. **Stage 2:** Stage 1 output compiles `mapa/self/*.mn` → identical LLVM IR

When Stage 1 and Stage 2 produce identical output, the compiler is a fixed
point and the bootstrap is complete.

## Files

Frozen copies of the original Python compiler modules:

- `lexer.py` — Lark-based tokenizer
- `parser.py` — LALR parser + AST transformer
- `ast_nodes.py` — AST node dataclasses
- `semantic.py` — Type checking and scope analysis
- `emit_llvm.py` — LLVM IR emitter via llvmlite
- `emit_python.py` — Python transpiler
- `optimizer.py` — AST optimization passes
- `cli.py` — Command-line interface
- `mapanare.lark` — Grammar definition
