// Benchmark: Concurrent Message Passing -- Rust std::sync::mpsc

use std::alloc::{GlobalAlloc, Layout, System};
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::mpsc;
use std::thread;
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
    let (tx_in, rx_in) = mpsc::sync_channel::<i64>(1024);
    let (tx_out, rx_out) = mpsc::sync_channel::<i64>(1024);

    PEAK.store(0, Ordering::Relaxed);
    ALLOCATED.store(0, Ordering::Relaxed);

    thread::spawn(move || {
        while let Ok(val) = rx_in.recv() {
            tx_out.send(val * 2 + 1).unwrap();
        }
    });

    let start = Instant::now();
    let mut sum: i64 = 0;
    for i in 0..10_000 {
        tx_in.send(i).unwrap();
        let result = rx_out.recv().unwrap();
        sum += result;
    }
    drop(tx_in);
    let elapsed = start.elapsed();
    let peak_kb = PEAK.load(Ordering::Relaxed) as f64 / 1024.0;

    println!("sum = {}", sum);
    println!("__BENCH_METRICS__");
    println!("wall_time_s={:.6}", elapsed.as_secs_f64());
    println!("peak_memory_kb={:.1}", peak_kb);
}
