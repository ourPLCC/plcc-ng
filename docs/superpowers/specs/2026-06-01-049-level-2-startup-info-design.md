# Design: Issue 049 — Level-2 Startup Info

**Date:** 2026-06-01
**Issue:** [049-level-2-startup-info](../../../issues/049-level-2-startup-info.md)

## Problem

When a student runs `plcc-scan`, `plcc-parse`, or `plcc-rep`, there is no immediate
confirmation of which grammar file is active or which version of plcc is running. This
causes the class of confusion described in issues 038 and 046: wrong grammar silently in
use, wrong version installed, no obvious way to verify what is actually running.

## Decisions

- **Always print** — no `--quiet` / `-q` flag. Startup output is always visible.
- **After make** — printed after `plcc-make` returns successfully, so the grammar path
  in `build/.grammar` is already resolved.
- **stdout** — consistent with issue 039's decision that all user-facing output goes to
  stdout.
- **`plcc-rep` tool line** — `Running <tool> with <language>.` using the tool section
  name and language from the spec. Does not attempt to reconstruct the raw subprocess
  command.

## Output Format

`plcc-scan` and `plcc-parse`:

```text
plcc-ng 1.2.3  grammar: /abs/path/to/grammar.plcc
```

`plcc-rep` (two lines):

```text
plcc-ng 1.2.3  grammar: /abs/path/to/grammar.plcc
Running calc with python.
```

The grammar path is read from `build/.grammar` (written by the sticky-grammar system in
issue 046). The version comes from `plcc.version.get_version()`.

## Approach

Shared helper in `output.py`; each command calls it after make succeeds.

**Rejected alternatives:**

- *Inline in each `main()`* — duplicates `get_version()` + `read_grammar()` in three
  places with no benefit.
- *Pipe grammar path back through `plcc-make` stdout* — changes `plcc-make`'s interface
  unnecessarily; `build/.grammar` is already the canonical source.

## Implementation

### `src/plcc/cmd/output.py`

Add:

```python
def print_startup_banner(grammar_path, version, tool=None, language=None):
    print(f"plcc-ng {version}  grammar: {grammar_path}", flush=True)
    if tool is not None and language is not None:
        print(f"Running {tool} with {language}.", flush=True)
```

### `src/plcc/cmd/scan.py`, `parse.py`

After the `make_result.returncode != 0` guard:

```python
import os
from plcc.version import get_version
from plcc.build.grammar import read_grammar
from .output import print_startup_banner
...
grammar_path = os.path.abspath(read_grammar('build'))
print_startup_banner(grammar_path, get_version())
```

`read_grammar` returns the raw stored path (possibly relative). `os.path.abspath` resolves
it to an absolute path so there is no ambiguity about which file is in use.

### `src/plcc/cmd/rep.py`

After `_resolve_tool()` returns `tool_name` and `language`:

```python
grammar_path = os.path.abspath(read_grammar('build'))
print_startup_banner(grammar_path, get_version(), tool=tool_name, language=language)
```

## Testing

Each command's existing test file already has `stub_make`, `monkeypatch`, `tmp_path`,
and `capsys` fixtures. New tests:

- Monkeypatch `get_version` to return a fixed string (e.g. `"1.2.3"`).
- Write `build/.grammar` with a known path.
- Call `main([])` and assert the banner line appears in captured stdout.
- For `rep_test.py`, also assert `Running <tool> with <language>.` appears.

No new test infrastructure required.
