# Docs-only changes never reach current-version docs (issue 157) — design

**Date:** 2026-07-07
**Issue:** [157 - docs-only-changes-never-reach-current-version-docs](../issues/done/157-docs-only-changes-never-reach-current-version-docs.md)

## Problem

`mike` versions the published docs (see
[.github/workflows/docs.yml](../../.github/workflows/docs.yml)): every
push to `main` redeploys the `dev` alias, but only a GitHub `release`
event redeploys a version alias (e.g. `1.0`) and moves `latest`. Since
`docs`-only commits never bump the version (by design — see
[issues/TEMPLATE.md](../issues/TEMPLATE.md)), a docs-only PR merged to
`main` updates `dev` but never reaches `1.0`/`latest` until the next
unrelated release. Discovered via issue #147 (heading capitalization):
the fix appeared on the `dev` preview but not on the docs users are
actually pinned to.

## Decisions

Explored during brainstorming (2026-07-07):

1. **Sync unconditionally on every docs-only push to `main`.** No
   label, commit-footer, or severity heuristic gates it. Simpler, no
   judgment calls to get wrong or forget; the tradeoff (a released
   version's docs can drift slightly from "exactly what shipped with
   that release," even for cosmetic edits) is accepted.
2. **Path filter is `docs/` only** — not `mkdocs.yml`. Matches the
   issue's proposed direction. A conscious YAGNI call: config/nav
   changes don't trigger the sync. Easy to widen later if that turns
   out to matter.
3. **Detect the changed paths inline with `git diff`, not a
   third-party Action.** `dorny/paths-filter` (or similar) would work,
   but this repo has no third-party Actions for anything this
   mechanical, and `docs.yml` already does inline bash for everything
   else. `fetch-depth: 0` is already set on checkout, so
   `github.event.before`/`github.event.after` are diffable with no new
   dependency.
4. **Extend the existing `deploy-docs` job — don't add a second
   workflow file.** A separate `docs-sync.yml` would duplicate
   checkout/setup-python/pdm-install/git-config and would need to
   share the `docs-deploy` concurrency group anyway to avoid racing on
   `gh-pages`. Two new steps in the existing job get the same result
   with no duplication.
5. **"Current version" = whatever `mike list` reports the `latest`
   alias pointing at**, looked up fresh at run time (`mike list latest
   -j`), not hardcoded or derived from `pyproject.toml`. If no
   `latest` alias exists yet (pre-first-release), the sync step is a
   no-op, not a failure.
6. **No automated test for this.** There is no existing harness for
   `docs.yml`'s YAML/bash logic in this repo, and building one isn't
   worth it for a few lines of shell. Verification is observational,
   per issue-conventions.md's "close on verification" exception: merge
   without closing #157, confirm on the next real docs-only push that
   `1.0`'s live content updates while `latest`/the version list stay
   unchanged, then close in a follow-up commit.

## Design

### Step order in `deploy-docs` (`.github/workflows/docs.yml`)

1. checkout — unchanged
2. setup-python — unchanged
3. install PDM — unchanged
4. install dependencies — unchanged
5. configure git for mike — unchanged
6. **(new) Detect docs changes** — `if: github.event_name == 'push'`
7. Deploy dev docs preview (on push to main) — unchanged, still runs
   on every push regardless of path
8. **(new) Sync current-version docs** — `if: github.event_name ==
   'push' && steps.docs-changed.outputs.changed == 'true'`
9. Deploy versioned docs (on release) — unchanged
10. Push gh-pages — unchanged; already unconditional, so it picks up
    any commit made by step 8 too

### Step 6 — Detect docs changes

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

### Step 8 — Sync current-version docs

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

No `--update-aliases`: this only refreshes the already-live version's
content. It does not create a new version, move `latest`, or touch
`dev`.

### Error handling

- **No `latest` alias yet** (pre-first-release): `mike list latest -j`
  exits 1. The `if CURRENT_JSON=$(...); then` form catches that
  without tripping GitHub Actions' `bash -eo pipefail` step semantics,
  and the step logs a skip message instead of failing.
- **`mike deploy` fails** (e.g. a `gh-pages` push conflict): left
  unguarded, so the step fails the job — same behavior as the existing
  "Deploy dev docs preview" and "Deploy versioned docs" steps. No
  silent swallowing.
- **Redundant run on a release-carrying push:** if a push to `main`
  both touches `docs/` and contains a `feat`/`fix` that triggers
  `release.yml`, this step will redeploy the *old* current version
  moments before the release pipeline deploys the *new* one via the
  `release` event. Harmless (extra `mike deploy` of soon-to-be-stale
  content) and not worth special-casing.
- **`git diff` can't resolve `before`/`after`** (e.g.
  `github.event.before` is the null SHA on an unusual push event —
  not expected on a `branches: [main]`-only trigger, but not
  impossible): the pipe-free `[ -n "$(...)" ]` test in the
  detect-changes step evaluates false in that case, so the step
  degrades to `changed=false` — a safe skip of this run's sync, not a
  crash or corruption.

## Verification

No automated test. After merging:

1. Wait for (or make) a real docs-only push to `main`.
2. Confirm the "Sync current-version docs" step ran and deployed the
   version matching the current `latest` alias.
3. Check the live site (`https://ourplcc.github.io/plcc-ng/<version>/`)
   reflects the change, and that `versions.json` / the version
   switcher's `latest` target is unchanged.
4. Close issue #157 in a follow-up commit once confirmed (per
   issue-conventions.md's verification exception).
