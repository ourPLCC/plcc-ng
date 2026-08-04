# Doc example drift — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the three `_run()` examples in `docs/` that exit 1 under the 2.0.0
contract, and leave behind a test tier that fails whenever a documented example
stops working or stops matching what its page claims.

**Architecture:** Each runnable example in `docs/` gets a fixture directory
under `tests/fixtures/docs/`. A new bats tier `tests/bats/docs/` runs each
fixture through the installed commands the page documents and diffs stdout
against the output the page prints, asserting exit 0. A pytest file
`tests/docs/example_block_test.py` extracts the page's fenced block and asserts
it is byte-identical to the fixture that was run. Fixture and doc block are
always edited as a pair. No `src/` change.

**Tech Stack:** bats-core 1.11.0 (pinned by `bin/install/bats.bash`), pytest
(stdlib `difflib`, `pathlib` only), GitHub Actions.

**Spec:** [2026-08-03-doc-example-drift-design.md](../specs/2026-08-03-doc-example-drift-design.md)
**Issues:** [181](../issues/done/181-docs-run-contract-stale-python-examples.md) (docs), [182](../issues/done/182-test-doc-example-drift.md) (test)

## Global Constraints

- Work in the `docs-run-contract-audit` worktree at
  `/workspaces/plcc-ng/.claude/worktrees/docs-run-contract-audit`, on branch
  `worktree-docs-run-contract-audit`. Always `cd` there explicitly at the start
  of every bash invocation; a bare shell may reset to the main checkout at
  `/workspaces/plcc-ng`, which is a *different* checkout on `main` and does not
  contain this work.
- **Do not modify anything under `src/`.** Both issues are classified `docs` and
  `test` and must stay that way so they do not bump the release version. No task
  in this plan changes `src/`; Task 6's red-proof mutations are confined to
  `docs/` and `tests/fixtures/`, and are reverted within the task and never
  committed.
- **A fixture's `spec.plcc` and its page's fenced block are one artifact in two
  places.** Never edit one without the other in the same step. The identity
  check exists to enforce this, and it will fail loudly if you forget.
- Bats tests never call `mktemp`; name paths under `BATS_TEST_TMPDIR` instead
  (`tests/bats/commands/bats-temp-dirs.bats` enforces this). Every bats file
  declares `bats_require_minimum_version 1.5.0` as its third line, after the
  shebang and a blank line.
- Do not write ad-hoc shell scripts. `bin/` has what you need; Task 5 adds the
  one new script this work requires, in `bin/` and matching existing style.
- Section headings in `docs/` use sentence case — capitalize only the first word
  and proper names.
- Commit messages follow conventional commits: scope `docs` for documentation
  content, `test` for fixtures, tiers, and runners, `ci` for workflow files.

### Background an implementer needs

Under the 2.0.0 `_run()` contract, the entry point **returns** a string. The
generated Python driver (`src/plcc/lang/ext/python/templates/main.py.jinja`)
checks the return value and raises `TypeError: _run() must return a string, got
<type>`, which `plcc-rep` reports as a specification error and exits 1.

All three `=== "Python"` tabs in `docs/` predate that change and call `print()`.
A `print()` returns `None`, so all three exit 1. The trap is that the printed
text still reaches the terminal, so the page's documented output appears
*above* the error — the example looks like it worked. That is why these shipped
in 2.0.0 and survived a release.

Java's tabs are all correct: `void _run()` could not compile under 2.0.0, so the
compiler forced them to be updated. That asymmetry is the whole reason this tier
is needed — statically-typed targets defend themselves, Python and JavaScript do
not.

One quirk you will see and must **not** "fix": for `docs/language-guide/examples.md`,
`plcc-scan` reports the source as `samples:1:1` while `plcc-parse` reports it as
`[-:1:1]` for the same file. That inconsistency is real current behavior and the
page records it faithfully. Transcribe it as-is. If it is ever fixed in `src/`,
this tier will fail and force the page to be updated, which is the mechanism
working correctly.

## File Structure

| File | Status | Responsibility |
|---|---|---|
| `tests/fixtures/docs/quick-start-{python,java}/` | Create (Task 1) | Runnable form of the `docs/quick-start.md` tabs |
| `tests/bats/docs/quick-start.bats` | Create (Task 1) | Behavior assertions for `docs/quick-start.md` |
| `bin/test/docs.bash` | Create (Task 1) | Tier runner: identity checks, then behavior tier |
| `docs/quick-start.md` | Modify (Task 1) | Python tab returns instead of printing |
| `tests/fixtures/docs/lang-guide-index-{python,java}/` | Create (Task 2) | Runnable form of the `docs/language-guide/index.md` tabs |
| `tests/bats/docs/language-guide-index.bats` | Create (Task 2) | Behavior assertions for that page |
| `docs/language-guide/index.md` | Modify (Task 2) | Python tab returns instead of printing |
| `tests/fixtures/docs/lang-guide-examples-{python,java}/` | Create (Task 3) | Runnable form of the `docs/language-guide/examples.md` tabs |
| `tests/bats/docs/language-guide-examples.bats` | Create (Task 3) | Behavior assertions for that page |
| `docs/language-guide/examples.md` | Modify (Task 3) | Python tab returns a *string* |
| `tests/docs/example_block_test.py` | Create (Task 4) | Extractor + identity check for all six fixtures |
| `docs/language-guide/semantic.md` | Modify (Task 5) | State the real `_run` contract |
| `bin/test/functional.bash` | Modify (Task 5) | Wire the tier into the aggregate runner (`all.bash` inherits it and is not touched) |
| `.github/workflows/docs-tests.yml` | Create (Task 5) | Run the tier on docs-only PRs |
| `.github/workflows/ci.yml` | Modify (Task 5) | Run the tier on code PRs |
| `CONTRIBUTING.md` | Modify (Task 5) | Document the tier and the fixture convention |
| `dev-docs/issues/18{1,2}-*.md` → `done/`, `dev-docs/roadmap.md` | Move/modify (Task 7) | Issue bookkeeping |

Each fixture directory holds the same five-or-three files, so the identity check
needs no per-fixture special cases:

```
tests/fixtures/docs/quick-start-python/
    spec.plcc          # byte-identical to the page's fenced block
    input              # program text
    expected-scan      # transcribed from observed output
    expected-parse
    expected-rep
```

`lang-guide-index-*` holds only `spec.plcc`, `input`, and `expected-rep`,
because that page documents no commands and no output.

Fixtures always use the names `spec.plcc` and `input`. Where a page tells the
reader to use different filenames — `docs/language-guide/examples.md` says
`subtract.plcc` and `samples` — the bats test copies them to those names in its
work directory. That keeps all six fixtures uniform for the identity check while
the behavior test still reproduces the page's commands exactly.

---

### Task 1: Tier runner, quick-start fixtures, and the quick-start fix

Builds the tier from nothing, proves it catches the real bug, then fixes the bug.

**Files:**
- Create: `bin/test/docs.bash`
- Create: `tests/fixtures/docs/quick-start-python/{spec.plcc,input,expected-scan,expected-parse,expected-rep}`
- Create: `tests/fixtures/docs/quick-start-java/{spec.plcc,input,expected-scan,expected-parse,expected-rep}`
- Create: `tests/bats/docs/quick-start.bats`
- Modify: `docs/quick-start.md:44-45`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: `bin/test/docs.bash`, invoked by every later task as
  `bin/test/docs.bash [path]`. With a path argument it runs only that bats file;
  with no argument it runs `pytest tests/docs/` then all of `tests/bats/docs/`.
  Also produces the fixture layout and the `_use` bats helper pattern that
  Tasks 2 and 3 follow.

- [ ] **Step 1: Create the tier runner**

Create `bin/test/docs.bash`:

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "bin/test/docs.bash"
echo "------------------"

SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( cd "${SCRIPT_DIR}/../.." &> /dev/null && pwd )"

# shellcheck source=bin/test/_cache.bash
source "${SCRIPT_DIR}/_cache.bash"

_run() {
    cd "${PROJECT_ROOT}"
    if [[ -z "${SKIP_SETUP:-}" ]]; then
        "${PROJECT_ROOT}/bin/install/bats.bash"
        pdm install
    fi
    export PATH="${PROJECT_ROOT}/.venv/bin:${PATH}"
    if [ -n "${1:-}" ]; then
        bats "$1"
        return
    fi
    pdm run pytest -qq tests/docs/
    bats tests/bats/docs/
}

