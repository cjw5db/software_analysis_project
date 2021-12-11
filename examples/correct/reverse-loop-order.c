#include <klee/klee.h>
#define LEN 10
#define RES 16

int arr[LEN];

int main(){
  klee_make_symbolic(&arr, sizeof(arr), "Array");
  int i, j;

  for(i = 0; i < 10; i += 1){
    klee_assume(arr[i] > 0);
  }

  for(j = 9; j >= 0; j -= 1){
    arr[j] = 0;
  }

  for(i = 0; i < 10; i += 1){
    if(arr[i] > 0){
      j = 1;
    }
  }

  return 0;
}
