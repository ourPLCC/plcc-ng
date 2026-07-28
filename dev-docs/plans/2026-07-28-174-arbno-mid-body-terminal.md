# Arbno Mid-Body Non-Capturing Terminal Fix — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make an arbno (`**=`) body parse its non-capturing terminals instead of silently dropping them, so `<LetDecls> **= <SYMBOL> EQUALS <Exp>` parses.

**Architecture:** Two small source edits sharing one convention. `_handle_arbno` (`src/plcc/ll1/spec_json_decoder.py`) stops filtering the repeated body by `isCapturing` and instead emits `"field": None` for non-capturing symbols — the same `field: string|null` convention `_prod_entry` already uses for regular `::=` productions. `_parse_arbno` (`src/plcc/parser/predictive_parser.py`) then consumes every rhs item in order but appends only the ones with a non-`None` field, exactly as `_parse_regular` already does. Two adjacent bugs (arbno lookahead derived from the first *capturing* symbol instead of the first symbol) fix themselves once the body is complete, and get regression tests but no code.

**Tech Stack:** Python 3, pytest (unit tier), bats (e2e tier). No new dependencies.

## Global Constraints

- Design of record: `dev-docs/specs/2026-07-28-174-arbno-mid-body-terminal-design.md`. If anything here seems to contradict it, the spec wins — stop and reconcile before continuing.
- Work happens in the worktree `/workspaces/plcc-ng/.claude/worktrees/arbno-mid-body-terminal` on branch `arbno-mid-body-terminal`. All paths below are relative to that worktree root.
- Follow CONTRIBUTING.md's TDD loop: write the failing test, confirm the failure, write the minimal fix, confirm the pass. `bin/test/units.bash` must be green at every commit.
- Never write ad-hoc shell scripts — use the runners in `bin/`. Pass `PLCC_NO_TEST_CACHE=1` whenever a run must not be served from the test-output cache.
- `build_model.py::_extract_arbno_fields` keeps its `isCapturing` filter. Non-capturing symbols must not become fields of a generated class. Do not touch that function.
- `src/plcc/schemas/ll1.schema.json` does not describe the `arbno` key at all — no schema change is part of this fix.
- Commit messages follow conventional-commit style with scopes already in the log (`fix(ll1)`, `fix(parser)`, `test(ll1)`, `test(parser)`, `test(e2e)`, `docs(language-guide)`, `docs(issues)`).
- Every commit ends with the trailer `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.
- The branch's final commit closes issue #174 via `bin/issues/close.bash 174`.

---

### Task 1: Keep non-capturing symbols in the arbno runtime body

**Files:**
- Modify: `src/plcc/ll1/spec_json_decoder.py:55-63` (`_handle_arbno`'s `arbno_rhs` comprehension)
- Test: `src/plcc/ll1/spec_json_decoder_test.py` (append at end of file)

**Interfaces:**
- Consumes: nothing new. `_handle_arbno(grammar, arbno_rules, nt, rhs, separator_entry)` keeps its signature; `_arbno_field(sym)` and `_bare_field_name(sym)` are unchanged.
- Produces: `arbno_rules[nt]["rhs"]` is now a list with **one entry per rhs symbol, in body order**, each `{"field": str | None, "symbol": str, "is_terminal": bool}`. `field` is `None` exactly when the symbol is non-capturing. Task 2 (`_parse_arbno`) and Task 3 (`build_ll1_result`'s lookahead, which reads `rhs[0]`) both depend on this shape.

- [ ] **Step 1: Write the failing tests**

Append to `src/plcc/ll1/spec_json_decoder_test.py`, after `test_arbno_field_bare_multiword_nonterminal_decapitalizes` (the last function in the file). The helpers `_spec`, `_rule`, `_arbno_rule`, `_terminal`, `_nonterminal` already exist at the top of that file — do not redefine them.

```python
def test_arbno_keeps_mid_body_noncapturing_terminal_with_null_field():
    """Regression for issue #174: a non-capturing terminal between two
    captures must survive into the runtime arbno body with field None,
    so the parser still shifts it. Before the fix it was filtered out
    entirely and the parser tried to parse <Exp> at the EQUALS."""
    spec = _spec([
        _arbno_rule("letDecls",
                    [_terminal("SYMBOL", capturing=True),
                     _terminal("EQUALS"),
                     _nonterminal("Exp", capturing=True)],
                    None),
        _rule("Exp", [_terminal("NUM")]),
    ])
    grammar, productions, arbno_rules = decode(spec)
    assert arbno_rules["letDecls"]["rhs"] == [
        {"field": "symbolList", "symbol": "SYMBOL", "is_terminal": True},
        {"field": None, "symbol": "EQUALS", "is_terminal": True},
        {"field": "expList", "symbol": "Exp", "is_terminal": False},
    ]


