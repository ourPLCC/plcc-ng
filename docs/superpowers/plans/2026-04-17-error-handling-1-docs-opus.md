# Error Handling Redesign — Part 1: Documentation (Opus)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Model:** Opus. Amendment prose must stay consistent with the existing §17.x voice and must not contradict unamended sections. Judgment-heavy writing.

**Goal:** Retire §8 (in-band error records) in the pipeline spec, add a new amendment §17.9 that defines the stderr + exit-code error model, and simplify the Phase 2 Part 1 design to drop the `Error` parse-tree node. After Part 1, the specs are internally consistent and ready for the code changes in Parts 2 and 3.

**Design spec:** This plan. The design was brainstormed on 2026-04-17 and is captured inline in §"Design summary" below. Amendment text is ready to paste.

**Successor plans:**
- `docs/plans/2026-04-17-error-handling-2-code-sonnet.md` — mechanical code changes across Level 0 stages.
- `docs/plans/2026-04-17-error-handling-3-orchestrators-opus.md` — pipefail discipline and cascade suppression in Level 2 orchestrators.

---

## Design summary

### Core principle

Every Level 0 stage has exactly one success contract: **valid output on stdout, exit 0**. Any other outcome is a failure: **nonzero exit, error on stderr, stdout undefined**. §8's "tool failures vs input errors" distinction disappears — without error recovery, both terminate the stage.

Per-stage applications:

- `plcc-tokens`: can't tokenize the entire input → stderr + exit nonzero.
- `plcc-parser-table`: can't produce a tree from the tokens → stderr + exit nonzero.
- `plcc-tree`: dispatcher; propagates the child's stderr and returncode unchanged.
- Interpreter (Phase 2 Part 2, forward-looking): long-lived; runtime errors in student code are evaluation records on stdout (its own stream schema), not in-band pipeline errors.

### Error rendering (on stderr)

Piggybacks on the `--verbose-format` infrastructure from §17.8:

- `--verbose-format=text` (default): GNU-style `plcc-parser-table: program.txt:4:12: error: expected IDENT or '(' but found '}'`.
- `--verbose-format=json` (orchestrator consuming): one JSONL record with `"event": "error"`, `"severity": "error"`, `"pos": {...}`, `"message": ...`, plus stage-specific fields (e.g. `expected`, `found`).

Errors are always emitted regardless of `--verbose` level — §17.8.4 already requires this.

### `plcc-ll1` becomes a pure filter

A non-LL(1) grammar is a *result*, not a failure.

- Exit 0 always (barring tool failures such as missing input).
- Stdout: the analysis JSON, always, with the same schema.
- Result signaled by top-level fields `is_ll1` (boolean), `conflicts` (array), `left_recursion` (array).
- No file I/O inside the tool — `plcc-make` captures stdout to `build/ll1.json` and reads it back to check `is_ll1`.

### Phase 2 Part 1 simplification

With no error recovery, parse trees are either valid or nonexistent. The `"kind": "Error"` node with typed payload (`scanner`/`parser`/`semantic`) is removed from the Phase 2 Part 1 parse-tree schema. Scanner errors are stderr from `plcc-tokens`; parser errors are stderr from `plcc-parser-table`; neither appears in the tree.

---

## Task 1 — Verify green bar

**Files:**
- Run only: `bin/test/all.bash`

- [ ] **Step 1: Run the full test suite**

```bash
cd /workspaces/plcc-ng/.worktrees/multi-lang
bin/test/all.bash
```

Expected: all tests pass. Do not proceed until green. If any fail, fix them first.

- [ ] **Step 2: Note the test counts**

Record passing unit tests and BATS tests. These numbers must not decrease through this plan. (Part 1 is doc-only, so they should be identical at the end.)

---

## Task 2 — Add §17.9 to the pipeline spec

**Files:**
- Edit: `docs/design/2026-04-12-multi-lang-pipeline.md`

- [ ] **Step 1: Append §17.9 to the Architectural Amendments section**

Append this section verbatim after §17.8.11 (end of §17 as of 2026-04-17):

