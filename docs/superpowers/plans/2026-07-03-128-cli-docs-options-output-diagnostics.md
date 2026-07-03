# CLI Docs Options/Output/Diagnostics Restructuring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update the five CLI command reference pages affected by issue 115's `--help` restructuring so their flag tables mirror the CLI's own `Arguments`/`Options`/`Output`/`Diagnostics` grouping.

**Architecture:** Each of the 5 files gets its single `## Arguments and Options` table split into up to 4 new H2 sections (`## Arguments`, `## Options`, `## Output`, `## Diagnostics`), in the same order the actual `--help` text uses. Row content and wording are carried over unchanged — this is a regrouping, not a rewrite. No code changes; docs only.

**Tech Stack:** Markdown, MkDocs (`pdm run mkdocs build --config-file mkdocs-dev.yml`).

## Global Constraints

- Do not reword any existing flag description — only regroup rows into new section tables.
- Section order within each file must match the order sections appear in that command's actual `--help` output: Arguments (if any positional args), Options, Output, Diagnostics.
- Only commands touched by issue 115 are in scope: `plcc-scan`, `plcc-parse`, `plcc-rep`, `plcc-make`, `plcc-diagram`. No other file under `docs/cli/commands/` changes.
- Do not add `[skip ci]` to any commit message — CI already skips via `paths-ignore` for doc-only changes.
- Reference: spec at `docs/superpowers/specs/2026-07-03-128-cli-docs-options-output-diagnostics-design.md`.

---

### Task 1: Restructure `plcc-scan.md`

**Files:**
- Modify: `docs/cli/commands/plcc-scan.md`

**Interfaces:** None — standalone documentation edit.

- [ ] **Step 1: Replace the `## Arguments and Options` section**

Replace this block:

```markdown
## Arguments and Options

| Argument/Option | Description |
|---|---|
| `SOURCE` | Source files to tokenize. Reads stdin if none given. |
| `-s PATH`, `--spec=PATH` | Spec file to build from. Remembered across invocations in the same directory. Defaults to `spec.plcc`. |
| `-t`, `--trace` | Show detailed scanning output including regex candidates and source lines. |
| `-b`, `--banner` | Print the plcc-ng version and spec path to stderr. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |
```

with:

```markdown
## Arguments

| Argument | Description |
|---|---|
| `SOURCE` | Source files to tokenize. Reads stdin if none given. |

## Options

| Option | Description |
|---|---|
| `-h`, `--help` | Show usage and exit. |
| `-s PATH`, `--spec=PATH` | Spec file to build from. Remembered across invocations in the same directory. Defaults to `spec.plcc`. |

## Output

| Option | Description |
|---|---|
| `-t`, `--trace` | Show detailed scanning output including regex candidates and source lines. |
| `-b`, `--banner` | Print the plcc-ng version and spec path to stderr. |

## Diagnostics

| Option | Description |
|---|---|
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |
```

- [ ] **Step 2: Diff against the actual `--help` output**

Run: `plcc-scan --help` (or read the `__doc__` string in `src/plcc/cmd/scan.py:120-136`)
Expected: every flag in the new tables appears in the same section (`Options:`/`Output:`/`Diagnostics:`) as in the real output, and no flag is missing or duplicated.

- [ ] **Step 3: Build the docs site**

Run: `pdm run mkdocs build --config-file mkdocs-dev.yml`
Expected: build completes with no errors or warnings referencing `plcc-scan.md`.

- [ ] **Step 4: Commit**

```bash
git add docs/cli/commands/plcc-scan.md
git commit -m "docs(cli): split plcc-scan reference into Options/Output/Diagnostics sections"
```

---

### Task 2: Restructure `plcc-parse.md`

**Files:**
- Modify: `docs/cli/commands/plcc-parse.md`

**Interfaces:** None — standalone documentation edit.

- [ ] **Step 1: Replace the `## Arguments and Options` section**

Replace this block:

```markdown
## Arguments and Options

| Argument/Option | Description |
|---|---|
| `SOURCE` | Source files to parse. Reads stdin if none given. |
| `-s PATH`, `--spec=PATH` | Spec file to build from. Remembered across invocations in the same directory. Defaults to `spec.plcc`. |
| `-b`, `--banner` | Print the plcc-ng version and spec path to stderr. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |
```

with:

