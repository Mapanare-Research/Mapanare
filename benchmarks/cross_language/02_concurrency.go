// Benchmark: Concurrent Message Passing -- Go goroutines + channels

package main

import (
	"fmt"
	"runtime"
	"time"
)

func worker(inbox <-chan int, outbox chan<- int) {
	for val := range inbox {
		outbox <- val*2 + 1
	}
	close(outbox)
}

func main() {
	inbox := make(chan int, 1024)
	outbox := make(chan int, 1024)

	runtime.GC()
	var memBefore runtime.MemStats
	runtime.ReadMemStats(&memBefore)

	go worker(inbox, outbox)

	start := time.Now()
	sum := 0
	for i := 0; i < 10000; i++ {
		inbox <- i
		result := <-outbox
		sum += result
	}
	close(inbox)
	elapsed := time.Since(start)

	var memAfter runtime.MemStats
	runtime.ReadMemStats(&memAfter)

	fmt.Printf("sum = %d\n", sum)
	fmt.Printf("__BENCH_METRICS__\n")
	fmt.Printf("wall_time_s=%.6f\n", elapsed.Seconds())
	fmt.Printf("peak_memory_kb=%.1f\n", float64(memAfter.TotalAlloc-memBefore.TotalAlloc)/1024.0)
}
