# Remove %%{ / %%} Block Delimiter Syntax Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the `%%{` / `%%}` asymmetric block delimiter syntax from the spec parser so that only `%%%` is recognised as a block delimiter; `%%{` and `%%}` become ordinary pass-through lines.

**Architecture:** All changes are confined to `parse_blocks.py` and its co-located test file. Remove the two compiled regex patterns (`PPLC`, `PPRC`) and their entry in the `brackets` dispatch dict. Update the test file: add two new pass-through tests first (TDD), then remove the three tests that relied on the old syntax.

**Tech Stack:** Python, pytest. Run tests with `bin/test/units.bash` (wraps `pdm test`; accepts pytest args).

---

## Files

- Modify: `src/plcc/spec/rough/parse_blocks.py` — remove `PPLC`, `PPRC`, and the `PPLC: PPRC` dict entry
- Modify: `src/plcc/spec/rough/parse_blocks_test.py` — add two pass-through tests; remove three obsolete tests

---

### Task 1: Write failing tests for `%%{` and `%%}` pass-through

**Files:**
- Modify: `src/plcc/spec/rough/parse_blocks_test.py`

- [ ] **Step 1: Add two failing tests after the existing `test_triple_percent_with_trailing_space_is_block_delimiter` test (line 51)**

  Append these two tests to `src/plcc/spec/rough/parse_blocks_test.py`:

  ```python
  def test_pplc_is_a_plain_line():
      lines_ = list(lines.parseLines('%%{'))
      assert list(parse_blocks(lines_)) == lines_


  def test_pprc_is_a_plain_line():
      lines_ = list(lines.parseLines('%%}'))
      assert list(parse_blocks(lines_)) == lines_
  ```

- [ ] **Step 2: Run the new tests and confirm the expected results**

  ```bash
  bin/test/units.bash src/plcc/spec/rough/parse_blocks_test.py::test_pplc_is_a_plain_line src/plcc/spec/rough/parse_blocks_test.py::test_pprc_is_a_plain_line -v
  ```

  Expected:
  - `test_pplc_is_a_plain_line` **FAILS** — `%%{` is currently recognised as a block opener, so `parse_blocks` raises `UnclosedBlockError` instead of yielding the line.
  - `test_pprc_is_a_plain_line` **PASSES** — `%%}` is only meaningful as a *closer*; it is never an opener, so it already passes through as a plain line before any code changes.

  The red step here is `test_pplc_is_a_plain_line` only. Confirm that result before continuing.

---

### Task 2: Remove `PPLC` / `PPRC` from `parse_blocks.py`

**Files:**
- Modify: `src/plcc/spec/rough/parse_blocks.py`

- [ ] **Step 1: Remove the three lines that define and use `PPLC` and `PPRC`**

  Current state of `parse_blocks` (lines 9–19):

  ```python
  def parse_blocks(lines, handler=raise_handler):
      if lines is None:
          return []
      PPP = re.compile(r'^%%%\s*(#.*)?$')
      PPLC = re.compile(r'^%%{(?:\s*#.*)?$')
      PPRC = re.compile(r'^%%}(?:\s*#.*)?$')
      brackets = {
          PPP: PPP,
          PPLC: PPRC
      }
      return BlockParser(brackets, handler).parse(lines)
  ```

  Replace with:

  ```python
  def parse_blocks(lines, handler=raise_handler):
      if lines is None:
          return []
      PPP = re.compile(r'^%%%\s*(#.*)?$')
      brackets = {
          PPP: PPP,
      }
      return BlockParser(brackets, handler).parse(lines)
  ```

- [ ] **Step 2: Run the two new tests and confirm they now pass**

  ```bash
  bin/test/units.bash src/plcc/spec/rough/parse_blocks_test.py::test_pplc_is_a_plain_line src/plcc/spec/rough/parse_blocks_test.py::test_pprc_is_a_plain_line -v
  ```

  Expected: both PASS.

- [ ] **Step 3: Run the full unit suite and note which tests fail**

  ```bash
  bin/test/units.bash src/plcc/spec/rough/parse_blocks_test.py -v
  ```

  Expected: `test_curly_percent_block`, `test_nested_blocks_produce_single_block`, and `test_mixed` now fail (they assert the old behaviour). All other tests pass. If anything unexpected fails, investigate before continuing.

---

### Task 3: Remove obsolete tests

**Files:**
- Modify: `src/plcc/spec/rough/parse_blocks_test.py`

- [ ] **Step 1: Delete the three tests that asserted the old `%%{`/`%%}` block behaviour**

  Remove these three functions entirely:

  - `test_curly_percent_block` (asserts `%%{`…`%%}` forms a block)
  - `test_nested_blocks_produce_single_block` (asserts `%%{`…`%%}` containing `%%%`…`%%%` forms a single block)
  - `test_mixed` (asserts a mix of `%%%` and `%%{`/`%%}` blocks in one stream)

  After removal the test file should contain exactly these test functions, in order:

  1. `test_None_yields_nothing`
  2. `test_empty_yields_nothing`
  3. `test_non_block_lines_are_passed_through`
  4. `test_unclosed_block_is_an_error`
  5. `test_handler`
  6. `test_triple_percent_block`
  7. `test_triple_percent_with_trailing_space_is_block_delimiter`
  8. `test_pplc_is_a_plain_line`
  9. `test_pprc_is_a_plain_line`

- [ ] **Step 2: Run the full unit suite and confirm all tests pass**

  ```bash
  bin/test/units.bash src/plcc/spec/rough/parse_blocks_test.py -v
  ```

  Expected: all 9 tests PASS, no failures or errors.

- [ ] **Step 3: Run the broader unit suite to check for regressions**

  ```bash
  bin/test/units.bash -v
  ```

  Expected: all tests pass.

- [ ] **Step 4: Commit**

  ```bash
  git add src/plcc/spec/rough/parse_blocks.py src/plcc/spec/rough/parse_blocks_test.py
  git commit -m "refactor(rough): remove %%{ / %%} block delimiter syntax (issue 051)"
  ```
