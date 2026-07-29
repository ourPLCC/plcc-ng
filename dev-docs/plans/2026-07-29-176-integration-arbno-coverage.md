# Integration coverage for repetition rules (`**=`) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give the `plcc-spec | plcc-ll1` boundary regression coverage for all
three repetition-rule body shapes, so a recurrence of issue #174 fails in the
integration tier instead of surfacing as a wrong evaluated value in e2e.

**Architecture:** Nine tests appended to the existing
`tests/bats/integration/spec-ll1.bats`, each running `plcc-spec` piped into
`plcc-ll1` and asserting on the resulting JSON — schema validity via
`check-jsonschema`, structure via `python3 -c` reading stdin. One new
grammar-only fixture supplies the third body shape. No `src/` change.

**Tech Stack:** bats-core 1.11.0 (pinned by `bin/install/bats.bash`), `python3`
(stdlib `json` only), `check-jsonschema` (already a dev dependency and already
used by five files in this tier).

**Spec:** [2026-07-29-176-integration-arbno-coverage-design.md](../specs/2026-07-29-176-integration-arbno-coverage-design.md)
**Issue:** [176](../issues/done/176-integration-tier-has-no-arbno-coverage.md)

## Global Constraints

- Work in the `arbno-mid-body-terminal` worktree at
  `/workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal`, on branch
  `arbno-mid-body-terminal`. Always `cd` there explicitly at the start of every
  bash invocation; a bare shell may reset to the main checkout at
  `/workspaces/plcc-ng`, which is a *different* checkout on `main` and does not
  contain the #174 fix. Running tests from the wrong directory produces
  confusing failures.
- **Do not modify anything under `src/`.** Issue 176 is classified `test` and
  must stay that way, so it does not bump the release version. The one
  exception is the deliberate, temporary red-proof mutation in Task 5, which is
  reverted within the same task and never committed.
