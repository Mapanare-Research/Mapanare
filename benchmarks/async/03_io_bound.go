package main

import (
	"fmt"
	"sync"
	"sync/atomic"
)

func main() {
	var total int64
	var wg sync.WaitGroup
	for i := 0; i < 1000; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			atomic.AddInt64(&total, 1)
		}()
	}
	wg.Wait()
	fmt.Printf("checksum = %d\n", total)
}
