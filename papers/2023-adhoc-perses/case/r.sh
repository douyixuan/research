#!/usr/bin/env bash
set -euo pipefail

python3 - <<'PY'
import re
from pathlib import Path

text = Path("program.tiny").read_text()
statement = re.compile(
    r"(?:let\s+[A-Za-z_][A-Za-z0-9_]*\s*=\s*[0-9]+\s*;|"
    r"bug\s+[A-Za-z_][A-Za-z0-9_]*\s*;)"
)
pos = 0
for match in statement.finditer(text):
    if text[pos:match.start()].strip():
        raise SystemExit(1)
    pos = match.end()
if text[pos:].strip():
    raise SystemExit(1)
if not list(statement.finditer(text)):
    raise SystemExit(1)
if not re.search(r"\bbug\s+keep\s*;", text):
    raise SystemExit(1)
PY