def test_arbno_keeps_leading_and_trailing_noncapturing_terminals():
    spec = _spec([
        _arbno_rule("items",
                    [_terminal("BANG"),
                     _nonterminal("Exp", capturing=True),
                     _terminal("SEMI")],
                    None),
        _rule("Exp", [_terminal("NUM")]),
    ])
    grammar, productions, arbno_rules = decode(spec)
    assert arbno_rules["items"]["rhs"] == [
        {"field": None, "symbol": "BANG", "is_terminal": True},
        {"field": "expList", "symbol": "Exp", "is_terminal": False},
        {"field": None, "symbol": "SEMI", "is_terminal": True},
    ]


def test_arbno_all_noncapturing_body_is_not_empty():
    """<Bangs> **= BANG captures nothing, but the body still has to be
    parsed. An empty rhs makes ll1_result_builder compute an empty
    lookahead, which makes the arbno match zero iterations against any
    input."""
    spec = _spec([
        _arbno_rule("bangs", [_terminal("BANG")], None),
    ])
    grammar, productions, arbno_rules = decode(spec)
    assert arbno_rules["bangs"]["rhs"] == [
        {"field": None, "symbol": "BANG", "is_terminal": True}
    ]
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
bin/test/units.bash src/plcc/ll1/spec_json_decoder_test.py
```

Expected: the three new tests FAIL. The first two fail with the non-capturing
entries missing from the actual list (e.g. actual is
`[{'field': 'symbolList', ...}, {'field': 'expList', ...}]`); the third fails
with `assert [] == [{'field': None, ...}]`. Every pre-existing test in the file
still passes.

- [ ] **Step 3: Write the minimal implementation**

In `src/plcc/ll1/spec_json_decoder.py`, replace the `arbno_rhs` comprehension in `_handle_arbno`:

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

Nothing else in the function changes — the LL(1) expansion above it already
included every symbol.

- [ ] **Step 4: Run the tests to verify they pass**

```bash
bin/test/units.bash src/plcc/ll1/spec_json_decoder_test.py
```

Expected: PASS, including the pre-existing arbno tests (their bodies are
all-capturing, so their expected `rhs` lists are unchanged).

- [ ] **Step 5: Run the whole unit tier**

```bash
bin/test/units.bash
```

Expected: PASS. Nothing else reads `arbno_rules[...]["rhs"]` — `build_model.py`
derives class fields from the spec JSON directly, not from this structure.

- [ ] **Step 6: Commit**

```bash
git add src/plcc/ll1/spec_json_decoder.py src/plcc/ll1/spec_json_decoder_test.py
git commit -m "fix(ll1): keep non-capturing symbols in the arbno runtime body

Non-capturing terminals in a **= body were filtered out of the runtime
arbno metadata, so the parser never shifted them. Keep every rhs symbol
and mark non-capturing ones with field: None, matching the convention
regular productions already use.

Refs #174

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 2: Shift-and-discard non-capturing symbols in `_parse_arbno`

**Files:**
- Modify: `src/plcc/parser/predictive_parser.py:179-231` (`_parse_arbno`, specifically the `list_fields` dict comprehension and the `parse_iteration` body)
- Test: `src/plcc/parser/predictive_parser_test.py` (append at end of file)

