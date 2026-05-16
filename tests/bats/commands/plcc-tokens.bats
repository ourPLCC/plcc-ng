#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    SCHEMA="$(git rev-parse --show-toplevel)/src/plcc/schemas/token.schema.json"
    SPEC_JSON="$(mktemp)"
    plcc-spec "${FIXTURES}/trivial.plcc" > "${SPEC_JSON}"
}

teardown() {
    rm -f "${SPEC_JSON}"
}

@test "plcc-tokens is on PATH" {
    command -v plcc-tokens
}

@test "plcc-tokens --help exits 0" {
    run plcc-tokens --help
    [ "$status" -eq 0 ]
}

@test "plcc-tokens outputs token JSONL for trivial input" {
    run bash -c "echo '42' | plcc-tokens '${SPEC_JSON}'"
    [ "$status" -eq 0 ]
    # Validate the first (and only) token record against the schema
    echo "$output" | head -1 | check-jsonschema --schemafile "${SCHEMA}" -
}

@test "plcc-tokens token record has kind=token" {
    result=$(echo '42' | plcc-tokens "${SPEC_JSON}" | head -1)
    echo "$result" | python3 -c "import json,sys; r=json.load(sys.stdin); assert r['kind']=='token', f\"expected kind=token, got {r['kind']}\""
}

@test "plcc-tokens lex error exits 0 and writes error record to stdout" {
    run --separate-stderr bash -c "echo 'xyz' | plcc-tokens '${SPEC_JSON}'"
    [ "$status" -eq 0 ]
    [ -z "$stderr" ]
    # every output line except the $ sentinel is a valid JSON record with kind=error
    while IFS= read -r line || [ -n "$line" ]; do
        [ -z "$line" ] && continue
        echo "$line" | python3 -c "import json,sys; r=json.load(sys.stdin); exit(0) if r.get('name')=='\$' else None; assert r['kind']=='error', f\"expected kind=error, got {r['kind']}\""
    done <<< "$output"
}

@test "plcc-tokens with no SOURCE args labels tokens with file=-" {
    result=$(echo '42' | plcc-tokens "${SPEC_JSON}" | head -1)
    file_val=$(echo "$result" | python3 -c "import json,sys; r=json.load(sys.stdin); print(r['source']['file'])")
    [ "$file_val" = "-" ]
}

@test "plcc-tokens with SOURCE file arg labels tokens with that filename" {
    tmp=$(mktemp)
    echo "42" > "$tmp"
    result=$(plcc-tokens "${SPEC_JSON}" "$tmp" | head -1)
    file_val=$(echo "$result" | python3 -c "import json,sys; r=json.load(sys.stdin); print(r['source']['file'])")
    [ "$file_val" = "$tmp" ]
    rm -f "$tmp"
}

@test "plcc-tokens default token record omits regex and source_line" {
    result=$(echo '42' | plcc-tokens "${SPEC_JSON}" | head -1)
    echo "$result" | python3 -c "
import json, sys
r = json.load(sys.stdin)
assert 'regex' not in r, f'regex present in lean record: {r}'
assert 'source_line' not in r, f'source_line present in lean record: {r}'
"
}

@test "plcc-tokens --trace token record includes regex and source_line" {
    result=$(echo '42' | plcc-tokens --trace "${SPEC_JSON}" | head -1)
    echo "$result" | python3 -c "
import json, sys
r = json.load(sys.stdin)
assert 'regex' in r, f'regex missing from enriched record: {r}'
assert 'source_line' in r, f'source_line missing from enriched record: {r}'
assert r['source_line'] == '42', f'wrong source_line: {r}'
"
}

@test "plcc-tokens --trace emits kind=skip records" {
    VERBOSITY_SPEC_JSON="$(mktemp)"
    plcc-spec "${FIXTURES}/scan-verbosity.plcc" > "${VERBOSITY_SPEC_JSON}"
    result=$(echo '42 99' | plcc-tokens --trace "${VERBOSITY_SPEC_JSON}")
    kinds=$(echo "$result" | python3 -c "
import json, sys
for line in sys.stdin:
    line = line.strip()
    if line:
        r = json.loads(line)
        print(r['kind'])
")
    [[ "$kinds" == *"skip"* ]]
    rm -f "${VERBOSITY_SPEC_JSON}"
}

@test "plcc-tokens --trace skip records validate against schema" {
    VERBOSITY_SPEC_JSON="$(mktemp)"
    plcc-spec "${FIXTURES}/scan-verbosity.plcc" > "${VERBOSITY_SPEC_JSON}"
    echo '42 99' | plcc-tokens --trace "${VERBOSITY_SPEC_JSON}" | while IFS= read -r line || [ -n "$line" ]; do
        [ -z "$line" ] && continue
        echo "$line" | check-jsonschema --schemafile "${SCHEMA}" -
    done
    rm -f "${VERBOSITY_SPEC_JSON}"
}

@test "plcc-tokens -v emits per-file scanning event on stderr" {
    tmp=$(mktemp)
    echo "42" > "$tmp"
    run --separate-stderr plcc-tokens -v --verbose-format=text "${SPEC_JSON}" "$tmp"
    [[ "$stderr" == *"scanning $tmp"* ]]
    rm -f "$tmp"
}
