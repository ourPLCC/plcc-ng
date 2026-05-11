#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    WORK_DIR="$(mktemp -d)"
    cd "${WORK_DIR}"
    cp "${FIXTURES}/trivial.plcc" grammar.plcc
}

teardown() {
    rm -rf "${WORK_DIR}"
}

@test "plcc-scan is on PATH" { command -v plcc-scan; }

@test "plcc-scan --help exits 0" {
    run plcc-scan --help
    [ "$status" -eq 0 ]
}

@test "plcc-scan tokenizes input" {
    run bash -c "echo '42' | plcc-scan"
    [ "$status" -eq 0 ]
    [[ "$output" == *"NUM"* ]]
    [[ "$output" == *"42"* ]]
}

@test "plcc-scan reads from source file" {
    run plcc-scan "${FIXTURES}/trivial_input.txt"
    [ "$status" -eq 0 ]
    [[ "$output" == *"NUM"* ]]
}

@test "plcc-scan accepts -v" {
    run bash -c "echo '42' | plcc-scan -v"
    [ "$status" -eq 0 ]
}

@test "plcc-scan accepts -vv (bundled short flag)" {
    run bash -c "echo '42' | plcc-scan -vv --verbose-format=json"
    [ "$status" -eq 0 ]
}

@test "plcc-scan includes file:line:col in token output" {
    run bash -c "echo '42' | plcc-scan"
    [ "$status" -eq 0 ]
    [[ "$output" =~ ^-:1:1\ NUM\ \'42\'$ ]]
}

@test "plcc-scan exits 0 on lex error in source" {
    run --separate-stderr bash -c "echo 'abc' | plcc-scan"
    [ "$status" -eq 0 ]
    [[ "$output" == *"error"* ]]
}

@test "plcc-scan brief usage mentions --help" {
    run --separate-stderr bash -c "cd '${WORK_DIR}' && rm grammar.plcc && plcc-scan"
    [[ "$stderr" == *"--help"* ]]
}

@test "plcc-scan accepts '-' as stdin" {
    run bash -c "echo '42' | plcc-scan -"
    [ "$status" -eq 0 ]
    [[ "$output" == *"NUM"* ]]
    [[ "$output" == *"42"* ]]
}

@test "plcc-scan '-' interleaved with file reads both" {
    run bash -c "echo '99' | plcc-scan '${FIXTURES}/trivial_input.txt' -"
    [ "$status" -eq 0 ]
    [[ "$output" == *"42"* ]]
    [[ "$output" == *"99"* ]]
}

@test "plcc-scan prints tokens before and after a lex error" {
    run --separate-stderr bash -c "printf '42 @ 99\n' | plcc-scan"
    [ "$status" -eq 0 ]
    [[ "$output" == *"42"* ]]
    [[ "$output" == *"99"* ]]
    [[ "$output" == *"error"* ]]
}

@test "plcc-scan outputs tokens for multi-line input" {
    run bash -c "printf '42\n99\n' | plcc-scan"
    [ "$status" -eq 0 ]
    [[ "$output" == *"42"* ]]
    [[ "$output" == *"99"* ]]
}

@test "plcc-scan includes source filename in token output for named file" {
    run plcc-scan "${FIXTURES}/trivial_input.txt"
    [ "$status" -eq 0 ]
    [[ "$output" == *"trivial_input.txt"* ]]
}

@test "plcc-scan exits nonzero when source file does not exist" {
    run --separate-stderr plcc-scan "/nonexistent/no-such-file.txt"
    [ "$status" -ne 0 ]
}

@test "plcc-scan --grammar-file uses specified grammar" {
    run bash -c "echo '42' | plcc-scan --grammar-file='${FIXTURES}/trivial.plcc'"
    [ "$status" -eq 0 ]
    [[ "$output" == *"NUM"* ]]
}

@test "plcc-scan --show-skips adds SKIPPED lines" {
    cp "${FIXTURES}/scan-verbosity.plcc" grammar.plcc
    run bash -c "echo '42 99' | plcc-scan --show-skips"
    [ "$status" -eq 0 ]
    [[ "$output" == *"SKIPPED"* ]]
}

@test "plcc-scan --show-skips format is file:line:col NAME 'lexeme' SKIPPED" {
    cp "${FIXTURES}/scan-verbosity.plcc" grammar.plcc
    run bash -c "echo '42 99' | plcc-scan --show-skips"
    [ "$status" -eq 0 ]
    [[ "$output" =~ -:1:[0-9]+\ WS\ \'\ \'\ SKIPPED ]]
}

@test "plcc-scan --show-line shows source line and caret cursor" {
    run bash -c "echo '42' | plcc-scan --show-line"
    [ "$status" -eq 0 ]
    [[ "$output" == *"42"* ]]
    [[ "$output" == *"^"* ]]
}

@test "plcc-scan --show-line cursor is at correct column" {
    run bash -c "echo '42' | plcc-scan --show-line"
    [ "$status" -eq 0 ]
    second_line=$(echo "$output" | sed -n '2p')
    [ "$second_line" = "^" ]
}

@test "plcc-scan --show-attempts produces indented attempt lines" {
    cp "${FIXTURES}/scan-verbosity.plcc" grammar.plcc
    run bash -c "echo '42' | plcc-scan --show-attempts"
    [ "$status" -eq 0 ]
    [[ "$output" == *"chars"* ]]
}

@test "plcc-scan --show-attempts has exactly one starred winner" {
    cp "${FIXTURES}/scan-verbosity.plcc" grammar.plcc
    run bash -c "echo '42' | plcc-scan --show-attempts"
    [ "$status" -eq 0 ]
    star_count=$(echo "$output" | grep -c '^\s*\*')
    [ "$star_count" -eq 1 ]
}

@test "plcc-scan --show-regex includes regex in token output" {
    run bash -c "echo '42' | plcc-scan --show-regex"
    [ "$status" -eq 0 ]
    [[ "$output" =~ ^-:1:1\ NUM\ \'\\\d\+\'\ \'42\'$ ]]
}

@test "plcc-scan --trace produces source line, cursor, attempts, and token line" {
    cp "${FIXTURES}/scan-verbosity.plcc" grammar.plcc
    run bash -c "echo '42' | plcc-scan --trace"
    [ "$status" -eq 0 ]
    [[ "$output" == *"42"* ]]
    [[ "$output" == *"^"* ]]
    [[ "$output" == *"chars"* ]]
    [[ "$output" =~ \'\\\d\+ ]]
}

@test "plcc-scan -v emits started and finished events on stderr" {
    run --separate-stderr bash -c "echo '42' | plcc-scan -v"
    [ "$status" -eq 0 ]
    [[ "$stderr" == *"started"* ]]
    [[ "$stderr" == *"finished"* ]]
}

@test "plcc-scan -v hint is absent from stderr" {
    run --separate-stderr bash -c "echo '42' | plcc-scan -v"
    [ "$status" -eq 0 ]
    [[ "$stderr" != *"press ^D"* ]]
}

@test "plcc-scan -vv produces no more plcc-scan stderr lines than -v" {
    run --separate-stderr bash -c "echo '42' | plcc-scan -v"
    v1_lines=$(echo "$stderr" | grep '^plcc-scan:' | wc -l)
    run --separate-stderr bash -c "echo '42' | plcc-scan -vv"
    v2_lines=$(echo "$stderr" | grep '^plcc-scan:' | wc -l)
    [ "$v2_lines" -le "$v1_lines" ]
}

@test "plcc-scan -vvv produces no more plcc-scan stderr lines than -v" {
    run --separate-stderr bash -c "echo '42' | plcc-scan -v"
    v1_lines=$(echo "$stderr" | grep '^plcc-scan:' | wc -l)
    run --separate-stderr bash -c "echo '42' | plcc-scan -vvv"
    v3_lines=$(echo "$stderr" | grep '^plcc-scan:' | wc -l)
    [ "$v3_lines" -le "$v1_lines" ]
}

@test "plcc-scan TTY hint absent when stdin is not a TTY" {
    run bash -c "echo '42' | plcc-scan"
    [ "$status" -eq 0 ]
    [[ "$output" != *"press ^D"* ]]
}

@test "plcc-scan triggers rebuild when grammar changes" {
    echo '42' | plcc-scan > /dev/null  # prime build
    cp "${FIXTURES}/trivial-python.plcc" grammar.plcc  # change grammar
    run bash -c "echo '42' | plcc-scan"
    [ "$status" -eq 0 ]
    [[ "$output" == *"NUM"* ]]
}

@test "plcc-scan exits nonzero when grammar has syntax error" {
    printf 'token BAD @@@\n' > grammar.plcc
    run --separate-stderr bash -c "echo '42' | plcc-scan"
    [ "$status" -ne 0 ]
}

@test "plcc-scan works with lexical-only grammar" {
    cp "${FIXTURES}/lexical-only.plcc" grammar.plcc
    run bash -c "echo '42' | plcc-scan"
    [ "$status" -eq 0 ]
    [[ "$output" == *"NUM"* ]]
}
