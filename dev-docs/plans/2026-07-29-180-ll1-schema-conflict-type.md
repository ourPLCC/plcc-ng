# Describe `conflict_type` in the ll1 output schema — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `src/plcc/schemas/ll1.schema.json` require and constrain the
`conflict_type` key that `plcc-ll1` has always emitted on every conflict entry,
and prove the new clause bites with a mutation test.

**Architecture:** Three changes. A new fixture
`tests/fixtures/ll1-conflicts.plcc` — the repository's first deliberately
non-LL(1) grammar — produces a two-entry `conflicts` array covering both
`conflict_type` values. Two new tests in the existing
`tests/bats/commands/plcc-ll1.bats`: a positive control (real conflicting
output validates clean) and a two-case mutation loop (delete `conflict_type`,
then set it to a non-enum value; both must be rejected). One additive edit to
`ll1.schema.json` adds `"conflict_type"` to the conflicts item's `required`
array and an `enum` clause to its `properties`. No Python source changes: the
emitted shape is already correct, only its description was missing.

**Tech Stack:** bats-core (pinned by `bin/install/bats.bash`), `python3`
(stdlib `json` and `os` only), `check-jsonschema` (already a dev dependency in
`pyproject.toml`, already used by this file).

**Spec:** [2026-07-29-180-ll1-schema-conflict-type-design.md](../specs/2026-07-29-180-ll1-schema-conflict-type-design.md)
**Issue:** [180](../issues/done/180-ll1-schema-omits-conflict-type.md)

## Global Constraints

- Work in the `arbno-mid-body-terminal` worktree at
  `/workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal`, on branch
  `arbno-mid-body-terminal`. Always `cd` there explicitly at the start of every
  bash invocation; a bare shell may reset to the main checkout at
  `/workspaces/plcc-ng`, which is a *different* checkout on `main` and does not
  contain the #174/#176/#179 work this builds on. Running tests from the wrong
  directory produces confusing failures.
- **Do not add `additionalProperties: false`** to `ll1.schema.json` or to any
  other schema. None of the six schemas in `src/plcc/schemas/` use it. The
  issue and the spec both rule it out explicitly.
- **Do not change any `.py` file.** `plcc-ll1` already emits the correct shape.
  A plan step that edits `src/plcc/ll1/` means the schema is being written to
  match something other than reality — stop and re-read the spec.
