# Version Header Prints First Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Print `plcc-ng <version>` as the very first output of every orchestrator command, even when the command fails early, and split the grammar path into a separate line printed only after `plcc-make` succeeds.

**Architecture:** Add `print_version_line` and `print_grammar_line` to `output.py`, replacing `print_startup_banner`. Each of the five orchestrators (`scan`, `parse`, `rep`, `diagram`, `make`) prints the version line before any other output and accepts `--no-banner` to suppress both lines. Orchestrators always pass `--no-banner` when spawning `plcc-make` as a subprocess, preventing double-printing.

**Tech Stack:** Python, docopt, pytest, `plcc.build.grammar.read_grammar`, `plcc.version.get_version`

---

### Task 1: Add print_version_line and print_grammar_line to output.py

**Files:**
- Modify: `src/plcc/cmd/output.py`
- Modify: `src/plcc/cmd/output_test.py`

- [ ] **Step 1: Write failing tests for the two new functions**

Replace all content in `src/plcc/cmd/output_test.py` with:

```python
from .output import print_user_error, print_version_line, print_grammar_line


def test_print_user_error_writes_to_stdout(capsys):
    print_user_error("scan error: bad token")
    out, err = capsys.readouterr()
    assert "scan error: bad token" in out
    assert err == ""


def test_print_user_error_does_not_write_to_stderr(capsys):
    print_user_error("any message")
    _, err = capsys.readouterr()
    assert err == ""


def test_print_version_line_contains_version(capsys):
    print_version_line("1.2.3")
    out, _ = capsys.readouterr()
    assert "plcc-ng 1.2.3" in out


def test_print_version_line_goes_to_stdout(capsys):
    print_version_line("1.2.3")
    _, err = capsys.readouterr()
    assert err == ""


def test_print_version_line_prints_one_line(capsys):
    print_version_line("1.2.3")
    out, _ = capsys.readouterr()
    assert out.count("\n") == 1


def test_print_grammar_line_contains_grammar_path(capsys):
    print_grammar_line("/abs/path/grammar.plcc")
    out, _ = capsys.readouterr()
    assert "/abs/path/grammar.plcc" in out


def test_print_grammar_line_goes_to_stdout(capsys):
    print_grammar_line("/abs/path/grammar.plcc")
    _, err = capsys.readouterr()
    assert err == ""


def test_print_grammar_line_no_tool_prints_one_line(capsys):
    print_grammar_line("/abs/path/grammar.plcc")
    out, _ = capsys.readouterr()
    assert out.count("\n") == 1


def test_print_grammar_line_with_tool_prints_running_line(capsys):
    print_grammar_line("/abs/path/grammar.plcc", tool="calc", language="python")
    out, _ = capsys.readouterr()
    assert "Running calc with python." in out


def test_print_grammar_line_tool_line_goes_to_stdout(capsys):
    print_grammar_line("/abs/path/grammar.plcc", tool="calc", language="python")
    _, err = capsys.readouterr()
    assert err == ""


def test_print_grammar_line_with_tool_prints_two_lines(capsys):
    print_grammar_line("/abs/path/grammar.plcc", tool="calc", language="python")
    out, _ = capsys.readouterr()
    assert out.count("\n") == 2
```

- [ ] **Step 2: Run tests to verify they fail**

```
bin/test/units.bash src/plcc/cmd/output_test.py -v
```

Expected: FAIL — `ImportError: cannot import name 'print_version_line'`

- [ ] **Step 3: Replace output.py with the two new functions**

Replace all content in `src/plcc/cmd/output.py` with:

```python
def print_user_error(message):
    print(message, flush=True)


def print_version_line(version):
    print(f"plcc-ng {version}", flush=True)


def print_grammar_line(grammar_path, tool=None, language=None):
    print(f"grammar: {grammar_path}", flush=True)
    if tool is not None and language is not None:
        print(f"Running {tool} with {language}.", flush=True)
```

- [ ] **Step 4: Run tests to verify they pass**

```
bin/test/units.bash src/plcc/cmd/output_test.py -v
```

Expected: all output tests pass

- [ ] **Step 5: Run full unit suite to catch broken callers**

```
bin/test/units.bash
```

Expected: FAIL — `scan.py`, `parse.py`, `rep.py` import `print_startup_banner` which no longer exists

*(This is expected — the next tasks fix each caller. Do not commit yet.)*

---

### Task 2: Update scan.py — version first, --no-banner, pass --no-banner to make

**Files:**
- Modify: `src/plcc/cmd/scan.py`
- Modify: `src/plcc/cmd/scan_test.py`

- [ ] **Step 1: Write failing tests**

Add these tests to the bottom of `src/plcc/cmd/scan_test.py`:

