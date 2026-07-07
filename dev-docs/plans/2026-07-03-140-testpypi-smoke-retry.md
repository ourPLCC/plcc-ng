# TestPyPI Smoke-Test Retry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stop the release pipeline's TestPyPI smoke test from flaking when the TestPyPI simple index lags the upload, by retrying the pip install for up to ~5 minutes.

**Architecture:** A single workflow step in `.github/workflows/release.yml` changes: the `pip install` from TestPyPI is wrapped in a fixed-backoff retry loop (20 attempts, 15s apart) with `--no-cache-dir`. Everything else in the step — venv creation before the loop, `plcc-make` smoke assertions after it — is unchanged. Spec: `dev-docs/specs/2026-07-03-140-testpypi-smoke-retry-design.md`.

**Tech Stack:** GitHub Actions workflow YAML, bash. No Python code changes; no unit-test tier covers workflows, so verification is a YAML parse plus `bash -n` on the extracted script (no `actionlint`/`shellcheck` in this container).

## Global Constraints

- Retry budget: exactly 20 attempts, 15s sleep between failures (~5 min worst case).
- Failure message on exhaustion: `FAIL: plcc-ng==<version> not installable from TestPyPI after 20 attempts`.
- Per-attempt log line: `TestPyPI index not ready (attempt N/20); retrying in 15s`.
- The functional assertions (`plcc-make`, `spec.json` check) run once, outside the loop.
- Work happens in the worktree at `.claude/worktrees/140-release-smoke-test-testpypi-propagation`; run all commands from that directory.
- Never assign issue numbers by hand; close issues only via `bin/issues/close.bash`.

---

### Task 1: Wrap the TestPyPI install in a retry loop

**Files:**
- Modify: `.github/workflows/release.yml:67-81` (the "Smoke test TestPyPI install" step)

**Interfaces:**
- Consumes: `needs.semantic-release.outputs.version` (already wired into the step).
- Produces: nothing consumed by later tasks; the step's pass/fail gates `create-release` as before.

- [ ] **Step 1: Edit the workflow step**

Replace the current step body:

```yaml
      - name: Smoke test TestPyPI install
        run: |
          VERSION="${{ needs.semantic-release.outputs.version }}"
          python -m venv /tmp/smoke-venv
          /tmp/smoke-venv/bin/pip install \
            --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            "plcc-ng==${VERSION}"
```

with:

```yaml
      - name: Smoke test TestPyPI install
        run: |
          VERSION="${{ needs.semantic-release.outputs.version }}"
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
```

The rest of the step (from `SPEC="$(pwd)/tests/fixtures/trivial.plcc"` through `echo "TestPyPI smoke test passed"`) is unchanged. Note the `if` guards the pip install, so the job's default `bash -e` does not abort on a failed attempt.

- [ ] **Step 2: Verify the YAML still parses**

Run:

```bash
python -c "import yaml; yaml.safe_load(open('.github/workflows/release.yml')); print('yaml ok')"
```

Expected: `yaml ok`

- [ ] **Step 3: Syntax-check the step's script with bash -n**

The run block contains a `${{ ... }}` template that is not valid bash, so substitute it before checking. Run:

```bash
SMOKE_SCRIPT=$(mktemp)
python - <<'EOF' > "${SMOKE_SCRIPT}"
import re, yaml
wf = yaml.safe_load(open('.github/workflows/release.yml'))
step = next(s for s in wf['jobs']['publish']['steps']
            if s.get('name') == 'Smoke test TestPyPI install')
print(re.sub(r'\$\{\{.*?\}\}', '0.0.0', step['run']))
EOF
bash -n "${SMOKE_SCRIPT}" && echo "bash syntax ok"
rm -f "${SMOKE_SCRIPT}"
```

Expected: `bash syntax ok`

- [ ] **Step 4: Dry-run the retry loop's control flow locally**

Exercise the loop with a command that fails a fixed number of times, to confirm it retries, logs, and breaks correctly. Run:

```bash
bash -e -o pipefail <<'EOF'
VERSION="9.9.9"
fails_left=3
fake_pip() { if [ "${fails_left}" -gt 0 ]; then fails_left=$((fails_left - 1)); return 1; fi; return 0; }
for attempt in $(seq 1 20); do
  if fake_pip; then
    echo "installed on attempt ${attempt}"
    break
  fi
  if [ "${attempt}" -eq 20 ]; then
    echo "FAIL: plcc-ng==${VERSION} not installable from TestPyPI after 20 attempts"
    exit 1
  fi
  echo "TestPyPI index not ready (attempt ${attempt}/20); retrying in 15s"
done
EOF
```

(The `sleep 15` is omitted from this harness so it runs instantly; the loop structure is otherwise identical.)

Expected output:

```
TestPyPI index not ready (attempt 1/20); retrying in 15s
TestPyPI index not ready (attempt 2/20); retrying in 15s
TestPyPI index not ready (attempt 3/20); retrying in 15s
installed on attempt 4
```

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/release.yml
git commit -m "fix(release): retry TestPyPI smoke-test install until index propagates

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: Close issue 140

**Files:**
- Modify (via script): `dev-docs/issues/140-release-smoke-test-testpypi-propagation.md` → `dev-docs/issues/done/`, `dev-docs/roadmap.md`

**Interfaces:**
- Consumes: nothing from Task 1 (but must be the final commit of the branch).
- Produces: nothing.

- [ ] **Step 1: Run the close script**

```bash
bin/issues/close.bash 140
```

Expected: the script moves the issue file to `dev-docs/issues/done/`, updates `dev-docs/roadmap.md`, and stages both (it stages; you commit).

- [ ] **Step 2: Verify issue-tracker consistency**

```bash
bin/issues/check.bash
```

Expected: exits 0 with no errors.

- [ ] **Step 3: Commit**

```bash
git commit -m "chore(issues): close 140 - release smoke test races TestPyPI propagation

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```
