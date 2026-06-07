# SourceRunner Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract shared source-routing, TTY detection, hint/prompt, and interactive accumulation logic into a `SourceRunner` class used by `plcc-scan`, `plcc-parse`, and `plcc-rep`.

**Architecture:** A `SourceHandler` protocol (one method: `feed(bytes, str) -> bool`) lets each command plug its pipeline into a shared interactive loop. `SourceRunner` owns source routing, hint/prompt display, accumulation, `^C`/`^D` semantics. `plcc-tokens` gains `--source-name` so file content can be piped while preserving filename metadata. `plcc-parser-table` gains stdout error emission so handlers can distinguish "done (error)" from "incomplete (need more input)" by checking stdout rather than exit code.

**Tech Stack:** Python 3, pytest, bats, docopt-ng. All work happens in `.worktrees/source-runner`. Run tests with `bin/test/units.bash` (pytest) and `bin/test/commands.bash` (bats).

---

## Files

| Action | Path | Purpose |
|--------|------|---------|
| Modify | `src/plcc/tokens/tokens_cli.py` | Add `--source-name` flag |
| Modify | `src/plcc/tokens/tokens_cli_test.py` | Tests for `--source-name` |
| Modify | `src/plcc/parser/predictive_parser.py` | Add `IncompleteInputError` |
| Modify | `src/plcc/parser/predictive_parser_test.py` | Tests for `IncompleteInputError` |
| Modify | `src/plcc/parser/table_cli.py` | Emit parse errors to stdout; swallow incomplete silently |
| Modify | `src/plcc/parser/table_cli_test.py` | Tests for new stdout/incomplete behavior |
| Create | `src/plcc/cmd/source_runner.py` | `SourceRunner` + `SourceHandler` protocol |
| Create | `src/plcc/cmd/source_runner_test.py` | Unit tests for `SourceRunner` |
| Modify | `src/plcc/cmd/scan.py` | Add `ScanHandler`; replace IO loop with `SourceRunner` |
| Modify | `src/plcc/cmd/scan_test.py` | Replace TTY-hint tests with `ScanHandler` tests |
| Modify | `src/plcc/cmd/parse.py` | Add `ParseHandler`; replace IO loop with `SourceRunner` |
| Create | `src/plcc/cmd/parse_test.py` | Unit tests for `ParseHandler` |
| Modify | `src/plcc/cmd/rep.py` | Add `RepHandler`; replace IO loop with `SourceRunner` |
| Create | `src/plcc/cmd/rep_test.py` | Unit tests for `RepHandler` |

---

## Task 1: Add `--source-name` to `plcc-tokens`

**Files:**
- Modify: `src/plcc/tokens/tokens_cli.py`
- Modify: `src/plcc/tokens/tokens_cli_test.py`

- [ ] **Step 1: Write the failing test**

  Open `src/plcc/tokens/tokens_cli_test.py`. Look at existing `_run` helpers and fixtures to understand the test style (the file already has tests; add these at the bottom).

  ```python
  def test_source_name_overrides_stdin_label(tmp_path, monkeypatch, capsys):
      """--source-name=myfile.txt labels stdin tokens as 'myfile.txt' instead of '-'."""
      import json
      from plcc.tokens.tokens_cli import main as run_main
      spec = _make_spec(tmp_path)   # use whatever spec-building helper already exists in the file
      tokens_out = []
      original_main = run_main

      monkeypatch.setattr("sys.stdin", io.StringIO("hello\n"))
      try:
          run_main([str(spec), "--source-name=myfile.txt", "-"])
      except SystemExit:
          pass
      out, _ = capsys.readouterr()
      for line in out.strip().splitlines():
          tokens_out.append(json.loads(line))
      files = {t["source"]["file"] for t in tokens_out}
      assert files == {"myfile.txt"}
  ```

  **Note:** Look at the existing test helpers at the top of `tokens_cli_test.py` before writing this. The file has a `_make_spec` or similar helper. Match the style exactly.

- [ ] **Step 2: Run to confirm failure**

  ```bash
  bin/test/units.bash src/plcc/tokens/tokens_cli_test.py -v -k source_name
  ```

  Expected: FAIL (unknown option `--source-name`).

- [ ] **Step 3: Implement**

  In `src/plcc/tokens/tokens_cli.py`, add the option to the docstring:

  ```python
  __doc__ = """plcc-tokens
      Tokenize source files given a spec JSON file, output token JSONL.

  Usage:
      plcc-tokens [-v ...] [options] SPEC_JSON [SOURCE ...]

  Arguments:
      SPEC_JSON   Path to spec JSON file (output of plcc-spec).
      SOURCE      Source files to tokenize. Use '-' for stdin. Defaults to stdin.

  Options:
      -h --help                   Show this message.
      -t --trace                  Include regex, source_line, attempts; emit skip records.
      --source-name=<label>       Override the source label for stdin [default: -].
  """ + VERBOSE_OPTIONS
  ```

  Pass it through in `main()`:

  ```python
  def main(argv=None):
      if argv is None:
          argv = sys.argv[1:]
      args = docopt(__doc__, argv)
      verbose = VerboseContext.from_args("plcc-tokens", Events, args)
      trace = args['--trace']
      rules = load_lexical_rules(args['SPEC_JSON'])
      matcher = Matcher(rules, record_attempts=trace)
      scanner = Scanner(matcher)
      sources = args['SOURCE'] or ['-']
      source_name = args['--source-name']
      verbose.emit(Events.STARTED, message="tokenizing")
      lines = _lines_from_sources(sources, verbose, source_name=source_name)
      for obj in scanner.scan(lines):
          if isinstance(obj, Skip):
              if trace:
                  print(format_record(obj, show_all=True), flush=True)
              continue
          if isinstance(obj, LexError):
              print(format_error_record(obj), flush=True)
              continue
          print(format_record(obj, show_all=trace), flush=True)
      verbose.emit(Events.FINISHED, message="done")
  ```

  Update `_lines_from_sources` to accept and apply `source_name`:

  ```python
  def _lines_from_sources(sources, verbose, source_name=None):
      for file in sources:
          verbose.emit(Events.SCANNING_FILE, level=1, message=f"scanning {file}")
          if file == '-':
              label = source_name if source_name else '-'
              yield from _lines_from_stream(sys.stdin, label)
          else:
              with open(file, 'r') as f:
                  yield from _lines_from_stream(f, file)
  ```

- [ ] **Step 4: Run to confirm pass**

  ```bash
  bin/test/units.bash src/plcc/tokens/tokens_cli_test.py -v -k source_name
  ```

  Expected: PASS.

