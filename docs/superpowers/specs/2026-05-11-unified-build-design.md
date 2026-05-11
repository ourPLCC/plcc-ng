# Unified Build: `build/` as Single Source of Truth

**Date:** 2026-05-11
**Status:** Draft — pending review

## 1. Problem

The Level 2 commands present inconsistent behavior around grammar changes:

- `plcc-scan` and `plcc-parse` compile fresh from the grammar file on every invocation, so a grammar edit is immediately reflected.
- `plcc-rep` reads pre-built artifacts from `build/` and requires a prior `plcc-make` run. A grammar edit is invisible to `plcc-rep` until the student remembers to rebuild.

A student who edits their grammar and runs `plcc-scan` sees the change. The same student who then runs `plcc-rep` sees the old behavior — silently, with no warning. This is a trap.

A secondary bug: `plcc-rep` accepts `GRAMMAR` as a CLI argument but never uses it; it always reads from `build/` regardless.

## 2. Goal

Make all four Level 2 commands — `plcc-make`, `plcc-scan`, `plcc-parse`, `plcc-rep` — read from and write to `build/` consistently. The grammar file is always the single source of truth. Students never need to remember to rebuild manually.

## 3. Design Overview

`plcc-make` becomes the gatekeeper for `build/`. It detects whether `build/` is current using a content-hash of the compiled spec, and rebuilds only when something has changed. All other Level 2 commands call `plcc-make` first and then use artifacts from `build/`.

`plcc-make` accepts a `--through=scan|parse|all` flag so that each command builds only what it needs, preventing errors in later pipeline stages from blocking commands that only depend on earlier stages.

All four commands default to looking for `grammar.plcc` in the current working directory, with a `--grammar-file=<path>` override.

## 4. `build/` Directory Structure

```
build/
  spec.json        ← output of plcc-spec (always written first)
  .spec-hash       ← SHA-256 of spec.json content (success sentinel)
  ll1.json         ← output of plcc-ll1
  model.json       ← output of plcc-model
  <tool>/          ← one directory per semantic section
    ...             ← emitted + compiled language artifacts
```

`build/` lives relative to the current working directory (unchanged from today). Its contents are reproducible from the grammar file; students should not edit them by hand.

## 5. `plcc-make` Staleness Algorithm

### 5.1 Motivation and Goal

The hash sentinel exists to make `plcc-make` fast when nothing has changed — a common case when students run `plcc-scan` or `plcc-parse` repeatedly against the same grammar. Without staleness detection, every command invocation would re-run the entire build pipeline.

The design hashes the *output* of `plcc-spec` (i.e., `spec.json`) rather than the raw grammar file. This is deliberate: the spec format supports `include` directives that pull in other files. Hashing the raw grammar file would miss changes to included files. Hashing the fully-resolved spec output catches all changes regardless of where they originated.

### 5.2 The `.spec-hash` Sentinel

`build/.spec-hash` is a JSON file written when a build completes successfully. It contains two fields:

```json
{"hash": "<sha256-hex>", "through": "scan|parse|all"}
```

- `hash`: SHA-256 hex digest of `spec.json` at the time the build completed.
- `through`: the `--through` level that was requested (determines which artifacts exist).

It is:

- Written **last**, after every required build step succeeds.
- Deleted immediately if any step fails.
- Absent when `build/` does not yet exist or the last build did not complete successfully.

**Invariant:** `.spec-hash` is present if and only if `build/` contains a complete, successful build at the recorded `through` level for the spec whose digest it contains.

Storing the level is necessary because a `--through=scan` run only produces `spec.json`, but then a `--through=all` call must still run the full downstream pipeline even if the grammar hasn't changed.

### 5.3 Algorithm

```
plcc-make [--through=scan|parse|all] [--grammar-file=<path>]
```

Default: `--through=all`, grammar file: `./grammar.plcc`.

Steps:

1. Resolve grammar file path (`--grammar-file` or `./grammar.plcc`). If not found, print a clear error and exit nonzero. Do not create or modify `build/`.

2. Create `build/` if it does not exist.

