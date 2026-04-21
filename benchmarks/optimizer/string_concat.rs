use std::time::Instant;
// Benchmark 4: String concatenation — Rust equivalent.
fn main() {
    let __bench_t0 = Instant::now();

    let mut result = String::new();
    for _ in 0..10000 {
        result.push_str("hello");
    }
    println!("len = {}", result.len());
    let __bench_dt = __bench_t0.elapsed().as_secs_f64();
    println!("__BENCH_METRICS__");
    println!("wall_time_s={}", __bench_dt);
    println!("cpu_time_s={}", __bench_dt);
    println!("peak_memory_kb=0");
}
