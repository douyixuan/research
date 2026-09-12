#include <stdio.h>
int main(void) {
  int a = 1;
  int b = 2;
  int c = 3;
  a++;
  b--;
  c += 7;
  b += c;
  c += b;
  printf("%d\n", a);
  return 0;
}
