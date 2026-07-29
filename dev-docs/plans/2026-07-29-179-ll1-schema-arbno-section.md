# Describe the `arbno` section in the ll1 output schema — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `src/plcc/schemas/ll1.schema.json` describe the top-level `arbno`
key that `plcc-ll1` has always emitted, and prove the new clause constrains
something with the suite's first negative schema test.

**Architecture:** One additive edit to `ll1.schema.json` — `"arbno"` appended to
the top-level `required` array plus a matching `properties` entry — and two new
tests in the existing `tests/bats/commands/plcc-ll1.bats`. The first is a
positive control (real output for a repetition grammar validates clean). The
second deletes each of the seven newly-required keys from real output in turn
and asserts `check-jsonschema` rejects every mutant. No Python source changes:
the emitted shape is already correct, only its description was missing.

**Tech Stack:** bats-core (pinned by `bin/install/bats.bash`), `python3`
(stdlib `json` and `os` only), `check-jsonschema` (already a dev dependency in
`pyproject.toml`, already used by this file).

**Spec:** [2026-07-29-179-ll1-schema-arbno-section-design.md](../specs/2026-07-29-179-ll1-schema-arbno-section-design.md)
**Issue:** [179](../issues/179-ll1-schema-omits-arbno-section.md)

## Global Constraints

- Work in the `arbno-mid-body-terminal` worktree at
  `/workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal`, on branch
  `arbno-mid-body-terminal`. Always `cd` there explicitly at the start of every
  bash invocation; a bare shell may reset to the main checkout at
  `/workspaces/plcc-ng`, which is a *different* checkout on `main` and does not
  contain the #174 fix or the #176 tests. Running tests from the wrong
  directory produces confusing failures.
- **Do not add `additionalProperties: false`** to `ll1.schema.json` or to any
  other schema. None of the five schemas in `src/plcc/schemas/` use it. Adding
  it here would be an unrelated tightening with its own blast radius, and the
  issue rules it out explicitly.
- **Do not change any `.py` file.** `plcc-ll1` already emits the correct shape.
  A plan step that edits `src/plcc/ll1/` means the schema is being written to
  match something other than reality — stop and re-read the spec.