```python
def test_main_version_line_appears_even_when_make_fails(monkeypatch, capsys):
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: SimpleNamespace(returncode=1))
    monkeypatch.setattr("plcc.cmd.scan.get_version", lambda: "1.2.3")
    with pytest.raises(SystemExit):
        run_main([])
    out, _ = capsys.readouterr()
    assert "plcc-ng 1.2.3" in out


def test_main_no_banner_suppresses_version_line(monkeypatch, tmp_path, capsys):
    build = tmp_path / "build"
    build.mkdir()
    (build / ".grammar").write_text(str(tmp_path / "grammar.plcc"))
    monkeypatch.setattr(_scan_module, "SourceRunner",
                        lambda **kw: type("R", (), {"run": lambda self, s, h: True})())
    monkeypatch.setattr("plcc.cmd.scan.get_version", lambda: "1.2.3")
    run_main(["--no-banner"])
    out, _ = capsys.readouterr()
    assert "plcc-ng" not in out


def test_main_no_banner_suppresses_grammar_line(monkeypatch, tmp_path, capsys):
    build = tmp_path / "build"
    build.mkdir()
    (build / ".grammar").write_text(str(tmp_path / "grammar.plcc"))
    monkeypatch.setattr(_scan_module, "SourceRunner",
                        lambda **kw: type("R", (), {"run": lambda self, s, h: True})())
    monkeypatch.setattr("plcc.cmd.scan.get_version", lambda: "1.2.3")
    run_main(["--no-banner"])
    out, _ = capsys.readouterr()
    assert "grammar:" not in out


def test_main_make_call_includes_no_banner(monkeypatch, tmp_path, capsys):
    build = tmp_path / "build"
    build.mkdir()
    (build / ".grammar").write_text(str(tmp_path / "grammar.plcc"))
    calls = []
    def fake_run(cmd, **kw):
        calls.append(list(cmd))
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(_scan_module, "SourceRunner",
                        lambda **kw: type("R", (), {"run": lambda self, s, h: True})())
    monkeypatch.setattr("plcc.cmd.scan.get_version", lambda: "0")
    run_main([])
    make_calls = [c for c in calls if c and c[0] == "plcc-make"]
    assert make_calls, "plcc-make was not called"
    assert any("--no-banner" in c for c in make_calls)
```

- [ ] **Step 2: Run tests to verify they fail (and that existing tests also fail due to import error)**

```
bin/test/units.bash src/plcc/cmd/scan_test.py -v
```

Expected: FAIL — `ImportError: cannot import name 'print_startup_banner'` from scan.py's import

- [ ] **Step 3: Update scan.py**

Replace `src/plcc/cmd/scan.py` with:

```python
import enum
import json
import os
import subprocess
import sys

from docopt import docopt, DocoptExit

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS
from plcc.version import get_version
from plcc.build.grammar import read_grammar
from .output import print_version_line, print_grammar_line, print_user_error
from .source_runner import SourceRunner, SubmitOn


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
    -g <path> --grammar=<path>  Grammar to build from. Once set, remembered for subsequent
                                commands until changed. Defaults to grammar.plcc on first use.
    -t --trace                  Show detailed scanning output.
    --no-banner                 Suppress the version and grammar banner.
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def _render_record(record, show_skips, show_line, show_attempts):
    kind = record.get("kind")

    if kind == "error":
        loc = _location_str(record.get("source", {}))
        message = record.get("message", "unrecognized character")
        print_user_error(f"{loc}: error: {message}")
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

    def feed(self, content, source, eof=False):
        proc = subprocess.Popen(
            ["plcc-tokens", self._spec_path,
             f"--source-name={source}", "-"] + self._tokens_flags,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=None,
        )
        stdout, _ = proc.communicate(content)
        trace = "--trace" in self._tokens_flags
        for raw in stdout.splitlines():
            raw = raw.strip()
            if not raw:
                continue
            record = json.loads(raw)
            if record.get("name") == "eof":
                continue
            _render_record(record, trace, trace, trace)
        if proc.returncode != 0:
            print(f"plcc-scan: plcc-tokens failed (exit {proc.returncode})",
                  file=sys.stderr)
            sys.exit(proc.returncode)
        return True


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    if "--no-banner" not in argv:
        print_version_line(get_version())
    try:
        args = docopt(__doc__, argv)
    except DocoptExit as e:
        print(str(e), file=sys.stderr)
        print(file=sys.stderr)
        print("Run 'plcc-scan --help' for more information.", file=sys.stderr)
        sys.exit(1)

    no_banner = args["--no-banner"]
    verbose = VerboseContext.from_args("plcc-scan", Events, args)
    grammar_file = args["--grammar"]
    sources = args["SOURCE"]
    trace = args["--trace"]

    if grammar_file is not None and not os.path.exists(grammar_file):
        print(f"plcc-scan: grammar file not found: {grammar_file}", file=sys.stderr)
        print(file=sys.stderr)
        print("Run 'plcc-scan --help' for more information.", file=sys.stderr)
        sys.exit(1)

    verbose.emit(Events.STARTED, message="scanning")
    child_flags = verbose.child_flags()

    make_result = subprocess.run(
        ["plcc-make", "--through=scan", "--no-banner"]
        + ([f"--grammar={grammar_file}"] if grammar_file is not None else [])
        + child_flags,
        stderr=None,
    )
    if make_result.returncode != 0:
        sys.exit(make_result.returncode)

    if not no_banner:
        print_grammar_line(os.path.abspath(read_grammar("build")))

    spec_path = os.path.join("build", "spec.json")
    tokens_flags = child_flags + (["--trace"] if trace else [])

    handler = ScanHandler(spec_path=spec_path, tokens_flags=tokens_flags)
    runner = SourceRunner(submit_on=SubmitOn.EOF)
    runner.run(sources, handler)

    verbose.emit(Events.FINISHED, message="done")
```

- [ ] **Step 4: Run scan tests to verify they pass**

```
bin/test/units.bash src/plcc/cmd/scan_test.py -v
```

Expected: all scan tests pass

