// Benchmark: Stream Pipeline Processing (1M items) -- Go
// Same workload: for x in 0..1M -> x*3 -> keep even -> sum

package main

import (
	"fmt"
	"runtime"
	"time"
)

func main() {
	runtime.GC()
	var memBefore runtime.MemStats
	runtime.ReadMemStats(&memBefore)

	start := time.Now()

	total := 0
	for x := 0; x < 1000000; x++ {
		v := x * 3
		if v%2 == 0 {
			total += v
		}
	}

	elapsed := time.Since(start)

	var memAfter runtime.MemStats
	runtime.ReadMemStats(&memAfter)

	fmt.Printf("result = %d\n", total)
	fmt.Printf("__BENCH_METRICS__\n")
	fmt.Printf("wall_time_s=%.6f\n", elapsed.Seconds())
	fmt.Printf("peak_memory_kb=%.1f\n", float64(memAfter.TotalAlloc-memBefore.TotalAlloc)/1024.0)
}
