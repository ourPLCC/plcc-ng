# Release Notes Unification (Issue 136) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** GitHub Release notes come from the tag's CHANGELOG.md section instead of `--generate-notes`, so each release has one narrative; a follow-up issue is opened for the user-facing "What's New" page.

**Architecture:** A new `bin/release/extract-changelog.bash` script prints one version's section from CHANGELOG.md (bats-tested). The `create-release` job in `.github/workflows/release.yml` calls it and passes the output to `gh release create --notes-file`, only when the release doesn't already exist — preserving the issue-134 recovery ordering. SOP and issue-tracker updates round it out.

**Tech Stack:** bash, awk, bats (`tests/bats/commands/`), GitHub Actions, `gh` CLI.

**Spec:** `docs/superpowers/specs/2026-07-04-136-release-notes-unification-design.md`

## Global Constraints

- No ad-hoc shell scripts — reusable logic goes in `bin/`, matching existing style: `#!/usr/bin/env bash`, `set -euo pipefail`, `SCRIPT_DIR`/`PROJECT_ROOT` preamble, `usage()` on bad args (see `bin/issues/new.bash`).
- Conventional commit messages; never add `[skip ci]`; end commit messages with `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`.
- TDD: write the failing bats test first, watch it fail, then implement.
- Issue files are only created/closed via `bin/issues/new.bash` / `bin/issues/close.bash`; roadmap entry lands in the same commit; `bin/issues/check.bash` must pass.
- No fallback to `--generate-notes` anywhere — extraction failure must fail the job loudly.

---

### Task 1: `bin/release/extract-changelog.bash` + bats tests

**Files:**
- Create: `bin/release/extract-changelog.bash`
- Test: `tests/bats/commands/release-extract-changelog.bats`

**Interfaces:**
- Produces: `bin/release/extract-changelog.bash <version>` — `<version>` has no leading `v` (e.g. `0.65.0`). Prints the CHANGELOG.md section for `v<version>` to stdout, **excluding** the `## v<version> (date)` heading line itself (the GitHub Release title already names the tag) and trimming leading/trailing blank lines. Reads `$CHANGELOG_FILE` if set (for tests), else `<repo>/CHANGELOG.md`. Exit 0 on success; usage + exit 1 on wrong argument count; diagnostic on stderr + exit 1 if no heading matches.
- The heading match is a literal line-prefix match on `## v<version>` followed by a space and the date's opening parenthesis — matching through that parenthesis prevents `0.1.1` from matching the `v0.1.10` heading.

- [ ] **Step 1: Write the failing bats tests**

Create `tests/bats/commands/release-extract-changelog.bats`:

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

PROJECT_ROOT="$(git rev-parse --show-toplevel)"
EXTRACT="${PROJECT_ROOT}/bin/release/extract-changelog.bash"

setup() {
    WORK_DIR="$(mktemp -d)"
    export CHANGELOG_FILE="${WORK_DIR}/CHANGELOG.md"
    cat > "${CHANGELOG_FILE}" <<'EOF'
# CHANGELOG


## v0.1.10 (2026-07-04)

### Bug Fixes

- newest fix entry


## v0.1.1 (2026-07-03)

### Features

- middle feature entry


## v0.1.0 (2026-07-01)

### Features

- oldest feature entry
EOF
}

teardown() {
    rm -rf "${WORK_DIR}"
}

@test "extract-changelog: extracts the newest section" {
    run bash "${EXTRACT}" 0.1.10
    [ "$status" -eq 0 ]
    [[ "$output" == *"newest fix entry"* ]]
}

@test "extract-changelog: extracts a middle section" {
    run bash "${EXTRACT}" 0.1.1
    [ "$status" -eq 0 ]
    [[ "$output" == *"middle feature entry"* ]]
}

@test "extract-changelog: extracts the oldest section (ends at EOF)" {
    run bash "${EXTRACT}" 0.1.0
    [ "$status" -eq 0 ]
    [[ "$output" == *"oldest feature entry"* ]]
}

@test "extract-changelog: output excludes neighboring sections" {
    run bash "${EXTRACT}" 0.1.1
    [ "$status" -eq 0 ]
    [[ "$output" != *"newest fix entry"* ]]
    [[ "$output" != *"oldest feature entry"* ]]
}

@test "extract-changelog: output excludes the version heading line" {
    run bash "${EXTRACT}" 0.1.1
    [ "$status" -eq 0 ]
    [[ "$output" != *"## v0.1.1"* ]]
}