- [ ] **Step 5: Run full unit suite (parse and rep still broken — expected)**

```
bin/test/units.bash 2>&1 | grep -E "FAILED|ERROR|passed|failed" | tail -5
```

Expected: failures only in parse_test.py and rep_test.py (still import print_startup_banner)

- [ ] **Step 6: Commit**

```bash
git -C /workspaces/plcc-ng/.worktrees/issue-067 add src/plcc/cmd/output.py src/plcc/cmd/output_test.py src/plcc/cmd/scan.py src/plcc/cmd/scan_test.py
git -C /workspaces/plcc-ng/.worktrees/issue-067 commit -m "$(cat <<'EOF'
feat(scan): print version first, add --no-banner, split banner output

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: Update parse.py — version first, --no-banner, pass --no-banner to make

**Files:**
- Modify: `src/plcc/cmd/parse.py`
- Modify: `src/plcc/cmd/parse_test.py`

- [ ] **Step 1: Write failing tests**

Add these tests to the bottom of `src/plcc/cmd/parse_test.py`:

```python
def test_parse_main_version_line_appears_even_when_make_fails(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "grammar.plcc").write_text("")
    monkeypatch.setattr("subprocess.run",
                        lambda *a, **kw: SimpleNamespace(returncode=1, stderr=b""))
    monkeypatch.setattr("plcc.cmd.parse.get_version", lambda: "1.2.3")
    with pytest.raises(SystemExit):
        from .parse import main as parse_main
        parse_main([])
    out, _ = capsys.readouterr()
    assert "plcc-ng 1.2.3" in out


def test_parse_main_no_banner_suppresses_version_line(monkeypatch, tmp_path, capsys):
    _setup_parse_main(monkeypatch, tmp_path)
    from .parse import main as parse_main
    parse_main(["--no-banner"])
    out, _ = capsys.readouterr()
    assert "plcc-ng" not in out


def test_parse_main_no_banner_suppresses_grammar_line(monkeypatch, tmp_path, capsys):
    _setup_parse_main(monkeypatch, tmp_path)
    from .parse import main as parse_main
    parse_main(["--no-banner"])
    out, _ = capsys.readouterr()
    assert "grammar:" not in out


def test_parse_main_make_call_includes_no_banner(monkeypatch, tmp_path, capsys):
    _setup_parse_main(monkeypatch, tmp_path)
    calls = []
    original_run = __import__("subprocess").run
    def capturing_run(cmd, **kw):
        calls.append(list(cmd))
        return SimpleNamespace(returncode=0, stderr=b"")
    monkeypatch.setattr("subprocess.run", capturing_run)
    from .parse import main as parse_main
    parse_main([])
    make_calls = [c for c in calls if c and c[0] == "plcc-make"]
    assert make_calls, "plcc-make was not called"
    assert any("--no-banner" in c for c in make_calls)
```

- [ ] **Step 2: Run tests to verify they fail**

```
bin/test/units.bash src/plcc/cmd/parse_test.py -v 2>&1 | tail -10
```

Expected: FAIL — `ImportError: cannot import name 'print_startup_banner'` in parse.py

- [ ] **Step 3: Update parse.py**

Replace `src/plcc/cmd/parse.py` with:

```python
import enum
import os
import subprocess
import sys

from docopt import docopt, DocoptExit

from plcc.version import get_version
from plcc.build.grammar import read_grammar
from plcc.verbose import VerboseContext, VERBOSE_OPTIONS
from .pipeline import TreePipeline, print_parse_error, location_str
from .output import print_version_line, print_grammar_line
from .source_runner import SourceRunner, SubmitOn