**Interfaces:**
- Consumes: the arbno entry shape Task 1 produces — `ll1["arbno"][sym]["rhs"]` is a list of `{"field": str | None, "symbol": str, "is_terminal": bool}` in body order, plus the existing `"separator"` and `"lookahead"` keys.
- Produces: no signature change. `parse(ll1, tokens, tracer=None) -> (tree_dict, consumed_count, extensible)` behaves as before for bodies whose symbols all capture; an item with `field is None` is now consumed (a terminal via `expect`, which raises `ParseError` if absent) and contributes to the node's source span but to no child list.

- [ ] **Step 1: Write the failing tests**

Append to `src/plcc/parser/predictive_parser_test.py`. `_tok(name, lexeme, line=1, col=1, file="<stdin>")` and `pytest` are already imported/defined at the top of that file — do not redefine them. Add the two ll1 fixtures first, then the tests:

```python
# ll1 dict for: letDecls **= SYMBOL EQUALS exp  (EQUALS non-capturing), exp → NUM
_LET_DECLS_LL1 = {
    "is_ll1": True,
    "start_symbol": "letDecls",
    "parse_table": {
        "exp": {
            "NUM": {"alt": None, "production": [{"symbol": "NUM", "field": "num"}]}
        }
    },
    "arbno": {
        "letDecls": {
            "rhs": [
                {"field": "symbolList", "symbol": "SYMBOL", "is_terminal": True},
                {"field": None, "symbol": "EQUALS", "is_terminal": True},
                {"field": "expList", "symbol": "exp", "is_terminal": False},
            ],
            "separator": None,
            "lookahead": ["SYMBOL"],
        }
    }
}

# ll1 dict for: bangs **= BANG  (nothing in the body captures)
_BANGS_LL1 = {
    "is_ll1": True,
    "start_symbol": "bangs",
    "parse_table": {},
    "arbno": {
        "bangs": {
            "rhs": [{"field": None, "symbol": "BANG", "is_terminal": True}],
            "separator": None,
            "lookahead": ["BANG"],
        }
    }
}


def _let_decls_tokens():
    return [
        _tok("SYMBOL", "three"),
        _tok("EQUALS", "="),
        _tok("NUM", "2"),
        _tok("SYMBOL", "four"),
        _tok("EQUALS", "="),
        _tok("NUM", "5"),
    ]


def test_arbno_mid_body_noncapturing_terminal_is_consumed():
    """Regression for issue #174: every token of both iterations is
    shifted, including the two EQUALS."""
    _, consumed, _ = parse(_LET_DECLS_LL1, _let_decls_tokens())
    assert consumed == 6


def test_arbno_mid_body_terminal_captures_stay_parallel():
    tree, _, _ = parse(_LET_DECLS_LL1, _let_decls_tokens())
    children = dict(tree["children"])
    assert [t["lexeme"] for t in children["symbolList"]] == ["three", "four"]
    assert len(children["expList"]) == 2
    assert children["expList"][0]["kind"] == "tree"


def test_arbno_discarded_terminal_creates_no_child():
    tree, _, _ = parse(_LET_DECLS_LL1, _let_decls_tokens())
    assert [name for name, _ in tree["children"]] == ["symbolList", "expList"]


def test_arbno_missing_mid_body_terminal_is_a_parse_error():
    with pytest.raises(ParseError) as excinfo:
        parse(_LET_DECLS_LL1, [_tok("SYMBOL", "x"), _tok("NUM", "1")])
    assert "EQUALS" in str(excinfo.value)


def test_arbno_mid_body_terminal_zero_iterations_yields_empty_lists():
    tree, _, _ = parse(_LET_DECLS_LL1, [])
    assert dict(tree["children"]) == {"symbolList": [], "expList": []}


def test_arbno_all_noncapturing_body_repeats():
    tree, consumed, _ = parse(_BANGS_LL1, [_tok("BANG", "!"), _tok("BANG", "!")])
    assert consumed == 2
    assert tree["children"] == []
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
bin/test/units.bash src/plcc/parser/predictive_parser_test.py
```

