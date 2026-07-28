#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    SPEC_SCHEMA="$(git rev-parse --show-toplevel)/src/plcc/schemas/spec.schema.json"
    MODEL_SCHEMA="$(git rev-parse --show-toplevel)/src/plcc/schemas/model.schema.json"
    WORK_DIR="${BATS_TEST_TMPDIR}/work"
    mkdir -p "${WORK_DIR}"
    cd "${WORK_DIR}"
    plcc-make --spec="${FIXTURES}/trivial.plcc"
}

@test "plcc-make produces plcc-ng/spec.json" {
    [ -f plcc-ng/spec.json ]
}

@test "plcc-ng/spec.json validates against spec schema" {
    check-jsonschema --schemafile "${SPEC_SCHEMA}" plcc-ng/spec.json
}

@test "plcc-make produces plcc-ng/model.json" {
    [ -f plcc-ng/model.json ]
}

@test "plcc-ng/model.json validates against model schema" {
    check-jsonschema --schemafile "${MODEL_SCHEMA}" plcc-ng/model.json
}

@test "plcc-make produces plcc-ng/ll1.json" {
    [ -f plcc-ng/ll1.json ]
}

@test "plcc-make updates spec.json and .spec-hash when spec changes" {
    first_hash=$(cat plcc-ng/.spec-hash)
    cp "${FIXTURES}/trivial-python.plcc" "${WORK_DIR}/spec2.plcc"
    run plcc-make --spec="${WORK_DIR}/spec2.plcc"
    [ "$status" -eq 0 ]
    second_hash=$(cat plcc-ng/.spec-hash)
    [ "$first_hash" != "$second_hash" ]
}

@test "plcc-spec | plcc-model | plcc-diagram-class-plantuml-emit produces diagram.puml" {
    DIAGRAM_DIR="${BATS_TEST_TMPDIR}/diagram"
    mkdir -p "${DIAGRAM_DIR}"
    plcc-spec "${FIXTURES}/arith.plcc" | plcc-model | plcc-diagram-class-plantuml-emit --output="${DIAGRAM_DIR}"
    [ -f "${DIAGRAM_DIR}/diagram.puml" ]
}

@test "diagram.puml contains expected classes" {
    DIAGRAM_DIR="${BATS_TEST_TMPDIR}/diagram"
    mkdir -p "${DIAGRAM_DIR}"
    plcc-spec "${FIXTURES}/arith.plcc" | plcc-model | plcc-diagram-class-plantuml-emit --output="${DIAGRAM_DIR}"
    grep 'ExprRest' "${DIAGRAM_DIR}/diagram.puml"
    grep 'ExprRest <|-- AddRest' "${DIAGRAM_DIR}/diagram.puml"
}

@test "plcc-diagram-list finds plantuml" {
    run plcc-diagram-list
    [[ "$output" == *"plantuml"* ]]
}

@test "plcc-make trivial-full produces build output for Python" {
    FULL_DIR="${BATS_TEST_TMPDIR}/full"
    mkdir -p "${FULL_DIR}"
    (
        cd "${FULL_DIR}"
        plcc-make --spec="${FIXTURES}/trivial-full.plcc"
        [ -f plcc-ng/ll1.json ]
        [ -d plcc-ng/Python ]
    )
}
