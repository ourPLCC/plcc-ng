#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    WORK_DIR="$(mktemp -d)"
    cd "${WORK_DIR}"
}

teardown() {
    rm -rf "${WORK_DIR}"
}

# ── Basic interface ────────────────────────────────────────────────────────────

@test "plcc-make is on PATH" { command -v plcc-make; }

@test "plcc-make --help exits 0" {
    run plcc-make --help
    [ "$status" -eq 0 ]
}

@test "plcc-make with no grammar.plcc exits nonzero" {
    run --separate-stderr plcc-make
    [ "$status" -ne 0 ]
    [[ "$stderr" == *"grammar file not found"* ]]
}

@test "plcc-make --grammar-file with missing file exits nonzero" {
    run --separate-stderr plcc-make --grammar-file=no-such-file.plcc
    [ "$status" -ne 0 ]
    [[ "$stderr" == *"grammar file not found"* ]]
}

@test "plcc-make defaults to grammar.plcc in CWD" {
    cp "${FIXTURES}/trivial.plcc" grammar.plcc
    run plcc-make --through=scan
    [ "$status" -eq 0 ]
    [ -f build/spec.json ]
}

@test "plcc-make --grammar-file uses specified path" {
    run plcc-make --through=scan "--grammar-file=${FIXTURES}/trivial.plcc"
    [ "$status" -eq 0 ]
    [ -f build/spec.json ]
}

@test "plcc-make accepts -v" {
    cp "${FIXTURES}/trivial.plcc" grammar.plcc
    run plcc-make -v --through=scan
    [ "$status" -eq 0 ]
}

# ── Build artifacts ────────────────────────────────────────────────────────────

@test "plcc-make full build produces spec.json ll1.json model.json" {
    cp "${FIXTURES}/trivial-python.plcc" grammar.plcc
    run plcc-make
    [ "$status" -eq 0 ]
    [ -f build/spec.json ]
    [ -f build/ll1.json ]
    [ -f build/model.json ]
}

@test "plcc-make full build writes .spec-hash sentinel" {
    cp "${FIXTURES}/trivial-python.plcc" grammar.plcc
    run plcc-make
    [ "$status" -eq 0 ]
    [ -f "build/.spec-hash" ]
}

@test "plcc-make --through=scan creates spec.json but not ll1.json" {
    cp "${FIXTURES}/trivial.plcc" grammar.plcc
    run plcc-make --through=scan
    [ "$status" -eq 0 ]
    [ -f build/spec.json ]
    [ ! -f build/ll1.json ]
}

@test "plcc-make --through=parse creates spec.json and ll1.json but not model.json" {
    cp "${FIXTURES}/trivial.plcc" grammar.plcc
    run plcc-make --through=parse
    [ "$status" -eq 0 ]
    [ -f build/spec.json ]
    [ -f build/ll1.json ]
    [ ! -f build/model.json ]
}

# ── Staleness: fast path ───────────────────────────────────────────────────────

@test "plcc-make does not rebuild when grammar is unchanged" {
    cp "${FIXTURES}/trivial.plcc" grammar.plcc
    plcc-make --through=parse
    rm build/ll1.json          # manually remove artifact
    plcc-make --through=parse  # grammar unchanged → fast path
    [ ! -f build/ll1.json ]    # not rebuilt confirms fast path taken
}

@test "plcc-make --through=all fast-paths when all-level sentinel present" {
    cp "${FIXTURES}/trivial-python.plcc" grammar.plcc
    plcc-make
    rm build/ll1.json          # manually corrupt build/
    plcc-make                  # grammar unchanged, sentinel at 'all' level → fast path
    [ ! -f build/ll1.json ]    # not rebuilt confirms fast path taken
}

# ── Staleness: slow path ───────────────────────────────────────────────────────

@test "plcc-make rebuilds when grammar changes" {
    cp "${FIXTURES}/trivial.plcc" grammar.plcc
    plcc-make --through=scan
    first_spec=$(cat build/spec.json)

    cp "${FIXTURES}/trivial-python.plcc" grammar.plcc  # different grammar
    plcc-make --through=scan
    second_spec=$(cat build/spec.json)

    [ "$first_spec" != "$second_spec" ]
}

@test "plcc-make --through=scan then --through=all completes full build" {
    cp "${FIXTURES}/trivial.plcc" grammar.plcc
    plcc-make --through=scan
    [ ! -f build/ll1.json ]

    plcc-make  # grammar unchanged but level insufficient (scan < all)
    [ -f build/ll1.json ]
}

@test "plcc-make --through=all then --through=scan fast-paths" {
    cp "${FIXTURES}/trivial.plcc" grammar.plcc
    plcc-make
    rm build/ll1.json
    plcc-make --through=scan  # all >= scan → fast path
    [ ! -f build/ll1.json ]   # not rebuilt confirms fast path
}