Expected: **three of the six FAIL** —
`test_arbno_discarded_terminal_creates_no_child`,
`test_arbno_mid_body_terminal_zero_iterations_yields_empty_lists`, and
`test_arbno_all_noncapturing_body_repeats`. `_parse_arbno` currently builds
`list_fields` with a `None` key and appends the discarded token to it, so
each failure shows a stray `None`-named child (e.g.
`assert [..., None, ...] == ['symbolList', 'expList']`) rather than a
`KeyError`.

The other three (`..._is_consumed`, `..._captures_stay_parallel`,
`..._is_a_parse_error`) PASS already: Task 1 put `EQUALS` back in the body,
so it is shifted correctly — it just lands in a bogus list. They are kept as
guards on the shifting behavior, not as red tests. The pre-existing arbno
tests still pass.

- [ ] **Step 3: Write the minimal implementation**

In `src/plcc/parser/predictive_parser.py`, inside `_parse_arbno`, replace the
`list_fields` initialization and the `parse_iteration` loop body:

```python
        list_fields = {item["field"]: [] for item in rhs if item["field"] is not None}

        def parse_iteration():
            if tracer:
                tracer.push(sym)
            for item in rhs:
                if item["is_terminal"]:
                    tok = expect(item["symbol"])
                    builder.note_token(tok)
                    if item["field"] is not None:
                        list_fields[item["field"]].append(tok)
                else:
                    child_builder = parse_nt(item["symbol"])
                    builder.note_span_from(child_builder)
                    if item["field"] is not None:
                        list_fields[item["field"]].append(child_builder.to_node())
            if tracer:
                tracer.pop()
```

Leave everything else in `_parse_arbno` alone — the separator loop, the
`lookahead_set` checks, the trailing
`for field, values in list_fields.items()` append, and the `extensible`
check are all unchanged. Note that `expect` still raises on a missing
discarded terminal and still emits the tracer's shift event, and
`builder.note_token` still runs so the node's source span covers the
discarded token.

- [ ] **Step 4: Run the tests to verify they pass**

```bash
bin/test/units.bash src/plcc/parser/predictive_parser_test.py
```

Expected: PASS, including the pre-existing `_RANDS_LL1` / `_CMDS_LL1` tests
and the tracer tests.

- [ ] **Step 5: Run the whole unit tier**

```bash
bin/test/units.bash
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/plcc/parser/predictive_parser.py src/plcc/parser/predictive_parser_test.py
git commit -m "fix(parser): shift and discard non-capturing arbno body symbols

An arbno rhs item with field None is now consumed without being appended
to a list, the same way a regular production consumes an elided symbol.
Discarded tokens still count toward the node's source span.

Refs #174

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 3: Pin the arbno lookahead contract

**Files:**
- Test: `src/plcc/ll1/ll1_result_builder_test.py` (append at end of file)

**Interfaces:**
- Consumes: `build_ll1_result(grammar, productions, arbno_rules)` from `plcc.ll1.ll1_result_builder`, `Grammar` from `plcc.spec.syntax.validations.ll1.Grammar`, and `Rule` from `plcc.ll1.spec_json_decoder` — all three are already imported at the top of this test file.
- Produces: nothing. This task adds tests only; no source file changes.

**Why this task has no source change:** `build_ll1_result` derives an arbno's
runtime `lookahead` from `entry["rhs"][0]`, which was always correct code
reading incorrect data. Task 1 fixed the data. These tests hand-build the
arbno entry, so they pass the moment they are written — that is expected, not
a mistake. They exist to pin the contract that the lookahead comes from the
body's *first symbol whatever it is*, so a future change that re-introduces
capture-filtering upstream fails here too.

- [ ] **Step 1: Write the tests**

Append to `src/plcc/ll1/ll1_result_builder_test.py`, after the last test in the file:

```python
def _leading_terminal_arbno():
    """Mimics <items> **= BANG <Exp> with <Exp> ::= NUM, no separator.
    Grammar: items→BANG Exp items#|ε, items#→BANG Exp items#|ε, Exp→NUM."""
    g = Grammar()
    g.addRule("items", ["BANG", "Exp", "items#"])
    g.addRule("items", [])
    g.addRule("items#", ["BANG", "Exp", "items#"])
    g.addRule("items#", [])
    g.addRule("Exp", ["NUM"])
    fm = {
        ("items", ("BANG", "Exp", "items#")): Rule(alt=None, fields=[None, None, None]),
        ("items", ()): Rule(alt=None, fields=[]),
        ("items#", ("BANG", "Exp", "items#")): Rule(alt=None, fields=[None, None, None]),
        ("items#", ()): Rule(alt=None, fields=[]),
        ("Exp", ("NUM",)): Rule(alt=None, fields=[None]),
    }
    arbno = {
        "items": {
            "rhs": [
                {"field": None, "symbol": "BANG", "is_terminal": True},
                {"field": "expList", "symbol": "Exp", "is_terminal": False},
            ],
            "separator": None,
        }
    }
    return g, fm, arbno