3. Run `plcc-spec <grammar>` writing output to a **temp file** (not directly to `build/spec.json`). On failure:
   - Delete the temp file.
   - Delete `build/.spec-hash` (forces full rebuild on next invocation).
   - Exit nonzero.

   Writing to a temp file is essential. If `plcc-spec` were to write directly to `build/spec.json` and then fail mid-stream, `build/spec.json` would be partially overwritten. The stale `.spec-hash` would then no longer match the corrupted file, triggering a spurious rebuild — or worse, a partial spec could be mistaken for valid output. Using a temp file keeps `build/spec.json` either fully updated or untouched.

4. Compute SHA-256 of the temp file → `new_hash`. Read `build/.spec-hash` → `{stored_hash, stored_level}` (or `None` if absent).

5. **Fast path:** if `new_hash == stored_hash` AND `stored_level` >= requested `--through` level (ordering: `scan` < `parse` < `all`):
   - Delete temp file.
   - Exit 0. Nothing has changed and the existing artifacts are sufficient.

   This level comparison is essential. A previous `--through=scan` run writes the sentinel with `"through": "scan"`. A subsequent `--through=all` call must detect that the stored level is insufficient and proceed to the slow path, even though the grammar hash matches.

6. **Slow path** (hash mismatch, missing hash, or missing artifacts):
   - Move temp file → `build/spec.json`.
   - Delete `build/.spec-hash` immediately. This ensures that any subsequent failure leaves no sentinel, forcing the next invocation to rebuild.
   - Run the steps required by `--through`:
     - `scan`: no additional steps (spec.json is sufficient).
     - `parse`: run `plcc-ll1` → `build/ll1.json`.
     - `all`: run `plcc-ll1` → `build/ll1.json`, `plcc-model` → `build/model.json`, then for each semantic section: `plcc-lang-emit` + `plcc-lang-build` → `build/<tool>/`.
   - On any step failure: delete `build/.spec-hash`, exit nonzero.
   - On full success: write `new_hash` → `build/.spec-hash` (the final step).

### 5.4 Pitfalls the Algorithm Avoids

**Corrupted `build/spec.json` after `plcc-spec` failure.** Using a temp file means `build/spec.json` is only replaced atomically on success. A failing `plcc-spec` run leaves the previous `build/spec.json` intact.

**Stale build appearing current after failure.** Deleting `.spec-hash` on any failure means the sentinel is absent whenever `build/` is in an incomplete or unknown state. The next `plcc-make` invocation always detects the missing sentinel and rebuilds.

**Repeated failure without grammar changes.** If `plcc-spec` fails (e.g., syntax error in grammar), the student re-runs any Level 2 command, which calls `plcc-make`, which re-runs `plcc-spec`, which fails again. The student is not confused by stale success — they get the same error every time until they fix the grammar.

**Included file changes undetected.** By hashing the output of `plcc-spec` (the fully-resolved spec) rather than the raw grammar file, changes to any `include`d file are automatically detected.

**Partial build hash.** Writing `.spec-hash` last means it is never present after a partial build. A process that is killed mid-build leaves no sentinel; the next run rebuilds from scratch.

**Insufficient prior build level.** A `--through=scan` run writes a sentinel with `"through": "scan"`. If `--through=all` is then called with an unchanged grammar, the hash still matches — but `ll1.json`, `model.json`, and tool directories do not exist. The level comparison in step 5 catches this: `scan < all`, so the fast path is skipped and the missing downstream steps run.

### 5.5 `--through` Levels

| Value | Artifacts built | Sufficient for |
|---|---|---|
| `scan` | `spec.json` | `plcc-scan` |
| `parse` | `spec.json`, `ll1.json` | `plcc-parse` |
| `all` | `spec.json`, `ll1.json`, `model.json`, `build/<tool>/` | `plcc-rep`, standalone `plcc-make` |

Default when called standalone: `--through=all`.

`--through` is primarily an internal flag used by the Level 2 commands to limit build scope. Students may also use it directly if they want to rebuild only up to a certain stage. The values are named after the command they enable, not after the internal artifact names, so the mapping is obvious without knowledge of pipeline internals.

**Why this matters:** without `--through`, a compile error in a Java semantics block would cause `plcc-scan` to fail even though scanning requires only `spec.json`. `--through=scan` stops the build at spec and never reaches the compile step. This preserves the natural student workflow of building the grammar incrementally: lexical section first, syntactic section second, semantic section last.

