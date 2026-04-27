#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    WORK_DIR="$(mktemp -d)"
    cd "${WORK_DIR}"
    mkdir -p build
    plcc-spec "${FIXTURES}/arith.plcc" > build/spec.json
    plcc-ll1 < build/spec.json > build/ll1.json
    plcc-spec "${FIXTURES}/arith.plcc" | plcc-model | plcc-python-emit --output=build/calculate
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
    run bash -c "echo '1 + 2' | plcc-rep --tool=calculate '${FIXTURES}/arith.plcc'"
    [ "$status" -eq 0 ]
    [[ "$output" == "3" ]]
}

@test "plcc-rep evaluates file argument" {
    echo '1 + 2' > input.txt
    run plcc-rep --tool=calculate "${FIXTURES}/arith.plcc" input.txt
    [ "$status" -eq 0 ]
    [[ "$output" == "3" ]]
}

@test "plcc-rep exits 0 on lex error" {
    run bash -c "echo 'bad input here' | plcc-rep --tool=calculate '${FIXTURES}/arith.plcc'"
    [ "$status" -eq 0 ]
}

@test "plcc-rep session continues after parse error in file argument" {
    echo '1 + 2' > good.txt
    echo 'bad input here' > bad.txt
    run plcc-rep --tool=calculate "${FIXTURES}/arith.plcc" good.txt bad.txt
    [ "$status" -eq 0 ]
    [[ "$output" == *"3"* ]]
}

@test "plcc-rep emits json eval record with --verbose-format=json" {
    run bash -c "echo '1 + 2' | plcc-rep --tool=calculate --verbose-format=json '${FIXTURES}/arith.plcc'"
    [ "$status" -eq 0 ]
    [[ "$output" == *'"kind"'* ]]
    [[ "$output" == *'"result"'* ]]
    [[ "$output" == *'3'* ]]
}

@test "plcc-rep exits non-zero without build/" {
    EMPTY_DIR="$(mktemp -d)"
    run bash -c "cd '${EMPTY_DIR}' && plcc-rep --tool=calculate '${FIXTURES}/arith.plcc'"
    [ "$status" -ne 0 ]
    rm -rf "${EMPTY_DIR}"
}

@test "standalone invocation: plcc-tokens | plcc-tree | python main.py" {
    echo '1 + 2' \
    | plcc-tokens build/spec.json \
    | plcc-tree --ll1=build/ll1.json \
    | python3 -u build/calculate/main.py \
    | python3 -c "import json,sys; r=json.loads(sys.stdin.read()); assert r['value']=='3', r"
}