- [ ] **Step 5: Run full unit suite**

  ```bash
  bin/test/units.bash
  ```

  Expected: all pass.

- [ ] **Step 6: Commit**

  ```bash
  git -C .worktrees/source-runner add src/plcc/tokens/tokens_cli.py src/plcc/tokens/tokens_cli_test.py
  git -C .worktrees/source-runner commit -m "feat(tokens): add --source-name flag to override stdin label"
  ```

---

## Task 2: Add `IncompleteInputError` to `predictive_parser`

**Files:**
- Modify: `src/plcc/parser/predictive_parser.py`
- Modify: `src/plcc/parser/predictive_parser_test.py`

The parser currently raises `ParseError` for all failures. We need to distinguish "ran out of tokens mid-parse" (lookahead is `$`) from "wrong token" so callers can treat them differently.

- [ ] **Step 1: Write the failing tests**

  Open `src/plcc/parser/predictive_parser_test.py`. It imports `parse, ParseError` at the top and has `_TRIVIAL_LL1`. Add at the bottom:

  ```python
  from plcc.parser.predictive_parser import IncompleteInputError

  def _tok(name, lexeme="x"):
      return {"kind": "token", "name": name, "lexeme": lexeme,
              "source": {"file": "-", "line": 1, "column": 1}}

  def test_incomplete_raises_IncompleteInputError_when_table_misses_sentinel():
      # Grammar: program → NUM PLUS NUM
      # Tokens: [NUM] — parser needs PLUS next, gets $ instead
      ll1 = {
          "is_ll1": True,
          "start_symbol": "program",
          "parse_table": {
              "program": {
                  "NUM": [
                      {"symbol": "NUM", "field": None},
                      {"symbol": "PLUS", "field": None},
                      {"symbol": "NUM", "field": None},
                  ]
              }
          },
      }
      with pytest.raises(IncompleteInputError):
          parse(ll1, [_tok("NUM")])

  def test_bad_token_raises_ParseError_not_IncompleteInputError():
      # Grammar: program → NUM
      # Tokens: [PLUS] — wrong token, not EOF
      ll1 = {
          "is_ll1": True,
          "start_symbol": "program",
          "parse_table": {
              "program": {
                  "NUM": [{"symbol": "NUM", "field": None}]
              }
          },
      }
      with pytest.raises(ParseError) as exc_info:
          parse(ll1, [_tok("PLUS")])
      assert not isinstance(exc_info.value, IncompleteInputError)
  ```

- [ ] **Step 2: Run to confirm failure**

  ```bash
  bin/test/units.bash src/plcc/parser/predictive_parser_test.py -v -k incomplete
  ```

  Expected: FAIL (`cannot import name 'IncompleteInputError'`).

- [ ] **Step 3: Implement**

  At the top of `src/plcc/parser/predictive_parser.py`, add the subclass right after `ParseError`:

  ```python
  class ParseError(Exception):
      pass


  class IncompleteInputError(ParseError):
      """Raised when the token stream ends before the parse is complete."""
      pass
  ```

  In `_parse_regular`, change the production-not-found branch to check for `$`:

  ```python
  production = nt_table.get(lookahead)
  if production is None:
      if lookahead == "$":
          raise IncompleteInputError(
              f"unexpected end of input while parsing {sym!r}"
          )
      raise ParseError(
          f"unexpected {lookahead!r}, no production for {sym!r} "
          f"at {current()['source']}"
      )
  ```

  In `expect`, change the mismatch branch to check for `$`:

  ```python
  def expect(sym):
      tok = current()
      if tok["name"] != sym:
          if tok["name"] == "$":
              raise IncompleteInputError(
                  f"unexpected end of input: expected {sym!r}"
              )
          raise ParseError(
              f"expected {sym!r}, got {tok['name']!r} "
              f"at {tok['source']}"
          )
      return advance()
  ```

- [ ] **Step 4: Run to confirm pass**

  ```bash
  bin/test/units.bash src/plcc/parser/predictive_parser_test.py -v
  ```

  Expected: all pass.

- [ ] **Step 5: Commit**

  ```bash
  git -C .worktrees/source-runner add src/plcc/parser/predictive_parser.py src/plcc/parser/predictive_parser_test.py
  git -C .worktrees/source-runner commit -m "feat(parser): add IncompleteInputError for EOF-mid-parse detection"
  ```

---

## Task 3: Update `plcc-parser-table` to emit parse errors to stdout

**Files:**
- Modify: `src/plcc/parser/table_cli.py`
- Modify: `src/plcc/parser/table_cli_test.py`

Handlers (ParseHandler, RepHandler) check stdout to decide True/False. Currently all parse errors go only to stderr. After this task:
- Actual parse errors → `{"kind": "error", "message": "..."}` on stdout AND stderr; exit 1
- Incomplete input (`IncompleteInputError`) → nothing on stdout; exit 1

- [ ] **Step 1: Write the failing tests**

  Open `src/plcc/parser/table_cli_test.py`. Look at the existing `_run` helper to understand the pattern. Add these tests:

  ```python
  from plcc.parser.table_cli import main as run_main

  # grammar: program → NUM PLUS NUM
  _ADDITION_LL1 = {
      "is_ll1": True,
      "start_symbol": "program",
      "parse_table": {
          "program": {
              "NUM": [
                  {"symbol": "NUM", "field": None},
                  {"symbol": "PLUS", "field": None},
                  {"symbol": "NUM", "field": None},
              ]
          }
      },
  }

  def test_parse_error_emits_error_record_to_stdout(tmp_path, capsys):
      """A real parse error (wrong token) emits {"kind":"error"} to stdout."""
      ll1_file = tmp_path / "ll1.json"
      ll1_file.write_text(json.dumps(_TRIVIAL_LL1))
      # PLUS is not valid for program → NUM
      bad_tokens = [_tok("PLUS", "+")]
      stdin_data = "\n".join(json.dumps(t) for t in bad_tokens) + "\n"
      with pytest.raises(SystemExit):
          monkeypatch_stdin(stdin_data)   # see note below
          run_main([f"--ll1={ll1_file}"])
      out, _ = capsys.readouterr()
      records = [json.loads(l) for l in out.strip().splitlines() if l.strip()]
      assert any(r.get("kind") == "error" for r in records)

  def test_incomplete_input_produces_no_stdout(tmp_path, capsys):
      """Incomplete input (EOF too soon) produces no stdout output."""
      ll1_file = tmp_path / "ll1.json"
      ll1_file.write_text(json.dumps(_ADDITION_LL1))
      # Only NUM, missing PLUS NUM
      partial_tokens = [_tok("NUM", "1")]
      stdin_data = "\n".join(json.dumps(t) for t in partial_tokens) + "\n"
      with pytest.raises(SystemExit):
          monkeypatch_stdin(stdin_data)
          run_main([f"--ll1={ll1_file}"])
      out, _ = capsys.readouterr()
      assert out.strip() == ""
  ```

  **Note:** Look at how existing tests in `table_cli_test.py` feed stdin (they use `monkeypatch` or `io.StringIO` — match that pattern exactly rather than the pseudocode above).

