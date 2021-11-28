#include <klee/klee.h>

int work(int);

#define SIZE 10000
int main(int argc, char** argv){
  int count[SIZE];

  //make 10000 element array symbolic
  klee_make_symbolic(&count, sizeof(count), "count");

  //require that all 10000 elements are > 0
  for(int element = 0; element < SIZE; element++){
    klee_assume(count[element] > 0);
  }
  int c;

  for(int element = 0; element < SIZE; element++){
    c = work(count[element]);
  }

  if(c == 1){
    return 2;
  }

  if(count[0] == 1){
    return 1;
  }
  return 0;
}

int work(int a){
  return a;
}
