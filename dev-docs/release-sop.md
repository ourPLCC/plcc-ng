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
   An input that is not an existing tag (a typo, or a branch name)
   fails immediately at a validation step right after checkout.
4. Verify: the version appears on <https://pypi.org/project/plcc-ng/>
   and the GitHub Release exists.

### Safe end-to-end test of the republish path

Dispatch with the **latest already-published** tag. Every step no-ops
gracefully and the run goes green without publishing anything. Do this
after any change to the publish jobs.
