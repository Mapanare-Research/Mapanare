use std::time::Instant;
// Benchmark: Enum matching — Rust equivalent.
enum Shape {
    Circle(i64),
    Square(i64),
    Triangle(i64, i64),
    Point,
    Line(i64),
    Rect(i64, i64),
}

fn area(s: &Shape) -> i64 {
    match s {
        Shape::Circle(r) => r * r * 3,
        Shape::Square(side) => side * side,
        Shape::Triangle(base, height) => base * height / 2,
        Shape::Point => 0,
        Shape::Line(len) => *len,
        Shape::Rect(w, h) => w * h,
    }
}

fn make_shape(i: i64) -> Shape {
    match i % 6 {
        0 => Shape::Circle(i % 50 + 1),
        1 => Shape::Square(i % 30 + 1),
        2 => Shape::Triangle(i % 20 + 1, i % 40 + 1),
        3 => Shape::Point,
        4 => Shape::Line(i % 100 + 1),
        _ => Shape::Rect(i % 25 + 1, i % 35 + 1),
    }
}

fn main() {
    let __bench_t0 = Instant::now();

    let mut total: i64 = 0;
    for i in 0..100_000i64 {
        let s = make_shape(i);
        total += area(&s);
    }
    println!("checksum = {}", total);
    let __bench_dt = __bench_t0.elapsed().as_secs_f64();
    println!("__BENCH_METRICS__");
    println!("wall_time_s={}", __bench_dt);
    println!("cpu_time_s={}", __bench_dt);
    println!("peak_memory_kb=0");
}