- [ ] **Step 2: Run to confirm failure**

  ```bash
  bin/test/units.bash src/plcc/parser/table_cli_test.py -v -k "error_record_to_stdout or no_stdout"
  ```

  Expected: FAIL (parse error goes to stderr only; incomplete input also goes to stderr).

- [ ] **Step 3: Implement**

  In `src/plcc/parser/table_cli.py`, add the import for `IncompleteInputError` and split the exception handling:

  ```python
  from .predictive_parser import parse, ParseError, IncompleteInputError
  ```

  Replace the single `except ParseError` block:

  ```python
  # Parse
  try:
      tree = parse(ll1, tokens)
  except IncompleteInputError:
      # Input ended before parse was complete. Emit nothing to stdout so
      # callers can detect "need more input" by checking for empty stdout.
      verbose.emit_error({}, "incomplete input")
      sys.exit(1)
  except ParseError as e:
      verbose.emit_error({}, str(e))
      print(json.dumps({"kind": "error", "message": str(e)}), flush=True)
      sys.exit(1)
  ```

- [ ] **Step 4: Run to confirm pass**

  ```bash
  bin/test/units.bash src/plcc/parser/table_cli_test.py -v
  ```

  Expected: all pass.

- [ ] **Step 5: Run full unit suite**

  ```bash
  bin/test/units.bash
  ```

  Expected: all pass.

- [ ] **Step 6: Commit**

  ```bash
  git -C .worktrees/source-runner add src/plcc/parser/table_cli.py src/plcc/parser/table_cli_test.py
  git -C .worktrees/source-runner commit -m "feat(parser-table): emit error record to stdout on parse error; silent on incomplete"
  ```

---

## Task 4: Create `SourceRunner`

**Files:**
- Create: `src/plcc/cmd/source_runner.py`
- Create: `src/plcc/cmd/source_runner_test.py`

- [ ] **Step 1: Write the failing tests**

  Create `src/plcc/cmd/source_runner_test.py`:

  ```python
  import io
  import sys
  from types import SimpleNamespace

  import pytest

  from .source_runner import SourceRunner

  HINT = "Enter input. Press ^D (EOF) when done."


  class RecordingHandler:
      """Captures feed() calls for assertions."""
      def __init__(self, results=None):
          # results: iterator of booleans to return from feed(); defaults to all True
          self._results = iter(results or [])
          self.calls = []  # list of (content, source)

      def feed(self, content, source):
          self.calls.append((content, source))
          try:
              return next(self._results)
          except StopIteration:
              return True


  @pytest.fixture()
  def runner():
      return SourceRunner()


  # --- File source ---

  def test_file_source_reads_content_and_passes_filename(tmp_path, runner):
      f = tmp_path / "hello.txt"
      f.write_bytes(b"hello")
      handler = RecordingHandler()
      runner.run([str(f)], handler)
      assert handler.calls == [(b"hello", str(f))]


  def test_no_sources_treated_as_stdin(monkeypatch, runner):
      monkeypatch.setattr(sys, "stdin", SimpleNamespace(
          isatty=lambda: False,
          buffer=io.BytesIO(b"data"),
      ))
      handler = RecordingHandler()
      runner.run([], handler)
      assert handler.calls == [(b"data", "-")]


  # --- Non-TTY stdin ---

  def test_non_tty_stdin_reads_all_and_passes_dash(monkeypatch, runner):
      monkeypatch.setattr(sys, "stdin", SimpleNamespace(
          isatty=lambda: False,
          buffer=io.BytesIO(b"content"),
      ))
      handler = RecordingHandler()
      runner.run(["-"], handler)
      assert handler.calls == [(b"content", "-")]


  # --- Interactive (TTY) stdin ---

  def _tty_stdin(lines):
      """Fake TTY stdin yielding lines from a list; empty bytes signals EOF."""
      buf = io.BytesIO(b"".join(l if isinstance(l, bytes) else l.encode() for l in lines))
      return SimpleNamespace(isatty=lambda: True, buffer=buf)


  def test_interactive_prints_hint(monkeypatch, runner, capsys):
      monkeypatch.setattr(sys, "stdin", _tty_stdin([b"hello\n", b""]))
      runner.run(["-"], RecordingHandler())
      _, err = capsys.readouterr()
      assert HINT in err


  def test_interactive_prints_prompt(monkeypatch, runner, capsys):
      monkeypatch.setattr(sys, "stdin", _tty_stdin([b"hello\n", b""]))
      runner.run(["-"], RecordingHandler())
      _, err = capsys.readouterr()
      assert ">>> " in err


  def test_interactive_true_result_resets_to_prompt(monkeypatch, runner, capsys):
      # feed returns True on first call → prompt resets to >>>
      monkeypatch.setattr(sys, "stdin", _tty_stdin([b"line1\n", b"line2\n", b""]))
      handler = RecordingHandler(results=[True, True])
      runner.run(["-"], handler)
      _, err = capsys.readouterr()
      assert err.count(">>> ") >= 2


  def test_interactive_false_result_shows_continuation(monkeypatch, runner, capsys):
      # feed returns False on first line → continuation prompt
      monkeypatch.setattr(sys, "stdin", _tty_stdin([b"line1\n", b"line2\n", b""]))
      handler = RecordingHandler(results=[False, True])
      runner.run(["-"], handler)
      _, err = capsys.readouterr()
      assert "... " in err


  def test_interactive_accumulates_on_false(monkeypatch, runner):
      monkeypatch.setattr(sys, "stdin", _tty_stdin([b"a\n", b"b\n", b""]))
      handler = RecordingHandler(results=[False, True])
      runner.run(["-"], handler)
      # Second call should have accumulated content
      assert handler.calls[1][0] == b"a\nb\n"


  def test_interactive_empty_line_on_fresh_prompt_does_not_call_feed(monkeypatch, runner):
      monkeypatch.setattr(sys, "stdin", _tty_stdin([b"\n", b"hello\n", b""]))
      handler = RecordingHandler()
      runner.run(["-"], handler)
      # Empty line with empty buffer: skipped. Only "hello\n" triggers feed.
      assert len(handler.calls) == 1
      assert handler.calls[0][0] == b"hello\n"


  def test_interactive_eof_with_buffer_calls_feed(monkeypatch, runner):
      monkeypatch.setattr(sys, "stdin", _tty_stdin([b"partial\n", b""]))
      handler = RecordingHandler(results=[False])  # first call: no result yet
      runner.run(["-"], handler)
      # EOF with non-empty buffer: feed called with buffer
      assert any(b"partial" in c for c, _ in handler.calls)


  def test_interactive_eof_with_empty_buffer_does_not_call_feed(monkeypatch, runner):
      monkeypatch.setattr(sys, "stdin", _tty_stdin([b""]))  # immediate EOF
      handler = RecordingHandler()
      runner.run(["-"], handler)
      assert handler.calls == []


  def test_ctrl_c_clears_buffer_and_continues(monkeypatch, runner, capsys):
      call_count = 0
      original_readline = None

      class InterruptOnce:
          def __init__(self):
              self._buf = io.BytesIO(b"line2\n")
              self._raised = False

          isatty = lambda self: True

          @property
          def buffer(self):
              return self

          def readline(self):
              if not self._raised:
                  self._raised = True
                  raise KeyboardInterrupt
              return self._buf.read(100) or b""

      monkeypatch.setattr(sys, "stdin", InterruptOnce())
      handler = RecordingHandler()
      runner.run(["-"], handler)
      _, err = capsys.readouterr()
      # After ^C, prompt resets to >>>
      assert ">>> " in err
  ```

