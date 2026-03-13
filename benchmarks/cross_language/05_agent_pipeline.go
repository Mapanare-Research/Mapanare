// Benchmark: Agent Pipeline Processing Messages — Go baseline.
package main

import (
	"fmt"
	"strconv"
	"time"
)

func parser(in <-chan string, out chan<- int) {
	for raw := range in {
		out <- len(raw)
	}
	close(out)
}

func validator(in <-chan int, out chan<- int) {
	for value := range in {
		if value > 0 {
			out <- value
		} else {
			out <- 0
		}
	}
	close(out)
}

func transformer(in <-chan int, out chan<- int) {
	for value := range in {
		out <- value*3 + 7
	}
	close(out)
}

func main() {
	pIn := make(chan string, 1024)
	pOut := make(chan int, 1024)
	vOut := make(chan int, 1024)
	tOut := make(chan int, 1024)

	go parser(pIn, pOut)
	go validator(pOut, vOut)
	go transformer(vOut, tOut)

	start := time.Now()
	total := 0
	for i := 0; i < 1000; i++ {
		msg := "message_payload_data_" + strconv.Itoa(i)
		pIn <- msg
		result := <-tOut
		total += result
	}
	close(pIn)
	elapsed := time.Since(start)

	fmt.Println(total)
	fmt.Println("__BENCH_METRICS__")
	fmt.Printf("wall_time_s=%.6f\n", elapsed.Seconds())
	fmt.Printf("cpu_time_s=%.6f\n", elapsed.Seconds())
	fmt.Println("peak_memory_kb=0")
}
