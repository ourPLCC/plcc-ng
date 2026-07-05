# Release Smoke Test Emitter Coverage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the release smoke test (and its local analog) to exercise all four emitters — Python, Java, Haskell, JavaScript — so a published wheel missing emitter runtime package data fails the smoke test instead of shipping broken.

**Architecture:** One new shared script, `bin/test/smoke.bash`, assumes the `plcc-*` entry points are already on `PATH` and runs emit-only checks (`plcc-lang-emit --target=<lang>` per language, asserting generated + runtime files exist). Two call sites consume it: the "Smoke test TestPyPI install" step in `.github/workflows/release.yml`, and `bin/test/packaging.bash` after its wheel install.

**Tech Stack:** Bash, bats-style assertion messages (`FAIL: ...`), GitHub Actions.

**Spec:** [dev-docs/specs/2026-07-05-release-smoke-test-emitter-coverage-design.md](../specs/2026-07-05-release-smoke-test-emitter-coverage-design.md)

## Global Constraints

- The script must NOT source `bin/test/_cache.bash` or use `run_cached`: its result depends on which package is installed on `PATH`, not on git state, so caching would be incorrect.
- Emitters are invoked through the `plcc-lang-emit --target=<lang>` dispatcher, never `plcc-<lang>-emit` directly, so language discovery in the installed package is exercised.
- The four languages (python, java, javascript, haskell) are hard-coded — this is a v1 release gate (issue 112), not a plugin enumeration.
- Fixture: `tests/fixtures/trivial.plcc` for everything. Do not add new fixtures.
- Follow `bin/test/` house style: `set -euo pipefail`, header echo, `SCRIPT_DIR`/`PROJECT_ROOT` derivation, `FAIL: ...` + `exit 1` on assertion failure.
- Never add `[skip ci]` to any commit message.

---

### Task 1: Create `bin/test/smoke.bash`

**Files:**
- Create: `bin/test/smoke.bash` (mode 755)

**Interfaces:**
- Consumes: `plcc-make`, `plcc-spec`, `plcc-model`, `plcc-lang-emit` entry points on `PATH`; `tests/fixtures/trivial.plcc`.
- Produces: an executable script that exits 0 printing `smoke: all checks passed` when the installed package is healthy, exits 1 with `FAIL: ...` otherwise. Tasks 2 and 3 call it as `bin/test/smoke.bash` (repo-relative) with entry points already on `PATH`.

- [ ] **Step 1: Write the script**

Create `bin/test/smoke.bash` with exactly this content:

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "bin/test/smoke.bash"
echo "-------------------"

# Smoke test an installed plcc-ng. Assumes the plcc-* entry points are
# already on PATH (installed from a wheel or from TestPyPI).
#
# Deliberately not cached via _cache.bash: the result depends on which
# package is installed on PATH, not on git state.

SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( cd "${SCRIPT_DIR}/../.." &> /dev/null && pwd )"

SPEC="${PROJECT_ROOT}/tests/fixtures/trivial.plcc"

WORK_DIR="$(mktemp -d)"
EMIT_DIR="$(mktemp -d)"
trap 'rm -rf "${WORK_DIR}" "${EMIT_DIR}"' EXIT

(
    cd "${WORK_DIR}"
    plcc-make --spec="${SPEC}"
    test -f plcc-ng/spec.json  || { echo "FAIL: plcc-ng/spec.json missing"; exit 1; }
    test -f plcc-ng/model.json || { echo "FAIL: plcc-ng/model.json missing"; exit 1; }
)
echo "OK: plcc-make produces spec.json and model.json"

MODEL_JSON="${WORK_DIR}/model.json"
plcc-spec "${SPEC}" | plcc-model > "${MODEL_JSON}"

# check_emitted <lang> <expected-glob>...
# Emits for <lang> into a fresh directory, then asserts each expected
# glob matches at least one file there.
check_emitted() {
    local lang="$1"; shift
    local out="${EMIT_DIR}/${lang}"
    mkdir -p "${out}"
    plcc-lang-emit --target="${lang}" --output="${out}" < "${MODEL_JSON}"
    local pattern
    for pattern in "$@"; do
        compgen -G "${out}/${pattern}" > /dev/null \
            || { echo "FAIL: ${lang}: ${pattern} missing"; exit 1; }
    done
    echo "OK: ${lang} emit produces expected files"
}

check_emitted python     Program.py   runtime/base.py
check_emitted java       Program.java runtime/Token.java "runtime/org.json-*.jar"
check_emitted javascript Program.js   runtime/base.js
check_emitted haskell    Program.hs   Token.hs interpreter.cabal

