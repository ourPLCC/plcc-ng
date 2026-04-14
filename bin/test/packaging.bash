#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( cd "${SCRIPT_DIR}/../.." &> /dev/null && pwd )"
cd "${PROJECT_ROOT}"

VENV=$(mktemp -d)
trap "rm -rf ${VENV}" EXIT

python -m venv "${VENV}"
"${VENV}/bin/pip" install --quiet dist/*.whl

# Verify all entry points are installed on the venv PATH
for cmd in plcc-spec plcc-tokens plcc-tree plcc-model \
           plcc-lang-emit plcc-lang-build plcc-lang-list \
           plcc-plantuml-emit plcc-make plcc-scan plcc-parse plcc-rep; do
    test -x "${VENV}/bin/${cmd}" || { echo "FAIL: ${cmd} not installed"; exit 1; }
    echo "OK: ${cmd}"
done

# Run end-to-end in the installed venv
"${VENV}/bin/plcc-make" tests/fixtures/trivial.plcc
test -f build/spec.json    || { echo "FAIL: build/spec.json missing"; exit 1; }
test -f build/model.json   || { echo "FAIL: build/model.json missing"; exit 1; }
ls build/diagram/*.puml    || { echo "FAIL: no .puml in build/diagram/"; exit 1; }
echo "packaging: all checks passed"
