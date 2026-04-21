// Benchmark: Enum dispatch -- Go equivalent.
// Tagged union via discriminant int + two payload fields.
// Mirrors the Mapanare 6-variant Shape (Circle, Square, Triangle, Point, Line, Rect).
// Checksum must equal 52818168 across all languages.
package main

import (
	"fmt"
	"runtime"
	"syscall"
	"time"
)

type Shape struct {
	Tag int64 // 0=Circle, 1=Square, 2=Triangle, 3=Point, 4=Line, 5=Rect
	A   int64
	B   int64
}

func area(s Shape) int64 {
	switch s.Tag {
	case 0:
		return s.A * s.A * 3
	case 1:
		return s.A * s.A
	case 2:
		return s.A * s.B / 2
	case 3:
		return 0
	case 4:
		return s.A
	default: // 5 = Rect
		return s.A * s.B
	}
}

func makeShape(i int64) Shape {
	tag := i % 6
	switch tag {
	case 0:
		return Shape{Tag: 0, A: i%50 + 1}
	case 1:
		return Shape{Tag: 1, A: i%30 + 1}
	case 2:
		return Shape{Tag: 2, A: i%20 + 1, B: i%40 + 1}
	case 3:
		return Shape{Tag: 3}
	case 4:
		return Shape{Tag: 4, A: i%100 + 1}
	default:
		return Shape{Tag: 5, A: i%25 + 1, B: i%35 + 1}
	}
}

func main() {
	runtime.GC()
	var ruStart, ruEnd syscall.Rusage
	syscall.Getrusage(syscall.RUSAGE_SELF, &ruStart)
	wall0 := time.Now()

	var total int64
	for i := int64(0); i < 100000; i++ {
		total += area(makeShape(i))
	}

	wall := time.Since(wall0).Seconds()
	syscall.Getrusage(syscall.RUSAGE_SELF, &ruEnd)
	cpu := timevalSub(ruEnd.Utime, ruStart.Utime) + timevalSub(ruEnd.Stime, ruStart.Stime)
	peakKB := float64(ruEnd.Maxrss)

	fmt.Printf("checksum = %d\n", total)
	fmt.Println("__BENCH_METRICS__")
	fmt.Printf("wall_time_s=%.6f\n", wall)
	fmt.Printf("cpu_time_s=%.6f\n", cpu)
	fmt.Printf("peak_memory_kb=%.1f\n", peakKB)
}

func timevalSub(end, start syscall.Timeval) float64 {
	return float64(end.Sec-start.Sec) + float64(end.Usec-start.Usec)/1e6
}
