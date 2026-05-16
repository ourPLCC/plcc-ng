#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    SPEC_JSON="$(mktemp)"
    MODEL_JSON="$(mktemp)"
    WORK_DIR="$(mktemp -d)"
    plcc-spec "${FIXTURES}/arith.plcc" > "${SPEC_JSON}"
    plcc-model "${SPEC_JSON}" > "${MODEL_JSON}"
    plcc-python-emit --output="${WORK_DIR}" < "${MODEL_JSON}"
}

teardown() {
    rm -f "${SPEC_JSON}" "${MODEL_JSON}"
    rm -rf "${WORK_DIR}"
}

@test "emit produces one py file per class" {
    for name in Program Expr ExprRest AddRest NilRest Term; do
        [ -f "${WORK_DIR}/${name}.py" ]
    done
}

@test "emit produces main.py" {
    [ -f "${WORK_DIR}/main.py" ]
}

@test "emit copies runtime directory" {
    [ -f "${WORK_DIR}/runtime/base.py" ]
    [ -f "${WORK_DIR}/runtime/registry.py" ]
    [ -f "${WORK_DIR}/runtime/deserialize.py" ]
}

@test "main.py evaluates 1+2 to 3 via plcc-python-run" {
    LL1_JSON="$(mktemp)"
    TREE_FILE="$(mktemp)"
    trap "rm -f '${LL1_JSON}' '${TREE_FILE}'" EXIT
    plcc-ll1 < "${SPEC_JSON}" > "${LL1_JSON}"
    echo '1 + 2' | plcc-tokens "${SPEC_JSON}" | plcc-trees "--ll1=${LL1_JSON}" > "${TREE_FILE}"
    run plcc-python-run --output="${WORK_DIR}" < "${TREE_FILE}"
    [ "$status" -eq 0 ]
    [[ "$output" == *'"value"'* ]]
    [[ "$output" == *'3'* ]]
}

@test "main.py is runnable standalone" {
    run python3 "${WORK_DIR}/main.py" <<< ""
    [ "$status" -eq 0 ]
}

@test "null entry_point in model generates main.py calling _run" {
    NULL_DIR="$(mktemp -d)"
    trap "rm -rf '${NULL_DIR}'" EXIT
    python3 -c "
import json, sys
with open('${MODEL_JSON}') as f:
    m = json.load(f)
for s in m.get('semantics', []):
    s['entry_point'] = None
print(json.dumps(m))
" | plcc-python-emit --output="${NULL_DIR}"
    grep '_run' "${NULL_DIR}/main.py"
}
