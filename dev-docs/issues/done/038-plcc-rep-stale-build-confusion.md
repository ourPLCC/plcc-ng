# 038 - plcc-rep silently uses default grammar.plcc with no indication of which build is active

**Type:** fix
**Date:** 2026-05-25

## Description

When a student runs `plcc-rep` without `--grammar-file`, it silently defaults to `grammar.plcc` in the current directory and runs whatever the build system produces. If the student was last testing with `plcc-scan` or `plcc-parse` using an explicitly named grammar file, they may not realize that `plcc-rep` is using a different grammar (or an old one) with no warning.

The confusion compounds because the REPL starts successfully — there is no error unless `grammar.plcc` is missing entirely.

## Steps to Reproduce

1. Run `plcc-rep --grammar-file=my_grammar.plcc` — REPL starts for `my_grammar.plcc`.
2. Run `plcc-scan --grammar-file=other_grammar.plcc` — scan stage built for `other_grammar.plcc`.
3. Run `plcc-rep` (no argument) — silently uses `grammar.plcc` (the default), which may be stale or unexpected.

## Notes

**What the staleness system does:**

`plcc-make` uses a content hash of `spec.json` plus a set of completed build stages stored in `build/.spec-hash`. When `plcc-rep` calls `plcc-make`, it requires stages `{scan, parse, model}` plus all tool stages. If those stages are not all present in the sentinel, it rebuilds. So the staleness system does correctly trigger a rebuild when stages are missing (e.g., after running only `plcc-scan`).

**What the staleness system cannot detect:**

The sentinel tracks the hash of `spec.json` content, not the grammar file path or name. If the user is working on a grammar with a non-default name and has never run `plcc-make --through=all` with `grammar.plcc`, the sentinel in `build/` reflects the last grammar that was fully built — which may not be `grammar.plcc`. There is also no record of which file the build was derived from, so the user cannot tell from the output whether they are running the grammar they intend.

**Possible fixes (needs design):**

- Print the resolved grammar file path and build status at startup (e.g., `plcc-rep: using grammar.plcc (build current)`).
- Store the grammar file path in the sentinel and warn if the current default grammar file differs from what was last built.
- Consider whether `--grammar-file` should be required (no default) to force the user to be explicit. This would be a breaking change.
- At minimum, the startup message could say which grammar is in use so the student can catch the mistake immediately.
