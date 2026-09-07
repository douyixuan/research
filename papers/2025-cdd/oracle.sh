#!/usr/bin/env bash
set -euo pipefail

# Persist a property-test count across Perses subprocess invocations.
echo 1 >> oracle-count.log
rm -f a.out temp.txt

GCC="$(command -v gcc-7.1.0 || command -v gcc)"
CLANG="$(command -v clang-7.1.0 || command -v clang)"

if ! "$GCC" -Wall -Wextra t.c &> temp.txt; then
  exit 1
fi
if ! "$CLANG" -Weverything t.c >> temp.txt 2>&1; then
  exit 1
fi

if grep -q "Wimplicit-int" temp.txt \
  || grep -q "defaulting to type" temp.txt \
  || grep -q "Wmain-return-type" temp.txt \
  || grep -q "Wimplicit-function-declaration" temp.txt \
  || grep -q "Wincompatible-library-redeclaration" temp.txt \
  || grep -q "too few arguments" temp.txt; then
  exit 1
fi

./a.out > temp.txt
grep -q 'world' temp.txt