## 6. Grammar File Resolution

All four commands default to `./grammar.plcc` and accept `--grammar-file=<path>` to override. If neither the default file exists nor `--grammar-file` is specified with a reachable file, the command exits with a clear error and does not touch `build/`.

| Command | Default usage | Override |
|---|---|---|
| `plcc-make` | `plcc-make` | `plcc-make --grammar-file=other.plcc` |
| `plcc-scan` | `plcc-scan [SOURCE ...]` | `plcc-scan --grammar-file=other.plcc [SOURCE ...]` |
| `plcc-parse` | `plcc-parse [SOURCE ...]` | `plcc-parse --grammar-file=other.plcc [SOURCE ...]` |
| `plcc-rep` | `plcc-rep [SOURCE ...]` | `plcc-rep --grammar-file=other.plcc [SOURCE ...]` |

The positional `GRAMMAR` argument is removed from all four commands. This fixes the latent bug in `plcc-rep` where `GRAMMAR` was accepted but silently ignored.

## 7. Changes to Level 2 Commands

### `plcc-make`

- Remove unconditional `shutil.rmtree(build_dir)` at startup; `build/` is now managed incrementally.
- Add `--grammar-file=<path>` option; default to `./grammar.plcc`.
- Add `--through=scan|parse|all` option; default to `all`.
- Implement the staleness algorithm (§5.3).
- Remove the positional `GRAMMAR` argument.

### `plcc-scan`

- Remove positional `GRAMMAR` argument.
- Add `--grammar-file=<path>` option; default to `./grammar.plcc`.
- Call `plcc-make --through=scan [--grammar-file=<path>]` as first step; exit with its return code on failure.
- Replace tempfile + `plcc-spec` logic with: use `build/spec.json` directly.
- Pass `build/spec.json` to `plcc-tokens` (path changes; behavior unchanged).

### `plcc-parse`

- Remove positional `GRAMMAR` argument.
- Add `--grammar-file=<path>` option; default to `./grammar.plcc`.
- Call `plcc-make --through=parse [--grammar-file=<path>]` as first step; exit on failure.
- Replace tempfile + `plcc-spec` + `plcc-ll1` logic with: use `build/spec.json` and `build/ll1.json` directly.

### `plcc-rep`

- Remove positional `GRAMMAR` argument (fixes the silent-ignore bug).
- Add `--grammar-file=<path>` option; default to `./grammar.plcc`.
- Call `plcc-make [--grammar-file=<path>]` (full build) as first step; exit on failure.
- Remove the manual `os.path.exists(spec_path)` guard — `plcc-make` guarantees artifact presence on exit 0.
- Everything else unchanged.

## 8. Partial Grammars

Students typically build their grammar incrementally: lexical section first, then syntactic, then semantic. All four commands must handle incomplete grammars gracefully.

- **Lexical only** (no syntactic or semantic sections): `plcc-make --through=scan` succeeds. `plcc-make --through=parse` and `--through=all` must also succeed gracefully — `plcc-ll1` and `plcc-model` must handle an empty syntactic section without error, and the semantic section loop in `plcc-make` already skips cleanly when there are no semantic sections.
- **Lexical + syntactic** (no semantic sections): `plcc-make --through=parse` succeeds. `plcc-make --through=all` succeeds because the emit/build loop is empty.
- **`plcc-rep` with no semantic sections:** `plcc-make` exits 0 but there is no `build/<tool>/` to run. `plcc-rep` fails with a clear message indicating no semantic sections were found.

Implementation must verify that `plcc-ll1` and `plcc-model` exit 0 with valid (possibly empty) output when the syntactic or semantic section is absent, and add tests if they do not.

## 9. Error Handling

| Failure | Behavior |
|---|---|
| Grammar file not found | Clear error message, exit nonzero, `build/` not created or modified |
| `plcc-spec` fails (syntax error) | Temp file deleted, `.spec-hash` deleted, exit nonzero |
| Grammar not LL(1) | Conflicts/cycles reported (existing behavior), `.spec-hash` deleted, exit nonzero |
| Downstream step fails (model, emit, build) | `.spec-hash` deleted, exit nonzero; partial artifacts remain but are unreachable without the sentinel |
| `plcc-rep` with no semantic sections | `plcc-make` exits 0; `plcc-rep` reports no semantic sections found |

