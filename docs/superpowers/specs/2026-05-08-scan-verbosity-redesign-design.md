# Design: Scan verbosity redesign — split diagnostics from output richness

**Date:** 2026-05-08
**Issue:** [003-scan-verbosity-levels-2-3-unused](../../issues/003-scan-verbosity-levels-2-3-unused.md)

## Problem

`plcc-scan` accepts `-v` as a counting flag (`-v` = level 1, `-vv` = level 2,
`-vvv` = level 3) but levels 2 and 3 produce output identical to level 1.
The framed question — "what useful information should levels 2 and 3 expose?"
— turned out to be the wrong question. The real problem is that `-v` was
being asked to do two unrelated jobs:

1. Control **stderr diagnostic noise** (process-level metadata: stage events,
   file events).
2. Control **stdout content richness** (per-token detail: matched regex,
   skips, rule-attempt traces).

Conflating these forced `plcc-scan` to capture and reformat `plcc-tokens`'s
stderr (in JSON) so it could correlate child verbose events with the rendered
token stream. That is the source of `reformat_child_events`,
`parse_child_events`, `child_flags_for_orchestrator`, the always-on internal
`--verbose-format=json` override, and the synchronization fragility we keep
hitting whenever someone tries to add per-token detail.

## Design

### Split the knob

Two independent controls with clearly separated responsibilities:

| Concern | Stream | Controlled by |
|---|---|---|
| Process-level metadata (stage, per-file) | stderr | `-v` (counting) |
| TTY `^D` hint | stdout (first line) | always on when stdin is a TTY |
| Token records (lean) | stdout JSONL → text | always on |
| Skip records, regex, source line, attempts | stdout JSONL → text | `--show-*` flags on `plcc-scan` |
| Lex errors | stdout JSONL → text | always on |

- `-v` (counting flag) controls **only** stderr diagnostics.
- Output richness is controlled by dedicated feature flags on `plcc-scan`:
  `--show-skips`, `--show-line`, `--show-regex`, `--show-attempts`, `--show-all`.
- `plcc-tokens` has a single enrichment flag, `--show-all`, that causes it to
  include the full record payload. `plcc-scan` passes this flag to `plcc-tokens`
  whenever any of its own enrichment flags are set; `plcc-tokens` does not need
  to know which specific things `plcc-scan` intends to render.

### Per-token verbose info travels in the stdout JSONL stream

Per-token data (regex, source line, skip records, rule attempts) is *associated
with* the token it describes. Putting it on a different stream from the token
forces synchronization. Putting it in the same record solves the synchronization
problem structurally — the data is shipped together because it belongs together.

Stderr is reserved for process-level metadata (stage start/finish, per-file
"scanning <file>"). These events are coarse-grained — not tied to specific
tokens — so any interleaving with stdout is harmless.

### Pass-through stderr; no capture or reformat

`plcc-scan` runs `plcc-spec` and `plcc-tokens` with `stderr=None` (inherited).
Each child writes its own stderr directly. `plcc-scan` does **not** parse,
capture, or reformat child stderr. Verbose flags propagate down unchanged
(`-v [-v ...] --verbose-format=FMT`); each command independently decides
what it emits at each level.

### Verbose level content (scope: scan/tokens)

- no `-v` (default): silent.
- `-v`: stage events (started/finished), per-file `scanning <file>` events.
- `-vv`, `-vvv`: reserved framework-wide for other commands; `plcc-scan` and
  `plcc-tokens` emit nothing additional at these levels for now.

Per-file events are emitted from `plcc-tokens` (the actual file reader).
`plcc-scan` emits its own outer started/finished events. The TTY `^D` hint
is emitted by `plcc-scan` to stdout as its first line of output, independent
of `-v`.

### Stdout schema (from `plcc-tokens`)

Three record kinds, all on stdout JSONL:

- `kind: "token"` — always present: `name`, `lexeme`, `source`. With
  `--show-all`: also `regex`, `source_line`, and optionally `attempts`.
- `kind: "skip"` — same shape as token, only emitted when `--show-all`.
- `kind: "error"` — unchanged from current schema. Lex errors never carry
  `attempts`.

`attempts` is the complete list of all rules that matched at the current
position, in grammar definition order — both token and skip rules, regardless
of which type wins. Non-matching rules are omitted. Exactly one entry has
`winner: true`; it is the object returned by `match()`. The formatter does not
re-derive the winner. This means: when a skip wins (it is first in definition
order), the list still includes any tokens that also matched; when a token wins,
the list still includes any skips that matched but appeared after a token rule.

