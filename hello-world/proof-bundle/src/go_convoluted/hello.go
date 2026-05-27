package main

import "fmt"

func concealedBytes() ([]byte, []byte) {
	left := []byte{0x48, 0x65, 0x6c, 0x6c, 0x6f}
	right := []byte{0x77, 0x6f, 0x72, 0x6c, 0x64}
	return left, right
}

func renderLine(left []byte, right []byte) string {
	buf := make([]byte, 0, len(left)+len(right)+3)
	buf = append(buf, left...)
	buf = append(buf, byte(','))
	buf = append(buf, byte(' '))
	buf = append(buf, right...)
	buf = append(buf, byte('!'))
	return string(buf)
}

func emit(write func(...any) (int, error), value string) {
	_, _ = write(value)
}

func main() {
	left, right := concealedBytes()
	emit(fmt.Println, renderLine(left, right))
}