- Do not touch the `conflicts` section of the schema. Its missing
  `conflict_type` key is a real gap, tracked separately as
  [#180](../issues/180-ll1-schema-omits-conflict-type.md).
- Both new tests go in the existing `tests/bats/commands/plcc-ll1.bats`. Do not
  create a new file — the commands tier names one file per command.
- Do not modify the existing tests in that file. `setup()` gains two lines and
  nothing else changes.
- Bats tests never call `mktemp`; name paths under `BATS_TEST_TMPDIR` instead
  (`tests/bats/commands/bats-temp-dirs.bats` enforces this). No `teardown()`,
  no `trap`, no trailing `rm` — bats removes that directory itself.
- Do not use `assert_success`, `assert_failure`, `fail`, or any other
  `bats-assert` helper. That library is not installed. Use plain `[ ... ]`
  tests on `$status`, as every existing test in this repository does.
- Do not add an entry to `docs/whats-new.md`. That file carries user-visible
  highlights; no runtime code reads `src/plcc/schemas/`, so nothing a user of
  PLCC-ng can observe changes here.
- Keep the tree green at every commit. The negative test only passes once the
  schema clause exists, so the test and the schema edit land in the *same*
  commit (Task 2). Confirming the test is red before that commit is a required
  step, not an optional one.

---

## Background an implementer needs

`plcc-ll1` reads spec JSON on stdin and writes LL(1) analysis JSON on stdout.
Its output always includes a top-level `arbno` key describing repetition rules
(written `**=` in a `.plcc` grammar, called "arbno" internally). See
`build_ll1_result` in `src/plcc/ll1/ll1_result_builder.py:96-120`, which builds
`arbno_out` unconditionally and returns it — `{}` when the grammar has no
repetition rules.

Running the fixture this plan uses:

```bash
plcc-spec tests/fixtures/arbno-mid-body-terminal.plcc | plcc-ll1
```

produces, among the other top-level keys:

```json
"arbno": {
  "Decls": {
    "rhs": [
      { "field": "symbolList", "symbol": "SYMBOL", "is_terminal": true  },
      { "field": null,         "symbol": "EQUALS", "is_terminal": true  },
      { "field": "expList",    "symbol": "Exp",    "is_terminal": false }
    ],
    "separator": null,
    "lookahead": ["SYMBOL"]
  }
}
```

That single entry exercises every value shape the schema must accept: both
`true` and `false` for `is_terminal`, a populated `field` and a null one, and a
null `separator`. The `trivial.plcc` spec that `setup()` already builds yields
`"arbno": {}` and cannot serve as a subject here.

`src/plcc/schemas/ll1.schema.json` never mentions `arbno`. Because no schema in
that directory sets `additionalProperties: false`, the undeclared key is
silently accepted and validated as "anything goes."

---

## Task 1: Positive control for a repetition grammar

Establishes the subject (`ARBNO_SPEC_JSON`) that Task 2 mutates, and pins the
*accepting* direction: valid `arbno` output — including its null `field` and
null `separator` — must validate. Without this, Task 2's mutants could all be
rejected for reasons unrelated to the deleted key and its loop would prove
nothing.

**Files:**
- Modify: `tests/bats/commands/plcc-ll1.bats` (`setup()` at lines 5-10; new
  test appended after the existing "plcc-ll1 reads from stdin via pipe" test)

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: the shell variable `ARBNO_SPEC_JSON`, set in `setup()` to
  `"${BATS_TEST_TMPDIR}/arbno-spec.json"` and holding the spec JSON for
  `tests/fixtures/arbno-mid-body-terminal.plcc`. Task 2 reads it.

- [ ] **Step 1: Extend `setup()` with the repetition-grammar spec**

In `tests/bats/commands/plcc-ll1.bats`, `setup()` currently reads:

```bash
setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    SCHEMA="$(git rev-parse --show-toplevel)/src/plcc/schemas/ll1.schema.json"
    SPEC_JSON="${BATS_TEST_TMPDIR}/spec.json"
    plcc-spec "${FIXTURES}/trivial.plcc" > "${SPEC_JSON}"
}
```

Add two lines so it reads:

```bash
setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    SCHEMA="$(git rev-parse --show-toplevel)/src/plcc/schemas/ll1.schema.json"
    SPEC_JSON="${BATS_TEST_TMPDIR}/spec.json"
    plcc-spec "${FIXTURES}/trivial.plcc" > "${SPEC_JSON}"
    ARBNO_SPEC_JSON="${BATS_TEST_TMPDIR}/arbno-spec.json"
    plcc-spec "${FIXTURES}/arbno-mid-body-terminal.plcc" > "${ARBNO_SPEC_JSON}"
}
```

Change nothing else in `setup()`.

- [ ] **Step 2: Write the positive control test**

Append after the existing `@test "plcc-ll1 reads from stdin via pipe"` block:

```bash
# --- arbno section of the output schema ---------------------------------
#
# trivial.plcc has no repetition rules, so the two schema checks above
# validate an empty "arbno": {}. These use a grammar that populates it.

@test "plcc-ll1 output for a repetition grammar is schema-valid" {
    run bash -c "plcc-ll1 < '${ARBNO_SPEC_JSON}'"
    [ "$status" -eq 0 ]
    echo "$output" | check-jsonschema --schemafile "${SCHEMA}" -
}
```

- [ ] **Step 3: Run the test and verify it passes**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal
bin/test/commands.bash tests/bats/commands/plcc-ll1.bats
```

Expected: all tests pass, including the new one. This is a characterization
test — it passes both before and after the schema change, which is exactly what
a control should do. If it *fails* here, the fixture or `plcc-spec` is broken;
stop and investigate rather than proceeding.

- [ ] **Step 4: Commit**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal
git add tests/bats/commands/plcc-ll1.bats
git commit -m "test(plcc-ll1): validate output for a repetition grammar"
```

---

## Task 2: Negative test and the schema clause

The heart of the change. The test is written and proven red against the
unmodified schema first, then the schema clause makes it green, and both land
in one commit so `HEAD` is never broken.

**Files:**
- Modify: `tests/bats/commands/plcc-ll1.bats` (append after the Task 1 test)
- Modify: `src/plcc/schemas/ll1.schema.json` (line 6 `required` array; new
  entry in `properties`)

**Interfaces:**
- Consumes: `ARBNO_SPEC_JSON` and `SCHEMA` from `setup()`, per Task 1.
- Produces: nothing later tasks depend on.

- [ ] **Step 1: Write the failing test**

Append to `tests/bats/commands/plcc-ll1.bats`:

```bash
# The schema must *constrain* the arbno section, not merely tolerate it.
# Deleting any required key from real plcc-ll1 output has to be rejected.
# Before issue 179 the schema did not mention arbno at all, so every one
# of these mutants validated clean.
@test "ll1 schema rejects arbno output missing any required key" {
    LL1_JSON="${BATS_TEST_TMPDIR}/ll1.json"
    plcc-ll1 < "${ARBNO_SPEC_JSON}" > "${LL1_JSON}"

    for path in \
        "arbno" \
        "arbno.Decls.rhs" \
        "arbno.Decls.separator" \
        "arbno.Decls.lookahead" \
        "arbno.Decls.rhs.0.symbol" \
        "arbno.Decls.rhs.0.field" \
        "arbno.Decls.rhs.0.is_terminal"
    do
        mutant="${BATS_TEST_TMPDIR}/without-${path}.json"
        DROP_PATH="${path}" python3 -c '
import json, os, sys

doc = json.load(sys.stdin)
segments = os.environ["DROP_PATH"].split(".")
node = doc
for segment in segments[:-1]:
    node = node[int(segment)] if isinstance(node, list) else node[segment]
last = segments[-1]
del node[int(last) if isinstance(node, list) else last]
json.dump(doc, sys.stdout)
' < "${LL1_JSON}" > "${mutant}"

        run check-jsonschema --schemafile "${SCHEMA}" "${mutant}"
        if [ "$status" -eq 0 ]; then
            echo "schema accepted output missing ${path}" >&2
            return 1
        fi
    done
}
```

Three details that matter, so do not "simplify" them away:

- Each mutant is written to a **file** and passed to `check-jsonschema` by
  path, not piped. No JSON is ever interpolated into a shell string.
- The deleter lets `del` raise on a path that does not exist. A typo'd path
  therefore aborts the test with a non-zero `python3` exit instead of silently
  writing out an unmutated document that would then be accepted for the wrong
  reason.
- Index `0` of `rhs` is `SYMBOL`, whose `field` is the non-null `"symbolList"`.
  JSON Schema's `required` does not distinguish null from non-null, so deleting
  the entry that *has* a value is sufficient. The null `field` at index `1` is
  covered by Task 1's accepting direction.

- [ ] **Step 2: Run the test and verify it FAILS**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal
bin/test/commands.bash tests/bats/commands/plcc-ll1.bats
```

Expected: `ll1 schema rejects arbno output missing any required key` **fails**,
with `schema accepted output missing arbno` on stderr — the loop's first
iteration, because the unmodified schema does not require the key. Every other
test in the file passes.

This is the red proof. If the test passes at this step, the schema already
constrains something it should not, or the loop is not measuring what it
claims — stop and investigate. Do not proceed to Step 3 without seeing red.

- [ ] **Step 3: Add `arbno` to the schema's `required` array**

In `src/plcc/schemas/ll1.schema.json`, line 6 currently reads:

```json
  "required": ["is_ll1", "start_symbol", "first_sets", "follow_sets", "predict_sets", "parse_table", "conflicts", "left_recursion"],
```

Append `"arbno"`:

```json
  "required": ["is_ll1", "start_symbol", "first_sets", "follow_sets", "predict_sets", "parse_table", "conflicts", "left_recursion", "arbno"],
```

`arbno` is required rather than optional because the emitter always returns the
key — `{}` for a grammar with no repetition rules is the key *present* with an
empty value, not the key absent.

- [ ] **Step 4: Add the `arbno` entry to `properties`**

The `properties` object currently ends with `left_recursion` (lines 81-90),
followed by the closing braces of `properties` and the document. Add a comma
after `left_recursion`'s closing brace and insert `arbno` after it, so the tail
of the file reads:

```json
    "left_recursion": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["cycle"],
        "properties": {
          "cycle": { "type": "array", "items": { "type": "string" } }
        }
      }
    },
    "arbno": {
      "type": "object",
      "additionalProperties": {
        "type": "object",
        "required": ["rhs", "separator", "lookahead"],
        "properties": {
          "rhs": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["symbol", "field", "is_terminal"],
              "properties": {
                "symbol":      { "type": "string" },
                "field":       { "type": ["string", "null"] },
                "is_terminal": { "type": "boolean" }
              }
            }
          },
          "separator": { "type": ["string", "null"] },
          "lookahead": { "type": "array", "items": { "type": "string" } }
        }
      }
    }
  }
}
```

Two things to note. The `additionalProperties: {…}` map form is how this file
already keys by nonterminal in `first_sets`, `follow_sets`, and `parse_table` —
it constrains the *values* and is not the same thing as
`additionalProperties: false`, which stays banned. And `field` and `separator`
are both nullable *and* required: requiredness and nullability are separate
axes, exactly as the existing `parse_table` production items already treat
`field`.

- [ ] **Step 5: Verify the file is still valid JSON**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal
python3 -m json.tool src/plcc/schemas/ll1.schema.json > /dev/null && echo OK
```

