package main

import "fmt"

func step(n int) <-chan int {
	ch := make(chan int, 1)
	go func() { ch <- n }()
	return ch
}

func main() {
	total := 0
	for i := 1; i <= 100; i++ {
		total += <-step(i)
	}
	fmt.Printf("checksum = %d\n", total)
}