__doc__ = """plcc-parse
    Parse source input and print parse tree in human-readable format.

Usage:
    plcc-parse [-v ...] [options] [SOURCE ...]

Arguments:
    SOURCE      Source files to parse. Reads stdin if none given.

Options:
    -h --help                   Show this message.
    -t --trace                  Show step-by-step trace of the parse algorithm.
    -g <path> --grammar=<path>  Grammar to build from. Once set, remembered for subsequent
                                commands until changed. Defaults to grammar.plcc on first use.
    --no-banner                 Suppress the version and grammar banner.
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


class ParseHandler:
    def __init__(self, spec_path, ll1_path, child_flags, trees_flags=None, verbose=None):
        self._pipeline = TreePipeline(spec_path, ll1_path, child_flags, trees_flags=trees_flags, verbose=verbose)
        self.had_error = False

    def feed(self, content, source, eof=False):
        items = self._pipeline.run(content, eof)
        if items is None:
            return False
        for record, _ in items:
            if record.get("kind") == "parse-step":
                _print_parse_step(record)
            elif record.get("kind") == "error":
                print_parse_error(record, default_stage="plcc-parse")
                self.had_error = True
                break
            elif record.get("kind") == "tree":
                _print_tree(record, indent=0)
        return True


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    if "--no-banner" not in argv:
        print_version_line(get_version())
    try:
        args = docopt(__doc__, argv)
    except DocoptExit as e:
        print(str(e), file=sys.stderr)
        print(file=sys.stderr)
        print("Run 'plcc-parse --help' for more information.", file=sys.stderr)
        sys.exit(1)
    no_banner = args["--no-banner"]
    verbose = VerboseContext.from_args("plcc-parse", Events, args)
    grammar_file = args["--grammar"]
    trace = args["--trace"]
    sources = args["SOURCE"]

    if grammar_file is not None and not os.path.exists(grammar_file):
        print(f"plcc-parse: grammar file not found: {grammar_file}", file=sys.stderr)
        print(file=sys.stderr)
        print("Run 'plcc-parse --help' for more information.", file=sys.stderr)
        sys.exit(1)

    verbose.emit(Events.STARTED, message="parsing")
    child_flags = verbose.child_flags_for_orchestrator(min_level=0)
    trees_flags = child_flags + (["--trace"] if trace else [])

    make_result = subprocess.run(
        ["plcc-make", "--through=parse", "--no-banner"]
        + ([f"--grammar={grammar_file}"] if grammar_file is not None else [])
        + child_flags,
        stderr=subprocess.PIPE,
    )
    if make_result.stderr:
        events = verbose.parse_child_events(make_result.stderr.decode("utf-8", errors="replace"))
        verbose.reformat_child_events(events)
    if make_result.returncode != 0:
        sys.exit(make_result.returncode)

    if not no_banner:
        print_grammar_line(os.path.abspath(read_grammar("build")))

    spec_path = os.path.join("build", "spec.json")
    ll1_path = os.path.join("build", "ll1.json")

    handler = ParseHandler(spec_path=spec_path, ll1_path=ll1_path,
                           child_flags=child_flags, trees_flags=trees_flags, verbose=verbose)
    runner = SourceRunner(submit_on=SubmitOn.EOF)
    completed = runner.run(sources, handler)

    if not completed or handler.had_error:
        sys.exit(1)
    verbose.emit(Events.FINISHED, message="done")


def _print_tree(node, indent):
    if isinstance(node, list):
        for item in node:
            _print_tree(item, indent)
        return
    prefix = "  " * indent
    kind = node.get("kind", "?")
    if kind == "tree":
        rule = node.get("rule", "?")
        children = node.get("children", [])
        suffix = " (empty)" if not children else ""
        print(f"{prefix}{rule}{suffix}")
        for _field, child in children:
            _print_tree(child, indent + 1)
    elif kind == "token":
        name = node.get("name", "?")
        lexeme = node.get("lexeme", "?")
        source = node.get("source", {})
        loc = location_str(source)
        print(f"{prefix}{name} '{lexeme}' [{loc}]")
    elif kind == "error":
        source = node.get("source", {})
        loc = location_str(source)
        message = node.get("message", "unknown error")
        print(f"{prefix}{loc}: error: {message}")


def _print_parse_step(record):
    depth = record.get("depth", 0)
    indent = "  " * depth
    event = record.get("event", "?")
    if event == "predict":
        sym = record.get("sym", "?")
        lookahead = record.get("lookahead", "?")
        production = record.get("production")
        if production is None:
            print(f"{indent}{'predict':<9}{sym}  lookahead={lookahead} → (iteration)", flush=True)
        else:
            print(f"{indent}{'predict':<9}{sym}  lookahead={lookahead} → {production}", flush=True)
    elif event == "shift":
        name = record.get("name", "?")
        lexeme = record.get("lexeme", "?")
        source = record.get("source", {})
        loc = location_str(source)
        loc_str = f" [{loc}]" if loc else ""
        print(f"{indent}{'shift':<9}{name} '{lexeme}'{loc_str}", flush=True)
    elif event == "complete":
        rule = record.get("rule", "?")
        print(f"{indent}{'complete':<9}{rule}", flush=True)
```

- [ ] **Step 4: Run parse tests to verify they pass**

```
bin/test/units.bash src/plcc/cmd/parse_test.py -v
```

Expected: all parse tests pass

- [ ] **Step 5: Commit**

```bash
git -C /workspaces/plcc-ng/.worktrees/issue-067 add src/plcc/cmd/parse.py src/plcc/cmd/parse_test.py
git -C /workspaces/plcc-ng/.worktrees/issue-067 commit -m "$(cat <<'EOF'
feat(parse): print version first, add --no-banner, split banner output

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: Update rep.py — version first, --no-banner, pass --no-banner to make

**Files:**
- Modify: `src/plcc/cmd/rep.py`
- Modify: `src/plcc/cmd/rep_test.py`

- [ ] **Step 1: Write failing tests**

Add these tests to the bottom of `src/plcc/cmd/rep_test.py`:

```python
def test_rep_main_version_line_appears_even_when_make_fails(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "grammar.plcc").write_text("")
    monkeypatch.setattr(
        "subprocess.run",
        lambda *a, **kw: _MagicMock(returncode=1, stderr=b""),
    )
    monkeypatch.setattr("plcc.cmd.rep.get_version", lambda: "1.2.3")
    with pytest.raises(SystemExit):
        _rep_module.main([])
    out, _ = capsys.readouterr()
    assert "plcc-ng 1.2.3" in out


def test_rep_main_no_banner_suppresses_version_line(monkeypatch, tmp_path, capsys):
    _setup_rep_main(monkeypatch, tmp_path)
    _rep_module.main(["--tool=calc", "--no-banner"])
    out, _ = capsys.readouterr()
    assert "plcc-ng" not in out


def test_rep_main_no_banner_suppresses_grammar_line(monkeypatch, tmp_path, capsys):
    _setup_rep_main(monkeypatch, tmp_path)
    _rep_module.main(["--tool=calc", "--no-banner"])
    out, _ = capsys.readouterr()
    assert "grammar:" not in out


def test_rep_main_no_banner_suppresses_running_line(monkeypatch, tmp_path, capsys):
    _setup_rep_main(monkeypatch, tmp_path)
    _rep_module.main(["--tool=calc", "--no-banner"])
    out, _ = capsys.readouterr()
    assert "Running" not in out


def test_rep_main_make_call_includes_no_banner(monkeypatch, tmp_path):
    _setup_rep_main(monkeypatch, tmp_path)
    calls = []
    def capturing_run(cmd, **kw):
        calls.append(list(cmd))
        return _MagicMock(returncode=0, stderr=b"")
    monkeypatch.setattr("subprocess.run", capturing_run)
    _rep_module.main(["--tool=calc"])
    make_calls = [c for c in calls if c and c[0] == "plcc-make"]
    assert make_calls, "plcc-make was not called"
    assert any("--no-banner" in c for c in make_calls)
```

- [ ] **Step 2: Run tests to verify they fail**

```
bin/test/units.bash src/plcc/cmd/rep_test.py -v 2>&1 | tail -10
```

Expected: FAIL — `ImportError: cannot import name 'print_startup_banner'` in rep.py

- [ ] **Step 3: Update rep.py**

Replace `src/plcc/cmd/rep.py` with:

```python
import enum
import json
import os
import subprocess
import sys

from docopt import docopt, DocoptExit

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS
from plcc.version import get_version
from plcc.build.grammar import read_grammar
from .pipeline import TreePipeline, print_parse_error
from .output import print_version_line, print_grammar_line, print_user_error
from .source_runner import SourceRunner, SubmitOn

__doc__ = """plcc-rep
    REPL — read, eval, print loop for a PLCC grammar.

