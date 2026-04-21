// Benchmark: Prime counter via trial division up to 100,000 -- Go equivalent.
// Mirrors the Mapanare is_prime (list_ops.mn).
// Expected output: primes = 9592.
package main

import (
	"fmt"
	"runtime"
	"syscall"
	"time"
)

func isPrime(n int64) bool {
	if n < 2 {
		return false
	}
	if n < 4 {
		return true
	}
	if n%2 == 0 {
		return false
	}
	d := int64(3)
	for d*d <= n {
		if n%d == 0 {
			return false
		}
		d += 2
	}
	return true
}

func main() {
	runtime.GC()
	var ruStart, ruEnd syscall.Rusage
	syscall.Getrusage(syscall.RUSAGE_SELF, &ruStart)
	wall0 := time.Now()

	var count int64
	for i := int64(0); i < 100000; i++ {
		if isPrime(i) {
			count++
		}
	}

	wall := time.Since(wall0).Seconds()
	syscall.Getrusage(syscall.RUSAGE_SELF, &ruEnd)
	cpu := timevalSub(ruEnd.Utime, ruStart.Utime) + timevalSub(ruEnd.Stime, ruStart.Stime)
	peakKB := float64(ruEnd.Maxrss)

	fmt.Printf("primes = %d\n", count)
	fmt.Println("__BENCH_METRICS__")
	fmt.Printf("wall_time_s=%.6f\n", wall)
	fmt.Printf("cpu_time_s=%.6f\n", cpu)
	fmt.Printf("peak_memory_kb=%.1f\n", peakKB)
}

func timevalSub(end, start syscall.Timeval) float64 {
	return float64(end.Sec-start.Sec) + float64(end.Usec-start.Usec)/1e6
}
