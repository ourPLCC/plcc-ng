# Release SOP

Standard operating procedure for releasing plcc-ng: how a release
happens, how to cut one, how to verify it landed, and how to recover
when a run fails.

## How a release happens

Releases are fully automated. Merging releasable conventional commits
to `main` **is** the release — no human bumps a version, tags, or
uploads anything. Two workflows do everything:

- `.github/workflows/release.yml` — runs on every push to `main`:
  semantic-release → build → TestPyPI → smoke test → PyPI → GitHub
  Release.
- `.github/workflows/docs.yml` — deploys versioned docs when the
  GitHub Release is published.

python-semantic-release decides the version from the
conventional-commit types on `main` since the last tag
(`major_on_zero = false` — the project is pre-1.0):

| Commits since the last tag include | Next version |
|---|---|
| `feat:` | minor bump |
| `fix:` or `perf:` | patch bump |
| a `BREAKING CHANGE:` footer or `!` after the type | minor bump (pre-1.0; major after v1.0) |
| only other types (`docs:`, `chore:`, `ci:`, `test:`, `refactor:`, …) | no release |

When nothing is releasable, the run ends quietly after the
semantic-release job. Otherwise the stages are:

1. **Semantic release** — computes the version, rewrites
   `CHANGELOG.md`, commits `chore(release): vX.Y.Z [skip ci]`, tags
   `vX.Y.Z`, and pushes both to `main`.
2. **Publish to PyPI** — checks out the tag, builds the wheel
   (`bin/build/package.bash`), uploads to TestPyPI, installs from
   TestPyPI into a clean venv and runs `bin/test/smoke.bash`
   (`plcc-make` plus all four emitters), then uploads to PyPI. Runs
   under the `pypi` GitHub Environment (see Reference).
3. **Create GitHub Release** — creates the release for the tag, with
   notes extracted from the tag's `CHANGELOG.md` section (see
   Reference).
4. **Docs deploy** — the `release: published` event triggers
   `docs.yml`, which runs `mike deploy --update-aliases X.Y latest`
   and publishes the versioned docs site.

## Cutting a release

1. **Before merging to `main`:** confirm CI is green on the branch,
   and that the branch's commit types produce the bump you expect
   (table above).
2. **Merge.** Watch the run under **Actions → Release**.
3. **If a stage fails**, nothing after it ran. Find the failed stage:

   | Failed stage | State it leaves | Recovery |
   |---|---|---|
   | Semantic release | No tag, nothing published. | Fix the cause, then **Re-run failed jobs** on the same run. (A *fresh* run would find no releasable commits if the release commit was already pushed.) |
   | Publish: build / TestPyPI / smoke test | Tagged, nothing on PyPI. | A smoke-test failure means the wheel is broken — fix forward with a new release. For transient failures, **Re-run failed jobs** or use the republish dispatch (Recovery below). |
   | Publish: PyPI upload | Tagged and on TestPyPI, not on PyPI. | Republish dispatch (Recovery below); every step is idempotent. |
   | Create GitHub Release | On PyPI, no GitHub Release. | Republish dispatch (Recovery below); the publish steps no-op. |
   | Docs deploy (`docs.yml`) | Release complete, docs stale. | "Deployment failed, try again later" from Pages is a transient GitHub backend error — re-run the docs workflow. |

4. **Verify** — next section.

## Verifying a release

From the repository root:

```bash
bin/release/verify.bash vX.Y.Z
```

The script fails fast with a `FAIL:` diagnostic. Check 4 needs a
python3 satisfying the package's `requires-python`; the script finds
one itself (ambient `python3`, else the project venv's — so run
`pdm install` once) and fails fast naming what it tried if neither
qualifies. `PLCC_VERIFY_PYTHON` overrides the search. Checks, in order:

1. PyPI serves `plcc-ng==X.Y.Z` on the simple index — the index pip
   installs from (retries briefly — it can lag the upload and it lags
   the JSON API).
2. The GitHub Release `vX.Y.Z` exists.
3. The docs site's `versions.json` lists `X.Y` and points the
   `latest` alias at it.
4. `pip install plcc-ng==X.Y.Z` from real PyPI into a throwaway venv,
   then `bin/test/smoke.bash` against the installed entry points. This
   is the only place the artifact served by real PyPI (rather than
   TestPyPI, which CI smoke-tests) is ever exercised.

`--no-install` skips check 4 — useful for cheaply re-checking the
observational state. In particular, `docs.yml` starts only after the
GitHub Release is published and takes a few minutes; a failing docs
check right after a release usually means it hasn't finished — re-run
with `--no-install` once it has. `PLCC_VERIFY_RETRY_DELAY` overrides
the retry delay in seconds (default 15).

