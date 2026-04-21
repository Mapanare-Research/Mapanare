# v4.10.0 — Drop Glue Complete — Continuation Prompt

> Remove skip_struct_ret. Every function gets proper cleanup.
> You are in WSL. Run valgrind after every change.

---

## Context

v4.9.0 fixed semantic.mn memory safety. The escape analysis in
emit_llvm_text.py is correct — it compares tracked values against
return value pointers. Now safe to enable for struct returns.

## Rules

- Run valgrind after EVERY change
- If valgrind shows new "Invalid read" or "Invalid free", stop and fix
- The escape analysis must handle: strings in structs, closures in structs,
  lists in structs, enums with string payloads
- Test string pooling with valgrind (cached strings must not be freed)
