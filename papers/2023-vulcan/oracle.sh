#!/usr/bin/env bash
set -euo pipefail
cc="${CC:-gcc}"
"$cc" -O0 -Wall small.c -o small.out >/tmp/vulcan-compile.log 2>&1
output="$(./small.out)"
[[ "$output" == "42" ]]
