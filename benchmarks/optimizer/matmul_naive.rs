use std::time::Instant;
// Benchmark 3: Naive matrix multiply — Rust equivalent.
fn main() {
    let __bench_t0 = Instant::now();

    let n: usize = 64;
    let n2 = n * n;
    let a: Vec<i64> = (0..n2).map(|i| ((i as i64) * 3 + 7) % 100).collect();
    let b: Vec<i64> = (0..n2).map(|i| ((i as i64) * 5 + 13) % 100).collect();
    let mut c = vec![0i64; n2];

    for i in 0..n {
        for j in 0..n {
            let mut s: i64 = 0;
            for k in 0..n {
                s += a[i * n + k] * b[k * n + j];
            }
            c[i * n + j] = s;
        }
    }

    let cs = c[0] + c[n - 1] + c[(n - 1) * n] + c[n2 - 1];
    println!("checksum = {}", cs);
    let __bench_dt = __bench_t0.elapsed().as_secs_f64();
    println!("__BENCH_METRICS__");
    println!("wall_time_s={}", __bench_dt);
    println!("cpu_time_s={}", __bench_dt);
    println!("peak_memory_kb=0");
}
