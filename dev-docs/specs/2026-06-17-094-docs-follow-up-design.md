# Design: Issue 094 Docs Follow-Up

**Date:** 2026-06-17
**Issue:** 094 — Docs status after initial documentation branch

## Summary

Four targeted changes to close out the remaining follow-up items identified in
issue 094. Instructor-guide placeholder pages are out of scope; those will be
addressed separately.

## Changes

### 1. `dev-docs/issues/093-incremental-parsing-repl.md`

Add a **Docs responsibility** section noting that when 093 lands, it must
update `cli/orchestrators.md`: resolve the `<!-- TODO: verify how to suppress
interactive mode -->` comment and update the `< /dev/null` example if the
behavior changes.

### 2. `cli/primitives.md` — add `plcc-ll1` section and fix `plcc-trees`

`plcc-ll1` is an undocumented primitive. It reads spec JSON from stdin (the
output of `plcc-spec`) and emits LL(1) analysis JSON to stdout. Add it as a
proper section in `primitives.md`, ordered between `plcc-tokens` and
`plcc-trees` (its natural pipeline position).

Remove the `<!-- TODO: document how to obtain LL1_JSON -->` comment from
`plcc-trees` and add a pipeline example showing `plcc-spec` → `plcc-ll1` →
`plcc-trees`.

### 3. `cli/orchestrators.md` — remove `--tool` from `plcc-rep` (095)

- Remove the `--tool=NAME` row from the plcc-rep options table.
- Remove `--tool=subtract` from the plcc-rep examples.
- Leave the `<!-- TODO: verify how to suppress interactive mode -->` comment
  untouched; 093 owns that.

### 4. `language-guide/examples.md` — full pass for 089 + 095, verify output

Four sub-changes:

**a. Spec file content (089 + 095)**
- Update the spec file shown in the example to use the 095 semantic section
  format: bare `%` divider, language name (`Python`) on its own line as the
  first line of the semantic section, `%%%` block delimiters.
- Remove any stray `%` or old `% toolname Language` divider line left from the
  old format.

**b. CLI commands (089)**
- Replace `-g subtract.plcc` with `-s subtract.plcc` in all four commands
  (`plcc-make`, `plcc-scan`, `plcc-parse`, `plcc-rep`).

**c. Remove `--tool` flag (095)**
- Remove `--tool=subtract` from the `plcc-rep` command.

**d. Verify and replace output blocks**
- Run each command against the subtract example and replace every
  `<!-- TODO: verify ... -->` output block with real, verified output.
- Commands to run (in the worktree):
  1. `plcc-make -s subtract.plcc`
  2. `plcc-scan -s subtract.plcc samples`
  3. `plcc-parse -s subtract.plcc samples`
  4. `plcc-rep -s subtract.plcc samples < /dev/null`

## Out of scope

- `instructor-guide/index.md`, `instructor-guide/evaluating.md`,
  `instructor-guide/adopting.md` — placeholder pages; tracked separately.
- Any other doc pages not listed above.
