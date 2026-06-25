# Design: Improve docopts error messages for unrecognized and duplicate options (issue 116)

**Date:** 2026-06-25
**Issue:** 116

## Problem

When a user passes an unrecognized or duplicate option to any `plcc-*` command, docopt raises `DocoptExit` with a message that exposes its internal object representation:

```
Warning: found unmatched (duplicate?) arguments [Option('-x', None, 0, True)]
Usage: plcc-tokens [-v ...] [options] SPEC_JSON [SOURCE ...]
```

This is confusing because it says "Warning" instead of "error", uses "or" to hedge between two possibilities the user must resolve themselves, and leaks the `Option(...)` repr.

## Goal

Replace the cryptic message with a precise, user-facing error:

- Unrecognized option: `error: unrecognized option '-x'`
- Duplicate recognized option: `error: duplicate option '--trace'`

Both followed by the command's usage string. Exit code remains 1.

Other docopt error messages (e.g. missing required positional, which already produces a clean `Usage: ...` message) are left unchanged.

## Design

### New module: `src/plcc/cli.py`

Single public function `parse_args(doc, argv)` — a thin wrapper around `docopt()`.

```python
from docopt import docopt, DocoptExit, parse_options
import re, sys

def parse_args(doc, argv):
    try:
        return docopt(doc, argv)
    except DocoptExit as e:
        _reformat_if_cryptic(str(e), doc)
        raise SystemExit(str(e))

def _reformat_if_cryptic(msg, doc):
    m = re.search(r"Option\(([^)]+)\)", msg)
    if not m:
        return
    parts = [p.strip().strip("'") for p in m.group(1).split(",")]
    short, long_ = parts[0], parts[1]
    opt = long_ if long_ != "None" else short
    opts = parse_options(doc)
    known = {o.short for o in opts if o.short} | {o.longer for o in opts if o.longer}
    kind = "duplicate" if (short in known or long_ in known) else "unrecognized"
    usage = re.search(r"(Usage:.*)", msg, re.DOTALL)
    usage_str = usage.group(1) if usage else ""
    print(f"error: {kind} option '{opt}'\n{usage_str}", file=sys.stderr)
    raise SystemExit(1)
```

**How it works:**

1. On a successful parse, returns the args dict unchanged.
2. On `DocoptExit`, inspects the message for the `Option(...)` pattern.
3. If found: extracts the short and long names, checks them against `parse_options(doc)` to determine "unrecognized" vs "duplicate", prints the clean message to stderr, and exits 1.
4. If not found (clean docopt messages like missing positionals): falls through and re-raises the original `SystemExit` with the original message.

### Call-site migration

All ~30 files that currently call `docopt()` directly are updated:

```python
# Before
from docopt import docopt
args = docopt(__doc__, argv)

# After
from plcc.cli import parse_args
args = parse_args(__doc__, argv)
```

Files that also import `DocoptExit` for other purposes keep that import unchanged. Affected packages: `cmd/`, `diagram/`, `lang/`, `model/`, `ll1/`, `parser/`, `spec/`, `tokens/`, `tree/`.

### Testing

New file `src/plcc/cli_test.py` with five pytest unit tests:

| Case | Input | Expected stderr | Exit code |
|---|---|---|---|
| Valid args | `['-t']` against a doc with `-t` | — | 0 (returns dict) |
| Unrecognized short option | `['-x']` | `error: unrecognized option '-x'` + usage | 1 |
| Unrecognized long option | `['--unknown']` | `error: unrecognized option '--unknown'` + usage | 1 |
| Duplicate known option | `['-t', '-t']` | `error: duplicate option '--trace'` + usage | 1 |
| Missing positional (passthrough) | `[]` against doc requiring `FILE` | `Usage: ...` (original) | 1 |

Tests use `capsys` for stderr capture and `pytest.raises(SystemExit)` for exit-code assertion, consistent with the existing `*_cli_test.py` pattern.

## Out of scope

- Improving error messages for missing required positionals (already clean).
- Changes to the `DocoptExit` exception itself.
- Any changes to docopt's parsing behaviour.
