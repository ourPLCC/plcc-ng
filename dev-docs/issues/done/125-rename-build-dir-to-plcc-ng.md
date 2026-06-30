# 125 - Rename `build/` output directory to `plcc-ng/`

**Type:** refactor
**Date:** 2026-06-29

## Description

plcc-ng currently writes its generated output into a directory named `build/`. This is a very common name used by many build tools (Maven, Gradle, CMake, npm, etc.), which creates a risk of name collisions when plcc-ng is used alongside other tools in the same project. Renaming the output directory to `plcc-ng/` makes the ownership of that directory unambiguous.

## Notes

- Find all places in the codebase that reference `build/` as the output directory and update them to `plcc-ng/`
- Update any user-facing documentation that mentions `build/`
- This is a breaking change for users who depend on the `build/` path — note it in CHANGELOG
- Consider whether `.gitignore` templates or quickstart examples need updating

## Scope (as of 2026-06-29)

The string `'build'` is hardcoded independently in each command — there is no shared constant.

**Source (~8 files):**

- `src/plcc/cmd/make.py:60` — `build_dir = Path('build')` (the orchestrator; central point of change)
- `src/plcc/cmd/scan.py`, `parse.py`, `rep.py` — each hardcode `os.path.join('build', ...)` (2–4 hits each)
- `src/plcc/diagram/class_diagram/diagram.py`, `syntax_diagram/diagram.py` — 2–3 hits each
- `src/plcc/cmd/diagram.py:28` — `_RESERVED = frozenset({'emit', 'build', 'run', 'list'})` — verify whether this `'build'` is a reserved subcommand name (unrelated to the directory) or not

**Tests (~14 files):**

- ~11 pytest files with `tmp_path / "build"` path construction
- 3 bats files (`tests/bats/commands/plcc-make.bats`, `tests/bats/e2e/plcc-rep.bats`, `tests/bats/e2e/happy-path.bats`) with direct `build/` shell paths — need manual attention

**Docs (~10 files):**

- User-facing docs under `docs/cli/commands/` and `docs/migration.md`
- Historical superpowers plans/specs also contain `build/` but do not need updating

## Recommended approach

Introduce a single `OUTPUT_DIR = 'plcc-ng'` constant in a shared module and import it from every command. That reduces the rename to a 1-liner plus import updates and prevents future drift. Without it, the change is ~40 individual string replacements across source, tests, and docs.
