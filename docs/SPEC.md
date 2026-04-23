# Mapanare Language Specification

**Version:** 5.3.3
**Status:** Live — synced to the v5.3.3 cut (2026-04-22)

Mapanare is an AI-native compiled programming language where agents, signals, streams, and tensors are first-class primitives -- not libraries. The production backend targets LLVM for native machine code; a C backend (gcc/clang) exists as fallback; a WebAssembly backend targets browser and server environments.

> **Spec sync discipline.** Each v4.x panel release fact-checks this
> spec against the live grammar (`mapanare/mapanare.lark`), type
> system (`mapanare/types.py`), and self-hosted lexer
> (`mapanare/self/lexer.mn`). The v4.129.0 documentation sync re-audits
> §2.1 (keywords + bilingual master list), §2.1.1 (master keyword
> table), §3 (type system), §6.3 (closures), §27.1 (stability count),
> §28 (stdlib), and Appendix B (compilation pipeline) against the
> v4.117.0–v4.128.0 changes. If you discover drift, open a
> documentation issue against the specific section number.

---

## 1. Language Goals and Non-Goals

### Goals

- **AI-native primitives.** Agents, signals, streams, and tensors are built into the language, not imported from libraries. AI workflows are expressible without external frameworks.
- **Compiled.** Mapanare is always compiled. The production backend targets LLVM for native machine code; a C backend (gcc/clang) exists as fallback; a WebAssembly backend targets browser and server environments.
- **Simple, familiar syntax.** The syntax draws from Rust (enums, pattern matching), TypeScript (type annotations, generics), and Python (readability, minimal ceremony).
- **Type-safe with inference.** Static types catch errors at compile time. Type inference reduces annotation burden -- you write types where they clarify, the compiler infers the rest.
- **Concurrency via agents and message passing.** No raw threads, no shared mutable state. Agents are concurrent actors that communicate through typed channels.
- **Reactive via signals.** Signals propagate changes automatically. Computed values recompute when their dependencies change, enabling declarative reactive dataflow.
- **Pipeline-oriented.** The `|>` pipe operator chains transformations naturally. Named pipelines compose agents into data-processing graphs.
- **ML-ready (via GPU builtins).** GPU-accelerated tensor operations via `gpu_tensor_add/mul/matmul` builtins using CUDA. `Tensor<T>[shape]` type with compile-time shape verification is planned.

### Non-Goals

- **Not a general-purpose systems language.** Mapanare does not aim to replace C or Rust for kernel development, device drivers, or bare-metal programming.
- **Not interpreted.** All Mapanare code is compiled before execution. An interactive REPL exists (`mapanare repl`) but it compiles each input before evaluating.
- **No garbage collector in native mode.** The LLVM backend uses arena-based memory management with scope-level cleanup and tag-bit freeing for heap-allocated strings.
- **No OOP class hierarchies.** There are no classes, no inheritance, no `extends`. Use agents for concurrent behavior and structs for data.
- **Not backwards-compatible with Python syntax.** Mapanare's syntax is its own: valid Python is not valid Mapanare and vice versa. (The legacy Python transpiler emitter `mapanare/emit_python_mir.py` was removed in v4.58.0; `mapanare bind --lang python` is the canonical Python-interop path via compiled `.so` + ctypes.)

---

## 2. Lexical Structure

### 2.1 Keywords

The following identifiers are reserved as keywords and cannot be used
as variable, function, struct, enum, or type names. Attempting to do so
is a parse error (`MN-P-006: unexpected token`) — for example
`let sino = 42` fails because `sino` is the Spanish form of `else`.
All keywords are case-sensitive and match only whole-word tokens
(`ifcount` is a valid identifier; `if` is not).

Every keyword listed below is hard-reserved in both lexers: the
Python bootstrap grammar at `mapanare/mapanare.lark:380-427` and the
self-hosted lexer at `mapanare/self/lexer.mn:59-177`
(`is_keyword` and `keyword_token_type`). The two lists are kept in
lock-step. Section 2.1.1 gives the authoritative alphabetical master
list; sections 2.1.2 onward group the same keywords by role for
readability. Tokens reserved for *future* use but not currently
tokenized live in Appendix C.

#### 2.1.1 Reserved Keyword Master List

Every token in the following table is reserved by both lexers and
cannot appear as an identifier. Bilingual pairs are grouped on the
same row; multi-alias keywords (`trait`/`modo`/`way`) list every
spelling.

| English | Spanish / alias | Category | AST role |
|---|---|---|---|
| `agent` | — | Declarations | Define an agent |
| `assert` | — | Control flow | Boolean assertion |
| `async` | — | Concurrency | Mark a function as a coroutine (see §29) |
| `await` | — | Concurrency | Suspend until a `Future` resolves (see §29) |
| `break` | `sal` | Control flow | Exit innermost loop |
| `const` | — | Bindings | Compile-time constant: `const N: T = EXPR`; requires a type annotation and a constant-foldable initializer (see §2.1 note) |
| `continue` | `sigue` | Control flow | Skip to next loop iteration |
| — | `da` | Functions | Spanish form of `return` |
| — | `di` | Statements | Print statement: `di expr` lowers to `print(expr)` |
| `else` | `sino` | Control flow | Alternative branch |
| `en` | — | Control flow | Spanish form of `in` |
| `enum` | — | Declarations | Algebraic data type |
| `export` | — | Modules | Re-export declaration |
| `extern` | — | Functions | FFI declaration |
| `false` | — | Literals | Boolean literal |
| `fn` | — | Functions | Function declaration |
| `for` | `cada` | Control flow | For-in loop |
| `if` | `si` | Control flow | Conditional branch |
| `impl` | — | Declarations | Method implementation block |
| `import` | `usa` | Modules | Module import |
| `in` | `en` | Control flow | For-loop iterable keyword |
| `input` | — | Agents | Channel declaration inside `agent` block |
| `let` | `pon` | Bindings | Immutable binding |
| `match` | — | Control flow | Pattern matching expression |
| `mut` | — | Bindings | Mutable binding modifier |
| `new` | — | Declarations | Struct construction |
| `none` | `nada` | Literals | `Option<T>::None` |
| `output` | — | Agents | Channel declaration inside `agent` block |
| `pipe` | — | Declarations | Pipeline declaration |
| `pub` | — | Visibility | Public visibility modifier |
| `return` | `da` | Functions | Return from function |
| `self` | `yo` | Functions | Method receiver |
| `signal` | — | Declarations | Reactive signal declaration |
| `spawn` | — | Concurrency | Agent spawn |
| `stream` | — | Declarations | Stream declaration |
| `struct` | — | Declarations | Struct declaration |
| `sync` | — | Concurrency | Agent/stream synchronization |
| `Tensor` | — | Types | Tensor type constructor (§7) |
| `trait` | `modo`, `way` | Declarations | Trait declaration |
| `true` | — | Literals | Boolean literal |
| `type` | `tipo` | Declarations | Type alias |
| `while` | `mien` | Control flow | While loop |
| `_` | — | Patterns | Wildcard pattern |

> **Cross-reference audit (v4.113.0).** Every row above has been
> checked against both lexer sources as of the v4.113.0 cut. If a
> future change adds or removes a keyword in one lexer, this table
> and the other lexer must be updated together; a mismatch is a
> bootstrap-breaking bug. The audit procedure is recorded in
> `docs/roadmap/v4/v4.113.0/artifacts/keyword-audit.md`.

#### Bindings and Mutability

| Keyword | Description |
|---|---|
| `let` | Declare an immutable binding. Also used at module scope: a top-level `let NAME: Type = value` declares a module-level immutable value visible to every function in the module. |
| `mut` | Declare a mutable variable binding: `let mut x = 0`. `let mut` is block-scoped and is not permitted at module scope (use `const` for module-level immutables, or wrap in `fn main()` for mutable state). The parser rejects module-level `let mut` with diagnostic E420. |

> **Note (v4.55.0, updated v4.129.0):** `const` is a Mapanare keyword.
> Its history is non-linear: v4.18.0 introduced it as a parser alias
> for module-level `let` with no additional semantics; v4.27.0
> removed that alias during post-review recovery because the feature
> was a shell; v4.55.0 reintroduced it as a real definition form
> (`ConstDef` in `mapanare/ast_nodes.py`, `const_def` rule in
> `mapanare/mapanare.lark`) with distinct semantics from module-level
> `let`:
>
> - Requires a type annotation and a constant-foldable initializer
>   (literals, other `const` references, and arithmetic on
>   constants). Non-constant initializers are rejected at compile
>   time with a diagnostic.
> - Registered under `SymbolKind.CONST` in the semantic checker,
>   distinct from `VARIABLE`; immutability is enforced.
> - Usable in tensor-shape positions, where `let`-bound values are
>   not.
>
> ```mn
> const MAX_RETRIES: Int = 3
> const TAU: Float = 2.0 * 3.141592653589793
> ```
>
> v4.126.0 fixed `is_definition_start` in the self-hosted parser
> (`mapanare/self/parser.mn`) to recognize `KW_CONST` at module
> scope; goldens `54_const_basic` and `58_const_scope` pass through
> both Python bootstrap and `mnc-stage1`.

#### Functions and Definitions

| Keyword | Description |
|---|---|
| `fn` | Define a function. |
| `return` | Return a value from a function. If omitted, the last expression is the return value. |
| `pub` | Mark a definition as publicly visible outside its module. |
| `self` | Reference to the current agent or struct instance within `impl` blocks. |
| `extern` | Declare a foreign function interface (FFI) binding. |

#### Agents and Concurrency

| Keyword | Description |
|---|---|
| `agent` | Define an agent (concurrent actor with typed input/output channels). |
| `spawn` | Create and start a new agent instance. Returns a handle to the running agent. |
| `sync` | Await and retrieve an asynchronous result from an agent output or stream. |

#### Reactive and Streaming

| Keyword | Description |
|---|---|
| `signal` | Declare a reactive signal binding. |
| `stream` | Declare a stream binding. |
| `pipe` | Define a named pipeline composing agents or functions via `|>`. |

#### Control Flow

| Keyword | Description |
|---|---|
| `if` | Conditional branch. |
| `else` | Alternative branch for `if`. |
| `match` | Pattern matching expression. Exhaustiveness is checked at compile time. |
| `for` | Loop over an iterable: `for x in items { }`. |
| `while` | Loop while a condition is true: `while cond { }`. |
| `in` | Used with `for` to specify the iterable. |
| `break` | Exit the innermost `for` or `while` loop immediately. |
| `continue` | Skip to the next iteration of the innermost `for` or `while` loop. |
| `assert` | Assert a boolean condition; abort with an error if false. |

#### Types and Data

| Keyword | Description |
|---|---|
| `type` | Define a type alias: `type Name = String`. |
| `struct` | Define a data structure with named fields. |
| `enum` | Define an algebraic data type (tagged union / sum type). |
| `impl` | Implement methods on a struct, enum, or agent. |
| `trait` | Define a trait (interface): a set of method signatures that types can implement. |
| `new` | Construct a struct instance: `new Point { x: 1.0, y: 2.0 }`. |

#### Modules

| Keyword | Description |
|---|---|
| `import` | Import definitions from another module. |
| `export` | Re-export definitions from the current module. |

#### Literals

| Keyword | Description |
|---|---|
| `true` | Boolean literal for true. |
| `false` | Boolean literal for false. |
| `none` | The `None` variant of `Option<T>`, representing absence of a value. |

#### Contextual Keywords

These identifiers are keywords only in specific grammar positions:

| Keyword | Context |
|---|---|
| `input` | Inside `agent` blocks — declares an input channel. |
| `output` | Inside `agent` blocks — declares an output channel. |
| `Tensor` | Type expressions — the tensor type constructor. |
| `any` | Type expressions — the dynamic type. |
| `_` | Pattern matching — wildcard pattern. |

#### Bilingual Keywords

> **v4.31.0 correction.** Earlier drafts listed `di` in the Contextual
> Keywords table with the description *"Bilingual alias for `let`"*.
> That was wrong on both counts. `di` is a **statement keyword** (not
> contextual — it is reserved unconditionally in every grammar
> position), and it is a **print alias**, not a `let` alias. It
> lowers through `di_stmt` to a `PrintStmt` in `parser.py:606`. The
> table below is the canonical bilingual keyword list — every
> English keyword with a Spanish alias is listed alongside its
> counterpart. Coral flagged the `di` mislabel five review cycles
> before v4.31.0; this release closes the carry-forward.

Mapanare supports a Spanish-language keyword layer in parallel with
the English layer. Both spellings lower to the same AST node, so a
single program can mix them. The table is exhaustive:

| English | Spanish | Role |
|---|---|---|
| `let` | `pon` | Local binding (`let x = 1` ≡ `pon x = 1`) |
| `return` | `da` | Return from a function |
| `self` | `yo` | Method receiver |
| `if` | `si` | Conditional branch |
| `else` | `sino` | Alternative branch |
| `for` | `cada` | For-loop |
| `while` | `mien` | While-loop |
| `in` | `en` | For-loop iterable binding |
| `type` | `tipo` | Type alias / tagged record |
| `trait` | `modo` | Trait declaration (also `way`) |
| `import` | `usa` | Module import |
| `none` | `nada` | `None` literal |
| `break` | `sal` | Loop break |
| `continue` | `sigue` | Loop continue |
| `print(...)` | `di <expr>` | Print expression (statement form) |

Keywords that currently only have an English spelling:

