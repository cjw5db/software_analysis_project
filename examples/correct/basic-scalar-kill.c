#include <klee/klee.h>
#define LEN 10
#define RES 16

int arr[LEN];

int main(){
  int i, j;
  klee_make_symbolic(&i, sizeof(i), "i");

  klee_assume(i > 0);

  for(j = 0; j < 2; j++){
    i = 0;
  }

  if(i > 0){
    return 1;
  }

  return 0;
}
