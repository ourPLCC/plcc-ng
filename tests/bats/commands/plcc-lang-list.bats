#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

@test "plcc-lang-list is on PATH" { command -v plcc-lang-list; }

@test "plcc-lang-list exits 0" {
    run plcc-lang-list
    [ "$status" -eq 0 ]
}

