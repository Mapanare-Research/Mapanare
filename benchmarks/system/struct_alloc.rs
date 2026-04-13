// Benchmark: Struct allocation — Rust equivalent.
struct Point { x: i64, y: i64, z: i64 }

fn make_point(i: i64) -> Point {
    Point { x: i, y: i * 2, z: i * 3 }
}

fn main() {
    let mut sum: i64 = 0;
    for i in 0..100_000i64 {
        let p = make_point(i);
        sum += p.x + p.y + p.z;
    }
    println!("checksum = {}", sum);
}
