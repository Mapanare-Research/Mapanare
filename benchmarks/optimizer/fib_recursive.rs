// Benchmark 1: Recursive Fibonacci — Rust equivalent.
fn fib(n: i64) -> i64 {
    if n <= 1 { return n; }
    fib(n - 1) + fib(n - 2)
}

fn main() {
    let r = fib(35);
    println!("fib(35) = {}", r);
}
