// Benchmark: Stream Pipeline Processing (1M items) -- Rust
// Same workload: for x in 0..1M -> x*3 -> keep even -> sum

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

fn main() {
    PEAK.store(0, Ordering::Relaxed);
    ALLOCATED.store(0, Ordering::Relaxed);

    let start = Instant::now();

    let result: i64 = (0..1_000_000i64)
        .map(|x| x * 3)
        .filter(|x| x % 2 == 0)
        .sum();

    let elapsed = start.elapsed();
    let peak_kb = PEAK.load(Ordering::Relaxed) as f64 / 1024.0;

    println!("result = {}", result);
    println!("__BENCH_METRICS__");
    println!("wall_time_s={:.6}", elapsed.as_secs_f64());
    println!("peak_memory_kb={:.1}", peak_kb);
}
