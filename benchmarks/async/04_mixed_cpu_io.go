package main

import (
	"fmt"
	"sync"
	"sync/atomic"
)

func cpuTask(n int) int {
	total := 0
	for i := 1; i <= n; i++ {
		total += i
	}
	return total
}

func main() {
	var total int64
	var wg sync.WaitGroup
	for i := 1; i <= 50; i++ {
		wg.Add(1)
		if i%2 == 0 {
			go func(n int) {
				defer wg.Done()
				atomic.AddInt64(&total, int64(cpuTask(n)))
			}(i)
		} else {
			go func(id int) {
				defer wg.Done()
				atomic.AddInt64(&total, int64(id))
			}(i)
		}
	}
	wg.Wait()
	fmt.Printf("checksum = %d\n", total)
}
