use std::time::Instant;
// Benchmark: Closure-like pattern — Rust equivalent.
#[inline(never)]
fn compute(a: i64, b: i64, c: i64, x: i64) -> i64 {
    x + a + b + c
}

fn main() {
    let __bench_t0 = Instant::now();

    let mut sum: i64 = 0;
    for i in 0..10_000i64 {
        let a = i;
        let b = i * 2;
        let c = i * 3;
        sum += compute(a, b, c, i);
    }
    println!("checksum = {}", sum);
    let __bench_dt = __bench_t0.elapsed().as_secs_f64();
    println!("__BENCH_METRICS__");
    println!("wall_time_s={}", __bench_dt);
    println!("cpu_time_s={}", __bench_dt);
    println!("peak_memory_kb=0");
}