- [ ] **Step 2: Run to confirm failure**

  ```bash
  bin/test/units.bash src/plcc/cmd/source_runner_test.py -v
  ```

  Expected: all FAIL (module does not exist yet).

- [ ] **Step 3: Implement**

  Create `src/plcc/cmd/source_runner.py`:

  ```python
  import sys

  HINT = "Enter input. Press ^D (EOF) when done."
  PROMPT = ">>> "
  CONTINUATION = "... "


  class SourceRunner:
      def __init__(self, hint=HINT, prompt=PROMPT, continuation=CONTINUATION):
          self._hint = hint
          self._prompt = prompt
          self._continuation = continuation

      def run(self, sources, handler):
          effective = sources if sources else ["-"]
          for source in effective:
              if source == "-":
                  if sys.stdin.isatty():
                      self._run_interactive(handler)
                  else:
                      content = sys.stdin.buffer.read()
                      handler.feed(content, "-")
              else:
                  with open(source, "rb") as f:
                      content = f.read()
                  handler.feed(content, source)

      def _run_interactive(self, handler):
          print(self._hint, file=sys.stderr)
          buffer = b""
          prompt = self._prompt
          while True:
              try:
                  print(prompt, end="", flush=True, file=sys.stderr)
                  line = sys.stdin.buffer.readline()
                  if not line:  # EOF (^D)
                      if buffer:
                          handler.feed(buffer, "-")
                      break
                  if not line.strip() and not buffer:
                      # Empty line on a fresh prompt: skip silently
                      continue
                  buffer += line
                  result = handler.feed(buffer, "-")
                  if result:
                      buffer = b""
                      prompt = self._prompt
                  else:
                      prompt = self._continuation
              except KeyboardInterrupt:
                  print(file=sys.stderr)
                  buffer = b""
                  prompt = self._prompt
  ```

- [ ] **Step 4: Run to confirm pass**

  ```bash
  bin/test/units.bash src/plcc/cmd/source_runner_test.py -v
  ```

  Expected: all pass.

- [ ] **Step 5: Run full unit suite**

  ```bash
  bin/test/units.bash
  ```

  Expected: all pass.

- [ ] **Step 6: Commit**

  ```bash
  git -C .worktrees/source-runner add src/plcc/cmd/source_runner.py src/plcc/cmd/source_runner_test.py
  git -C .worktrees/source-runner commit -m "feat(cmd): add SourceRunner with source routing and interactive loop"
  ```

---

## Task 5: Add `ScanHandler` and rewire `scan.py`

**Files:**
- Modify: `src/plcc/cmd/scan.py`
- Modify: `src/plcc/cmd/scan_test.py`

`ScanHandler.feed(content, source)` pipes `content` to a fresh `plcc-tokens` subprocess with `--source-name=<source>`, renders the token records, and always returns `True` (scan has no continuation concept).

The existing `scan_test.py` tests the old per-source TTY hint loop; those tests will be replaced with `ScanHandler` unit tests.

- [ ] **Step 1: Write the failing tests**

  Replace the entire contents of `src/plcc/cmd/scan_test.py` with:

  ```python
  import io
  import json
  import subprocess
  import sys
  from types import SimpleNamespace

  import pytest

  from .scan import ScanHandler, main as run_main


  def _make_proc(stdout_lines=None):
      data = b"".join(stdout_lines or [])
      return SimpleNamespace(
          stdout=io.BytesIO(data),
          returncode=0,
          wait=lambda: None,
      )


  @pytest.fixture(autouse=True)
  def grammar(tmp_path, monkeypatch):
      monkeypatch.chdir(tmp_path)
      (tmp_path / "grammar.plcc").write_text("")


  @pytest.fixture(autouse=True)
  def stub_make(monkeypatch):
      monkeypatch.setattr(subprocess, "run", lambda *a, **kw: SimpleNamespace(returncode=0))


  # --- ScanHandler.feed() ---

  def test_scan_handler_passes_source_name_to_plcc_tokens(monkeypatch):
      calls = []
      def fake_popen(cmd, **kw):
          calls.append(cmd)
          return _make_proc()
      monkeypatch.setattr(subprocess, "Popen", fake_popen)
      handler = ScanHandler(spec_path="build/spec.json", tokens_flags=[])
      handler.feed(b"hello\n", "myfile.txt")
      assert any("--source-name=myfile.txt" in arg for arg in calls[0])


  def test_scan_handler_pipes_content_to_stdin(monkeypatch):
      received = []
      class FakeProc:
          stdout = io.BytesIO(b"")
          returncode = 0
          def __init__(self): self.stdin = io.BytesIO()
          def wait(self): pass
          def communicate(self, inp=None):
              if inp: received.append(inp)
              return b"", b""
      monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: FakeProc())
      handler = ScanHandler(spec_path="build/spec.json", tokens_flags=[])
      handler.feed(b"hello\n", "-")
      # content was passed; we verify via communicate or stdin


  def test_scan_handler_always_returns_true(monkeypatch):
      monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: _make_proc())
      handler = ScanHandler(spec_path="build/spec.json", tokens_flags=[])
      assert handler.feed(b"", "-") is True
      assert handler.feed(b"anything\n", "foo.txt") is True


  def test_scan_handler_renders_token_records(monkeypatch, capsys):
      token = json.dumps({
          "kind": "token", "name": "NUM", "lexeme": "42",
          "source": {"file": "-", "line": 1, "column": 1}
      }).encode() + b"\n"
      monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: _make_proc([token]))
      handler = ScanHandler(spec_path="build/spec.json", tokens_flags=[])
      handler.feed(b"42\n", "-")
      out, _ = capsys.readouterr()
      assert "NUM" in out
      assert "42" in out
  ```