`fn`, `pub`, `agent`, `spawn`, `sync`, `signal`, `stream`, `pipe`,
`match`, `struct`, `enum`, `impl`, `export`, `extern`, `true`,
`false`, `new`, `input`, `output`, `assert`.

Also reserved by both lexers: `async`, `await` (hard keywords since
v4.68.0 / v4.72.0 — see §29 for the coroutine specification), `di`
(Spanish print statement, §9), `const` (compile-time constant — see the `const` note in
the *Bindings and Mutability* subsection below), `input`, `output`, `Tensor`, `_`.

The self-hosted lexer (`mapanare/self/lexer.mn`) treats both columns
as keywords. The Python bootstrap lexer is defined in
`mapanare/mapanare.lark` — each bilingual alias appears as a second
pattern on the same terminal (e.g. `KW_RETURN.2: /(?:return|da)(?![a-zA-Z0-9_])/`).
Section 2.1.1 above is the authoritative master list — whenever a
keyword is added or removed, both lexers, §2.1.1, and Appendix C
must be updated in the same commit.

### 2.2 Operators

#### Pipe Operator

| Operator | Name | Description |
|---|---|---|
| `\|>` | Pipe | Pass the result of the left-hand expression as the first argument to the right-hand function or agent. Enables left-to-right data flow. |

```mn
let result = data |> tokenize |> classify |> format
// Equivalent to: format(classify(tokenize(data)))
```

#### Type and Function Operators

| Operator | Name | Description |
|---|---|---|
| `->` | Return type | Annotates the return type of a function: `fn foo() -> Int`. |
| `=>` | Arrow | Used in lambda expressions and match arms: `(x) => x + 1` or `Some(v) => v`. |
| `::` | Namespace | Access a namespaced item: `Math::sqrt`, `Option::Some`. Also used for turbofish generic calls: `foo::<Int>(x)`. |
| `@` | Decorator | Apply a compile-time annotation or decorator to a definition. Also used for matrix multiplication on tensors: `a @ b`. |

#### Arithmetic Operators

| Operator | Name | Description |
|---|---|---|
| `+` | Add | Addition for numeric types, concatenation for strings. |
| `-` | Subtract | Subtraction. Also unary negation: `-x`. |
| `*` | Multiply | Multiplication. |
| `/` | Divide | Division. Integer division for `Int`, floating-point division for `Float`. |
| `%` | Modulo | Remainder after integer division. |

#### Comparison Operators

| Operator | Name | Description |
|---|---|---|
| `==` | Equal | Structural equality. |
| `!=` | Not equal | Structural inequality. |
| `<` | Less than | Ordering comparison. |
| `>` | Greater than | Ordering comparison. |
| `<=` | Less or equal | Ordering comparison. |
| `>=` | Greater or equal | Ordering comparison. |

#### Logical Operators

| Operator | Name | Description |
|---|---|---|
| `&&` | Logical AND | Short-circuiting conjunction. |
| `\|\|` | Logical OR | Short-circuiting disjunction. |
| `!` | Logical NOT | Boolean negation. |

#### Assignment Operators

| Operator | Name | Description |
|---|---|---|
| `=` | Assign | Assign a value to a mutable binding. |
| `+=` | Add-assign | `x += 1` is equivalent to `x = x + 1`. |
| `-=` | Subtract-assign | Compound subtraction assignment. |
| `*=` | Multiply-assign | Compound multiplication assignment. |
| `/=` | Divide-assign | Compound division assignment. |

#### Other Operators

| Operator | Name | Description |
|---|---|---|
| `..` | Range | Create an exclusive range: `0..10`. |
| `..=` | Range inclusive | Create an inclusive range: `0..=10`. |
| `?` | Error propagation | Unwrap a `Result` or `Option`. If `Err` or `None`, return early from the enclosing function. Modeled after Rust's `?` operator. |
| `<-` | Send | Send a value into an agent's input channel: `agent.input <- value`. |

#### Operator Precedence (Highest to Lowest)

| Precedence | Operators |
|---|---|
| 1 (highest) | `::` `@` `.` |
| 2 | `!` `-` (unary) |
| 3 | `*` `/` `%` `@` (matmul) |
| 4 | `+` `-` |
| 5 | `..` `..=` |
| 6 | `\|>` |
| 7 | `<` `>` `<=` `>=` |
| 8 | `==` `!=` |
| 9 | `&&` |
| 10 | `\|\|` |
| 11 | `?` |
| 12 | `=` `+=` `-=` `*=` `/=` `<-` |
| 13 (lowest) | `=>` |

### 2.3 Literals

#### Numeric Literals

```mn
let a: Int = 42
let b: Int = 1_000_000       // underscores for readability
let c: Float = 3.14
let d: Float = 1.0e-10       // scientific notation
let e: Int = 0xFF             // hexadecimal
let f: Int = 0b1010           // binary
let g: Int = 0o77             // octal
```

#### String Literals

```mn
let s = "hello, world"
let multi = "line one\nline two"
let interpolated = "value is ${x}"   // string interpolation
let multiline = """
    This is a multi-line
    string literal
"""
```

String interpolation with `${expr}` is supported in both regular and triple-quoted strings.
Any valid expression can appear inside `${...}`, including function calls and binary operations:

```mn
let name = "world"
print("Hello, ${name}!")
print("sum: ${a + b}")
print("length: ${len(items)}")
```

#### Character Literals

```mn
let c: Char = 'a'
let newline: Char = '\n'
let backslash: Char = '\\'
```

A `Char` literal is a single Unicode scalar value enclosed in single quotes. Escape sequences are supported: `\n`, `\t`, `\r`, `\\`, `\'`.

#### Boolean and None Literals

```mn
let t = true
let f = false
let absent: Option<Int> = none
```

### 2.4 Comments

<!-- pseudo -->
```mn
// Single-line comment

/* Multi-line
   block comment */

/// Doc comment — attached to the following definition
/// and available to tooling and documentation generators
```

Doc comments (`///`) are captured by the parser and associated with the following function, agent, struct, enum, trait, or type alias definition.

### 2.5 Identifiers

Identifiers start with a letter or underscore, followed by letters, digits, or underscores: `[a-zA-Z_][a-zA-Z0-9_]*`. Identifiers are case-sensitive.

---

## 3. Type System

### 3.1 Primitive Types

| Type | TypeKind | Description |
|---|---|---|
| `Int` | `INT` | 64-bit signed integer. |
| `Float` | `FLOAT` | 64-bit IEEE 754 floating-point number. |
| `Bool` | `BOOL` | Boolean value: `true` or `false`. |
| `String` | `STRING` | Immutable UTF-8 encoded string. |
| `Char` | `CHAR` | Single Unicode scalar value (code point). |
| `Void` | `VOID` | Unit type representing the absence of a value. Functions with no meaningful return value return `Void`. |

### 3.2 Generic Container Types

| Type | TypeKind | Description |
|---|---|---|
| `List<T>` | `LIST` | Dynamically-sized ordered collection of elements of type `T`. Arena-backed. |
| `Map<K, V>` | `MAP` | Hash map from keys of type `K` to values of type `V`. Keys must be hashable. Robin Hood hash table in native mode. |
| `Option<T>` | `OPTION` | A value that is either `Some(value)` or `None`. Represents the possible absence of a value without null pointers. |
| `Result<T, E>` | `RESULT` | A value that is either `Ok(value)` or `Err(error)`. Used for recoverable error handling. |
| `Signal<T>` | `SIGNAL` | Reactive container holding a value of type `T`. When the value changes, all dependents are notified and recomputed. |
| `Stream<T>` | `STREAM` | Asynchronous iterable producing values of type `T` over time. Supports backpressure. |
| `Channel<T>` | `CHANNEL` | Typed, bounded message channel for inter-agent communication. Carries values of type `T`. |
| `Tensor<T>[shape]` | `TENSOR` | N-dimensional array with element type `T` and compile-time verified shape. Example: `Tensor<Float>[3, 3]` is a 3x3 matrix of floats. |
| `Future<T>` | `FUTURE` | The pending result of an `async fn` call; resolved by `await` (inside another async context) or `block_on` (from synchronous code). Added v4.69.0; see §29. |

### 3.3 Compound / User-Defined Types

| Type | TypeKind | Description |
|---|---|---|
| `fn(A, B) -> C` | `FN` | Function type with parameter types and return type. Used for closures and function references. |
| `struct Name { ... }` | `STRUCT` | Named product type with typed fields. |
| `enum Name { ... }` | `ENUM` | Named sum type (tagged union) with variants. |
| `agent Name { ... }` | `AGENT` | Concurrent actor type with typed input/output channels. |
| `pipe Name { ... }` | `PIPE` | Named agent pipeline composition. |
| `type Name = ...` | `TYPE_ALIAS` | Type alias. |
| `trait Name { ... }` | `TRAIT` | Trait (interface) definition. |

### 3.4 Special Types

| Type | TypeKind | Description |
|---|---|---|
| `Range` | `RANGE` | Integer range created by `..` and `..=` operators. Used in `for` loops. |
| (type variable) | `TYPE_VAR` | Compiler-internal type variable for generic instantiation. |
| (unknown) | `UNKNOWN` | Compiler-internal placeholder for unresolved types. Compatible with all types during inference. |
| (builtin fn) | `BUILTIN_FN` | Compiler-internal type for builtin function references. |

### 3.5 Dynamic Type (`any`)

| Type | TypeKind | Description |
|---|---|---|
| `any` | `ANY` | Dynamic type — a boxed value that carries its runtime type tag. 24 bytes: `{i32 type_tag, i32 subtype, {ptr, i64} payload}`. |

The `any` type enables gradual typing: statically-typed code can interoperate with
dynamically-typed values at an explicit opt-in boundary.

#### Boxing and Unboxing

When a concrete value is assigned to an `any` variable, the compiler emits a
boxing call (`__mn_any_box_int`, `__mn_any_box_float`, `__mn_any_box_bool`,
`__mn_any_box_str`). The runtime type tag is stored alongside the payload.

```mn
let x: any = 42        // boxes Int → MnValue{tag=INT, payload=42}
let y: any = "hello"   // boxes String → MnValue{tag=STRING, payload=ptr}
```

#### Runtime Type Inspection

The `typeof` builtin returns the runtime type name as a `String`:

```mn
let x: any = 42
assert typeof(x) == "Int"
```

For concrete (non-`any`) types, `typeof` is resolved at compile time.

#### Compatibility Rules

- Any concrete type can be assigned to `any` (implicit boxing).
- `any` is compatible with all types for equality (`==`, `!=`) and comparison.
- Arithmetic on `any` values (`+`, `-`, `*`, `/`, `%`) is **rejected** at compile
  time with a clear error. Cast to a concrete type first.
- `any` values can be passed to functions expecting `any` parameters.

### 3.6 Type Inference Rules

Mapanare uses local type inference. The compiler infers types from the immediate context of each expression.

#### What is Inferred

- **Let bindings:** The type of a `let` binding is inferred from its initializer expression. An explicit annotation is optional.

  ```mn
  let x = 42              // inferred as Int
  let y = 3.14            // inferred as Float
  let z: String = "hello" // explicitly annotated
  let flag = true         // inferred as Bool
  ```

- **List element types:** Inferred from the first element. `[1, 2, 3]` is `List<Int>`.

- **Map key/value types:** Inferred from the first entry. `#{"a": 1}` is `Map<String, Int>`.

- **Lambda return types:** Inferred from the body expression. `(x) => x + 1` where `x: Int` returns `Int`.

- **Generic instantiation:** Generic type parameters are inferred at call sites from argument types. `identity(42)` infers `T = Int`.

#### What Must Be Annotated

- **Function parameters:** All function parameters require type annotations.

  ```mn
  fn add(a: Int, b: Int) -> Int {
      return a + b
  }
  ```

- **Function return types:** Required when the function signature needs to be clear. Can be omitted if the return type is `Void`.

- **Ambiguous generics:** When the compiler cannot determine the type parameter from context, use the turbofish syntax:

  ```mn
  let result = decode::<MyStruct>(json_string)
  ```

#### Type Checking Rules

- If a `let` binding has both an annotation and an initializer, their types must be compatible. A mismatch is a compile-time error.
- Arithmetic operators require both operands to be the same numeric type (`Int` or `Float`). No implicit numeric coercion.
- Comparison operators (`==`, `!=`, `<`, `>`, `<=`, `>=`) require both operands to be the same type.
- The condition in `if`, `while`, and `assert` must be `Bool`.
- The `?` operator requires the enclosing function to return `Result` or `Option`.

### 3.7 Struct Types

Structs are product types -- named collections of fields.

```mn
struct Point {
    x: Float,
    y: Float,
}
```

#### Struct Construction

Structs are constructed using the `new` keyword followed by the struct name and field initializers:

```mn
let p = new Point { x: 1.0, y: 2.0 }
```

The `new` keyword is required for LALR grammar disambiguation (it distinguishes struct literals from blocks after `if`/`for`/`while`).

#### Methods via `impl`

```mn
impl Point {
    fn distance(self, other: Point) -> Float {
        let dx = self.x - other.x
        let dy = self.y - other.y
        return Math::sqrt(dx * dx + dy * dy)
    }
}
```

#### Generic Structs

```mn
struct Pair<A, B> {
    first: A,
    second: B,
}
```

### 3.8 Enum Types (Algebraic Data Types)

Enums are sum types -- tagged unions where each variant can carry different data.

