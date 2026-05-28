#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

@test "plcc-parse: lex error reports plcc-tokens, not plcc-trees cascade" {
    tmp=$(mktemp -d)
    cat > "$tmp/trivial.plcc" <<'EOF'
token NUM '\d+'
%
<program> ::= NUM
%
% diagram PlantUML
EOF
    run --separate-stderr bash -c "echo 'abc' | plcc-parse --grammar-file='$tmp/trivial.plcc'"
    [ "$status" -ne 0 ]
    # User-facing error: plcc-tokens is responsible, rendered via reformat_child_events
    [[ "$output" == *"plcc-tokens"* ]]
    [[ "$output" == *"error"* ]]
    # plcc-trees's cascading error must NOT appear
    ! [[ "$output" == *"plcc-trees:"*"error"* ]]
    rm -rf "$tmp"
}
