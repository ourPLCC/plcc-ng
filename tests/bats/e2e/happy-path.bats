#!/usr/bin/env bats

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    SPEC_SCHEMA="$(git rev-parse --show-toplevel)/src/plcc/schemas/spec.schema.json"
    MODEL_SCHEMA="$(git rev-parse --show-toplevel)/src/plcc/schemas/model.schema.json"
    WORK_DIR="$(mktemp -d)"
    cd "${WORK_DIR}"
    plcc-make --spec="${FIXTURES}/trivial.plcc"
}

teardown() {
    rm -rf "${WORK_DIR}"
}

@test "plcc-make produces build/spec.json" {
    [ -f build/spec.json ]
}

@test "build/spec.json validates against spec schema" {
    check-jsonschema --schemafile "${SPEC_SCHEMA}" build/spec.json
}

@test "plcc-make produces build/model.json" {
    [ -f build/model.json ]
}

@test "build/model.json validates against model schema" {
    check-jsonschema --schemafile "${MODEL_SCHEMA}" build/model.json
}

@test "plcc-make produces build/ll1.json" {
    [ -f build/ll1.json ]
}

@test "plcc-make updates spec.json and .spec-hash when spec changes" {
    first_hash=$(cat build/.spec-hash)
    cp "${FIXTURES}/trivial-python.plcc" "${WORK_DIR}/spec2.plcc"
    run plcc-make --spec="${WORK_DIR}/spec2.plcc"
    [ "$status" -eq 0 ]
    second_hash=$(cat build/.spec-hash)
    [ "$first_hash" != "$second_hash" ]
}

@test "plcc-spec | plcc-model | plcc-plantuml-diagram-emit produces diagram.puml" {
    DIAGRAM_DIR="$(mktemp -d)"
    trap "rm -rf '${DIAGRAM_DIR}'" EXIT
    plcc-spec "${FIXTURES}/arith.plcc" | plcc-model | plcc-plantuml-diagram-emit --output="${DIAGRAM_DIR}"
    [ -f "${DIAGRAM_DIR}/diagram.puml" ]
}

@test "diagram.puml contains expected classes" {
    DIAGRAM_DIR="$(mktemp -d)"
    trap "rm -rf '${DIAGRAM_DIR}'" EXIT
    plcc-spec "${FIXTURES}/arith.plcc" | plcc-model | plcc-plantuml-diagram-emit --output="${DIAGRAM_DIR}"
    grep 'ExprRest' "${DIAGRAM_DIR}/diagram.puml"
    grep 'ExprRest <|-- AddRest' "${DIAGRAM_DIR}/diagram.puml"
}

@test "plcc-diagram-list finds plantuml" {
    run plcc-diagram-list
    [[ "$output" == *"plantuml"* ]]
}

@test "plcc-make trivial-full produces build output for Python" {
    FULL_DIR="$(mktemp -d)"
    (
        cd "${FULL_DIR}"
        plcc-make --spec="${FIXTURES}/trivial-full.plcc"
        [ -f build/ll1.json ]
        [ -d build/Python ]
    )
    rm -rf "${FULL_DIR}"
}