<!-- pseudo -->
```mn
enum Shape {
    Circle(Float),
    Rectangle(Float, Float),
    Triangle(Float, Float, Float),
}

fn area(shape: Shape) -> Float {
    match shape {
        Circle(r)          => 3.14159 * r * r,
        Rectangle(w, h)    => w * h,
        Triangle(a, b, c)  => {
            let s = (a + b + c) / 2.0
            return Math::sqrt(s * (s - a) * (s - b) * (s - c))
        },
    }
}
```

#### Variants

Each variant can carry zero or more values:

```mn
enum Token {
    Eof,                           // no data
    Number(Int),                   // one value
    Pair(String, Int),             // two values
}
```

#### Exhaustiveness

Match expressions on enums must be exhaustive -- every variant must be handled, or a wildcard `_` arm must be present. The compiler reports an error if a variant is missing and no wildcard is present.

#### Generic Enums

```mn
enum Either<A, B> {
    Left(A),
    Right(B),
}
```

### 3.9 Option and Result Types

#### Option<T>

`Option<T>` represents a value that may or may not be present. It replaces null pointers.

<!-- pseudo -->
```mn
let x: Option<Int> = Some(42)
let y: Option<Int> = none

match x {
    Some(v) => print("Got: ${v}"),
    None    => print("Nothing"),
}
```

`Option` values must be explicitly unwrapped before use. There is no implicit null.

**Construction:**
- `Some(value)` — wraps a value.
- `none` — the absent variant.

**Pattern matching:** See section 5 (Pattern Matching).

**Error propagation:** The `?` operator on an `Option<T>` unwraps `Some(v)` or returns `none` from the enclosing function (which must also return `Option`).

#### Result<T, E>

`Result<T, E>` represents an operation that can succeed with `Ok(value)` or fail with `Err(error)`. It is the primary error-handling mechanism.

<!-- pseudo -->
```mn
fn parse_int(s: String) -> Result<Int, String> {
    // ...
}

let result = parse_int("42")
match result {
    Ok(n)  => print("Parsed: ${n}"),
    Err(e) => print("Error: ${e}"),
}
```

**Construction:**
- `Ok(value)` — success variant.
- `Err(error)` — error variant.

**Error propagation:** The `?` operator provides concise error propagation:

```mn
fn process(s: String) -> Result<Int, String> {
    let n = parse_int(s)?    // returns Err early if parse fails
    return Ok(n * 2)
}
```

When `?` is applied to a `Result`, it unwraps `Ok(v)` for the expression's value or returns `Err(e)` from the enclosing function. The enclosing function must return a compatible `Result` type.

### 3.10 Agent Types

Agents have typed input and output channels that form their public interface.

```mn
agent Counter {
    input increment: Int
    output count: Int

    let mut state: Int = 0

    fn handle(increment: Int) -> Int {
        self.state += increment
        return self.state
    }
}
```

When you `spawn` an agent, the returned handle exposes the input and output channels with their declared types. See section 9 (Agent Model) for full semantics.

### 3.11 Tensor Types

> **Status:** Stable on LLVM backend. Tensor literals (v4.42.0), multi-dimensional indexing with bounds checking (v4.43.0), NumPy-style broadcasting (v4.44.0), reductions and slicing (v4.45.0). GPU-accelerated when CUDA/Vulkan available; CPU fallback otherwise.

Tensors have their element type and shape verified at compile time. Tensor literals use the `Tensor<Type>[elements]` syntax with nested brackets for multi-dimensional data:

<!-- pseudo -->
```mn
let v: Tensor<Float>[3] = Tensor<Float>[1.0, 2.0, 3.0]           // 1D vector
let m: Tensor<Float>[2, 3] = Tensor<Float>[[1.0, 2.0, 3.0],      // 2D matrix
                                            [4.0, 5.0, 6.0]]
let t: Tensor<Int>[2, 2, 2] = Tensor<Int>[[[1, 2], [3, 4]],      // 3D tensor
                                           [[5, 6], [7, 8]]]
```

The parser infers the shape from nesting depth and per-level element counts. Jagged arrays (sibling sub-arrays with different lengths) are rejected at parse time with a diagnostic message. Elements must be scalars — nested tensor composition is not supported.

Tensor elements are accessed via multi-dimensional indexing (v4.43.0):

```mn
let m = Tensor<Float>[[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]
let x: Float = m[1, 2]    // 6.0 — row 1, column 2
m[0, 0] = 99.0            // write element

let v = Tensor<Int>[10, 20, 30]
let y: Int = v[1]          // 20 — single index for 1-D
```

The number of indices must equal the tensor's rank; under-rank and over-rank indexing are compile errors. Bounds are checked at runtime — out-of-bounds access aborts with a diagnostic message showing the offending index and tensor shape.

Shape mismatches are compile-time errors:

```mn
let a: Tensor<Float>[3] = [1.0, 2.0, 3.0]
let b: Tensor<Float>[4] = [1.0, 2.0, 3.0, 4.0]
let c = a + b   // COMPILE ERROR: shape mismatch [3] vs [4]
```

Binary operations follow NumPy-style broadcasting rules (v4.44.0). Dimensions are compared right-to-left; a dimension pair is compatible if both are equal or one is 1. Shorter shapes are left-padded with 1s:

```mn
let a = Tensor<Float>[[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]   // [2, 3]
let b = Tensor<Float>[10.0, 20.0, 30.0]                      // [3]
let c = a + b       // Broadcast: [2, 3] + [3] -> [2, 3]

let d = a * 2.0     // Scalar broadcast: [2, 3] * scalar -> [2, 3]
```

Incompatible shapes produce a compile-time error with the offending dimension:

```mn
let x = Tensor<Float>[[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]   // [2, 3]
let y = Tensor<Float>[[1.0, 2.0], [3.0, 4.0]]                // [2, 2]
let z = x + y   // COMPILE ERROR: shapes [2, 3] and [2, 2] are not
                 //   broadcast-compatible; dimension 1 differs: 3 vs 2
```

Matrix multiplication verifies dimensional compatibility:

<!-- pseudo -->
```mn
let a: Tensor<Float>[2, 3] = ...
let b: Tensor<Float>[3, 4] = ...
let c = a @ b   // Result: Tensor<Float>[2, 4] -- inner dimensions must match
```

Tensors support global reduction methods (v4.45.0):

```mn
let t = Tensor<Float>[1.0, 4.0, 2.0, 5.0, 3.0]
let s = t.sum()      // 15.0
let m = t.mean()     // 3.0
let hi = t.max()     // 5.0
let lo = t.min()     // 1.0
let imax = t.argmax()  // 3 (index of max element)
let imin = t.argmin()  // 0 (index of min element)
```

Tensor slicing extracts sub-tensors using range (`N..M`) and wildcard (`_`) syntax (v4.45.0). Slicing returns a copy:

```mn
let v = Tensor<Float>[10.0, 20.0, 30.0, 40.0, 50.0]
let s = v[1..3]   // Tensor<Float>[20.0, 30.0]

let m = Tensor<Float>[[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]]
let rows = m[0..2, _]   // First two rows, all columns -> [2, 3]
```

### 3.12 Type Aliases

```mn
type Name = String
type Matrix = Tensor<Float>[3, 3]
type Callback = fn(Int) -> Bool
```

Type aliases are transparent -- the alias name and the underlying type are interchangeable.

### 3.13 Function Types

Function types describe the signature of a callable value (function pointer or closure):

```mn
type Predicate = fn(Int) -> Bool
type Mapper = fn(String) -> String

fn apply(f: fn(Int) -> Int, x: Int) -> Int {
    return f(x)
}
```

---

## 4. Control Flow

### 4.1 If / Else

`if` is an expression — it evaluates to a value when both branches are present.

```mn
if condition {
    // then branch
} else {
    // else branch
}
```

Chained conditions use `else if`:

```mn
if x > 10 {
    print("big")
} else if x > 0 {
    print("small")
} else {
    print("non-positive")
}
```

The condition must be of type `Bool`.

### 4.2 For Loop

Iterates over a range or iterable:

```mn
for i in 0..10 {
    print("${i}")
}

for item in items {
    process(item)
}
```

The loop variable is immutable within the body. The iterable can be a `Range`, `List<T>`, `Stream<T>`, or `Map<K, V>` (iterates over entries).

### 4.3 While Loop

Loops while a condition is true:

```mn
fn main() {
    let mut count = 0
    while count < 10 {
        print("${count}")
        count += 1
    }
}
```

The condition must be of type `Bool`. Evaluated before each iteration.

### 4.4 Break

`break` exits the innermost `for` or `while` loop immediately:

```mn
for i in 0..100 {
    if i > 10 {
        break
    }
}
```

### 4.5 Return

`return` exits the current function with a value:

```mn
fn double(x: Int) -> Int {
    return x * 2
}
```

`return` without a value returns `Void`. If omitted, the last expression in the function body is the implicit return value.

### 4.6 Match Expression

Pattern matching dispatches on the structure of a value. See section 5 (Pattern Matching) for full details.

<!-- pseudo -->
```mn
match value {
    Some(x) => print("got ${x}"),
    None    => print("nothing"),
}
```

### 4.7 Assert Statement

`assert` is a built-in statement that evaluates a boolean expression and aborts with an error if the result is `false`.

```mn
assert x > 0
assert len(items) == expected_count
assert result == 42, "Expected 42"
```

The optional second argument is an error message expression (typically a string). The compiler emits `assert` as an `Assert` MIR instruction, handled natively by both backends.

---

## 5. Pattern Matching

### 5.1 Syntax

<!-- pseudo -->
```mn
match expr {
    pattern1 => expr_or_block,
    pattern2 => expr_or_block,
    ...
}
```

Match arms are separated by commas. Each arm consists of a pattern, `=>`, and either an expression or a block.

### 5.2 Pattern Kinds

| Pattern | Syntax | Matches |
|---|---|---|
| **Constructor** | `Name(p1, p2, ...)` | Enum variant with the given name, binding inner values to sub-patterns. |
| **Literal** | `42`, `3.14`, `"hello"`, `true`, `false` | Exact value match for integers, floats, strings, and booleans. |
| **Identifier** | `x` | Matches anything, binding the value to the name `x`. |
| **Wildcard** | `_` | Matches anything, discarding the value. |

### 5.3 Destructuring

Enum variants are destructured by their constructor pattern:

<!-- pseudo -->
```mn
enum Expr {
    Num(Int),
    Add(Int, Int),
}

match expr {
    Num(n)    => print("number: ${n}"),
    Add(a, b) => print("sum: ${a + b}"),
}
```

Nested destructuring is supported:

<!-- pseudo -->
```mn
match result {
    Ok(Some(v)) => print("got ${v}"),
    Ok(None)    => print("ok but empty"),
    Err(e)      => print("error: ${e}"),
}
```

### 5.4 Exhaustiveness

The compiler checks that match expressions are exhaustive:

- For enum types, every variant must have a matching arm, OR a wildcard `_` arm must be present.
- For `Option<T>`, both `Some(...)` and `None` must be handled.
- For `Result<T, E>`, both `Ok(...)` and `Err(...)` must be handled.
- For `Bool`, both `true` and `false` must be handled, or a wildcard must be present.

A missing arm is a compile-time error.

### 5.5 Match Guards

A match arm can have an optional `if` guard between the pattern and `=>`:

<!-- pseudo -->
```mn
match n {
    x if x < 0 => "negative",
    0 => "zero",
    x if x > 0 => "positive",
    _ => "unreachable"
}
```

The guard expression must evaluate to `Bool`. If the guard is `false`, the match falls through to the next arm. Guards can reference names bound by the pattern (e.g., `Some(x) if x > 0`).

Guards do not affect exhaustiveness checking: a guarded arm's pattern counts toward coverage regardless of the guard's truth value.

### 5.6 Or-Patterns

A pattern can be a disjunction of alternatives separated by `|`:

<!-- pseudo -->
```mn
match token {
    Plus | Minus => "additive",
    Star | Slash | Mod => "multiplicative",
    Eof => "end",
    _ => "other"
}
```

All alternatives in an or-pattern must bind the same set of variable names. (The current implementation checks name-set equality only; type compatibility across alternatives is not yet enforced.) An or-pattern expands coverage: `A | B` covers both `A` and `B`.

Or-patterns can be combined with guards: `A | B if cond => body`. The guard applies to the whole arm (all alternatives), not to individual alternatives.

### 5.7 Match as Expression

When all arms produce a value, `match` is an expression:

<!-- pseudo -->
```mn
let name = match status {
    Ok(v) => v.name,
    Err(_) => "unknown",
}
```

### 5.8 The `?` Operator (Error Propagation)

The `?` operator propagates errors from `Result<T, E>` and unwraps `Option<T>`:

<!-- pseudo -->
```mn
fn parse_config(path: String) -> Result<Config, String> {
    let text = read_file(path)?
    let config = parse(text)?
    return Ok(config)
}
```

When applied to a `Result`, `?` returns the `Ok` value or early-returns the `Err`. When applied to an `Option`, `?` returns the `Some` value or early-returns `None`. The enclosing function must return a compatible `Result` or `Option` type.

---

## 6. Functions

### 6.1 Function Definition

```mn
fn name(param1: Type1, param2: Type2) -> ReturnType {
    // body
}
```

Functions can be marked `pub` for visibility outside the module:

```mn
pub fn add(a: Int, b: Int) -> Int {
    return a + b
}
```

### 6.2 Generic Functions

```mn
fn identity<T>(x: T) -> T {
    return x
}

let a = identity(42)       // T = Int
let b = identity("hello")  // T = String
```

### 6.3 Closures and Lambdas

Lambda expressions create anonymous functions:

```mn
let double = (x) => x * 2
let add = (a, b) => a + b
```