@test "extract-changelog: does not trim or pad output content" {
    run bash "${EXTRACT}" 0.1.1
    [ "$status" -eq 0 ]
    [ "${lines[0]}" = "### Features" ]
    [ "${lines[1]}" = "- middle feature entry" ]
}

@test "extract-changelog: version is not treated as a prefix" {
    # v0.1.1 must not match the v0.1.10 heading; entry content proves which
    # section was found.
    run bash "${EXTRACT}" 0.1.1
    [[ "$output" != *"newest fix entry"* ]]
    [[ "$output" == *"middle feature entry"* ]]
}

@test "extract-changelog: fails with a diagnostic on an unknown version" {
    run bash "${EXTRACT}" 9.9.9
    [ "$status" -ne 0 ]
    [[ "$output" == *"no section for version 'v9.9.9'"* ]]
}

@test "extract-changelog: fails with usage when called without arguments" {
    run bash "${EXTRACT}"
    [ "$status" -ne 0 ]
    [[ "$output" == *"Usage:"* ]]
}
```

Note on the "does not trim or pad" test: `bats` `lines[]` skips blank lines, so it checks content order; the leading/trailing blank-line trim is observable via `$output` not starting/ending with newline noise — content assertions above are sufficient.

- [ ] **Step 2: Run the tests to verify they fail**

```bash
bin/install/bats.bash
bats tests/bats/commands/release-extract-changelog.bats
```

Expected: all 9 tests FAIL (status 127, `bin/release/extract-changelog.bash: No such file or directory`).

- [ ] **Step 3: Write the script**

Create `bin/release/extract-changelog.bash` (mode 755):

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( cd "${SCRIPT_DIR}/../.." &> /dev/null && pwd )"

usage() {
    echo "Usage: $(basename "$0") <version>"
    echo "  version  release version without the leading 'v', e.g. 0.65.0"
    echo
    echo "Prints the CHANGELOG.md section for the given version to stdout,"
    echo "excluding the version heading line. Exits non-zero if the version"
    echo "has no section. Reads \$CHANGELOG_FILE if set (for tests)."
    exit 1
}

[[ $# -ne 1 ]] && usage

VERSION="$1"
CHANGELOG="${CHANGELOG_FILE:-${PROJECT_ROOT}/CHANGELOG.md}"

if ! awk -v ver="${VERSION}" '
    BEGIN { header = "## v" ver " ("; found = 0; printing = 0; n = 0 }
    printing && /^## / { printing = 0 }
    printing { lines[n++] = $0 }
    !printing && index($0, header) == 1 { found = 1; printing = 1 }
    END {
        if (!found) exit 1
        while (n > 0 && lines[n - 1] == "") n--
        i = 0
        while (i < n && lines[i] == "") i++
        for (; i < n; i++) print lines[i]
    }
' "${CHANGELOG}"; then
    echo "error: no section for version 'v${VERSION}' in ${CHANGELOG}" >&2
    exit 1
fi
```

Then `chmod +x bin/release/extract-changelog.bash`.

- [ ] **Step 4: Run the tests to verify they pass**

```bash
bats tests/bats/commands/release-extract-changelog.bats
```

Expected: 9 tests, all PASS.

- [ ] **Step 5: Sanity-check against the real CHANGELOG**

```bash
bin/release/extract-changelog.bash 0.65.0 | head -5
bin/release/extract-changelog.bash 9.9.9; echo "exit: $?"
```

Expected: first prints `### Bug Fixes` and the v0.65.0 entries (no `## v0.65.0` heading line); second prints the error to stderr and `exit: 1`.

- [ ] **Step 6: Run the full commands tier**

```bash
bin/test/commands.bash
```

Expected: all command bats tests pass (pre-existing tests unaffected).

- [ ] **Step 7: Commit**

```bash
git add bin/release/extract-changelog.bash tests/bats/commands/release-extract-changelog.bats
git commit -m "feat(release): add extract-changelog script for version release notes

Prints one version's CHANGELOG.md section, excluding the heading line,
for use as GitHub Release notes. Fails loudly on an unknown version.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: `create-release` uses the CHANGELOG section

**Files:**
- Modify: `.github/workflows/release.yml` (the `Create GitHub Release` step, last step of the `create-release` job)

**Interfaces:**
- Consumes: `bin/release/extract-changelog.bash <version>` from Task 1 (version without leading `v`; section on stdout; non-zero exit on failure).

- [ ] **Step 1: Replace the release-creation command**

In `.github/workflows/release.yml`, replace the final step's `run` block. Current:

```yaml
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

