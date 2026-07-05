#!/usr/bin/env bash
set -euo pipefail

echo "bin/test/smoke.bash"
echo "-------------------"

# Smoke test an installed plcc-ng. Assumes the plcc-* entry points are
# already on PATH (installed from a wheel or from TestPyPI).
#
# Deliberately not cached via _cache.bash: the result depends on which
# package is installed on PATH, not on git state.

SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( cd "${SCRIPT_DIR}/../.." &> /dev/null && pwd )"

SPEC="${PROJECT_ROOT}/tests/fixtures/trivial.plcc"

WORK_DIR="$(mktemp -d)"
EMIT_DIR="$(mktemp -d)"
trap 'rm -rf "${WORK_DIR}" "${EMIT_DIR}"' EXIT

(
    cd "${WORK_DIR}"
    plcc-make --spec="${SPEC}"
    test -f plcc-ng/spec.json  || { echo "FAIL: plcc-ng/spec.json missing"; exit 1; }
    test -f plcc-ng/model.json || { echo "FAIL: plcc-ng/model.json missing"; exit 1; }
)
echo "OK: plcc-make produces spec.json and model.json"

MODEL_JSON="${WORK_DIR}/model.json"
plcc-spec "${SPEC}" | plcc-model > "${MODEL_JSON}"

# check_emitted <lang> <expected-glob>...
# Emits for <lang> into a fresh directory, then asserts each expected
# glob matches at least one file there.
check_emitted() {
    local lang="$1"; shift
    local out="${EMIT_DIR}/${lang}"
    mkdir -p "${out}"
    plcc-lang-emit --target="${lang}" --output="${out}" < "${MODEL_JSON}"
    local pattern
    for pattern in "$@"; do
        compgen -G "${out}/${pattern}" > /dev/null \
            || { echo "FAIL: ${lang}: ${pattern} missing"; exit 1; }
    done
    echo "OK: ${lang} emit produces expected files"
}

check_emitted python     Program.py   runtime/base.py
check_emitted java       Program.java runtime/Token.java "runtime/org.json-*.jar"
check_emitted javascript Program.js   runtime/base.js
check_emitted haskell    Program.hs   Token.hs interpreter.cabal

echo "smoke: all checks passed"
