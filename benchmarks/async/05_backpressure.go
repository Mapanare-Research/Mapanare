package main

import "fmt"

func stageA(n int) <-chan int {
	ch := make(chan int, 1)
	go func() { ch <- n + 1 }()
	return ch
}

func stageB(n int) <-chan int {
	ch := make(chan int, 1)
	go func() { ch <- n * 2 }()
	return ch
}

func stageC(n int) <-chan int {
	ch := make(chan int, 1)
	go func() { ch <- n - 1 }()
	return ch
}

func main() {
	total := 0
	for i := 0; i < 50; i++ {
		a := <-stageA(i)
		b := <-stageB(a)
		c := <-stageC(b)
		total += c
	}
	fmt.Printf("checksum = %d\n", total)
}