- [ ] **Step 2: Run to confirm failure**

  ```bash
  bin/test/units.bash src/plcc/cmd/scan_test.py -v
  ```

  Expected: FAIL (`cannot import name 'ScanHandler'`).

- [ ] **Step 3: Implement**

  Rewrite `src/plcc/cmd/scan.py`. Keep `_location_str`, `_render_record`, `Events`, `__doc__`
  unchanged. Replace the IO block in `main()` and add `ScanHandler`:

  ```python
  import enum
  import json
  import os
  import subprocess
  import sys

  from docopt import docopt, DocoptExit

  from plcc.verbose import VerboseContext, VERBOSE_OPTIONS
  from .source_runner import SourceRunner


  def _location_str(source):
      file = source.get("file", "-")
      line = source.get("line", "?")
      col = source.get("column", "?")
      return f"{file}:{line}:{col}"


  __doc__ = """plcc-scan
      Tokenize source input and print tokens in human-readable format.

  Usage:
      plcc-scan [-v ...] [options] [SOURCE ...]

  Arguments:
      SOURCE      Source files to tokenize. Reads stdin if none given.

  Options:
      -h --help                   Show this message.
      --grammar-file=<path>       Path to the PLCC grammar file [default: grammar.plcc].
      -t --trace                  Show detailed scanning output.
  """ + VERBOSE_OPTIONS


  class Events(enum.Enum):
      STARTED = "started"
      FINISHED = "finished"


  def _render_record(record, show_skips, show_line, show_attempts):
      kind = record.get("kind")

      if kind == "error":
          loc = _location_str(record.get("pos", {}))
          lexeme = record.get("lexeme", "?")
          message = record.get("message", "unrecognized character")
          print(f"{loc}: error: {message} '{lexeme}'", flush=True)
          return

      if kind == "skip" and not show_skips:
          return

      if kind not in ("token", "skip"):
          return

      source = record.get("source", {})
      loc = _location_str(source)
      name = record.get("name", "?")
      lexeme = record.get("lexeme", "?")
      source_line = record.get("source_line", "")
      attempts = record.get("attempts", [])
      col = source.get("column", 1)

      if show_line and source_line:
          print(source_line, flush=True)
          print(" " * (col - 1) + "^", flush=True)

      if show_attempts:
          print("Candidates:", flush=True)
          for attempt in attempts:
              if attempt.get("char_count", 0) == 0:
                  continue
              prefix = "-> " if attempt.get("winner") else "   "
              a_name = attempt.get("name", "?")
              a_regex = attempt.get("regex", "?")
              a_count = attempt.get("char_count", 0)
              a_lexeme = attempt.get("lexeme", "?")
              print(f"{prefix}{a_name} '{a_regex}' {a_count} chars '{a_lexeme}'", flush=True)

      if show_attempts:
          if kind == "skip":
              print(f"{loc}: skip: {name} '{lexeme}'", flush=True)
          else:
              print(f"{loc}: token: {name} '{lexeme}'", flush=True)
          print(flush=True)
      elif kind == "skip":
          print(f"{loc} {name} '{lexeme}' SKIPPED", flush=True)
      else:
          print(f"{loc} {name} '{lexeme}'", flush=True)


  class ScanHandler:
      def __init__(self, spec_path, tokens_flags):
          self._spec_path = spec_path
          self._tokens_flags = tokens_flags

      def feed(self, content, source):
          proc = subprocess.Popen(
              ["plcc-tokens", self._spec_path,
               f"--source-name={source}", "-"] + self._tokens_flags,
              stdin=subprocess.PIPE,
              stdout=subprocess.PIPE,
              stderr=None,
          )
          stdout, _ = proc.communicate(content)
          proc.wait()
          trace = "--trace" in self._tokens_flags
          for raw in stdout.splitlines():
              raw = raw.strip()
              if not raw:
                  continue
              record = json.loads(raw)
              _render_record(record, trace, trace, trace)
          if proc.returncode != 0:
              print(f"plcc-scan: plcc-tokens failed (exit {proc.returncode})",
                    file=sys.stderr)
              sys.exit(proc.returncode)
          return True


  def main(argv=None):
      if argv is None:
          argv = sys.argv[1:]
      try:
          args = docopt(__doc__, argv)
      except DocoptExit as e:
          print(str(e), file=sys.stderr)
          print(file=sys.stderr)
          print("Run 'plcc-scan --help' for more information.", file=sys.stderr)
          sys.exit(1)

      verbose = VerboseContext.from_args("plcc-scan", Events, args)
      grammar_file = args["--grammar-file"]
      sources = args["SOURCE"]
      trace = args["--trace"]

      if not os.path.exists(grammar_file):
          print(f"plcc-scan: grammar file not found: {grammar_file}", file=sys.stderr)
          print(file=sys.stderr)
          print("Run 'plcc-scan --help' for more information.", file=sys.stderr)
          sys.exit(1)

      verbose.emit(Events.STARTED, message=f"scanning with {grammar_file}")
      child_flags = verbose.child_flags()

      make_result = subprocess.run(
          ['plcc-make', '--through=scan', f'--grammar-file={grammar_file}'] + child_flags,
          stderr=None,
      )
      if make_result.returncode != 0:
          sys.exit(make_result.returncode)

      spec_path = os.path.join('build', 'spec.json')
      tokens_flags = child_flags + (["--trace"] if trace else [])

      handler = ScanHandler(spec_path=spec_path, tokens_flags=tokens_flags)
      runner = SourceRunner()
      runner.run(sources, handler)

      verbose.emit(Events.FINISHED, message="done")
  ```

- [ ] **Step 4: Run to confirm pass**

  ```bash
  bin/test/units.bash src/plcc/cmd/scan_test.py -v
  ```

  Expected: all pass.

- [ ] **Step 5: Run full unit suite**

  ```bash
  bin/test/units.bash
  ```

  Expected: all pass.

- [ ] **Step 6: Run bats command tests for plcc-scan**

  ```bash
  bin/test/commands.bash tests/bats/commands/plcc-scan.bats
  ```

  Expected: all pass.