Usage:
    plcc-rep [-v ...] [options] [SOURCE ...]

Arguments:
    SOURCE      Source files to evaluate before entering interactive mode.

Options:
    -g <path> --grammar=<path>
                            Grammar to build from. Once set, remembered for subsequent
                            commands until changed. Defaults to grammar.plcc on first use.
    --tool=NAME             Semantic section to run (inferred if only one exists).
    --no-banner             Suppress the version and grammar banner.
    -h --help               Show this message.
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


class RepHandler:
    def __init__(self, spec_path, ll1_path, interpreter, verbose_format,
                 child_flags=None, verbose=None):
        self._pipeline = TreePipeline(spec_path, ll1_path, child_flags, verbose=verbose)
        self._interpreter = interpreter
        self._verbose_format = verbose_format

    def feed(self, content, source, eof=False):
        items = self._pipeline.run(content, eof)
        if items is None:
            return False
        for record, raw in items:
            if record.get("kind") == "error":
                print_parse_error(record, default_stage="plcc-rep")
                break
            elif record.get("kind") == "tree":
                try:
                    self._interpreter.stdin.write(raw + b'\n')
                    self._interpreter.stdin.flush()
                except BrokenPipeError:
                    print('plcc-rep: interpreter exited unexpectedly', file=sys.stderr)
                    sys.exit(1)
                _read_response(self._interpreter.stdout, self._interpreter, self._verbose_format)
        return True


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    if "--no-banner" not in argv:
        print_version_line(get_version())
    try:
        args = docopt(__doc__, argv)
    except DocoptExit as e:
        print(str(e), file=sys.stderr)
        print(file=sys.stderr)
        print("Run 'plcc-rep --help' for more information.", file=sys.stderr)
        sys.exit(1)
    no_banner = args["--no-banner"]
    verbose = VerboseContext.from_args("plcc-rep", Events, args)
    grammar_file = args['--grammar']
    sources = args['SOURCE']
    tool_name = args['--tool']
    verbose_format = args['--verbose-format'] or 'text'

    if grammar_file is not None and not os.path.exists(grammar_file):
        print(f"plcc-rep: grammar file not found: {grammar_file}", file=sys.stderr)
        print(file=sys.stderr)
        print("Run 'plcc-rep --help' for more information.", file=sys.stderr)
        sys.exit(1)

    verbose.emit(Events.STARTED, message='starting')
    child_flags = verbose.child_flags_for_orchestrator(min_level=0)

    make_result = subprocess.run(
        ['plcc-make', '--no-banner']
        + ([f'--grammar={grammar_file}'] if grammar_file is not None else [])
        + child_flags,
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
    if not no_banner:
        print_grammar_line(
            os.path.abspath(read_grammar('build')),
            tool=tool_name,
            language=language,
        )
    tool_dir = os.path.join('build', tool_name)

    interpreter = subprocess.Popen(
        ['plcc-lang-run', f'--target={language}', f'--output={tool_dir}'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=None,
    )

    completed = True
    try:
        handler = RepHandler(
            spec_path=spec_path,
            ll1_path=ll1_path,
            interpreter=interpreter,
            verbose_format=verbose_format,
            child_flags=child_flags,
            verbose=verbose,
        )
        runner = SourceRunner(submit_on=SubmitOn.EOF)
        completed = runner.run(sources, handler)
    finally:
        try:
            interpreter.stdin.close()
        except BrokenPipeError:
            pass
        interpreter.wait()

    if not completed:
        sys.exit(1)
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


def _read_response(stdout, interpreter, verbose_format):
    while True:
        raw = stdout.readline()
        if not raw:
            rc = interpreter.poll()
            if rc is not None and (rc < 0 or rc == 130):
                sys.exit(130)
            print('plcc-rep: interpreter exited unexpectedly', file=sys.stderr)
            sys.exit(1)
        line = raw.decode('utf-8', errors='replace').rstrip('\n')
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            print(line)
            continue
        if not isinstance(record, dict) or 'kind' not in record:
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
        print_user_error(f"error: {record.get('type')}: {record.get('message')}")
```

- [ ] **Step 4: Run rep tests to verify they pass**

```
bin/test/units.bash src/plcc/cmd/rep_test.py -v
```

Expected: all rep tests pass

- [ ] **Step 5: Run full unit suite — should now be fully green**

```
bin/test/units.bash
```

Expected: all 955+ tests pass (scan, parse, rep, output all updated)

- [ ] **Step 6: Commit**

```bash
git -C /workspaces/plcc-ng/.worktrees/issue-067 add src/plcc/cmd/rep.py src/plcc/cmd/rep_test.py
git -C /workspaces/plcc-ng/.worktrees/issue-067 commit -m "$(cat <<'EOF'
feat(rep): print version first, add --no-banner, split banner output

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

### Task 5: Update diagram.py — add banner, --no-banner, pass --no-banner to make

**Files:**
- Modify: `src/plcc/cmd/diagram.py`
- Modify: `src/plcc/cmd/diagram_test.py`

- [ ] **Step 1: Write failing tests**

Add these tests to the bottom of `src/plcc/cmd/diagram_test.py`:

```python
def test_diagram_main_version_line_appears_even_when_make_fails(tmp_path, monkeypatch, capsys):
    grammar = tmp_path / "grammar.plcc"
    grammar.write_text("# stub")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("plcc.cmd.diagram.get_version", lambda: "1.2.3")

    def fake_run(cmd, **kwargs):
        m = MagicMock()
        m.returncode = 1
        m.stderr = b''
        return m

    with patch('subprocess.run', side_effect=fake_run):
        with pytest.raises(SystemExit):
            run_main([])

    out, _ = capsys.readouterr()
    assert "plcc-ng 1.2.3" in out


def test_diagram_main_no_banner_suppresses_version_line(tmp_path, monkeypatch, capsys):
    grammar = tmp_path / "grammar.plcc"
    grammar.write_text("# stub")
    build_dir = tmp_path / 'build'
    build_dir.mkdir()
    (build_dir / 'model.json').write_text('{}')
    (build_dir / '.grammar').write_text(str(grammar))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("plcc.cmd.diagram.get_version", lambda: "1.2.3")

    def fake_run(cmd, **kwargs):
        m = MagicMock()
        m.returncode = 0
        m.stderr = b''
        return m

    with patch('subprocess.run', side_effect=fake_run):
        run_main(["--no-banner"])

    out, _ = capsys.readouterr()
    assert "plcc-ng" not in out


def test_diagram_main_no_banner_suppresses_grammar_line(tmp_path, monkeypatch, capsys):
    grammar = tmp_path / "grammar.plcc"
    grammar.write_text("# stub")
    build_dir = tmp_path / 'build'
    build_dir.mkdir()
    (build_dir / 'model.json').write_text('{}')
    (build_dir / '.grammar').write_text(str(grammar))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("plcc.cmd.diagram.get_version", lambda: "1.2.3")

    def fake_run(cmd, **kwargs):
        m = MagicMock()
        m.returncode = 0
        m.stderr = b''
        return m

    with patch('subprocess.run', side_effect=fake_run):
        run_main(["--no-banner"])

    out, _ = capsys.readouterr()
    assert "grammar:" not in out


def test_diagram_main_make_call_includes_no_banner(tmp_path, monkeypatch):
    grammar = tmp_path / "grammar.plcc"
    grammar.write_text("# stub")
    build_dir = tmp_path / 'build'
    build_dir.mkdir()
    (build_dir / 'model.json').write_text('{}')
    (build_dir / '.grammar').write_text(str(grammar))
    monkeypatch.chdir(tmp_path)
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(list(cmd))
        m = MagicMock()
        m.returncode = 0
        m.stderr = b''
        return m

    with patch('subprocess.run', side_effect=fake_run):
        run_main([])

    make_calls = [c for c in calls if c and c[0] == 'plcc-make']
    assert make_calls, "plcc-make was not called"
    assert any('--no-banner' in c for c in make_calls)
```

Also update the existing `test_calls_emit_build_run_after_make` test to add `build/.grammar` (required now that diagram reads it for the grammar line). Find this test and add one line:

```python
def test_calls_emit_build_run_after_make(tmp_path, monkeypatch):
    grammar = tmp_path / "grammar.plcc"
    grammar.write_text("# stub")
    build_dir = tmp_path / 'build'
    build_dir.mkdir()
    (build_dir / 'model.json').write_text('{}')
    (build_dir / '.grammar').write_text(str(grammar))   # ADD THIS LINE
    monkeypatch.chdir(tmp_path)
    # ... rest unchanged
```

- [ ] **Step 2: Run tests to verify they fail**

```
bin/test/units.bash src/plcc/cmd/diagram_test.py -v
```

Expected: new tests FAIL — `AttributeError: module 'plcc.cmd.diagram' has no attribute 'get_version'`; `test_calls_emit_build_run_after_make` may also fail with a read_grammar error

- [ ] **Step 3: Update diagram.py**

Replace `src/plcc/cmd/diagram.py` with:

```python
import enum
import os
import subprocess
import sys

from docopt import docopt, DocoptExit

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS
from plcc.version import get_version
from plcc.build.grammar import read_grammar
from .output import print_version_line, print_grammar_line

__doc__ = """plcc-diagram
    Generate and display a class diagram from a PLCC grammar file.

Usage:
    plcc-diagram [-v ...] [options]

Options:
    -g <path> --grammar=<path>
                            Grammar to build from. Once set, remembered for subsequent
                            commands until changed. Defaults to grammar.plcc on first use.
    --format=FMT            Diagram format [default: plantuml].
    --no-banner             Suppress the version and grammar banner.
    -h --help               Show this message.
""" + VERBOSE_OPTIONS


_SOURCE_EXT = {'mermaid': 'mmd', 'plantuml': 'puml'}


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    if "--no-banner" not in argv:
        print_version_line(get_version())
    try:
        args = docopt(__doc__, argv)
    except DocoptExit as e:
        print(str(e), file=sys.stderr)
        print(file=sys.stderr)
        print("Run 'plcc-diagram --help' for more information.", file=sys.stderr)
        sys.exit(1)

    no_banner = args["--no-banner"]
    verbose = VerboseContext.from_args("plcc-diagram", Events, args)
    grammar_file = args['--grammar']
    fmt = args['--format']

    if grammar_file is not None and not os.path.exists(grammar_file):
        print(f"plcc-diagram: grammar file not found: {grammar_file}", file=sys.stderr)
        print(file=sys.stderr)
        print("Run 'plcc-diagram --help' for more information.", file=sys.stderr)
        sys.exit(1)

    verbose.emit(Events.STARTED, message="generating diagram")
    child_flags = verbose.child_flags()

    make_result = subprocess.run(
        ['plcc-make', '--through=model', '--no-banner']
        + ([f'--grammar={grammar_file}'] if grammar_file is not None else [])
        + child_flags,
        stderr=subprocess.PIPE,
    )
    if make_result.stderr:
        sys.stderr.buffer.write(make_result.stderr)
    if make_result.returncode != 0:
        sys.exit(make_result.returncode)

    if not no_banner:
        print_grammar_line(os.path.abspath(read_grammar('build')))

    source_ext = _SOURCE_EXT.get(fmt, fmt)
    build_diagram_dir = os.path.join('build', 'diagram')
    os.makedirs(build_diagram_dir, exist_ok=True)
    diagram_source = os.path.join(build_diagram_dir, f'diagram.{source_ext}')
    diagram_image = os.path.join(build_diagram_dir, 'diagram.png')
    model_json = os.path.join('build', 'model.json')

    with open(model_json) as stdin_f, open(diagram_source, 'w') as stdout_f:
        emit_result = subprocess.run(
            ['plcc-diagram-emit', f'--format={fmt}'] + child_flags,
            stdin=stdin_f, stdout=stdout_f, stderr=subprocess.PIPE,
        )
    if emit_result.stderr:
        sys.stderr.buffer.write(emit_result.stderr)
    if emit_result.returncode != 0:
        sys.exit(emit_result.returncode)

    build_result = subprocess.run(
        ['plcc-diagram-build', f'--format={fmt}',
         f'--input={diagram_source}',
         f'--output={diagram_image}'] + child_flags,
        stderr=subprocess.PIPE,
    )
    if build_result.stderr:
        sys.stderr.buffer.write(build_result.stderr)
    if build_result.returncode != 0:
        sys.exit(build_result.returncode)

    run_result = subprocess.run(
        ['plcc-diagram-run', f'--format={fmt}', f'--input={diagram_image}'] + child_flags,
        stderr=subprocess.PIPE,
    )
    if run_result.stderr:
        sys.stderr.buffer.write(run_result.stderr)
    if run_result.returncode != 0:
        sys.exit(run_result.returncode)

    verbose.emit(Events.FINISHED, message="done")
```

- [ ] **Step 4: Run diagram tests to verify they pass**

```
bin/test/units.bash src/plcc/cmd/diagram_test.py -v
```

Expected: all diagram tests pass

- [ ] **Step 5: Commit**

```bash
git -C /workspaces/plcc-ng/.worktrees/issue-067 add src/plcc/cmd/diagram.py src/plcc/cmd/diagram_test.py
git -C /workspaces/plcc-ng/.worktrees/issue-067 commit -m "$(cat <<'EOF'
feat(diagram): add banner, --no-banner, pass --no-banner to make

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

### Task 6: Update make.py — add banner, --no-banner

**Files:**
- Modify: `src/plcc/cmd/make.py`
- Modify: `src/plcc/cmd/make_test.py`

- [ ] **Step 1: Write failing tests**

Add these tests to the bottom of `src/plcc/cmd/make_test.py`:

```python
def test_make_main_version_line_appears_before_grammar_error(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("plcc.cmd.make.get_version", lambda: "1.2.3")
    with pytest.raises(SystemExit):
        run_main([])  # no grammar.plcc — fails early
    out, _ = capsys.readouterr()
    assert "plcc-ng 1.2.3" in out


def test_make_main_no_banner_suppresses_version_line(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("plcc.cmd.make.get_version", lambda: "1.2.3")
    with pytest.raises(SystemExit):
        run_main(["--no-banner"])  # no grammar.plcc — fails, but no version
    out, _ = capsys.readouterr()
    assert "plcc-ng" not in out


def test_make_main_grammar_line_appears_after_grammar_resolved(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    grammar = tmp_path / "grammar.plcc"
    grammar.write_text("")
    monkeypatch.setattr("subprocess.run",
                        lambda *a, **kw: SimpleNamespace(returncode=1, stderr=b""))
    monkeypatch.setattr("plcc.cmd.make.get_version", lambda: "1.2.3")
    with pytest.raises(SystemExit):
        run_main([])
    out, _ = capsys.readouterr()
    assert "grammar:" in out
    assert str(grammar) in out


def test_make_main_no_banner_suppresses_grammar_line(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    grammar = tmp_path / "grammar.plcc"
    grammar.write_text("")
    monkeypatch.setattr("subprocess.run",
                        lambda *a, **kw: SimpleNamespace(returncode=1, stderr=b""))
    monkeypatch.setattr("plcc.cmd.make.get_version", lambda: "1.2.3")
    with pytest.raises(SystemExit):
        run_main(["--no-banner"])
    out, _ = capsys.readouterr()
    assert "grammar:" not in out
```

`make_test.py` does not currently import `SimpleNamespace`. Add it at the top of `make_test.py`:

```python
from types import SimpleNamespace
```

- [ ] **Step 2: Run tests to verify they fail**

```
bin/test/units.bash src/plcc/cmd/make_test.py::test_make_main_version_line_appears_before_grammar_error -v
```

Expected: FAIL — `AttributeError: module 'plcc.cmd.make' has no attribute 'get_version'`

- [ ] **Step 3: Update make.py**

Add these imports near the top of `src/plcc/cmd/make.py` (after the existing imports):

```python
from plcc.version import get_version
from .output import print_version_line, print_grammar_line
```

Add `--no-banner` to the docopt string in `__doc__`:

```python
__doc__ = """plcc-make
    Build a PLCC project from a grammar file.

Usage:
    plcc-make [-v ...] [options]

Options:
    -g <path> --grammar=<path>
                            Grammar to build from. Once set, remembered for subsequent
                            commands until changed. Defaults to grammar.plcc on first use.
    --through=<level>       Build up to this level: scan, parse, model, or all [default: all].
    --no-banner             Suppress the version and grammar banner.
    -h --help               Show this message.
""" + VERBOSE_OPTIONS
```

In `main()`, add the version line as the very first output (before `docopt`), and the grammar line after grammar is validated. The diff to `main()`:

```python
def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    if "--no-banner" not in argv:          # ADD
        print_version_line(get_version())  # ADD
    try:
        args = docopt(__doc__, argv)
    except DocoptExit as e:
        ...

    no_banner = args["--no-banner"]        # ADD
    verbose = VerboseContext.from_args("plcc-make", Events, args)
    explicit_grammar = args['--grammar']
    through = args['--through']
    build_dir = Path('build')

    stored_grammar = read_grammar(build_dir) if build_dir.is_dir() else None

    if explicit_grammar is not None:
        grammar = explicit_grammar
    elif stored_grammar is not None:
        grammar = stored_grammar
    else:
        grammar = 'grammar.plcc'

    if through not in ('scan', 'parse', 'model', 'all'):
        print(...)
        sys.exit(1)

    if explicit_grammar is None and stored_grammar is not None and not os.path.exists(grammar):
        print(...)
        sys.exit(1)

    if not os.path.exists(grammar):
        print(...)
        sys.exit(1)

    # grammar is resolved and exists here
    if not no_banner:                                          # ADD
        print_grammar_line(os.path.abspath(grammar))          # ADD

    if (...):   # existing shutil.rmtree block
        ...

    verbose.emit(Events.STARTED, message=f"grammar: {grammar}")
    ...
```

The full updated `main()` function (only showing modified regions — leave everything else unchanged):

At the very start of `main()`, before the `try: args = docopt(...)` block:
```python
    if "--no-banner" not in argv:
        print_version_line(get_version())
```

After `try/except DocoptExit`, add:
```python
    no_banner = args["--no-banner"]
```

After the second `if not os.path.exists(grammar): sys.exit(1)` block and before the `if (explicit_grammar is not None and stored_grammar is not None ...)` block:
```python
    if not no_banner:
        print_grammar_line(os.path.abspath(grammar))
```

- [ ] **Step 4: Run make tests to verify they pass**

```
bin/test/units.bash src/plcc/cmd/make_test.py -v
```

Expected: all make tests pass

- [ ] **Step 5: Run full unit suite**

```
bin/test/units.bash
```

Expected: all tests pass

- [ ] **Step 6: Commit**

```bash
git -C /workspaces/plcc-ng/.worktrees/issue-067 add src/plcc/cmd/make.py src/plcc/cmd/make_test.py
git -C /workspaces/plcc-ng/.worktrees/issue-067 commit -m "$(cat <<'EOF'
feat(make): add version banner and --no-banner flag

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

### Task 7: Final check and run commands tests

- [ ] **Step 1: Run the full unit suite one final time**

```
bin/test/units.bash
```

Expected: all tests pass, 0 failures

- [ ] **Step 2: Run commands tests (black-box CLI tier)**

```
bin/test/commands.bash
```

Expected: pass (or note any pre-existing failures unrelated to this change)

- [ ] **Step 3: Confirm no print_startup_banner references remain**

```
grep -r "print_startup_banner" /workspaces/plcc-ng/src/
```

Expected: no output (all callers migrated)