- Do not touch `src/plcc/schemas/ll1.schema.json`. The schema's failure to
  describe the `arbno` section is real but is tracked separately as
  [#179](../issues/done/179-ll1-schema-omits-arbno-section.md); a sibling gap in the
  `conflicts` section is [#180](../issues/done/180-ll1-schema-omits-conflict-type.md).
- All new tests go in the existing `tests/bats/integration/spec-ll1.bats`. Do
  not create a second file for this boundary — the tier names one file per
  pipeline boundary.
- Do not modify the existing `setup()` or the existing first test in that file.
  `FIXTURES` and `LL1_SCHEMA` are already defined and are all the new tests need.
- Bats tests never call `mktemp`; name paths under `BATS_TEST_TMPDIR` instead.
  (`tests/bats/commands/bats-temp-dirs.bats` enforces this.) No task in this
  plan needs a temporary file, so this should not come up.
- Run the tier with `bin/test/integration.bash
  tests/bats/integration/spec-ll1.bats`. Do not write an ad-hoc shell script to
  run tests — `bin/` already has what you need.
- Commit messages follow conventional commits, scope `test` for test and
  fixture changes.

## File Structure

| File | Status | Responsibility |
|---|---|---|
| `tests/bats/integration/spec-ll1.bats` | Modify (append only) | All assertions at the `plcc-spec \| plcc-ll1` boundary |
| `tests/fixtures/arbno-leading-terminal.plcc` | Create | Grammar whose repetition body *starts* with a non-capturing terminal |
| `dev-docs/issues/176-…md` → `done/` | Move (Task 6) | Issue bookkeeping |
| `dev-docs/roadmap.md` | Modify (Task 6) | Issue bookkeeping |

### Background an implementer needs

A repetition rule is written `<Nt> **= <body…>` and is internally called an
"arbno". `plcc-ll1` emits a top-level `arbno` key in its JSON output — an object
keyed by repetition nonterminal, `{}` when the grammar has none. Each entry has
three fields:

- `rhs` — the body symbols in order, each `{"symbol": str, "field": str|null,
  "is_terminal": bool}`. `field` is `null` for non-capturing symbols.
- `separator` — the separator token name, or `null` when the rule declares none.
- `lookahead` — the tokens that can start one iteration of the body.

`_handle_arbno` in `src/plcc/ll1/spec_json_decoder.py` builds this, and also
expands the rule into right-recursive internal rules (`Nt → body Nt#`,
`Nt# → body Nt# | ε`) used *only* to drive LL(1) analysis. Those internal
nonterminals must not leak into `parse_table`, `first_sets`, or `follow_sets`.

Issue #174 was a bug in that function: `rhs` was built from capturing symbols
only, silently dropping every non-capturing terminal in the body. It is already
fixed on this branch. Task 5 proves the new tests would have caught it.

---

### Task 1: Separator-form coverage

The baseline shape, and the one #174 never affected — its body is all-capturing,
so it is the control case.

**Files:**
- Modify: `tests/bats/integration/spec-ll1.bats` (append at end of file)

**Interfaces:**
- Consumes: `FIXTURES` and `LL1_SCHEMA`, already set by the file's existing
  `setup()`. `tests/fixtures/trivial-arbno.plcc`, which already exists and
  contains `<Rands> **= <Expr:expr> +COMMA`.
- Produces: the section comment and the two-test pattern that Tasks 2–4 follow.

- [ ] **Step 1: Append the section comment and the two tests**

Append verbatim to the end of `tests/bats/integration/spec-ll1.bats`:

```bash

# --- repetition rules (**=) ---------------------------------------------
#
# Three body shapes, three paths through _handle_arbno in
# src/plcc/ll1/spec_json_decoder.py: a separator form, a non-capturing
# terminal between two capturing symbols, and a non-capturing terminal
# leading the body. Issue 174 dropped every non-capturing terminal from
# arbno.<nt>.rhs, which in the leading case also shifted
# arbno.<nt>.lookahead onto the wrong symbol.

@test "plcc-spec | plcc-ll1 on a separator arbno grammar produces schema-valid ll1 JSON" {
    run bash -c "plcc-spec '${FIXTURES}/trivial-arbno.plcc' | plcc-ll1"
    [ "$status" -eq 0 ]
    echo "$output" | check-jsonschema --schemafile "${LL1_SCHEMA}" -
}

@test "separator arbno: rhs, separator, and lookahead are correct" {
    result=$(plcc-spec "${FIXTURES}/trivial-arbno.plcc" | plcc-ll1)
    echo "$result" | python3 -c "
import json, sys
arbno = json.load(sys.stdin)['arbno']
assert arbno['Rands'] == {
    'rhs': [{'field': 'exprList', 'symbol': 'Expr', 'is_terminal': False}],
    'separator': 'COMMA',
    'lookahead': ['NUM', 'PLUS'],
}, arbno['Rands']
"
}
```

Two details that matter and are easy to get wrong:

- The second test captures into `result` with `$(…)` **before** piping to
  `python3`, rather than piping the whole chain directly. Bats does not set
  `pipefail`, so in a direct `plcc-spec | plcc-ll1 | python3` chain only
  `python3`'s exit status is seen. Capturing first means a `plcc-ll1` crash
  yields empty output and `json.load` raises, which fails the test.
- The Python snippet uses single quotes for every string, because it sits
  inside a double-quoted bash string. Do not introduce `$` or backticks into it.

- [ ] **Step 2: Run the file and confirm all three tests pass**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal
bin/test/integration.bash tests/bats/integration/spec-ll1.bats
```

Expected: `1..3`, all `ok`. Test 1 is the pre-existing trivial-grammar test.

These are characterization tests — they pass on arrival by design, because the
behaviour they pin is correct today. Task 5 is where detection power is proven.

- [ ] **Step 3: Commit**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal
git add tests/bats/integration/spec-ll1.bats
git commit -m "test(integration): cover separator-form arbno at the spec|ll1 boundary"
```

---

### Task 2: Interior non-capturing terminal coverage

The shape from issue #174's title: a non-capturing terminal *between* two
capturing symbols.

**Files:**
- Modify: `tests/bats/integration/spec-ll1.bats` (append at end of file)

**Interfaces:**
- Consumes: `FIXTURES`, `LL1_SCHEMA`. `tests/fixtures/arbno-mid-body-terminal.plcc`,
  which already exists and contains `<Decls> **= <SYMBOL> EQUALS <Exp>`.
- Produces: nothing later tasks depend on.

- [ ] **Step 1: Append the three tests**

Append verbatim to the end of `tests/bats/integration/spec-ll1.bats`:

```bash

@test "mid-body-terminal arbno: plcc-spec | plcc-ll1 produces schema-valid ll1 JSON" {
    run bash -c "plcc-spec '${FIXTURES}/arbno-mid-body-terminal.plcc' | plcc-ll1"
    [ "$status" -eq 0 ]
    echo "$output" | check-jsonschema --schemafile "${LL1_SCHEMA}" -
}

@test "mid-body-terminal arbno: rhs keeps the non-capturing terminal (issue 174)" {
    result=$(plcc-spec "${FIXTURES}/arbno-mid-body-terminal.plcc" | plcc-ll1)
    echo "$result" | python3 -c "
import json, sys
arbno = json.load(sys.stdin)['arbno']
assert arbno['Decls']['rhs'] == [
    {'field': 'symbolList', 'symbol': 'SYMBOL', 'is_terminal': True},
    {'field': None, 'symbol': 'EQUALS', 'is_terminal': True},
    {'field': 'expList', 'symbol': 'Exp', 'is_terminal': False},
], arbno['Decls']['rhs']
"
}

@test "mid-body-terminal arbno: lookahead is the first body symbol" {
    result=$(plcc-spec "${FIXTURES}/arbno-mid-body-terminal.plcc" | plcc-ll1)
    echo "$result" | python3 -c "
import json, sys
arbno = json.load(sys.stdin)['arbno']
assert arbno['Decls']['lookahead'] == ['SYMBOL'], arbno['Decls']['lookahead']
"
}
```

The `rhs` assertion compares the whole list, not just the presence of `EQUALS`.
That way it also fails if a symbol is spuriously *added* or reordered, which a
`'EQUALS' in symbols` check would miss.

- [ ] **Step 2: Run the file and confirm all six tests pass**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal
bin/test/integration.bash tests/bats/integration/spec-ll1.bats
```

Expected: `1..6`, all `ok`.

- [ ] **Step 3: Commit**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal
git add tests/bats/integration/spec-ll1.bats
git commit -m "test(integration): cover interior-terminal arbno at the spec|ll1 boundary"
```

---

### Task 3: Leading non-capturing terminal coverage

The shape the issue names explicitly, and the only one where dropping the
terminal also corrupts `lookahead`. No fixture exists for it.

**Files:**
- Create: `tests/fixtures/arbno-leading-terminal.plcc`
- Modify: `tests/bats/integration/spec-ll1.bats` (append at end of file)

**Interfaces:**
- Consumes: `FIXTURES`, `LL1_SCHEMA`.
- Produces: `tests/fixtures/arbno-leading-terminal.plcc`, referenced again by
  Task 4.

- [ ] **Step 1: Create the fixture**

Create `tests/fixtures/arbno-leading-terminal.plcc` with exactly this content:

```
token BANG '!'
token NUM  '\d+'
skip  SPACE '\s+'
%
<Program> ::= <Items:items>
<Items>   **= BANG <Exp>
<Exp>     ::= <NUM:num>
```

This is grammar-only — there is no second `%` delimiter and no language section.
The fixture is consumed by `plcc-spec` and nothing downstream, so a semantics
block would be dead weight. `tests/fixtures/trivial.plcc` is the precedent; the
two existing arbno fixtures carry Python sections only because the e2e tier
evaluates them.

`BANG` is non-capturing (a bare token name, not `<BANG>`), so its `rhs` entry
gets `"field": null`. `<Exp>` is a bare nonterminal capture inside a repetition
body, so its field is the pluralized `expList`.

- [ ] **Step 2: Verify the fixture analyzes as expected**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal
plcc-spec tests/fixtures/arbno-leading-terminal.plcc | plcc-ll1
```

Expected: exit 0, and the `arbno` key reads

```json
"arbno": {"Items": {"rhs": [{"field": null, "symbol": "BANG", "is_terminal": true}, {"field": "expList", "symbol": "Exp", "is_terminal": false}], "separator": null, "lookahead": ["BANG"]}}
```

If `plcc-spec` is not on PATH, the venv is not active; run the command through
`bin/test/integration.bash` instead, which sets PATH itself.

- [ ] **Step 3: Append the three tests**

Append verbatim to the end of `tests/bats/integration/spec-ll1.bats`:

```bash

@test "leading-terminal arbno: plcc-spec | plcc-ll1 produces schema-valid ll1 JSON" {
    run bash -c "plcc-spec '${FIXTURES}/arbno-leading-terminal.plcc' | plcc-ll1"
    [ "$status" -eq 0 ]
    echo "$output" | check-jsonschema --schemafile "${LL1_SCHEMA}" -
}

@test "leading-terminal arbno: rhs keeps the leading non-capturing terminal (issue 174)" {
    result=$(plcc-spec "${FIXTURES}/arbno-leading-terminal.plcc" | plcc-ll1)
    echo "$result" | python3 -c "
import json, sys
arbno = json.load(sys.stdin)['arbno']
assert arbno['Items']['rhs'] == [
    {'field': None, 'symbol': 'BANG', 'is_terminal': True},
    {'field': 'expList', 'symbol': 'Exp', 'is_terminal': False},
], arbno['Items']['rhs']
"
}

@test "leading-terminal arbno: lookahead is the leading terminal, not the first capture (issue 174)" {
    result=$(plcc-spec "${FIXTURES}/arbno-leading-terminal.plcc" | plcc-ll1)
    echo "$result" | python3 -c "
import json, sys
arbno = json.load(sys.stdin)['arbno']
assert arbno['Items']['lookahead'] == ['BANG'], arbno['Items']['lookahead']
"
}
```

- [ ] **Step 4: Run the file and confirm all nine tests pass**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal
bin/test/integration.bash tests/bats/integration/spec-ll1.bats
```

Expected: `1..9`, all `ok`.

- [ ] **Step 5: Commit**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal
git add tests/fixtures/arbno-leading-terminal.plcc tests/bats/integration/spec-ll1.bats
git commit -m "test(integration): cover leading-terminal arbno at the spec|ll1 boundary"
```

---

### Task 4: Desugaring-leak guard

`_handle_arbno` expands each repetition into internal rules named `Nt` and
`Nt#`. Those are an analysis device, not part of the emitted grammar, and must
not appear in the output tables. The unit tier checks this for one hand-built
grammar; this checks it for real decoded specs across all three shapes.

**Files:**
- Modify: `tests/bats/integration/spec-ll1.bats` (append at end of file)

**Interfaces:**
- Consumes: `FIXTURES`. All three fixtures from Tasks 1–3.
- Produces: nothing.

- [ ] **Step 1: Append the test**

Append verbatim to the end of `tests/bats/integration/spec-ll1.bats`:

```bash

@test "arbno nonterminals and their desugared continuations stay out of the ll1 tables" {
    for pair in "trivial-arbno:Rands" "arbno-mid-body-terminal:Decls" "arbno-leading-terminal:Items"; do
        fixture="${pair%%:*}"
        nt="${pair##*:}"
        result=$(plcc-spec "${FIXTURES}/${fixture}.plcc" | plcc-ll1)
        echo "$result" | FIXTURE="${fixture}" NT="${nt}" python3 -c "
import json, os, sys
d = json.load(sys.stdin)
nt = os.environ['NT']
fixture = os.environ['FIXTURE']
for section in ('parse_table', 'first_sets', 'follow_sets'):
    keys = sorted(d[section])
    assert nt not in keys, (fixture, section, nt, keys)
    assert nt + '#' not in keys, (fixture, section, nt + '#', keys)
"
    done
}
```

The fixture name and nonterminal are passed to Python through **environment
variables**, not string interpolation. Interpolating bash variables into the
double-quoted Python snippet would require escaping and would break the moment a
value contained a quote. The assertion messages carry `fixture` and `section`,
so a failure identifies which of the three shapes broke and where.

- [ ] **Step 2: Run the file and confirm all ten tests pass**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal
bin/test/integration.bash tests/bats/integration/spec-ll1.bats
```

Expected: `1..10`, all `ok`.

- [ ] **Step 3: Commit**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal
git add tests/bats/integration/spec-ll1.bats
git commit -m "test(integration): assert desugared arbno nonterminals stay out of ll1 tables"
```

---

### Task 5: Red-proof the regression guards

Every test written so far passed the moment it was added, because #174 is
already fixed. That is not evidence any of them detect anything. This task
temporarily reintroduces the bug and confirms exactly the right tests fail.

**Nothing in this task is committed.** The mutation is reverted before the task
ends.

**Files:**
- Temporarily modify, then revert: `src/plcc/ll1/spec_json_decoder.py:55-63`

**Interfaces:**
- Consumes: the ten tests from Tasks 1–4.
- Produces: nothing.

- [ ] **Step 1: Reintroduce the #174 bug**

In `src/plcc/ll1/spec_json_decoder.py`, the `arbno_rhs` comprehension currently
reads:

```python
    arbno_rhs = [
        {
            "field": _arbno_field(s) if s.get("isCapturing", False) else None,
            "symbol": s["name"],
            "is_terminal": bool(s.get("isTerminal", False)),
        }
        for s in rhs
    ]
```

Add back the filter that #174 removed — one line, immediately after `for s in rhs`:

```python
    arbno_rhs = [
        {
            "field": _arbno_field(s) if s.get("isCapturing", False) else None,
            "symbol": s["name"],
            "is_terminal": bool(s.get("isTerminal", False)),
        }
        for s in rhs
        if s.get("isCapturing", False)
    ]
```

- [ ] **Step 2: Run the file and confirm exactly three tests fail**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal
PLCC_NO_TEST_CACHE=1 bin/test/integration.bash tests/bats/integration/spec-ll1.bats
```

`PLCC_NO_TEST_CACHE=1` is required here. The cache keys on git state, and this
mutation is an uncommitted working-tree change; bypassing the cache guarantees a
live run.

Expected: `1..10` with exactly these three failing, and all seven others passing:

```
not ok 5 mid-body-terminal arbno: rhs keeps the non-capturing terminal (issue 174)
not ok 8 leading-terminal arbno: rhs keeps the leading non-capturing terminal (issue 174)
not ok 9 leading-terminal arbno: lookahead is the leading terminal, not the first capture (issue 174)
```

Read that expected result carefully, because two of the near-misses are the
point of the exercise:

- Test 6 (`mid-body-terminal arbno: lookahead is the first body symbol`) must
  **pass** under the mutation. In `<Decls> **= <SYMBOL> EQUALS <Exp>` the first
  body symbol is capturing, so it survives the filter and the lookahead is still
  `SYMBOL` even while `rhs` is corrupt. Only a *leading* non-capturing terminal
  moves the lookahead. If test 6 fails, something other than the intended
  mutation is wrong.
- Tests 4 and 7 (the schema-validity tests) must also **pass** under the
  mutation. `ll1.schema.json` does not describe the `arbno` section at all, so
  `check-jsonschema` cannot see the corruption. That is exactly the gap recorded
  as #179, and observing it here is confirmation, not a defect in this work.

If more or fewer than these three fail, stop and investigate before continuing —
the tests are not measuring what the design claims.

- [ ] **Step 3: Revert the mutation**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal
git checkout -- src/plcc/ll1/spec_json_decoder.py
git status --short
```

Expected: `git status --short` prints nothing for `src/`. Confirm this before
moving on. Committing that mutation would reintroduce a shipped bug.

- [ ] **Step 4: Confirm the suite is green again**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal
PLCC_NO_TEST_CACHE=1 bin/test/integration.bash tests/bats/integration/spec-ll1.bats
```

Expected: `1..10`, all `ok`.

- [ ] **Step 5: Run the full functional suite**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal
bin/test/functional.bash
```

Expected: units, commands, integration, and e2e all pass. The new fixture is a
new file in `tests/fixtures/`; confirm nothing globs that directory and trips
over a grammar-only spec.

There is no commit in this task.

---

### Task 6: Close the issue

**Files:**
- Move: `dev-docs/issues/done/176-integration-tier-has-no-arbno-coverage.md` →
  `dev-docs/issues/done/`
- Modify: `dev-docs/roadmap.md`

**Interfaces:**
- Consumes: a green suite from Task 5.
- Produces: nothing.

- [ ] **Step 1: Close the issue with the script**

Never move the file or edit the roadmap by hand — `close.bash` also rewrites
`dev-docs/` links that point at the issue's old path, adjusts the moved file's
own relative links for its new depth, and drops a `###` roadmap group that has
no entries left. The `### Test` group also holds #178, so it stays.

```bash
cd /workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal
bin/issues/close.bash 176
```

- [ ] **Step 2: Review what the script staged**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal
git status --short
git diff --cached
```

Expected: the issue file moved to `done/` and its roadmap entry removed, with
the `### Test` heading still present because #178 remains under it. The design doc
`dev-docs/specs/2026-07-29-176-integration-arbno-coverage-design.md` and issues
#179 and #180 all link to the issue's old path — confirm the script repointed
them at `issues/done/`. Milestone rationale prose is not auto-edited; if the
roadmap mentions #176 in prose, fix it by hand now.

- [ ] **Step 3: Verify issue bookkeeping is consistent**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal
bin/issues/check.bash
```

Expected: `OK: 7 open issues, roadmap consistent, next id 181`.

- [ ] **Step 4: Commit**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal
git add -A
git commit -m "docs(issues): close issue 176 (integration arbno coverage), update roadmap"
```

This is the final commit of the branch, per the issue conventions.