# ── Staleness: failure handling ────────────────────────────────────────────────

@test "plcc-make deletes sentinel when plcc-spec fails" {
    cp "${FIXTURES}/trivial-python.plcc" grammar.plcc
    plcc-make
    [ -f "build/.spec-hash" ]

    printf 'token BAD @@@\n' > grammar.plcc  # syntax error
    run plcc-make
    [ "$status" -ne 0 ]
    [ ! -f "build/.spec-hash" ]
}

@test "plcc-make re-fails on repeated call with broken grammar" {
    printf 'token BAD @@@\n' > grammar.plcc
    run plcc-make
    [ "$status" -ne 0 ]
    run plcc-make
    [ "$status" -ne 0 ]
}

@test "plcc-make rebuilds after broken grammar is fixed" {
    cp "${FIXTURES}/trivial.plcc" grammar.plcc
    plcc-make --through=scan

    printf 'token BAD @@@\n' > grammar.plcc
    run plcc-make --through=scan
    [ "$status" -ne 0 ]

    cp "${FIXTURES}/trivial-python.plcc" grammar.plcc
    run plcc-make --through=scan
    [ "$status" -eq 0 ]
    [ -f build/spec.json ]
}

# ── Partial grammars ───────────────────────────────────────────────────────────

@test "plcc-make --through=scan succeeds with lexical-only grammar" {
    cp "${FIXTURES}/lexical-only.plcc" grammar.plcc
    run plcc-make --through=scan
    [ "$status" -eq 0 ]
    [ -f build/spec.json ]
}

@test "plcc-make --through=parse succeeds with lexical-only grammar" {
    cp "${FIXTURES}/lexical-only.plcc" grammar.plcc
    run plcc-make --through=parse
    [ "$status" -eq 0 ]
    [ -f build/ll1.json ]
}

@test "plcc-make full build succeeds with lexical+syntactic grammar and no semantics" {
    cp "${FIXTURES}/trivial.plcc" grammar.plcc
    run plcc-make
    [ "$status" -eq 0 ]
    [ -f build/ll1.json ]
    [ -f build/model.json ]
}

# ── Sticky grammar ─────────────────────────────────────────────────────────────

@test "plcc-make writes build/.grammar after successful build" {
    cp "${FIXTURES}/trivial.plcc" grammar.plcc
    plcc-make --through=scan
    [ -f "build/.grammar" ]
    [[ "$(cat build/.grammar)" == "grammar.plcc" ]]
}

@test "plcc-make with --grammar-file writes that path to build/.grammar" {
    run plcc-make --through=scan "--grammar-file=${FIXTURES}/trivial.plcc"
    [ "$status" -eq 0 ]
    [[ "$(cat build/.grammar)" == "${FIXTURES}/trivial.plcc" ]]
}

@test "plcc-make without --grammar-file uses stored grammar" {
    # Build from an absolute path grammar, then invoke plcc-make with no args
    # → should use stored path, not look for grammar.plcc in CWD
    run plcc-make --through=scan "--grammar-file=${FIXTURES}/trivial.plcc"
    [ "$status" -eq 0 ]
    [[ "$(cat build/.grammar)" == "${FIXTURES}/trivial.plcc" ]]
    # Now run with no --grammar-file from a dir with no grammar.plcc
    run --separate-stderr plcc-make --through=scan
    [ "$status" -eq 0 ]
    [[ "$(cat build/.grammar)" == "${FIXTURES}/trivial.plcc" ]]
}

@test "plcc-make with --grammar-file differing from stored wipes build" {
    cp "${FIXTURES}/trivial.plcc" grammar.plcc
    plcc-make --through=scan
    cp "${FIXTURES}/trivial-python.plcc" other.plcc
    plcc-make --through=scan --grammar-file=other.plcc
    # build/ was wiped and rebuilt from other.plcc
    [[ "$(cat build/.grammar)" == "other.plcc" ]]
}

@test "plcc-make stored grammar missing gives error to stderr with hint" {
    mkdir -p build
    echo "ghost.plcc" > build/.grammar
    run --separate-stderr plcc-make
    [ "$status" -ne 0 ]
    [[ "$stderr" == *"grammar file not found"* ]]
    [[ "$stderr" == *"ghost.plcc"* ]]
    [[ "$stderr" == *"--grammar-file"* ]]
}

@test "plcc-make no build/.grammar no --grammar-file falls back to grammar.plcc" {
    run --separate-stderr plcc-make
    [ "$status" -ne 0 ]
    [[ "$stderr" == *"grammar.plcc"* ]]
}
