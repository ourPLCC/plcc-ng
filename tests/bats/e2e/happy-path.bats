#!/usr/bin/env bats

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    SPEC_SCHEMA="$(git rev-parse --show-toplevel)/src/plcc/schemas/spec.schema.json"
    MODEL_SCHEMA="$(git rev-parse --show-toplevel)/src/plcc/schemas/model.schema.json"
    WORK_DIR="$(mktemp -d)"
    cd "${WORK_DIR}"
    plcc-make "${FIXTURES}/plantuml_only.plcc"
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

@test "plcc-make produces at least one .puml file in build/diagram/" {
    ls build/diagram/*.puml
}

@test "plcc-lang-list finds plantuml after install" {
    run plcc-lang-list
    [[ "$output" == *"plantuml"* ]]
}

@test "plcc-make cleans build/ on rebuild" {
    touch build/diagram/stale-marker.txt
    plcc-make "${FIXTURES}/plantuml_only.plcc"
    [ ! -f build/diagram/stale-marker.txt ]
}

@test "plcc-make produces build/ll1.json" {
    [ -f build/ll1.json ]
}

@test "plcc-make trivial-full produces build output for all three languages" {
    if ! command -v javac &>/dev/null; then skip "JDK not available"; fi
    FULL_DIR="$(mktemp -d 2>/dev/null || mktemp -d -t plcc)"
    (
        cd "${FULL_DIR}"

        # Debug
        echo "${FULL_DIR}"
        pwd
        ls -R

        plcc-make "${FIXTURES}/trivial-full.plcc"
        [ -f build/ll1.json ]
        [ -d build/Java ]
        [ -d build/py ]
        [ -d build/diagram ]
    )
    rm -rf "${FULL_DIR}"
}
