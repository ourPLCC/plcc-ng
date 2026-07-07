# 134 — PyPI Publish Failure Recovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give `release.yml` a `workflow_dispatch` `tag` input that republishes an existing tag through the full publish path, and remove the dispatch dry-run behavior that stops at TestPyPI.

**Architecture:** Single workflow, one optional input. `tag` empty (or push trigger) → today's behavior: semantic-release decides, full publish. `tag` set → semantic-release job is skipped and publish/create-release run against the existing tag, with every step idempotent (`skip-existing` on both indexes, GitHub Release created only if missing).

**Tech Stack:** GitHub Actions YAML, bash, python-semantic-release, pypa/gh-action-pypi-publish, `gh` CLI (in CI only — the local `gh` is a fake; do not run `gh` locally).

**Spec:** `docs/superpowers/specs/2026-07-04-134-pypi-publish-failure-recovery-design.md`

## Global Constraints

- Conventional commits, scopes matching the git log (`feat(release): …`, `docs(release): …`, `docs(issues): …`).
- Never add `[skip ci]` to commit messages — CI already path-skips doc-only changes.
- End every commit message with `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`.
- Do not write ad-hoc shell scripts; use existing `bin/` scripts (`bin/issues/close.bash`, `bin/issues/check.bash`).
- Workflow logic cannot be unit-tested locally. Local verification is YAML parsing only; the live end-to-end test happens post-merge (see final section) and is the maintainer's step, not part of this plan's tasks.
- Work happens on the current worktree branch `worktree-134-release-pypi-publish-failure-recovery`; do not push or create PRs (the user handles GitHub).

---

### Task 1: Rework release.yml — `tag` input, republish plumbing, no dry-run

**Files:**
- Modify: `.github/workflows/release.yml` (whole file — final content below)

**Interfaces:**
- Produces: workflow behavior consumed by Task 2's documentation — dispatch input named exactly `tag`, expecting an existing tag like `v0.64.4`; empty input = normal full release.

