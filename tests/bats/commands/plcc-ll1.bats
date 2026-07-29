#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    SCHEMA="$(git rev-parse --show-toplevel)/src/plcc/schemas/ll1.schema.json"
    SPEC_JSON="${BATS_TEST_TMPDIR}/spec.json"
    plcc-spec "${FIXTURES}/trivial.plcc" > "${SPEC_JSON}"
    ARBNO_SPEC_JSON="${BATS_TEST_TMPDIR}/arbno-spec.json"
    plcc-spec "${FIXTURES}/arbno-mid-body-terminal.plcc" > "${ARBNO_SPEC_JSON}"
    CONFLICT_SPEC_JSON="${BATS_TEST_TMPDIR}/conflict-spec.json"
    plcc-spec "${FIXTURES}/ll1-conflicts.plcc" > "${CONFLICT_SPEC_JSON}"
}

@test "plcc-ll1 is on PATH" { command -v plcc-ll1; }

@test "plcc-ll1 --help exits 0" {
    run plcc-ll1 --help
    [ "$status" -eq 0 ]
}

@test "plcc-ll1 produces schema-valid output" {
    run bash -c "plcc-ll1 < '${SPEC_JSON}'"
    [ "$status" -eq 0 ]
    echo "$output" | check-jsonschema --schemafile "${SCHEMA}" -
}

@test "plcc-ll1 reads from stdin via pipe" {
    run bash -c "cat '${SPEC_JSON}' | plcc-ll1"
    [ "$status" -eq 0 ]
    echo "$output" | check-jsonschema --schemafile "${SCHEMA}" -
}

# --- arbno section of the output schema ---------------------------------
#
# trivial.plcc has no repetition rules, so the two schema checks above
# validate an empty "arbno": {}. These use a grammar that populates it.

@test "plcc-ll1 output for a repetition grammar is schema-valid" {
    run bash -c "plcc-ll1 < '${ARBNO_SPEC_JSON}'"
    [ "$status" -eq 0 ]
    echo "$output" | check-jsonschema --schemafile "${SCHEMA}" -
}

# The schema must *constrain* the arbno section, not merely tolerate it.
# Deleting any required key from real plcc-ll1 output has to be rejected.
# Before issue 179 the schema did not mention arbno at all, so every one
# of these mutants validated clean.
@test "ll1 schema rejects arbno output missing any required key" {
    LL1_JSON="${BATS_TEST_TMPDIR}/ll1.json"
    plcc-ll1 < "${ARBNO_SPEC_JSON}" > "${LL1_JSON}"

    for path in \
        "arbno" \
        "arbno.Decls.rhs" \
        "arbno.Decls.separator" \
        "arbno.Decls.lookahead" \
        "arbno.Decls.rhs.0.symbol" \
        "arbno.Decls.rhs.0.field" \
        "arbno.Decls.rhs.0.is_terminal"
    do
        mutant="${BATS_TEST_TMPDIR}/without-${path}.json"
        DROP_PATH="${path}" python3 -c '
import json, os, sys

doc = json.load(sys.stdin)
segments = os.environ["DROP_PATH"].split(".")
node = doc
for segment in segments[:-1]:
    node = node[int(segment)] if isinstance(node, list) else node[segment]
last = segments[-1]
del node[int(last) if isinstance(node, list) else last]
json.dump(doc, sys.stdout)
' < "${LL1_JSON}" > "${mutant}"

        run check-jsonschema --schemafile "${SCHEMA}" "${mutant}"
        if [ "$status" -eq 0 ]; then
            echo "schema accepted output missing ${path}" >&2
            return 1
        fi
    done
}

# --- conflicts section of the output schema ------------------------------
#
# Every other fixture in this repository is LL(1)-clean, so every other
# schema check here validates an empty "conflicts": [] — which `required`
# never reaches. ll1-conflicts.plcc is the only grammar that populates it,
# with one entry of each conflict_type.

@test "plcc-ll1 output for a conflicting grammar is schema-valid" {
    run bash -c "plcc-ll1 < '${CONFLICT_SPEC_JSON}'"
    [ "$status" -eq 0 ]
    echo "$output" | check-jsonschema --schemafile "${SCHEMA}" -
}

@test "plcc-ll1 accepts -v without error" {
    run bash -c "plcc-ll1 -v < '${SPEC_JSON}'"
    [ "$status" -eq 0 ]
}

@test "plcc-ll1 accepts --verbose-format without error" {
    run bash -c "plcc-ll1 -v --verbose-format=json < '${SPEC_JSON}'"
    [ "$status" -eq 0 ]
}

@test "plcc-ll1: is_ll1 is true for empty spec" {
    run bash -c "echo '{\"lexical\":{\"ruleList\":[]},\"syntax\":{\"rules\":[]},\"semantics\":[]}' | plcc-ll1"
    [ "$status" -eq 0 ]
    echo "$output" | grep -q '"is_ll1"'
}

@test "plcc-ll1 emits start_symbol for trivial grammar" {
    run bash -c "plcc-ll1 < '${SPEC_JSON}'"
    [ "$status" -eq 0 ]
    echo "$output" | python3 -c "import json,sys; r=json.load(sys.stdin); assert r['start_symbol'] == 'Program', r['start_symbol']"
}

@test "plcc-ll1 populates first_sets for trivial grammar" {
    run bash -c "plcc-ll1 < '${SPEC_JSON}'"
    [ "$status" -eq 0 ]
    echo "$output" | python3 -c "import json,sys; r=json.load(sys.stdin); assert r['first_sets']['Program'] == ['NUM'], r['first_sets']"
}
