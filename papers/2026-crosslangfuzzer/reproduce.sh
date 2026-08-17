#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS="${1:-$ROOT/results}"
CACHE="${KOTLIN_CACHE_DIR:-${XDG_CACHE_HOME:-$HOME/.cache}/crosslangfuzzer-kotlin}"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

mkdir -p "$RESULTS" "$CACHE" "$WORK/src" "$WORK/java-classes"
rm -f "$RESULTS"/*.log "$RESULTS"/summary.md

for tool in java javac curl unzip; do
  command -v "$tool" >/dev/null || { echo "missing required tool: $tool" >&2; exit 2; }
done

if command -v sha256sum >/dev/null; then
  hash_file() { sha256sum "$1" | awk '{print $1}'; }
elif command -v shasum >/dev/null; then
  hash_file() { shasum -a 256 "$1" | awk '{print $1}'; }
else
  echo "missing sha256sum or shasum" >&2
  exit 2
fi

cat > "$WORK/src/ITop.java" <<'EOF'
public interface ITop {
    default public void func() {}
}
EOF

cat > "$WORK/src/ISecondary.java" <<'EOF'
public interface ISecondary extends ITop {
    default public void func() {}
}
EOF

cat > "$WORK/src/IChild.java" <<'EOF'
public interface IChild extends ISecondary, ITop {
}
EOF

cat > "$WORK/src/GrandParent.java" <<'EOF'
public class GrandParent implements ITop {
    final public void func() {}
}
EOF

cat > "$WORK/src/Parent.java" <<'EOF'
public class Parent extends GrandParent implements ISecondary {
}
EOF

cat > "$WORK/src/ChildJava.java" <<'EOF'
public abstract class ChildJava extends Parent implements IChild {
}
EOF

cat > "$WORK/src/Child.kt" <<'EOF'
abstract class Child : Parent(), IChild
EOF

# Oracle: the equivalent Java hierarchy is valid.
javac -d "$WORK/java-classes" \
  "$WORK/src/ITop.java" \
  "$WORK/src/ISecondary.java" \
  "$WORK/src/IChild.java" \
  "$WORK/src/GrandParent.java" \
  "$WORK/src/Parent.java"

if javac -cp "$WORK/java-classes" -d "$WORK/java-classes" "$WORK/src/ChildJava.java" \
    >"$RESULTS/javac.log" 2>&1; then
  JAVA_ORACLE="PASS"
else
  JAVA_ORACLE="FAIL"
  cat "$RESULTS/javac.log" >&2
  echo "Java oracle unexpectedly rejected the equivalent hierarchy" >&2
  exit 1
fi

download_kotlin() {
  local version="$1"
  local zip="$CACHE/kotlin-compiler-$version.zip"
  local sha="$CACHE/kotlin-compiler-$version.zip.sha256"
  local base="https://github.com/JetBrains/kotlin/releases/download/v$version/kotlin-compiler-$version.zip"

  if [[ ! -s "$zip" ]]; then
    curl -fL --retry 3 --retry-delay 2 -o "$zip" "$base"
  fi
  curl -fsSL --retry 3 --retry-delay 2 -o "$sha" "$base.sha256"

  local expected actual
  expected="$(awk '{print $1}' "$sha" | tr -d '\r\n')"
  actual="$(hash_file "$zip")"
  if [[ -z "$expected" || "$expected" != "$actual" ]]; then
    echo "checksum mismatch for Kotlin $version" >&2
    rm -f "$zip"
    exit 1
  fi

  local unpack="$WORK/kotlin-$version"
  mkdir -p "$unpack"
  unzip -q "$zip" -d "$unpack"
  printf '%s\n' "$unpack/kotlinc/bin/kotlinc"
}

compile_kotlin() {
  local version="$1"
  local kotlinc="$2"
  local log="$RESULTS/kotlin-$version.log"
  local out="$WORK/kotlin-classes-$version"
  mkdir -p "$out"

  set +e
  "$kotlinc" "$WORK/src/Child.kt" \
    -classpath "$WORK/java-classes" \
    -d "$out" >"$log" 2>&1
  local status=$?
  set -e
  printf '%s\n' "$status"
}

KOTLINC_210="$(download_kotlin 2.1.0)"
STATUS_210="$(compile_kotlin 2.1.0 "$KOTLINC_210")"

# KT-74109: Kotlin 2.1.0 should falsely reject this valid hierarchy.
if [[ "$STATUS_210" -eq 0 ]]; then
  echo "Kotlin 2.1.0 unexpectedly accepted KT-74109; historical bug not reproduced" >&2
  exit 1
fi
if ! grep -Eiq 'inherits multiple implementations|must override.*func|MANY_IMPL_MEMBER_NOT_IMPLEMENTED' \
    "$RESULTS/kotlin-2.1.0.log"; then
  echo "Kotlin 2.1.0 rejected the program, but diagnostic did not match KT-74109" >&2
  cat "$RESULTS/kotlin-2.1.0.log" >&2
  exit 1
fi
HISTORICAL="REPRODUCED"

KOTLINC_CURRENT="$(download_kotlin 2.4.10)"
STATUS_CURRENT="$(compile_kotlin 2.4.10 "$KOTLINC_CURRENT")"
if [[ "$STATUS_CURRENT" -eq 0 ]]; then
  CURRENT="ACCEPTED (bug no longer reproduces in 2.4.10)"
else
  CURRENT="REJECTED (bug still reproduces in 2.4.10)"
fi

JAVA_VERSION="$(java -version 2>&1 | head -n 1)"
{
  echo "# CrossLangFuzzer KT-74109 reproduction"
  echo
  echo "| Check | Result |"
  echo "|---|---|"
  echo "| Java equivalent hierarchy | $JAVA_ORACLE |"
  echo "| Kotlin 2.1.0 historical trigger | $HISTORICAL (exit $STATUS_210) |"
  echo "| Kotlin 2.4.10 drift check | $CURRENT (exit $STATUS_CURRENT) |"
  echo
  echo "Environment: \`$JAVA_VERSION\`"
  echo
  echo "## Interpretation"
  echo
  echo "Java acceptance plus Kotlin 2.1.0 rejection reproduces the reported cross-language override-resolution inconsistency."
  echo "The 2.4.10 row is deliberately observational and records whether the same minimized trigger survives in the current stable compiler."
  echo
  echo "## Logs"
  echo
  echo "- \`javac.log\`"
  echo "- \`kotlin-2.1.0.log\`"
  echo "- \`kotlin-2.4.10.log\`"
} > "$RESULTS/summary.md"

cat "$RESULTS/summary.md"