- Do not touch the `arbno` section of the schema, or the `parse_table` section.
  Only the `conflicts` item changes. `arbno` was described by
  [#179](../issues/done/179-ll1-schema-omits-arbno-section.md) and is done.
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
- Every `.bats` file needs `bats_require_minimum_version 1.5.0` after the
  shebang. `tests/bats/commands/plcc-ll1.bats` already has it; do not remove or
  duplicate it.
- Do not add an entry to `docs/whats-new.md`. That file carries user-visible
  highlights; no runtime code reads `src/plcc/schemas/`, so nothing a user of
  PLCC-ng can observe changes here.
- Keep the tree green at every commit. The mutation test only passes once the
  schema clause exists, so the test and the schema edit land in the *same*
  commit (Task 2). Confirming the test is red before that commit is a required
  step, not an optional one.

---

## Background an implementer needs

`plcc-ll1` reads spec JSON on stdin and writes LL(1) analysis JSON on stdout.
When a grammar is not LL(1) it still exits 0; the trouble is reported in the
output, not the exit status. `build_ll1_result` in
`src/plcc/ll1/ll1_result_builder.py:67-89` walks the conflicting parse-table
cells and appends one entry per conflict:

```python
has_empty = any(len(cp["production"]) == 0 for cp in conflict_productions)
conflict_type = "first_follow" if has_empty else "first_first"
conflicts.append({
    "nonterminal": nt,
    "lookahead": lookahead,
    "conflict_type": conflict_type,
    "productions": conflict_productions,
})
```

So `conflict_type` is emitted unconditionally, and `first_first` /
`first_follow` are the only two reachable values.
`src/plcc/ll1/format_conflict_message.py:10` branches on it to choose between
two different diagnostic wordings, defaulting to `"first_first"` when the key
is absent.

`src/plcc/schemas/ll1.schema.json` does not mention `conflict_type`. Its
`conflicts` item declares `required: ["nonterminal", "lookahead",
"productions"]` and properties for exactly those three. Because no schema in
that directory sets `additionalProperties: false`, the fourth key is silently
accepted and validated as "anything goes."

**No test in this repository currently produces a conflicting grammar.** Every
fixture is LL(1)-clean, so every `check-jsonschema` call in the suite validates
`"conflicts": []` — an empty array, which `required` never reaches. Task 1
builds the first subject that reaches the section at all.

Two grammar shapes produce the two conflict types:

- **FIRST/FIRST** — two alternatives of the same nonterminal begin with the
  same token, so the parser cannot choose between them.
- **FIRST/FOLLOW** — a nullable nonterminal whose FIRST set and FOLLOW set
  share a token, so the parser cannot tell whether to take the non-empty
  production or the empty one.

The fixture in Task 1 contains one of each.

Note the `%` section separator in `.plcc` files is a **single** percent sign,
not `%%`. (The `%%%` fences that appear in some fixtures delimit semantic code
blocks, which this fixture does not have.)

---

## Task 1: Conflict fixture and positive control

Builds the subject Task 2 mutates, and pins the *accepting* direction: real
output with a populated `conflicts` array — including both `conflict_type`
values — must validate. Without this, Task 2's mutants could both be rejected
for reasons unrelated to the mutated key and its loop would prove nothing.

**Files:**
- Create: `tests/fixtures/ll1-conflicts.plcc`
- Modify: `tests/bats/commands/plcc-ll1.bats` (`setup()` at lines 5-12; new
  test appended after the `ll1 schema rejects arbno output missing any
  required key` test)

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: the shell variable `CONFLICT_SPEC_JSON`, set in `setup()` to
  `"${BATS_TEST_TMPDIR}/conflict-spec.json"` and holding the spec JSON for
  `tests/fixtures/ll1-conflicts.plcc`. Task 2 reads it.

- [ ] **Step 1: Create the fixture**

Create `tests/fixtures/ll1-conflicts.plcc` with exactly this content:

```text
# Deliberately non-LL(1): exercises both conflict_type values.
token X 'x'
token Y 'y'
skip  SPACE '\s+'
%
<Program> ::= <A:a> X <B:b>
<A:Some>  ::= X          # FIRST/FOLLOW: X starts <A> and also follows it
<A:None>  ::=
<B:One>   ::= Y          # FIRST/FIRST: both alternatives start with Y
<B:Two>   ::= Y X
```

`<A:None> ::=` with nothing after the `::=` is an empty production — that is
what makes `<A>` nullable and produces the FIRST/FOLLOW conflict. It is not a
truncated line. Both whole-line and trailing `#` comments are accepted by
`plcc-spec`; this content was verified verbatim.

- [ ] **Step 2: Verify the fixture produces the expected conflicts**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal
plcc-spec tests/fixtures/ll1-conflicts.plcc | plcc-ll1 | python3 -c "
import json, sys
d = json.load(sys.stdin)
assert d['is_ll1'] is False, d['is_ll1']
got = [(c['nonterminal'], c['lookahead'], c['conflict_type']) for c in d['conflicts']]
assert got == [('A', 'X', 'first_follow'), ('B', 'Y', 'first_first')], got
print('fixture OK')
"
```

Expected: `fixture OK`, with both commands exiting 0. `plcc-ll1` exits 0 on a
non-LL(1) grammar — a non-zero exit here means something other than the
conflict is wrong.

Entry order matters: `conflicts[0]` is the `A`/`first_follow` entry, and Task 2
mutates index `0`. The order is determined by sorting on nonterminal name,
then lookahead token — not the order rules were written in — and is stable
across runs. If this assertion fails on the tuple comparison, stop and
investigate rather than editing the assertion to match.

- [ ] **Step 3: Extend `setup()` with the conflict grammar's spec**

In `tests/bats/commands/plcc-ll1.bats`, `setup()` currently reads:

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

Add two lines so it reads:

```bash
setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    SCHEMA="$(git rev-parse --show-toplevel)/src/plcc/schemas/ll1.schema.json"
    SPEC_JSON="${BATS_TEST_TMPDIR}/spec.json"
    plcc-spec "${FIXTURES}/trivial.plcc" > "${SPEC_JSON}"
    ARBNO_SPEC_JSON="${BATS_TEST_TMPDIR}/arbno-spec.json"
    plcc-spec "${FIXTURES}/arbno-mid-body-terminal.plcc" > "${ARBNO_SPEC_JSON}"
    CONFLICT_SPEC_JSON="${BATS_TEST_TMPDIR}/conflict-spec.json"
    plcc-spec "${FIXTURES}/ll1-conflicts.plcc" > "${CONFLICT_SPEC_JSON}"
}
```

Change nothing else in `setup()`.

- [ ] **Step 4: Write the positive control test**

Append to `tests/bats/commands/plcc-ll1.bats`, after the existing
`@test "ll1 schema rejects arbno output missing any required key"` block and
before `@test "plcc-ll1 accepts -v without error"`:

```bash
# --- conflicts section of the output schema ------------------------------
#
# Every other fixture in this repository is LL(1)-clean, so every other
# schema check here validates an empty "conflicts": [] — which `required`
# never reaches. ll1-conflicts.plcc is the only grammar that populates it,
# with one entry of each conflict_type.