- [ ] **Step 7: Commit**

  ```bash
  git -C .worktrees/source-runner add src/plcc/cmd/scan.py src/plcc/cmd/scan_test.py
  git -C .worktrees/source-runner commit -m "feat(scan): add ScanHandler; route IO through SourceRunner"
  ```

---

## Task 6: Add `ParseHandler` and rewire `parse.py`

**Files:**
- Modify: `src/plcc/cmd/parse.py`
- Create: `src/plcc/cmd/parse_test.py`

`ParseHandler.feed(content, source)` spawns a fresh `plcc-tokens | plcc-tree` pipeline, pipes `content`, reads stdout. Non-empty stdout → renders result, returns `True`. Empty stdout → returns `False` (incomplete parse, need more input).

- [ ] **Step 1: Write the failing tests**

  Create `src/plcc/cmd/parse_test.py`:

  ```python
  import io
  import json
  import subprocess
  import sys
  from types import SimpleNamespace

  import pytest

  from .parse import ParseHandler


  def _proc(stdout=b"", returncode=0):
      p = SimpleNamespace(
          stdout=io.BytesIO(stdout),
          stderr=io.BytesIO(b""),
          returncode=returncode,
      )
      p.communicate = lambda: (stdout, b"")
      p.wait = lambda: None
      p.stdin = io.BytesIO()
      return p


  def _tree_record():
      return json.dumps({
          "kind": "tree", "rule": "program",
          "source": {}, "children": []
      }).encode() + b"\n"


  def _error_record(msg="syntax error"):
      return json.dumps({"kind": "error", "message": msg}).encode() + b"\n"


  @pytest.fixture()
  def handler():
      return ParseHandler(spec_path="build/spec.json", ll1_path="build/ll1.json",
                          child_flags=[])


  def test_feed_returns_true_when_tree_produced(monkeypatch, handler):
      procs = iter([_proc(), _proc(stdout=_tree_record())])
      monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
      assert handler.feed(b"1+2\n", "-") is True


  def test_feed_returns_false_when_stdout_empty(monkeypatch, handler):
      procs = iter([_proc(), _proc(stdout=b"")])
      monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
      assert handler.feed(b"1+\n", "-") is False


  def test_feed_returns_true_on_error_record(monkeypatch, handler):
      procs = iter([_proc(), _proc(stdout=_error_record())])
      monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
      assert handler.feed(b"bad input\n", "-") is True


  def test_feed_prints_tree(monkeypatch, handler, capsys):
      procs = iter([_proc(), _proc(stdout=_tree_record())])
      monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
      handler.feed(b"1\n", "-")
      out, _ = capsys.readouterr()
      assert "program" in out


  def test_feed_prints_error_to_stderr(monkeypatch, handler, capsys):
      procs = iter([_proc(), _proc(stdout=_error_record("oops"))])
      monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
      handler.feed(b"bad\n", "-")
      _, err = capsys.readouterr()
      assert "oops" in err
  ```

- [ ] **Step 2: Run to confirm failure**

  ```bash
  bin/test/units.bash src/plcc/cmd/parse_test.py -v
  ```

  Expected: FAIL (`cannot import name 'ParseHandler'`).

- [ ] **Step 3: Implement**

  Rewrite `src/plcc/cmd/parse.py`. Keep `_location_str`, `_print_tree`, `Events`, `__doc__` unchanged. Add `ParseHandler` and replace the IO block in `main()`:

  ```python
  import enum
  import json
  import os
  import subprocess
  import sys

  from docopt import docopt, DocoptExit

  from plcc.verbose import VerboseContext, VERBOSE_OPTIONS, reap_pipeline
  from .source_runner import SourceRunner


  __doc__ = """plcc-parse
      Parse source input and print parse tree in human-readable format.

  Usage:
      plcc-parse [-v ...] [options] [SOURCE ...]

  Arguments:
      SOURCE      Source files to parse. Reads stdin if none given.

  Options:
      -h --help                   Show this message.
      --grammar-file=<path>       Path to the PLCC grammar file [default: grammar.plcc].
  """ + VERBOSE_OPTIONS


  class Events(enum.Enum):
      STARTED = "started"
      FINISHED = "finished"


  def _location_str(source):
      file = source.get("file")
      line = source.get("line", "?")
      col = source.get("column", "?")
      if file and file != "<stdin>":
          return f"{file}:{line}:{col}"
      return f"{line}:{col}"


  class ParseHandler:
      def __init__(self, spec_path, ll1_path, child_flags):
          self._spec_path = spec_path
          self._ll1_path = ll1_path
          self._child_flags = child_flags

      def feed(self, content, source):
          tokens_proc = subprocess.Popen(
              ["plcc-tokens", self._spec_path, "-"] + self._child_flags,
              stdin=subprocess.PIPE,
              stdout=subprocess.PIPE,
              stderr=None,
          )
          tree_proc = subprocess.Popen(
              ["plcc-tree", f"--ll1={self._ll1_path}"] + self._child_flags,
              stdin=tokens_proc.stdout,
              stdout=subprocess.PIPE,
              stderr=None,
          )
          tokens_proc.stdout.close()
          tokens_proc.stdin.write(content)
          tokens_proc.stdin.close()
          tree_out, _ = tree_proc.communicate()
          tokens_proc.wait()

          tree_out = tree_out.strip()
          if not tree_out:
              return False

          record = json.loads(tree_out)
          if record.get("kind") == "error":
              print(f"error: {record.get('message', 'parse error')}", file=sys.stderr)
              return True

          _print_tree(record, indent=0)
          return True


  def main(argv=None):
      if argv is None:
          argv = sys.argv[1:]
      try:
          args = docopt(__doc__, argv)
      except DocoptExit as e:
          print(str(e), file=sys.stderr)
          print(file=sys.stderr)
          print("Run 'plcc-parse --help' for more information.", file=sys.stderr)
          sys.exit(1)

      verbose = VerboseContext.from_args("plcc-parse", Events, args)
      grammar_file = args["--grammar-file"]
      sources = args["SOURCE"]

      if not os.path.exists(grammar_file):
          print(f"plcc-parse: grammar file not found: {grammar_file}", file=sys.stderr)
          print(file=sys.stderr)
          print("Run 'plcc-parse --help' for more information.", file=sys.stderr)
          sys.exit(1)

      verbose.emit(Events.STARTED, message=f"parsing with {grammar_file}")
      child_flags = verbose.child_flags_for_orchestrator(min_level=0)

      make_result = subprocess.run(
          ['plcc-make', '--through=parse', f'--grammar-file={grammar_file}'] + child_flags,
          stderr=subprocess.PIPE,
      )
      if make_result.stderr:
          events = verbose.parse_child_events(make_result.stderr.decode('utf-8', errors='replace'))
          verbose.reformat_child_events(events)
      if make_result.returncode != 0:
          sys.exit(make_result.returncode)

      spec_path = os.path.join('build', 'spec.json')
      ll1_path = os.path.join('build', 'll1.json')

      handler = ParseHandler(spec_path=spec_path, ll1_path=ll1_path,
                             child_flags=child_flags)
      runner = SourceRunner()
      runner.run(sources, handler)

      verbose.emit(Events.FINISHED, message="done")


  def _print_tree(node, indent):
      prefix = "  " * indent
      kind = node.get("kind", "?")
      if kind == "tree":
          rule = node.get("rule", "?")
          print(f"{prefix}{rule}")
          for _field, child in node.get("children", []):
              _print_tree(child, indent + 1)
      elif kind == "token":
          name = node.get("name", "?")
          lexeme = node.get("lexeme", "?")
          source = node.get("source", {})
          loc = _location_str(source)
          print(f"{prefix}{name} '{lexeme}' [{loc}]")
      elif kind == "error":
          source = node.get("source", {})
          loc = _location_str(source)
          message = node.get("message", "unknown error")
          print(f"{prefix}{loc}: error: {message}")
  ```

