use std::time::Instant;
// Benchmark 1: Recursive Fibonacci — Rust equivalent.
fn fib(n: i64) -> i64 {
    if n <= 1 { return n; }
    fib(n - 1) + fib(n - 2)
}

fn main() {
    let __bench_t0 = Instant::now();

    let r = fib(35);
    println!("fib(35) = {}", r);
    let __bench_dt = __bench_t0.elapsed().as_secs_f64();
    println!("__BENCH_METRICS__");
    println!("wall_time_s={}", __bench_dt);
    println!("cpu_time_s={}", __bench_dt);
    println!("peak_memory_kb=0");
}
