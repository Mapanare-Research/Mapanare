// Benchmark: Recursive Fibonacci(35) -- Go equivalent.
// Matches Mapanare/Python/Rust/C implementations bit-for-bit.
// Emits __BENCH_METRICS__ block for run_benchmarks.py harness.
package main

import (
	"fmt"
	"runtime"
	"syscall"
	"time"
)

func fib(n int64) int64 {
	if n <= 1 {
		return n
	}
	return fib(n-1) + fib(n-2)
}

func main() {
	runtime.GC()
	var ruStart, ruEnd syscall.Rusage
	syscall.Getrusage(syscall.RUSAGE_SELF, &ruStart)

	wall0 := time.Now()
	r := fib(35)
	wall := time.Since(wall0).Seconds()

	syscall.Getrusage(syscall.RUSAGE_SELF, &ruEnd)
	cpu := timevalSub(ruEnd.Utime, ruStart.Utime) + timevalSub(ruEnd.Stime, ruStart.Stime)
	peakKB := float64(ruEnd.Maxrss) // ru_maxrss is KB on Linux

	fmt.Printf("fib(35) = %d\n", r)
	fmt.Println("__BENCH_METRICS__")
	fmt.Printf("wall_time_s=%.6f\n", wall)
	fmt.Printf("cpu_time_s=%.6f\n", cpu)
	fmt.Printf("peak_memory_kb=%.1f\n", peakKB)
}

func timevalSub(end, start syscall.Timeval) float64 {
	return float64(end.Sec-start.Sec) + float64(end.Usec-start.Usec)/1e6
}
