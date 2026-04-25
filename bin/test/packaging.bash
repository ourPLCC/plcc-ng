#!/usr/bin/env bash
set -euo pipefail

echo "bin/test/packaging.bash"
echo "-----------------------"

SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( cd "${SCRIPT_DIR}/../.." &> /dev/null && pwd )"
cd "${PROJECT_ROOT}"

VENV=$(mktemp -d)
trap 'rm -rf "${VENV}"' EXIT

python -m venv "${VENV}"
"${VENV}/bin/pip" install --quiet dist/*.whl

# Verify all entry points are installed on the venv PATH
for cmd in plcc-spec plcc-tokens plcc-tree plcc-model \
           plcc-lang-emit plcc-lang-build plcc-lang-list \
           plcc-diagram plcc-diagram-list \
           plcc-make plcc-scan plcc-parse plcc-rep; do
    test -x "${VENV}/bin/${cmd}" || { echo "FAIL: ${cmd} not installed"; exit 1; }
    echo "OK: ${cmd}"
done

# Run end-to-end in the installed venv
export PATH="${VENV}/bin:${PATH}"
WORK_DIR="$(mktemp -d)"
trap 'rm -rf "${VENV}" "${WORK_DIR}"' EXIT
(
    cd "${WORK_DIR}"
    plcc-make "${PROJECT_ROOT}/tests/fixtures/trivial.plcc"
    test -f build/spec.json   || { echo "FAIL: build/spec.json missing"; exit 1; }
    test -f build/model.json  || { echo "FAIL: build/model.json missing"; exit 1; }
)
DIAGRAM_DIR="$(mktemp -d)"
trap 'rm -rf "${VENV}" "${WORK_DIR}" "${DIAGRAM_DIR}"' EXIT
plcc-spec "${PROJECT_ROOT}/tests/fixtures/arith.plcc" | plcc-model | plcc-diagram --output="${DIAGRAM_DIR}"
test -f "${DIAGRAM_DIR}/diagram.puml" || { echo "FAIL: diagram.puml missing"; exit 1; }
echo "packaging: all checks passed"
