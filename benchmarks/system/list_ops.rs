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
    let mut count = 0i64;
    for i in 0..100_000i64 {
        if is_prime(i) {
            count += 1;
        }
    }
    println!("primes = {}", count);
}
