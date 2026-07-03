# Design: Update command reference pages for Options/Output/Diagnostics help restructuring (issue 128)

**Date:** 2026-07-03
**Issue:** 128

## Goal

Issue 115 restructured the `--help` output of `plcc-scan`, `plcc-parse`,
`plcc-rep`, `plcc-make`, and `plcc-diagram` into three named sections:
`Options:`, `Output:`, and `Diagnostics:`. None of these five reference pages
embed raw help text — each uses a single flat "Arguments and Options" table
instead — so nothing is factually stale, but the tables no longer mirror the
CLI's own grouping. This restructures each page's flags table to match.

## Scope

### Modified files

| File | Change |
| --- | --- |
| `docs/cli/commands/plcc-scan.md` | Split `## Arguments and Options` into `## Arguments`, `## Options`, `## Output`, `## Diagnostics` |
| `docs/cli/commands/plcc-parse.md` | Same split |
| `docs/cli/commands/plcc-rep.md` | Same split |
| `docs/cli/commands/plcc-make.md` | Split into `## Options`, `## Output`, `## Diagnostics` (no `## Arguments` — no positional args) |
| `docs/cli/commands/plcc-diagram.md` | Same split as `plcc-make.md` (no `## Arguments`) |

### Out of scope

- All other files under `docs/cli/commands/` — not touched by issue 115, no embedded help text or grouping to fix.
- Wording of existing flag descriptions — this is a regrouping, not a rewrite. Descriptions carry over unchanged.
- `## Usage`, `## Examples`, and command-specific trailing sections (`## Interactive mode`, `## Build levels`, `## Diagram types`, `## Startup and errors`) — untouched.

## New section structure

Each modified file replaces its old `## Arguments and Options` section with up
to four new H2 sections, in the same order the actual `--help` output uses:

1. `## Arguments` (scan, parse, rep only) — one table, column header `Argument`
2. `## Options` — one table, column header `Option`
3. `## Output` — one table, column header `Option`
4. `## Diagnostics` — one table, column header `Option`

All tables keep the existing `Description` column and existing row content;
rows are only regrouped, not reworded.

### Per-file breakdown

**`plcc-scan.md`**
- Arguments: `SOURCE`
- Options: `-h`/`--help`, `-s PATH`/`--spec=PATH`
- Output: `-t`/`--trace`, `-b`/`--banner`
- Diagnostics: `-v`, `--verbose-format=FMT`

**`plcc-parse.md`**
- Arguments: `SOURCE`
- Options: `-h`/`--help`, `-s PATH`/`--spec=PATH`
- Output: `-b`/`--banner`
- Diagnostics: `-v`, `--verbose-format=FMT`

**`plcc-rep.md`**
- Arguments: `SOURCE`
- Options: `-h`/`--help`, `-s PATH`/`--spec=PATH`
- Output: `-b`/`--banner` (description mentions target language, per current text)
- Diagnostics: `-v`, `--verbose-format=FMT`

**`plcc-make.md`**
- Options: `-h`/`--help`, `-s PATH`/`--spec=PATH`, `--through=LEVEL`
- Output: `-b`/`--banner`
- Diagnostics: `-v`, `--verbose-format=FMT`

**`plcc-diagram.md`**
- Options: `-h`/`--help`, `-s PATH`/`--spec=PATH`
- Output: `-b`/`--banner`
- Diagnostics: `-v`, `--verbose-format=FMT`

## Verification

- Run `pdm run mkdocs build --config-file mkdocs-dev.yml` (matches the check in
  `.github/workflows/docs.yml`) to confirm the docs still build cleanly.
- Manually diff each file's new tables against that command's actual
  `--help` output (`src/plcc/cmd/{scan,parse,rep,make,diagram}.py` docstrings)
  to confirm every flag is present, correctly grouped, and correctly ordered.
