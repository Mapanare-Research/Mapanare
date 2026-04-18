use std::time::Instant;
// Benchmark: Compile-self proxy — Rust equivalent.
fn make_grid(w: usize, h: usize) -> Vec<i64> {
    (0..w * h).map(|i| ((i * 7 + 13) % 256) as i64).collect()
}

fn simulate_step(grid: &[i64], w: usize, h: usize) -> i64 {
    let mut s = 0i64;
    for y in 1..h - 1 {
        for x in 1..w - 1 {
            let center = grid[y * w + x];
            let north = grid[(y - 1) * w + x];
            let south = grid[(y + 1) * w + x];
            let east = grid[y * w + x + 1];
            let west = grid[y * w + x - 1];
            s += (center + north + south + east + west) / 5;
        }
    }
    s
}

fn fibonacci(n: i64) -> i64 {
    if n <= 1 { return n; }
    fibonacci(n - 1) + fibonacci(n - 2)
}

fn collatz_steps(n: i64) -> i64 {
    let (mut val, mut steps) = (n, 0i64);
    while val != 1 {
        let rem = val % 2;
        if rem == 0 { val /= 2; } else { val = val * 3 + 1; }
        steps += 1;
    }
    steps
}

fn main() {
    let __bench_t0 = Instant::now();

    let (w, h) = (50usize, 50usize);
    let grid = make_grid(w, h);
    let sim_result: i64 = (0..10).map(|_| simulate_step(&grid, w, h)).sum();
    let fib_result = fibonacci(25);
    let collatz_sum: i64 = (1..=1000).map(collatz_steps).sum();
    println!("checksum = {}", sim_result + fib_result + collatz_sum);
    let __bench_dt = __bench_t0.elapsed().as_secs_f64();
    println!("__BENCH_METRICS__");
    println!("wall_time_s={}", __bench_dt);
    println!("cpu_time_s={}", __bench_dt);
    println!("peak_memory_kb=0");
}
