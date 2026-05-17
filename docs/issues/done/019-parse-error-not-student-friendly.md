# 019 - plcc-parse error output is not student-friendly

**Type:** fix
**Date:** 2026-05-14

## Description

When `plcc-parse` encounters a parse error, two lines appear on stderr:

```
{"stage": "plcc-parser-table", "time": 83130153900935, "event": "error", "severity": "error", "pos": {}, "message": "unexpected 'ID', no production for 'prog' at {'file': '-', 'line': 1, 'column': 1}"}
plcc-parser-table: error: unexpected 'ID', no production for 'prog' at {'file': '-', 'line': 1, 'column': 1}
```

Two problems here:

### 1. Raw JSON event line visible to the student

The first line is a structured machine-readable event record. It is useful
for tooling (piped pipelines, editors parsing diagnostics) but is noise for a
student running `plcc-parse` interactively. Students see a wall of JSON before
they see the actual error message.

### 2. Position formatted as a Python dict

Both lines embed the source position as a Python dict literal:

```
at {'file': '-', 'line': 1, 'column': 1}
```

This format is unfamiliar to most students and harder to read than the
conventional `file:line:column` notation:

```
at -:1:1
```

## Steps to Reproduce

Grammar file:

```
skip WS '\s+'
token A 'a'
token AA 'aa'
token ID '\w+'
%
<prog> ::= <A> <AA> <ID>
```

1. Start an interactive session with the grammar above.
2. At the `>>>` prompt, type `asdf` and press ^D (without pressing Enter first).
3. Observe the two lines of error output shown in the Description.

The input `asdf` is scanned as a single `ID` token (longest-match wins over `A`
and `AA`), which does not satisfy the first position of `<prog>`. The error fires
immediately at line 1, column 1.

Pressing ^D without Enter is a natural student workflow — it submits the current
line and exits in one keystroke — which also makes issue
[018](018-ctrl-d-exit-missing-newline.md) visible: the shell prompt appears on
the same line as the last prompt, immediately after the error output.

## Desired behaviour

In interactive / non-piped use, students should see only a concise,
human-readable error on stderr:

```
error: unexpected 'ID', no production for 'prog' at -:1:1
```

The machine-readable JSON event line should be suppressed or reserved for
verbose (`-v`) or piped contexts where a downstream tool can consume it.

## Notes

- The JSON event line is the verbose-event infrastructure; suppressing it for
  non-verbose interactive sessions is the right fix, not removing it entirely.
- The Python-dict position format (`{'file': ..., 'line': ..., 'column': ...}`)
  should be replaced with `file:line:column` in all human-facing message
  strings. This is a formatting change inside the message construction, not
  just the event serialisation.
- Related to issue [012](012-parser-table-error-record-missing-position.md):
  the JSON event above shows `"pos": {}` — the structured position field is
  empty and the position appears only as a Python-formatted substring of
  `message`. Issue 012 addresses adding a proper structured `source` field;
  this issue addresses human-readable formatting of the same information.
- A good end state: the structured record has a populated `source` field
  (issue 012), the `message` string uses `file:line:column` notation (this
  issue), and the raw JSON event is hidden unless `-v` is passed or stdout is
  piped.
