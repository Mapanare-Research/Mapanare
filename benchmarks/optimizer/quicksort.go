// Benchmark 2: Quicksort — Go equivalent.
package main

import "fmt"

func lcgNext(seed int) int {
	return (seed*1103515245 + 12345) % 2147483648
}

func partition(arr []int, lo, hi int) int {
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

func qsort(arr []int, lo, hi int) {
	if lo < hi {
		p := partition(arr, lo, hi)
		qsort(arr, lo, p-1)
		qsort(arr, p+1, hi)
	}
}

func main() {
	arr := make([]int, 0, 10000)
	seed := 42
	for i := 0; i < 10000; i++ {
		seed = lcgNext(seed)
		arr = append(arr, seed%100000)
	}
	qsort(arr, 0, 9999)
	checksum := 0
	for i := 0; i < 10; i++ {
		checksum += arr[i]
	}
	fmt.Printf("checksum = %d\n", checksum)
}
