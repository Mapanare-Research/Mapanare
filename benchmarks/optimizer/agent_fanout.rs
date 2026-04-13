// Benchmark 5: Simulated agent fanout — Rust equivalent.
fn worker(id: i64, message: i64) -> i64 {
    (message * (id + 1)) % 1000000
}

fn main() {
    let mut total: i64 = 0;
    for msg in 0..1000 {
        for w in 0..10 {
            total += worker(w, msg);
        }
    }
    println!("total = {}", total);
}
