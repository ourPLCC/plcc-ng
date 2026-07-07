# Design: Installation Page and Migration Guide from PLCC

**Issues:** 071 (upgrade instructions), 072 (version pinning), 102 (migration from PLCC)
**Date:** 2026-06-22

## Overview

Three related docs issues addressed together:

- Add `installation.md` covering pip install, upgrade, version pinning, and uninstall (issues 071, 072)
- Add `migration.md` — a checklist-driven guide for users migrating from the original PLCC tool (issue 102)
- Rename `getting-started.md` → `quick-start.md` and update its nav label to "Quick Start"
- Add a link from Quick Start to Installation for users who need more than the one-liner

## Files Changed

| File | Change |
|---|---|
| `docs/getting-started.md` → `docs/quick-start.md` | Rename; add link to `installation.md`; no other content changes |
| `docs/installation.md` | New page |
| `docs/migration.md` | New page |
| `mkdocs.yml` | Rename Getting Started entry, add Installation and Migration from PLCC entries |

## Navigation

```yaml
- Home: index.md
- Quick Start: quick-start.md
- Installation: installation.md
- Migration from PLCC: migration.md
- Language Guide: ...
- CLI: ...
- Instructor Guide: ...
- Changelog: changelog.md
```

`Installation` and `Migration from PLCC` are top-level peers sitting immediately after Quick Start.

---

## `quick-start.md`

Identical to the current `getting-started.md` except:

- Page title updated to "Quick Start" (or the existing title kept if it already differs from the filename)
- A note added below the `pip install plcc-ng` line:
  > For upgrade, version pinning, and uninstall instructions, see [Installation](installation.md).

---

## `installation.md`

### Structure

**Requirements**
- Python 3.12 or later
- Java JDK 21 or later (only needed if implementing semantics in Java)

**Install**
```bash
pip install plcc-ng
```
Verify with:
```bash
plcc-version
```

**Upgrade**
```bash
pip install --upgrade plcc-ng
```
Verify with `plcc-version`. Check the [Changelog](changelog.md) for breaking changes between versions.

**Pin a specific version**

Install a specific version:
```bash
pip install plcc-ng==X.Y.Z
```

Pin in `requirements.txt`:
```
plcc-ng==X.Y.Z
```

Pin in `pyproject.toml`:
```toml
[project]
dependencies = [
    "plcc-ng==X.Y.Z",
]
```

Check the currently installed version:
```bash
plcc-version
```

**Uninstall**
```bash
pip uninstall plcc-ng
```

### Extensibility

The page ends after Uninstall with no "coming soon" placeholders. Docker and DevContainer methods will be added as new top-level sections when they are ready. The intro sentence will note: "This page covers installing plcc-ng via pip. Additional installation methods will be documented here as they become available."

---

## `migration.md`

### Audience

Users of the original PLCC tool who want to port an existing project to PLCC-ng.

### Structure

**Why PLCC-ng?**
Short paragraph: PLCC-ng is a modern, pip-installable rewrite of PLCC. It adds Python semantics support, a cleaner CLI, and a more extensible architecture. It is not backward compatible — spec files and command invocations both require updates.

**Migration checklist**

Each step includes: what to change, why it changed, and a before/after code block or table.

1. **Install PLCC-ng**
   Replace the shell script, Docker, or DevContainer install with `pip install plcc-ng`.

2. **Rename your grammar file**
   PLCC default: `grammar`. PLCC-ng default: `spec.plcc`.

3. **Update regex patterns in the lexical section**
   PLCC uses Java regex (`java.util.regex.Pattern`). PLCC-ng uses Python regex (`re` module). Most common patterns are identical, but Java-specific syntax — e.g. `\p{Alpha}`, named groups with `(?<name>...)` — must be rewritten in Python equivalent syntax.

4. **Check scan algorithm behavior**
   PLCC gives skip rules priority over token rules when they match any input, regardless of match length. PLCC-ng uses pure first-longest-match — skip and token rules compete equally. Grammars that relied on skip-first behavior may need rule reordering.

   Before (PLCC — skip wins regardless of length):
   ```
   skip WORD '[a-z]+'
   token IF 'if'
   ```
   Given input `if`, PLCC emits nothing (skip wins). PLCC-ng emits `IF` (longest match wins; both match 2 chars, IF appears later but WORD is a skip so… actually need to verify exact PLCC-ng behavior here).

   > **Note to implementer:** Verify the exact PLCC-ng behavior for this case by reading `matcher_test.py` and `scanner_test.py` before writing this step. The description above is approximate.

5. **Update nonterminal names to PascalCase**
   PLCC nonterminals use lowercase: `<prog>`, `<exp>`. PLCC-ng uses PascalCase: `<Program>`, `<Expr>`.

6. **Update alternative/subclass syntax**
   PLCC: distinguishing name is a suffix after the closing bracket: `<exp>SubExp`
   PLCC-ng: distinguishing name is after a colon inside the brackets: `<Expr:SubExp>`

7. **Update captured field syntax**
   PLCC: field name is a suffix after the closing bracket: `<exp>exp1`, `<WHOLE>` captured as `whole`
   PLCC-ng: field name is after a colon inside the brackets: `<Expr:left>`, `<WHOLE:whole>`

   Before/after table:
   | PLCC | PLCC-ng |
   |---|---|
   | `<exp>exp1` | `<Expr:exp1>` |
   | `<WHOLE>` | `<WHOLE>` (auto-names field `whole`) |
   | `<WHOLE>` (explicit) | `<WHOLE:whole>` |

8. **Add semantic section language header**
   PLCC has no language header concept — it only supports Java. PLCC-ng requires the first non-blank line of the semantic section to declare the language: `Java` or `Python`.

   Before:
   ```
   %
   Prog
   %%%
   ```
   After:
   ```
   %
   Java
   
   Prog
   %%%
   ```

9. **Rename the entry point method**
   PLCC: `$run()`. PLCC-ng: `_run()`.

10. **Check `%include` paths**
    Both tools support `%include FILENAME`. No syntax change. However, if your include paths were relative to a file named `grammar`, update them for `spec.plcc` if needed.

11. **Replace commands**

    | PLCC | PLCC-ng | Notes |
    |---|---|---|
    | `plcc.py --version` | `plcc-version` | |
    | `plccmk [-c] [file]` | *(not needed)* | Top-level commands run generation automatically |
    | `scan` | `plcc-scan` | Token output format also changed (see below) |
    | `parse [-t] [-n]` | `plcc-parse` | Always shows parse tree; no `-t` flag needed |
    | `rep [-t] [-n]` | `plcc-rep` | |
    | `parse --json_ast` | `plcc-tokens \| plcc-trees` | For JSON parse trees, use the pipeline |

    Token output format change:
    - PLCC: `   1: WHOLE '3'`
    - PLCC-ng: `-:1:1 NUM '42'` (file:line:col)

**Features not yet in PLCC-ng**

- **Docker installation** — PLCC supported Docker via `plcc-con`. PLCC-ng is currently pip-only. Docker support is planned; see [issue link].
- **DevContainer** — PLCC provided a ready-to-use devcontainer image. PLCC-ng does not yet have one. It is planned; see [issue link].

> **Note to implementer:** Check whether open GitHub issues exist for Docker and DevContainer support and link to them here. If no issues exist, omit the links or create the issues first.

---

## Out of scope

- No changes to Language Guide, CLI reference, or Instructor Guide content
- No new issues created as part of this work (Docker/DevContainer issues are pre-existing or not yet filed)
