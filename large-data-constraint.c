#include <klee/klee.h>
#include <stdint.h>
#include <stdio.h>
#define LEN 10
#define RES 16

int main(){
	int a;
	uint8_t arr[LEN];
	klee_make_symbolic(&arr, sizeof(arr), "Array");

  //klee_assume(arr[0] > 0);
  /*
	for(int i = 1; i < LEN; i++){
    klee_assume(arr[i] > 0);
	}
  */

  if(arr[0] == RES){
    return 1;
  }
  /*
	if(arr[9999] == 2) { //bb 1
    return 1;
  }
  if(arr[4350] == 3) { //bb2
    return 2;
  }
  */
	return 0;
}


/*
klee_assume is called for arr[0-9999]

bb1 arr[9999]
bb2 arr[4350]

output:
only index 9999 and 4350 affect paths, 9997 klee_assume calls are unnecessary

for(int i = 0; i < LEN; i++){
  klee_assume(arr[i] > 0);
}
->
klee_assume(arr[9999] > 0);
klee_assume(arr[4350] > 0);
*/
