// Benchmark: Struct allocation -- Go equivalent.
// Allocate 100,000 Points {x, y, z}, accumulate fields.
// Checksum = sum of (x + y + z) for i in 0..100000 = 6 * 99999 * 100000 / 2 = 29999700000.
package main

import (
	"fmt"
	"runtime"
	"syscall"
	"time"
)

type Point struct {
	X, Y, Z int64
}

func makePoint(i int64) *Point {
	return &Point{X: i, Y: i * 2, Z: i * 3}
}

func main() {
	runtime.GC()
	var ruStart, ruEnd syscall.Rusage
	syscall.Getrusage(syscall.RUSAGE_SELF, &ruStart)
	wall0 := time.Now()

	var sum int64
	for i := int64(0); i < 100000; i++ {
		p := makePoint(i)
		sum += p.X + p.Y + p.Z
	}

	wall := time.Since(wall0).Seconds()
	syscall.Getrusage(syscall.RUSAGE_SELF, &ruEnd)
	cpu := timevalSub(ruEnd.Utime, ruStart.Utime) + timevalSub(ruEnd.Stime, ruStart.Stime)
	peakKB := float64(ruEnd.Maxrss)

	fmt.Printf("checksum = %d\n", sum)
	fmt.Println("__BENCH_METRICS__")
	fmt.Printf("wall_time_s=%.6f\n", wall)
	fmt.Printf("cpu_time_s=%.6f\n", cpu)
	fmt.Printf("peak_memory_kb=%.1f\n", peakKB)
}

func timevalSub(end, start syscall.Timeval) float64 {
	return float64(end.Sec-start.Sec) + float64(end.Usec-start.Usec)/1e6
}
