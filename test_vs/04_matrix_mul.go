// Benchmark: Matrix Multiplication -- Go

package main

import (
	"fmt"
	"runtime"
	"time"
)

func matmul(a, b [][]float64, n int) [][]float64 {
	c := make([][]float64, n)
	for i := range c {
		c[i] = make([]float64, n)
		for j := 0; j < n; j++ {
			s := 0.0
			for k := 0; k < n; k++ {
				s += a[i][k] * b[k][j]
			}
			c[i][j] = s
		}
	}
	return c
}

func main() {
	size := 100
	a := make([][]float64, size)
	b := make([][]float64, size)
	for i := 0; i < size; i++ {
		a[i] = make([]float64, size)
		b[i] = make([]float64, size)
		for j := 0; j < size; j++ {
			a[i][j] = 1.0
			b[i][j] = 2.0
		}
	}

	runtime.GC()
	var memBefore runtime.MemStats
	runtime.ReadMemStats(&memBefore)

	start := time.Now()
	c := matmul(a, b, size)
	elapsed := time.Since(start)

	var memAfter runtime.MemStats
	runtime.ReadMemStats(&memAfter)

	fmt.Printf("c[0][0] = %.1f\n", c[0][0])
	fmt.Printf("__BENCH_METRICS__\n")
	fmt.Printf("wall_time_s=%.6f\n", elapsed.Seconds())
	fmt.Printf("peak_memory_kb=%.1f\n", float64(memAfter.TotalAlloc-memBefore.TotalAlloc)/1024.0)
}
