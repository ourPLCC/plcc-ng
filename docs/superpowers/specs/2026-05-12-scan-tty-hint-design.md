# Design: plcc-scan TTY hint

**Date:** 2026-05-12
**Issue:** docs/issues/005-scan-no-tty-hint.md

## Problem

When `plcc-scan` reads from stdin and stdin is a TTY (interactive session), the user sees a blank terminal with no indication that the command is waiting for input or how to signal end-of-input. The fix is to print a hint to stderr each time the command begins reading from an interactive stdin source.

## Hint message

```
Enter input. Press ^D (EOF) when done.
```

Printed to stderr. Absent when stdin is not a TTY or when the source is a file.

## Change to `scan.py`

The current implementation passes all sources to `plcc-tokens` in a single subprocess call. The fix restructures this into a per-source loop so a hint can be emitted before each interactive read begins.

```python
token_sources = sources if sources else ["-"]
tokens_flags = child_flags + (["--trace"] if any_enrichment else [])

for source in token_sources:
    if source == "-" and sys.stdin.isatty():
        print("Enter input. Press ^D (EOF) when done.", file=sys.stderr)

    proc = subprocess.Popen(
        ["plcc-tokens", spec_path, source] + tokens_flags,
        stdout=subprocess.PIPE,
        stderr=None,
    )
    for raw in proc.stdout:
        line = raw.decode("utf-8").strip()
        if not line:
            continue
        record = json.loads(line)
        _render_record(record, trace, trace, trace)
    proc.wait()
    if proc.returncode != 0:
        print(f"plcc-scan: plcc-tokens failed (exit {proc.returncode})", file=sys.stderr)
        sys.exit(proc.returncode)
```

The hint prints once per `-` source entry, so `plcc-scan - - file.txt -` prints the hint three times (before each `-`). Token records already carry file/line metadata so per-source `plcc-tokens` invocations produce the same output format as the single-call approach.

## Testing

### Existing bats test (update required)

`tests/bats/commands/plcc-scan.bats` has:

```
@test "plcc-scan -v hint is absent from stderr" {
    [[ "$stderr" != *"press ^D"* ]]
```

The matched string `"press ^D"` must be updated to match the new message (`"Press ^D"`).

The existing `plcc-scan TTY hint absent when stdin is not a TTY` bats test requires no changes.

### New pytest unit tests (`src/plcc/cmd/scan_test.py`)

Each test monkeypatches within `plcc.cmd.scan`:
- `subprocess.run` → returns `SimpleNamespace(returncode=0)` (stubs `plcc-make`)
- `subprocess.Popen` → returns a mock proc with empty stdout and `returncode=0`
- `sys.stdin.isatty` → controlled per test

A dummy `grammar.plcc` is created in `tmp_path` so the grammar-file check passes.

| Test | `isatty` | sources arg | Expected hint count |
|------|----------|-------------|---------------------|
| Hint printed for implicit stdin | True | `[]` | 1 |
| Hint printed for explicit `-` | True | `["-"]` | 1 |
| Hint printed twice for `["-", "-"]` | True | `["-", "-"]` | 2 |
| Hint absent when not a TTY | False | `[]` | 0 |
| Hint absent for file source | True | `["file.txt"]` | 0 |
