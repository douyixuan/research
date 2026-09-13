#!/usr/bin/env bash
set -euo pipefail

program="$(find . -maxdepth 1 -type f -name '*.calc' -print -quit)"
[[ -n "${program}" ]]
compact="$(tr -d '[:space:]' < "${program}")"
[[ "${compact}" == *"lettarget=7;"* ]]
[[ "${compact}" == *"printtarget;"* ]]
