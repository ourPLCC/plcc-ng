#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

@test "plcc-haskell-emit is on PATH" { command -v plcc-haskell-emit; }

@test "plcc-haskell-emit --help exits 0" {
    run plcc-haskell-emit --help
    [ "$status" -eq 0 ]
}

@test "plcc-haskell-emit: no args exits nonzero" {
    run plcc-haskell-emit
    [ "$status" -ne 0 ]
}

@test "plcc-haskell-emit: emits interpreter.cabal given minimal model" {
    local out
    out=$(mktemp -d)
    echo '{"start":"prog","classes":[{"name":"Prog","extends":null,"abstract":false,"rule_name":"prog","fields":[]}],"semantic_sections":[]}' \
        | plcc-haskell-emit --output="$out"
    [ -f "$out/interpreter.cabal" ]
    rm -rf "$out"
}

@test "plcc-haskell-emit: emits Token.hs given minimal model" {
    local out
    out=$(mktemp -d)
    echo '{"start":"prog","classes":[{"name":"Prog","extends":null,"abstract":false,"rule_name":"prog","fields":[]}],"semantic_sections":[]}' \
        | plcc-haskell-emit --output="$out"
    [ -f "$out/Token.hs" ]
    rm -rf "$out"
}