Multi-parameter lambdas use tuple syntax on the left of `=>`:

```mn
let sum = (a, b) => a + b
```

Note: Lambda parameter types are inferred from context. Type annotations on lambda parameters are not supported in the grammar — use a named function if explicit types are needed.

#### Capture Semantics

Closures capture variables from the enclosing scope:

<!-- pseudo -->
```mn
let offset = 10
let add_offset = (x) => x + offset
print(str(add_offset(5)))  // prints 15
```

**Implementation:** Closures with free variables are compiled as a pair: `{function_pointer, environment_struct_pointer}`. The environment struct contains the captured variables. Variables are captured by value (copy).

Closures without free variables are compiled as plain function pointers with no environment overhead.

### 6.4 Decorators

Decorators are compile-time annotations applied to definitions:

```mn
@test
fn test_addition() {
    assert 1 + 1 == 2
}

@supervised("one_for_one")
agent Worker {
    // ...
}
```

Built-in decorators:
- `@test` — marks a function as a test case.
- `@supervised(strategy)` — configures agent restart policy.
- `@restart(policy, max, window)` — detailed restart configuration.
- `@allow(permission)` — security permission annotation.

---

## 7. Trait System

### 7.1 Trait Declaration

A trait defines a set of method signatures that types can implement:

```mn
trait Display {
    fn to_string(self) -> String
}

trait Eq {
    fn eq(self, other: Self) -> Bool
}
```

Trait methods declare their signatures without bodies. The `self` parameter indicates the method receiver.

### 7.2 Trait Implementation

Types implement traits via `impl Trait for Type` blocks:

```mn
impl Display for Point {
    fn to_string(self) -> String {
        return "(${self.x}, ${self.y})"
    }
}

impl Eq for Point {
    fn eq(self, other: Point) -> Bool {
        return self.x == other.x && self.y == other.y
    }
}
```

The compiler verifies that all trait methods are implemented. Missing or extra methods are compile-time errors.

### 7.3 Builtin Traits

| Trait | Method | Signature | Description |
|---|---|---|---|
| `Display` | `to_string` | `(self) -> String` | Convert to human-readable string. |
| `Eq` | `eq` | `(self, other: Self) -> Bool` | Structural equality. |
| `Ord` | `cmp` | `(self, other: Self) -> Int` | Ordering comparison. Returns -1, 0, or 1. |
| `Hash` | `hash` | `(self) -> Int` | Hash value for use in maps/sets. |

### 7.4 Trait Bounds on Generics

Generic type parameters can be constrained with trait bounds:

```mn
fn print_value<T: Display>(x: T) {
    print(x.to_string())
}
```

The bound `T: Display` means `T` must implement the `Display` trait.

---

## 8. Module System

### 8.1 File-Based Modules

Each `.mn` file is a module. The module name is derived from the file path relative to the project root.

### 8.2 Imports

```mn
import encoding::json
import net::http {get, post}
import crypto
```

Import syntax:
- `import path::to::module` — imports the module, access via `module::item`.
- `import path::to::module {item1, item2}` — imports specific items into the local scope.
- Module paths use `::` as the separator.

### 8.3 Visibility

Definitions are private by default. The `pub` keyword makes a definition visible to other modules:

```mn
pub fn public_function() -> Int { return 42 }
fn private_function() -> Int { return 0 }

pub struct PublicStruct { field: Int }
```

### 8.4 Exports

The `export` keyword re-exports definitions:

```mn
export fn helper() -> Int { return 1 }
export name1, name2
```

### 8.5 Self-References

Within a multi-module compilation, `self::` refers to the current module:

```mn
import self::lexer
import self::parser
```

### 8.6 Circular Dependencies

The compiler detects circular imports and reports an error. Circular dependencies between modules are not allowed.

---

## 9. Agent Model

### 9.1 Overview

Agents are the fundamental concurrency primitive in Mapanare. They are concurrent actors that encapsulate state, communicate exclusively through typed message channels, and run independently of each other. There is no shared mutable state between agents.

### 9.2 Definition

```mn
agent MyAgent {
    input request: RequestType
    output response: ResponseType

    // Private state
    let mut counter: Int = 0

    // Handler: called when input is received
    fn handle(request: RequestType) -> ResponseType {
        self.counter += 1
        // process and return
    }

    // Lifecycle hooks (optional)
    fn on_init() { }
    fn on_stop() { }
}
```

Agent members:
- `input name: Type` — declares a typed input channel.
- `output name: Type` — declares a typed output channel.
- `let [mut] name = expr` — declares internal state.
- `fn name(...) { ... }` — defines methods. The `handle` method processes incoming messages.

### 9.3 Spawning and Communication

```mn
let a = spawn MyAgent()           // create and start agent
a.request <- some_value            // send input (non-blocking)
let result = sync a.response       // receive output (blocking)
```

- `spawn Name()` creates a new agent instance and starts it running.
- `<-` sends a message to an agent's input channel. The send is non-blocking; the message is queued in the agent's ring buffer.
- `sync expr` blocks the current execution until the agent produces an output.

### 9.4 Lifecycle

Every agent progresses through defined lifecycle states:

```
init --> running --> paused --> stopped
              |                   ^
              +-------------------+
```

| State | Description |
|---|---|
| `init` | Agent is created. `on_init()` is called. Resources are allocated. |
| `running` | Agent is processing messages from its input channels. |
| `paused` | Agent is temporarily suspended. Messages are buffered but not processed. |
| `stopped` | Agent has terminated. `on_stop()` is called. Resources are released. |

### 9.5 Typed Channels

Agent channels are typed and bounded. The type is declared in the agent definition. In the native runtime, channels are implemented as lock-free SPSC (single-producer, single-consumer) ring buffers.

### 9.6 Backpressure

When an agent's input buffer reaches capacity, the sending side is notified. The sender can:

- Block until space is available (default behavior with `sync`).
- Drop the message (configurable policy).
- Apply a timeout and fail with a `Result`.

Backpressure propagates through pipelines automatically.

### 9.7 Supervision

Agents can be configured with restart policies for failure recovery:

```mn
let worker = spawn MyAgent() @restart("always", 3, 60)
```

| Policy | Behavior |
|---|---|
| `always` | Restart the agent on any failure, up to `max` times within `window` seconds. |
| `never` | Let the agent stay stopped on failure. |
| `transient` | Restart only on unexpected failures (not on normal exit). |

Supervision trees can be built by having agents spawn and monitor child agents.

---

## 10. Signal Model

### 10.1 Overview

Signals are reactive primitives that hold a value and automatically propagate changes to dependents. They enable declarative, reactive dataflow without manual event wiring.

### 10.2 Declaration

```mn
fn main() {
    // Mutable signal: can be set directly
    let mut count = signal(0)

    // Computed signal: derived from other signals, read-only
    let doubled = signal { count.value * 2 }

    // Updating a signal
    count.value = 5
    print(doubled.value)   // prints 10
}
```

`signal(expr)` creates a mutable signal with an initial value. `signal { expr }` creates a computed signal that re-evaluates when its dependencies change.

### 10.3 Dependency Tracking

The compiler tracks which signals are read during the evaluation of a computed signal. When any dependency changes, the computed signal is marked dirty and recomputed on next access (lazy) or immediately (eager, configurable).

```mn
fn main() {
    let mut a = signal(1)
    let mut b = signal(2)
    let sum = signal { a.value + b.value }

    a.value = 10
    print(sum.value)   // prints 12
}
```

### 10.4 Subscribers

Signals support subscriptions for side effects on change:

<!-- pseudo -->
```mn
let mut temperature = signal(20.0)

// Subscribe to changes
temperature.subscribe((t) => {
    print("Temperature changed to ${t}")
})
```

### 10.5 Batched Updates

> **Note:** The `batch` block syntax is not yet implemented in the compiler. Signal batching is handled automatically by the runtime (see `mn_signal_batch_begin`/`mn_signal_batch_end` in the C runtime). This section describes the planned language-level syntax.

Multiple signal updates within a `batch` block are coalesced into a single recomputation pass, avoiding intermediate recalculations:

<!-- pseudo -->
```mn
batch {
    x.value = 10
    y.value = 20
    z.value = 30
}
// Dependents recompute once, not three times
```

### 10.6 Propagation Order

Signal updates propagate in topological order of the dependency graph. If signal A depends on signals B and C, A is recomputed only after both B and C have been updated.

---

## 11. Stream Model

### 11.1 Overview

Streams are asynchronous iterables that produce values over time. They are the primary abstraction for handling sequences of events, data chunks, and real-time feeds.

### 11.2 Declaration and Usage

```mn
// Create a stream from values
let s = Stream::from([1, 2, 3, 4, 5])

// Consume a stream
for value in s {
    print("${value}")
}
```

### 11.3 Stream Operators

Streams support a rich set of composable operators. These can be chained with the pipe operator.

| Operator | Description |
|---|---|
| `map(fn)` | Transform each element. |
| `filter(fn)` | Keep elements matching a predicate. |
| `flat_map(fn)` | Map each element to a stream, then flatten. |
| `take(n)` | Emit only the first `n` elements. |
| `skip(n)` | Skip the first `n` elements. |
| `chunk(n)` | Group elements into chunks of size `n`. |
| `zip(other)` | Pair elements from two streams. |
| `merge(other)` | Interleave elements from two streams. |
| `fold(init, fn)` | Reduce the stream to a single value. |
| `scan(init, fn)` | Like fold, but emits each intermediate accumulator. |
| `distinct()` | Remove consecutive duplicates. |
| `throttle(ms)` | Emit at most one element per time window. |
| `debounce(ms)` | Emit only after a quiet period. |
| `collect()` | Collect all elements into a `List`. |

<!-- pseudo -->
```mn
let result = numbers
    |> Stream::filter((n) => n % 2 == 0)
    |> Stream::map((n) => n * n)
    |> Stream::take(10)
    |> Stream::fold(0, (acc, n) => acc + n)
```

### 11.4 Backpressure

Streams have built-in backpressure. When a consumer processes values slower than the producer emits them, the producer is throttled automatically.

Backpressure strategies:

| Strategy | Behavior |
|---|---|
| `buffer(n)` | Buffer up to `n` elements, then apply backpressure. |
| `drop_oldest` | Drop the oldest buffered element when full. |
| `drop_newest` | Drop the newest (incoming) element when full. |
| `error` | Raise an error when the buffer overflows. |

### 11.5 Stream Fusion

The compiler optimizes adjacent stream operators by fusing them into a single pass. This eliminates intermediate allocations and reduces overhead. Fusion does not change observable behavior.

### 11.6 Lazy vs Eager

Stream operators are lazy by default — they are not evaluated until the stream is consumed (via `for`, `fold`, `collect`, or `for_each`). This enables efficient composition of long operator chains.

---

## 12. Pipe Definitions

Named pipelines compose agents into data-processing graphs:

```mn
agent Tokenizer {
    input text: String
    output tokens: List<String>

    fn handle(text: String) -> List<String> {
        return text.split(" ")
    }
}

agent Classifier {
    input tokens: List<String>
    output label: String

    fn handle(tokens: List<String>) -> String {
        if len(tokens) > 10 {
            return "long"
        }
        return "short"
    }
}

pipe ClassifyText {
    Tokenizer |> Classifier
}

let pipeline = spawn ClassifyText()
pipeline.text <- "Mapanare is an AI-native programming language"
let label = sync pipeline.label
print(label)
```

The pipe chain connects the output of one agent to the input of the next. The pipeline itself is spawned and used like a single agent — input goes to the first agent; output comes from the last.

---

## 13. Generics

### 13.1 Declaration

Functions, structs, enums, and agents can be parameterized over types using angle-bracket syntax:

```mn
fn identity<T>(x: T) -> T {
    return x
}

struct Pair<A, B> {
    first: A,
    second: B,
}

enum Either<A, B> {
    Left(A),
    Right(B),
}
```

### 13.2 Type Parameter Constraints

Type parameters can have trait bounds:

```mn
fn max<T: Ord>(a: T, b: T) -> T {
    if a.cmp(b) > 0 {
        return a
    }
    return b
}
```

### 13.3 Instantiation

Generic types are instantiated either by inference or explicitly:

```mn
// Inferred: T = Int from argument type
let x = identity(42)

// Explicit via turbofish syntax
let y = identity::<String>("hello")
let data = decode::<MyStruct>(json_string)
```

The turbofish syntax `name::<Type>(args)` explicitly provides type arguments at a call site. It is required when the compiler cannot infer the type parameter from the arguments alone.

### 13.4 Monomorphization

In the LLVM backend, generics are monomorphized at compile time. Each unique instantiation of a generic function or type generates a specialized version. There is no runtime polymorphism for generics.

---

## 14. Builtin Functions

The following functions are available without import:

| Function | Signature | Description |
|---|---|---|
| `print(value)` | `(Any) -> Void` | Print a value to stdout with a trailing newline. |
| `println(value)` | `(Any) -> Void` | **Deprecated.** Alias for `print`. Use `print` instead. |
| `len(collection)` | `(List<T> \| String \| Map<K,V>) -> Int` | Return the number of elements or characters. |
| `str(value)` | `(Any) -> String` | Convert a value to its string representation. |
| `toString(value)` | `(Any) -> String` | Alias for `str()`. |
| `int(value)` | `(Float \| String) -> Int` | Convert to integer. |
| `float(value)` | `(Int \| String) -> Float` | Convert to float. |
| `Some(value)` | `(T) -> Option<T>` | Wrap a value in `Some`. |
| `Ok(value)` | `(T) -> Result<T, E>` | Wrap a value in `Ok`. |
| `Err(error)` | `(E) -> Result<T, E>` | Wrap an error in `Err`. |
| `signal(value)` | `(T) -> Signal<T>` | Create a mutable signal with an initial value. |
| `stream(value)` | `(T) -> Stream<T>` | Create a stream from a value. |