def test_arbno_lookahead_uses_leading_noncapturing_terminal():
    """Issue #174: the lookahead comes from the body's first symbol, not
    its first capturing symbol. Predicting on FIRST(Exp) here would leave
    BANG unshiftable."""
    g, fm, arbno = _leading_terminal_arbno()
    result = build_ll1_result(g, fm, arbno)
    assert result["arbno"]["items"]["lookahead"] == ["BANG"]


def test_arbno_lookahead_nonempty_for_all_noncapturing_body():
    """<bangs> **= BANG captures nothing; an empty lookahead would make it
    match zero iterations against every input."""
    g = Grammar()
    g.addRule("bangs", ["BANG", "bangs#"])
    g.addRule("bangs", [])
    g.addRule("bangs#", ["BANG", "bangs#"])
    g.addRule("bangs#", [])
    fm = {
        ("bangs", ("BANG", "bangs#")): Rule(alt=None, fields=[None, None]),
        ("bangs", ()): Rule(alt=None, fields=[]),
        ("bangs#", ("BANG", "bangs#")): Rule(alt=None, fields=[None, None]),
        ("bangs#", ()): Rule(alt=None, fields=[]),
    }
    arbno = {
        "bangs": {
            "rhs": [{"field": None, "symbol": "BANG", "is_terminal": True}],
            "separator": None,
        }
    }
    result = build_ll1_result(g, fm, arbno)
    assert result["arbno"]["bangs"]["lookahead"] == ["BANG"]
```

- [ ] **Step 2: Run the tests**

```bash
bin/test/units.bash src/plcc/ll1/ll1_result_builder_test.py
```

Expected: PASS on the first run, for the reason stated above. If either test
FAILS, stop — that means `build_ll1_result` is not reading `rhs[0]` the way
this plan assumes, and the design needs revisiting before continuing.

- [ ] **Step 3: Commit**

```bash
git add src/plcc/ll1/ll1_result_builder_test.py
git commit -m "test(ll1): pin arbno lookahead to the body's first symbol

Refs #174

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 4: End-to-end regression through plcc-rep

**Files:**
- Create: `tests/fixtures/arbno-mid-body-terminal.plcc`
- Modify: `tests/bats/e2e/plcc-rep.bats` (append at end of file)

**Interfaces:**
- Consumes: the installed CLI entry points `plcc-spec`, `plcc-ll1`, `plcc-model`, `plcc-python-emit`, `plcc-rep`, and the bats `FIXTURES` / `WORK_DIR` variables set by that file's existing `setup()`.
- Produces: nothing other tasks depend on.

- [ ] **Step 1: Create the fixture grammar**

Create `tests/fixtures/arbno-mid-body-terminal.plcc` with exactly this content — it is the shape from issue #174 (`EQUALS` is a bare, non-capturing terminal between two captures, and there is no separator):