```markdown
### 17.9 Amends §8, §17.4: Retire in-band error records; adopt stderr + exit-code error model (from brainstorm, 2026-04-17)

**Original §8** defined errors as in-band JSON records that flow through the pipeline alongside normal output. Every stage recognized, passed through, and sometimes emitted records of the form `{"kind": "error", "stage": ..., "severity": ..., ...}`. The motivation was pipeline robustness across multiple programs in a long-running streaming pipeline.

**Original §17.4** specified that `plcc-ll1` exits nonzero on non-LL(1) grammars with the diagnostic artifact still written to stdout — a deliberate exception to the usual stdout contract.

**Amendment.** Both are superseded.

With `plcc-tree` one-shot (§17.3) and the orchestrator controlling per-chunk lifetimes (§17.7), and with no plans for parser error recovery, every error terminates its stage. The uniform contract across all Level 0 stages is:

- **Success:** valid output on stdout, exit 0.
- **Failure:** error on stderr, exit nonzero, stdout undefined.

Error rendering uses the verbose infrastructure (§17.8): GNU-style text on stderr when `--verbose-format=text`, a JSONL record with `"event": "error"` when `--verbose-format=json`. Errors are always emitted regardless of `--verbose` level (§17.8.4).

Orchestrators detect failures by checking child returncodes in pipeline order (upstream first), capture the structured JSONL stderr their children produce (children are always spawned with `--verbose-format=json` per §17.8.3), and report the first failing stage's error. In interpreter sessions (§17.7), per-chunk subpipeline failures do not kill the long-lived interpreter; the orchestrator reports the error and continues.

**`plcc-ll1` becomes a pure filter.** It always exits 0 (barring tool failures such as missing input or malformed spec JSON). A non-LL(1) grammar is a result, not a failure. Its stdout carries the same analysis JSON in every case, with top-level fields `is_ll1` (boolean), `conflicts` (array, empty on success), and `left_recursion` (array, empty on success) signaling the result. `plcc-make` redirects stdout to `build/ll1.json`, reads the file back, checks `is_ll1`, and decides whether subsequent phases run.

**Interpreter runtime errors** are the interpreter's own stdout schema, not a revival of in-band errors. Because the interpreter is long-lived (§17.7), runtime errors in student code are emitted as one kind of evaluation record on stdout. Exit stays 0; stderr is reserved for interpreter-level tool failures. The exact record shape is a Phase 2 Part 2 design-doc decision.

**Rationale.** The original §8 served a streaming multi-program pipeline that no longer exists. Under the one-shot + orchestrator architecture, every stage either produces its output and exits cleanly, or stops and reports. The Unix `stderr + nonzero exit` convention fits this exactly: simpler contract, no "error record pass-through" discipline across every stage, no dual-schema stdout, editor-friendly error messages for free, and a single rendering system shared with verbose diagnostics.

The `plcc-ll1` change aligns the tool with the rest of the pipeline rather than treating it as an exception. A grammar being non-LL(1) is a property of the grammar — the analyzer completed its analysis. `grep` exits 1 on no matches, which is widely considered a design mistake that makes scripting harder; `jq` exits 0 on `null` results, which is preferred. `plcc-ll1` joins the latter camp.

#### Revised §5 row for `plcc-ll1`

| Command | Input | Output | Role |
| --- | --- | --- | --- |
| `plcc-ll1` | spec JSON (stdin or path) | LL(1) analysis JSON (stdout) | One-shot; single JSON document. Exits 0 on any grammar that parses as spec JSON; result is signaled by top-level `is_ll1` field. Nonzero exit is reserved for tool failures (missing input, malformed spec JSON). |

#### Revised §9 phase-failure behaviour

> If `plcc-ll1` reports `is_ll1: false` in its output, `plcc-make` writes the output to `build/ll1.json`, prints a human-readable summary of `conflicts` and `left_recursion` on stderr, and exits nonzero. If any other phase exits nonzero, `plcc-make` reports the error and stops; subsequent phases do not run.
```

- [ ] **Step 2: Replace §8 body with a pointer**

Locate §8 ("Error Handling") in `docs/design/2026-04-12-multi-lang-pipeline.md`. Replace the section body (but not the `## 8. Error Handling` heading) with:

```markdown
## 8. Error Handling

Superseded by §17.9. Errors are reported via stderr and nonzero exit codes. Every stage that fails emits a structured error on stderr (GNU-style under `--verbose-format=text`, JSONL with `"event": "error"` under `--verbose-format=json`) and exits nonzero. `plcc-ll1` is a pure filter and does not fail on non-LL(1) grammars; see §17.9 for the full model.
```

- [ ] **Step 3: Sanity-check cross-references**

Search the spec for other references to §8 or "in-band error":

```bash
grep -n "§8\|in-band error\|error record" docs/design/2026-04-12-multi-lang-pipeline.md
```

For each hit outside §8 and §17.9:

- If the text says "per §8" or "see §8", change it to "per §17.9" or "see §17.9".
- If the text describes in-band error semantics as a design principle, either delete it or rewrite it to match §17.9.