New:

```yaml
      - name: Create GitHub Release
        env:
          GH_TOKEN: ${{ steps.app-token.outputs.token }}
        run: |
          if gh release view "${RELEASE_TAG}" >/dev/null 2>&1; then
            echo "Release ${RELEASE_TAG} already exists; nothing to do"
          else
            bin/release/extract-changelog.bash "${RELEASE_TAG#v}" \
              > "${RUNNER_TEMP}/release-notes.md"
            gh release create "${RELEASE_TAG}" \
              --title "${RELEASE_TAG}" \
              --notes-file "${RUNNER_TEMP}/release-notes.md"
          fi
```

Why inside the `else`: the job checks out the repository *at the tag*. Old tags predate the script, so running extraction unconditionally would break the SOP's safe end-to-end republish test (dispatch with the latest already-published tag). When the release already exists, there is nothing to extract notes for. Actions `run` uses `bash -e`, so a failing extraction fails the step — no fallback.

- [ ] **Step 2: Verify the workflow file still parses**

```bash
pdm run python -c "import yaml; yaml.safe_load(open('.github/workflows/release.yml')); print('ok')"
```

Expected: `ok`. (If `yaml` is unavailable in the venv, `python3 -c` with the same body — PyYAML ships with the mkdocs toolchain.)

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/release.yml
git commit -m "feat(release): source GitHub Release notes from CHANGELOG.md

Replace --generate-notes (PR-based auto-notes) with the tag's
CHANGELOG.md section via bin/release/extract-changelog.bash, so each
release has one narrative. Extraction failure fails the job; recovery
is the existing republish path. Runs only when the release is missing,
so republishing tags that predate the script still no-ops green.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: Release SOP update

**Files:**
- Modify: `dev-docs/release-sop.md`

**Interfaces:** none (docs only).

- [ ] **Step 1: Document the notes source in the SOP**

In `dev-docs/release-sop.md`, append a new section at the end of the file:

```markdown
## GitHub Release notes

GitHub Release notes are the tag's `CHANGELOG.md` section, extracted by
[bin/release/extract-changelog.bash](../../bin/release/extract-changelog.bash)
in the `create-release` job — the same conventional-commit content
python-semantic-release writes to the changelog, so the two never
diverge. There is deliberately no fallback to GitHub's PR-based
auto-notes: if extraction fails (e.g. a malformed changelog heading),
the `create-release` job fails. Fix the cause, then recover with the
republish dispatch above. Extraction only runs when the release is
missing, so republishing a tag that predates the script still no-ops
green.
```

Also update the "Republish an existing tag" section's idempotency sentence to keep it accurate. Replace:

```markdown
3. The run skips semantic-release, builds the wheel from the tag, and
   reruns the whole publish path. Every step is idempotent —
   `skip-existing` on TestPyPI and PyPI, GitHub Release created only if
   missing — so there is no need to know how far the failed run got.
```

with:

```markdown
3. The run skips semantic-release, builds the wheel from the tag, and
   reruns the whole publish path. Every step is idempotent —
   `skip-existing` on TestPyPI and PyPI, GitHub Release created (with
   notes from the tag's `CHANGELOG.md` section) only if missing — so
   there is no need to know how far the failed run got.
```

- [ ] **Step 2: Commit**

```bash
git add dev-docs/release-sop.md
git commit -m "docs(release): document changelog-sourced GitHub Release notes in SOP

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 4: Open the "What's New" follow-up issue

**Files:**
- Create: `dev-docs/issues/141-whats-new-user-release-notes.md` (via `bin/issues/new.bash` — never by hand; the ID comes from `.next-id.txt`, expected to be 141)
- Modify: `dev-docs/roadmap.md` (Open Issues → Features)

**Interfaces:** none (issue tracker only).

- [ ] **Step 1: Create the issue file**

```bash
bin/issues/new.bash whats-new-user-release-notes feat
```

Expected output: `dev-docs/issues/141-whats-new-user-release-notes.md` (use whatever path it prints — do not rename).

- [ ] **Step 2: Fill in the issue body**

Replace the created file's content below the header (keep the `# 141 - …`, `**Type:**`, `**Date:**` lines the script generated; delete the "Steps to Reproduce" section) so the file reads:

