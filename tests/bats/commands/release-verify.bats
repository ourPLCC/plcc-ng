#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

PROJECT_ROOT="$(git rev-parse --show-toplevel)"
VERIFY="${PROJECT_ROOT}/bin/release/verify.bash"

# The script's observational checks are plain curl calls. A stub curl on
# PATH serves canned responses per URL (controlled by STUB_FAIL_*,
# ${STUB_DIR}/simple-index.html, and ${STUB_DIR}/versions.json) and logs
# every requested URL, making the checks hermetic and the request order
# observable. The install path (check 4) is deliberately untested here;
# it is exercised for real on a release (issue 112).

setup() {
    STUB_DIR="$(mktemp -d)"
    export STUB_DIR
    cat > "${STUB_DIR}/curl" <<'EOF'
#!/usr/bin/env bash
url=""
for arg in "$@"; do
    case "${arg}" in
        http*) url="${arg}" ;;
    esac
done
echo "${url}" >> "${STUB_DIR}/requests.log"
case "${url}" in
    *pypi.org/pypi/*)
        echo '{}'
        ;;
    *pypi.org/simple/plcc-ng/*)
        [[ -n "${STUB_FAIL_PYPI:-}" ]] && exit 22
        cat "${STUB_DIR}/simple-index.html"
        ;;
    *api.github.com/repos/*/releases/tags/*)
        [[ -n "${STUB_FAIL_GITHUB:-}" ]] && exit 22
        echo '{}'
        ;;
    *versions.json*)
        [[ -n "${STUB_FAIL_DOCS:-}" ]] && exit 22
        cat "${STUB_DIR}/versions.json"
        ;;
    *)
        exit 22
        ;;
esac
exit 0
EOF
    chmod +x "${STUB_DIR}/curl"
    export PATH="${STUB_DIR}:${PATH}"
    export PLCC_VERIFY_RETRY_DELAY=0
    echo '[{"version": "0.65", "title": "0.65", "aliases": ["latest"]}]' \
        > "${STUB_DIR}/versions.json"
    cat > "${STUB_DIR}/simple-index.html" <<'EOF'
<a href="https://files.pythonhosted.org/x/plcc_ng-0.65.0-py3-none-any.whl">plcc_ng-0.65.0-py3-none-any.whl</a>
<a href="https://files.pythonhosted.org/x/plcc_ng-0.65.0.tar.gz">plcc_ng-0.65.0.tar.gz</a>
EOF
}

teardown() {
    rm -rf "${STUB_DIR}"
}

# A stub python3 that reports ${STUB_PYTHON_VERSION} for --version and
# delegates everything else (the docs-check JSON parsing) to the real
# interpreter. Lets tests simulate an ambient python3 too old for the
# package's requires-python (issue 143).
create_python3_stub() {
    local real_python3
    real_python3="$(command -v python3)"
    cat > "${STUB_DIR}/python3" <<EOF
#!/usr/bin/env bash
if [[ "\${1:-}" == "--version" ]]; then
    echo "Python \${STUB_PYTHON_VERSION}"
    exit 0
fi
if [[ "\${1:-}" == "-m" && "\${2:-}" == "venv" ]]; then
    echo "stub python3: refusing to create a venv in tests" >&2
    exit 1
fi
exec "${real_python3}" "\$@"
EOF
    chmod +x "${STUB_DIR}/python3"
}

@test "verify: fails with usage when called without arguments" {
    run bash "${VERIFY}"
    [ "$status" -ne 0 ]
    [[ "$output" == *"Usage:"* ]]
}

@test "verify: fails with usage on extra arguments" {
    run bash "${VERIFY}" v0.65.0 v0.65.1
    [ "$status" -ne 0 ]
    [[ "$output" == *"Usage:"* ]]
}

@test "verify: rejects a tag without the leading v" {
    run bash "${VERIFY}" 0.65.0
    [ "$status" -ne 0 ]
    [[ "$output" == *"Usage:"* ]]
}

@test "verify: rejects a tag that is not vX.Y.Z shaped" {
    run bash "${VERIFY}" v0.65
    [ "$status" -ne 0 ]
    [[ "$output" == *"Usage:"* ]]
}

@test "verify: --no-install passes when all checks pass" {
    run bash "${VERIFY}" --no-install v0.65.0
    [ "$status" -eq 0 ]
    [[ "$output" == *"OK: PyPI has plcc-ng 0.65.0"* ]]
    [[ "$output" == *"OK: GitHub Release v0.65.0 exists"* ]]
    [[ "$output" == *"OK: docs 0.65 deployed with latest alias"* ]]
    [[ "$output" == *"verify: all checks passed for v0.65.0"* ]]
}

@test "verify: PyPI check polls the simple index pip installs from, not the JSON API" {
    run bash "${VERIFY}" --no-install v0.65.0
    [ "$status" -eq 0 ]
    grep -q 'pypi.org/simple/plcc-ng/' "${STUB_DIR}/requests.log"
    run ! grep -q 'pypi.org/pypi/' "${STUB_DIR}/requests.log"
}

@test "verify: fails when the simple index lags the JSON API (no wheel for the version yet)" {
    cat > "${STUB_DIR}/simple-index.html" <<'EOF'
<a href="https://files.pythonhosted.org/x/plcc_ng-0.64.0-py3-none-any.whl">plcc_ng-0.64.0-py3-none-any.whl</a>
<a href="https://files.pythonhosted.org/x/plcc_ng-0.64.0.tar.gz">plcc_ng-0.64.0.tar.gz</a>
EOF
    run bash "${VERIFY}" --no-install v0.65.0
    [ "$status" -ne 0 ]
    [[ "$output" == *"FAIL: plcc-ng 0.65.0 not on PyPI"* ]]
}

@test "verify: fails when PyPI lacks the version" {
    export STUB_FAIL_PYPI=1
    run bash "${VERIFY}" --no-install v0.65.0
    [ "$status" -ne 0 ]
    [[ "$output" == *"FAIL: plcc-ng 0.65.0 not on PyPI"* ]]
}

@test "verify: PyPI failure stops before GitHub and docs are checked" {
    export STUB_FAIL_PYPI=1
    run bash "${VERIFY}" --no-install v0.65.0
    [ "$status" -ne 0 ]
    grep -q 'pypi.org/simple/plcc-ng/' "${STUB_DIR}/requests.log"
    run ! grep -q 'api.github.com' "${STUB_DIR}/requests.log"
    run ! grep -q 'versions.json' "${STUB_DIR}/requests.log"
}

@test "verify: retries the PyPI check five times" {
    export STUB_FAIL_PYPI=1
    run bash "${VERIFY}" --no-install v0.65.0
    [ "$status" -ne 0 ]
    [ "$(grep -c 'pypi.org/simple/plcc-ng/' "${STUB_DIR}/requests.log")" -eq 5 ]
}

@test "verify: fails when the GitHub Release is missing" {
    export STUB_FAIL_GITHUB=1
    run bash "${VERIFY}" --no-install v0.65.0
    [ "$status" -ne 0 ]
    [[ "$output" == *"FAIL: GitHub Release v0.65.0 missing"* ]]
}

@test "verify: fails when the docs version is not deployed" {
    echo '[{"version": "0.64", "title": "0.64", "aliases": ["latest"]}]' \
        > "${STUB_DIR}/versions.json"
    run bash "${VERIFY}" --no-install v0.65.0
    [ "$status" -ne 0 ]
    [[ "$output" == *"FAIL: docs version 0.65 not deployed"* ]]
}

@test "verify: fails when the latest alias is on a different version" {
    echo '[{"version": "0.65", "title": "0.65", "aliases": []}, {"version": "0.64", "title": "0.64", "aliases": ["latest"]}]' \
        > "${STUB_DIR}/versions.json"
    run bash "${VERIFY}" --no-install v0.65.0
    [ "$status" -ne 0 ]
    [[ "$output" == *"FAIL: docs latest alias is not on 0.65"* ]]
}

@test "verify: fails fast when no python3 satisfies requires-python" {
    create_python3_stub
    export STUB_PYTHON_VERSION=3.9.2
    # Restrict the interpreter search to the stub so the project venv's
    # python cannot rescue the run (which would then really install).
    export PLCC_VERIFY_PYTHON="${STUB_DIR}/python3"
    run bash "${VERIFY}" v0.65.0
    [ "$status" -ne 0 ]
    [[ "$output" == *"FAIL: no python3 satisfying requires-python"* ]]
    [[ "$output" == *"(3.9.2)"* ]]
    # Fails before any network check or install retry.
    [[ "$output" != *"OK: PyPI"* ]]
    [[ "$output" != *"PyPI install not ready"* ]]
}

@test "verify: --no-install skips the python3 preflight" {
    create_python3_stub
    export STUB_PYTHON_VERSION=3.9.2
    run bash "${VERIFY}" --no-install v0.65.0
    [ "$status" -eq 0 ]
    [[ "$output" == *"verify: all checks passed for v0.65.0 (install skipped)"* ]]
}

@test "verify: fails when versions.json cannot be fetched" {
    export STUB_FAIL_DOCS=1
    run bash "${VERIFY}" --no-install v0.65.0
    [ "$status" -ne 0 ]
    [[ "$output" == *"FAIL: could not fetch docs versions.json"* ]]
}
