# Mapanare v3.30.0 — "Turpial" (TypeScript Transpiler)

> Compile TypeScript to native code via Mapanare. `mapanare compile app.ts`
> tokenizes TypeScript, translates to Mapanare AST, and runs the full
> compilation pipeline: semantic check, MIR lowering, LLVM IR, native binary.

**Status:** DONE
**Estimated scope:** Large (3-4 sessions)
**Breaking:** No
**Prerequisite:** v3.29.0 (transpiler framework battle-tested by Python + PHP)

---

## Motivation

TypeScript is the most popular typed language for web and server development.
It compiles to JavaScript, which is interpreted. Mapanare can compile
TypeScript to native code — the same way it compiles Python and PHP.

The alignment is natural:
- TypeScript interfaces → Mapanare traits
- TypeScript classes → Mapanare structs + impl blocks
- TypeScript union types → Mapanare enums
- TypeScript `async/await` → Mapanare agents
- TypeScript `Promise` → Mapanare `Result` or agent sync
- TypeScript optional chaining (`?.`) → Mapanare `Option`
- TypeScript generics → Mapanare generics (monomorphized)

The transpiler framework from v3.27.0 handles type mapping, class→struct,
exception→Result, and stdlib shims. This module implements only the
TypeScript-specific lexer, parser, and AST walk.

The name "Turpial" (Venezuelan national bird) soars — TypeScript transpilation
takes Mapanare to its highest-profile target yet.

---

## Items

### 1. TypeScript tokenizer in `.mn` [HIGH]

**File:** `mapanare/self/from_typescript.mn` (new)
**Reporter:** roadmap
**Fix:** Character-by-character tokenizer for TypeScript 5.0+ syntax:
- Keywords: `function`, `class`, `interface`, `type`, `enum`, `const`, `let`,
  `var`, `if`, `else`, `for`, `while`, `do`, `switch`, `case`, `default`,
  `return`, `import`, `export`, `from`, `as`, `new`, `this`, `extends`,
  `implements`, `static`, `private`, `public`, `protected`, `readonly`,
  `abstract`, `async`, `await`, `try`, `catch`, `finally`, `throw`,
  `typeof`, `instanceof`, `in`, `of`, `null`, `undefined`, `true`, `false`,
  `void`, `never`, `any`, `unknown`, `yield`, `delete`, `super`,
  `break`, `continue`
- Type annotations: `x: number`, `-> string`, `Array<T>`, `Record<K,V>`,
  `T | U` (union), `T & U` (intersection), `T?` (optional)
- Template literals: `` `hello ${name}` ``
- Arrow functions: `(x) => x + 1`, `(x: number): number => x + 1`
- Decorators: `@decorator`
- Optional chaining: `?.`, `??`
- Operators: same as JavaScript/PHP plus `===`, `!==`, `??=`, `&&=`, `||=`
- Comments: `//`, `/* ... */`
- JSX: skip/warn (not supported)

### 2. TypeScript AST data structures [HIGH]

**File:** `mapanare/self/from_typescript.mn`
**Reporter:** roadmap
**Fix:** TypeScript-specific AST nodes:

