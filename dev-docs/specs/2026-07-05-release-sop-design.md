# Release SOP — design

**Issue:** [130](../issues/done/130-release-sop.md)
**Date:** 2026-07-05

## Problem

`dev-docs/release-sop.md` documents manual triggers, publish recovery, the `pypi`
environment, and release-notes extraction (accumulated from issues 134–138), but not what
issue 130 asks for: the normal release procedure end-to-end and a post-release verification
checklist. The release pipeline is now stable (issues 134, 135, 136, 137, 138, 140 all
closed), so this is the right time to write the SOP. Issue 112 lists "Release SOP is
complete and tested" as a v1.0 criterion.

One verification gap motivates a new script: CI smoke-tests the **TestPyPI** install
(all four emitters, via `bin/test/smoke.bash`), but nothing ever installs and exercises
the artifact served by **real PyPI**.

## Decision summary

- **Framing:** the SOP is an operator checklist ("how to cut and verify a release"), not a
  narrative of the workflows. The pipeline is fully automated — merging releasable
  conventional commits to `main` *is* the release — so the human steps are: check what a
  merge will release, watch the run, verify the result, recover if needed.
- **Structure:** one document, reorganized around the release lifecycle. Existing recovery
  and reference content is preserved, re-homed under later sections.
- **Verification:** a new `bin/release/verify.bash <tag>` script performs the post-release
  checks, including installing from real PyPI into a throwaway venv and running
  `bin/test/smoke.bash`. The SOP invokes the script rather than listing copy-paste commands.
- **Exercise:** issue 130 closes on this branch. The "exercise the SOP on a pre-1.0
  release" requirement moves to an explicit item in issue 112. Landing `verify.bash` as
  `feat(release)` (the same type `extract-changelog.bash` used) makes the merge of this
  branch releasable, which supplies the pre-1.0 release to exercise the SOP on.

## `dev-docs/release-sop.md` structure

1. **How a release happens** — merging releasable conventional commits to `main` is the
   release; no human step cuts a version. A table of commit types: `feat` → minor;
   `fix`/`perf` → patch; `BREAKING CHANGE` → minor while `major_on_zero = false`; all
   other types (`docs`, `chore`, `ci`, `test`, `refactor`, …) do not release. Names the
   two workflows once: `release.yml` (semantic-release → build → TestPyPI → smoke → PyPI →
   GitHub Release) and `docs.yml` (versioned docs via mike on `release: published`).
2. **Cutting a release** — the operator checklist: before merging, confirm CI is green and
   the branch's commit types produce the expected bump; merge; watch **Actions → Release**
   with a stage-by-stage table (job/step, what it does, what its failure means, which
   recovery procedure applies); then verify.
3. **Verifying a release** — run `bin/release/verify.bash <tag>`; optionally eyeball the
   docs site version switcher. Lists what the script checks so the SOP is meaningful
   without reading the script.
4. **Recovery** — the existing "Manual triggers and publish recovery" content essentially
   as-is, plus one addition: a run that fails *before* tagging is recovered with
   "Re-run failed jobs" on the same run; the republish dispatch is for
   tagged-but-not-published.
5. **Reference** — the existing `pypi` environment and GitHub Release notes sections,
   unchanged.

## `bin/release/verify.bash`

Interface: one required argument, the tag with leading `v` (e.g. `v0.64.4`) — the same
convention as the republish dispatch input. An optional `--no-install` flag runs only the
observational checks. No arguments, extra arguments, or a tag not shaped `vX.Y.Z` → usage
message on stderr, exit 1 (matching `extract-changelog.bash`).

Checks, in order, cheap first, fail-fast, with `OK:`/`FAIL:` lines in the
`bin/test/smoke.bash` style:

1. **PyPI has the version** — `curl -fsS https://pypi.org/pypi/plcc-ng/<version>/json`,
   with a short retry loop (the operator may run this moments after publish).
2. **GitHub Release exists** —
   `curl -fsS https://api.github.com/repos/ourPLCC/plcc-ng/releases/tags/<tag>`
   (anonymous API; deliberately `curl`, not `gh`).
3. **Versioned docs deployed** — fetch
   `https://ourplcc.github.io/plcc-ng/versions.json` (written by mike) and confirm the
   `major.minor` entry exists and carries the `latest` alias.
4. **Real-PyPI install + smoke** (skipped by `--no-install`) — `python -m venv` in a
   `mktemp -d` (trap cleanup), `pip install --no-cache-dir plcc-ng==<version>` with the
   same retry pattern, prepend the venv's `bin` to `PATH`, run `bin/test/smoke.bash`
   (which exercises `plcc-make` plus all four emitters).

Retry loops read their delay from `PLCC_VERIFY_RETRY_DELAY` (default 15 seconds) so
tests run fast. The script is deliberately **not** cached via `bin/test/_cache.bash`: like
`smoke.bash`, its result depends on external state, not git state — a comment says so.
Ends with `verify: all checks passed for v<version>`.

## Testing

`tests/bats/commands/release-verify.bats`, following the `release-extract-changelog.bats`
precedent. Checks 1–3 are made hermetic by stubbing `curl` via PATH injection — a fake
`curl` in a temp dir that returns canned responses per URL and logs every request.
Check 4 is not stubbed (faking `python -m venv` + pip + four emitters is test-induced
complexity); the full install path is covered by the real end-to-end exercise under
issue 112, the same tier philosophy as `smoke.bash` itself.

Coverage:

- Usage error on no/extra arguments; malformed tag rejected (missing `v`, not `X.Y.Z`).
- Each observational check failing → its specific `FAIL:` diagnostic, nonzero exit.
- Fail-fast: when the PyPI check fails, the GitHub and docs URLs are never requested
  (asserted via the stub's request log).
- `versions.json` logic: passes with the `major.minor` entry carrying `latest`; fails when
  the entry is missing; fails when `latest` is on a different version.
- Full success path via `--no-install` prints the summary line.
- Retry loop honors the delay-override environment variable.

TDD order per CONTRIBUTING: bats tests first, watch them fail via
`bin/test/commands.bash`, then the script.

## Bookkeeping

Commits on this branch, in order:

1. `docs(specs)` — this design doc.
2. `test(release)` — the bats tests (failing).
3. `feat(release)` — `verify.bash`; rides with a CONTRIBUTING.md addition: a "Release"
   command table listing `extract-changelog.bash` and `verify.bash` (CONTRIBUTING indexes
   `bin/` but has no Release section today). **Releasable on merge — intentional**; the
   resulting release is the SOP exercise opportunity.
4. `docs(release-sop)` — the restructured SOP.
5. `docs(issues)` — add the explicit exercise item to issue 112's notes: follow the SOP
   and run `bin/release/verify.bash` on a pre-1.0 release.
6. `bin/issues/close.bash 130`; verify with `bin/issues/check.bash`.
7. `docs(specs)` — repoint this spec's issue link at its `done/` path (same follow-up as
   issue 137).

No nav changes: `mkdocs-dev.yml` and `dev-docs/index.md` already link `release-sop.md`.
The roadmap update is handled by `close.bash`. After the final commit the branch is
pushed; the maintainer opens the PR.