```markdown
## Arguments

| Argument | Description |
|---|---|
| `SOURCE` | Source files to parse. Reads stdin if none given. |

## Options

| Option | Description |
|---|---|
| `-h`, `--help` | Show usage and exit. |
| `-s PATH`, `--spec=PATH` | Spec file to build from. Remembered across invocations in the same directory. Defaults to `spec.plcc`. |

## Output

| Option | Description |
|---|---|
| `-b`, `--banner` | Print the plcc-ng version and spec path to stderr. |

## Diagnostics

| Option | Description |
|---|---|
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |
```

- [ ] **Step 2: Diff against the actual `--help` output**

Run: `plcc-parse --help` (or read `src/plcc/cmd/parse.py:21-32`)
Expected: every flag in the new tables appears in the same section as in the real output; nothing missing or duplicated. Note `plcc-parse` has no `--trace` flag — `Output` contains only `-b`/`--banner`.

- [ ] **Step 3: Build the docs site**

Run: `pdm run mkdocs build --config-file mkdocs-dev.yml`
Expected: build completes with no errors or warnings referencing `plcc-parse.md`.

- [ ] **Step 4: Commit**

```bash
git add docs/cli/commands/plcc-parse.md
git commit -m "docs(cli): split plcc-parse reference into Options/Output/Diagnostics sections"
```

---

### Task 3: Restructure `plcc-rep.md`

**Files:**
- Modify: `docs/cli/commands/plcc-rep.md`

**Interfaces:** None — standalone documentation edit.

- [ ] **Step 1: Replace the `## Arguments and Options` section**

Replace this block:

```markdown
## Arguments and Options

| Argument/Option | Description |
|---|---|
| `SOURCE` | Source files to evaluate. Omit (or pass `-`) to enter interactive mode. |
| `-s PATH`, `--spec=PATH` | Spec file to build from. Remembered across invocations in the same directory. Defaults to `spec.plcc`. |
| `-b`, `--banner` | Print the plcc-ng version, spec path, and target language to stderr. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |
```

with:

```markdown
## Arguments

| Argument | Description |
|---|---|
| `SOURCE` | Source files to evaluate. Omit (or pass `-`) to enter interactive mode. |

## Options

| Option | Description |
|---|---|
| `-h`, `--help` | Show usage and exit. |
| `-s PATH`, `--spec=PATH` | Spec file to build from. Remembered across invocations in the same directory. Defaults to `spec.plcc`. |

## Output

| Option | Description |
|---|---|
| `-b`, `--banner` | Print the plcc-ng version, spec path, and target language to stderr. |

## Diagnostics

| Option | Description |
|---|---|
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |
```

- [ ] **Step 2: Diff against the actual `--help` output**

Run: `plcc-rep --help` (or read `src/plcc/cmd/rep.py:22-33`)
Expected: every flag in the new tables appears in the same section as in the real output; nothing missing or duplicated.

- [ ] **Step 3: Build the docs site**

Run: `pdm run mkdocs build --config-file mkdocs-dev.yml`
Expected: build completes with no errors or warnings referencing `plcc-rep.md`.

- [ ] **Step 4: Commit**

```bash
git add docs/cli/commands/plcc-rep.md
git commit -m "docs(cli): split plcc-rep reference into Options/Output/Diagnostics sections"
```

---

### Task 4: Restructure `plcc-make.md`

**Files:**
- Modify: `docs/cli/commands/plcc-make.md`

**Interfaces:** None — standalone documentation edit.

- [ ] **Step 1: Replace the `## Arguments and Options` section**

Replace this block:

```markdown
## Arguments and Options

| Option | Description |
|---|---|
| `-s PATH`, `--spec=PATH` | Spec file to build from. Remembered across invocations in the same directory. Defaults to `spec.plcc` on first use. |
| `--through=LEVEL` | Build up to this level: `scan`, `parse`, `model`, or `all`. Default: `all`. |
| `-b`, `--banner` | Print the plcc-ng version and spec path to stderr. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |
```

with (no `## Arguments` section — `plcc-make` takes no positional arguments):

```markdown
## Options

| Option | Description |
|---|---|
| `-h`, `--help` | Show usage and exit. |
| `-s PATH`, `--spec=PATH` | Spec file to build from. Remembered across invocations in the same directory. Defaults to `spec.plcc` on first use. |
| `--through=LEVEL` | Build up to this level: `scan`, `parse`, `model`, or `all`. Default: `all`. |

## Output

| Option | Description |
|---|---|
| `-b`, `--banner` | Print the plcc-ng version and spec path to stderr. |

## Diagnostics

| Option | Description |
|---|---|
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |
```