**What changes and why (review against this list):**
1. `workflow_dispatch` gains optional input `tag` (default `""`).
2. `semantic-release` job gains `if: inputs.tag == ''` (on push events `inputs.tag` evaluates to empty string, so push runs are unaffected).
3. `publish` job: condition becomes `${{ !cancelled() && (inputs.tag != '' || needs.semantic-release.outputs.released == 'true') }}`. `!cancelled()` lets it run after a *skipped* semantic-release; if semantic-release *fails* in normal mode the second clause is false, so publish still skips.
4. `publish` job gains job-level env `RELEASE_TAG` — the input tag if set, else `v{version}` from semantic-release. Checkout `ref` uses it; the smoke test derives `VERSION="${RELEASE_TAG#v}"` from it (job env vars are visible in `run` steps). A nonexistent input tag makes checkout fail with "couldn't find remote ref" — checkout is the input validation.
5. The real-PyPI step's `if: github.event_name != 'workflow_dispatch'` (the dry-run behavior) is deleted.
6. `create-release` job: condition becomes `${{ !cancelled() && needs.publish.result == 'success' }}`; same `RELEASE_TAG` env; checkout ref uses it; `gh release create` becomes idempotent (view first, create only if missing); `--target` is dropped (the tag always exists by this point, so `--target` is ignored in normal runs and misleading in republish runs where `github.sha` is main's HEAD).
7. Everything else (app-token steps, TestPyPI step, smoke-test retry loop, permissions) is unchanged.

- [ ] **Step 1: Replace `.github/workflows/release.yml` with this exact content**

```yaml
name: Release

on:
  push:
    branches: [main]
  workflow_dispatch:
    inputs:
      tag:
        description: "Existing tag to republish (e.g. v0.64.4). Leave empty for a normal release."
        required: false
        default: ""

permissions:
  contents: write
  id-token: write

jobs:
  semantic-release:
    name: Semantic release
    if: inputs.tag == ''
    runs-on: ubuntu-latest
    outputs:
      released: ${{ steps.release.outputs.released }}
      version: ${{ steps.release.outputs.version }}
    steps:
      - uses: actions/create-github-app-token@v1
        id: app-token
        with:
          app-id: ${{ secrets.RELEASE_APP_ID }}
          private-key: ${{ secrets.RELEASE_APP_PRIVATE_KEY }}
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          token: ${{ steps.app-token.outputs.token }}
      - uses: actions/setup-python@v5
        with:
          python-version: '3.14'
      - name: Python Semantic Release
        id: release
        uses: python-semantic-release/python-semantic-release@v9
        with:
          github_token: ${{ steps.app-token.outputs.token }}
          push: "true"
          changelog: "true"
          vcs_release: "false"

  publish:
    name: Publish to PyPI
    needs: semantic-release
    if: ${{ !cancelled() && (inputs.tag != '' || needs.semantic-release.outputs.released == 'true') }}
    runs-on: ubuntu-latest
    environment: pypi
    env:
      RELEASE_TAG: ${{ inputs.tag != '' && inputs.tag || format('v{0}', needs.semantic-release.outputs.version) }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          ref: ${{ env.RELEASE_TAG }}
      - uses: actions/setup-python@v5
        with:
          python-version: '3.14'
      - name: Install PDM
        run: pip install pdm
      - name: Build wheel
        run: bin/build/package.bash

      - name: Publish to TestPyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          repository-url: https://test.pypi.org/legacy/
          skip-existing: true
          attestations: false

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

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          skip-existing: true

  create-release:
    name: Create GitHub Release
    needs: [semantic-release, publish]
    if: ${{ !cancelled() && needs.publish.result == 'success' }}
    runs-on: ubuntu-latest
    env:
      RELEASE_TAG: ${{ inputs.tag != '' && inputs.tag || format('v{0}', needs.semantic-release.outputs.version) }}
    steps:
      - uses: actions/create-github-app-token@v1
        id: app-token
        with:
          app-id: ${{ secrets.RELEASE_APP_ID }}
          private-key: ${{ secrets.RELEASE_APP_PRIVATE_KEY }}
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          ref: ${{ env.RELEASE_TAG }}
          token: ${{ steps.app-token.outputs.token }}
      - name: Create GitHub Release
        env:
          GH_TOKEN: ${{ steps.app-token.outputs.token }}
        run: |
          if gh release view "${RELEASE_TAG}" >/dev/null 2>&1; then
            echo "Release ${RELEASE_TAG} already exists; nothing to do"
          else
            gh release create "${RELEASE_TAG}" \
              --title "${RELEASE_TAG}" \
              --generate-notes
          fi
```

- [ ] **Step 2: Verify the YAML parses**

Run:

```bash
pdm run python -c 'import yaml; yaml.safe_load(open(".github/workflows/release.yml")); print("YAML OK")'
```

Expected output ends with: `YAML OK`

(There is no actionlint in this environment; YAML parsing is the only local check.)

- [ ] **Step 3: Diff against the intent list**

Run: `git diff .github/workflows/release.yml`

Check the diff shows exactly the 7 numbered changes in "What changes and why" above — in particular that the TestPyPI step, smoke-test retry loop, and app-token steps are untouched, and that the deleted lines include `if: github.event_name != 'workflow_dispatch'` and `--target "${{ github.sha }}"`.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/release.yml
git commit -m "feat(release): add republish-tag dispatch input, drop TestPyPI-only dry run

A failed publish after tagging left no recovery path: reruns found no
releasable commits, and the old dispatch mode stopped at TestPyPI while
still tagging and creating a GitHub Release. Dispatching with the new
tag input skips semantic-release and reruns the full idempotent publish
path for an existing tag; dispatching without it is now a normal full
release.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: Document manual triggers and publish recovery in the release SOP

**Files:**
- Modify: `dev-docs/release-sop.md` (currently a 3-line stub — final content below)

**Interfaces:**
- Consumes: the dispatch input named `tag` from Task 1, format `v{X.Y.Z}` (e.g. `v0.64.4`).

**Scope guard:** The full SOP is issue 130's job (still open). This task adds only the manual-triggers section and reworks the stub line to say so. Do not write version-bump/CHANGELOG/docs-deploy procedure here.

- [ ] **Step 1: Replace `dev-docs/release-sop.md` with this exact content**

```markdown
# Release SOP

*The full SOP (release procedure, verification checklist) is tracked in
issue 130. The section below documents the release workflow's manual
triggers.*

## Manual triggers and publish recovery

The release workflow (`.github/workflows/release.yml`) runs automatically
on every push to `main`. It can also be run by hand: **Actions → Release
→ Run workflow**, always from `main` (the selected branch decides which
version of the workflow file runs). The `tag` input selects one of two
modes.

### Normal release (leave `tag` empty)

Identical to a push-triggered release: semantic-release computes the next
version from unreleased commits; if there is something to release it
tags, updates the CHANGELOG, builds, publishes to TestPyPI, smoke-tests
the TestPyPI install, publishes to PyPI, and creates the GitHub Release.
If nothing is releasable, the run ends after the semantic-release job.

**This is a real release.** Manual runs used to stop at TestPyPI; that
behavior is gone. Do not dispatch with an empty `tag` to "test" the
workflow — use the republish mode below with an already-published tag
instead.

### Republish an existing tag (set `tag`, e.g. `v0.64.4`)

Use this when a release run failed *after* tagging: the tag exists, but
the version is missing from PyPI and/or GitHub Releases, and re-running
the workflow does nothing because semantic-release finds no new
releasable commits. This works regardless of why or when the original
run failed — including workflow bugs fixed since (the run uses the
workflow file from `main`, not from the failed run).

1. Confirm the state: the tag exists in the repo, but
   <https://pypi.org/project/plcc-ng/> lacks the version and/or the
   GitHub Release is missing.
2. **Actions → Release → Run workflow** from `main`, set `tag` to the
   existing tag (with the leading `v`).
3. The run skips semantic-release, builds the wheel from the tag, and
   reruns the whole publish path. Every step is idempotent —
   `skip-existing` on TestPyPI and PyPI, GitHub Release created only if
   missing — so there is no need to know how far the failed run got.
   A nonexistent tag fails immediately at checkout.
4. Verify: the version appears on <https://pypi.org/project/plcc-ng/>
   and the GitHub Release exists.

### Safe end-to-end test of the republish path

Dispatch with the **latest already-published** tag. Every step no-ops
gracefully and the run goes green without publishing anything. Do this
after any change to the publish jobs.
```

- [ ] **Step 2: Verify the referenced input still matches the workflow**

Run:

```bash
grep -n 'tag:' .github/workflows/release.yml | head -2
grep -c 'Run workflow' dev-docs/release-sop.md
```

Expected: the first grep shows the `tag:` input in the `workflow_dispatch` block; the second prints `2`.

- [ ] **Step 3: Commit**

```bash
git add dev-docs/release-sop.md
git commit -m "docs(release): document manual triggers and republish recovery in SOP

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: Close issue 134

**Files:**
- Move: `dev-docs/issues/134-release-pypi-publish-failure-recovery.md` → `dev-docs/issues/done/` (via script)
- Modify: `dev-docs/roadmap.md` (via script)

**Interfaces:**
- Consumes: nothing from earlier tasks; must run after Tasks 1–2 are committed (this is the final commit of the branch).

- [ ] **Step 1: Run the close script**

```bash
bin/issues/close.bash 134
```

Expected output includes `closed: dev-docs/issues/done/134-release-pypi-publish-failure-recovery.md` and a suggested commit message. The script also runs `bin/issues/check.bash` itself and stages the changes.

- [ ] **Step 2: Review the roadmap edit**

Run: `git diff --cached dev-docs/roadmap.md`

Expected: the milestone task-list line for #134 is now `[x]` and its link points at `done/`; the Open Issues paragraph for #134 is gone. The milestone rationale sentence mentioning "release-pipeline gaps 134-138 and 140" is prose the script does not edit — leave it as is (prior closes, e.g. 135, left it too).

- [ ] **Step 3: Commit**

```bash
git commit -m "docs(issues): close issue 134 (PyPI publish failure recovery), update roadmap

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

## Post-merge verification (maintainer, not part of this plan's tasks)

After the branch merges and any resulting release settles:

1. **Actions → Release → Run workflow** from `main`, `tag` = the latest already-published tag.
2. Expect a green run: semantic-release skipped, wheel built from the tag, TestPyPI and PyPI uploads skipped as existing, smoke test passes, "Release … already exists; nothing to do" in the create-release log.

This exercises the entire republish path without publishing anything and is the acceptance test for this issue.
