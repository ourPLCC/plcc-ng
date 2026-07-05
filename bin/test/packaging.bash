#!/usr/bin/env bash
set -euo pipefail

echo "bin/test/packaging.bash"
echo "-----------------------"

SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( cd "${SCRIPT_DIR}/../.." &> /dev/null && pwd )"
cd "${PROJECT_ROOT}"

# shellcheck source=bin/test/_cache.bash
source "${SCRIPT_DIR}/_cache.bash"

_run() {
    VENV=$(mktemp -d)
    trap 'rm -rf "${VENV}"' EXIT

    # Find Python interpreter - handle worktree case where .venv is in parent
    local python_exe
    if [[ -x "${PROJECT_ROOT}/.venv/bin/python" ]]; then
        python_exe="${PROJECT_ROOT}/.venv/bin/python"
    else
        python_exe="$(which python)" || { echo "FAIL: python not found"; exit 1; }
    fi

    "${python_exe}" -m venv "${VENV}"
    "${VENV}/bin/pip" install --quiet dist/*.whl

    # Verify all entry points are installed on the venv PATH
    for cmd in plcc-spec plcc-tokens plcc-trees plcc-model \
               plcc-lang-emit plcc-lang-build plcc-lang-list \
               plcc-diagram plcc-diagram-emit plcc-diagram-build plcc-diagram-run plcc-diagram-list \
               plcc-diagram-class plcc-diagram-class-plantuml-emit \
               plcc-diagram-syntax plcc-diagram-syntax-plantuml-emit \
               plcc-diagram-plantuml-build plcc-diagram-plantuml-run \
               plcc-make plcc-scan plcc-parse plcc-rep; do
        test -x "${VENV}/bin/${cmd}" || { echo "FAIL: ${cmd} not installed"; exit 1; }
        echo "OK: ${cmd}"
    done

    export PATH="${VENV}/bin:${PATH}"

    # Verify language and diagram discovery
    LANG_LIST=$("${VENV}/bin/plcc-lang-list")
    echo "${LANG_LIST}" | grep -q "python" || { echo "FAIL: plcc-lang-list missing 'python'"; exit 1; }
    echo "${LANG_LIST}" | grep -q "java"   || { echo "FAIL: plcc-lang-list missing 'java'";   exit 1; }
    echo "OK: plcc-lang-list reports python and java"

    DIAGRAM_LIST=$("${VENV}/bin/plcc-diagram-list")
    echo "${DIAGRAM_LIST}" | grep -q "class/plantuml" || { echo "FAIL: plcc-diagram-list missing 'class/plantuml'"; exit 1; }
    echo "OK: plcc-diagram-list reports class/plantuml"
    echo "${DIAGRAM_LIST}" | grep -q "syntax/plantuml" || { echo "FAIL: plcc-diagram-list missing 'syntax/plantuml'"; exit 1; }
    echo "OK: plcc-diagram-list reports syntax/plantuml"

    # Smoke test the installed package (plcc-make + all four emitters)
    "${SCRIPT_DIR}/smoke.bash"

    DIAGRAM_DIR="$(mktemp -d)"
    trap 'rm -rf "${VENV}" "${DIAGRAM_DIR}"' EXIT
    plcc-spec "${PROJECT_ROOT}/tests/fixtures/arith.plcc" | plcc-model | plcc-diagram-class-plantuml-emit --output="${DIAGRAM_DIR}"
    test -f "${DIAGRAM_DIR}/diagram.puml" || { echo "FAIL: diagram.puml missing"; exit 1; }
    echo "packaging: all checks passed"
}

run_cached /tmp/plcc-test-packaging.log _run