Do **not** edit §17.x amendments that were written before §17.9 (those are historical snapshots — they describe the state at that time). Only edit unamended sections that still describe live behavior.

- [ ] **Step 4: Verify the spec reads coherently**

Re-read §1–§16 and §17.1–§17.9 in order. Flag any remaining contradictions. Fix inline.

---

## Task 3 — Simplify the Phase 2 Part 1 design

**Files:**
- Edit: `docs/design/2026-04-16-phase-2-part-1-ll1-parser-design.md`

- [ ] **Step 1: Remove the "Error node (option Q)" subsection**

Locate §3 ("Parse tree schema (A′)"). Delete the subsection that starts `### Error node (option Q)` and the paragraph immediately after it that lists error types (`scanner`, `parser`, `semantic`). Keep the "Design principles" subsection.

- [ ] **Step 2: Rewrite the "Error contract" bullet in §7**

Locate §7 ("Cross-cutting concerns"). Find the bullet beginning `**Error contract:**`. Replace the entire bullet with:

```markdown
**Error contract (§17.9):** Every Level 0 stage follows the uniform stderr + exit-code error model. When `plcc-tokens` cannot tokenize its input, it emits a structured error on stderr and exits nonzero; `plcc-parser-table` does the same when it hits a syntax error in its token stream. Neither emits error records into the token stream or Error nodes into the parse tree. Orchestrators that drive the pipeline (`plcc-rep`, `plcc-parse`) detect upstream-first failure, capture the JSONL stderr from children (always spawned with `--verbose-format=json`), and report the first failing stage's error.
```

- [ ] **Step 3: Update the §5 `plcc-parser-table` row**

Locate §5 (or wherever the parser-table command contract is specified). If it references error recovery ("panic-mode", "recovery strategy TBD", "emits Error nodes at the recovery point"), replace those references with:

> On syntax error, `plcc-parser-table` emits a structured error on stderr per §17.9 and exits nonzero. No error recovery; no partial tree.

- [ ] **Step 4: Update the §5 `plcc-parser-table` internals**

Locate the internals description (it mentions "Error recovery" as a TBD item). Replace the error-recovery bullet with:

> **On error:** emit structured error via the verbose module's error helper per §17.9; return immediately with a nonzero exit code. No tree is produced.

- [ ] **Step 5: Update the status banner**

The document's status banner at the top still notes that several decisions are load-bearing including "error shape". Update the banner to reflect that the error shape is now settled per §17.9 (stderr + exit code; no tree-embedded errors).

- [ ] **Step 6: Cross-reference check**

Search for remaining references to "Error node", "in-band error", or the old error typing:

```bash
grep -nE "Error node|in-band error|error\.kind.*scanner|error\.kind.*parser" docs/design/2026-04-16-phase-2-part-1-ll1-parser-design.md
```

Expected after all edits: no matches. Fix any stragglers.

---

## Task 4 — Commit

**Files:**
- Git only.

- [ ] **Step 1: Verify test suite still green**

```bash
bin/test/all.bash
```

Expected: all tests pass with identical counts to Task 1 (no code changed).

- [ ] **Step 2: Stage and commit**

```bash
git add docs/design/2026-04-12-multi-lang-pipeline.md docs/design/2026-04-16-phase-2-part-1-ll1-parser-design.md
git commit -m "docs(design): retire §8 in-band errors; add §17.9 stderr+exit-code model; simplify Part 1 parse-tree schema"
```

- [ ] **Step 3: Verify the commit**

```bash
git log -1 --stat
```

Expected: two files changed, both design documents. No code files touched in this plan.

---

## Verification

This plan is doc-only. Verification is a reading pass plus a green-bar check:

- `bin/test/all.bash` — still passes, same counts as before.
- `grep -n "§8\|in-band error" docs/design/2026-04-12-multi-lang-pipeline.md` — matches only §8 (the pointer) and §17.9 (history).
- `grep -n "Error node\|in-band error" docs/design/2026-04-16-phase-2-part-1-ll1-parser-design.md` — no matches.
- Read §17.9 end-to-end; read §17.3, §17.7, §17.8 and confirm §17.9 doesn't contradict them; read §8 and confirm it now points to §17.9.

## Handoff

When this plan is complete and its commit is pushed:

1. Hand off to `docs/plans/2026-04-17-error-handling-2-code-sonnet.md` (start a fresh Sonnet session; the plan is self-contained).
2. Part 2 performs the mechanical code changes that the updated specs now describe.
3. Part 3 (Opus again) handles orchestrator pipefail.
