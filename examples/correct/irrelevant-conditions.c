#include <klee/klee.h>
#define LEN 10
#define RES 16

int arr[LEN];

int main(){
  klee_make_symbolic(&arr, sizeof(arr), "Array");
  int i;

  for(i = 0; i < LEN; i+= 1){
    arr[i] = 0;
  }

  if(arr[1] > 0){
    return 2;
  }

  for(i = 0; i < LEN; i += 1){
    klee_assume(arr[i] > 0);
  }

  if(arr[0] > 0){
    return 1;
  }

  return 0;
}