Expected: `OK`. A misplaced comma in Step 4 is the likeliest mistake and this
catches it in one second instead of as a confusing bats failure.

- [ ] **Step 6: Run the commands tier and verify it passes**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal
bin/test/commands.bash tests/bats/commands/plcc-ll1.bats
```

Expected: every test passes, including both new ones. All seven deletions are
now rejected, and the unmutated output still validates.

- [ ] **Step 7: Verify the stricter schema against the integration tier**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal
bin/test/integration.bash tests/bats/integration/spec-ll1.bats
```

Expected: all ten tests pass. Four of them run `check-jsonschema` against this
schema using real output from all three repetition fixtures
(`trivial-arbno`, `arbno-mid-body-terminal`, `arbno-leading-terminal`). If the
new clause misdescribes the emitted shape — a wrong type, a key that is not
actually always present — this is where it surfaces, on a fixture Task 2 never
looked at.

- [ ] **Step 8: Commit**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal
git add src/plcc/schemas/ll1.schema.json tests/bats/commands/plcc-ll1.bats
git commit -m "fix(schema): describe the arbno section in the ll1 schema"
```

---

## Task 3: Full verification and issue closure

**Files:**
- Modify: `dev-docs/roadmap.md` (by script)
- Move: `dev-docs/issues/179-ll1-schema-omits-arbno-section.md` →
  `dev-docs/issues/done/` (by script)

**Interfaces:**
- Consumes: a green commands tier and integration tier from Task 2.
- Produces: nothing.

- [ ] **Step 1: Run the full functional suite**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal
bin/test/functional.bash
```