run_cached /tmp/plcc-test-docs.log _run "$@"
```

Then make it executable:

```bash
cd /workspaces/plcc-ng/.claude/worktrees/docs-run-contract-audit
chmod +x bin/test/docs.bash
```

Three details copied deliberately from `bin/test/e2e.bash` and
`bin/test/integration.bash`, not invented here: the `SKIP_SETUP` guard (so
`functional.bash` can call this without reinstalling), prepending
`.venv/bin` to `PATH` (so bats sees the installed `plcc-*` entry points), and
`run_cached` with a tier-specific log path. The early return on a path argument
mirrors `e2e.bash` — narrowing to one bats file skips the pytest half, which is
what you want while iterating on a single page.

`pdm run pytest -qq tests/docs/` is used rather than `pdm test`, because
`pdm test` adds `--cov=plcc` and coverage of the shipped package is meaningless
for a docs consistency check.

- [ ] **Step 2: Create the Python fixture from the page as it stands today**

The point of this step is that the fixture starts out **broken**, exactly as the
page is broken. Do not fix anything yet.

Create `tests/fixtures/docs/quick-start-python/spec.plcc` with exactly this
content — it is `docs/quick-start.md` lines 26–46 with the four spaces of tab
indentation removed:

```
# Define the tokens of the language.
skip  WHITESPACE '\s+'
token NUM '\d+'

%

# Define the structure of the language.
# A program consists of a sequence of numbers.
<Program> **= <NUM:num>

%

# Define what happens when a program is run.
Python

Program
%%%
def _run(self):
  print(sum(int(str(num)) for num in self.numList))
%%%
```

Note the two-space body indent under `def _run(self):`. That is what the page
uses. Preserve it — normalizing it to four spaces would be a gratuitous change
and would break the identity check against the unmodified page.

Create `tests/fixtures/docs/quick-start-python/input` containing one line:

```
42 36 2
```

Create `tests/fixtures/docs/quick-start-python/expected-scan`:

```
-:1:1 NUM '42'
-:1:4 NUM '36'
-:1:7 NUM '2'
```

Create `tests/fixtures/docs/quick-start-python/expected-parse`:

```
Program
  NUM '42' [-:1:1]
  NUM '36' [-:1:4]
  NUM '2' [-:1:7]
```

Create `tests/fixtures/docs/quick-start-python/expected-rep`:

```
80
```

The source is `-` rather than a filename because the page pipes program text in
on stdin.

- [ ] **Step 3: Create the Java fixture**

Create `tests/fixtures/docs/quick-start-java/spec.plcc` — `docs/quick-start.md`
lines 51–75, de-indented:

```
# Define the tokens of the language.
skip  WHITESPACE '\s+'
token NUM '\d+'

%

# Define the structure of the language.
# A program consists of a sequence of numbers.
<Program> **= <NUM:num>

%

# Define what happens when a program is run.
Java

Program
%%%
public String _run() {
    int sum = 0;
    for (Token num : numList) {
        sum += Integer.parseInt(num.lexeme);
    }
    return String.valueOf(sum);
}
%%%
```

The `input`, `expected-scan`, `expected-parse`, and `expected-rep` files are
byte-identical to the Python fixture's — same grammar, same program, same
result. Copy them:

```bash
cd /workspaces/plcc-ng/.claude/worktrees/docs-run-contract-audit
cp tests/fixtures/docs/quick-start-python/{input,expected-scan,expected-parse,expected-rep} \
   tests/fixtures/docs/quick-start-java/
```

- [ ] **Step 4: Write the behavior tests**

Create `tests/bats/docs/quick-start.bats`:

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures/docs"
    WORK_DIR="${BATS_TEST_TMPDIR}/work"
    mkdir -p "${WORK_DIR}"
    cd "${WORK_DIR}"
}

# Lay a fixture out the way docs/quick-start.md tells the reader to: a
# spec.plcc in the working directory, found by automatic discovery, with
# program text arriving on stdin.
_use() {
    FIXTURE="${FIXTURES}/$1"
    cp "${FIXTURE}/spec.plcc" spec.plcc
}

@test "quick-start Python: plcc-scan matches the documented output" {
    _use quick-start-python
    run plcc-scan < "${FIXTURE}/input"
    [ "$status" -eq 0 ]
    [ "$output" = "$(cat "${FIXTURE}/expected-scan")" ]
}

@test "quick-start Python: plcc-parse matches the documented output" {
    _use quick-start-python
    run plcc-parse < "${FIXTURE}/input"
    [ "$status" -eq 0 ]
    [ "$output" = "$(cat "${FIXTURE}/expected-parse")" ]
}

@test "quick-start Python: plcc-rep matches the documented output and exits 0" {
    _use quick-start-python
    run plcc-rep < "${FIXTURE}/input"
    [ "$status" -eq 0 ]
    [ "$output" = "$(cat "${FIXTURE}/expected-rep")" ]
}

@test "quick-start Java: plcc-scan matches the documented output" {
    _use quick-start-java
    run plcc-scan < "${FIXTURE}/input"
    [ "$status" -eq 0 ]
    [ "$output" = "$(cat "${FIXTURE}/expected-scan")" ]
}

@test "quick-start Java: plcc-parse matches the documented output" {
    _use quick-start-java
    run plcc-parse < "${FIXTURE}/input"
    [ "$status" -eq 0 ]
    [ "$output" = "$(cat "${FIXTURE}/expected-parse")" ]
}

@test "quick-start Java: plcc-rep matches the documented output and exits 0" {
    _use quick-start-java
    run plcc-rep < "${FIXTURE}/input"
    [ "$status" -eq 0 ]
    [ "$output" = "$(cat "${FIXTURE}/expected-rep")" ]
}
```

Two things that matter:

- `[ "$status" -eq 0 ]` is the assertion that catches the bug in this issue. The
  output comparison alone would **pass** for the broken Python example, because
  the leaked `print` puts `80` on stdout. Only the exit status reveals the
  specification error. Never drop that line.
- `$output` has trailing newlines stripped by bats, and `$(cat …)` strips them
  too, so the comparison is well-defined without any trailing-whitespace
  fiddling in the `expected-*` files.

- [ ] **Step 5: Run the tier and confirm the three Python tests fail**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/docs-run-contract-audit
PLCC_NO_TEST_CACHE=1 bin/test/docs.bash tests/bats/docs/quick-start.bats
```

`PLCC_NO_TEST_CACHE=1` is needed because these are uncommitted working-tree
changes and you want a live run.

Expected: `1..6`, with **exactly one** failure — the Python `plcc-rep` test:

```
ok 1 quick-start Python: plcc-scan matches the documented output
ok 2 quick-start Python: plcc-parse matches the documented output
not ok 3 quick-start Python: plcc-rep matches the documented output and exits 0
ok 4 quick-start Java: plcc-scan matches the documented output
ok 5 quick-start Java: plcc-parse matches the documented output
ok 6 quick-start Java: plcc-rep matches the documented output and exits 0
```

Test 3 must fail on `status`, with `_run() must return a string, got NoneType`
visible in the output. That is the bug from issue #181.

Tests 1 and 2 **passing** against a broken spec is correct, not a symptom of a
misplaced fixture. `plcc-scan` runs `plcc-make --through=scan` and `plcc-parse`
runs `--through=parse`; neither reaches semantic validation or builds the
interpreter, so neither can observe a broken `_run()`. Only `plcc-rep` uses
`--through=all`. Verify with `src/plcc/cmd/{scan,parse,rep}.py` and `make.py`'s
stage table if you want to see it for yourself.

That narrows where the detection actually lives: for this class of bug the
`plcc-rep` test is the sole detector, and its `status` assertion is the sole
mechanism. The scan and parse tests still earn their place — they pin the output
those pages document — but they are not what catches a `_run()` regression.

If test 3 *passes*, stop: the fixture is not the broken version of the spec, and
you should re-check Step 2.

- [ ] **Step 6: Fix the page and the fixture together**

In `docs/quick-start.md`, replace line 45:

```
      print(sum(int(str(num)) for num in self.numList))
```

with:

```
      return str(sum(int(str(num)) for num in self.numList))
```

Mind the indentation: inside the tab that line carries six spaces (four for the
tab, two for the Python body).

Then make the identical change in
`tests/fixtures/docs/quick-start-python/spec.plcc`, where the line carries two
spaces:

```
  return str(sum(int(str(num)) for num in self.numList))
```

`str(...)` is required, not optional. `sum(...)` returns an `int`, and returning
an `int` is just as much a `specification_error` as returning `None` — it fails
with `got int`. The Java tab wraps the same value in `String.valueOf(...)` for
the same reason.

- [ ] **Step 7: Run the tier and confirm all six pass**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/docs-run-contract-audit
PLCC_NO_TEST_CACHE=1 bin/test/docs.bash tests/bats/docs/quick-start.bats
```

Expected: `1..6`, all `ok`.

- [ ] **Step 8: Commit**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/docs-run-contract-audit
git add bin/test/docs.bash tests/fixtures/docs tests/bats/docs docs/quick-start.md
git commit -m "$(cat <<'EOF'
test(docs): add doc-example tier and fix the quick-start Python example

