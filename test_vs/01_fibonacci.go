// Benchmark: Recursive Fibonacci -- Go

package main

import (
	"fmt"
	"runtime"
	"time"
)

func fib(n int) int {
	if n <= 1 {
		return n
	}
	return fib(n-1) + fib(n-2)
}

func main() {
	runtime.GC()
	var memBefore runtime.MemStats
	runtime.ReadMemStats(&memBefore)

	start := time.Now()
	result := fib(35)
	elapsed := time.Since(start)

	var memAfter runtime.MemStats
	runtime.ReadMemStats(&memAfter)

	fmt.Printf("fib(35) = %d\n", result)
	fmt.Printf("__BENCH_METRICS__\n")
	fmt.Printf("wall_time_s=%.6f\n", elapsed.Seconds())
	fmt.Printf("peak_memory_kb=%.1f\n", float64(memAfter.TotalAlloc-memBefore.TotalAlloc)/1024.0)
}
