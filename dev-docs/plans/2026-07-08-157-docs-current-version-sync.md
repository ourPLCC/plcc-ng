# Docs-only current-version sync (issue 157) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** When a push to `main` touches `docs/` without triggering a release, re-deploy the currently-live doc version (`mike`'s `latest` alias) so the fix reaches users pinned to it, not just the `dev` preview.

**Architecture:** Two new steps added to the existing `deploy-docs` job in `.github/workflows/docs.yml`: one detects whether the push touched `docs/` (via `git diff` on the push event's before/after SHAs), the other looks up the version `mike`'s `latest` alias currently points at and re-deploys it with `mike deploy <version>` (no `--update-aliases`, so no new version is created and no alias moves).

**Tech Stack:** GitHub Actions (YAML + bash), `mike` 2.2 (already a project dependency), `jq` (preinstalled on `ubuntu-latest` runners).

## Global Constraints

- Path filter is `docs/` only — not `mkdocs.yml`. (Spec decision 2.)
- No third-party GitHub Action for path detection — inline `git diff` using the already-present `fetch-depth: 0` checkout. (Spec decision 3.)
- Everything goes into the existing `deploy-docs` job in `.github/workflows/docs.yml` — no new workflow file. (Spec decision 4.)
- "Current version" is looked up fresh at run time via `mike list latest -j`, never hardcoded. If no `latest` alias exists yet, the sync step must no-op, not fail. (Spec decision 5.)
- No automated test for this change — verification is manual/observational after merge, per the spec's Verification section. (Spec decision 6.)

Full design: [dev-docs/specs/2026-07-07-157-docs-current-version-sync-design.md](../specs/2026-07-07-157-docs-current-version-sync-design.md).

---

### Task 1: Add the "Detect docs changes" step

**Files:**
- Modify: `.github/workflows/docs.yml:36` (insert before the existing "Deploy dev docs preview" step)

**Interfaces:**
- Produces: step id `docs-changed` with output `changed` (`"true"`/`"false"`), readable elsewhere in the job as `steps.docs-changed.outputs.changed`. Consumed by Task 2.

- [ ] **Step 1: Insert the new step into `.github/workflows/docs.yml`**

Insert immediately before the `- name: Deploy dev docs preview (on push to main)` step (currently line 36), i.e. right after the "Configure git for mike" step:

```yaml
      - name: Detect docs changes
        id: docs-changed
        if: github.event_name == 'push'
        run: |
          if git diff --name-only "${{ github.event.before }}" "${{ github.event.after }}" -- docs/ | grep -q .; then
            echo "changed=true" >> "$GITHUB_OUTPUT"
          else
            echo "changed=false" >> "$GITHUB_OUTPUT"
          fi
```

The full file from line 32 through the (unmodified) "Deploy dev docs preview" step should now read:

```yaml
      - name: Configure git for mike
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
      - name: Detect docs changes
        id: docs-changed
        if: github.event_name == 'push'
        run: |
          if git diff --name-only "${{ github.event.before }}" "${{ github.event.after }}" -- docs/ | grep -q .; then
            echo "changed=true" >> "$GITHUB_OUTPUT"
          else
            echo "changed=false" >> "$GITHUB_OUTPUT"
          fi
      - name: Deploy dev docs preview (on push to main)
        if: github.event_name == 'push'
        run: |
          pdm run mike deploy dev
          if ! pdm run mike list 2>/dev/null | grep -qw 'latest'; then
            pdm run mike set-default dev
          fi
```

- [ ] **Step 2: Validate YAML syntax**

Run: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/docs.yml')); print('valid')"`
Expected: `valid`

- [ ] **Step 3: Dry-run the detection logic against real repository history**

This workflow has no test harness (see Global Constraints), so validate the embedded bash logic directly against real commits instead of a mocked CI event:

```bash
# de4b31fc touched docs/ (issue 147 heading fix) — expect changed=true
git diff --name-only 9335129ee09f9c01721337f6c0bb55570edc36bf de4b31fc3574197aace8c7146018c5dbf3986954 -- docs/ | grep -q . && echo "changed=true" || echo "changed=false"

# 6d838d13 only touched dev-docs/ (this issue's own spec commit) — expect changed=false
git diff --name-only f95aae308d3a62cba84f20fb47f07658c138ed47 6d838d1319862a3660150b2e1a10e96021910baf -- docs/ | grep -q . && echo "changed=true" || echo "changed=false"
```

Expected: `changed=true` for the first command, `changed=false` for the second.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/docs.yml
git commit -m "ci(docs): detect docs/ changes on push to main"
```

---

### Task 2: Add the "Sync current-version docs" step

**Files:**
- Modify: `.github/workflows/docs.yml` (insert after "Deploy dev docs preview", before "Deploy versioned docs (on release)")

**Interfaces:**
- Consumes: `steps.docs-changed.outputs.changed` (produced by Task 1).

- [ ] **Step 1: Insert the new step into `.github/workflows/docs.yml`**

Insert immediately after the "Deploy dev docs preview (on push to main)" step and before the "Deploy versioned docs (on release)" step:

```yaml
      - name: Sync current-version docs (docs-only push to main)
        if: github.event_name == 'push' && steps.docs-changed.outputs.changed == 'true'
        run: |
          if CURRENT_JSON=$(pdm run mike list latest -j 2>/dev/null); then
            CURRENT=$(echo "$CURRENT_JSON" | jq -r '.version')
            echo "Re-syncing docs-only change into current version: $CURRENT"
            pdm run mike deploy "$CURRENT"
          else
            echo "No 'latest' alias yet (no release published); skipping current-version sync."
          fi
```

The full job's step list should now read, in order: checkout, setup-python, Install PDM, Install dependencies, Configure git for mike, Detect docs changes, Deploy dev docs preview, **Sync current-version docs**, Deploy versioned docs (on release), Push gh-pages.

- [ ] **Step 2: Validate YAML syntax**

Run: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/docs.yml')); print('valid')"`
Expected: `valid`

- [ ] **Step 3: Dry-run the sync logic's two branches locally**

Again, no test harness exists for this workflow — validate the embedded bash directly.

Branch A — a `latest` alias exists (true today: `mike list latest -j` currently reports version `1.0`):

```bash
if CURRENT_JSON=$(pdm run mike list latest -j 2>/dev/null); then
  CURRENT=$(echo "$CURRENT_JSON" | jq -r '.version')
  echo "Re-syncing docs-only change into current version: $CURRENT"
else
  echo "No 'latest' alias yet (no release published); skipping current-version sync."
fi
```

Expected: `Re-syncing docs-only change into current version: 1.0` (do **not** run the actual `pdm run mike deploy "$CURRENT"` line locally — it writes a real commit to the local `gh-pages` branch; the goal here is only to confirm the conditional and `jq` parsing pick the right branch and extract the right version string).

Branch B — no `latest` alias (simulate by querying a nonexistent alias, confirming the `if` catches the failure instead of aborting):

```bash
if CURRENT_JSON=$(pdm run mike list nonexistent-alias -j 2>/dev/null); then
  echo "unexpected success"
else
  echo "No 'latest' alias yet (no release published); skipping current-version sync."
fi
```

Expected: `No 'latest' alias yet (no release published); skipping current-version sync.` — confirms the `if command; then` form correctly no-ops on failure rather than aborting the step (GitHub Actions runs `run:` blocks as `bash -eo pipefail`, which would otherwise kill the step on the first failing command).

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/docs.yml
git commit -m "ci(docs): sync docs-only changes into the current live version"
```

---

### Task 3: Final review and issue bookkeeping

**Files:**
- Read: `.github/workflows/docs.yml` (final state)
- Read: `dev-docs/issues/done/157-docs-only-changes-never-reach-current-version-docs.md`

- [ ] **Step 1: Read the full final `docs.yml` and confirm step order matches the design**

Run: `cat -n .github/workflows/docs.yml`
Expected order of `- name:` entries: checkout (unnamed), setup-python (unnamed), Install PDM, Install dependencies, Configure git for mike, Detect docs changes, Deploy dev docs preview (on push to main), Sync current-version docs (docs-only push to main), Deploy versioned docs (on release), Push gh-pages.

- [ ] **Step 2: Confirm no other test tier is affected**

This change touches only `.github/workflows/docs.yml`, which is not exercised by `bin/test/units.bash`, `bin/test/commands.bash`, `bin/test/integration.bash`, or `bin/test/e2e.bash` (none of them reference `docs.yml` or `mike` — confirmed during design research). Run the fast tier anyway as a sanity check that nothing else broke:

Run: `bin/test/units.bash`
Expected: all tests pass (same pass count as the pre-work baseline).

- [ ] **Step 3: Do not close issue 157 yet**

Per `dev-docs/issue-conventions.md`'s verification exception (used for release-pipeline changes that can only be proven by a real event after merge): leave issue 157 open. It gets closed with `bin/issues/close.bash 157` in a follow-up commit once a real docs-only push to `main` is observed re-deploying the current version, per the spec's Verification section. Note this explicitly when handing off / opening the PR so it isn't forgotten.

- [ ] **Step 4: Push the branch**

```bash
git push -u origin worktree-issue-157-docs-current-version-sync
```

(Per project convention, stop here — the user handles PR creation.)
