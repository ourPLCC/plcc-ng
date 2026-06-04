# Scanner First-Longest-Match Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the scanner's skip-priority algorithm with a single first-longest-match algorithm where skips and tokens compete together.

**Architecture:** Remove the skip-priority short-circuit in `Matcher.match()` and the `_removeSkips` helper. The existing `_getLongestMatch` already implements first-longest-match with declaration-order tiebreaking — skips just weren't being passed to it. Update four tests that encoded the old behavior to document the new semantics.

**Tech Stack:** Python, pytest (`bin/test/units.bash`)

---

## Task 1: Rewrite the four tests that encode old skip-priority behavior

**Files:**

- Modify: `src/plcc/scan/matcher_test.py`

These tests currently pass under the old algorithm. After this task they will fail — that is the goal. The production code is not touched yet.

- [ ] **Step 1: Replace `test_skip_wins_if_it_matches_before_any_token_rules`**

Find and replace that entire test function with:

```python
def test_longer_token_beats_shorter_skip_regardless_of_declaration_order():
    matcher = makeMatcher(r'''
        skip ONE '1'
        token NUMBER '\d+'
    ''')
    line = parseLine("123")
    result = matcher.match(line, index=0)
    assert result == Token(lexeme='123', name='NUMBER', line=line, column=1)
```

- [ ] **Step 2: Replace `test_once_a_token_matches_subsequent_skip_are_ignored`**

Find and replace that entire test function with:

```python
def test_skip_and_token_tie_on_length_declaration_order_decides():
    # ONETWOTHREE (skip) and NUMBER (token) both match '123'.
    # ONETWOTHREE is declared first, so it wins.
    matcher = makeMatcher(r'''
        token ONETWO '12'
        skip ONETWOTHREE '123'
        token NUMBER '\d+'
    ''')
    line = parseLine("123")
    result = matcher.match(line, index=0)
    assert result == Skip(lexeme='123', name='ONETWOTHREE', line=line, column=1)
```

- [ ] **Step 3: Update `test_match_mid_string`**

Find and replace that entire test function with:

```python
def test_match_mid_string():
    matcher = makeMatcher(r'''
        skip ONE '1'
        token NUMBER '\d+'
    ''')
    line = parseLine("hi 123")
    result = matcher.match(line, index=3)
    assert result == Token(lexeme='123', name='NUMBER', line=line, column=4)
    result = matcher.match(line, index=4)
    assert result == Token(lexeme='23', name='NUMBER', line=line, column=5)
```

- [ ] **Step 4: Update `test_record_attempts_skip_win_includes_token_candidates`**

The assertions are unchanged — skip still wins because it is declared first and the match length is equal. Only the comment explaining *why* changes.

Find and replace the comment block at the top of that test (the three lines starting with `# skip appears before token...`) with:

```python
    # WS and NUM both match '42' with the same length.
    # WS is declared first, so it wins by declaration order — not by skip priority.
```

- [ ] **Step 5: Run the four updated tests and confirm they all fail**

```bash
bin/test/units.bash src/plcc/scan/matcher_test.py -v -k "longer_token_beats or tie_on_length or mid_string or skip_win_includes"
```

Expected: 3 failures, 1 pass. The first three fail with assertion errors (wrong result type or lexeme). The fourth passes because its behavior is unchanged under the old code (both skip and token match the same span, skip declared first → skip wins either way) — if it fails here, something else is wrong.

---

## Task 2: Update the production code

**Files:**

- Modify: `src/plcc/scan/matcher.py`

- [ ] **Step 1: Replace the `match` method body**

Find and replace the entire `match` method with:

```python
def match(self, line, index):
    matches = self._getMatches(line, index)
    if not matches:
        return LexError(line=line, column=index+1)

    result = self._getLongestMatch(matches)

    if self._record_attempts:
        result.attempts = [
            {
                'name': m.name,
                'regex': m.pattern,
                'lexeme': m.lexeme,
                'char_count': len(m.lexeme),
                'is_skip': isinstance(m, Skip),
                'winner': m is result,
            }
            for m in matches
        ]

    return result
```

- [ ] **Step 2: Delete the `_removeSkips` method**

Remove this method entirely:

```python
def _removeSkips(self, matches):
    return [m for m in matches if isinstance(m, Token)]
```

- [ ] **Step 3: Run all matcher tests and confirm they all pass**

```bash
bin/test/units.bash src/plcc/scan/matcher_test.py -v
```

Expected: all tests pass, 0 failures.

- [ ] **Step 4: Run the full unit suite to check for regressions**

```bash
bin/test/units.bash
```

Expected: 915+ tests pass, 0 failures.

- [ ] **Step 5: Commit**

```bash
git add src/plcc/scan/matcher.py src/plcc/scan/matcher_test.py
git commit -m "feat(scan): replace skip-priority algorithm with first-longest-match"
```
