#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    WORK_DIR="$(mktemp -d)"
    cd "${WORK_DIR}"
    mkdir -p plcc-ng
    plcc-spec "${FIXTURES}/arith.plcc" > plcc-ng/spec.json
    plcc-ll1 < plcc-ng/spec.json > plcc-ng/ll1.json
    plcc-model plcc-ng/spec.json | plcc-python-emit --output=plcc-ng/Python
}

teardown() {
    rm -rf "${WORK_DIR}"
}

@test "plcc-rep is on PATH" {
    command -v plcc-rep
}

@test "plcc-ng/Python/ is set up correctly" {
    [ -d plcc-ng/Python ]
    [ -f plcc-ng/Python/main.py ]
    [ -f plcc-ng/Python/Program.py ]
}

@test "plcc-rep evaluates 1+2 to 3 in batch mode" {
    run --separate-stderr bash -c "echo '1 + 2' | plcc-rep --spec='${FIXTURES}/arith.plcc'"
    [ "$status" -eq 0 ]
    [[ "${lines[-1]}" == "3" ]]
}

@test "plcc-rep evaluates file argument" {
    echo '1 + 2' > input.txt
    run --separate-stderr plcc-rep --spec="${FIXTURES}/arith.plcc" input.txt
    [ "$status" -eq 0 ]
    [[ "${lines[-1]}" == "3" ]]
}

@test "plcc-rep exits 0 on lex error" {
    run --separate-stderr bash -c "echo 'bad input here' | plcc-rep --spec='${FIXTURES}/arith.plcc'"
    [ "$status" -eq 0 ]
}

@test "plcc-rep session continues after parse error in file argument" {
    echo '1 + 2' > good.txt
    echo 'bad input here' > bad.txt
    run --separate-stderr plcc-rep --spec="${FIXTURES}/arith.plcc" good.txt bad.txt
    [ "$status" -eq 0 ]
    [[ "$output" == *"3"* ]]
}

@test "plcc-rep emits json eval record with --verbose-format=json" {
    run --separate-stderr bash -c "echo '1 + 2' | plcc-rep --verbose-format=json --spec='${FIXTURES}/arith.plcc'"
    [ "$status" -eq 0 ]
    [[ "$output" == *'"kind"'* ]]
    [[ "$output" == *'"result"'* ]]
    [[ "$output" == *'3'* ]]
}

@test "plcc-rep exits non-zero when spec file does not exist" {
    EMPTY_DIR="$(mktemp -d)"
    trap "rm -rf '${EMPTY_DIR}'" EXIT
    run bash -c "cd '${EMPTY_DIR}' && plcc-rep --spec='${EMPTY_DIR}/no-such.plcc'"
    [ "$status" -ne 0 ]
}

@test "standalone invocation: plcc-tokens | plcc-trees | python main.py" {
    echo '1 + 2' \
    | plcc-tokens plcc-ng/spec.json \
    | plcc-trees --ll1=plcc-ng/ll1.json \
    | python3 -u plcc-ng/Python/main.py \
    | python3 -c "import json,sys; recs=[json.loads(l) for l in sys.stdin if l.strip()]; r=next(x for x in recs if x.get('kind')=='result'); assert r['value']=='3', r"
}

setup_arbno_build() {
    ARBNO_DIR="$(mktemp -d)"
    mkdir -p "${ARBNO_DIR}/plcc-ng"
    plcc-spec "${FIXTURES}/trivial-arbno.plcc" > "${ARBNO_DIR}/plcc-ng/spec.json"
    plcc-ll1 < "${ARBNO_DIR}/plcc-ng/spec.json" > "${ARBNO_DIR}/plcc-ng/ll1.json"
    plcc-model "${ARBNO_DIR}/plcc-ng/spec.json" | plcc-python-emit --output="${ARBNO_DIR}/plcc-ng/Python"
    cd "${ARBNO_DIR}"
}

@test "trivial-arbno: plcc-rep evaluates 1, 2, 3 to [1, 2, 3]" {
    setup_arbno_build
    run --separate-stderr bash -c "echo '1, 2, 3' | plcc-rep --spec='${FIXTURES}/trivial-arbno.plcc'"
    [ "$status" -eq 0 ]
    [[ "${lines[-1]}" == "[1, 2, 3]" ]]
}

@test "trivial-arbno: plcc-rep evaluates empty input to []" {
    setup_arbno_build
    run --separate-stderr bash -c "echo '' | plcc-rep --spec='${FIXTURES}/trivial-arbno.plcc'"
    [ "$status" -eq 0 ]
    [[ "${lines[-1]}" == "[]" ]]
}

@test "trivial-arbno: plcc-rep evaluates single item 42 to [42]" {
    setup_arbno_build
    run --separate-stderr bash -c "echo '42' | plcc-rep --spec='${FIXTURES}/trivial-arbno.plcc'"
    [ "$status" -eq 0 ]
    [[ "${lines[-1]}" == "[42]" ]]
}

@test "plcc-rep --verbose-format=json shows a real value for the default _run()" {
    cat > spec.plcc << 'EOF'
token NUM '\d+'
skip WS '\s+'
%
<Program> ::= <NUM:num>
%
Python
EOF
    run --separate-stderr bash -c "echo '42' | plcc-rep --verbose-format=json --spec=spec.plcc"
    [ "$status" -eq 0 ]
    [[ "$output" == *'"kind"'* ]]
    [[ "$output" == *'"result"'* ]]
    [[ "$output" != *'"value": null'* ]]
    [[ "$output" == *'"value": "'* ]]
}
