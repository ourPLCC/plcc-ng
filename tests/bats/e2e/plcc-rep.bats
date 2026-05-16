#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    WORK_DIR="$(mktemp -d)"
    cd "${WORK_DIR}"
    mkdir -p build
    plcc-spec "${FIXTURES}/arith.plcc" > build/spec.json
    plcc-ll1 < build/spec.json > build/ll1.json
    plcc-model build/spec.json | plcc-python-emit --output=build/calculate
}

teardown() {
    rm -rf "${WORK_DIR}"
}

@test "plcc-rep is on PATH" {
    command -v plcc-rep
}

@test "build/calculate/ is set up correctly" {
    [ -d build/calculate ]
    [ -f build/calculate/main.py ]
    [ -f build/calculate/Program.py ]
}

@test "plcc-rep evaluates 1+2 to 3 in batch mode" {
    run bash -c "echo '1 + 2' | plcc-rep --tool=calculate --grammar-file='${FIXTURES}/arith.plcc'"
    [ "$status" -eq 0 ]
    [[ "$output" == "3" ]]
}

@test "plcc-rep evaluates file argument" {
    echo '1 + 2' > input.txt
    run plcc-rep --tool=calculate --grammar-file="${FIXTURES}/arith.plcc" input.txt
    [ "$status" -eq 0 ]
    [[ "$output" == "3" ]]
}

@test "plcc-rep exits 0 on lex error" {
    run bash -c "echo 'bad input here' | plcc-rep --tool=calculate --grammar-file='${FIXTURES}/arith.plcc'"
    [ "$status" -eq 0 ]
}

@test "plcc-rep session continues after parse error in file argument" {
    echo '1 + 2' > good.txt
    echo 'bad input here' > bad.txt
    run plcc-rep --tool=calculate --grammar-file="${FIXTURES}/arith.plcc" good.txt bad.txt
    [ "$status" -eq 0 ]
    [[ "$output" == *"3"* ]]
}

@test "plcc-rep emits json eval record with --verbose-format=json" {
    run bash -c "echo '1 + 2' | plcc-rep --tool=calculate --verbose-format=json --grammar-file='${FIXTURES}/arith.plcc'"
    [ "$status" -eq 0 ]
    [[ "$output" == *'"kind"'* ]]
    [[ "$output" == *'"result"'* ]]
    [[ "$output" == *'3'* ]]
}

@test "plcc-rep exits non-zero when grammar file does not exist" {
    EMPTY_DIR="$(mktemp -d)"
    trap "rm -rf '${EMPTY_DIR}'" EXIT
    run bash -c "cd '${EMPTY_DIR}' && plcc-rep --tool=calculate --grammar-file='${EMPTY_DIR}/no-such.plcc'"
    [ "$status" -ne 0 ]
}

@test "standalone invocation: plcc-tokens | plcc-trees | python main.py" {
    echo '1 + 2' \
    | plcc-tokens build/spec.json \
    | plcc-trees --ll1=build/ll1.json \
    | python3 -u build/calculate/main.py \
    | python3 -c "import json,sys; r=json.loads(sys.stdin.read()); assert r['value']=='3', r"
}

setup_arbno_build() {
    ARBNO_DIR="$(mktemp -d)"
    mkdir -p "${ARBNO_DIR}/build"
    plcc-spec "${FIXTURES}/trivial-arbno.plcc" > "${ARBNO_DIR}/build/spec.json"
    plcc-ll1 < "${ARBNO_DIR}/build/spec.json" > "${ARBNO_DIR}/build/ll1.json"
    plcc-model "${ARBNO_DIR}/build/spec.json" | plcc-python-emit --output="${ARBNO_DIR}/build/eval"
    cd "${ARBNO_DIR}"
}

@test "trivial-arbno: plcc-rep evaluates 1, 2, 3 to [1, 2, 3]" {
    setup_arbno_build
    run bash -c "echo '1, 2, 3' | plcc-rep --tool=eval --grammar-file='${FIXTURES}/trivial-arbno.plcc'"
    [ "$status" -eq 0 ]
    [[ "$output" == "[1, 2, 3]" ]]
}

@test "trivial-arbno: plcc-rep evaluates empty input to []" {
    setup_arbno_build
    run bash -c "echo '' | plcc-rep --tool=eval --grammar-file='${FIXTURES}/trivial-arbno.plcc'"
    [ "$status" -eq 0 ]
    [[ "$output" == "[]" ]]
}

@test "trivial-arbno: plcc-rep evaluates single item 42 to [42]" {
    setup_arbno_build
    run bash -c "echo '42' | plcc-rep --tool=eval --grammar-file='${FIXTURES}/trivial-arbno.plcc'"
    [ "$status" -eq 0 ]
    [[ "$output" == "[42]" ]]
}