echo "smoke: all checks passed"
```

Notes for the implementer:
- `plcc-lang-emit` reads the model JSON from stdin (same contract the e2e bats tests use).
- The model is generated once and reused for all four languages; each emit still goes through the dispatcher.
- `compgen -G` is the glob-match assertion; it is needed because the Java runtime jar is version-pinned in its filename (`org.json-20250107.jar` today) — assert `runtime/org.json-*.jar`, never the pinned name.
- The `exit 1` inside `check_emitted`'s `{ ...; }` group exits the whole script (it is not a subshell), which is intended.

- [ ] **Step 2: Make it executable**

```bash
chmod +x bin/test/smoke.bash
```

- [ ] **Step 3: Run it against the dev venv (expect pass)**

The dev environment installs the entry points into the project venv, so `pdm run` puts them on `PATH`:

```bash
pdm run bin/test/smoke.bash
```

Expected output ends with:

```
OK: plcc-make produces spec.json and model.json
OK: python emit produces expected files
OK: java emit produces expected files
OK: javascript emit produces expected files
OK: haskell emit produces expected files
smoke: all checks passed
```

and exit status 0 (`echo $?` → `0`).

- [ ] **Step 4: Verify the failure path fires**

Run once with a target that cannot exist, by temporarily exercising the assertion helper — simplest reliable probe: check the script fails fast when entry points are absent.

```bash
env PATH=/usr/bin:/bin bash bin/test/smoke.bash; echo "exit=$?"
```

Expected: a `plcc-make: command not found` error and `exit=127` (non-zero). This confirms `set -euo pipefail` aborts the script when the installed package is broken rather than printing `smoke: all checks passed`.

- [ ] **Step 5: Commit**

```bash
git add bin/test/smoke.bash
git commit -m "test(packaging): add smoke script covering all four emitters

Emit-only checks for python, java, javascript, and haskell against an
installed plcc-ng, asserting generated files and runtime package data
exist. Shared by the release workflow and bin/test/packaging.bash.

Refs #137

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: Call `smoke.bash` from `bin/test/packaging.bash`

**Files:**
- Modify: `bin/test/packaging.bash:55-64` (the `WORK_DIR` block)

