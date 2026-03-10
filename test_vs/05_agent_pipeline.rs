// Benchmark: Agent Pipeline Processing Messages — Rust baseline.
use std::sync::mpsc;
use std::thread;
use std::time::Instant;

fn main() {
    let (p_in_tx, p_in_rx) = mpsc::sync_channel::<String>(1024);
    let (p_out_tx, p_out_rx) = mpsc::sync_channel::<i64>(1024);
    let (v_out_tx, v_out_rx) = mpsc::sync_channel::<i64>(1024);
    let (t_out_tx, t_out_rx) = mpsc::sync_channel::<i64>(1024);

    // Parser
    thread::spawn(move || {
        while let Ok(raw) = p_in_rx.recv() {
            p_out_tx.send(raw.len() as i64).unwrap();
        }
    });

    // Validator
    thread::spawn(move || {
        while let Ok(value) = p_out_rx.recv() {
            v_out_tx.send(if value > 0 { value } else { 0 }).unwrap();
        }
    });

    // Transformer
    thread::spawn(move || {
        while let Ok(value) = v_out_rx.recv() {
            t_out_tx.send(value * 3 + 7).unwrap();
        }
    });

    let start = Instant::now();
    let mut total: i64 = 0;
    for i in 0..1000 {
        let msg = format!("message_payload_data_{}", i);
        p_in_tx.send(msg).unwrap();
        let result = t_out_rx.recv().unwrap();
        total += result;
    }
    drop(p_in_tx);
    let elapsed = start.elapsed().as_secs_f64();

    println!("{}", total);
    println!("__BENCH_METRICS__");
    println!("wall_time_s={:.6}", elapsed);
    println!("cpu_time_s={:.6}", elapsed);
    println!("peak_memory_kb=0");
}
