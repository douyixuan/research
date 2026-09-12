#include <stdio.h>
int main(void) {
  int a = 1;
  int b = 2;
  int c = 3;
  b += c;
  c += b;
  printf("%d\n", a);
  return 0;
}
