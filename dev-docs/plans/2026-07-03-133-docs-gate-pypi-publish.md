# Gate docs deploy on PyPI publish success — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stop `docs.yml` from promoting a version to `latest` before that version has actually reached PyPI, by delaying the GitHub Release object (and therefore the `release: published` event) until the `publish` job succeeds.

**Architecture:** Split the "Create GitHub Release" step out of the `semantic-release` job in `.github/workflows/release.yml` into a new `create-release` job that depends on both `semantic-release` and `publish`, with an explicit `if:` condition re-checking `needs.publish.result == 'success'` (a custom `if:` on a job with `needs:` disables GitHub Actions' implicit success-of-dependencies check, so that check must be written out by hand). `docs.yml` is not modified — it already reacts correctly to `release: published`; the fix is that the event no longer fires early.

**Tech Stack:** GitHub Actions workflow YAML (`.github/workflows/release.yml`), `gh` CLI, PyYAML (for syntax validation only, already a transitive dependency — no new deps).

## Global Constraints

- Design doc: `dev-docs/specs/2026-07-03-133-docs-gate-pypi-publish-design.md`
- Scope covers issue 133 (ordering/gating) and issue 139 (GITHUB_TOKEN-created releases don't trigger downstream workflows — folded in because it's a direct prerequisite for this fix to have any effect). Do not touch retry logic (issue 134) or PyPI environment protection (issue 138).
- `docs.yml` must not be modified — the design relies on the existing `release: published` trigger continuing to work unchanged, just firing later (and, per issue 139, actually reaching it).
- The `create-release` job's gating condition must be exactly:
  `needs.semantic-release.outputs.released == 'true' && needs.publish.result == 'success'`
  (omitting the `needs.publish.result` check reproduces the bug — see design doc §2).
- The `create-release` job must authenticate `gh release create` with a GitHub App installation token (via `actions/create-github-app-token@v1`, `secrets.RELEASE_APP_ID` / `secrets.RELEASE_APP_PRIVATE_KEY`), not `secrets.GITHUB_TOKEN` — see design doc's "Release creation must use the GitHub App token" section.
- No CI test tier exists for GitHub Actions YAML in this repo (no `actionlint`/`yamllint` installed). Verification is YAML-syntax parsing plus manual trace against the design doc's behavior matrix.

---

### Task 1: Split release creation into a publish-gated job

**Files:**
- Modify: `.github/workflows/release.yml`

**Interfaces:**
- Consumes: `needs.semantic-release.outputs.released`, `needs.semantic-release.outputs.version` (already exposed as job outputs on the existing `semantic-release` job — unchanged by this task).
- Produces: N/A (this is the only task in the plan; nothing downstream depends on new interfaces).

- [ ] **Step 1: Read the current file to confirm line numbers before editing**

Run: `grep -n "Create GitHub Release\|^  publish:\|^  semantic-release:\|^jobs:" .github/workflows/release.yml`

Expected output (line numbers may vary slightly but structure should match):
```text
11:jobs:
12:  semantic-release:
...
39:      - name: Create GitHub Release
...
47:  publish:
```

- [ ] **Step 2: Remove the "Create GitHub Release" step from the `semantic-release` job**

In `.github/workflows/release.yml`, delete this block from inside the `semantic-release` job's `steps:` (it currently follows the "Python Semantic Release" step):

```yaml
      - name: Create GitHub Release
        if: steps.release.outputs.released == 'true'
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          VERSION="${{ steps.release.outputs.version }}"
          gh release create "v${VERSION}" \
            --title "v${VERSION}" \
            --target "${{ github.sha }}" \
            --generate-notes
```

The `semantic-release` job's `steps:` list should now end with the "Python Semantic Release" step (id: `release`).

- [ ] **Step 3: Add the new `create-release` job**

Add this job to `.github/workflows/release.yml`, after the `publish` job (i.e., as the last job in the file):

```yaml

  create-release:
    name: Create GitHub Release
    needs: [semantic-release, publish]
    if: |
      needs.semantic-release.outputs.released == 'true' &&
      needs.publish.result == 'success'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/create-github-app-token@v1
        id: app-token
        with:
          app-id: ${{ secrets.RELEASE_APP_ID }}
          private-key: ${{ secrets.RELEASE_APP_PRIVATE_KEY }}
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          ref: ${{ format('v{0}', needs.semantic-release.outputs.version) }}
          token: ${{ steps.app-token.outputs.token }}
      - name: Create GitHub Release
        env:
          GH_TOKEN: ${{ steps.app-token.outputs.token }}
        run: |
          VERSION="${{ needs.semantic-release.outputs.version }}"
          gh release create "v${VERSION}" \
            --title "v${VERSION}" \
            --target "${{ github.sha }}" \
            --generate-notes
```

This uses the GitHub App installation token (same secrets `semantic-release` already uses) instead of `secrets.GITHUB_TOKEN`, and checks out the pushed `v{version}` tag instead of `github.sha` — see design doc's "Release creation must use the GitHub App token" section for why (issue 139: `GITHUB_TOKEN`-created releases don't trigger downstream workflows, so `docs.yml` would never receive `release: published` regardless of this task's gating fix).

- [ ] **Step 4: Validate YAML syntax**

Run: `python -c "import yaml; yaml.safe_load(open('.github/workflows/release.yml')); print('OK')"`

Expected: `OK` with no exception. If this raises a `yaml.YAMLError`, the indentation from Steps 2–3 is wrong — fix before proceeding.

- [ ] **Step 5: Manually trace the job graph against the behavior matrix**

Open `.github/workflows/release.yml` and confirm each row of the design doc's behavior matrix by reading the relevant `if:`/`needs:` lines (no code changes in this step — this is a verification checklist):

1. `semantic-release` job: confirm it has no `if:` on the job itself (always runs), and its `steps.release.outputs.released` / `.version` are exposed via the job-level `outputs:` block (should already exist above `jobs.semantic-release.steps`) — confirm with:
   `grep -n -A2 "^    outputs:" .github/workflows/release.yml`
2. `publish` job: confirm `needs: semantic-release` and `if: needs.semantic-release.outputs.released == 'true'` are unchanged:
   `grep -n -B1 -A1 "^  publish:" .github/workflows/release.yml`
3. `create-release` job: confirm `needs: [semantic-release, publish]` and the two-part `if:` from Step 3 are present exactly as written (a missing `needs.publish.result == 'success'` clause means a failed `publish` would not block release creation — this is the bug):
   `grep -n -A5 "^  create-release:" .github/workflows/release.yml`
4. Confirm `docs.yml` is untouched:
   `git diff --stat -- .github/workflows/docs.yml` should print nothing (no output = no changes).

- [ ] **Step 6: Run the unit test suite as a regression sanity check**

This change touches no Python code, so no test should be affected — this step confirms that's true and the baseline stays green.

Run: `bin/test/units.bash`

Expected: same pass count as the pre-work baseline (1175 passed, 1 skipped), 0 new failures.

- [ ] **Step 7: Commit**

```bash
git add .github/workflows/release.yml
git commit -m "$(cat <<'EOF'
fix(release): gate GitHub Release creation on publish job success

The semantic-release job used to create the GitHub Release immediately
after tagging, before the publish job (TestPyPI, smoke test, real PyPI)
ran. docs.yml deploys and promotes docs to `latest` on release:published,
so it could fire before, or even if, the version ever reached PyPI.

Move release creation into a new create-release job that needs both
semantic-release and publish, with an explicit check on
needs.publish.result since a custom `if:` on a job disables the
implicit success-of-dependencies check GitHub Actions would otherwise
apply.
EOF
)"
```

- [ ] **Step 8: Fold in issue 139's fix (GitHub App token instead of GITHUB_TOKEN)**

Raised by PR review after Step 7's commit landed: `secrets.GITHUB_TOKEN` is
subject to GitHub's recursion-prevention rule, so events it creates
(including the `release: published` this whole task depends on) may never
reach `docs.yml`. Apply the `create-release` job changes shown in Step 3
above (the `actions/create-github-app-token@v1` step, checkout `ref`/`token`,
and `GH_TOKEN: ${{ steps.app-token.outputs.token }}`), then repeat Step 4
(YAML syntax check) and Step 6 (`bin/test/units.bash` regression check).

Commit:

```bash
git add .github/workflows/release.yml
git commit -m "$(cat <<'EOF'
fix(release): authenticate create-release with GitHub App token

gh release create was authenticated with secrets.GITHUB_TOKEN, which
GitHub Actions exempts from triggering downstream workflows (recursion
prevention). That meant docs.yml's release:published listener likely
never fired on any past release, regardless of this branch's ordering
fix. Switch to the GitHub App installation token semantic-release
already uses, and checkout the pushed version tag for consistency with
the publish job's checkout. Closes issue 139.
EOF
)"
```

---

## Self-Review Notes

- **Spec coverage:** Design doc's "Job graph change" → Steps 2–3. "Gating condition" → Step 3's `if:` block. "Behavior across trigger types" → Step 5's trace. "Testing/verification" → Steps 4 and 6. No spec section is left uncovered; `docs.yml` is explicitly confirmed untouched in Step 5.4.
- **Placeholder scan:** No TBD/TODO; every step has literal YAML/commands, not descriptions.
- **Type/interface consistency:** `needs.semantic-release.outputs.released` and `.version` are the same names used in the existing `publish` job (`needs.semantic-release.outputs.released` / `.version` per the current file) and are not renamed here — single source of truth.
- **Scope:** Single file, single task. No decomposition into multiple tasks needed; the whole change is one atomic, independently-testable-by-YAML-parse-and-trace unit.