```mn
enum TsExpr {
    IntLit(Int), FloatLit(Float), StrLit(String), BoolLit(Bool),
    NullLit, UndefinedLit, Name(String),
    BinOp(TsExpr, String, TsExpr), UnaryOp(String, TsExpr),
    Call(TsExpr, List<TsExpr>), MethodCall(TsExpr, String, List<TsExpr>),
    PropertyAccess(TsExpr, String), ElementAccess(TsExpr, TsExpr),
    ArrayLit(List<TsExpr>), ObjectLit(List<TsExpr>, List<TsExpr>),
    ArrowFn(List<TsParam>, List<TsStmt>),
    New(String, List<TsExpr>), Typeof(TsExpr),
    TemplateLit(List<TsExpr>), OptionalChain(TsExpr, String),
    NullCoalesce(TsExpr, TsExpr), Ternary(TsExpr, TsExpr, TsExpr),
    As(TsExpr, String), Spread(TsExpr),
    Await(TsExpr),
}

enum TsStmt {
    FuncDecl(String, List<TsParam>, String, List<TsStmt>),
    ClassDecl(String, String, List<String>, List<TsStmt>),
    InterfaceDecl(String, List<TsMethod>),
    TypeAlias(String, TsType),
    EnumDecl(String, List<TsEnumMember>),
    If(TsExpr, List<TsStmt>, List<TsStmt>),
    For(TsStmt, TsExpr, TsStmt, List<TsStmt>),
    ForOf(String, TsExpr, List<TsStmt>),
    While(TsExpr, List<TsStmt>),
    Switch(TsExpr, List<TsCase>),
    Return(TsExpr), Throw(TsExpr),
    VarDecl(String, String, TsExpr, Bool),  // name, type, init, is_const
    ExprStmt(TsExpr), Import(String, List<String>),
    TryCatch(List<TsStmt>, String, List<TsStmt>, List<TsStmt>),
    Export(TsStmt),
    Break, Continue,
}
```

### 3. TypeScript parser [HIGH]

**File:** `mapanare/self/from_typescript.mn`
**Reporter:** roadmap
**Fix:** Recursive descent parser with type annotation parsing.
Must handle:
- Function declarations with generic parameters: `function f<T>(x: T): T`
- Arrow functions: `const f = (x: number): number => x + 1`
- Class declarations with constructor shorthand: `constructor(public name: string)`
- Interface declarations → trait definitions
- Type aliases: `type Result<T> = Success<T> | Failure`
- Enum declarations → Mapanare enums
- for/of loops: `for (const item of items)` → `for item in items`
- Template literals → concat chains
- Optional chaining: `x?.y?.z` → `x.map(|v| v.y).map(|v| v.z)`
- Destructuring: `const { a, b } = obj` → `let a = obj.a; let b = obj.b`
- Import/export statements → Mapanare import/pub

### 4. Walk: interfaces → traits [HIGH]

**File:** `mapanare/self/from_typescript.mn`
**Reporter:** roadmap
**Fix:** TypeScript interfaces map naturally to Mapanare traits:
- `interface Describable { describe(): string }` →
  `trait Describable { fn describe(self) -> String }`
- `class Dog implements Describable` →
  `impl Describable for Dog { fn describe(self) -> String { ... } }`
- Interface extension: `interface B extends A` →
  `trait B: A` (trait bound)
- Optional methods: `method?(): void` → warn unsupported

### 5. Walk: classes → struct + impl [HIGH]

**File:** `mapanare/self/from_typescript.mn`
**Reporter:** roadmap
**Fix:** Via `transpiler.translate_class_to_struct()`:
- Constructor shorthand: `constructor(public name: string)` → field `name: String`
- Regular fields: `private count: number = 0` → field `count: Int`
- Methods → impl block
- `this.field` → `self.field`
- Static methods → standalone functions
- Getters/setters → regular methods with warnings
- `extends` → embed parent struct + forward methods (composition)
- `abstract class` → trait

### 6. Walk: union types → enums, `Promise` → Result [MEDIUM]

**File:** `mapanare/self/from_typescript.mn`
**Reporter:** roadmap
**Fix:**
- `string | number` → `any` (simple union)
- `Success | Failure` → enum with variants (named union)
- `type Shape = Circle | Square` → `enum Shape { Circle, Square }`
- `T | null` / `T | undefined` → `Option<T>`
- `Promise<T>` → agent result (spawn + sync)
- `async function` → `agent` definition
- `await expr` → `sync expr`

### 7. Walk: `try/catch` → Result, optional chaining → Option [MEDIUM]

**File:** `mapanare/self/from_typescript.mn`
**Reporter:** roadmap
**Fix:** Via `transpiler.translate_exception_to_result()`:
- `try { ... } catch (e) { ... }` → `match result { Ok(val) => ..., Err(e) => ... }`
- `throw new Error("msg")` → `return Err("msg")`
- `x?.y` → `x.map(|v| v.y)` or simplified to Option access
- `x ?? default` → `x.unwrap_or(default)`

