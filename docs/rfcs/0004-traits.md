# RFC 0004: Traits / Interfaces

- **Status:** Accepted
- **Date:** 2026-03-10
- **Author:** Mapanare Team

## Summary

Add trait definitions and implementations to Mapanare, enabling generic
abstractions over types (e.g., `Ord`, `Display`, `Eq`, `Hash`). Traits
provide the missing piece for bounded generics: `fn sort<T: Ord>(list: List<T>)`.

## Motivation

Without traits, Mapanare has no way to express type constraints on generics.
You cannot write a generic `max`, `sort`, or `print` that works across types
while guaranteeing the required operations exist. This was cited by 5/7
reviewers as a critical gap.

## Design

### Trait Definition

```mapanare
trait Display {
    fn to_string(self) -> String
}

trait Ord {
    fn cmp(self, other: Self) -> Int
}

trait Hash {
    fn hash(self) -> Int
}

trait Eq {
    fn eq(self, other: Self) -> Bool
}
```

- `trait Name { method_signatures }` defines a trait.
- Method signatures have no body — just name, params, and return type.
- `self` is the receiver (the implementing type).
- `Self` in parameter/return positions refers to the implementing type.
- Traits can be `pub` for cross-module visibility.
- No default method implementations in v0.3 (deferred to v0.4).
- No trait inheritance/supertraits in v0.3 (deferred to v0.4).

### Trait Implementation

```mapanare
struct Point {
    x: Float,
    y: Float
}

impl Display for Point {
    fn to_string(self) -> String {
        return str(self.x) + ", " + str(self.y)
    }
}

impl Eq for Point {
    fn eq(self, other: Point) -> Bool {
        return self.x == other.x && self.y == other.y
    }
}
```

- `impl TraitName for TypeName { methods }` implements a trait for a type.
- All methods declared in the trait must be implemented.
- Missing methods produce a semantic error.
- Extra methods not in the trait produce a semantic error.
- The existing `impl TypeName { methods }` (inherent impls) remain unchanged.

### Trait Bounds on Generics

```mapanare
fn max<T: Ord>(a: T, b: T) -> T {
    if a.cmp(b) > 0 {
        return a
    }
    return b
}

fn print_all<T: Display>(items: List<T>) {
    for item in items {
        println(item.to_string())
    }
}
```

- Type parameters can have trait bounds: `<T: Ord>`.
- Multiple bounds on a single parameter use `+`: `<T: Ord + Display>` (v0.4).
- The semantic checker verifies that any method called on a bounded type
  parameter is declared in the constraining trait.
- At call sites, the checker verifies the actual type argument implements
  the required trait.

### Grammar Changes

```
trait_def: KW_PUB? KW_TRAIT NAME LBRACE _nl* (trait_method _nl*)* RBRACE
trait_method: KW_FN NAME LPAREN param_list? RPAREN (ARROW type_expr)?

// Updated impl_def to support `impl Trait for Type`
impl_def: KW_IMPL NAME LBRACE _nl* (fn_def _nl*)* RBRACE
        | KW_IMPL NAME KW_FOR NAME LBRACE _nl* (fn_def _nl*)* RBRACE

// Updated type_params to support trait bounds
type_params: LT type_param (COMMA type_param)* GT
type_param: NAME (COLON NAME)?
```

### Code Generation

**Python backend:** Traits emit as `typing.Protocol` classes. Trait impls
are merged into the target class as regular methods (same as inherent impls).
No runtime dispatch needed — Python duck typing handles it.

**LLVM backend:** Monomorphization. Each concrete type that implements a
trait gets its methods compiled directly. No vtable indirection. Generic
functions with trait bounds are specialized per concrete type at call sites
(for now, the LLVM backend handles them the same as unbound generics since
full monomorphization requires whole-program analysis deferred to v0.4).

## What This Does NOT Include

- Default method implementations (v0.4)
- Trait inheritance / supertraits (v0.4)
- Multiple trait bounds with `+` syntax (v0.4)
- Associated types (v0.5+)
- Trait objects / dynamic dispatch via `dyn Trait` (v0.5+)
- Auto-derive for builtin traits (v0.5+)

## Success Criteria

1. `trait Display { fn to_string(self) -> String }` parses and type-checks.
2. `impl Display for Point { ... }` is verified against the trait.
3. Missing impl methods produce a clear error.
4. `fn max<T: Ord>(a: T, b: T) -> T` compiles on both backends.
5. Builtin traits `Display`, `Eq`, `Ord`, `Hash` are defined.
