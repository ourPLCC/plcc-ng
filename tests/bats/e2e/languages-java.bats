#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    if ! command -v javac &>/dev/null; then skip "JDK not available"; fi
    if [ -z "${LANGUAGES_REPO_PATH:-}" ]; then skip "LANGUAGES_REPO_PATH not set"; fi
    CORPUS="$(git rev-parse --show-toplevel)/tests/fixtures/languages-corpus.txt"
}

# Helper: run one grammar test case
# Usage: run_test_case <grammar_dir> <test_dir>
run_test_case() {
    local grammar_dir="$1"
    local test_dir="$2"
    local input_file expected_file build_dir ll1_json

    input_file=$(ls "${test_dir}"/*.input 2>/dev/null | head -1)
    expected_file=$(ls "${test_dir}"/*.expected 2>/dev/null | head -1)

    [ -n "${input_file}" ] || return 0
    [ -n "${expected_file}" ] || return 0

    build_dir="$(mktemp -d)"
    ll1_json="$(mktemp)"
    trap "rm -rf '${build_dir}' '${ll1_json}'" RETURN

    plcc-spec "${grammar_dir}" | plcc-ll1 > "${ll1_json}"
    plcc-spec "${grammar_dir}" | plcc-model | plcc-java-emit --output="${build_dir}"
    plcc-java-build --output="${build_dir}"

    actual=$(
        cat "${input_file}" \
        | plcc-tokens "${grammar_dir}" \
        | plcc-tree --ll1="${ll1_json}" \
        | plcc-java-run --output="${build_dir}" \
        | grep -v '^{"kind":'
    )
    expected=$(cat "${expected_file}")

    [ "${actual}" = "${expected}" ]
}

@test "corpus grammars pass" {
    while IFS= read -r line || [ -n "$line" ]; do
        # skip blank lines and comments
        [[ "$line" =~ ^[[:space:]]*# ]] && continue
        [[ -z "${line// }" ]] && continue

        grammar_dir="${LANGUAGES_REPO_PATH}/${line}"
        [ -d "${grammar_dir}" ] || { echo "SKIP: ${grammar_dir} not found"; continue; }

        for test_dir in "${grammar_dir%/grammar}/tests"/*/; do
            [ -d "${test_dir}" ] || continue
            run_test_case "${grammar_dir}" "${test_dir}"
        done
    done < "${CORPUS}"
}