**Interfaces:**
- Consumes: `bin/test/smoke.bash` from Task 1 (invoked as `"${SCRIPT_DIR}/smoke.bash"`; entry points already on `PATH` from line 41's `export PATH="${VENV}/bin:${PATH}"`).
- Produces: `bin/test/packaging.bash` whose wheel-install test now covers all four emitters.

- [ ] **Step 1: Replace the trivial `plcc-make` block with a `smoke.bash` call**

In `bin/test/packaging.bash`, replace this block (currently lines 55–64):

```bash
    # Run end-to-end in the installed venv
    WORK_DIR="$(mktemp -d)"
    trap 'rm -rf "${VENV}" "${WORK_DIR}"' EXIT
    (
        cd "${WORK_DIR}"
        cp "${PROJECT_ROOT}/tests/fixtures/trivial.plcc" spec.plcc
        plcc-make
        test -f plcc-ng/spec.json   || { echo "FAIL: plcc-ng/spec.json missing"; exit 1; }
        test -f plcc-ng/model.json  || { echo "FAIL: plcc-ng/model.json missing"; exit 1; }
    )
    DIAGRAM_DIR="$(mktemp -d)"
    trap 'rm -rf "${VENV}" "${WORK_DIR}" "${DIAGRAM_DIR}"' EXIT
```

with:

```bash
    # Smoke test the installed package (plcc-make + all four emitters)
    "${SCRIPT_DIR}/smoke.bash"

    DIAGRAM_DIR="$(mktemp -d)"
    trap 'rm -rf "${VENV}" "${DIAGRAM_DIR}"' EXIT
```

Note the trap rewrite: `WORK_DIR` no longer exists in this script, so the second trap must drop it (`smoke.bash` cleans up its own temp dirs via its own trap). The diagram-emit check below the block stays unchanged.

- [ ] **Step 2: Run the packaging test fresh (expect pass)**

```bash
PLCC_NO_TEST_CACHE=1 bin/test/packaging.bash
```

This builds nothing itself but installs `dist/*.whl`; if `dist/` is empty or stale, first run `bin/build/package.bash`. Takes on the order of a minute.

Expected output includes, in order: the `OK: <cmd>` entry-point lines, `OK: plcc-lang-list reports python and java`, the `smoke.bash` header and its five `OK:` lines ending `smoke: all checks passed`, then `packaging: all checks passed`. Exit 0.

- [ ] **Step 3: Commit**

```bash
git add bin/test/packaging.bash
git commit -m "test(packaging): run emitter smoke checks in packaging test

Replaces the inline trivial plcc-make block with bin/test/smoke.bash so
the local wheel-install test covers the same emitter package-data
checks as the release workflow.

Refs #137

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: Call `smoke.bash` from the release workflow

**Files:**
- Modify: `.github/workflows/release.yml:85-110` (the "Smoke test TestPyPI install" step)

**Interfaces:**
- Consumes: `bin/test/smoke.bash` from Task 1 (the step runs from the repo checkout root, with the TestPyPI-installed venv prepended to `PATH`).
- Produces: a release workflow whose smoke test fails if any emitter's package data is missing from the published package.

- [ ] **Step 1: Replace the inline `plcc-make` lines**

In `.github/workflows/release.yml`, the step currently reads:

```yaml
      - name: Smoke test TestPyPI install
        run: |
          VERSION="${RELEASE_TAG#v}"
          python -m venv /tmp/smoke-venv
          for attempt in $(seq 1 20); do
            if /tmp/smoke-venv/bin/pip install \
                --no-cache-dir \
                --index-url https://test.pypi.org/simple/ \
                --extra-index-url https://pypi.org/simple/ \
                "plcc-ng==${VERSION}"; then
              break
            fi
            if [ "${attempt}" -eq 20 ]; then
              echo "FAIL: plcc-ng==${VERSION} not installable from TestPyPI after 20 attempts"
              exit 1
            fi
            echo "TestPyPI index not ready (attempt ${attempt}/20); retrying in 15s"
            sleep 15
          done
          SPEC="$(pwd)/tests/fixtures/trivial.plcc"
          WORK=$(mktemp -d)
          cd "${WORK}"
          export PATH="/tmp/smoke-venv/bin:${PATH}"
          plcc-make --spec="${SPEC}"
          test -f plcc-ng/spec.json || { echo "FAIL: plcc-ng/spec.json missing"; exit 1; }
          echo "TestPyPI smoke test passed"
```

Keep the `VERSION`/venv/retry-loop lines unchanged, and replace everything from `SPEC="$(pwd)/..."` to the final `echo` with:

```yaml
          export PATH="/tmp/smoke-venv/bin:${PATH}"
          bin/test/smoke.bash
          echo "TestPyPI smoke test passed"
```

(No `cd` — the step must stay in the checkout root so `bin/test/smoke.bash` resolves; the script manages its own temp dirs.)

- [ ] **Step 2: Lint the workflow**

```bash
command -v actionlint && actionlint .github/workflows/release.yml || python -c "import yaml, pathlib; yaml.safe_load(pathlib.Path('.github/workflows/release.yml').read_text()); print('yaml ok')"
```

Expected: `actionlint` reports nothing (exit 0), or if actionlint is not installed, `yaml ok`.

- [ ] **Step 3: Rehearse the step's shell locally**

The workflow shell after the retry loop is exactly `export PATH=...; bin/test/smoke.bash` from the repo root, which Task 1 Step 3 already exercised (`pdm run` ≈ venv on `PATH`). Re-run to confirm nothing in Tasks 2–3 broke it:

```bash
pdm run bin/test/smoke.bash
```

Expected: ends with `smoke: all checks passed`, exit 0.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/release.yml
git commit -m "ci(release): exercise all four emitters in TestPyPI smoke test

The smoke step now runs bin/test/smoke.bash, which emits for python,
java, javascript, and haskell and asserts runtime package data landed
in the published package, instead of only checking spec.json exists.

Refs #137

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 4: Run the test suite and close issue 137

**Files:**
- Modify (via script): `dev-docs/issues/137-release-smoke-test-emitter-coverage.md` → `dev-docs/issues/done/`, `dev-docs/roadmap.md`

**Interfaces:**
- Consumes: `bin/issues/close.bash` (stages the move + roadmap edit; you commit), `bin/issues/check.bash` (runs automatically at the end of close.bash).
- Produces: the branch's final commit; issue 137 closed per repo convention.

- [ ] **Step 1: Run the functional test tiers (expect pass)**

```bash
bin/test/units.bash && bin/test/commands.bash
```

Expected: pytest ends `1175 passed, 1 skipped` (the pre-existing timing-sensitive JavaScript skip; count may drift slightly with main), bats commands all pass. Nothing in this branch touches `src/`, so failures here mean environment trouble, not this change — investigate before proceeding, do not skip.

- [ ] **Step 2: Close the issue**

```bash
bin/issues/close.bash 137
```

Expected output: `closed: dev-docs/issues/done/137-release-smoke-test-emitter-coverage.md` and a reminder to review the roadmap. Review `git diff --cached dev-docs/roadmap.md` — the script does not auto-edit milestone rationale prose; if any paragraph still describes the smoke-test gap as open, fix it and `git add` it.

- [ ] **Step 3: Commit (final commit of the branch)**

```bash
git commit -m "docs(issues): close issue 137 (release smoke test emitter coverage), update roadmap

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

- [ ] **Step 4: Verify issue consistency**

```bash
bin/issues/check.bash
```

Expected: exit 0, no complaints.