`source_line` is the raw text of the source line containing the token's start
position, read from `obj.line.string`. It is always present when `--show-all`
is set, and is passed through in the JSONL for downstream consumers such as
`plcc-parse`.

### `plcc-scan` enrichment flags

All flags are independent and composable. `--show-all` is equivalent to setting
all four.

| Flag | Effect |
|---|---|
| `--show-skips` | Render skip records: `file:line:col NAME 'lexeme' SKIPPED` |
| `--show-line` | Before each record, print the source line and a `^` cursor at the token's column |
| `--show-attempts` | Before the token line (after cursor if present), print indented attempt lines |
| `--show-regex` | Include matched regex in the token/skip line: `file:line:col NAME 'regex' 'lexeme'` |
| `--show-all` | All of the above |

When any enrichment flag is set, `plcc-scan` passes `--show-all` to
`plcc-tokens`. When no enrichment flags are set, `plcc-tokens` produces lean
JSONL and `plcc-scan` ignores any optional fields.

### `plcc-scan` rendering

**Default** (no enrichment flags):
```
-:1:1 NUM '42'
```

**`--show-regex`**:
```
-:1:1 NUM '\d+' '42'
```

**`--show-skips`**:
```
-:1:1 NUM '42'
-:1:4 WS ' ' SKIPPED
-:1:5 NUM '99'
```

**`--show-line`**:
```
42
^
-:1:1 NUM '42'
```

**`--show-attempts`** (on its own, `^` absent):
```
      INT '\d+' 2 chars '42'
    * NUM '\d+' 2 chars '42'
-:1:1 NUM '42'
```
Winner prefix: `"    * "`. Loser prefix: `"      "`.

**`--show-all`** (all flags):
```
42 99
^
      INT '\d+' 2 chars '42'
    * NUM '\d+' 2 chars '42'
-:1:1 NUM '\d+' '42'
42 99
  ^
    * WS '\s+' 1 chars ' '
-:1:3 WS '\s+' ' ' SKIPPED
42 99
     ^
      INT '\d+' 2 chars '99'
    * NUM '\d+' 2 chars '99'
-:1:5 NUM '\d+' '99'
```

The `^` cursor is placed at column − 1 spaces from the left (columns are
1-indexed, so column 1 means zero leading spaces).

### Data flow

**Before:**
```
plcc-scan
  → spawns plcc-spec and plcc-tokens with stderr=PIPE
  → captures child stderr, parses as JSONL, reformats per --verbose-format
  → reads stdout JSONL, renders tokens
```

**After:**
```
plcc-scan
  → if stdin is a TTY, prints ^D hint to stdout first
  → spawns plcc-spec and plcc-tokens with stderr=None (inherited)
  → passes --show-all to plcc-tokens when any enrichment flag is set
  → reads stdout JSONL, renders records (token / skip / error + line / attempts)
plcc-tokens
  → writes stage / scanning events to its own stderr
  → writes lean token / error JSONL records to its own stdout (default)
  → with --show-all: includes regex, source_line, attempts; emits skip records
```

## File changes (summary)

- `src/plcc/scan/Token.py`, `src/plcc/scan/Skip.py`: add
  `pattern: str = field(default="", compare=False)` and
  `attempts: list = field(default_factory=list, compare=False)`. `compare=False`
  preserves existing `Token(...)` equality assertions in tests. No `source_line`
  field needed — `Token` and `Skip` already carry `line`, and `line.string` is
  the raw source line text.
- `src/plcc/scan/matcher.py`: add `record_attempts: bool = False` to
  `__init__`. When enabled, capture the full `_getMatches` result (all
  matching rules — both tokens and skips — in definition order) before any
  filtering, and populate it as `attempts` on the returned object. Always
  populate `Token.pattern`/`Skip.pattern`.
- `src/plcc/scan/scanner.py`: no changes.
- `src/plcc/tokens/jsonl_formatter.py`: handle `Token` and `Skip`. Default
  output: `name`, `lexeme`, `source` only. When `show_all=True`: also emit
  `regex` (from `obj.pattern`), `source_line` (from `obj.line.string`), and
  `attempts` array (with `winner` flags) when populated. `source_line` is
  passed through in the JSONL for downstream consumers such as `plcc-parse`.
  Skip records get `kind=skip`.
- `src/plcc/tokens/tokens_cli.py`: add `--show-all` option (single enrichment
  flag). New event `SCANNING_FILE`. Per-file event from `_lines_from_sources`.
  Construct `Matcher(rules, record_attempts=args["--show-all"])`. Emit skip
  records only when `--show-all`.
