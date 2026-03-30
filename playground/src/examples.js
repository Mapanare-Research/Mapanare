/**
 * Pre-loaded example programs for the Mapanare playground.
 */

export const EXAMPLES = [
  {
    name: "Hello World",
    code: `// Hello World in Mapanare
fn main() {
    print("Hello, Mapanare!")
}`,
  },
  {
    name: "String Interpolation",
    code: `// String interpolation with \${expr}
fn greet(name: String) -> String {
    return "Hello, \${name}! Welcome to Mapanare."
}

fn main() {
    let name = "World"
    print(greet(name))
    print("2 + 3 = \${2 + 3}")
}`,
  },
  {
    name: "Fibonacci",
    code: `// Fibonacci sequence
fn fib(n: Int) -> Int {
    if n <= 1 {
        return n
    }
    return fib(n - 1) + fib(n - 2)
}

fn main() {
    let mut i = 0
    while i < 10 {
        print("fib(\${i}) = \${fib(i)}")
        i = i + 1
    }
}`,
  },
  {
    name: "Structs & Enums",
    code: `// Structs and pattern matching
struct Point { x: Float, y: Float }

enum Shape {
    Circle(Float),
    Rect(Float, Float)
}

fn describe(s: Shape) -> String {
    match s {
        Shape_Circle(r) => { return "Circle area: " + str(3.14159 * r * r) },
        Shape_Rect(w, h) => { return "Rect area: " + str(w * h) },
        _ => { return "unknown" }
    }
    return "unreachable"
}

fn main() {
    let c = Shape_Circle(5.0)
    let r = Shape_Rect(4.0, 6.0)
    print(describe(c))
    print(describe(r))
}`,
  },
  {
    name: "Option & Result",
    code: `// Option and Result types
fn divide(a: Float, b: Float) -> Result<Float, String> {
    if b == 0.0 {
        return Err("division by zero")
    }
    return Ok(a / b)
}

fn find_first(items: List<Int>, target: Int) -> Option<Int> {
    let mut i = 0
    while i < len(items) {
        if items[i] == target {
            return Some(i)
        }
        i = i + 1
    }
    return none
}

fn main() {
    let result = divide(10.0, 3.0)
    print("10 / 3 = \${result}")

    let err = divide(1.0, 0.0)
    print("1 / 0 = \${err}")

    let nums = [1, 2, 3, 4, 5]
    print("find 3: \${find_first(nums, 3)}")
    print("find 9: \${find_first(nums, 9)}")
}`,
  },
  {
    name: "Higher-Order Functions",
    code: `// Lambdas and higher-order functions
fn apply(f: fn(Int) -> Int, x: Int) -> Int {
    return f(x)
}

fn main() {
    let double = (x) => x * 2
    let square = (x) => x * x

    print("double(5) = \${apply(double, 5)}")
    print("square(5) = \${apply(square, 5)}")

    let nums = [1, 2, 3, 4, 5]
    let mut i = 0
    while i < len(nums) {
        print("\${nums[i]} squared = \${apply(square, nums[i])}")
        i = i + 1
    }
}`,
  },
  {
    name: "Pipe Operator",
    code: `// Pipeline operator |>
fn double(x: Int) -> Int {
    return x * 2
}

fn add_one(x: Int) -> Int {
    return x + 1
}

fn to_string(x: Int) -> String {
    return "result: \${x}"
}

fn main() {
    let result = 5 |> double |> add_one |> to_string
    print(result)
}`,
  },
];
