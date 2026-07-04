# 134 — Recovery path for PyPI publish failure after tagging

**Date:** 2026-07-04
**Issue:** [dev-docs/issues/134-release-pypi-publish-failure-recovery.md](../../../dev-docs/issues/134-release-pypi-publish-failure-recovery.md)
**Status:** Approved

## Problem

In `.github/workflows/release.yml`, once `python-semantic-release` tags
`v{version}` and pushes the CHANGELOG commit, those commits count as
released — even if the downstream `publish` job (build → TestPyPI → smoke
test → real PyPI) fails partway through. Re-running the workflow finds no
new releasable commits, so `publish` is skipped again. There is no
documented or automated way to retry publishing an already-tagged version.

"Re-run failed jobs" on the original run covers only transient failures:
it re-uses the workflow file as it existed on that run (useless when the
failure was a workflow bug that has since been fixed) and re-runs expire.

A second, related defect: the real-PyPI step carries
`if: github.event_name != 'workflow_dispatch'`, making manual dispatch a
partial "dry run" that stops at TestPyPI. But semantic-release still tags
and pushes for real on dispatch, and `create-release` still creates a
GitHub Release — so dispatching with unreleased commits on main
*manufactures* exactly the tagged-but-not-on-PyPI state this issue is
about. The condition dates from the first version of the workflow with no
recorded rationale.

## Design

One workflow, one new input. `workflow_dispatch` gains an optional `tag`
input ("Existing tag to republish (e.g. v0.64.4). Leave empty for a
normal release."). The dry-run behavior is removed.

- **`tag` empty (or push trigger):** identical to today's push-triggered
  release — semantic-release decides whether anything is releasable and
  the full publish path runs, including real PyPI.
- **`tag` set:** semantic-release is skipped; the publish and
  create-release jobs run against the existing tag. Every step is
  idempotent (`skip-existing: true` on both indexes, release created only
  if missing), so the maintainer never needs to diagnose how far the
  original run got.

On push events `inputs.tag` evaluates to the empty string, so all
conditions below behave correctly for both trigger types.

### Job changes

**`semantic-release`** gains `if: inputs.tag == ''`.

**`publish`:**

- Condition becomes
  `!cancelled() && (inputs.tag != '' || needs.semantic-release.outputs.released == 'true')`.
  `!cancelled()` lets the job run after a *skipped* semantic-release; if
  semantic-release *fails* in normal mode, the second clause is false and
  publish still skips.
- Job-level env
  `RELEASE_TAG: ${{ inputs.tag != '' && inputs.tag || format('v{0}', needs.semantic-release.outputs.version) }}`.
  The checkout step uses it as `ref`; the smoke test derives
  `VERSION="${RELEASE_TAG#v}"` instead of reading the semantic-release
  output directly.
- The real-PyPI step's `if: github.event_name != 'workflow_dispatch'` is
  deleted. The publish steps are now identical in both modes.
- A nonexistent ref makes the checkout step fail immediately with
  "couldn't find remote ref". Checkout alone is not sufficient
  validation — it accepts any ref (branch, SHA), and a non-tag input
  would build from an unintended ref and fail confusingly later (or,
  for a branch named like a tag, publish it). A validation step
  immediately after checkout asserts that `RELEASE_TAG` resolves to an
  existing tag and that the checked-out HEAD is that tag's commit
  (checkout prefers branches on ambiguous names), failing fast with a
  clear message otherwise.

**`create-release`:**

- Condition becomes `!cancelled() && needs.publish.result == 'success'`
  (publish succeeding already implies one of the two modes was live).
- Checkout ref uses the same `RELEASE_TAG` expression.
- The `gh release create` step becomes idempotent: check
  `gh release view "$RELEASE_TAG"` first, create only if missing.
- `--target "${{ github.sha }}"` is dropped: the tag always exists by
  this point, so `--target` is ignored in normal runs and misleading in
  republish runs (where `github.sha` is main's HEAD, not the tag commit).

### Maintainer procedure (republish)

1. Notice a tag exists but the version is missing from PyPI or GitHub
   Releases (release run failed after tagging).
2. Actions → Release → Run workflow (run from `main`), set `tag` to the
   existing tag, e.g. `v0.64.4`.
3. Verify as for a normal release: version on PyPI, GitHub Release
   present.

## Documentation

`dev-docs/release-sop.md` (currently a stub owned by open issue 130)
gains a focused "Manual triggers and publish recovery" section:

- The two dispatch modes and when to reach for the `tag` input.
- Step-by-step republish procedure and post-run verification.
- A prominent note that empty-input dispatch now performs a **real**
  release — the old stop-at-TestPyPI behavior is gone.

The rest of the SOP remains issue 130's scope.

## Testing and verification

Workflow logic cannot be unit-tested locally. Verification:

1. Local YAML sanity check (actionlint if available).
2. After merge, a live end-to-end test that is safe by construction:
   dispatch with the latest already-published tag. Every step no-ops
   gracefully (skip-existing on both indexes, smoke test passes, release
   view finds the existing release) and the run goes green — exercising
   the entire republish path without publishing anything. This doubles as
   the SOP's "how to verify" example.

## Out of scope

- The full release SOP (issue 130).
- CHANGELOG / `vcs_release` divergence (issue 136).
- Smoke-test emitter coverage (issue 137).
- PyPI environment protection check (issue 138).
