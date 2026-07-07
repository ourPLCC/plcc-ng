# 093 — Incremental parsing in interactive mode

**Issue:** [dev-docs/issues/093-incremental-parsing-repl.md](../issues/done/093-incremental-parsing-repl.md)
**Date:** 2026-06-17
**Type:** feat

## Summary

Replace the `SubmitOn.EOF` interactive model (everything accumulates until `^D`
submits the whole buffer) with an **incremental** model. After each line the
tool re-parses the accumulated buffer, evaluates every complete sentence that
cannot be extended, and uses what remains to decide the prompt: empty buffer →
`>>>`, a complete-but-extensible or incomplete prefix → `...`. `^D` becomes a
conventional context-exit: it never needs a second press, and it force-submits
whatever is buffered.

This applies globally to both interactive orchestrators, `plcc-rep` and
`plcc-parse`. `SubmitOn.EOF` is removed.

## Behavior

### Incremental evaluation (per line, `eof=False`)

1. Append the entered line to the buffer.
2. Re-parse the whole buffer. Peel complete sentences off the front:
   - A **complete-final** sentence (a complete sentence that cannot be a prefix
     of any longer sentence in the grammar) is evaluated and removed from the
     buffer. Keep peeling.
   - Stop peeling at the first trailing portion that is **complete-extensible**
     (a complete sentence that could still be the prefix of a longer one) or
     **incomplete** (a valid prefix that is not yet a complete sentence). That
     portion stays in the buffer.
3. If the buffer is now empty, return to the top-level prompt `>>>`.
4. Otherwise start or stay in continuation mode, prompting `...`.

A single line may contain a complete-final sentence followed by the start of a
new sentence. The complete-final sentence is evaluated; the remainder becomes
the new front of the buffer and is re-examined under the same rules.

A complete-**extensible** trailing sentence is held (not evaluated) so the user
can extend it. If they intended it as-is, `^D` submits it. This matches the
original PLCC.

### `^D` (force submit / exit) — global

`^D` always exits the current context:

1. **Empty buffer, top-level prompt (`>>>`)** → exit immediately. No second
   "are you sure" `^D`.
2. **Non-empty buffer, continuation prompt (`...`), empty line** → force-submit
   the buffer (`eof=True`), then return to `>>>`.
3. **Non-empty buffer, continuation prompt (`...`), partial line** (text typed,
   then `^D` with no newline) → force-submit `buffer + line` (no trailing
   newline), then return to `>>>`.

Force-submission **never** holds and **never** enters continuation mode. The
entire buffer is processed: zero or more complete sentences are reported as
trees, and a trailing incomplete fragment, if any, is reported as an **error**
record. The buffer always clears and the prompt returns to `>>>`.

### Genuine errors

A genuine syntax error (an unexpected real token, `found != "eof"`) is reported
and the buffer is cleared, returning to `>>>`.

### Trailing-portion decision table

| Trailing portion | Parser signal | `eof=False` (Enter) | `eof=True` (`^D` / file / pipe) |
|---|---|---|---|
| Complete, cannot be a prefix | success, `extensible=false`, consumed all | evaluate, keep peeling | evaluate |
| Complete, could be a prefix | success, `extensible=true`, consumed all | **hold** → `...` | **evaluate** |
| Valid prefix, not complete | `ParseError(found="eof")` | **hold** → `...` | **report as error** |
| Complete + leftover real tokens | success, consumed < all | evaluate the complete one; leftover re-examined | same |
| Unexpected real token | `ParseError(found=<token>)` | report error, clear → `>>>` | report error |

## Architecture

The pipeline already does most of this: `plcc-parser-table` loops, peels
sentences, emits multiple trees, and reports `found="eof"` for a trailing
incomplete prefix; `TreePipeline` already holds (returns no records) when
`eof=False` and the only result is a trailing eof-error. Three new capabilities
are required.

### 1. `predictive_parser.py` — extensibility detection

`parse()` returns `(tree, consumed)` today. Change it to return
`(tree, consumed, extensible)`.

`extensible` is `True` when, during the parse, a *stop* decision was taken
**because the current lookahead was the `eof` sentinel** while a real-terminal
alternative existed:

- a nonterminal selected an ε-production keyed by `eof` while that same
  nonterminal had productions keyed by real terminals, **or**
- an arbno loop terminated because `current()` was `eof` while another
  iteration or separator was possible.

Worked examples:

- Grammar `exp → NUM tail; tail → PLUS NUM tail | ε`. Parsing `3`: `tail` takes
  the ε-production on lookahead `eof`, and a `PLUS` alternative exists →
  `extensible = true`.
- Grammar `program → NUM`. Parsing `5`: the production is forced by `NUM` and
  finishes by shifting it; no eof-stop decision → `extensible = false`.

This is pure LL(1)-table reasoning — no grammar annotation or configuration.

### 2. `table_cli.py` — surface the signals (additive)

- Tag the **trailing** successful parse's tree record with
  `"extensible": true|false`. (Non-trailing trees are always followed by more
  real tokens, so they are committed regardless; tagging the trailing one is
  sufficient.)
- When the trailing parse fails with `found="eof"`, include the **start**
  position of that incomplete fragment (the source of `tokens[cursor]` at the
  start of the failed attempt) on the error record, so the remainder boundary
  is known to the pipeline.
