# Roadmap

## Open Issues

### Fix

- **[#160](issues/160-concurrent-plcc-build-dir-race.md) — Concurrent plcc-scan/plcc-make invocations race on shared build dir**
  Two CLI invocations sharing the same `./plcc-ng/` build dir race on temp-file creation/cleanup and crash with a raw `FileNotFoundError` traceback instead of a friendly error.
- **[#186](issues/186-rep-deadlocks-on-partial-stdout-line.md) — plcc-rep deadlocks on a partial stdout line**
  A semantic action that writes without a trailing newline merges with the JSON result line, so `_read_response` destroys the result and blocks forever — exit 124, no stdout, no stderr.
- **[#190](issues/190-rep-kills-session-on-program-errors.md) — A program error kills the plcc-rep session and blames the specification**
  Any exception a semantic action raises that is not a `LanguageError` becomes a `specification_error`, so one bad input ends the session and tells the user to go fix a specification that is not at fault.
- **[#191](issues/191-rep-reports-resource-exhaustion-as-specification-error.md) — Interpreter resource exhaustion is reported as a specification error**
  Exhausting the target runtime's call stack reads as `Specification error: RecursionError`, and the ceiling differs about eightfold between Python and the other targets, so the same program is fine on two of them.
- **[#192](issues/192-syntax-diagram-empty-alternative-invalid-ebnf.md) — Syntax diagram emits invalid EBNF for empty alternatives**
  A grammar with an empty alternative produces a dangling `|` that PlantUML rejects, so `syntax.png` is an error image while `plcc-diagram` still exits 0 — and the empty alternative is the standard LL(1) list idiom the tool's own conflict message recommends.

### Feat

- **[#161](issues/161-rename-plcc-rep-to-plcc-eval.md) — Consider renaming plcc-rep to plcc-eval for phase-naming consistency**
  `plcc-rep` is named after its interaction mode (REPL), not its phase, breaking the `scan`/`parse`/`?` naming pattern; an alias or rename to `plcc-eval` would restore it.
- **[#187](issues/187-rep-lacks-output-and-clean-exit-records.md) — plcc-rep lacks output and clean-exit record kinds**
  Semantic actions have no supported channel for user-visible output and no way to end the session cleanly, so output must be buffered into the result and a deliberate `exit` reads as a crash.

### Docs

- **[#185](issues/185-rep-parses-each-source-independently.md) — plcc-rep parses each SOURCE independently, unlike PLCC's `rep`**
  Old PLCC's `rep` joined its file arguments into one stream; plcc-ng parses each separately, so a program split across two files no longer parses — an undocumented breaking change.

### Test

- **[#184](issues/184-docs-tier-followups.md) — Follow-ups left open by the docs example tier**
  Six non-blocking observations from the #181/#182/#183 reviews: the strict gate re-enumerates `mkdocs.yml`'s plugin list, plus five diagnostics and test-hygiene items.

### Chore

- **[#154](issues/154-update-python-semantic-release.md) — Update python-semantic-release**
  Pinned to 9.x (locked 9.21.2); latest is 10.5.3. Dev-only dependency, consider updating.
- **[#156](issues/156-mkdocs-1x-successor-decision.md) — Decide our MkDocs 1.x successor**
  mkdocs-material hard-pins mkdocs<2; mkdocs-kroki-plugin already pulls in properdocs. Not urgent yet, but we'll need to pick ProperDocs, Zensical, or stay pinned once MkDocs 1.x actually breaks.
- **[#189](issues/189-align-issue-system-with-languages-ng.md) — Adopt the languages-ng issue-system shape: issues never move, status is frontmatter**
  Moving issues to `done/` on close keeps breaking links (14 are broken right now, despite #150's rewriting); making `closed:` a frontmatter date instead deletes the bug class and the machinery guarding it.