@test "plcc-ll1 output for a conflicting grammar is schema-valid" {
    run bash -c "plcc-ll1 < '${CONFLICT_SPEC_JSON}'"
    [ "$status" -eq 0 ]
    echo "$output" | check-jsonschema --schemafile "${SCHEMA}" -
}
```

`plcc-ll1` exits 0 on a non-LL(1) grammar, so `[ "$status" -eq 0 ]` is correct
here and is not a copy-paste slip from the tests above it.

- [ ] **Step 5: Run the test and verify it passes**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal
bin/test/commands.bash tests/bats/commands/plcc-ll1.bats
```

Expected: all tests pass, including the new one. This is a characterization
test — it passes both before and after the schema change, which is exactly what
a control should do. If it *fails* here, the fixture or `plcc-spec` is broken;
stop and investigate rather than proceeding.

- [ ] **Step 6: Commit**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal
git add tests/fixtures/ll1-conflicts.plcc tests/bats/commands/plcc-ll1.bats
git commit -m "test(plcc-ll1): validate output for a conflicting grammar"
```

---

## Task 2: Mutation test and the schema clause

The heart of the change. The test is written and proven red against the
unmodified schema first, then the schema clause makes it green, and both land
in one commit so `HEAD` is never broken.

**Files:**
- Modify: `tests/bats/commands/plcc-ll1.bats` (append after the Task 1 test)
- Modify: `src/plcc/schemas/ll1.schema.json` (the `conflicts` item's `required`
  array and `properties` object, around lines 50-55)

**Interfaces:**
- Consumes: `CONFLICT_SPEC_JSON` and `SCHEMA` from `setup()`, per Task 1.
- Produces: nothing later tasks depend on.

- [ ] **Step 1: Write the failing test**

Append to `tests/bats/commands/plcc-ll1.bats`, immediately after the positive
control added in Task 1:

```bash
# The schema must *constrain* conflict_type, not merely tolerate it. Two
# mutations of real plcc-ll1 output have to be rejected: dropping the key
# (proves `required`) and giving it an unknown value (proves the `enum`).
# Before issue 180 the schema did not mention conflict_type at all, so both
# mutants validated clean.
@test "ll1 schema rejects bad conflict_type in conflicts output" {
    LL1_JSON="${BATS_TEST_TMPDIR}/conflict-ll1.json"
    plcc-ll1 < "${CONFLICT_SPEC_JSON}" > "${LL1_JSON}"

    for mutation in \
        "delete:conflicts.0.conflict_type" \
        "set:conflicts.0.conflict_type"
    do
        kind="${mutation%%:*}"
        path="${mutation##*:}"
        mutant="${BATS_TEST_TMPDIR}/${kind}-${path}.json"
        MUTATE_KIND="${kind}" MUTATE_PATH="${path}" python3 -c '
import json, os, sys

doc = json.load(sys.stdin)
segments = os.environ["MUTATE_PATH"].split(".")
node = doc
for segment in segments[:-1]:
    node = node[int(segment)] if isinstance(node, list) else node[segment]
last = int(segments[-1]) if isinstance(node, list) else segments[-1]
if os.environ["MUTATE_KIND"] == "delete":
    del node[last]
else:
    node[last]  # raises if the path does not exist
    node[last] = "not_a_conflict_type"
json.dump(doc, sys.stdout)
' < "${LL1_JSON}" > "${mutant}"

        run check-jsonschema --schemafile "${SCHEMA}" "${mutant}"
        if [ "$status" -eq 0 ]; then
            echo "schema accepted ${kind} of ${path}" >&2
            return 1
        fi
    done
}
```

Four details that matter, so do not "simplify" them away:

- Each mutant is written to a **file** and passed to `check-jsonschema` by
  path, not piped. No JSON is ever interpolated into a shell string.
- The walker lets a bad path raise. `delete` raises through `del`; `set` raises
  through the bare `node[last]` read on the line before the assignment. Without
  that read, a typo'd path would silently *add* a key and the mutant would be
  accepted for the wrong reason.
- `conflicts.0` is the `A`/`first_follow` entry, verified in Task 1 Step 2.
  Either entry would do — both carry `conflict_type` — but the index must match
  a real entry.
- The loop packs kind and path into one string because bats runs under `set
  -u`-friendly plain bash with no associative-array helpers in this suite;
  `${mutation%%:*}` / `${mutation##*:}` is the same splitting idiom
  `tests/bats/integration/spec-ll1.bats:101-102` already uses for its
  `fixture:nt` pairs.

- [ ] **Step 2: Run the test and verify it FAILS**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal
bin/test/commands.bash tests/bats/commands/plcc-ll1.bats
```

Expected: `ll1 schema rejects bad conflict_type in conflicts output` **fails**,
with `schema accepted delete of conflicts.0.conflict_type` on stderr — the
loop's first iteration, because the unmodified schema does not require the key.
Every other test in the file passes.

This is the red proof. If the test passes at this step, the schema already
constrains something it should not, or the loop is not measuring what it
claims — stop and investigate. Do not proceed to Step 3 without seeing red.

- [ ] **Step 3: Add `conflict_type` to the conflicts item**

In `src/plcc/schemas/ll1.schema.json`, the `conflicts` item currently opens:

```json
    "conflicts": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["nonterminal", "lookahead", "productions"],
        "properties": {
          "nonterminal": { "type": "string" },
          "lookahead":   { "type": "string" },
          "productions": {
```

Change the `required` array and insert one property line, so it reads:

```json
    "conflicts": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["nonterminal", "lookahead", "conflict_type", "productions"],
        "properties": {
          "nonterminal":   { "type": "string" },
          "lookahead":     { "type": "string" },
          "conflict_type": { "enum": ["first_first", "first_follow"] },
          "productions": {
```

Everything from `"productions": {` onward is unchanged. Do not touch the
`parse_table` section, which contains a nearly identical `production`
sub-schema and is easy to edit by mistake — confirm the block you are editing
is the one under `"conflicts"`.

Three notes on the shape:

- `conflict_type` is **required**, not optional: `build_ll1_result` appends it
  on every entry with no conditional path.
- `enum` carries no sibling `"type": "string"`. JSON Schema's `enum` already
  constrains value and type both; the extra keyword would be redundant. This is
  the file's first enum.
- No `additionalProperties: false`. The ban from the Global Constraints applies
  here as much as anywhere.

- [ ] **Step 4: Verify the file is still valid JSON**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal
python3 -m json.tool src/plcc/schemas/ll1.schema.json > /dev/null && echo OK
```

Expected: `OK`. A misplaced comma in Step 3 is the likeliest mistake and this
catches it in one second instead of as a confusing bats failure.

- [ ] **Step 5: Run the commands tier and verify it passes**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal
bin/test/commands.bash tests/bats/commands/plcc-ll1.bats
```

Expected: every test passes, including both new ones. Both mutants are now
rejected, and the unmutated conflicting output still validates.

- [ ] **Step 6: Verify the stricter schema against the integration tier**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal
bin/test/integration.bash tests/bats/integration/spec-ll1.bats
```

Expected: all tests pass, unchanged. Every fixture that file uses is
LL(1)-clean, so their `conflicts` arrays are empty and the new `required` entry
is never reached. This step confirms the edit did not disturb the surrounding
`productions` sub-schema — a stray comma or brace there would red here.

- [ ] **Step 7: Commit**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal
git add src/plcc/schemas/ll1.schema.json tests/bats/commands/plcc-ll1.bats
git commit -m "fix(schema): describe conflict_type in the ll1 schema"
```

---

## Task 3: Full verification and issue closure

**Files:**
- Modify: `dev-docs/roadmap.md` (by script)
- Move: `dev-docs/issues/180-ll1-schema-omits-conflict-type.md` →
  `dev-docs/issues/done/` (by script)

**Interfaces:**
- Consumes: a green commands tier and integration tier from Task 2.
- Produces: nothing.

- [ ] **Step 1: Run the full functional suite**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal
bin/test/functional.bash
```

Expected: units, commands, integration, and e2e all pass. Only one schema, one
bats file, and one new fixture changed, and nothing globs `tests/fixtures/` —
every reference names a specific file — so a failure elsewhere means the enum
is wrong about output some other test produces. Investigate before closing.

- [ ] **Step 2: Close the issue**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal
bin/issues/close.bash 180
```

This moves the issue file to `dev-docs/issues/done/`, removes its Open Issues
entry from `dev-docs/roadmap.md`, rewrites `dev-docs/` links that pointed at
the old path — including the two references to #180 in #179's spec and plan —
and stages the result. It runs `bin/issues/check.bash` itself.

- [ ] **Step 3: Review the staged roadmap change**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal
git diff --cached dev-docs/roadmap.md
```

The script does not edit milestone rationale prose. Read the diff and confirm
no stale sentence now refers to #180 as open.

- [ ] **Step 4: Commit**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal
git add -A dev-docs
git commit -m "docs(issues): close issue 180 (ll1 schema conflict_type), update roadmap"
```

---

## Definition of done

- `src/plcc/schemas/ll1.schema.json` lists `"conflict_type"` in the conflicts
  item's `required` array and declares it as
  `{ "enum": ["first_first", "first_follow"] }`.
- No schema in `src/plcc/schemas/` sets `additionalProperties: false`.
- No `.py` file changed.
- `tests/fixtures/ll1-conflicts.plcc` exists and yields
  `[('A', 'X', 'first_follow'), ('B', 'Y', 'first_first')]`.
- `tests/bats/commands/plcc-ll1.bats` holds a positive control and a two-case
  mutation loop, and the mutation test was observed failing against the
  unmodified schema before the clause landed.
- `bin/test/functional.bash` is green.
- Issue 180 is in `dev-docs/issues/done/` and `bin/issues/check.bash` exits 0.
