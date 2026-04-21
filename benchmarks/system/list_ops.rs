use std::time::Instant;
// Benchmark: Prime sieve — Rust equivalent.
fn is_prime(n: i64) -> bool {
    if n < 2 { return false; }
    if n < 4 { return true; }
    if n % 2 == 0 { return false; }
    let mut d = 3i64;
    while d * d <= n {
        if n % d == 0 { return false; }
        d += 2;
    }
    true
}

fn main() {
    let __bench_t0 = Instant::now();

    let mut count = 0i64;
    for i in 0..100_000i64 {
        if is_prime(i) {
            count += 1;
        }
    }
    println!("primes = {}", count);
    let __bench_dt = __bench_t0.elapsed().as_secs_f64();
    println!("__BENCH_METRICS__");
    println!("wall_time_s={}", __bench_dt);
    println!("cpu_time_s={}", __bench_dt);
    println!("peak_memory_kb=0");
}
