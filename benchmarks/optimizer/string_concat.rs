// Benchmark 4: String concatenation — Rust equivalent.
fn main() {
    let mut result = String::new();
    for _ in 0..10000 {
        result.push_str("hello");
    }
    println!("len = {}", result.len());
}
