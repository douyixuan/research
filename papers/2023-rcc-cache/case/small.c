int main(void) {
  volatile int guard = 0;
  guard += 1;
  guard += 1;
  guard += 1;
  guard += 1;
  guard += 1;
  guard += 1;
  guard += 1;
  guard += 1;
  guard += 1;
  guard += 1;
  guard += 1;
  guard += 1;
  return guard;
}