- [ ] **Step 2: Diff against the actual `--help` output**

Run: `plcc-make --help` (or read `src/plcc/cmd/make.py:28-39`)
Expected: every flag in the new tables appears in the same section as in the real output; nothing missing or duplicated. The `## Build levels` section further down the file is unaffected and must remain unchanged.

- [ ] **Step 3: Build the docs site**

Run: `pdm run mkdocs build --config-file mkdocs-dev.yml`
Expected: build completes with no errors or warnings referencing `plcc-make.md`.

- [ ] **Step 4: Commit**

```bash
git add docs/cli/commands/plcc-make.md
git commit -m "docs(cli): split plcc-make reference into Options/Output/Diagnostics sections"
```

---

### Task 5: Restructure `plcc-diagram.md`

**Files:**
- Modify: `docs/cli/commands/plcc-diagram.md`

**Interfaces:** None — standalone documentation edit.

- [ ] **Step 1: Replace the `## Arguments and Options` section**

Replace this block:

```markdown
## Arguments and Options

| Option | Description |
|---|---|
| `-s PATH`, `--spec=PATH` | Spec file. Remembered across invocations. Defaults to `spec.plcc`. |
| `-b`, `--banner` | Print the plcc-ng version and spec path to stderr. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |
```

with (no `## Arguments` section — `plcc-diagram` takes no positional arguments):

```markdown
## Options

| Option | Description |
|---|---|
| `-h`, `--help` | Show usage and exit. |
| `-s PATH`, `--spec=PATH` | Spec file. Remembered across invocations. Defaults to `spec.plcc`. |

## Output

| Option | Description |
|---|---|
| `-b`, `--banner` | Print the plcc-ng version and spec path to stderr. |

## Diagnostics

| Option | Description |
|---|---|
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |
```

- [ ] **Step 2: Diff against the actual `--help` output**

Run: `plcc-diagram --help` (or read `src/plcc/cmd/diagram.py:16-27`)
Expected: every flag in the new tables appears in the same section as in the real output; nothing missing or duplicated. The `## Diagram types` section further down the file is unaffected and must remain unchanged.

- [ ] **Step 3: Build the docs site**

Run: `pdm run mkdocs build --config-file mkdocs-dev.yml`
Expected: build completes with no errors or warnings referencing `plcc-diagram.md`.

- [ ] **Step 4: Commit**

```bash
git add docs/cli/commands/plcc-diagram.md
git commit -m "docs(cli): split plcc-diagram reference into Options/Output/Diagnostics sections"
```

---

### Task 6: Full verification and close issue 128

**Files:**
- Modify: `dev-docs/roadmap.md`
- Move: `dev-docs/issues/128-docs-help-options-output-diagnostics.md` → `dev-docs/issues/done/128-docs-help-options-output-diagnostics.md`

**Interfaces:** None — standalone documentation edit.

- [ ] **Step 1: Full docs build**

Run: `pdm run mkdocs build --config-file mkdocs-dev.yml`
Expected: clean build, no errors or warnings, across all 5 modified files.

- [ ] **Step 2: Full unit test baseline (confirm no regression)**

Run: `bin/test/units.bash`
Expected: same pass count as the pre-work baseline (1175 passed, 1 skipped) — this task touches no source code, so the count must not change.

- [ ] **Step 3: Move the issue file to `done/`**

```bash
git mv dev-docs/issues/128-docs-help-options-output-diagnostics.md dev-docs/issues/done/128-docs-help-options-output-diagnostics.md
```

- [ ] **Step 4: Update the roadmap**

In `dev-docs/roadmap.md`, remove the `#128` bullet (lines 9-10) from the `### Docs` section:

```markdown
- **[#128](issues/128-docs-help-options-output-diagnostics.md) — Update command reference pages for Options/Output/Diagnostics help restructuring**
  Issue 115 reorganized `--help` output; command reference pages may be stale.

```

and change the open-issue count on line 3 from:

```markdown
10 open issues as of 2026-07-03.
```

to:

```markdown
9 open issues as of 2026-07-03.
```

- [ ] **Step 5: Commit**

```bash
git add dev-docs/roadmap.md dev-docs/issues/done/128-docs-help-options-output-diagnostics.md
git commit -m "docs(issues): close issue 128 (CLI docs Options/Output/Diagnostics), update roadmap"
```
