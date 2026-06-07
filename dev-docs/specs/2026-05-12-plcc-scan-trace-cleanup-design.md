# plcc-scan trace cleanup design

**Date:** 2026-05-12
**Issues:** 006 (improve --trace output format), 007 (remove --show-* flags)
**Approach:** two commits on one branch — 007 first, then 006

## Scope

Issues 006 and 007 share the same rendering code and bats tests, so they are
implemented together on a single branch to avoid duplicate churn. Issue 005
(TTY hint) is out of scope for this work.

## Versioning

`major_on_zero = false` is already set in `pyproject.toml`. A `fix!:` commit
with a `BREAKING CHANGE` footer will bump the minor version, not trigger
1.0.0.

---

## Commit 1 — Remove `--show-*` flags (007)

### What changes

**`src/plcc/cmd/scan.py`**

- Remove `--show-skips`, `--show-line`, `--show-attempts`, `--show-regex`
  from the docstring/usage block.
- Remove the four `args["--show-*"] or trace` lines.
- Collapse to `any_enrichment = trace`.
- `_render_record` signature is reduced to three bool parameters
  (`show_skips`, `show_line`, `show_attempts`); `show_regex` is removed as
  dead code. All three are passed `trace` at the call site.

**`tests/bats/commands/plcc-scan.bats`**

Delete these seven tests (they exercise removed flags directly):

- `plcc-scan --show-skips adds SKIPPED lines`
- `plcc-scan --show-skips format is file:line:col NAME 'lexeme' SKIPPED`
- `plcc-scan --show-line shows source line and caret cursor`
- `plcc-scan --show-line cursor is at correct column`
- `plcc-scan --show-attempts produces indented attempt lines`
- `plcc-scan --show-attempts has exactly one starred winner`
- `plcc-scan --show-regex includes regex in token output`

The `--trace` test is kept and updated in commit 2.

### Commit message

```
fix!: remove --show-skips, --show-line, --show-regex, --show-attempts flags

BREAKING CHANGE: the four --show-* flags are removed. Use --trace, which
already implied all four, to enable detailed output.
```

---

## Commit 2 — Improve `--trace` output format (006)

### Output format

Normal output (no `--trace`) is **unchanged**.

Under `--trace`, each match event is rendered as a block:

```
{source line}
{caret cursor}
Candidates:
   {name} '{regex}' {char_count} chars '{lexeme}'   ← non-winner (3 spaces)
-> {name} '{regex}' {char_count} chars '{lexeme}'   ← winner (-> + space)
{loc}: {disposition}: {name} '{lexeme}'
                                                     ← blank line
```

Rules:

- **Candidates list** shows only rules that matched at least one character.
  Rules with 0 chars matched are excluded.
- **Winner** is marked with `->` (2 chars + 1 space). Non-winners are
  indented 3 spaces. Names align at column 4 in both cases.
- **No asterisk** on the winner.
- **Disposition** is `token` or `skip`. Error lines already use `error` and
  are unchanged.
- **Regex** is present in the candidates list and absent from the
  disposition line.
- **Blank line** follows every token or skip disposition line.

### Examples

Single token, one candidate:
```
42
^
Candidates:
-> NUM '\d+' 2 chars '42'
-:1:1: token: NUM '42'

```

Two tokens with a skip, multiple candidates:
```
42 99
^
Candidates:
-> NUM '\d+' 2 chars '42'
-:1:1: token: NUM '42'

42 99
  ^
Candidates:
-> WS '\s+' 1 chars ' '
-:1:3: skip: WS ' '

42 99
   ^
Candidates:
-> NUM '\d+' 2 chars '99'
-:1:4: token: NUM '99'

```

### What changes

**`src/plcc/cmd/scan.py`** — `_render_record`:

- When `show_attempts`: print `Candidates:` heading before the attempt loop.
  Filter out attempts where `char_count == 0`. Use `-> ` for winner,
  `   ` (3 spaces) for non-winners. Remove the `*` prefix logic.
- Regex is removed from the token/skip disposition line (present only in
  Candidates list). The `show_regex` parameter is dropped entirely.
- Token disposition line: `f"{loc}: token: {name} '{lexeme}'"`.
- Skip disposition line: `f"{loc}: skip: {name} '{lexeme}'"`.
- After each token or skip disposition line: print a blank line.

**`tests/bats/commands/plcc-scan.bats`**

Update the existing `--trace` test to match the new format. Add new tests:

- `plcc-scan --trace shows Candidates: heading`
- `plcc-scan --trace marks winner with ->`
- `plcc-scan --trace excludes zero-match candidates`
- `plcc-scan --trace token line uses token: disposition`
- `plcc-scan --trace skip line uses skip: disposition`
- `plcc-scan --trace token line has no regex`
- `plcc-scan --trace adds blank line after each block`

### Commit message

```
fix: improve --trace output format

- Add Candidates: heading before match attempts
- Mark winning candidate with -> instead of *
- Exclude zero-match candidates from Candidates list
- Use location: disposition: details format for token and skip lines
- Remove regex from token/skip lines (still present in Candidates)
- Add blank line after each match block
```