The Python tab printed from _run() instead of returning, so it exited 1
with a specification_error under the 2.0.0 contract. The leaked print put
the documented output on stdout anyway, which is why it went unnoticed.

Adds bin/test/docs.bash and tests/bats/docs/, which assert exit status as
well as output — the output comparison alone passes for the broken
example.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: Language guide overview page

Same shape as Task 1, on a page that documents no commands and no output.

**Files:**
- Create: `tests/fixtures/docs/lang-guide-index-python/{spec.plcc,input,expected-rep}`
- Create: `tests/fixtures/docs/lang-guide-index-java/{spec.plcc,input,expected-rep}`
- Create: `tests/bats/docs/language-guide-index.bats`
- Modify: `docs/language-guide/index.md:25`

**Interfaces:**
- Consumes: `bin/test/docs.bash` from Task 1; the fixture layout and `_use`
  helper pattern from Task 1.
- Produces: nothing later tasks depend on beyond two more manifest entries for
  Task 4 (`lang-guide-index-python`, `lang-guide-index-java`).

- [ ] **Step 1: Create the Python fixture from the page as it stands**

Create `tests/fixtures/docs/lang-guide-index-python/spec.plcc` — this is
`docs/language-guide/index.md` lines 8–26, de-indented, still broken:

```
# Lexical section
skip WHITESPACE /\s+/
token NUM /\d+/

%

# Syntactic section
<Exp> ::= <NUM>

%

# Semantic section
Python

Exp
%%%
def _run(self):
    print("Hello")
%%%
```

This page uses slash-delimited patterns (`/\s+/`) and a four-space Python body
indent, unlike `quick-start.md`. Both are correct as written; transcribe them
exactly.

Create `tests/fixtures/docs/lang-guide-index-python/input`:

```
5
```

Create `tests/fixtures/docs/lang-guide-index-python/expected-rep`:

```
Hello
```

The page shows no commands and no output, so `input` and `expected-rep` are
authored here rather than transcribed. The grammar's start symbol is `Exp` and
the semantics ignore the parsed value, so any single number works as input.

- [ ] **Step 2: Create the Java fixture**

Create `tests/fixtures/docs/lang-guide-index-java/spec.plcc` — lines 31–50 of
the page, de-indented:

```
# Lexical section
skip WHITESPACE /\s+/
token NUM /\d+/

%

# Syntactic section
<Exp> ::= <NUM>

%

# Semantic section
Java

Exp
%%%
public String _run() {
    return "Hello";
}
%%%
```

```bash
cd /workspaces/plcc-ng/.claude/worktrees/docs-run-contract-audit
cp tests/fixtures/docs/lang-guide-index-python/{input,expected-rep} \
   tests/fixtures/docs/lang-guide-index-java/
```

- [ ] **Step 3: Write the behavior tests**

Create `tests/bats/docs/language-guide-index.bats`:

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures/docs"
    WORK_DIR="${BATS_TEST_TMPDIR}/work"
    mkdir -p "${WORK_DIR}"
    cd "${WORK_DIR}"
}

# This page shows a specification but no commands, so there is nothing to
# reproduce beyond running it. input and expected-rep are authored in the
# fixture rather than transcribed from the page.
_use() {
    FIXTURE="${FIXTURES}/$1"
    cp "${FIXTURE}/spec.plcc" spec.plcc
}

@test "language guide overview Python: the example runs and exits 0" {
    _use lang-guide-index-python
    run plcc-rep < "${FIXTURE}/input"
    [ "$status" -eq 0 ]
    [ "$output" = "$(cat "${FIXTURE}/expected-rep")" ]
}

@test "language guide overview Java: the example runs and exits 0" {
    _use lang-guide-index-java
    run plcc-rep < "${FIXTURE}/input"
    [ "$status" -eq 0 ]
    [ "$output" = "$(cat "${FIXTURE}/expected-rep")" ]
}
```

- [ ] **Step 4: Run the file and confirm the Python test fails**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/docs-run-contract-audit
PLCC_NO_TEST_CACHE=1 bin/test/docs.bash tests/bats/docs/language-guide-index.bats
```

Expected: `1..2`, with the Python test failing and the Java test passing:

```
not ok 1 language guide overview Python: the example runs and exits 0
ok 2 language guide overview Java: the example runs and exits 0
```

The Python failure must show `_run() must return a string, got NoneType`. Note
that `$output` will contain `Hello` — the leaked print — so this test would pass
on output alone. The `status` assertion is doing all the work.

- [ ] **Step 5: Fix the page and the fixture together**

In `docs/language-guide/index.md`, replace line 25:

```
        print("Hello")
```

with:

```
        return "Hello"
```

(eight spaces inside the tab: four for the tab, four for the Python body.)

Then the same change in
`tests/fixtures/docs/lang-guide-index-python/spec.plcc`, with four spaces:

```
    return "Hello"
```

No `str(...)` here — `"Hello"` is already a string.

- [ ] **Step 6: Run the file and confirm both pass**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/docs-run-contract-audit
PLCC_NO_TEST_CACHE=1 bin/test/docs.bash tests/bats/docs/language-guide-index.bats
```

Expected: `1..2`, all `ok`.

- [ ] **Step 7: Commit**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/docs-run-contract-audit
git add tests/fixtures/docs tests/bats/docs docs/language-guide/index.md
git commit -m "$(cat <<'EOF'
test(docs): cover the language guide overview example and fix its Python tab

Same pre-2.0.0 print idiom as the quick start: _run() printed instead of
returning, so the example exited 1.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: Subtraction language example

The page with the double bug, and the one whose commands use explicit filenames.

**Files:**
- Create: `tests/fixtures/docs/lang-guide-examples-python/{spec.plcc,input,expected-scan,expected-parse,expected-rep}`
- Create: `tests/fixtures/docs/lang-guide-examples-java/{spec.plcc,input,expected-scan,expected-parse,expected-rep}`
- Create: `tests/bats/docs/language-guide-examples.bats`
- Modify: `docs/language-guide/examples.md:44`

**Interfaces:**
- Consumes: `bin/test/docs.bash` from Task 1; the fixture layout from Task 1.
- Produces: two more manifest entries for Task 4
  (`lang-guide-examples-python`, `lang-guide-examples-java`).

- [ ] **Step 1: Create the Python fixture from the page as it stands**

Create `tests/fixtures/docs/lang-guide-examples-python/spec.plcc` — lines 27–57
of the page, de-indented, still broken:

```
# Subtraction language
skip WHITESPACE '\s+'
token WHOLE     '\d+'
token MINUS     '\-'
token LP        '\('
token RP        '\)'
token COMMA     ','
%
<Prog>         ::= <Exp:exp>
<Exp:WholeExp> ::= <WHOLE:whole>
<Exp:SubExp>   ::= MINUS LP <Exp:exp1> COMMA <Exp:exp2> RP
%
Python

Prog
%%%
def _run(self):
    print(self.exp.eval())
%%%

WholeExp
%%%
def eval(self):
    return int(self.whole.lexeme)
%%%

SubExp
%%%
def eval(self):
    return self.exp1.eval() - self.exp2.eval()
%%%
```

Create `tests/fixtures/docs/lang-guide-examples-python/input` — the `samples`
file from the page, which has blank lines between programs:

```
3

-(3,2)

-(-(4,1), -(3,2))
```

Create `tests/fixtures/docs/lang-guide-examples-python/expected-scan`:

```
samples:1:1 WHOLE '3'
samples:3:1 MINUS '-'
samples:3:2 LP '('
samples:3:3 WHOLE '3'
samples:3:4 COMMA ','
samples:3:5 WHOLE '2'
samples:3:6 RP ')'
samples:5:1 MINUS '-'
samples:5:2 LP '('
samples:5:3 MINUS '-'
samples:5:4 LP '('
samples:5:5 WHOLE '4'
samples:5:6 COMMA ','
samples:5:7 WHOLE '1'
samples:5:8 RP ')'
samples:5:9 COMMA ','
samples:5:11 MINUS '-'
samples:5:12 LP '('
samples:5:13 WHOLE '3'
samples:5:14 COMMA ','
samples:5:15 WHOLE '2'
samples:5:16 RP ')'
samples:5:17 RP ')'
```

Create `tests/fixtures/docs/lang-guide-examples-python/expected-parse`:

```
Prog
  WholeExp
    WHOLE '3' [-:1:1]
Prog
  SubExp
    WholeExp
      WHOLE '3' [-:3:3]
    WholeExp
      WHOLE '2' [-:3:5]
Prog
  SubExp
    SubExp
      WholeExp
        WHOLE '4' [-:5:5]
      WholeExp
        WHOLE '1' [-:5:7]
    SubExp
      WholeExp
        WHOLE '3' [-:5:13]
      WholeExp
        WHOLE '2' [-:5:15]
