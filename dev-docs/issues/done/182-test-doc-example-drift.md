# 182 - Nothing executes the examples in docs/, so they drift silently

**Type:** test
**Date:** 2026-08-03

## Description

No test in this repository runs any example from `docs/`. A specification in
the documentation can stop working — or keep working while printing something
other than what the page claims — and every tier stays green. #181 is what
that costs: three broken examples shipped in 2.0.0 and survived a release.

Two structural gaps let it happen:

1. **Nothing runs doc examples.** `grep -rl 'docs/' tests/` matches only the
   issue-tooling tests. Correctness of a doc example rests entirely on whoever
   edits it remembering to run it by hand.

2. **Docs-only PRs skip CI entirely.** `.github/workflows/ci.yml` sets
   `paths-ignore` on `docs/**`, `*.md`, and `mkdocs.yml`. So even if a doc test
   existed in the normal suite, it would not run on the PRs most likely to
   break an example.

Statically-typed targets are partly self-defending — Java's `_run()` signature
change could not compile, which is why every Java tab got fixed. Python and
JavaScript examples fail only at runtime, and only if something runs them.

## Notes

Design: `dev-docs/specs/2026-08-03-doc-example-drift-design.md`.

Approach is a runnable fixture per doc example plus two independent checks: a
bats tier that runs the fixture through the real CLI and asserts the output the
page documents, and a fast pytest check that the fenced block in the `.md` is
byte-identical to the fixture. Drift in either direction fails. A dedicated
workflow triggered on doc paths closes gap 2 without making every docs-only PR
run the full suite.

Deliberately out of scope, worth separate issues:

- `docs/language-guide/{index,examples}.md` and `docs/quick-start.md` show only
  Python and Java tabs though four targets are supported.
- The four `docs/language-guide/languages/*.md` quick-reference specs are
  correct today but equally able to drift.
