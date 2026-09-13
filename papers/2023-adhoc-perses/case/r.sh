#!/usr/bin/env bash
set -euo pipefail

grep -q 'bug' program.tiny
grep -q 'keep' program.tiny
