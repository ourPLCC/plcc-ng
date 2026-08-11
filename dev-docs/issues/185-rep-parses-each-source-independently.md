# 185 - plcc-rep parses each SOURCE independently, unlike PLCC's `rep`

**Type:** docs
**Date:** 2026-08-11

<!--
Classify by user-facing impact, not by whether something was "broken".
`fix` and `feat` bump the release version (see [tool.semantic_release]
in pyproject.toml); reserve them for changes to the shipped package
(src/). A bug in a test, script, or CI workflow (bin/, tests/,
.github/) is still a bug, but it's not user-facing — classify it
`test` or `chore` instead so it doesn't spin the version. `docs` is for
documentation content, and never bumps the version either way.
-->

## Description

`plcc-rep` parses each `SOURCE` argument as an independent token stream.
Old PLCC's `rep` joined its file arguments into a single stream, so a
program split across two files parsed as one program. Under plcc-ng the
same invocation fails.

This is not a defect — per-source parsing is the design issue
[#008](done/008-parse-multi-program-streaming.md) settled on ("Each source
is parsed independently, producing one or more trees per source"), and
[`SourceRunner.run`](../../src/plcc/cmd/source_runner.py) implements it
uniformly for `plcc-scan`, `plcc-parse`, and `plcc-rep`. But it is an
undocumented breaking change: [docs/migration.md](../../docs/migration.md)'s
command table maps `rep [-t] [-n] [file...]` → `plcc-rep [file...]` with an
empty notes column, which reads as "same behavior, new name."

Splitting one program across files is a real course-material pattern — an
exercise that hands students a partial program in one file and the
remainder in another — so this silently changes what an existing
demonstration does, and does it with a parse error rather than a diagnosis.

## Steps to Reproduce

1. With a spec for a simple expression language, put `+(3` in `p1` and
   `,4)` in `p2`:

   ```
   $ plcc-rep p1 p2
   plcc-parser-table: -:1:3: error: expected 'RPAREN', got end of file
   plcc-parser-table: -:1:1: error: unexpected 'COMMA', no production for 'Program'
   ```

2. Concatenating first works as expected:

   ```
   $ cat p1 p2 | plcc-rep
   7
   ```

## Notes

The minimum fix is documentation: add a **Breaking behavior changes** entry
and fill in the `rep` row's notes column in
[docs/migration.md](../../docs/migration.md), stating that each `SOURCE` is
its own token stream and that `cat f1 f2 | plcc-rep` reproduces the old
behavior. Issue
[#159](done/159-migration-guide-missing-breaking-changes-callout.md) is the
precedent for that shape.

Worth deciding at the same time whether the divergence is wanted at all for
`plcc-rep` specifically. `plcc-scan` and `plcc-parse` have a clear reason to
keep sources separate — their output is per-source records carrying a
`source` field. `plcc-rep`'s output is the *program's* result, where "these
files are one program" is at least as plausible a reading as "these files
are separate programs." If joining is the wanted behavior, it is a `feat` on
top of this docs entry, not a replacement for it: the divergence has already
shipped and still needs a migration-guide note.

Found while migrating a set of course languages to plcc-ng, where the
affected example is a two-file program built exactly this way.
