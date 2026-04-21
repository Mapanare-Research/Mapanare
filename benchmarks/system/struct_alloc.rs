use std::time::Instant;
// Benchmark: Struct allocation — Rust equivalent.
struct Point { x: i64, y: i64, z: i64 }

fn make_point(i: i64) -> Point {
    Point { x: i, y: i * 2, z: i * 3 }
}

fn main() {
    let __bench_t0 = Instant::now();

    let mut sum: i64 = 0;
    for i in 0..100_000i64 {
        let p = make_point(i);
        sum += p.x + p.y + p.z;
    }
    println!("checksum = {}", sum);
    let __bench_dt = __bench_t0.elapsed().as_secs_f64();
    println!("__BENCH_METRICS__");
    println!("wall_time_s={}", __bench_dt);
    println!("cpu_time_s={}", __bench_dt);
    println!("peak_memory_kb=0");
}
