use std::time::Instant;
// Benchmark 5: Simulated agent fanout — Rust equivalent.
fn worker(id: i64, message: i64) -> i64 {
    (message * (id + 1)) % 1000000
}

fn main() {
    let __bench_t0 = Instant::now();

    let mut total: i64 = 0;
    for msg in 0..1000 {
        for w in 0..10 {
            total += worker(w, msg);
        }
    }
    println!("total = {}", total);
    let __bench_dt = __bench_t0.elapsed().as_secs_f64();
    println!("__BENCH_METRICS__");
    println!("wall_time_s={}", __bench_dt);
    println!("cpu_time_s={}", __bench_dt);
    println!("peak_memory_kb=0");
}