- [ ] **Step 4: Run to confirm pass**

  ```bash
  bin/test/units.bash src/plcc/cmd/parse_test.py -v
  ```

  Expected: all pass.

- [ ] **Step 5: Run full unit suite**

  ```bash
  bin/test/units.bash
  ```

  Expected: all pass.

- [ ] **Step 6: Run bats command tests for plcc-parse**

  ```bash
  bin/test/commands.bash tests/bats/commands/plcc-parse.bats
  ```

  Expected: all pass.

- [ ] **Step 7: Commit**

  ```bash
  git -C .worktrees/source-runner add src/plcc/cmd/parse.py src/plcc/cmd/parse_test.py
  git -C .worktrees/source-runner commit -m "feat(parse): add ParseHandler; route IO through SourceRunner"
  ```

---

## Task 7: Add `RepHandler` and rewire `rep.py`

**Files:**
- Modify: `src/plcc/cmd/rep.py`
- Create: `src/plcc/cmd/rep_test.py`

`RepHandler.feed(content, source)` is structurally identical to `ParseHandler` up to the point of getting a tree. If a tree is produced, it is forwarded to the long-lived interpreter; the interpreter's response is printed. If no tree (incomplete), returns `False` without touching the interpreter.

- [ ] **Step 1: Write the failing tests**

  Create `src/plcc/cmd/rep_test.py`:

  ```python
  import io
  import json
  import subprocess
  import sys
  from types import SimpleNamespace

  import pytest

  from .rep import RepHandler


  def _proc(stdout=b"", returncode=0):
      p = SimpleNamespace(returncode=returncode)
      p.communicate = lambda: (stdout, b"")
      p.wait = lambda: None
      p.stdin = io.BytesIO()
      p.stdout = io.BytesIO(stdout)
      return p


  def _tree():
      return json.dumps({
          "kind": "tree", "rule": "program",
          "source": {}, "children": []
      }).encode() + b"\n"


  def _error_record():
      return json.dumps({"kind": "error", "message": "bad"}).encode() + b"\n"


  def _make_interpreter(response=b'{"kind":"result","value":"42"}\n'):
      interp = SimpleNamespace()
      interp.stdin = io.BytesIO()
      interp.stdout = io.BytesIO(response)
      return interp


  @pytest.fixture()
  def handler(monkeypatch):
      interp = _make_interpreter()
      return RepHandler(
          spec_path="build/spec.json",
          ll1_path="build/ll1.json",
          interpreter=interp,
          verbose_format="text",
      ), interp


  def test_feed_returns_false_when_no_tree(monkeypatch, handler):
      h, _ = handler
      procs = iter([_proc(), _proc(stdout=b"")])
      monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
      assert h.feed(b"1+\n", "-") is False


  def test_feed_returns_true_when_tree_produced(monkeypatch, handler):
      h, _ = handler
      procs = iter([_proc(), _proc(stdout=_tree())])
      monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
      assert h.feed(b"42\n", "-") is True


  def test_feed_does_not_contact_interpreter_when_no_tree(monkeypatch, handler):
      h, interp = handler
      procs = iter([_proc(), _proc(stdout=b"")])
      monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
      h.feed(b"1+\n", "-")
      assert interp.stdin.tell() == 0  # nothing written to interpreter


  def test_feed_sends_tree_to_interpreter(monkeypatch, handler):
      h, interp = handler
      procs = iter([_proc(), _proc(stdout=_tree())])
      monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
      h.feed(b"42\n", "-")
      written = interp.stdin.getvalue()
      assert b"tree" in written


  def test_feed_prints_result(monkeypatch, handler, capsys):
      h, _ = handler
      procs = iter([_proc(), _proc(stdout=_tree())])
      monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
      h.feed(b"42\n", "-")
      out, _ = capsys.readouterr()
      assert "42" in out


  def test_feed_returns_true_on_error_record(monkeypatch, handler):
      h, _ = handler
      procs = iter([_proc(), _proc(stdout=_error_record())])
      monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
      assert h.feed(b"bad\n", "-") is True
  ```

- [ ] **Step 2: Run to confirm failure**

  ```bash
  bin/test/units.bash src/plcc/cmd/rep_test.py -v
  ```

  Expected: FAIL (`cannot import name 'RepHandler'`).