---

## 15. String Methods

Strings support the following methods, all callable via dot syntax:

| Method | Signature | Description |
|---|---|---|
| `len()` | `() -> Int` | Return the byte length of the string. |
| `char_at(index)` | `(Int) -> String` | Return the character at the given index as a single-character string. |
| `byte_at(index)` | `(Int) -> Int` | Return the byte value at the given index. |
| `substr(start, length)` | `(Int, Int) -> String` | Extract a substring starting at `start` with the given `length`. |
| `find(needle)` | `(String) -> Int` | Return the index of the first occurrence of `needle`, or -1 if not found. |
| `contains(needle)` | `(String) -> Bool` | Return `true` if the string contains `needle`. |
| `starts_with(prefix)` | `(String) -> Bool` | Return `true` if the string starts with `prefix`. |
| `ends_with(suffix)` | `(String) -> Bool` | Return `true` if the string ends with `suffix`. |
| `split(delimiter)` | `(String) -> List<String>` | Split the string by `delimiter` and return a list of parts. |
| `trim()` | `() -> String` | Remove leading and trailing whitespace. |
| `trim_start()` | `() -> String` | Remove leading whitespace. |
| `trim_end()` | `() -> String` | Remove trailing whitespace. |
| `to_upper()` | `() -> String` | Convert to uppercase. |
| `to_lower()` | `() -> String` | Convert to lowercase. |
| `replace(old, new)` | `(String, String) -> String` | Replace all occurrences of `old` with `new`. |

Example:

```mn
let s = "  Hello, World!  "
let trimmed = s.trim()              // "Hello, World!"
let upper = trimmed.to_upper()      // "HELLO, WORLD!"
let parts = trimmed.split(", ")     // ["Hello", "World!"]
let found = trimmed.contains("World") // true
let sub = trimmed.substr(0, 5)      // "Hello"
```

---

## 16. List Operations

### 16.1 List Literals

```mn
let nums: List<Int> = [1, 2, 3, 4, 5]
let empty: List<String> = []
```

The element type is inferred from the first element, or from the type annotation if the list is empty.

### 16.2 Indexing

```mn
let first = nums[0]      // get element at index (0-based)
```

Out-of-bounds access is a runtime error.

### 16.3 Operations

| Operation | Syntax | Description |
|---|---|---|
| Get element | `list[index]` | Access element by index (0-based). |
| Push | `list.push(value)` | Append an element to the end. Requires `let mut`. |
| Length | `len(list)` | Return number of elements. |
| Iteration | `for item in list { }` | Iterate over elements. |

### 16.4 List in LLVM Backend

Lists are implemented as arena-backed dynamic arrays. In native mode, `__mn_list_new(elem_size)` allocates, `__mn_list_push(list, elem)` appends, and `__mn_list_get(list, index)` retrieves.

---

## 17. Map Operations

### 17.1 Map Literals

Map literals use the `#{ }` syntax:

```mn
let ages = #{"Alice": 30, "Bob": 25}
let empty: Map<String, Int> = #{}
```

Key and value types are inferred from the first entry.

### 17.2 Indexing

```mn
let age = ages["Alice"]       // get value by key
```

### 17.3 Operations

| Operation | Syntax | Description |
|---|---|---|
| Get value | `map[key]` | Access value by key. |
| Set value | `map[key] = value` | Insert or update a key-value pair. Requires `let mut`. |
| Length | `len(map)` | Return number of entries. |
| Contains | `map.contains(key)` | Check if key exists. |
| Delete | `map.delete(key)` | Remove a key-value pair. |
| Iteration | `for entry in map { }` | Iterate over key-value pairs. |

### 17.4 Map in LLVM Backend

Maps are implemented as a Robin Hood hash table in the C runtime, type-erased via `i8*`. Key types must be hashable (primitives and strings). The map supports iteration via `__mn_map_iter_new()`, `__mn_map_iter_next()`, `__mn_map_iter_free()`.

---

## 18. FFI (Foreign Function Interface)

### 18.1 C FFI

Declare external C functions using `extern "C"`:

```mn
extern "C" fn sqrt(x: Float) -> Float
extern "C" fn puts(s: String) -> Int
```

External functions can then be called directly:

```mn
let root = sqrt(2.0)
```

Link external libraries with the `--link-lib` flag:

```bash
mapanare build program.mn --link-lib m -o program
```

### 18.2 Python Interop

> **Note.** `extern "Python" fn` syntax was removed in v4.29.0 (the lexer rejects any non-`"C"` extern ABI). The canonical Python-interop path is `mapanare bind --lang python`, which compiles `.mn` → `.so` and emits a `ctypes` wrapper callable from CPython with typed argtypes/restype.

```bash
mapanare bind --lang python math_lib.mn -o math_lib.so
# Python:
#   from math_lib import add
#   assert add(3, 4) == 7
```

See §18.1 for C FFI details and §18.3 for calling conventions. The generated wrappers use the C ABI; Python-side bindings are `ctypes.CDLL` loads of the compiled shared library.

### 18.3 Calling Conventions

All FFI functions use the C calling convention. Types are mapped as:

| Mapanare Type | C Type |
|---|---|
| `Int` | `int64_t` |
| `Float` | `double` |
| `Bool` | `int32_t` (0 or 1) |
| `String` | `const char*` |
| `Void` | `void` |

---

## 19. Error Model

### 19.1 Structured Diagnostics

All compiler and runtime errors use structured codes in the format `MN-X0000`:

| Prefix | Category | Example |
|---|---|---|
| `MN-P` | Parse errors | `MN-P0001` unexpected token |
| `MN-S` | Semantic errors | `MN-S0001` undefined variable |
| `MN-L` | MIR lowering errors | `MN-L0001` unsupported node |
| `MN-C` | Code generation errors | `MN-C0001` LLVM emit failure |
| `MN-R` | Runtime errors | `MN-R0001` agent mailbox full |
| `MN-T` | Tooling errors | `MN-T0001` test discovery failure |

### 19.2 Error Reporting

Compiler errors include:
- **Error code** (e.g., `MN-S0001`).
- **Source location** (file, line, column).
- **Span** highlighting the offending code.
- **Message** describing the error.
- **Notes** with additional context (e.g., "did you mean X?").

Errors are formatted in Rust-style with color-coded output:

```
error[MN-S0001]: undefined variable `foo`
  --> src/main.mn:5:12
   |
5  |     let x = foo + 1
   |             ^^^ not found in this scope
```

### 19.3 Recoverable vs Panic Errors

- **Recoverable errors** use `Result<T, E>` and the `?` operator. These are the standard error-handling mechanism for operations that can fail (I/O, parsing, network).
- **Panics** (`assert` failures, out-of-bounds access, division by zero) terminate the program immediately with an error message and stack trace. Panics are not catchable.

---

## 20. Testing

### 20.1 Built-in Test Runner

Mapanare includes a built-in test runner invoked via `mapanare test`. Test functions are marked with the `@test` decorator and use `assert` statements for verification.

### 20.2 Test Syntax

```mn
@test
fn test_addition() {
    assert 1 + 1 == 2
}

@test
fn test_string_length() {
    let s = "hello"
    assert len(s) == 5
}
```

**Rules:**

- Test functions must be decorated with `@test`.
- Test functions take no parameters and return `Void`.
- `assert <expr>` evaluates the expression; if it is `false`, the test fails with an `AssertionError` including the source location.
- The optional second argument to `assert` is a message: `assert x > 0, "x must be positive"`.
- Test functions are discovered automatically in `.mn` files.

### 20.3 Test Discovery and Execution

```bash
mapanare test                          # run all tests in current directory
mapanare test path/to/tests/           # run tests in a specific directory
mapanare test --filter "test_add"      # run tests matching a substring
```

The test runner:

1. Scans `.mn` files for functions decorated with `@test`.
2. Compiles each test file through the MIR pipeline.
3. Executes each test function in a subprocess.
4. Reports pass/fail results with file:line locations and durations.

---

## 21. Observability

### 21.1 Tracing

Mapanare supports OpenTelemetry-compatible distributed tracing for agent operations. Tracing is enabled via the `--trace` CLI flag.

```bash
mapanare run --trace program.mn              # console output
mapanare run --trace=otlp program.mn         # OTLP HTTP export
```

Traced operations:

| Operation | Span Name | Attributes |
|-----------|-----------|------------|
| Agent spawn | `agent.spawn` | `agent.name`, `agent.id` |
| Message send | `agent.send` | `agent.name`, `channel` |
| Message handle | `agent.handle` | `agent.name`, `duration_ms` |
| Agent stop | `agent.stop` | `agent.name`, `reason` |
| Agent pause/resume | `agent.pause`, `agent.resume` | `agent.name` |

Spans carry W3C Trace Context (`trace_id`, `span_id`, `parent_span_id`) and are exportable via OTLP HTTP/JSON to any OpenTelemetry-compatible backend (Jaeger, Zipkin, Grafana Tempo, etc.).

### 21.2 Metrics

Prometheus-format metrics are served via the `--metrics` flag:

```bash
mapanare run --metrics :9090 program.mn
```

Exposed metrics:

| Metric | Type | Description |
|--------|------|-------------|
| `mapanare_agent_spawns_total` | Counter | Total agents spawned |
| `mapanare_agent_messages_total` | Counter | Total messages sent |
| `mapanare_agent_errors_total` | Counter | Total agent errors |
| `mapanare_agent_stops_total` | Counter | Total agents stopped |
| `mapanare_agent_handle_duration_seconds` | Histogram | Message handling latency |

### 21.3 Debug Info (DWARF) — **deferred to v5.x**

