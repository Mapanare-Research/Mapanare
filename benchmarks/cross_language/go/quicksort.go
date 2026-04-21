// Benchmark: Quicksort on 10,000 pseudo-random integers -- Go equivalent.
// Uses same LCG (seed=42, a=1103515245, c=12345, mod=2^31) as other languages.
// Checksum = sum of first 10 elements after sort.
package main

import (
	"fmt"
	"runtime"
	"syscall"
	"time"
)

func lcgNext(seed int64) int64 {
	return (seed*1103515245 + 12345) % 2147483648
}

func partition(arr []int64, lo, hi int) int {
	pivot := arr[hi]
	i := lo
	for j := lo; j < hi; j++ {
		if arr[j] < pivot {
			arr[i], arr[j] = arr[j], arr[i]
			i++
		}
	}
	arr[i], arr[hi] = arr[hi], arr[i]
	return i
}

func qsort(arr []int64, lo, hi int) {
	if lo < hi {
		p := partition(arr, lo, hi)
		qsort(arr, lo, p-1)
		qsort(arr, p+1, hi)
	}
}

func main() {
	runtime.GC()
	var ruStart, ruEnd syscall.Rusage
	syscall.Getrusage(syscall.RUSAGE_SELF, &ruStart)
	wall0 := time.Now()

	arr := make([]int64, 0, 10000)
	seed := int64(42)
	for i := 0; i < 10000; i++ {
		seed = lcgNext(seed)
		arr = append(arr, seed%100000)
	}
	qsort(arr, 0, 9999)
	var checksum int64
	for k := 0; k < 10; k++ {
		checksum += arr[k]
	}

	wall := time.Since(wall0).Seconds()
	syscall.Getrusage(syscall.RUSAGE_SELF, &ruEnd)
	cpu := timevalSub(ruEnd.Utime, ruStart.Utime) + timevalSub(ruEnd.Stime, ruStart.Stime)
	peakKB := float64(ruEnd.Maxrss)

	fmt.Printf("checksum = %d\n", checksum)
	fmt.Println("__BENCH_METRICS__")
	fmt.Printf("wall_time_s=%.6f\n", wall)
	fmt.Printf("cpu_time_s=%.6f\n", cpu)
	fmt.Printf("peak_memory_kb=%.1f\n", peakKB)
}

func timevalSub(end, start syscall.Timeval) float64 {
	return float64(end.Sec-start.Sec) + float64(end.Usec-start.Usec)/1e6
}