Optionally, eyeball <https://ourplcc.github.io/plcc-ng/>: the version
switcher should show `X.Y` as `latest`.

## Recovery

If a run failed **before** the tag was created, there is nothing to
republish: fix the cause and use **Re-run failed jobs** on the same
run (see the table above). The procedures below are for runs that
failed **after** tagging.

### Manual triggers and publish recovery

The release workflow (`.github/workflows/release.yml`) runs
automatically on every push to `main`. It can also be run by hand:
**Actions → Release → Run workflow**, always from `main` (the selected
branch decides which version of the workflow file runs). The `tag`
input selects one of two modes.

#### Normal release (leave `tag` empty)

Identical to a push-triggered release: semantic-release computes the
next version from unreleased commits; if there is something to release
it tags, updates the CHANGELOG, builds, publishes to TestPyPI,
smoke-tests the TestPyPI install, publishes to PyPI, and creates the
GitHub Release. If nothing is releasable, the run ends after the
semantic-release job.

**This is a real release.** Manual runs used to stop at TestPyPI; that
behavior is gone. Do not dispatch with an empty `tag` to "test" the
workflow — use the republish mode below with an already-published tag
instead.

#### Republish an existing tag (set `tag`, e.g. `v0.64.4`)

Use this when a release run failed *after* tagging: the tag exists,
but the version is missing from PyPI and/or GitHub Releases, and
re-running the workflow does nothing because semantic-release finds no
new releasable commits. This works regardless of why or when the
original run failed — including workflow bugs fixed since (the run
uses the workflow file from `main`, not from the failed run).

1. Confirm the state: the tag exists in the repo, but
   <https://pypi.org/project/plcc-ng/> lacks the version and/or the
   GitHub Release is missing (`bin/release/verify.bash --no-install`
   shows exactly which).
2. **Actions → Release → Run workflow** from `main`, set `tag` to the
   existing tag (with the leading `v`).
3. The run skips semantic-release, builds the wheel from the tag, and
   reruns the whole publish path. Every step is idempotent —
   `skip-existing` on TestPyPI and PyPI, GitHub Release created (with
   notes from the tag's `CHANGELOG.md` section) only if missing — so
   there is no need to know how far the failed run got.
   An input that is not an existing tag (a typo, or a branch name)
   fails immediately at a validation step right after checkout.
4. Verify: run `bin/release/verify.bash` with the tag (see Verifying
   a release above).

#### Safe end-to-end test of the republish path

Dispatch with the **latest already-published** tag. Every step no-ops
gracefully and the run goes green without publishing anything. Do this
after any change to the publish jobs.

## Reference

### The `pypi` environment

The `publish` job in `.github/workflows/release.yml` runs under the
`pypi` GitHub Environment. Its protection configuration (Settings →
Environments → `pypi`; verified 2026-07-05 via the environments API,
which is anonymously readable for this public repo):

- **Deployment branch policy: `main` branch and `v*.*.*` tags.** A
  workflow dispatched from any other branch can never reach the publish
  job, so the "always from `main`" rule above is enforced in settings,
  not just prose.
- **No required reviewers — intentional.** Once conventional commits
  land on `main`, the pipeline runs to real PyPI with no manual
  approval step. The safeguards are the review that lands the commits
  on `main`, the TestPyPI publish + smoke test that precede the PyPI
  upload, and the branch policy above. A gate would trade release speed
  for an approval click on every release; if a bad release ships, the
  recovery is a follow-up release, not a gate. Revisit if the project
  gains maintainers who want a human checkpoint (issue 138 has the
  original analysis).

### GitHub Release notes

GitHub Release notes are the tag's `CHANGELOG.md` section, extracted by
[bin/release/extract-changelog.bash](../bin/release/extract-changelog.bash)
in the `create-release` job — the same conventional-commit content
python-semantic-release writes to the changelog, so the two never
diverge. There is deliberately no fallback to GitHub's PR-based
auto-notes: if extraction fails (e.g. a malformed changelog heading),
the `create-release` job fails. Fix the cause, then recover with the
republish dispatch above. Extraction only runs when the release is
missing, so republishing a tag that predates the script still no-ops
green.
The one gap: a pre-script tag whose GitHub Release is missing
(e.g. deleted) cannot be recreated by the workflow, because the checkout
at the tag lacks the script. Recover by hand: extract that version's
section from the tag's `CHANGELOG.md` and run
`gh release create <tag> --title <tag> --notes-file <file>`.
