#!/usr/bin/env bats

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    MODEL_SCHEMA="$(git rev-parse --show-toplevel)/src/plcc/schemas/model.schema.json"
}

@test "plcc-spec | plcc-model produces valid model JSON" {
    run bash -c "plcc-spec '${FIXTURES}/trivial.plcc' | plcc-model -"
    [ "$status" -eq 0 ]
    echo "$output" | check-jsonschema --schemafile "${MODEL_SCHEMA}" -
}

@test "plcc-spec | plcc-model model has correct start symbol" {
    result=$(plcc-spec "${FIXTURES}/trivial.plcc" | plcc-model -)
    echo "$result" | python -c "
import json, sys
m = json.load(sys.stdin)
assert m['start'] == 'program', f'Expected program, got {m[\"start\"]}'
"
}
