# Design: gate docs deploy on PyPI publish success

Issue: [dev-docs/issues/133-release-docs-gate-pypi-publish.md](../issues/done/133-release-docs-deploy-decoupled-from-pypi-publish.md)

## Problem

In `.github/workflows/release.yml`, the `semantic-release` job creates the
GitHub Release (`gh release create`) immediately after tagging and updating
the changelog — before the `publish` job (build wheel, publish TestPyPI,
smoke test, publish real PyPI) has run or succeeded.

`docs.yml` deploys versioned docs and promotes a version to `latest` on the
`release: published` event, which fires as soon as the GitHub Release object
is created. Because that happens before `publish` completes, the docs site
can point users at a version that isn't installable yet, or never will be if
`publish` fails.

## Scope

This design covers the ordering/gating bug (issue 133) and, since it was
discovered mid-implementation to be a direct prerequisite for the fix to
have any effect, issue 139 (releases created with `GITHUB_TOKEN` don't
trigger downstream workflows — see "Release creation must use the GitHub
App token" below). It does not address:
- Issue 134 (no recovery path if a tagged release's `publish` job fails)
- Issue 138 (whether the `pypi` environment has a required-reviewer gate)

Those remain separate issues; this design doesn't block or preclude them.

## Design

### Job graph change

Split `gh release create` out of the `semantic-release` job into a new job,
`create-release`, that depends on both `semantic-release` and `publish`:

- **`semantic-release`** — unchanged except for removing the "Create GitHub
  Release" step. Still tags, updates `CHANGELOG.md`, pushes both, and
  outputs `released` / `version`.
- **`publish`** — unchanged. Still `needs: semantic-release`, still gated
  on `needs.semantic-release.outputs.released == 'true'`.
- **`create-release`** (new) — runs the `gh release create` step. `needs:
  [semantic-release, publish]`.

Because `create-release` depends on `publish`, the `release: published`
event cannot fire until `publish` has completed. **`docs.yml` requires no
changes** — it already reacts correctly to that event; the event itself is
just no longer premature.

### Gating condition

A `needs:` edge alone is not sufficient. GitHub Actions' implicit
`success()` check on a job only applies when the job has no custom `if:`.
`create-release` needs a custom condition regardless (to check
`released == 'true'`), and writing any custom `if:` removes the implicit
success-of-all-needed-jobs check — the job would otherwise run even if
`publish` failed.

The condition must explicitly re-check `publish`'s result:

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

Without the explicit `needs.publish.result == 'success'` clause, a failed
`publish` job would still leave `create-release` free to run, reproducing
the bug this design fixes.

### Release creation must use the GitHub App token, not GITHUB_TOKEN (issue 139)

The original step (both before this design and in an earlier draft of it)
authenticated `gh release create` with `secrets.GITHUB_TOKEN`. GitHub
Actions suppresses downstream workflow triggers for events created by the
automatic `GITHUB_TOKEN` (recursion prevention) — for `release: published`,
this means `docs.yml` may never run at all, regardless of timing. Evidence
for this in this repo: `gh-pages`'s `versions.json` shows only a `dev`
entry despite 60+ tagged releases — the release-triggered docs deploy job
appears to have never fired.

The fix is to mint a GitHub App installation token (`actions/create-github-app-token@v1`,
the same `RELEASE_APP_ID` / `RELEASE_APP_PRIVATE_KEY` secrets the
`semantic-release` job already uses) and use that token both for checkout
and as `GH_TOKEN` when calling `gh release create`. Events created with an
app installation token are not subject to the `GITHUB_TOKEN` recursion
restriction, so `release: published` reaches `docs.yml` as intended.

The checkout is also changed to check out the pushed `v{version}` tag
(via `ref:`) rather than `github.sha`, matching how the `publish` job
checks out the same tag — consistent, and necessary once checkout needs
the app token's ref resolution to match the tag `gh release create`
operates on.

### Behavior across trigger types

| Trigger | `released` | `publish` | `create-release` | Docs deploy |
|---|---|---|---|---|
| Push to `main`, releasable commits, publish succeeds | `true` | runs, succeeds | runs → GH Release created | Fires correctly, after real PyPI publish confirmed |
| Push to `main`, releasable commits, publish fails | `true` | runs, fails | skipped (condition false) | Never fires — no premature "latest" |
| Push to `main`, no releasable commits | `false` | skipped | skipped | No release, no docs event (same as today) |
| `workflow_dispatch` (manual dry run) | `true` | runs; real-PyPI step skipped by its own `if`, job still succeeds | runs → GH Release created | Fires (same as today — real-PyPI is intentionally skipped only on dispatch, unrelated to this issue) |

### Residual state (explicitly out of scope)

If `publish` fails, the tag and `CHANGELOG.md` update from `semantic-release`
have already been pushed to `main`, but no GitHub Release or docs deploy
happens. That "tagged but not released" state is what issue 134 (recovery
path) covers. This design doesn't resolve it, but it also doesn't make it
worse — and it's now visible (no release, no docs change) instead of masked
by a premature Release/docs deploy.

## Testing / verification

This is CI workflow YAML; there's no unit-test tier for it, and neither
`actionlint` nor `yamllint` is available in this repo. Verification is:

1. **YAML syntax check** — parse `release.yml` with
   `python -c "import yaml; yaml.safe_load(open('.github/workflows/release.yml'))"`
   before committing.
2. **Manual dependency-graph trace** — walk the `needs:`/`if:` conditions
   against the behavior matrix above to confirm no path lets
   `create-release` fire without `publish` succeeding.
3. **No live end-to-end test is possible from a branch** — exercising the
   fix for real requires a push to `main` with a releasable commit, which
   only happens post-merge. The next real release is the de facto
   integration test for this change.