- Greedy emission is otherwise unchanged. The hold/commit decision stays in the
  pipeline. **`eof=True` callers see byte-identical output to today.**

### 3. `pipeline.py` — hold trailing extensible, compute remainder

Extend the existing "only EOF errors → hold" logic:

- When `eof=False`, also **hold** a trailing tree tagged `extensible=true`
  (do not dispatch it).
- Compute the **remainder**: the offset in the buffer where the held portion
  begins — from the held tree's source start, or the incomplete fragment's start
  position carried on the eof-error. Map `(line, column)` against the **decoded**
  buffer text (so multibyte characters are handled correctly), then slice.
- `run()` returns the committed records **and** the `remainder` text.
- When `eof=True`, commit everything and set `remainder = ""`: a trailing
  extensible sentence is evaluated; a trailing incomplete fragment is emitted as
  an error record. This keeps batch (`plcc-parse` on files/pipes) and `^D`
  force-submit behavior unchanged.

### 4. `feed()` interface — return remainder text

`handler.feed(content, source, eof)` changes its return type from `bool` to the
**remainder text**:

- `""` → buffer fully consumed → caller shows `>>>`.
- non-empty → caller holds it as the new buffer → `...`.

Both `RepHandler` (`plcc-rep`) and `ParseHandler` (`plcc-parse`) evaluate the
committed sentences exactly as today (send trees to the interpreter / print
them), then return the remainder reported by the pipeline. Under `eof=True` the
remainder is always `""`.

### 5. `source_runner.py` — incremental buffer + new `^D`, global

- After each line: `buffer = feed(buffer, eof=False)`; prompt is `>>>` when the
  remainder is empty and `...` otherwise. This replaces the all-or-nothing
  accumulate/clear behavior.
- `^D` semantics as in the Behavior section: single-press exit on empty buffer;
  force-submit (`eof=True`) on non-empty buffer, both empty-line and partial-line
  cases; always returns to `>>>`.
- **Remove `SubmitOn.EOF`** and its `read1(65536)` machinery. EOL-mode
  `readline()` already returns a partial line (no trailing newline) when the user
  presses `^D` after typing without Enter, which drives the partial-line
  force-submit; an empty `readline()` result drives the exit.
- Remove the double-`^D` "press `^D` again to exit" machinery (`pending_exit`,
  the warning).
- Collapse to a single interactive mode. Remove the `SubmitOn` enum and the
  `submit_on` constructor parameter (no remaining caller needs the distinction).

### 6. Orchestrators

`plcc-rep` and `plcc-parse` construct `SourceRunner` without `SubmitOn`, using
the single incremental mode.

## Files touched

- `src/plcc/parser/predictive_parser.py` (+ test) — extensibility return value.
- `src/plcc/parser/table_cli.py` (+ test) — emit `extensible` on trailing tree;
  start position on eof-error.
- `src/plcc/cmd/pipeline.py` (+ test) — hold trailing extensible when
  `eof=False`; compute and return remainder.
- `src/plcc/cmd/source_runner.py` (+ test) — incremental remainder buffering;
  new `^D` semantics; remove `SubmitOn`/EOF and double-`^D`.
- `src/plcc/cmd/rep.py` (+ test) — `feed` returns remainder; construct runner in
  incremental mode.
- `src/plcc/cmd/parse.py` (+ test) — `feed` returns remainder; construct runner
  in incremental mode.
- `src/plcc/cmd/_test_helpers.py` — helpers for extensible/remainder records as
  needed.
- `docs/cli/orchestrators.md` — interactive-mode and `^D` documentation.

## Testing (TDD)

- **Parser unit:** `extensible` flag for a final single-token grammar; an
  extensible left-factored expression grammar; arbno termination; nested/ε
  chains. Existing `found="eof"` behavior preserved.
- **`table_cli` unit:** trailing tree carries `extensible`; eof-error carries the
  fragment start position; `eof=True` output byte-identical to current.
- **pipeline unit:** holds trailing extensible when `eof=False`, commits when
  `eof=True`; remainder offset correct including multi-line and multibyte input;
  "complete-final + start-of-next on one line" splits correctly.
- **source_runner unit:** incremental remainder buffering; the three `^D` cases;
  single-`^D` exit; partial-line force-submit; removal of the double-`^D` and
  `SubmitOn.EOF` tests.
- **rep / parse unit:** `feed` returns remainder; orchestrators use incremental
  mode.
- **e2e / functional:** `3` → `...` → `+ 4` → evaluates; one line containing a
  complete-final sentence plus the start of the next splits and continues; `^D`
  on `complete\nincomplete` prints the tree(s) then an error then `>>>`; `^D` on
  an empty prompt exits cleanly.

## Risks and edge cases

- **Extensibility-detection correctness** across ε-chains, arbno, and separators
  — covered by focused parser unit tests.
- **Remainder offset mapping** — mapping on decoded text by `(line, column)`
  keeps it multibyte-safe; re-tokenizing `content[offset:]` must reproduce the
  held tokens (leading inter-token whitespace is insignificant).
- **Shared `table_cli` / pipeline** — all changes are additive on the `eof=True`
  path so batch `plcc-parse` and existing tests do not regress.

## Out of scope

- Changing the grammar/spec format.
- Non-LL(1) grammars (parser already rejects these upstream).
- Readline history / line editing.