- `src/plcc/cmd/scan.py`: add `--show-skips`, `--show-line`, `--show-regex`,
  `--show-attempts`, `--show-all` options. Use `verbose.child_flags()` (no JSON
  override). `stderr=None` on both child invocations. If stdin is a TTY, print
  the `^D` hint to stdout before any token output. Pass `--show-all` to the
  `plcc-tokens` invocation when any enrichment flag is set. Remove threading,
  stderr capture, `parse_child_events`/`reformat_child_events` calls. Render
  `kind=token`/`kind=skip`/`kind=error` with source line, cursor, attempts, and
  regex according to active flags.
- `src/plcc/verbose.py`: **no removals.** `parse_child_events`,
  `reformat_child_events`, `child_flags_for_orchestrator`, `reap_pipeline`,
  `PipelineResult` are still consumed by `plcc-parse` and `plcc-make`.
  Converting those to pass-through is a follow-up.
- `src/plcc/schemas/token.schema.json`: add `SkipRecord` branch. `regex`,
  `source_line`, and `attempts` are optional on `TokenRecord` and `SkipRecord`
  (present only when `plcc-tokens --show-all`).

## Tests

**Pytest (new):**
- `matcher_test.py`: `record_attempts=True` populates `attempts`; default
  empty; skip-first-match still records attempts; `pattern` always set.
- `jsonl_formatter_test.py`: lean token records omit `regex`/`source_line`/
  `attempts`; enriched records include all three; skip records have
  `kind=skip`; `attempts` has `winner: true` on exactly one entry.
- `tokens_cli_test.py`: `--show-all` emits `kind=skip` records, `regex`,
  `source_line`, and `attempts`; per-file event emitted at `-v`.
- `scan_cli_test.py` (or bats): TTY hint printed to stdout as first line when
  stdin is a TTY (monkeypatch `isatty`); absent when stdin is not a TTY.

**Pytest (regression):** `compare=False` keeps existing matcher/scanner test
assertions valid.

**Bats (`plcc-scan.bats`):**

- Confirm existing `file:line:col in token output` test still matches lean
  default format `^-:1:1 NUM '42'$` (no regex).
- New: `--show-skips` adds `SKIPPED` lines.
- New: `--show-line` shows source line and `^` cursor.
- New: `--show-attempts` produces indented attempt lines with one starred winner.
- New: `--show-regex` adds regex field to output line.
- New: `--show-all` produces all of the above.
- New: `-v` emits `started`/`finished`/`scanning` on stderr
  (`--separate-stderr`); hint is absent from stderr.
- New: TTY `^D` hint appears on stdout as first line when stdin is a TTY;
  absent when stdin is not a TTY.
- New: `-vv` and `-vvv` produce no more scan-emitted output than `-v`.

**Bats (`plcc-tokens.bats`):**

- New: `--show-all` emits `kind=skip` records (validate updated schema).
- New: `--show-all` token records include `regex` and `source_line`.
- Confirm: default token records do not include `regex` or `source_line`.
- New: `-v` emits per-file scanning events on stderr.

## Verification

```sh
cd .worktrees/003-scan-verbosity-levels

# Default output: lean
echo '42' | plcc-scan tests/fixtures/trivial.plcc
# Expected: -:1:1 NUM '42'

# Skips visible
echo '42 99' | plcc-scan --show-skips tests/fixtures/trivial.plcc

# Source line + cursor
echo '42' | plcc-scan --show-line tests/fixtures/trivial.plcc

# Attempts visible
echo '42' | plcc-scan --show-attempts tests/fixtures/trivial.plcc

# Regex in output
echo '42' | plcc-scan --show-regex tests/fixtures/trivial.plcc
# Expected: -:1:1 NUM '\d+' '42'

# All flags at once
echo '42 99' | plcc-scan --show-all tests/fixtures/trivial.plcc

# Stderr at -v
echo '42' | plcc-scan -v tests/fixtures/trivial.plcc 2>&1 1>/dev/null

# Levels -vv/-vvv don't add scan-specific content
echo '42' | plcc-scan -vvv tests/fixtures/trivial.plcc 2>&1 1>/dev/null

# Test suite
bin/test
```

`plcc-parse` and `plcc-tree` consume the same JSONL. The lean default record
is unchanged from their perspective (`regex`, `source_line`, `attempts` are
absent unless `--show-all` is passed to `plcc-tokens`, which `plcc-parse` does
not do). Downstream consumers are unaffected.

## Out of scope (deferred follow-ups)

- Convert `plcc-parse` and `plcc-make` to the same stderr-inheritance model
  and remove `reformat_child_events` / `parse_child_events` /
  `reap_pipeline` once they have no consumers.
- Whether `-vv`/`-vvv` should ever have scan-specific content. Reserved.