When any Level 2 command calls `plcc-make` and `plcc-make` fails, the calling command propagates `plcc-make`'s exit code without additional output.

## 10. Test Plan

### Staleness algorithm — `plcc-make` (commands tier)

These tests are the most critical. The staleness logic is subtle; any regression here produces silent stale-build bugs.

| Case | Expected behaviour |
|---|---|
| First run, no `build/` directory | `build/` created, full pipeline runs, `.spec-hash` written |
| Second run, grammar unchanged | Hash matches; exits 0 immediately; no downstream tools invoked |
| Run after grammar edit | Hash mismatch detected; full rebuild; `.spec-hash` updated |
| Run after edit to an `include`d file | Hash mismatch detected (resolved spec changes); full rebuild |
| `build/` exists but `.spec-hash` absent | Treated as dirty; full rebuild; `.spec-hash` written |
| `--through=scan` run succeeds, then `--through=all` called, grammar unchanged | Level comparison detects `scan < all`; downstream steps run; sentinel updated to `all` |
| `--through=all` run succeeds, then `--through=scan` called, grammar unchanged | Level comparison detects `all >= scan`; fast path taken |
| `plcc-spec` fails (syntax error in grammar) | `.spec-hash` deleted; exits nonzero |
| `plcc-spec` fails, re-run without fixing grammar | `plcc-spec` fails again; `.spec-hash` absent; exits nonzero |
| `plcc-spec` fails, grammar fixed, re-run | Hash differs from absent sentinel; full rebuild succeeds |
| Downstream step fails (e.g., not LL(1)) | `.spec-hash` deleted; exits nonzero; re-run rebuilds |
| Build interrupted (`.spec-hash` absent after partial build) | Next run treats as dirty; full rebuild |

### `--through` levels (commands tier)

| Case | Expected behaviour |
|---|---|
| `--through=scan`: Java compile error in semantics block | Exits 0; `build/spec.json` written; `build/ll1.json` not required |
| `--through=parse`: Java compile error in semantics block | Exits 0; `build/spec.json` and `build/ll1.json` written |
| `--through=all` (default): Java compile error | Exits nonzero at compile step; `.spec-hash` deleted |
| `--through=scan` then `--through=all` | Second run detects missing downstream artifacts and completes the build |
| `--through=parse` then `--through=scan`, grammar unchanged | `--through=scan` fast-paths; no rebuild |

### Grammar file resolution (commands tier, all four commands)

| Case | Expected behaviour |
|---|---|
| `grammar.plcc` present in CWD, no `--grammar-file` | Used automatically |
| `grammar.plcc` absent, no `--grammar-file` | Clear error; `build/` not touched |
| `--grammar-file=other.plcc`, file present | That file used |
| `--grammar-file=other.plcc`, file absent | Clear error; `build/` not touched |

### Level 2 command delegation (commands tier)

| Case | Expected behaviour |
|---|---|
| `plcc-scan` with changed grammar | Triggers rebuild before scanning |
| `plcc-scan` with unchanged grammar | No rebuild; uses existing `build/spec.json` |
| `plcc-scan` when `plcc-make` fails | Exits with `plcc-make`'s error code |
| `plcc-parse` with changed grammar | Triggers rebuild before parsing |
| `plcc-parse` when `plcc-make` fails | Exits with `plcc-make`'s error code |
| `plcc-rep` with changed grammar | Triggers full rebuild before starting REPL |
| `plcc-rep` when `plcc-make` fails | Exits with `plcc-make`'s error code |
| `plcc-rep` with grammar that has no semantic sections | `plcc-make` succeeds; `plcc-rep` reports no semantic sections |

### Partial grammars (commands tier)

| Case | Expected behaviour |
|---|---|
| `plcc-scan` with lexical-only grammar | Succeeds |
| `plcc-parse` with lexical + syntactic grammar, no semantics | Succeeds |
| `plcc-make` with lexical-only grammar | Succeeds (emit/build loop is empty) |

### Hash logic (unit tier)

- Hash match returns true for identical spec.json content
- Hash mismatch returns false for any content change
- Missing `.spec-hash` file treated as mismatch
- Hash written to correct path with correct content