```text
token SYMBOL '[A-Za-z]\w*'
token EQUALS '='
token NUM '\d+'
skip  SPACE '\s+'
%
<Program> ::= <Decls:decls>
<Decls>   **= <SYMBOL> EQUALS <Exp>
<Exp>     ::= <NUM:num>
%
Python
Program
%%%
def _run(self):
    pairs = zip(self.decls.symbolList, self.decls.expList)
    return str([f"{s.lexeme}={e.eval()}" for s, e in pairs])
%%%
Exp
%%%
def eval(self):
    return int(self.num.lexeme)
%%%
```

The field names are derived, not chosen: a bare capturing terminal `<SYMBOL>`
yields `symbolList` (terminal names lowercase), and a bare capturing
nonterminal `<Exp>` yields `expList`.

- [ ] **Step 2: Write the bats tests**

Append to `tests/bats/e2e/plcc-rep.bats`, at the end of the file. This mirrors
the existing `setup_arbno_build` helper a few tests above it:

```bash
setup_mid_body_arbno_build() {
    MID_BODY_DIR="$(mktemp -d)"
    mkdir -p "${MID_BODY_DIR}/plcc-ng"
    plcc-spec "${FIXTURES}/arbno-mid-body-terminal.plcc" > "${MID_BODY_DIR}/plcc-ng/spec.json"
    plcc-ll1 < "${MID_BODY_DIR}/plcc-ng/spec.json" > "${MID_BODY_DIR}/plcc-ng/ll1.json"
    plcc-model "${MID_BODY_DIR}/plcc-ng/spec.json" | plcc-python-emit --output="${MID_BODY_DIR}/plcc-ng/Python"
    cd "${MID_BODY_DIR}"
}

@test "arbno-mid-body-terminal: plcc-rep evaluates two declarations" {
    setup_mid_body_arbno_build
    run --separate-stderr bash -c "echo 'x = 1 y = 2' | plcc-rep --spec='${FIXTURES}/arbno-mid-body-terminal.plcc'"
    [ "$status" -eq 0 ]
    [[ "${lines[-1]}" == "['x=1', 'y=2']" ]]
}

@test "arbno-mid-body-terminal: plcc-rep evaluates a single declaration" {
    setup_mid_body_arbno_build
    run --separate-stderr bash -c "echo 'x = 1' | plcc-rep --spec='${FIXTURES}/arbno-mid-body-terminal.plcc'"
    [ "$status" -eq 0 ]
    [[ "${lines[-1]}" == "['x=1']" ]]
}

@test "arbno-mid-body-terminal: plcc-rep evaluates empty input to []" {
    setup_mid_body_arbno_build
    run --separate-stderr bash -c "echo '' | plcc-rep --spec='${FIXTURES}/arbno-mid-body-terminal.plcc'"
    [ "$status" -eq 0 ]
    [[ "${lines[-1]}" == "[]" ]]
}
```

- [ ] **Step 3: Run the bats file to verify it passes with the fix**

```bash
PLCC_NO_TEST_CACHE=1 bin/test/e2e.bash tests/bats/e2e/plcc-rep.bats
```

Expected: PASS, all tests in the file. If the three new tests fail on output
mismatch rather than a parse error, check the fixture's `_run` against the
actual last line before changing any source code.

- [ ] **Step 4: Prove the new tests catch the bug**

Temporarily restore the pre-fix decoder, confirm the new tests go red, then
put it back. `5446141a` is this branch's commit before any source change (the
issue-filing commit):

```bash
git checkout 5446141a -- src/plcc/ll1/spec_json_decoder.py
PLCC_NO_TEST_CACHE=1 bin/test/e2e.bash tests/bats/e2e/plcc-rep.bats
```

Expected: the two non-empty-input `arbno-mid-body-terminal` tests FAIL, with
`unexpected 'EQUALS', no production for 'Exp'` visible in the output — the
exact symptom from the issue. The `trivial-arbno` and `arith` tests still
pass, confirming the fix was needed only for this shape.

The empty-input test still passes even pre-fix — zero repetitions never
reach the dropped terminal — so 2 of 3 red is the correct outcome.

