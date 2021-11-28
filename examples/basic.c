#include <klee/klee.h>
#include <stdint.h>
#include <stdio.h>
#define LEN 10000
#define RES 16

int main(){
	int a;
	uint8_t arr[LEN];
	klee_make_symbolic(&arr, sizeof(arr), "Array");

	for(int i = 0; i < LEN; i++){
    klee_assume(arr[i] > 0);
	}

  if(arr[0] == RES){
    return 1;
  }

	return 0;
}