- [ ] **Step 3: Implement**

  Rewrite `src/plcc/cmd/rep.py`. Keep `_resolve_tool`, `_read_response`, `_render_record`, `Events`, `__doc__` unchanged. Add `RepHandler` and replace the IO block in `main()`:

  ```python
  import enum
  import json
  import os
  import subprocess
  import sys

  from docopt import docopt, DocoptExit

  from plcc.verbose import VerboseContext, VERBOSE_OPTIONS
  from .source_runner import SourceRunner


  __doc__ = """plcc-rep
      REPL — read, eval, print loop for a PLCC grammar.

  Usage:
      plcc-rep [-v ...] [options] [SOURCE ...]

  Arguments:
      SOURCE      Source files to evaluate before entering interactive mode.

  Options:
      --grammar-file=<path>   Path to the PLCC grammar file [default: grammar.plcc].
      --tool=NAME             Semantic section to run (inferred if only one exists).
      -h --help               Show this message.
  """ + VERBOSE_OPTIONS


  class Events(enum.Enum):
      STARTED = "started"
      FINISHED = "finished"


  class RepHandler:
      def __init__(self, spec_path, ll1_path, interpreter, verbose_format):
          self._spec_path = spec_path
          self._ll1_path = ll1_path
          self._interpreter = interpreter
          self._verbose_format = verbose_format

      def feed(self, content, source):
          tokens_proc = subprocess.Popen(
              ["plcc-tokens", self._spec_path, "-"],
              stdin=subprocess.PIPE,
              stdout=subprocess.PIPE,
              stderr=None,
          )
          tree_proc = subprocess.Popen(
              ["plcc-tree", f"--ll1={self._ll1_path}"],
              stdin=tokens_proc.stdout,
              stdout=subprocess.PIPE,
              stderr=None,
          )
          tokens_proc.stdout.close()
          tokens_proc.stdin.write(content)
          tokens_proc.stdin.close()
          tree_out, _ = tree_proc.communicate()
          tokens_proc.wait()

          tree_out = tree_out.strip()
          if not tree_out:
              return False

          record = json.loads(tree_out)
          if record.get("kind") == "error":
              print(f"error: {record.get('message', 'parse error')}", file=sys.stderr)
              return True

          try:
              self._interpreter.stdin.write(tree_out + b'\n')
              self._interpreter.stdin.flush()
          except BrokenPipeError:
              print('plcc-rep: interpreter exited unexpectedly', file=sys.stderr)
              sys.exit(1)

          _read_response(self._interpreter.stdout, self._verbose_format)
          return True


  def main(argv=None):
      if argv is None:
          argv = sys.argv[1:]
      try:
          args = docopt(__doc__, argv)
      except DocoptExit as e:
          print(str(e), file=sys.stderr)
          print(file=sys.stderr)
          print("Run 'plcc-rep --help' for more information.", file=sys.stderr)
          sys.exit(1)

      verbose = VerboseContext.from_args("plcc-rep", Events, args)
      grammar_file = args['--grammar-file']
      sources = args['SOURCE']
      tool_name = args['--tool']
      verbose_format = args['--verbose-format'] or 'text'

      if not os.path.exists(grammar_file):
          print(f"plcc-rep: grammar file not found: {grammar_file}", file=sys.stderr)
          print(file=sys.stderr)
          print("Run 'plcc-rep --help' for more information.", file=sys.stderr)
          sys.exit(1)

      verbose.emit(Events.STARTED, message=f'starting rep with {grammar_file}')
      child_flags = verbose.child_flags_for_orchestrator(min_level=0)

      make_result = subprocess.run(
          ['plcc-make', f'--grammar-file={grammar_file}'] + child_flags,
          stderr=subprocess.PIPE,
      )
      if make_result.stderr:
          events = verbose.parse_child_events(make_result.stderr.decode('utf-8', errors='replace'))
          verbose.reformat_child_events(events)
      if make_result.returncode != 0:
          sys.exit(make_result.returncode)

      spec_path = os.path.join('build', 'spec.json')
      ll1_path = os.path.join('build', 'll1.json')

      with open(spec_path) as f:
          spec = json.load(f)

      tool_name, language = _resolve_tool(spec, tool_name)
      tool_dir = os.path.join('build', tool_name)

      interpreter = subprocess.Popen(
          ['plcc-lang-run', f'--target={language}', f'--output={tool_dir}'],
          stdin=subprocess.PIPE,
          stdout=subprocess.PIPE,
          stderr=None,
      )

      try:
          handler = RepHandler(
              spec_path=spec_path,
              ll1_path=ll1_path,
              interpreter=interpreter,
              verbose_format=verbose_format,
          )
          runner = SourceRunner()
          runner.run(sources, handler)
      finally:
          try:
              interpreter.stdin.close()
          except BrokenPipeError:
              pass
          interpreter.wait()

      verbose.emit(Events.FINISHED, message='done')


  def _resolve_tool(spec, tool_name):
      sections = spec.get('semantics', [])
      if tool_name:
          for s in sections:
              if s['tool'] == tool_name:
                  return s['tool'], s['language']
          print(f"plcc-rep: no semantic section with tool '{tool_name}'", file=sys.stderr)
          sys.exit(1)

      if len(sections) == 0:
          print("plcc-rep: no semantic sections found in grammar.", file=sys.stderr)
          sys.exit(1)

      if len(sections) == 1:
          return sections[0]['tool'], sections[0]['language']

      names = [s['tool'] for s in sections]
      print(f"plcc-rep: multiple semantic sections: {names}. Use --tool=NAME.", file=sys.stderr)
      sys.exit(1)


  def _read_response(stdout, verbose_format):
      while True:
          raw = stdout.readline()
          if not raw:
              print('plcc-rep: interpreter exited unexpectedly', file=sys.stderr)
              sys.exit(1)
          line = raw.decode('utf-8', errors='replace').rstrip('\n')
          try:
              record = json.loads(line)
          except json.JSONDecodeError:
              print(line)
              continue
          if 'kind' not in record:
              print(line)
              continue
          _render_record(record, verbose_format)
          return


  def _render_record(record, verbose_format):
      if verbose_format == 'json':
          print(json.dumps(record))
          return
      if record['kind'] == 'result':
          value = record.get('value')
          if value is not None:
              print(value)
      elif record['kind'] == 'error':
          print(f"error: {record.get('type')}: {record.get('message')}", file=sys.stderr)
  ```

- [ ] **Step 4: Run to confirm pass**

  ```bash
  bin/test/units.bash src/plcc/cmd/rep_test.py -v
  ```

  Expected: all pass.

- [ ] **Step 5: Run full unit suite**

  ```bash
  bin/test/units.bash
  ```

  Expected: all pass.

- [ ] **Step 6: Run bats command tests for plcc-rep**

  ```bash
  bin/test/commands.bash tests/bats/commands/plcc-rep.bats
  ```

  Expected: all pass.

- [ ] **Step 7: Commit**

  ```bash
  git -C .worktrees/source-runner add src/plcc/cmd/rep.py src/plcc/cmd/rep_test.py
  git -C .worktrees/source-runner commit -m "feat(rep): add RepHandler; route IO through SourceRunner"
  ```

---

## Task 8: Final verification

- [ ] **Step 1: Run the full functional test suite**

  ```bash
  cd .worktrees/source-runner && bin/test/functional.bash
  ```

  Expected: all tiers pass (units, commands, integration, e2e).

- [ ] **Step 2: Confirm bats tests for the affected tokens and parser commands still pass**

  ```bash
  cd .worktrees/source-runner && bin/test/commands.bash tests/bats/commands/plcc-tokens.bats tests/bats/commands/plcc-parser-table.bats
  ```

  Expected: all pass.