Restore the fix before continuing, and confirm the tree is clean:

```bash
git checkout HEAD -- src/plcc/ll1/spec_json_decoder.py
git status --short
```

Expected: only the two new/modified test-tier files appear.

- [ ] **Step 5: Commit**

```bash
git add tests/fixtures/arbno-mid-body-terminal.plcc tests/bats/e2e/plcc-rep.bats
git commit -m "test(e2e): cover arbno with a mid-body non-capturing terminal

Refs #174

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 5: Document non-captured symbols in repetition bodies

**Files:**
- Modify: `docs/language-guide/syntactic.md:186-211` (the "Repetition rules" section, between the `<Args>`/`<Pairs>` example block and the "Captured symbols become parallel lists" paragraph)

**Interfaces:**
- Consumes: nothing. Documentation only.
- Produces: nothing.

This task is an addition to the approved design, which covered code and tests
only. The behavior it documents is the behavior Tasks 1–2 create; the section
currently shows only bodies in which every symbol is captured, which is what
made the broken shape look unsupported rather than buggy.

- [ ] **Step 1: Add the fixture-backed example**

In `docs/language-guide/syntactic.md`, in the "Repetition rules" section,
extend the example block so it reads:

```text
<Args>  **= <Expr:expr>
<Pairs> **= <WHOLE:x> <WHOLE:y> +COMMA
<Decls> **= <SYMBOL> EQUALS <Exp>
```

Then, immediately after the existing sentence "Captured symbols become
parallel lists:", add this paragraph before the `class Args { ... }` code
block:

```markdown
A symbol in the body that is not captured — `EQUALS` in `<Decls>` above — is
still matched on every repetition, but produces no list. `Decls` gets
`symbolList` and `expList` only.
```

Headings in `docs/` use sentence case; this change adds no headings, so
nothing else in the file needs adjusting.

- [ ] **Step 2: Skip the docs build**

`bin/docs/` contains only `serve.bash` (a local mkdocs server); there is no
build-and-check script to run, and this change adds no headings, links, or
new files. Read the edited section once to confirm the Markdown renders as
intended, and move on.

- [ ] **Step 3: Commit**

```bash
git add docs/language-guide/syntactic.md
git commit -m "docs(language-guide): note non-captured symbols in repetition bodies

Refs #174

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 6: Full verification and issue close

**Files:**
- Modify: `dev-docs/issues/174-arbno-drops-mid-body-terminal.md` (moved to `dev-docs/issues/done/` by the script)
- Modify: `dev-docs/roadmap.md` (edited by the script)

**Interfaces:**
- Consumes: `bin/test/functional.bash`, `bin/issues/close.bash`, `bin/issues/check.bash`.
- Produces: the branch's final commit.

- [ ] **Step 1: Run every functional tier**

```bash
PLCC_NO_TEST_CACHE=1 bin/test/functional.bash
```

Expected: PASS across units, commands, integration, and e2e. Do not proceed
to the close while anything is red — report the failure instead.

- [ ] **Step 2: Close the issue**

```bash
bin/issues/close.bash 174
```

This moves the issue file to `dev-docs/issues/done/`, removes its Open Issues
entry from `dev-docs/roadmap.md` (and the `### fix` heading if it is now
empty), rewrites `dev-docs/` links that pointed at the old path, and stages
everything. It runs `bin/issues/check.bash` itself.

- [ ] **Step 3: Review the staged bookkeeping**

```bash
git diff --cached
```

Confirm the design doc's and plan's links to the issue were rewritten to
`issues/done/174-arbno-drops-mid-body-terminal.md`, and read the roadmap diff
— milestone rationale prose is not auto-edited and may need a manual touch.

- [ ] **Step 4: Commit**

```bash
git commit -m "docs(issues): close issue 174 (arbno drops mid-body terminal), update roadmap

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

- [ ] **Step 5: Report**

State plainly which tiers were run and their results, and that issue #174 is
closed on branch `arbno-mid-body-terminal`. Do not claim the fix is verified
beyond the tiers actually run.
