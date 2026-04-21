// Benchmark: String concatenation -- Go equivalent.
// 10,000 iterations of s += "hello". Final length = 50,000.
// Idiomatic Go is strings.Builder, but to match the other languages' pattern
// (allocate+memcpy per iteration) we use plain += on a string variable.
package main

import (
	"fmt"
	"runtime"
	"syscall"
	"time"
)

func main() {
	runtime.GC()
	var ruStart, ruEnd syscall.Rusage
	syscall.Getrusage(syscall.RUSAGE_SELF, &ruStart)
	wall0 := time.Now()

	result := ""
	for i := 0; i < 10000; i++ {
		result += "hello"
	}

	wall := time.Since(wall0).Seconds()
	syscall.Getrusage(syscall.RUSAGE_SELF, &ruEnd)
	cpu := timevalSub(ruEnd.Utime, ruStart.Utime) + timevalSub(ruEnd.Stime, ruStart.Stime)
	peakKB := float64(ruEnd.Maxrss)

	fmt.Printf("len = %d\n", len(result))
	fmt.Println("__BENCH_METRICS__")
	fmt.Printf("wall_time_s=%.6f\n", wall)
	fmt.Printf("cpu_time_s=%.6f\n", cpu)
	fmt.Printf("peak_memory_kb=%.1f\n", peakKB)
}

func timevalSub(end, start syscall.Timeval) float64 {
	return float64(end.Sec-start.Sec) + float64(end.Usec-start.Usec)/1e6
}
