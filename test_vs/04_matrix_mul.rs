// Benchmark: Matrix Multiplication -- Rust

use std::alloc::{GlobalAlloc, Layout, System};
use std::sync::atomic::{AtomicUsize, Ordering};
use std::time::Instant;

struct TrackingAlloc;
static ALLOCATED: AtomicUsize = AtomicUsize::new(0);
static PEAK: AtomicUsize = AtomicUsize::new(0);

unsafe impl GlobalAlloc for TrackingAlloc {
    unsafe fn alloc(&self, layout: Layout) -> *mut u8 {
        let ret = unsafe { System.alloc(layout) };
        if !ret.is_null() {
            let current = ALLOCATED.fetch_add(layout.size(), Ordering::Relaxed) + layout.size();
            PEAK.fetch_max(current, Ordering::Relaxed);
        }
        ret
    }
    unsafe fn dealloc(&self, ptr: *mut u8, layout: Layout) {
        ALLOCATED.fetch_sub(layout.size(), Ordering::Relaxed);
        unsafe { System.dealloc(ptr, layout) };
    }
}

#[global_allocator]
static A: TrackingAlloc = TrackingAlloc;

fn matmul(a: &[Vec<f64>], b: &[Vec<f64>], n: usize) -> Vec<Vec<f64>> {
    let mut c = vec![vec![0.0; n]; n];
    for i in 0..n {
        for j in 0..n {
            let mut s = 0.0;
            for k in 0..n {
                s += a[i][k] * b[k][j];
            }
            c[i][j] = s;
        }
    }
    c
}

fn main() {
    let size = 100;
    let a = vec![vec![1.0_f64; size]; size];
    let b = vec![vec![2.0_f64; size]; size];

    PEAK.store(0, Ordering::Relaxed);
    ALLOCATED.store(0, Ordering::Relaxed);

    let start = Instant::now();
    let c = matmul(&a, &b, size);
    let elapsed = start.elapsed();
    let peak_kb = PEAK.load(Ordering::Relaxed) as f64 / 1024.0;

    println!("c[0][0] = {:.1}", c[0][0]);
    println!("__BENCH_METRICS__");
    println!("wall_time_s={:.6}", elapsed.as_secs_f64());
    println!("peak_memory_kb={:.1}", peak_kb);
}
