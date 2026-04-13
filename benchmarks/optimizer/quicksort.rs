// Benchmark 2: Quicksort — Rust equivalent.
fn lcg_next(seed: i64) -> i64 {
    (seed.wrapping_mul(1103515245).wrapping_add(12345)) % 2147483648
}

fn partition(arr: &mut Vec<i64>, lo: usize, hi: usize) -> usize {
    let pivot = arr[hi];
    let mut i = lo;
    for j in lo..hi {
        if arr[j] < pivot {
            arr.swap(i, j);
            i += 1;
        }
    }
    arr.swap(i, hi);
    i
}

fn qsort(arr: &mut Vec<i64>, lo: i64, hi: i64) {
    if lo < hi {
        let p = partition(arr, lo as usize, hi as usize);
        qsort(arr, lo, p as i64 - 1);
        qsort(arr, p as i64 + 1, hi);
    }
}

fn main() {
    let mut arr = Vec::new();
    let mut seed: i64 = 42;
    for _ in 0..10000 {
        seed = lcg_next(seed);
        arr.push(seed % 100000);
    }
    qsort(&mut arr, 0, 9999);
    let checksum: i64 = arr[..10].iter().sum();
    println!("checksum = {}", checksum);
}
