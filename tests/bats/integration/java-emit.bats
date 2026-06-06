#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    if ! command -v javac &>/dev/null; then skip "JDK not available"; fi
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    WORK_DIR="$(mktemp -d)"
    plcc-spec "${FIXTURES}/trivial-java.plcc" \
        | plcc-model \
        | plcc-java-emit --output="${WORK_DIR}"
    plcc-java-build --output="${WORK_DIR}"
}

teardown() { rm -rf "${WORK_DIR}"; }

@test "emit produces one .java file per class" {
    [ -f "${WORK_DIR}/Program.java" ]
}

@test "emit produces Main.java" {
    [ -f "${WORK_DIR}/Main.java" ]
}

@test "emit copies runtime directory" {
    [ -f "${WORK_DIR}/runtime/Node.java" ]
    [ -f "${WORK_DIR}/runtime/Deserializer.java" ]
    ls "${WORK_DIR}/runtime/org.json"*.jar
}

@test "build produces .class files" {
    [ -f "${WORK_DIR}/Program.class" ]
    [ -f "${WORK_DIR}/Main.class" ]
}

@test "run exits 0 on valid tree JSON" {
    TREE='{"kind":"tree","rule":"Program","children":[["num",{"kind":"token","name":"NUM","lexeme":"99"}]]}'
    run bash -c "echo '${TREE}' | plcc-java-run --output='${WORK_DIR}'"
    [ "$status" -eq 0 ]
}

@test "run outputs token lexeme from void _run()" {
    TREE='{"kind":"tree","rule":"Program","children":[["num",{"kind":"token","name":"NUM","lexeme":"99"}]]}'
    run bash -c "echo '${TREE}' | plcc-java-run --output='${WORK_DIR}'"
    [[ "$output" == *"99"* ]]
}

@test "run outputs JSON result record" {
    TREE='{"kind":"tree","rule":"Program","children":[["num",{"kind":"token","name":"NUM","lexeme":"99"}]]}'
    run bash -c "echo '${TREE}' | plcc-java-run --output='${WORK_DIR}'"
    [[ "$output" == *'"kind"'* ]]
    [[ "$output" == *'"result"'* ]]
}

@test "full pipeline: plcc-tokens | plcc-trees | plcc-java-run" {
    SPEC_JSON="$(mktemp)"
    LL1_JSON="$(mktemp)"
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    plcc-spec "${FIXTURES}/trivial-java.plcc" > "${SPEC_JSON}"
    plcc-ll1 < "${SPEC_JSON}" > "${LL1_JSON}"
    run bash -c "echo '42' | plcc-tokens '${SPEC_JSON}' | plcc-trees --ll1='${LL1_JSON}' | plcc-java-run --output='${WORK_DIR}'"
    rm -f "${SPEC_JSON}" "${LL1_JSON}"
    [ "$status" -eq 0 ]
    [[ "$output" == *"42"* ]]
}

@test "no-semantics grammar generates _Start.java" {
    NO_SEM_DIR="$(mktemp -d)"
    trap "rm -rf '${NO_SEM_DIR}'" EXIT
    plcc-spec "${FIXTURES}/trivial.plcc" | plcc-model | plcc-java-emit --output="${NO_SEM_DIR}"
    [ -f "${NO_SEM_DIR}/_Start.java" ]
}

@test "no-semantics grammar: start class extends _Start" {
    NO_SEM_DIR="$(mktemp -d)"
    trap "rm -rf '${NO_SEM_DIR}'" EXIT
    plcc-spec "${FIXTURES}/trivial.plcc" | plcc-model | plcc-java-emit --output="${NO_SEM_DIR}"
    grep 'extends _Start' "${NO_SEM_DIR}/Program.java"
}

@test "no-semantics grammar: compiles and runs on empty input" {
    NO_SEM_DIR="$(mktemp -d)"
    trap "rm -rf '${NO_SEM_DIR}'" EXIT
    plcc-spec "${FIXTURES}/trivial.plcc" | plcc-model | plcc-java-emit --output="${NO_SEM_DIR}"
    plcc-java-build --output="${NO_SEM_DIR}"
    run bash -c "echo '' | plcc-java-run --output='${NO_SEM_DIR}'"
    [ "$status" -eq 0 ]
}
