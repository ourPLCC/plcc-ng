#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
}

@test "plcc-diagram-syntactic-plantuml-emit is on PATH" {
    command -v plcc-diagram-syntactic-plantuml-emit
}

@test "plcc-diagram-syntactic-plantuml-emit --help exits 0" {
    run plcc-diagram-syntactic-plantuml-emit --help
    [ "$status" -eq 0 ]
}

@test "emitter produces @startebnf output" {
    run bash -c "plcc-spec '${FIXTURES}/arith.plcc' | plcc-diagram-syntactic-plantuml-emit"
    [ "$status" -eq 0 ]
    [[ "$output" =~ "@startebnf" ]]
    [[ "$output" =~ "@endebnf" ]]
}

@test "emitter output contains grammar rule names" {
    run bash -c "plcc-spec '${FIXTURES}/arith.plcc' | plcc-diagram-syntactic-plantuml-emit"
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Program" ]]
    [[ "$output" =~ "Expr" ]]
    [[ "$output" =~ "Term" ]]
}

@test "emitter output contains quoted terminal" {
    run bash -c "plcc-spec '${FIXTURES}/arith.plcc' | plcc-diagram-syntactic-plantuml-emit"
    [ "$status" -eq 0 ]
    [[ "$output" =~ "'PLUS'" ]]
}