> **v4.29.0 correction.** Earlier drafts of this section claimed that binaries
> compiled with `-g` / `--debug` contain DWARF debug metadata. That claim was
> aspirational: the MIR already threads `SourceSpan` per instruction, but
> `LLVMTextEmitter` never emitted a single `!DICompileUnit`, `!DISubprogram`,
> `!DILocation`, `!DILocalVariable`, or `DICompositeType` node. Thirty-plus
> tests in `tests/llvm/test_dwarf_debug_info.py` had been silently
> `pytest.mark.skip`'d since v4.2.0, and the v4.26.0 seven-reviewer panel
> (Rattler #4) flagged it as a core hollow-feature case.
>
> The claim is hereby struck. DWARF debug info emission is deferred to the
> v5.x line. Until it lands:
>
> - The `-g` / `--debug` flag is still accepted (for forward compatibility
>   with scripts and IDEs that pass it unconditionally).
> - Every use of the flag prints a loud stderr warning naming v5.x as the
>   tracking version. The emitted IR/binary contains no DWARF metadata.
> - Source-level debuggers (`gdb`, `lldb`) will show only machine-level
>   frames for Mapanare programs. Stack traces from the C runtime are
>   fully symbolic (the C runtime is built with `-g` by default).
>
> When v5.x picks this up, it will build on the existing `SourceSpan`
> infrastructure; see `tests/llvm/test_dwarf_debug_info.py` for the
> regression gate that currently pins "no DWARF metadata" so the next
> implementation cannot land silently.

---

## 22. Deployment

### 22.1 Supervision Trees

Agents can be organized into supervision trees with configurable restart strategies:

```mn
@supervised("one_for_one")
agent Worker {
    input task: String
    output result: String

    fn handle(task: String) -> String {
        return process(task)
    }
}
```

| Strategy | Behavior |
|----------|----------|
| `one_for_one` | Restart only the failed agent |
| `one_for_all` | Restart all agents in the tree when one fails |
| `rest_for_one` | Restart the failed agent and all agents started after it |

### 22.2 Health Checks

Agent applications expose health and readiness endpoints:

- `/health` — liveness check (is the process running?)
- `/ready` — readiness check (are all agents initialized and running?)
- `/status` — detailed agent status (names, states, uptime)

### 22.3 Graceful Shutdown

On `SIGTERM`, the runtime:

1. Stops accepting new messages.
2. Drains in-flight messages from all agent mailboxes.
3. Calls `on_stop()` on each agent.
4. Exits cleanly within a configurable timeout (default: 30 seconds).

### 22.4 Deploy Scaffolding

```bash
mapanare deploy init                   # generate Dockerfile + config
```

Generates a multi-stage Dockerfile optimized for Mapanare agent applications.

---

## 23. GPU Computing

Mapanare provides GPU-accelerated tensor operations via built-in functions. GPU compute uses the CUDA Driver API loaded at runtime via `dlopen` — no SDK installation required. Programs degrade gracefully to CPU when no GPU is available.

```mn
fn main() {
    si gpu_available() {
        print("GPU: " + gpu_device_name())

        pon a: List<Float> = [1.0, 2.0, 3.0, 4.0]
        pon b: List<Float> = [5.0, 6.0, 7.0, 8.0]
        pon c: List<Float> = gpu_tensor_add(a, b)
        // c = [6.0, 8.0, 10.0, 12.0]
        print("c[0] = " + str(c[0]))
    }
}
```

### 23.1 Built-in GPU Functions

| Function | Signature | Description |
|----------|-----------|-------------|
| `gpu_available()` | `() -> Bool` | True if a CUDA GPU was detected |
| `gpu_device_name()` | `() -> String` | Device name (e.g., "NVIDIA GeForce RTX 4090") |
| `gpu_device_memory()` | `() -> Int` | Total VRAM in bytes |
| `gpu_tensor_add(a, b)` | `(List<Float>, List<Float>) -> List<Float>` | Element-wise addition |
| `gpu_tensor_sub(a, b)` | `(List<Float>, List<Float>) -> List<Float>` | Element-wise subtraction |
| `gpu_tensor_mul(a, b)` | `(List<Float>, List<Float>) -> List<Float>` | Element-wise multiplication |
| `gpu_tensor_div(a, b)` | `(List<Float>, List<Float>) -> List<Float>` | Element-wise division |
| `gpu_tensor_matmul(a, b, m, n, k)` | `(List<Float>, List<Float>, Int, Int, Int) -> List<Float>` | Matrix multiply (M,K)@(K,N) |

All tensor operations fall back to CPU when no GPU is available. No code changes needed.

### 23.2 Supported Backends

| Backend | Library | Detection | Status |
|---------|---------|-----------|--------|
| CUDA | `libcuda.so` / `nvcuda.dll` | `dlopen` at runtime | Functional (v3.46.0) |
| Vulkan | `libvulkan.so` / `vulkan-1.dll` | `dlopen` at runtime | Infrastructure present, not exposed as builtins |
| Metal | macOS/iOS framework | Compile-time detection | Planned |

Built-in PTX kernels for CUDA cover `add`, `sub`, `mul`, `div`, `matmul` at float64 precision.

### 23.3 Note: @gpu Decorator (reserved, no semantics)

> **Status (v4.27.0):** The `@gpu` / `@cuda` / `@vulkan` decorators are
> accepted by the parser as ordinary decorator attributes but have **no
> compiler behaviour**: no kernel extraction, no PTX/SPIR-V emission, no
> dispatch routing. GPU compute in Mapanare goes through the
> `gpu_tensor_*` runtime builtins (see §23.1/23.2), which are the
> supported surface for CUDA and Vulkan. The `lower.py` handler that
> previously raised `NotImplementedError` when one of these decorators
> was encountered was removed in v4.27.0 as part of the post-review
> recovery — the decorator was never wired to the runtime and claiming it
> was "auto-kernel extraction" misled users.
>
> The decorator names remain reserved. A future release may revive them
> as the user-facing entry point to the runtime kernel infrastructure,
> but doing so will require an AST-level extractor and a real end-to-end
> pytest — not a parser alias.

---

## 24. WebAssembly Backend

Mapanare compiles to WebAssembly (WAT text format and `.wasm` binary) for browser and server-side execution.

### 24.1 Compilation

```bash
mapanare emit-wasm source.mn              # Emit WAT text format
mapanare emit-wasm --binary source.mn     # Emit .wasm binary (invokes wat2wasm)
```

### 24.2 Target Triples

| Triple | Environment |
|--------|-------------|
| `wasm32-unknown-unknown` | Browser (no system calls, JS host) |
| `wasm32-wasi` | Server-side (WASI preview 1 syscalls) |

### 24.3 Memory Model

WebAssembly output uses a linear memory model:

- **Bump allocator** for dynamic allocations within a single WASM memory.
- **Strings** are length-prefixed in linear memory.
- **Closures** use `call_indirect` with a function table for dispatch.

### 24.4 JS Bridge

The `stdlib/wasm/bridge.mn` module provides browser interop:

| Function | Description |
|----------|-------------|
| `js_call(fn_name, args)` | Call a JavaScript function by name |
| `dom_query(selector)` | Query a DOM element |
| `dom_set_text(element, text)` | Set text content of a DOM element |
| `dom_on(element, event, handler)` | Attach an event listener |
| `fetch(url)` | HTTP fetch (returns `Result<String, String>`) |
| `set_timeout(handler, ms)` | Schedule a delayed callback |
| `set_interval(handler, ms)` | Schedule a repeating callback |

### 24.5 WASI Support

The `stdlib/wasm/runtime.mn` module provides WASI syscall wrappers:

| Function | WASI Syscall |
|----------|-------------|
| `fd_write(fd, data)` | `fd_write` |
| `fd_read(fd, len)` | `fd_read` |
| `args()` | `args_sizes_get` + `args_get` |
| `environ()` | `environ_sizes_get` + `environ_get` |
| `clock_time()` | `clock_time_get` |
| `proc_exit(code)` | `proc_exit` |
| `random(len)` | `random_get` |

### 24.6 Signal and Stream Support

Signals and streams compile to WASM with eager evaluation semantics. Signal subscriptions fire synchronously, and stream operators are inlined as direct function calls (no async runtime in WASM).

---

## 25. Mobile Cross-Compilation

Mapanare uses the same LLVM pipeline for mobile targets, with platform-specific target triples and runtime tuning.

### 25.1 Target Triples

| Triple | Platform |
|--------|----------|
| `aarch64-apple-ios17.0` | iOS ARM64 |
| `aarch64-linux-android34` | Android ARM64 |
| `x86_64-linux-android34` | Android emulator (x86_64) |

### 25.2 Building for Mobile

```bash
# iOS static library
mapanare build --target aarch64-apple-ios17.0 --lib app.mn

# Android shared library
mapanare build --target aarch64-linux-android34 --lib app.mn
```

The `--lib` flag produces a static archive (`.a`) for iOS or a shared library (`.so`) for Android, instead of a standalone executable. iOS linking uses `clang -target` or `libtool -static`; Android linking uses NDK clang with `-shared`.

### 25.3 Mobile Runtime Tuning

Mobile targets use smaller defaults to conserve memory and battery:

| Parameter | Desktop Default | Mobile Default | Compile-time Override |
|-----------|----------------|----------------|----------------------|
| Arena block size | 8 KB | 4 KB | `-DMAPANARE_DEFAULT_ARENA_BLOCK=4096` |
| Ring buffer slots | 1024 | 256 | `-DMAPANARE_DEFAULT_RING_CAPACITY=256` |
| Agent queue depth | 256 | 64 | `-DMAPANARE_DEFAULT_AGENT_QUEUE=64` |
| Signal batch interval | 16 ms | 1 ms | `-DMAPANARE_DEFAULT_BATCH_MS=1` |

All defaults are defined as `MAPANARE_DEFAULT_*` macros in `mapanare_platform.h` and can be overridden via compile-time `-D` flags. Platform detection is handled by `mapanare_platform.h` in the C runtime.

---

## 26. Example Programs

### Example 1: Hello World

The minimal Mapanare program. Top-level statements are automatically wrapped in `main`.

```mn
print("Hello, Mapanare!")
```

**Behavior:** Prints `Hello, Mapanare!` to standard output and exits.

### Example 2: Agent Definition

Demonstrates defining an agent with typed input and output channels, spawning it, sending a message, and synchronously receiving a result.

```mn
agent Greeter {
    input name: String
    output greeting: String

    fn handle(name: String) -> String {
        return "Hello, " + name + "!"
    }
}

let greeter = spawn Greeter()
greeter.name <- "World"
let result = sync greeter.greeting
print(result)
```

**Behavior:** Spawns a `Greeter` agent, sends `"World"` to its `name` input channel, waits for the `greeting` output, and prints `Hello, World!`.

**Key concepts illustrated:**
- `agent` keyword defines a concurrent actor.
- `input` and `output` declare typed channels.
- `spawn` creates a running agent instance.
- `<-` sends a value into a channel.
- `sync` blocks until the output is available.
- Top-level statements are automatically wrapped in `fn main()` by the compiler.

### Example 3: Multi-Agent Pipeline

Demonstrates composing multiple agents into a named pipeline using the `pipe` keyword and `|>` operator.

```mn
agent Tokenizer {
    input text: String
    output tokens: List<String>

    fn handle(text: String) -> List<String> {
        return text.split(" ")
    }
}

agent Classifier {
    input tokens: List<String>
    output label: String

    fn handle(tokens: List<String>) -> String {
        if len(tokens) > 10 {
            return "long"
        }
        return "short"
    }
}

pipe ClassifyText {
    Tokenizer |> Classifier
}

let pipeline = spawn ClassifyText()
pipeline.text <- "Mapanare is an AI-native programming language"
let label = sync pipeline.label
print(label)
```

**Behavior:** Defines two agents (`Tokenizer` and `Classifier`), composes them into a pipeline called `ClassifyText`, feeds in a sentence, and prints the classification label `short`.

**Key concepts illustrated:**
- `pipe` defines a named agent pipeline.
- `|>` connects the output of one agent to the input of the next.
- The pipeline itself is spawned and used like a single agent.
- Input goes to the first agent in the chain; output comes from the last.

---

## 27. Stability

### 27.1 What Is Frozen

Starting with v1.0.0, the following are frozen and will not change without an RFC and deprecation cycle:

- **Syntax:** All grammar rules defined in this specification.
- **Semantics:** Type checking rules, operator behavior, control flow semantics.
- **Type system:** All 29 TypeKind variants and their behavior (see `mapanare/types.py::TypeKind`).
- **Builtin functions:** Names, signatures, and behavior of all builtin functions.
- **String methods:** All 15 methods and their signatures.
- **Agent model:** Spawn, send, sync semantics, lifecycle states.
- **Signal model:** Creation, computed, subscription, batched update semantics.
- **Stream operators:** All documented operators and their behavior.
- **Error codes:** Format (`MN-X0000`) and assigned codes.

### 27.2 What Can Still Change

The following areas may evolve without a breaking change:

- **Standard library additions:** New modules and functions can be added.
- **Optimizer improvements:** Better optimization passes and strategies.
- **New compilation targets:** Additional CPU architectures and platforms.
- **Tooling:** New CLI commands, LSP features, formatter improvements.
- **Performance:** Implementation changes that do not affect observable behavior.

### 27.3 Breaking Change Process

Any change to a frozen area requires:

1. **RFC:** A written proposal in `docs/rfcs/` following the RFC template.
2. **Deprecation warning:** The old behavior must emit a compiler warning for at least one minor version.
3. **Migration guide:** Instructions for updating affected code.
4. **Major version bump:** Breaking changes require a new major version.

---

## 28. Standard Library

The standard library is written in Mapanare (`.mn`) and compiled via
LLVM. Modules live under `stdlib/` and are organized by domain. The
following sub-sections document public APIs for the modules with
stable, published surfaces. For the canonical list of shipped
modules, see the `stdlib/` directory.

**Domains currently covered:**

| Domain | Path prefix | Representative modules |
|---|---|---|
| Encoding | `encoding/` | `json`, `csv`, `toml`, `yaml` |
| Networking | `net/` | `http` (client), `http/server`, `websocket`, `http/session`, `http/sse` |
| Crypto | `crypto.mn` | SHA-1, SHA-256, HMAC, Base64, random, JWT |
| Text | `text/` | `regex` (PCRE2), `string_utils`, `text` |
| Database | `db/` | `sqlite`, `postgres`, `redis`, `embedded_kv`, `migrate`, `pool` |
| AI | `ai/` | `llm`, `embedding`, `rag`, `structured` |
| GPU | `gpu/` | `device`, `kernel`, `tensor` |
| Filesystem / system | `fs.mn`, `time.mn`, `log.mn`, `math.mn` | |
| Testing | `test/runner.mn` | built-in `@test` runner |
| WASM | `wasm/bridge.mn` | JS-interop bridge for the WASM backend |

The per-module subsections that follow describe the public API for
the most widely-used modules. New modules added after v4.129.0 should
be added to `stdlib/` and, if their API is intended as stable, get
a subsection here.

### JSON Module (`encoding/json`)

Types: `JsonValue` (enum: Null, Bool, Int, Float, Str, Array, Object), `JsonError`.

Functions:
- `decode(String) -> Result<JsonValue, JsonError>` — parse JSON string.
- `encode(JsonValue) -> String` — serialize to compact JSON.
- `encode_pretty(JsonValue, Int) -> String` — serialize with indentation.
- `stream_parse(String) -> Stream<JsonEvent>` — streaming parser.
- `validate(JsonValue, JsonSchema) -> Result<Bool, List<JsonError>>` — schema validation.

### CSV Module (`encoding/csv`)

Types: `CsvTable` (headers + rows), `CsvError`, `CsvConfig`.

Functions:
- `parse(String) -> Result<CsvTable, CsvError>` — parse CSV string.
- `parse_with(String, CsvConfig) -> Result<CsvTable, CsvError>` — parse with custom config.
- `to_string(CsvTable, String, String) -> String` — serialize to CSV string.
- `write(CsvTable, String) -> Result<Bool, CsvError>` — write to file.

### HTTP Client (`net/http`)

Types: `HttpMethod` (enum), `HttpRequest`, `HttpResponse`, `HttpError`, `HttpConfig`.

Functions:
- `get(String) -> Result<HttpResponse, HttpError>` — HTTP GET.
- `post(String, String) -> Result<HttpResponse, HttpError>` — HTTP POST.
- `put`, `delete`, `patch`, `head`, `options` — other methods.

### HTTP Server (`net/http/server`)

Types: `Route`, `Router`, `MatchResult`, `ServerConfig`.

Functions:
- `new_router() -> Router` — create router.
- `router_add_route(Router, String, String, String) -> Router` — add route.
- `match_route(String, String, String, String) -> MatchResult` — match request.
- `build_response(Int, Map<String, String>, String) -> String` — build HTTP response.

### WebSocket (`net/websocket`)

Types: `WsMessage` (enum: Text, Binary, Ping, Pong, Close), `WsConnection`, `WsError`, `WsFrame`.

Functions:
- `ws_connect(String) -> Result<WsConnection, WsError>` — connect to server.
- `ws_send(WsConnection, WsMessage)` — send message.
- `ws_recv(WsConnection) -> Result<WsMessage, WsError>` — receive message.
- `ws_close(WsConnection)` — close connection.

### Crypto (`crypto`)

Functions: SHA-1, SHA-256, HMAC, Base64 encode/decode, random bytes, JWT helpers. FFI to OpenSSL via `dlopen`.

### Regex (`text/regex`)

Functions: `regex_match`, `regex_search`, `regex_replace`, `regex_split`. Character classes, quantifiers, capture groups via PCRE2 FFI.

---

## 29. Futures and Async/Await

> **v4.72.0-v4.76.0 (Arc 9).** Async/await was implemented across arcs 8 and 9
> using LLVM switched-resume coroutines. See the [Coroutine Design Document](roadmap/v4/v4.67.0/DESIGN.md)
> for the full implementation spec. This section defines the user-visible semantics.
>
> **v4.115.0 status update.** Native file I/O and network I/O inside
> async pipelines were demonstrated end-to-end in
> `examples/async_file_io.mn` and `examples/async_http_demo.mn`. The
> async model is **cooperative, not preemptive**: async fns yield only
> at `await` points; synchronous runtime calls (`__mn_file_write`,
> `http_get`) block the current worker for their duration. Full
> non-blocking suspension is a v5.x target. The self-hosted compiler
> (`mnc-stage1`) does not yet lower async — async programs currently
> compile through the Python bootstrap's `emit-llvm` pipeline and link
> against `libmapanare_rt.a` for a native binary (docket Sh.4).

### 29.1 `async fn` -- Asynchronous Function Declaration

An `async fn` declares a function that can suspend and resume:

```mn
async fn fetch_data(url: String) -> String {
    let response = await http_get(url)
    return response.body
}
```

Semantics:

- The declared return type `T` is sugar for `Future<T>`. Calling an `async fn` does **not** execute the body -- it creates a suspended coroutine and returns a `Future<T>` handle immediately.
- The body executes when the returned future is driven by `await` (from another async context) or `block_on` (from synchronous code).
- An `async fn` may contain zero or more `await` expressions. An `async fn` with zero `await` points is valid -- it completes on first resume (single-step coroutine).
- `async fn` can call non-async functions freely. Non-async functions cannot use `await`.

### 29.2 `await expr` -- Suspension Point

```mn
let result = await some_async_fn(args)
```

`await` suspends the current coroutine until the operand future is ready.

- The operand must have type `Future<U>`. Type error otherwise.
- If the future is already `Ready`, the value is extracted immediately without suspending.
- If the future is `Pending`, the current coroutine suspends. The scheduler resumes it when the awaited future becomes `Ready`.
- The expression evaluates to type `U`.
- `await` is only valid inside `async fn` bodies. Using `await` outside an async context is a semantic error.

### 29.3 `Future<T>` -- The Future Type

`Future<T>` is a built-in generic type representing a value that may not be available yet.

**States:**

| State | Value | Meaning |
|-------|-------|---------|
| `Pending` | 0 | The coroutine has not yet produced a value. |
| `Ready` | 1 | The value is available. |

**LLVM representation:**

```llvm
%Future = type { i8, ptr }
; field 0: state (0 = Pending, 1 = Ready)
; field 1: payload pointer
;   Pending: ptr to the coroutine handle (for scheduler resume)
;   Ready:   ptr to the result value (heap-allocated T)
```

All `Future<T>` have the same LLVM type (`{i8, ptr}`) regardless of `T`, enabling a uniform scheduler queue.

**User-visible operations:**

| Operation | Context | Description |
|-----------|---------|-------------|
| `await future` | async fn body | Suspend until ready, extract `T` |
| `block_on(future)` | sync fn body | Run event loop until ready, return `T` |

No explicit `.poll()`, `.cancel()`, or `.then()` in v4.x. The scheduler is the sole driver.

### 29.4 `block_on(future)` -- Synchronous Driver

`block_on` is a built-in function that bridges synchronous and asynchronous code:

```mn
fn main() {
    let result: Int = block_on(compute())
}
```

- Drives the event loop until the given future resolves.
- Returns the unwrapped value of type `T`.
- May only be called from synchronous functions. Calling `block_on` from inside an `async fn` will deadlock (the event loop is already running).

### 29.5 Coroutine Lifecycle

1. **Creation.** Calling an `async fn` allocates a coroutine frame on the heap and returns a `Future<T>` in `Pending` state.
2. **First resume.** The scheduler (or `block_on`) calls `llvm.coro.resume` on the coroutine handle. Execution begins at the function entry point.
3. **Suspension.** At each `await` point, if the operand future is `Pending`, the coroutine saves its state and returns to the scheduler.
4. **Resumption.** When the awaited future becomes `Ready`, the scheduler resumes the suspended coroutine. Execution continues after the `await` expression.
5. **Completion.** When the coroutine reaches a `return` statement (or the end of the body), it stores the result, transitions the future to `Ready`, and destroys the coroutine frame.

### 29.6 Memory Model

- **Frame allocation.** Each coroutine frame is heap-allocated via `malloc`. LLVM's CoroElide pass may promote this to a stack allocation when the future's lifetime is bounded by the caller.
- **Spilled variables.** Values whose definitions and uses span a suspension point are stored in the coroutine frame. The LLVM CoroSplit pass handles this automatically.
- **Result allocation.** The result value is heap-allocated when the future becomes `Ready`. The caller frees it after extracting the value via `await` or `block_on`.
- **Destruction.** `llvm.coro.destroy` is called when the future is consumed or goes out of scope. This runs the coroutine's cleanup path and frees the frame.

### 29.7 Interaction with Other Primitives

| Primitive | Interaction |
|-----------|-------------|
| Agents | Agents run on their own threads. `async fn` runs within the caller's event loop. No implicit agent spawning. |
| Signals | Signal reads inside `async fn` are synchronous (no suspension). |
| Streams | `for await` iterates over an async stream, suspending between elements — *planned (v5.x)*. The `for await` grammar is not yet tokenized; today, iterate synchronously over a `Stream<T>` and `await` individual async-fn calls inside the loop body. |
| Closures | Closures may capture variables from the enclosing `async fn`. Captured values that cross suspension points are spilled into the coroutine frame. |

---

## 30. Package Management

Mapanare ships a first-class package manager as part of the standard
toolchain. This section is normative: it defines the manifest schema,
install semantics, lockfile format, version-constraint grammar, and
registry protocol that a conforming Mapanare distribution MUST
implement. The user-facing guide lives at `docs/guides/packages.md`;
the reference implementation is `stdlib/pkg.py`.

### 30.1 `mapanare.toml` Manifest

Every Mapanare project is identified by a `mapanare.toml` file at its
root. The file is TOML (v1.0) with the following tables.

**`[package]` table** — project metadata.

| Field | Required | Type | Meaning |
|---|---|---|---|
| `name` | yes | String | Package name. Lowercase, alphanumeric + hyphens (`[a-z0-9][a-z0-9-]*`). |
| `version` | yes | String | Semver 2.0.0 version (`MAJOR.MINOR.PATCH`). |
| `description` | no | String | One-line summary. |
| `license` | no | String | SPDX license identifier. |
| `repository` | no | String | Source repository URL. |
| `authors` | no | List\<String\> | Author names or `"Name <email>"` entries. |
| `entry` | no | String | Entry-point `.mn` file. Default: `"main.mn"`. |
| `mapanare_version` | no | String | Semver constraint on the toolchain. Default: `">=0.2.0"`. |

**`[dependencies]` table** — runtime dependencies. Each entry is
`name = <spec>` where `<spec>` is either a constraint string (e.g.
`"^1.0.0"`) or an inline table `{ version = "...", git = "...",
branch = "..." }` for git-backed dependencies.

**`[dev-dependencies]` table** — same shape as `[dependencies]`, but
installed only when running tests or local development targets.

Example:

```toml
[package]
name = "myapp"
version = "0.1.0"
description = "Example"
license = "MIT"
entry = "main.mn"

[dependencies]
json = "^1.0.0"
http-server = { version = "~2.0.0" }

[dev-dependencies]
mn_test = "*"
```

Unknown keys MUST be ignored, not rejected, to permit forward
compatibility with future extensions.

### 30.2 Version Constraints

Dependency specifications use a subset of the semver-range syntax:

| Syntax | Meaning |
|---|---|
| `^X.Y.Z` | Compatible: `>= X.Y.Z, < (X+1).0.0` (when `X>0`). |
| `~X.Y.Z` | Patch-only: `>= X.Y.Z, < X.(Y+1).0`. |
| `>=X.Y.Z` | Minimum version. |
| `>=X.Y.Z,<A.B.C` | Range. |
| `X.Y.Z` | Exact (pinned). |
| `*` | Any published version. |

Resolution strategy is **greedy latest-satisfying**: for each direct
dependency, the resolver selects the highest published version that
satisfies the constraint. There is no SAT solver. Transitive
dependency resolution is deferred; in v5.3.x, a package's
`[dependencies]` table is read but nested resolution across the
full graph is **not guaranteed** — projects that require it must
flatten dependencies manually or wait for a future spec revision.

If two constraints in the same manifest select incompatible versions
for the same package, installation MUST fail with a diagnostic.

### 30.3 `mapanare install` Semantics

The command `mapanare install [<name>[@<version>]]` performs:

1. **Manifest load.** Parse `mapanare.toml` at the working directory.
   Error if absent (unless a name argument was provided).
2. **Lock consultation.** If `mapanare.lock` exists and is consistent
   with the manifest, use the pinned versions recorded there. The
   lockfile is authoritative over the manifest when both are present.
3. **Resolution.** For each unresolved dependency, query the registry
   for the highest version satisfying the constraint (§30.2).
4. **Download.** Fetch the `.tar.gz` archive from the registry's
   download endpoint (§30.5).
5. **Integrity check.** Compute SHA-256 of the archive bytes. Compare
   against the `integrity` field returned by the registry. On
   mismatch, abort with no files written.
6. **Extract.** Unpack into `mn_modules/<name>-<version>/`. Existing
   directories for the same `<name>-<version>` are replaced
   atomically (write-then-rename).
7. **Lock update.** Write resolved versions and integrity hashes to
   `mapanare.lock`.

**Install-time scripts are not supported.** Packages MUST NOT execute
arbitrary code during install. The installer only unpacks files and
writes the lockfile.

**Side effects are confined to** the current project directory
(`mn_modules/`, `mapanare.lock`) and `~/.mapanare/cache/` for
downloaded archives.

### 30.4 `mapanare.lock` Lockfile

The lockfile is JSON with the following shape:

```json
{
  "lockfile_version": 1,
  "packages": [
    {
      "name": "json",
      "version": "1.0.0",
      "git": "https://mapanare.dev/api/packages/json/1.0.0/download",
      "commit": "sha256:abc123...",
      "integrity": "sha256:def456..."
    }
  ]
}
```

**Fields:**

| Field | Required | Meaning |
|---|---|---|
| `lockfile_version` | yes | Format version. Current: `1`. |
| `packages` | yes | Array of locked entries. |
| `packages[].name` | yes | Package name. |
| `packages[].version` | yes | Resolved version (exact). |
| `packages[].git` | yes | Download URL used at install time. |
| `packages[].commit` | yes | Archive content hash (SHA-256). |
| `packages[].integrity` | yes | Subresource-Integrity-style hash. |

The lockfile SHOULD be committed to version control. When present,
subsequent `mapanare install` invocations MUST reproduce the same
resolution (subject to the registry still serving the pinned
versions). A lockfile whose `lockfile_version` is higher than the
installer supports MUST cause the install to abort with a diagnostic
rather than silently downgrade.

### 30.5 Registry API

The default registry is `https://mapanare.dev`. The base URL is
overridable via the `MAPANARE_REGISTRY_URL` environment variable.

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `GET` | `/api/packages` | none | List all packages (paginated). |
| `GET` | `/api/packages?q=<term>` | none | Search by name/keyword. |
| `GET` | `/api/packages/{name}` | none | Package metadata + version list. |
| `GET` | `/api/packages/{name}/{version}` | none | Version details + integrity hash. |
| `GET` | `/api/packages/{name}/{version}/download` | none | Download `.tar.gz` archive. |
| `POST` | `/api/packages` | token | Publish a new version. |

**Authentication.** Publish requests carry a bearer token obtained
via GitHub OAuth (`mapanare login`) or provided inline
(`--token <value>` / `MAPANARE_TOKEN` env var). Tokens are stored at
`~/.mapanare/token`.

**Publish payload.** A `.tar.gz` archive containing `mapanare.toml`,
all `.mn` source files, and `README.md` / `LICENSE` if present.
Excluded: `mn_modules/`, hidden directories, `__pycache__/`,
`node_modules/`.

**Idempotency.** Publishing the same `(name, version)` twice MUST
be rejected by the registry. New versions bump semver per the
publisher's chosen level (`--minor`, `--major`, default `--patch`).

### 30.6 Security Model

- **SHA-256 integrity** on every download; mismatches abort install.
- **No install-time code execution.** Packages declare data and
  sources, not build actions.
- **Sandboxed module path.** Installed packages live under
  `mn_modules/` relative to the project root; resolution never
  escapes this directory.
- **Token storage.** Tokens are stored with user-only permissions
  (`0600`) under `~/.mapanare/`. They are never written to
  `mapanare.toml` or `mapanare.lock`.

### 30.7 Out of Scope for v5.x

The following are not specified by v5.3.3 and remain open for a
future revision: full transitive resolution with conflict detection,
version yanking, private registries, vendoring, cryptographic
signatures beyond SHA-256, and offline-first mirror support.
Implementations MAY experiment with these but MUST NOT rely on
them in documented behavior.

---

## Appendix A: Grammar Summary (EBNF Sketch)

This is a simplified sketch of the grammar. The authoritative grammar is in `mapanare/mapanare.lark`.

```ebnf
program        = { import_decl | definition | statement } ;
definition     = fn_def | agent_def | struct_def | enum_def
               | type_alias | pipe_def | impl_def | trait_def
               | impl_trait_def | export_def | extern_fn_def
               | decorated_def | doc_commented_def ;

fn_def         = ["pub"] "fn" IDENT ["<" type_params ">"]
                 "(" [params] ")" ["->" type] block ;
extern_fn_def  = "extern" STRING "fn" IDENT ["::" IDENT]
                 "(" [params] ")" ["->" type] ;
agent_def      = ["pub"] "agent" IDENT "{" { agent_member } "}" ;
struct_def     = ["pub"] "struct" IDENT ["<" type_params ">"]
                 "{" { field_def } "}" ;
enum_def       = ["pub"] "enum" IDENT ["<" type_params ">"]
                 "{" { variant } "}" ;
pipe_def       = ["pub"] "pipe" IDENT "{" pipe_chain "}" ;
impl_def       = "impl" IDENT "{" { fn_def } "}" ;
trait_def      = ["pub"] "trait" IDENT "{" { trait_method } "}" ;
impl_trait_def = "impl" IDENT "for" IDENT "{" { fn_def } "}" ;
import_decl    = "import" path [ "{" names "}" ] ;
export_def     = "export" ( definition | "{" names "}" ) ;
decorated_def  = { decorator } definition ;
decorator      = "@" IDENT [ "(" args ")" ] ;
doc_commented_def = { "///" text } definition ;

agent_member   = "input" IDENT ":" type
               | "output" IDENT ":" type
               | let_binding
               | fn_def ;

pipe_chain     = IDENT { "|>" IDENT } ;

type_expr      = fn_type | tensor_type | generic_type | named_type ;
generic_type   = IDENT "<" type_expr { "," type_expr } ">" ;
tensor_type    = "Tensor" "<" type_expr ">" "[" expr { "," expr } "]" ;
fn_type        = "fn" "(" [ type_expr { "," type_expr } ] ")" "->" type_expr ;

statement      = let_binding | assignment | expr | for_loop
               | while_loop | if_expr | match_expr | return_stmt
               | break_stmt | assert_stmt ;
let_binding    = "let" ["mut"] IDENT [":" type] "=" expr ;
for_loop       = "for" IDENT "in" expr block ;
while_loop     = "while" expr block ;
return_stmt    = "return" [expr] ;
break_stmt     = "break" ;
assert_stmt    = "assert" expr ["," expr] ;

expr           = assign_expr "=>" expr                    (* lambda *)
               | assign_expr ;
assign_expr    = or_expr [ ("=" | "+=" | "-=" | "*=" | "/=") assign_expr ]
               | or_expr "<-" assign_expr ;
or_expr        = and_expr { "||" and_expr } ;
and_expr       = eq_expr { "&&" eq_expr } ;
eq_expr        = cmp_expr { ("==" | "!=") cmp_expr } ;
cmp_expr       = pipe_expr { ("<" | ">" | "<=" | ">=") pipe_expr } ;
pipe_expr      = range_expr { "|>" range_expr } ;
range_expr     = add_expr [ (".." | "..=") add_expr ] ;
add_expr       = mul_expr { ("+" | "-") mul_expr } ;
mul_expr       = unary_expr { ("*" | "/" | "%" | "@") unary_expr } ;
unary_expr     = ("-" | "!") unary_expr | postfix_expr ;
postfix_expr   = atom_expr { call | method_call | field_access | index | "?" } ;

atom_expr      = INT | FLOAT | STRING | CHAR | "true" | "false" | "none"
               | "spawn" IDENT "(" [args] ")"
               | "sync" postfix_expr
               | "signal" "(" expr ")" | "signal" block
               | "stream" "(" expr ")"
               | if_expr | match_expr
               | "new" IDENT "{" { field_init } "}"
               | IDENT "::" "<" type_args ">" "(" [args] ")"  (* turbofish *)
               | IDENT "::" IDENT                              (* namespace *)
               | "self"
               | IDENT
               | "[" [expr { "," expr }] "]"                   (* list *)
               | "#{" [expr ":" expr { "," expr ":" expr }] "}" (* map *)
               | "(" expr ")"
               | "(" expr "," expr { "," expr } ")"           (* tuple *)
               ;
```

---

## Appendix B: Compilation Pipeline

### Overview

The Mapanare compiler uses a multi-stage pipeline with an intermediate representation (MIR) between the AST and final code emission:

```
.mn source --> Lexer --> Parser --> AST --> Semantic Analysis --> MIR Lowering --> MIR Optimizer --> Emitter
                                                                                                    |--> LLVM IR --> Native Binary
                                                                                                    |--> C Source  --> gcc/clang --> Native Binary
                                                                                                    +--> WebAssembly (WAT/WASM)
```

### MIR (Mid-level Intermediate Representation)

MIR is a typed, SSA-based intermediate representation that sits between the AST and code emission. It was introduced in v0.6.0 to decouple frontend analysis from backend code generation.

**Key properties:**

- **SSA form:** Each temporary is assigned exactly once. Phi nodes merge values at control-flow join points.
- **Typed:** Every instruction carries type information from the semantic checker.
- **Basic blocks:** Code is organized into basic blocks with explicit terminators (branch, switch, return, jump).
- **Three-address form:** Operations use `%temp = op(arg1, arg2)` style instructions.

**Instruction categories:**

| Category | Instructions |
|----------|-------------|
| **Arithmetic** | `Add`, `Sub`, `Mul`, `Div`, `Mod`, `Neg` |
| **Comparison** | `Eq`, `Ne`, `Lt`, `Le`, `Gt`, `Ge` |
| **Logic** | `And`, `Or`, `Not` |
| **Memory** | `Alloca`, `Load`, `Store`, `FieldGet`, `FieldSet` |
| **Control** | `Branch`, `Jump`, `Switch`, `Return`, `Phi` |
| **Calls** | `Call`, `CallBuiltin`, `CallMethod` |
| **Types** | `StructInit`, `EnumInit`, `EnumTag`, `Cast` |
| **Agents** | `AgentSpawn`, `AgentSend`, `AgentSync` |
| **Signals** | `SignalInit`, `SignalGet`, `SignalSet`, `SignalComputed`, `SignalSubscribe` |
| **Streams** | `StreamOp` (map, filter, take, skip, collect, fold) |
| **Closures** | `ClosureCreate`, `ClosureCall`, `EnvLoad` |
| **Strings** | `InterpConcat` |

**MIR optimizer passes:**

Optimization level (`-O0` through `-O3`) gates which passes run.
`-O0` runs no passes; `-O2` is the default for `build`. See
`mapanare/mir_opt.py` for the canonical pass list.

Always-on (at `-O1` and above):

- Constant folding and propagation
- Dead code elimination
- Copy propagation
- Basic block merging
- Unreachable block removal
- Auto-StringBuilder rewrite for loop-accumulated string concat
  (v4.108.0)

Higher-level passes exist in `mir_opt.py` (strength reduction, small-
function inlining, LICM, escape analysis, string-concat rewrite).
Some are enabled only in the Python bootstrap and were disabled in
the self-hosted compiler at v4.111.0 as zero-ROI; see
`docs/roadmap/v4/v4.109.0/OPT_ROI_ANALYSIS.md` for the forensics.
LLVM's own optimization pipeline handles most lowering-friendly
rewrites at `-O2`.

> **Note (v4.58.0):** A Python source emitter
> (`mapanare/emit_python_mir.py`) existed historically as a
> legacy transpiler target. It was removed in v4.58.0. A
> regression test at `tests/test_python_emitter_deleted.py`
> prevents reintroduction.

### LLVM Native Backend

The LLVM emitter (`mapanare/emit_llvm_text.py`) translates MIR to
LLVM IR, producing native machine code. This is the production
backend.

- Agent spawn/send/sync codegen backed by the C runtime thread pool and ring buffers.
- Compile-time tensor shape verification (element-wise ops and matmul via runtime calls).
- Arena-based memory management with `MnString` bitfield heap tagging (no garbage collector; v4.100.0 removed the older tagged-pointer UB).
- Ahead-of-time compilation for deployment.
- Cross-compilation to Linux x64, macOS ARM64, Windows x64.

### C Backend (v3.0.0+)

The C emitter (`mapanare/emit_c.py`) translates MIR to portable C
source. `gcc` or `clang` then produces the native binary. The C
backend is a fallback when the LLVM toolchain is unavailable and
the primary path for platforms where the LLVM IR → object-code
route is unreliable. It shares the runtime (`libmapanare_rt.a`)
with the LLVM backend.

### WebAssembly Backend (v2.0.0+)

The WASM emitter (`mapanare/emit_wasm.py`) translates MIR to
WebAssembly text format (WAT). The `wasm_linker.py` module
links multi-module WAT into a single `.wasm` for browser or WASI
targets. See §24.

### 3-stage fixed point

The self-hosted compiler reaches a 3-stage fixed point: `stage2.ll`
and `stage3.ll` are identical in every respect the compiler controls
— same IR instructions, same block order, same metadata graph, same
line count (109,872 lines at v4.142.0).

- **v4.134.0:** strict byte-identical — stage2 and stage3 shared md5
  `0c00ad07fee94f98bb350b359395843b`.
- **v4.139.0–present (Dr.1):** *near fixed point* — the
  `__MN_VERSION__` build-time substitution introduces a bounded
  4-line version-metadata diff (`!"__MN_VERSION__"` vs `!"4.143.0"`),
  so md5s differ by construction but the IR is otherwise identical.
  Current md5s: `stage2.ll = 6d4963cdbe060ac1cee85eb58f2fa932`,
  `stage3.ll = dddf64c3a77ed9236c82de517bc055d1` (v4.142.0).

The 4-line diff is a build-time artifact, not semantic codegen drift.
See `docs/roadmap/v4/v4.142.0/FIXEDPOINT_STATUS.md` for full provenance
and `scripts/verify_fixed_point.sh` to reproduce. `DIFF_THRESHOLD=100`
in the verifier script gates the acceptable bound.

---

## Appendix C: Reserved Keywords

This appendix lists identifiers reserved *for future use*. They are
not currently tokenized by either lexer but are treated as reserved
by convention so that future language changes will not break existing
code. For the complete list of identifiers that are **already**
tokenized and enforced as keywords today, see §2.1.1
*Reserved Keyword Master List*.

> **v4.72.0-v4.76.0 update:** `async` and `await` are now real keywords
> with full LLVM coroutine lowering (switched-resume ABI). See section
> 29 for the specification. They are no longer listed in the reserved
> table below.

| Reserved | Potential Future Use |
|---|---|
| `yield` | Generator / coroutine yield |
| `macro` | Compile-time macro system |
| `where` | Generic constraint clauses |
| `use` | Path shortening |
| `as` | Type casting / import renaming |
| `static` | Module-level mutable state |
| `unsafe` | Escape hatch for memory safety |
| `move` | Explicit ownership transfer |
| `ref` | Reference binding in patterns |
| `loop` | Infinite loop construct |
| `super` | Parent module reference |
| `crate` | Root module reference |
| `mod` | Module declaration |
| `dyn` | Dynamic dispatch |
| `box` | Heap allocation |

Note: These keywords are not currently enforced by the parser. They are reserved by convention to prevent user code from using names that may become keywords in future versions.

---

## Appendix D: Error Code Registry

See section 19.1 for the error code format. The complete registry of assigned error codes:

### Parse Errors (MN-P)

| Code | Description |
|---|---|
| `MN-P0001` | Unexpected token |
| `MN-P0002` | Unterminated string literal |
| `MN-P0003` | Invalid numeric literal |
| `MN-P0004` | Unexpected end of input |

### Semantic Errors (MN-S)

| Code | Description |
|---|---|
| `MN-S0001` | Undefined variable |
| `MN-S0002` | Type mismatch |
| `MN-S0003` | Undefined function |
| `MN-S0004` | Wrong number of arguments |
| `MN-S0005` | Assignment to immutable variable |
| `MN-S0006` | Undefined type |
| `MN-S0007` | Duplicate definition |
| `MN-S0008` | Missing trait method implementation |
| `MN-S0009` | Non-exhaustive match |
| `MN-S0010` | Invalid `?` operator context |

### Lowering Errors (MN-L)

| Code | Description |
|---|---|
| `MN-L0001` | Unsupported AST node in lowering |

### Code Generation Errors (MN-C)

| Code | Description |
|---|---|
| `MN-C0001` | LLVM IR emission failure |
| `MN-C0002` | Linking failure |

### Runtime Errors (MN-R)

| Code | Description |
|---|---|
| `MN-R0001` | Agent mailbox full |
| `MN-R0002` | Index out of bounds |
| `MN-R0003` | Division by zero |
| `MN-R0004` | Assert failure |
| `MN-R0005` | Stack overflow |

### Tooling Errors (MN-T)

| Code | Description |
|---|---|
| `MN-T0001` | Test discovery failure |
| `MN-T0002` | Benchmark failure |
