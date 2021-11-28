#include <klee/klee.h>
#include <stdlib.h>

struct data {
  short val;
  struct data *next;
};

int main(){
  struct data *ptr;
  struct data *head;
  head = (struct data *) malloc(sizeof(struct data));
  ptr = head;
  for (int i = 0; i < 10000; i++){
    klee_make_symbolic(&(ptr->val), sizeof(ptr->val), "a");
    ptr->next = (struct data *) malloc(sizeof(struct data));
    ptr = ptr->next;
  }

  ptr = head;
  while(ptr != NULL){
    klee_assume(ptr->val > 0);
    ptr = ptr->next;
  }

  if(ptr->val == 100){
    return 1;
  }
  return 0;
}

