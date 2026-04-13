// Benchmark: Closure-like pattern — Rust equivalent.
#[inline(never)]
fn compute(a: i64, b: i64, c: i64, x: i64) -> i64 {
    x + a + b + c
}

fn main() {
    let mut sum: i64 = 0;
    for i in 0..10_000i64 {
        let a = i;
        let b = i * 2;
        let c = i * 3;
        sum += compute(a, b, c, i);
    }
    println!("checksum = {}", sum);
}
