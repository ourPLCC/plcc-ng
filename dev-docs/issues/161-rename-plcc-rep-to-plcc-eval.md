# 161 - Consider renaming plcc-rep to plcc-eval for phase-naming consistency

**Type:** feat
**Date:** 2026-07-22

## Description

The three plcc-ng CLI tools are named inconsistently relative to the phases
of language processing they perform:

- `plcc-scan` — named after the phase (lexical analysis / scanning)
- `plcc-parse` — named after the phase (syntactic analysis / parsing)
- `plcc-rep` — named after the *interaction mode* (REPL), not the phase
  (semantic analysis / evaluation)

This came up while onboarding to the plcc-ng-demo repo: before reading its
`03-semantic/README.md`, the reader guessed the third tool would be called
`plcc-run` by analogy with a scan → parse → run pipeline, and was wrong —
it's `plcc-rep`. `rep` names the fact that the tool loops
read-eval-print-style, which is true, but it doesn't tell a newcomer which
phase of language processing it belongs to, breaking the pattern the other
two tool names establish.

Renaming `plcc-rep` to `plcc-eval` would restore the pattern:
`plcc-scan` → `plcc-parse` → `plcc-eval`, each named after its phase
(lexical, syntactic, semantic/evaluation), with the REPL behavior remaining
an implementation detail of how `plcc-eval` runs rather than part of its
name.

## Notes

- Two ways to do this, with different classifications:
  - **Hard rename** (drop `plcc-rep`, ship only `plcc-eval`): breaking for
    anyone with `plcc-rep` in muscle memory, scripts, or course materials
    (including plcc-ng-demo's `03-semantic/README.md` and
    `solution/README.md`, which would need updating in lockstep). Not a
    plain `feat` — needs a breaking-change marker (`feat!` / `BREAKING
    CHANGE:` footer) so semantic-release cuts a major version, not a minor
    one.
  - **Alias** (keep `plcc-rep` working, add `plcc-eval` as a synonym):
    purely additive, non-breaking — a plain `feat`. Newcomers get the
    phase-consistent name to guess at (as happened, incorrectly, with
    `plcc-run`), existing muscle memory and scripts keep working, and the
    docs can migrate to `plcc-eval` as the primary name over time while
    `plcc-rep` quietly remains as a deprecated-but-working alias.
  - The alias approach gets most of the discoverability benefit without
    forcing a major version bump or breaking anyone immediately — probably
    the better starting point, with a hard rename (and removal of the
    alias) reserved for a later major version if ever.
- Not urgent — `plcc-rep` is accurate and "REPL" is well-understood PL
  vocabulary — but if the project revisits CLI naming, `plcc-eval` (not
  `plcc-run`) is the name that best matches the existing `scan`/`parse`
  convention.
- Originally filed as issue #5 in `ourPLCC/plcc-ng-demo`.