Expected: units, commands, integration, and e2e all pass. Nothing outside the
two `.bats` files and the schema changed, so a failure elsewhere means the
schema clause is wrong about output some other test produces — most likely a
grammar shape neither the commands nor the integration tier covers. Investigate
before closing.

- [ ] **Step 2: Close the issue**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal
bin/issues/close.bash 179
```

This moves the issue file to `dev-docs/issues/done/`, removes its Open Issues
entry from `dev-docs/roadmap.md`, rewrites `dev-docs/` links that pointed at
the old path, and stages the result. It runs `bin/issues/check.bash` itself.
The `### Fix` heading has other entries under it and stays.

- [ ] **Step 3: Review the staged roadmap change**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal
git diff --cached dev-docs/roadmap.md
```

The script does not edit milestone rationale prose. Read the diff and confirm
no stale sentence now refers to #179 as open.

- [ ] **Step 4: Commit**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal
git add -A dev-docs
git commit -m "docs(issues): close issue 179 (ll1 schema arbno section), update roadmap"
```

---

## Definition of done

- `src/plcc/schemas/ll1.schema.json` lists `"arbno"` in the top-level `required`
  array and describes it in `properties`, with `rhs`/`separator`/`lookahead`
  required per entry and `symbol`/`field`/`is_terminal` required per `rhs` item.
- No schema in `src/plcc/schemas/` sets `additionalProperties: false`.
- No `.py` file changed.
- `tests/bats/commands/plcc-ll1.bats` holds a positive control and a
  seven-case negative loop, and the negative test was observed failing against
  the unmodified schema before the clause landed.
- `bin/test/functional.bash` is green.
- Issue 179 is in `dev-docs/issues/done/` and `bin/issues/check.bash` exits 0.