```

Yes, `plcc-scan` says `samples:` and `plcc-parse` says `[-:`, for the same file
in the same run. That is real current behavior and the page records it. Do not
"correct" it.

Create `tests/fixtures/docs/lang-guide-examples-python/expected-rep`:

```
3
1
2
```

- [ ] **Step 2: Create the Java fixture**

Create `tests/fixtures/docs/lang-guide-examples-java/spec.plcc` — lines 62–100
of the page, de-indented:

```
# Subtraction language
skip WHITESPACE '\s+'
token WHOLE     '\d+'
token MINUS     '\-'
token LP        '\('
token RP        '\)'
token COMMA     ','
%
<Prog>         ::= <Exp:exp>
<Exp:WholeExp> ::= <WHOLE:whole>
<Exp:SubExp>   ::= MINUS LP <Exp:exp1> COMMA <Exp:exp2> RP
%
Java

Prog
%%%
public String _run() {
    return String.valueOf(exp.eval());
}
%%%

Exp
%%%
public abstract int eval();
%%%

WholeExp
%%%
public int eval() {
    return Integer.parseInt(whole.lexeme);
}
%%%

SubExp
%%%
public int eval() {
    return exp1.eval() - exp2.eval();
}
%%%
```

The Java tab has an extra `Exp` block declaring `public abstract int eval();`
that the Python tab has no equivalent for. That is correct — Java needs the
abstract declaration on the base class, Python does not. Do not add one to the
Python fixture to "match".

```bash
cd /workspaces/plcc-ng/.claude/worktrees/docs-run-contract-audit
cp tests/fixtures/docs/lang-guide-examples-python/{input,expected-scan,expected-parse,expected-rep} \
   tests/fixtures/docs/lang-guide-examples-java/
```

- [ ] **Step 3: Write the behavior tests**

Create `tests/bats/docs/language-guide-examples.bats`:

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures/docs"
    WORK_DIR="${BATS_TEST_TMPDIR}/work"
    mkdir -p "${WORK_DIR}"
    cd "${WORK_DIR}"
}

# docs/language-guide/examples.md names its files subtract.plcc and samples,
# and passes both explicitly on the command line. Fixtures are stored under
# the uniform spec.plcc/input names, so rename on the way in.
_use() {
    FIXTURE="${FIXTURES}/$1"
    cp "${FIXTURE}/spec.plcc" subtract.plcc
    cp "${FIXTURE}/input" samples
}

@test "subtraction example Python: plcc-scan matches the documented output" {
    _use lang-guide-examples-python
    run plcc-scan -s subtract.plcc samples
    [ "$status" -eq 0 ]
    [ "$output" = "$(cat "${FIXTURE}/expected-scan")" ]
}

@test "subtraction example Python: plcc-parse matches the documented output" {
    _use lang-guide-examples-python
    run plcc-parse -s subtract.plcc samples
    [ "$status" -eq 0 ]
    [ "$output" = "$(cat "${FIXTURE}/expected-parse")" ]
}

@test "subtraction example Python: plcc-rep matches the documented output and exits 0" {
    _use lang-guide-examples-python
    run plcc-rep -s subtract.plcc samples
    [ "$status" -eq 0 ]
    [ "$output" = "$(cat "${FIXTURE}/expected-rep")" ]
}

@test "subtraction example Java: plcc-scan matches the documented output" {
    _use lang-guide-examples-java
    run plcc-scan -s subtract.plcc samples
    [ "$status" -eq 0 ]
    [ "$output" = "$(cat "${FIXTURE}/expected-scan")" ]
}

@test "subtraction example Java: plcc-parse matches the documented output" {
    _use lang-guide-examples-java
    run plcc-parse -s subtract.plcc samples
    [ "$status" -eq 0 ]
    [ "$output" = "$(cat "${FIXTURE}/expected-parse")" ]
}

@test "subtraction example Java: plcc-rep matches the documented output and exits 0" {
    _use lang-guide-examples-java
    run plcc-rep -s subtract.plcc samples
    [ "$status" -eq 0 ]
    [ "$output" = "$(cat "${FIXTURE}/expected-rep")" ]
}
```

- [ ] **Step 4: Run the file and confirm the three Python tests fail**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/docs-run-contract-audit
PLCC_NO_TEST_CACHE=1 bin/test/docs.bash tests/bats/docs/language-guide-examples.bats
```

Expected: `1..6`, with **exactly one** failure — the Python `plcc-rep` test,
showing `got NoneType`.

As in Task 1, the Python `plcc-scan` and `plcc-parse` tests pass against the
broken spec. Those commands stop at `--through=scan` and `--through=parse` and
never build the interpreter, so they cannot see a broken `_run()`. Only the
`plcc-rep` test detects this bug.

- [ ] **Step 5: Apply the naive fix and watch it still fail**

This step exists because the obvious fix is wrong, and a future maintainer
reaching for it should find it already documented as a dead end.

In `tests/fixtures/docs/lang-guide-examples-python/spec.plcc` only — not the
page yet — change:

```
    print(self.exp.eval())
```

to:

```
    return self.exp.eval()
```

Run just that fixture's rep test:

```bash
cd /workspaces/plcc-ng/.claude/worktrees/docs-run-contract-audit
PLCC_NO_TEST_CACHE=1 bin/test/docs.bash tests/bats/docs/language-guide-examples.bats
```

Expected: the Python `plcc-rep` test still fails, now with a different message:

```
Specification error: TypeError: _run() must return a string, got int
```

`eval()` returns an `int`. Mechanically rewriting `print(x)` to `return x`
trades one `specification_error` for another. Confirm you see `got int` before
moving on — that is the whole point of this step.

- [ ] **Step 6: Apply the real fix to the page and the fixture together**

In `docs/language-guide/examples.md`, replace line 44:

```
        print(self.exp.eval())
```

with:

```
        return str(self.exp.eval())
```

Then in `tests/fixtures/docs/lang-guide-examples-python/spec.plcc`, replace the
`return self.exp.eval()` line from Step 5 with:

```
    return str(self.exp.eval())
```

This mirrors the Java tab's `String.valueOf(exp.eval())`.

- [ ] **Step 7: Run the file and confirm all six pass**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/docs-run-contract-audit
PLCC_NO_TEST_CACHE=1 bin/test/docs.bash tests/bats/docs/language-guide-examples.bats
```

Expected: `1..6`, all `ok`.

- [ ] **Step 8: Commit**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/docs-run-contract-audit
git add tests/fixtures/docs tests/bats/docs docs/language-guide/examples.md
git commit -m "$(cat <<'EOF'
test(docs): cover the subtraction example and fix its Python tab

_run() printed an int instead of returning a string. Rewriting print(x)
to return x is not sufficient here — eval() returns an int, which is also
a specification_error. The fix wraps it in str(), mirroring the Java
tab's String.valueOf().

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: Identity check

The behavior tier proves the fixtures work. This proves the pages still contain
what the fixtures ran.

**Files:**
- Create: `tests/docs/example_block_test.py`

**Interfaces:**
- Consumes: all six fixture directories from Tasks 1–3, and the three modified
  pages.
- Produces: `extract_tabbed_block(md_text, tab_label) -> str` and the `MANIFEST`
  dict mapping fixture directory name → `(page path relative to docs/, tab
  label)`. Task 5 references neither directly; Task 6 mutates a fixture to
  red-proof this file.

- [ ] **Step 1: Write the extractor and its tests**

Create `tests/docs/example_block_test.py`:

```python
"""Assert every runnable spec in docs/ is byte-identical to its fixture.

Behaviour of these examples is covered by tests/bats/docs/, which runs the
fixtures through the real CLI. This file covers the other half: that what a
reader copies out of the documentation is exactly what those tests ran.

This lives here rather than co-located in src/ because it tests documentation
rather than a src module, and must not ship in the wheel. See CONTRIBUTING.md.
"""

import difflib
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOCS = PROJECT_ROOT / "docs"
FIXTURES = PROJECT_ROOT / "tests" / "fixtures" / "docs"

# Four spaces of indentation nest a fenced block inside a `=== "Tab"` block.
TAB_INDENT = "    "

# fixture directory -> (page, relative to docs/; tab label)
MANIFEST = {
    "quick-start-python": ("quick-start.md", "Python"),
    "quick-start-java": ("quick-start.md", "Java"),
    "lang-guide-index-python": ("language-guide/index.md", "Python"),
    "lang-guide-index-java": ("language-guide/index.md", "Java"),
    "lang-guide-examples-python": ("language-guide/examples.md", "Python"),
    "lang-guide-examples-java": ("language-guide/examples.md", "Java"),
}


def extract_tabbed_block(md_text, tab_label):
    """Return the first fenced code block inside the `=== "<tab_label>"` tab.

    The four spaces that nest the block inside the tab are stripped, so the
    result is directly comparable to a standalone file. Indentation relative
    to the block is preserved.
    """
    lines = md_text.split("\n")
    header = f'=== "{tab_label}"'

    for start, line in enumerate(lines):
        if line.strip() == header:
            break
    else:
        raise LookupError(f"no {header} tab found")

    i = start + 1
    while i < len(lines) and not lines[i].strip().startswith("```"):
        if lines[i].strip():
            raise LookupError(f"{header} is not followed by a fenced block")
        i += 1
    if i == len(lines):
        raise LookupError(f"{header} is not followed by a fenced block")

    body = []
    i += 1
    while i < len(lines) and not lines[i].strip().startswith("```"):
        line = lines[i]
        if line.startswith(TAB_INDENT):
            line = line[len(TAB_INDENT):]
        elif line.strip():
            raise LookupError(f"{header} block has an under-indented line: {line!r}")
        body.append(line)
        i += 1
    if i == len(lines):
        raise LookupError(f"{header} block is never closed")

    return "\n".join(body) + "\n"


def test_extract_selects_the_named_tab():
    md = (
        '=== "Python"\n    ```text\n    py\n    ```\n'
        '\n'
        '=== "Java"\n    ```text\n    java\n    ```\n'
    )
    assert extract_tabbed_block(md, "Java") == "java\n"


def test_extract_strips_the_tab_indent_but_keeps_relative_indentation():
    md = '=== "Python"\n    ```text\n    def _run(self):\n      return "x"\n    ```\n'
    assert extract_tabbed_block(md, "Python") == 'def _run(self):\n  return "x"\n'


def test_extract_keeps_blank_lines_inside_the_block():
    md = '=== "Python"\n    ```text\n    a\n\n    b\n    ```\n'
    assert extract_tabbed_block(md, "Python") == "a\n\nb\n"


def test_extract_raises_for_a_missing_tab():
    md = '=== "Python"\n    ```text\n    a\n    ```\n'
    with pytest.raises(LookupError, match="Haskell"):
        extract_tabbed_block(md, "Haskell")


def test_extract_raises_for_an_unclosed_block():
    md = '=== "Python"\n    ```text\n    a\n'
    with pytest.raises(LookupError, match="never closed"):
        extract_tabbed_block(md, "Python")


@pytest.mark.parametrize("fixture", sorted(MANIFEST))
def test_documented_block_matches_its_fixture(fixture):
    page, tab = MANIFEST[fixture]
    documented = extract_tabbed_block((DOCS / page).read_text(), tab)
    tested = (FIXTURES / fixture / "spec.plcc").read_text()
    if documented != tested:
        diff = "".join(
            difflib.unified_diff(
                tested.splitlines(keepends=True),
                documented.splitlines(keepends=True),
                fromfile=f"tests/fixtures/docs/{fixture}/spec.plcc",
                tofile=f'docs/{page}  === "{tab}"',
            )
        )
        pytest.fail(
            f'docs/{page} tab "{tab}" has drifted from its fixture.\n'
            f"tests/bats/docs/ runs the fixture, so the documentation is no "
            f"longer what was tested. Edit both or neither.\n\n{diff}"
        )
```

The five extractor tests are not ceremony. An identity check that silently
extracts the wrong text — or the empty string — passes forever and protects
nothing, which is worse than having no check at all. `test_extract_selects_the_named_tab`
is the one that matters most: every page here has a `Python` tab immediately
followed by a `Java` tab.

- [ ] **Step 2: Run the file and confirm all eleven tests pass**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/docs-run-contract-audit
bin/test/units.bash tests/docs/example_block_test.py
```

Expected: 11 passed — five extractor tests plus six parameterized identity
tests.

These pass on arrival, because Tasks 1–3 kept each fixture and its page in sync.
Step 3 is what proves the check has teeth.

- [ ] **Step 3: Red-proof the identity check**

Introduce a one-character drift into a fixture:

```bash
cd /workspaces/plcc-ng/.claude/worktrees/docs-run-contract-audit
sed -i 's/^token NUM /token NUMBER /' tests/fixtures/docs/quick-start-python/spec.plcc
bin/test/units.bash tests/docs/example_block_test.py
```

Expected: exactly one failure,
`test_documented_block_matches_its_fixture[quick-start-python]`, with a unified
diff showing `token NUMBER` on one side and `token NUM` on the other.

Then revert:

```bash
cd /workspaces/plcc-ng/.claude/worktrees/docs-run-contract-audit
git checkout -- tests/fixtures/docs/quick-start-python/spec.plcc
git status --short
bin/test/units.bash tests/docs/example_block_test.py
```

Expected: `git status --short` shows no change under `tests/fixtures/`, and all
11 tests pass again.

- [ ] **Step 4: Confirm the units tier still passes as a whole**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/docs-run-contract-audit
PLCC_NO_TEST_CACHE=1 bin/test/units.bash
```

Expected: the whole unit suite passes, now including 11 more tests.

`bin/test/units.bash` runs `pdm test`, which is bare `pytest` with no
`testpaths` restriction, so it collects `tests/docs/example_block_test.py`
alongside the co-located `src/**/*_test.py` files. That means this file runs
both here and in `bin/test/docs.bash`. That duplication is deliberate — see the
design doc — and buys having doc drift caught by the fastest tier. Do not add
config to suppress it.

- [ ] **Step 5: Commit**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/docs-run-contract-audit
git add tests/docs/example_block_test.py
git commit -m "$(cat <<'EOF'
test(docs): assert documented examples match the fixtures that were run

The bats tier proves the fixtures work; this proves the pages still
contain what the fixtures ran. Drift in either direction now fails with a
unified diff.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 5: Prose fix, runner wiring, CI, and CONTRIBUTING

Everything that makes the tier reachable and the convention discoverable.

**Files:**
- Modify: `docs/language-guide/semantic.md:42-47`
- Modify: `bin/test/functional.bash:18-31`
- Modify: `bin/test/all.bash:12-16`
- Create: `.github/workflows/docs-tests.yml`
- Modify: `.github/workflows/ci.yml`
- Modify: `CONTRIBUTING.md`

**Interfaces:**
- Consumes: `bin/test/docs.bash` from Task 1.
- Produces: `bin/test/docs.bash` reachable from `functional.bash` and
  `all.bash`, and from two CI jobs.

- [ ] **Step 1: Fix the semantic section prose**

In `docs/language-guide/semantic.md`, replace the whole `## Entry point: _run`
section (lines 42–47) with:

```markdown
## Entry point: `_run`

The start symbol's class inherits from `_Start`, which defines a `_run`
method that is called when you run a program with `plcc-rep`. `_run`
**returns** its output as a string; `plcc-rep` prints what it returns. The
default implementation returns a string representation of the parse tree
root. Override `_run` in your start class to implement your language's
semantics.

Returning something other than a string is a specification error, so
convert explicitly when your semantics produce another type. Do not print
or write to stdout from inside `_run` — that bypasses `plcc-rep`'s result
protocol. `plcc-rep` echoes the stray text as-is, so it surfaces in every
verbose format: under `plcc-rep --verbose-format=json` it lands among the
JSON records as a line that is not JSON, breaking any consumer that parses
the stream.

Signatures differ by target language — see your language's page below.
```

The old text said the default implementation "prints a string representation of
the parse tree root." It returns it: `src/plcc/lang/ext/python/emit.py` defines
`_Start._run` as `return str(self)`. This page is the language guide's
conceptual home for `_run` and previously never stated the return contract at
all, which is why three pages could drift from it unnoticed.

Headings stay sentence case, per CONTRIBUTING.

- [ ] **Step 1b: Correct the same false claim in the four other pages that carry it**

The `--verbose-format=json` sentence above was wrong in an earlier draft of this
plan, and the identical wrong claim is *already shipped* in four other pages.
Verified against the running CLI: a `_run()` that prints `LEAKED` and returns
`RETURNED-OK` produces, under `--verbose-format=json`:

```
LEAKED
{"kind": "result", "value": "RETURNED-OK"}
```

The leak is shown, not hidden. [rep.py:179-183](src/plcc/cmd/rep.py#L179-L183)
prints any line that is not a JSON dict with a `kind` key, unconditionally,
before `verbose_format` is ever consulted. So the true failure mode is stream
corruption — a non-JSON line among the JSON records — not silent omission.

In `docs/language-guide/languages/python.md`, `javascript.md`, and `java.md`,
each of which carries this sentence verbatim, replace:

```markdown
Do not print or write to stdout from inside `_run()` — that bypasses `plcc-rep`'s JSON result envelope. Plain-text mode will still show what you printed, but `plcc-rep --verbose-format=json` will not.
```

with:

```markdown
Do not print or write to stdout from inside `_run()` — that bypasses `plcc-rep`'s JSON result envelope. `plcc-rep` echoes the stray text as-is in every verbose format: plain-text mode shows it alongside the result, and `--verbose-format=json` emits it as a line that is not JSON among the JSON records, breaking any consumer that parses the stream.
```

In `docs/cli/guide/language-extensions.md`, replace:

```markdown
- The entry-point implementation itself must never write to stdout. Doing
  so bypasses the JSON envelope entirely; plain-text `plcc-rep` sessions
  will still show it (by accident, since unparseable lines are echoed
  as-is), but `plcc-rep --verbose-format=json` will not.
```

with:

```markdown
- The entry-point implementation itself must never write to stdout. Doing
  so bypasses the JSON envelope entirely. `plcc-rep` echoes unparseable
  lines as-is, so the stray text surfaces in every verbose format — and
  under `plcc-rep --verbose-format=json` it lands among the JSON records
  as a line that is not JSON, breaking consumers that parse the stream.
```

That page already described the mechanism correctly ("unparseable lines are
echoed as-is") and then drew the opposite conclusion from it, which is why the
error survived review for so long.

Nothing in this plan's tier can catch a wrong prose claim about behavior — the
tier executes examples, and these are sentences. That is a real limitation of
the design and worth stating plainly rather than implying the tier makes all doc
drift impossible.

- [ ] **Step 2: Wire the tier into functional.bash**

In `bin/test/functional.bash`, add the docs tier to the no-argument run. Replace:

```bash
    if [[ -z "${path}" ]]; then
        SKIP_SETUP=1 "${SCRIPT_DIR}/units.bash"
        SKIP_SETUP=1 "${SCRIPT_DIR}/commands.bash"
        SKIP_SETUP=1 "${SCRIPT_DIR}/integration.bash"
        SKIP_SETUP=1 "${SCRIPT_DIR}/e2e.bash"
        return
    fi
```

with:

```bash
    if [[ -z "${path}" ]]; then
        SKIP_SETUP=1 "${SCRIPT_DIR}/units.bash"
        SKIP_SETUP=1 "${SCRIPT_DIR}/commands.bash"
        SKIP_SETUP=1 "${SCRIPT_DIR}/integration.bash"
        SKIP_SETUP=1 "${SCRIPT_DIR}/e2e.bash"
        SKIP_SETUP=1 "${SCRIPT_DIR}/docs.bash"
        return
    fi
```

And add a routing case so a `tests/bats/docs/...` path goes to the right tier.
Replace:

```bash
    case "${path}" in
        tests/bats/commands*)    SKIP_SETUP=1 "${SCRIPT_DIR}/commands.bash" "${path}" ;;
        tests/bats/integration*) SKIP_SETUP=1 "${SCRIPT_DIR}/integration.bash" "${path}" ;;
        tests/bats/e2e*)         SKIP_SETUP=1 "${SCRIPT_DIR}/e2e.bash" "${path}" ;;
        *)                       SKIP_SETUP=1 "${SCRIPT_DIR}/units.bash" "${path}" ;;
    esac
```

with:

```bash
    case "${path}" in
        tests/bats/commands*)    SKIP_SETUP=1 "${SCRIPT_DIR}/commands.bash" "${path}" ;;
        tests/bats/integration*) SKIP_SETUP=1 "${SCRIPT_DIR}/integration.bash" "${path}" ;;
        tests/bats/e2e*)         SKIP_SETUP=1 "${SCRIPT_DIR}/e2e.bash" "${path}" ;;
        tests/bats/docs*)        SKIP_SETUP=1 "${SCRIPT_DIR}/docs.bash" "${path}" ;;
        *)                       SKIP_SETUP=1 "${SCRIPT_DIR}/units.bash" "${path}" ;;
    esac
```

The `docs*` case must come before the catch-all `*`, and the ordering among the
`tests/bats/*` cases does not otherwise matter since the prefixes are disjoint.

- [ ] **Step 3: Verify functional.bash routing works both ways**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/docs-run-contract-audit
PLCC_NO_TEST_CACHE=1 bin/test/functional.bash tests/bats/docs/quick-start.bats
```

Expected: only the docs tier runs, `1..6`, all `ok`. If you see the unit suite
run instead, the new `case` arm is in the wrong place or misspelled.

- [ ] **Step 4: Wire the tier into all.bash**

`bin/test/all.bash` calls `functional.bash`, which now includes the docs tier,
so no change is needed there. Confirm that is actually true rather than assuming
it:

```bash
cd /workspaces/plcc-ng/.claude/worktrees/docs-run-contract-audit
grep -n "docs" bin/test/all.bash bin/test/functional.bash
```

Expected: matches in `functional.bash` only. `all.bash` inherits the tier
through `functional.bash` and needs no edit. Leave it alone.

- [ ] **Step 5: Add the docs-only CI workflow**

Create `.github/workflows/docs-tests.yml`:

```yaml
name: Docs tests

on:
  pull_request:
    branches: [main]
    paths:
      - 'docs/**'
      - '*.md'
      - 'mkdocs.yml'
      - 'tests/fixtures/docs/**'
      - 'tests/bats/docs/**'
      - 'tests/docs/**'
      - 'bin/test/docs.bash'
      - '.github/workflows/docs-tests.yml'

jobs:
  docs:
    name: Documentation example tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.14'
      - uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: '17'
      - uses: actions/cache@v4
        with:
          path: .venv
          key: ${{ runner.os }}-venv-${{ hashFiles('pdm.lock') }}
      - name: Install PDM
        run: pip install pdm
      - name: Run documentation example tests
        env:
          PLCC_NO_TEST_CACHE: "1"
        run: bin/test/docs.bash
```

`setup-java` is required — three of the six fixtures are Java, and without a JDK
those tests fail. The `e2e` job in `ci.yml` is the precedent for the version and
distribution.

- [ ] **Step 6: Add a docs job to ci.yml**

`docs-tests.yml` alone is not enough. It fires on doc paths, so a change to
`src/plcc/lang/ext/python/emit.py` that breaks a working example would not
trigger it — which is precisely the 2.0.0 scenario this work exists to prevent.

Append this job to `.github/workflows/ci.yml`, after the `e2e` job and before
`e2e-haskell-roundtrip`:

```yaml
  docs:
    name: Documentation example tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.14'
      - uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: '17'
      - uses: actions/cache@v4
        with:
          path: .venv
          key: ${{ runner.os }}-venv-${{ hashFiles('pdm.lock') }}
      - name: Install PDM
        run: pip install pdm
      - name: Run documentation example tests
        env:
          PLCC_NO_TEST_CACHE: "1"
        run: bin/test/docs.bash
```

Do not touch `ci.yml`'s `paths-ignore`. Removing `docs/**` from it would make
every documentation typo run the full suite including the Haskell roundtrip;
these two jobs cover both directions far more cheaply. A PR touching both `src/`
and `docs/` runs the tier twice, which is accepted.

- [ ] **Step 7: Validate both workflow files parse**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/docs-run-contract-audit
pdm run python -c "
import yaml, pathlib
for p in ('.github/workflows/ci.yml', '.github/workflows/docs-tests.yml'):
    d = yaml.safe_load(pathlib.Path(p).read_text())
    print(p, sorted(d['jobs']))
"
```

Expected:

```
.github/workflows/ci.yml ['commands', 'docs', 'e2e', 'e2e-haskell-roundtrip', 'integration', 'package', 'units']
.github/workflows/docs-tests.yml ['docs']
```

If `pyyaml` is not available in the venv, skip this step — Step 8's review of
the diff is the fallback, and CI itself will reject a malformed workflow.

- [ ] **Step 8: Document the tier in CONTRIBUTING**

In `CONTRIBUTING.md`, add a row to the **Test** command table, immediately after
the `bin/test/e2e.bash` row:

```markdown
| [bin/test/docs.bash](bin/test/docs.bash) | Run the documentation example tests: the `tests/docs/` identity checks, then the `tests/bats/docs/` behavior tier. Accepts an optional path to narrow to one bats file. | After editing any runnable example in `docs/`. |
```

Add a row to the **Test tiers** table, immediately after the **End-to-end** row:

```markdown
| **Docs** | `tests/bats/docs/` (behavior) and `tests/docs/` (identity) | Every runnable specification in `docs/`, run through the commands its page documents and diffed against the output the page shows. The identity half asserts the page's fenced block is still byte-identical to the fixture that was run. |
```

In the `bin/test/functional.bash` row of the command table, the description
lists the tiers it runs. Update it to include the docs tier, so it reads
`units + commands + integration + e2e + docs` instead of
`units + commands + integration + e2e`.

Then add this subsection to **Documentation conventions**, after the existing
sentence-case paragraph:

```markdown
### Documentation examples

Every runnable specification in `docs/` has a fixture directory under
`tests/fixtures/docs/` holding the spec, its input, and the output each
documented command produces. [bin/test/docs.bash](bin/test/docs.bash) runs the
fixture through the real commands and asserts both the output and a zero exit
status, then asserts the page's fenced code block is byte-identical to the
fixture.

A page's fenced block and its fixture are one artifact stored in two places.
Change both in the same commit or the identity check fails. To add an example,
add the fixture first, register it in the `MANIFEST` in
`tests/docs/example_block_test.py`, and write the page from it.

Asserting the exit status is the point, not a formality. A Python or JavaScript
`_run()` that prints instead of returning still puts the expected text on
stdout, so an output-only comparison passes while the example is broken.

The identity check departs from the co-location rule above in two ways, both
deliberate. It lives in `tests/docs/` rather than beside a module in `src/`,
because it tests documentation rather than a `src` module and must not ship in
the wheel. And because `pdm test` runs bare `pytest` with no `testpaths`
restriction, the units tier collects it too — so it runs in both tiers. That is
kept on purpose: it means documentation drift is caught by the fastest tier.
Do not add pytest config to suppress the second run.
```

That closing paragraph is required, not optional garnish. It is the only place a
reader learns why `tests/docs/` sits outside `src/`, and without it the
docstring in `tests/docs/example_block_test.py` points at a CONTRIBUTING that
documents only the rule this file breaks.

- [ ] **Step 9: Commit**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/docs-run-contract-audit
git add docs/language-guide/semantic.md bin/test/functional.bash \
        .github/workflows/docs-tests.yml .github/workflows/ci.yml CONTRIBUTING.md
git commit -m "$(cat <<'EOF'
ci: run the doc example tier, and state the real _run contract

semantic.md described the pre-2.0.0 behaviour ("the default
implementation prints...") and never stated that _run returns a string,
despite being the language guide's conceptual home for it.

Two CI jobs, because a doc example breaks from two directions: a
docs-only PR (which ci.yml skips) and a src/ change (which the doc-path
trigger misses).

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 6: Red-proof both halves of the tier

Every test now passes, which is not by itself evidence that any of them detect
anything. The tier makes two independent claims, so this task falsifies them
one at a time: reintroduce issue #181 consistently and the *behavior* half must
fail; reintroduce it in the page alone and the *identity* half must fail.

**Nothing in this task is committed.** Every mutation is reverted within the
task.

**Files:**
- Temporarily modify, then revert: `docs/quick-start.md`,
  `tests/fixtures/docs/quick-start-python/spec.plcc`

**Interfaces:**
- Consumes: the full docs tier from Tasks 1–5.
- Produces: nothing.

- [ ] **Step 1: Reintroduce issue #181 in both copies at once**

This is the scenario where someone reverts the fix properly — page and fixture
together — so the identity check is satisfied and only behavior can catch it.

```bash
cd /workspaces/plcc-ng/.claude/worktrees/docs-run-contract-audit
sed -i 's/  return str(sum(int(str(num)) for num in self.numList))/  print(sum(int(str(num)) for num in self.numList))/' \
    tests/fixtures/docs/quick-start-python/spec.plcc
sed -i 's/      return str(sum(int(str(num)) for num in self.numList))/      print(sum(int(str(num)) for num in self.numList))/' \
    docs/quick-start.md
git diff --stat
```

Expected: exactly two files changed, one line each. If either file shows no
change, the `sed` pattern did not match — check the leading whitespace, which is
two spaces in the fixture and six in the page.

- [ ] **Step 2: Confirm the behavior half fails and the identity half does not**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/docs-run-contract-audit
PLCC_NO_TEST_CACHE=1 bin/test/docs.bash
```

Expected: all 11 pytest tests pass, and exactly one bats test fails —
`quick-start Python: plcc-rep matches the documented output and exits 0` —
showing `_run() must return a string, got NoneType`.

Three parts of that result matter:

- The identity tests **passing** is correct — the two copies agree with each
  other. They are just both wrong. This is why identity alone is insufficient.
- The `plcc-rep` test failing on `status` is the detection this whole plan
  exists for. Note that its `$output` still contains `80`, so it would have
  passed on output alone.
- The Python `plcc-scan` and `plcc-parse` tests **passing** is also correct:
  they stop before the interpreter is built and cannot see a broken `_run()`.
  For this class of bug the `plcc-rep` test is the only detector.

- [ ] **Step 3: Revert the fixture only, leaving the page broken**

Now the opposite scenario: someone edits a page and forgets the fixture.

```bash
cd /workspaces/plcc-ng/.claude/worktrees/docs-run-contract-audit
git checkout -- tests/fixtures/docs/quick-start-python/spec.plcc
git diff --stat
```

Expected: only `docs/quick-start.md` still modified.

- [ ] **Step 4: Confirm the identity half fails and the behavior half does not**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/docs-run-contract-audit
PLCC_NO_TEST_CACHE=1 bin/test/docs.bash
```

Expected: `test_documented_block_matches_its_fixture[quick-start-python]` fails
with a unified diff showing `print(...)` on the documentation side and
`return str(...)` on the fixture side. All 14 bats tests pass, because the
fixture — which is what they run — is correct again.

This is the case the behavior tier structurally cannot catch: it never reads the
`.md`. Without the identity check, a page could rot to arbitrary garbage while
the tier stayed green.

- [ ] **Step 5: Revert and confirm fully green**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/docs-run-contract-audit
git checkout -- docs/quick-start.md
git status --short
PLCC_NO_TEST_CACHE=1 bin/test/docs.bash
```

Expected: `git status --short` prints nothing, 11 pytest tests pass, and 14 bats
tests pass across the three files.

There is no commit in this task.

---

### Task 7: Full verification and close both issues

**Files:**
- Move: `dev-docs/issues/done/181-docs-run-contract-stale-python-examples.md` → `done/`
- Move: `dev-docs/issues/done/182-test-doc-example-drift.md` → `done/`
- Modify: `dev-docs/roadmap.md`

**Interfaces:**
- Consumes: a green tier from Task 6.
- Produces: nothing.

- [ ] **Step 1: Run the full functional suite**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/docs-run-contract-audit
PLCC_NO_TEST_CACHE=1 bin/test/functional.bash
```

Expected: units, commands, integration, e2e, and docs all pass. Two things to
watch for specifically:

- The units tier count grew by 11 — it collects
  `tests/docs/example_block_test.py` as well.
- `tests/bats/commands/bats-temp-dirs.bats` still passes. It enforces the
  `BATS_TEST_TMPDIR` and version-declaration rules across every bats file, and
  the three new files are now in its scope.

- [ ] **Step 2: Confirm the docs site still builds**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/docs-run-contract-audit
pdm run mkdocs build --strict
```

Expected: exit 0, no warnings. The `semantic.md` rewrite in Task 5 added no
links, but `--strict` is how this repo catches a broken one, and the build is
cheap.

- [ ] **Step 3: Close all three issues with the script**

Never move the files or edit the roadmap by hand — `close.bash` also rewrites
`dev-docs/` links pointing at each issue's old path, fixes the moved file's own
relative links for its new depth, and drops a `###` roadmap group left with no
entries.

```bash
cd /workspaces/plcc-ng/.claude/worktrees/docs-run-contract-audit
bin/issues/close.bash 181
bin/issues/close.bash 182
bin/issues/close.bash 183
```

Three, not two. #183 (the orphan nav entries and the missing strict-build gate)
was filed and fixed during this branch by Task 9, so it closes here with the
other two.

- [ ] **Step 4: Review what the script staged**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/docs-run-contract-audit
git status --short
git diff --cached
```

Expected: all three issue files moved to `dev-docs/issues/done/`, and both the
`### Docs` and `### Test` roadmap groups removed entirely — `### Test` held only
#182, and `### Docs` held only #181 and #183, so both groups empty out.
`dev-docs/specs/2026-08-03-doc-example-drift-design.md` and the issues'
cross-references to each other should now point at `issues/done/`, as should the
plan's own link to #183. Milestone prose is not auto-edited; if the roadmap
mentions any of the three in prose, fix it by hand now.

- [ ] **Step 5: Verify issue bookkeeping is consistent**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/docs-run-contract-audit
bin/issues/check.bash
```

Expected: `OK: 4 open issues, roadmap consistent, next id 184`.

Both numbers differ from an earlier draft of this plan: seven issues are open
before this step (six originally plus #183), and `.next-id.txt` advanced to 184
when #183 was created.

- [ ] **Step 6: Commit**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/docs-run-contract-audit
git add -A
git commit -m "$(cat <<'EOF'
docs(issues): close issues 181, 182, 183 (doc example drift), update roadmap

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
EOF
)"
```

This is the final commit of the branch, per the issue conventions.

---

### Task 8: Update the functional.bash coverage that Task 5 broke

**Run this BEFORE Task 7.** It is numbered 8 only because it was discovered
during Task 7; it belongs logically with Task 5 and must land before the
branch's final commit.

Task 5 added a fifth sub-script call and a fifth routing arm to
`bin/test/functional.bash`. `tests/bats/commands/test-scripts-path-filter.bats`
covers that script by copying it into a stub tree and stubbing each sub-script,
and it was never updated — so `functional.bash` now calls a `docs.bash` that the
stub tree does not contain, and the test dies with exit 127
(`docs.bash: No such file or directory`).

This is a plan defect, not an implementer error: the plan modified
`functional.bash` without checking what covered it. The regression is real and
was caught only by the full-suite run in Task 7, because Task 5's own
verification exercised the docs tier and the routing behaviour directly but not
the commands tier.

**Files:**
- Modify: `tests/bats/commands/test-scripts-path-filter.bats:67`, `:112-120`, and append one test

**Interfaces:**
- Consumes: `bin/test/functional.bash` as Task 5 left it — five sub-scripts in
  the no-argument path, and a `tests/bats/docs*` arm before the catch-all `*`.
- Produces: nothing later tasks depend on.

- [ ] **Step 1: Confirm the failure before changing anything**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/docs-run-contract-audit
PLCC_NO_TEST_CACHE=1 bin/test/commands.bash tests/bats/commands/test-scripts-path-filter.bats
```

Expected: one failure, `functional.bash: no argument runs all four sub-scripts`,
with `docs.bash: No such file or directory` and status 127 in the output. All
other tests in the file pass.

- [ ] **Step 2: Add `docs` to the stub tree**

In `tests/bats/commands/test-scripts-path-filter.bats:67`, change:

```bash
    for tier in units commands integration e2e; do
```

to:

```bash
    for tier in units commands integration e2e docs; do
```

- [ ] **Step 3: Update the no-argument test to assert all five**

Replace the whole final test (lines 112-120) with:

```bash
@test "functional.bash: no argument runs all five sub-scripts" {
    setup_functional_stub_tree
    "${STUB_ROOT}/bin/test/functional.bash"
    run cat "${ROUTE_LOG}"
    [[ "$output" == *"units "* ]]
    [[ "$output" == *"commands "* ]]
    [[ "$output" == *"integration "* ]]
    [[ "$output" == *"e2e "* ]]
    [[ "$output" == *"docs "* ]]
}
```

The name changes from "four" to "five". A test whose name miscounts what it
asserts is the same class of defect this branch exists to remove.

- [ ] **Step 4: Cover the new routing arm**

The file has one routing test per tier, and Task 5's `tests/bats/docs*` arm has
none — it was verified by hand during Task 5 but nothing pins it. Append, after
the `e2e-tier path` test and matching its form exactly:

```bash

@test "functional.bash: docs-tier path routes only to docs.bash" {
    setup_functional_stub_tree
    "${STUB_ROOT}/bin/test/functional.bash" "tests/bats/docs/quick-start.bats"
    [ "$(cat "${ROUTE_LOG}")" = "docs tests/bats/docs/quick-start.bats" ]
}
```

This is the test that would have caught the regression had it existed, and it
guards the arm against being reordered after the catch-all `*` later.

- [ ] **Step 5: Confirm the file passes**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/docs-run-contract-audit
PLCC_NO_TEST_CACHE=1 bin/test/commands.bash tests/bats/commands/test-scripts-path-filter.bats
```

Expected: all tests pass, one more than before (the new routing test).

- [ ] **Step 6: Commit**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/docs-run-contract-audit
git add tests/bats/commands/test-scripts-path-filter.bats
git commit -m "$(cat <<'EOF'
test(commands): cover the docs tier in functional.bash's routing tests

functional.bash gained a fifth sub-script and a fifth routing arm, but its
stub tree still stubbed only four, so the no-argument test died on a
missing docs.bash (exit 127). Adds docs to the stub tree, corrects the
test's name and assertions from four to five, and adds the per-tier
routing test the new arm was missing.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 9: Delete the orphan nav entries and gate strict builds in CI

**Run this BEFORE Task 7.** Numbered 9 because it was discovered during Task 7's
`mkdocs build --strict` step; it must land before the branch's final commit so
Task 7 can close #183 alongside #181 and #182.

Closes [#183](../issues/done/183-docs-orphan-plantuml-nav-entries.md).

`mkdocs build --strict` fails on three nav entries in `mkdocs.yml` that point at
pages which do not exist. They are leftovers from #113's diagram-command rename.
This predates the branch — `mkdocs.yml` is untouched by Tasks 1-8 and the same
three lines are on `main`'s tip — but it blocks Task 7's verification, and the
reason it survived is squarely this branch's subject: **nothing in CI runs
`mkdocs build --strict`.** `docs.yml` publishes via `mike deploy` (no `--strict`)
and only on push to `main` or release; `ci.yml` skips docs-only PRs entirely.

**Files:**
- Modify: `mkdocs.yml:88-90` (delete)
- Modify: `.github/workflows/docs-tests.yml` (add one step)

**Interfaces:**
- Consumes: `.github/workflows/docs-tests.yml` as Task 5 created it.
- Produces: nothing later tasks depend on, beyond #183 becoming closeable.

- [ ] **Step 1: Confirm the failure and that the targets are orphans**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/docs-run-contract-audit
pdm run mkdocs build --strict; echo "EXIT=$?"
grep -n "plcc-diagram-build\|plcc-diagram-emit\|plcc-diagram-run" mkdocs.yml
```

Expected: a nonzero exit naming the three missing `plcc-plantuml-diagram-*`
pages, and the grep showing `plcc-diagram-build`, `plcc-diagram-emit`, and
`plcc-diagram-run` **already present** in the nav at lines 62, 65, and 67. That
second check is what proves deletion loses nothing — do not skip it.

- [ ] **Step 2: Delete the three orphan entries**

In `mkdocs.yml`, delete exactly these three lines (88-90):

```yaml
      - plcc-plantuml-diagram-build: cli/commands/plcc-plantuml-diagram-build.md
      - plcc-plantuml-diagram-emit: cli/commands/plcc-plantuml-diagram-emit.md
      - plcc-plantuml-diagram-run: cli/commands/plcc-plantuml-diagram-run.md
```

Change nothing else in the file. Do not reorder or reformat the surrounding
alphabetical list.

- [ ] **Step 3: Confirm the strict build now passes**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/docs-run-contract-audit
pdm run mkdocs build --strict; echo "EXIT=$?"
```

Expected: `EXIT=0`, no warnings.

You may see a notice in the output recommending `pip install properdocs` for
"MkDocs 2.0". That is a real deprecation notice from `properdocs`, a legitimate
transitive dependency (`pdm.lock` pins 1.6.7 via `mkdocs-kroki-plugin`; see
[#156](../issues/156-mkdocs-1x-successor-decision.md)). **Do not install it, and
do not set any environment variable it suggests.** Choosing this project's
MkDocs successor is tracked separately in #156 and is not part of this task.

- [ ] **Step 4: Gate strict builds on documentation PRs**

In `.github/workflows/docs-tests.yml`, add a step to the `docs` job immediately
after the "Run documentation example tests" step:

```yaml
      - name: Build docs strictly
        run: pdm run mkdocs build --strict
```

This workflow already triggers on `docs/**`, `*.md`, and `mkdocs.yml`, so a PR
that breaks a nav target or a link now fails before merge. The gate belongs here
rather than in `docs.yml`, which runs only on push to `main` and on release —
a gate there would report the problem only after it had already shipped.

- [ ] **Step 5: Verify the workflow still parses**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/docs-run-contract-audit
pdm run python -c "
import yaml, pathlib
d = yaml.safe_load(pathlib.Path('.github/workflows/docs-tests.yml').read_text())
steps = [s.get('name') or s.get('uses') for s in d['jobs']['docs']['steps']]
print(steps)
"
```

Expected: the step list ends with `'Run documentation example tests'` followed by
`'Build docs strictly'`. If `pyyaml` is unavailable, say so and review the diff
by eye instead.

- [ ] **Step 6: Commit**

```bash
cd /workspaces/plcc-ng/.claude/worktrees/docs-run-contract-audit
git add mkdocs.yml .github/workflows/docs-tests.yml
git commit -m "$(cat <<'EOF'
docs: drop orphan plantuml nav entries and gate strict builds

mkdocs.yml still listed three command pages that #113's rename removed.
The renamed pages were already in the nav, so the entries were pure
orphans putting three dead links in the published site.

It survived because nothing in CI runs `mkdocs build --strict`: docs.yml
publishes via mike (no --strict) and only after merge, and ci.yml skips
docs-only PRs. Adds the gate to docs-tests.yml, which already triggers on
mkdocs.yml and docs/**, so a broken link fails the PR that introduces it.

Closes #183.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
EOF
)"
```

Note that the issue itself is closed by Task 7 via `bin/issues/close.bash 183`,
not here — this commit only does the work.
