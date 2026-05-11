#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
}

@test "plcc-scan is on PATH" { command -v plcc-scan; }

@test "plcc-scan --help exits 0" {
    run plcc-scan --help
    [ "$status" -eq 0 ]
}

@test "plcc-scan tokenizes input" {
    run bash -c "echo '42' | plcc-scan '${FIXTURES}/trivial.plcc'"
    [ "$status" -eq 0 ]
    [[ "$output" == *"NUM"* ]]
    [[ "$output" == *"42"* ]]
}

@test "plcc-scan reads from source file" {
    run plcc-scan "${FIXTURES}/trivial.plcc" "${FIXTURES}/trivial_input.txt"
    [ "$status" -eq 0 ]
    [[ "$output" == *"NUM"* ]]
}

@test "plcc-scan accepts -v" {
    run bash -c "echo '42' | plcc-scan -v '${FIXTURES}/trivial.plcc'"
    [ "$status" -eq 0 ]
}

@test "plcc-scan accepts -vv (bundled short flag)" {
    run bash -c "echo '42' | plcc-scan -vv --verbose-format=json '${FIXTURES}/trivial.plcc'"
    [ "$status" -eq 0 ]
}

@test "plcc-scan includes file:line:col in token output" {
    run bash -c "echo '42' | plcc-scan '${FIXTURES}/trivial.plcc'"
    [ "$status" -eq 0 ]
    [[ "$output" =~ ^-:1:1\ NUM\ \'42\'$ ]]
}

@test "plcc-scan exits 0 on lex error in source" {
    run --separate-stderr bash -c "echo 'abc' | plcc-scan '${FIXTURES}/trivial.plcc'"
    [ "$status" -eq 0 ]
    [[ "$output" == *"error"* ]]
}

@test "plcc-scan brief usage mentions --help" {
    run --separate-stderr plcc-scan
    [[ "$stderr" == *"--help"* ]]
}

@test "plcc-scan accepts '-' as stdin" {
    run bash -c "echo '42' | plcc-scan '${FIXTURES}/trivial.plcc' -"
    [ "$status" -eq 0 ]
    [[ "$output" == *"NUM"* ]]
    [[ "$output" == *"42"* ]]
}

@test "plcc-scan '-' interleaved with file reads both" {
    run bash -c "echo '99' | plcc-scan '${FIXTURES}/trivial.plcc' '${FIXTURES}/trivial_input.txt' -"
    [ "$status" -eq 0 ]
    [[ "$output" == *"42"* ]]
    [[ "$output" == *"99"* ]]
}

@test "plcc-scan prints tokens before and after a lex error" {
    run --separate-stderr bash -c "printf '42 @ 99\n' | plcc-scan '${FIXTURES}/trivial.plcc'"
    [ "$status" -eq 0 ]
    [[ "$output" == *"42"* ]]
    [[ "$output" == *"99"* ]]
    [[ "$output" == *"error"* ]]
}

@test "plcc-scan outputs tokens for multi-line input" {
    run bash -c "printf '42\n99\n' | plcc-scan '${FIXTURES}/trivial.plcc'"
    [ "$status" -eq 0 ]
    [[ "$output" == *"42"* ]]
    [[ "$output" == *"99"* ]]
}

@test "plcc-scan includes source filename in token output for named file" {
    run plcc-scan "${FIXTURES}/trivial.plcc" "${FIXTURES}/trivial_input.txt"
    [ "$status" -eq 0 ]
    [[ "$output" == *"trivial_input.txt"* ]]
}

@test "plcc-scan exits nonzero when source file does not exist" {
    run --separate-stderr plcc-scan "${FIXTURES}/trivial.plcc" "/nonexistent/no-such-file.txt"
    [ "$status" -ne 0 ]
}

@test "plcc-scan --show-skips adds SKIPPED lines" {
    run bash -c "echo '42 99' | plcc-scan --show-skips '${FIXTURES}/scan-verbosity.plcc'"
    [ "$status" -eq 0 ]
    [[ "$output" == *"SKIPPED"* ]]
}

@test "plcc-scan --show-skips format is file:line:col NAME 'lexeme' SKIPPED" {
    run bash -c "echo '42 99' | plcc-scan --show-skips '${FIXTURES}/scan-verbosity.plcc'"
    [ "$status" -eq 0 ]
    [[ "$output" =~ -:1:[0-9]+\ WS\ \'\ \'\ SKIPPED ]]
}

@test "plcc-scan --show-line shows source line and caret cursor" {
    run bash -c "echo '42' | plcc-scan --show-line '${FIXTURES}/trivial.plcc'"
    [ "$status" -eq 0 ]
    [[ "$output" == *"42"* ]]
    [[ "$output" == *"^"* ]]
}

@test "plcc-scan --show-line cursor is at correct column" {
    # '42' starts at column 1: cursor should have zero leading spaces
    run bash -c "echo '42' | plcc-scan --show-line '${FIXTURES}/trivial.plcc'"
    [ "$status" -eq 0 ]
    # Second line of output should be exactly "^" (no leading spaces)
    second_line=$(echo "$output" | sed -n '2p')
    [ "$second_line" = "^" ]
}

@test "plcc-scan --show-attempts produces indented attempt lines" {
    run bash -c "echo '42' | plcc-scan --show-attempts '${FIXTURES}/scan-verbosity.plcc'"
    [ "$status" -eq 0 ]
    [[ "$output" == *"chars"* ]]
}

@test "plcc-scan --show-attempts has exactly one starred winner" {
    run bash -c "echo '42' | plcc-scan --show-attempts '${FIXTURES}/scan-verbosity.plcc'"
    [ "$status" -eq 0 ]
    star_count=$(echo "$output" | grep -c '^\s*\*')
    [ "$star_count" -eq 1 ]
}

@test "plcc-scan --show-regex includes regex in token output" {
    run bash -c "echo '42' | plcc-scan --show-regex '${FIXTURES}/trivial.plcc'"
    [ "$status" -eq 0 ]
    [[ "$output" =~ ^-:1:1\ NUM\ \'\\\d\+\'\ \'42\'$ ]]
}

@test "plcc-scan --trace produces source line, cursor, attempts, and token line" {
    run bash -c "echo '42' | plcc-scan --trace '${FIXTURES}/scan-verbosity.plcc'"
    [ "$status" -eq 0 ]
    [[ "$output" == *"42"* ]]
    [[ "$output" == *"^"* ]]
    [[ "$output" == *"chars"* ]]
    [[ "$output" =~ \'\\\d\+ ]]
}

@test "plcc-scan -v emits started and finished events on stderr" {
    run --separate-stderr bash -c "echo '42' | plcc-scan -v '${FIXTURES}/trivial.plcc'"
    [ "$status" -eq 0 ]
    [[ "$stderr" == *"started"* ]]
    [[ "$stderr" == *"finished"* ]]
}

@test "plcc-scan -v hint is absent from stderr" {
    run --separate-stderr bash -c "echo '42' | plcc-scan -v '${FIXTURES}/trivial.plcc'"
    [ "$status" -eq 0 ]
    [[ "$stderr" != *"press ^D"* ]]
}

@test "plcc-scan -vv produces no more stderr output than -v" {
    run --separate-stderr bash -c "echo '42' | plcc-scan -v '${FIXTURES}/trivial.plcc'"
    v1_stderr="$stderr"
    run --separate-stderr bash -c "echo '42' | plcc-scan -vv '${FIXTURES}/trivial.plcc'"
    v2_stderr="$stderr"
    # -vv should not add scan-specific lines beyond -v
    v1_lines=$(echo "$v1_stderr" | wc -l)
    v2_lines=$(echo "$v2_stderr" | wc -l)
    [ "$v2_lines" -le "$v1_lines" ]
}

@test "plcc-scan -vvv produces no more stderr output than -v" {
    run --separate-stderr bash -c "echo '42' | plcc-scan -v '${FIXTURES}/trivial.plcc'"
    v1_stderr="$stderr"
    run --separate-stderr bash -c "echo '42' | plcc-scan -vvv '${FIXTURES}/trivial.plcc'"
    v3_stderr="$stderr"
    v1_lines=$(echo "$v1_stderr" | wc -l)
    v3_lines=$(echo "$v3_stderr" | wc -l)
    [ "$v3_lines" -le "$v1_lines" ]
}

@test "plcc-scan TTY hint absent when stdin is not a TTY" {
    run bash -c "echo '42' | plcc-scan '${FIXTURES}/trivial.plcc'"
    [ "$status" -eq 0 ]
    [[ "$output" != *"press ^D"* ]]
}