### 8. TypeScript type mapping [MEDIUM]

**File:** `mapanare/self/from_typescript.mn`
**Reporter:** roadmap
**Fix:** Register TypeScript type mappings via `transpiler.translate_type()`:
| TypeScript | Mapanare |
|------------|----------|
| `number` | `Float` (or `Int` if integer context detected) |
| `string` | `String` |
| `boolean` | `Bool` |
| `void` | `Void` |
| `null`/`undefined` | `None` |
| `any` | `any` |
| `unknown` | `any` (with warning) |
| `never` | `Void` (with warning) |
| `Array<T>` / `T[]` | `List<T>` |
| `Record<K,V>` / `Map<K,V>` | `Map<K,V>` |
| `Set<T>` | `List<T>` (with warning) |
| `Promise<T>` | agent return type |
| `T \| null` | `Option<T>` |
| `T \| U` | `any` (complex union) |

### 9. TS stdlib mapping [LOW]

**File:** `mapanare/self/from_typescript.mn`
**Reporter:** roadmap
**Fix:** Register TypeScript stdlib shims:
- `console.log→print`, `console.error→print`
- `Array.prototype`: `push→push`, `pop→pop`, `map→map`, `filter→filter`,
  `reduce→fold`, `forEach→for..in`, `length→len`, `includes→contains`,
  `indexOf→index_of`, `slice→substr`, `join→join`, `reverse→reverse`
- `String.prototype`: `toLowerCase→to_lower`, `toUpperCase→to_upper`,
  `trim→trim`, `split→split`, `includes→contains`, `startsWith→starts_with`,
  `endsWith→ends_with`, `replace→replace`, `length→len`
- `Math`: `Math.sqrt→math.sqrt`, `Math.abs→math.abs`, `Math.floor→math.floor`,
  `Math.ceil→math.ceil`, `Math.round→math.round`, `Math.random→math.random`,
  `Math.max→math.max`, `Math.min→math.min`
- `JSON.parse→json.parse`, `JSON.stringify→json.to_string`
- `parseInt→int`, `parseFloat→float`, `String(x)→str(x)`

### 10. Test suite [MEDIUM]

**File:** `tests/ts_compat/test_from_typescript.py` (new, ~500 lines)
**Reporter:** roadmap
**Fix:** 50+ compatibility tests across 15+ test classes:
- Functions with type annotations
- Arrow functions
- Classes with constructors and methods
- Interfaces → traits
- Union types → enums
- Optional chaining → Option
- Template literals → concat
- `async/await` → agents
- for/of loops
- Destructuring
- Type aliases
- Enum declarations
- Import/export
- Try/catch → Result
- End-to-end programs (fizzbuzz, fibonacci, linked list)

---

## What's NOT in This Release

- **No JSX/TSX support.** React components are out of scope. Diagnosed with warning.
- **No module resolution.** `import` from `node_modules` is not supported.
  Only relative imports are translated.
- **No decorators.** TypeScript experimental decorators are skipped with warning.
- **No mapped/conditional types.** `Partial<T>`, `Pick<T,K>`, `Exclude<T,U>` etc.
  are treated as `any` with warning.
- **No `Symbol`, `WeakMap`, `WeakSet`, `Proxy`, `Reflect`.** Diagnosed with warning.

---

## Verification

- [ ] `from_typescript.mn` compiles through the Python bootstrap emitter
- [ ] `mnc compile fizzbuzz.ts` produces correct native binary
- [ ] `interface Describable { describe(): string }` → trait definition
- [ ] `class Dog implements Describable` → struct + impl Describable for Dog
- [ ] `async function fetch()` → agent definition
- [ ] `await result` → sync expression
- [ ] `x?.y ?? "default"` → Option chain with unwrap_or
- [ ] `const { a, b } = obj` → let a = obj.a; let b = obj.b
- [ ] Template literal → concat chain
- [ ] 50+ compatibility tests pass
- [ ] `bash scripts/rebuild.sh` — golden tests still pass