```markdown
# 141 - whats-new-user-release-notes

**Type:** feat
**Date:** 2026-07-04

## Description

Add a user-facing "What's New" page: hand-curated (AI-drafted,
human-reviewed) release notes that tell users what changed, why it
matters to them, and where to learn more — distinct from the
developer-facing CHANGELOG.md and GitHub Releases.

Agreed design (Part 2 of
[the issue-136 design spec](../specs/2026-07-04-136-release-notes-unification-design.md)):

- `docs/whats-new.md`, in the mkdocs nav near the top. Newest entry
  first. Each entry: date, version range covered, prose sections, links
  into the user docs. An HTML comment marker
  (`<!-- last-covered: vX.Y.Z -->`) records where the next drafting
  session picks up.
- Cadence: milestone-driven with a quarterly floor — a new entry when a
  roadmap phase or significant batch of work completes, or when three
  months elapse, whichever comes first.
- Process: AI drafts from CHANGELOG.md (since the marker), design specs,
  and closed issues in that range; a human reviews and edits before
  merge. Review is the quality gate.
- First entry: timed with the approach to v1.0 — a highlights tour of
  PLCC-ng, especially relative to PLCC, linking to `docs/migration.md`
  rather than duplicating it.
- Once the page exists, the changelog page (`docs/changelog.md`) leaves
  the user docs site and nav (`mkdocs.yml`); the developer-facing
  changelog is published on the dev-docs site (`mkdocs-dev.yml`)
  instead.

## Notes

- Split out of issue 136 during brainstorming (2026-07-04): the
  per-release narrative unification landed there; this issue owns the
  user-facing narrative.
- Towncrier (per-PR news fragments) was considered and rejected for
  now — wrong cost/benefit at release-per-merge cadence; revisit if the
  milestone cadence proves too coarse.
```

- [ ] **Step 3: Add the roadmap entry**

In `dev-docs/roadmap.md`, under `## Open Issues` → `### Features`, add (alphabetical/numeric position among existing entries — append after the last `#1xx` feature entry):

```markdown
- **[#141](issues/141-whats-new-user-release-notes.md) — Add a user-facing "What's New" page**
  Milestone-cadence, AI-drafted/human-reviewed release notes in the user
  docs; moves the changelog page to the dev-docs site. First entry
  targets v1.0. Design in the issue-136 spec (Part 2).
```

- [ ] **Step 4: Verify tracker consistency**

```bash
bin/issues/check.bash
```

Expected: passes with no errors.

- [ ] **Step 5: Commit**

```bash
git add dev-docs/issues/.next-id.txt dev-docs/issues/141-whats-new-user-release-notes.md dev-docs/roadmap.md
git commit -m "docs(issues): open issue 141 (user-facing what's-new page)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 5: Close issue 136 (final commit)

**Files:**
- Modify (via script): `dev-docs/issues/136-release-changelog-vcs-release-divergence.md` → `dev-docs/issues/done/`, `dev-docs/roadmap.md`

**Interfaces:** none.

- [ ] **Step 1: Run the close script**

```bash
bin/issues/close.bash 136
```

Expected: moves the file to `done/`, checks the box in the "Path to v1.0" list, removes the Open Issues entry, runs `check.bash`, and prints the suggested commit message.

- [ ] **Step 2: Review the roadmap milestone text**

The "Path to v1.0" item 4 rationale reads "decide `vcs_release` vs. PR-based notes; the answer changes what the SOP documents" — the decision is made (neither: notes-file from CHANGELOG). Edit that line's rationale to:

```markdown
4. [x] [#136](issues/done/136-release-changelog-vcs-release-divergence.md) — resolved: GitHub Release notes now come from the tag's CHANGELOG.md section (`--notes-file`); `vcs_release` stays false; SOP updated.
```

- [ ] **Step 3: Run the full functional check**

```bash
bin/test/functional.bash
```

Expected: all tiers pass.

- [ ] **Step 4: Commit**

```bash
git add dev-docs/roadmap.md
git commit -m "docs(issues): close issue 136 (release notes unification), update roadmap

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

(The close script already staged the file move; `git add` of the roadmap picks up the manual rationale edit.)

---

## Post-merge verification (not part of this branch)

1. After the PR merges and the next release runs, confirm the new GitHub
   Release's body matches that version's `CHANGELOG.md` section.
2. Run the SOP's safe end-to-end republish test (dispatch with the latest
   already-published tag) and confirm the run no-ops green.
