import io
import sys
from types import SimpleNamespace

import pytest

from .source_runner import SourceRunner, _InteractiveState

HINT = "Enter input. Press ^D (EOF) when done."


class RecordingHandler:
    """Captures feed() calls for assertions. results: iterator of remainder bytes."""
    def __init__(self, results=None):
        self._results = iter(results or [])
        self.calls = []       # list of (content, source)
        self.eof_flags = []   # parallel list of eof values

    def feed(self, content, source, eof=False):
        self.calls.append((content, source))
        self.eof_flags.append(eof)
        try:
            return next(self._results)
        except StopIteration:
            return b""


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


def test_non_tty_stdin_passes_eof_true(monkeypatch, runner):
    monkeypatch.setattr(sys, "stdin", SimpleNamespace(
        isatty=lambda: False,
        buffer=io.BytesIO(b"content"),
    ))
    handler = RecordingHandler()
    runner.run(["-"], handler)
    assert handler.eof_flags == [True]


def test_file_source_passes_eof_true(tmp_path, runner):
    f = tmp_path / "hello.txt"
    f.write_bytes(b"hello")
    handler = RecordingHandler()
    runner.run([str(f)], handler)
    assert handler.eof_flags == [True]


# --- Interactive (TTY) stdin ---

def _tty_stdin(lines):
    """Simulate canonical TTY: each read1() call returns the next item from lines."""
    _iter = iter(lines)

    class _TtyBuffer:
        def read1(self, n=-1):
            try:
                return next(_iter)
            except StopIteration:
                return b""

    return SimpleNamespace(isatty=lambda: True, buffer=_TtyBuffer())


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


def test_interactive_remainder_becomes_next_buffer(monkeypatch, runner):
    # First line is held (remainder == the line); second line completes it.
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"a\n", b"b\n", b""]))
    handler = RecordingHandler(results=[b"a\n", b""])
    runner.run(["-"], handler)
    assert handler.calls[1][0] == b"a\nb\n"   # accumulated, fed again


def test_interactive_empty_remainder_resets_to_prompt(monkeypatch, runner, capsys):
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"line1\n", b""]))
    handler = RecordingHandler(results=[b""])
    runner.run(["-"], handler)
    _, err = capsys.readouterr()
    assert err.count(">>> ") >= 2


def test_interactive_nonempty_remainder_shows_continuation(monkeypatch, runner, capsys):
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"line1\n", b""]))
    handler = RecordingHandler(results=[b"line1\n"])
    runner.run(["-"], handler)
    _, err = capsys.readouterr()
    assert "... " in err


def test_ctrl_d_empty_buffer_exits_immediately(monkeypatch, runner):
    # Single ^D on the top-level prompt exits; feed is never called.
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b""]))
    handler = RecordingHandler()
    runner.run(["-"], handler)
    assert handler.calls == []


def test_ctrl_d_empty_buffer_prints_newline(monkeypatch, runner, capsys):
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b""]))
    runner.run(["-"], RecordingHandler())
    _, err = capsys.readouterr()
    assert err.endswith(">>> \n")


def test_ctrl_d_partial_line_at_top_level_prompt_force_submits(monkeypatch, runner):
    # 098 regression: at >>>, type "hello" then ^D (no Enter) — force-submit immediately.
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"hello", b""]))
    handler = RecordingHandler(results=[b""])
    runner.run(["-"], handler)
    assert handler.calls == [(b"hello", "-")]
    assert handler.eof_flags == [True]


def test_ctrl_d_nonempty_buffer_force_submits_and_returns_to_prompt(monkeypatch, runner, capsys):
    # line1 is held; ^D on the continuation prompt force-submits with eof=True.
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"line1\n", b""]))
    handler = RecordingHandler(results=[b"line1\n", b""])
    runner.run(["-"], handler)
    assert handler.eof_flags[-1] is True
    assert handler.calls[-1][0] == b"line1\n"


def test_partial_line_then_ctrl_d_force_submits_with_partial(monkeypatch, runner):
    # "world" arrives with no trailing newline (text then ^D).
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"hello\n", b"world", b""]))
    handler = RecordingHandler(results=[b"hello\n", b""])
    runner.run(["-"], handler)
    assert handler.calls[-1][0] == b"hello\nworld"
    assert handler.eof_flags[-1] is True


def test_interactive_eof_with_buffer_calls_feed(monkeypatch, runner):
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"partial\n", b""]))
    handler = RecordingHandler(results=[b"partial\n"])  # first call: hold
    runner.run(["-"], handler)
    # EOF with non-empty buffer: feed called with buffer
    assert any(b"partial" in c for c, _ in handler.calls)


def test_interactive_eof_with_empty_buffer_does_not_call_feed(monkeypatch, runner):
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b""]))  # immediate EOF
    handler = RecordingHandler()
    runner.run(["-"], handler)
    assert handler.calls == []


# --- ^C (KeyboardInterrupt) ---

def test_ctrl_c_with_empty_buffer_exits_130(monkeypatch, runner):
    class ImmediateInterrupt:
        isatty = lambda self: True

        @property
        def buffer(self):
            return self

        def read1(self, n=-1):
            raise KeyboardInterrupt

    monkeypatch.setattr(sys, "stdin", ImmediateInterrupt())
    with pytest.raises(SystemExit) as exc_info:
        runner.run(["-"], RecordingHandler())
    assert exc_info.value.code == 130


def test_ctrl_c_with_buffer_clears_and_continues(monkeypatch, runner, capsys):
    class InterruptAfterLine:
        def __init__(self):
            self._calls = 0

        isatty = lambda self: True

        @property
        def buffer(self):
            return self

        def read1(self, n=-1):
            self._calls += 1
            if self._calls == 1:
                return b"partial\n"   # builds the buffer
            if self._calls == 2:
                raise KeyboardInterrupt  # ^C with non-empty buffer
            if self._calls == 3:
                return b"hello\n"
            return b""

    monkeypatch.setattr(sys, "stdin", InterruptAfterLine())
    handler = RecordingHandler(results=[b"partial\n", b""])
    runner.run(["-"], handler)
    _, err = capsys.readouterr()
    assert "KeyboardInterrupt" in err
    # buffer was cleared by ^C; next feed sees only "hello\n"
    assert handler.calls[-1][0] == b"hello\n"


def test_ctrl_c_during_evaluation_exits_130(monkeypatch, runner):
    class InterruptingHandler:
        def feed(self, content, source, eof=False):
            raise KeyboardInterrupt

    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"hello\n", b""]))
    with pytest.raises(SystemExit) as exc_info:
        runner.run(["-"], InterruptingHandler())
    assert exc_info.value.code == 130


# --- _InteractiveState ---

def test_interactive_state_stores_buffer_and_prompt():
    state = _InteractiveState(buffer=b"hello", prompt=">>> ")
    assert state.buffer == b"hello"
    assert state.prompt == ">>> "
    assert state.done is False


def test_interactive_state_done_flag():
    state = _InteractiveState(buffer=b"", prompt=">>> ", done=True)
    assert state.done is True


def test_ctrl_d_on_fresh_prompt_prints_newline(monkeypatch, runner, capsys):
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b""]))
    runner.run(["-"], RecordingHandler())
    _, err = capsys.readouterr()
    # Prompt is ">>> " (no newline); ^D should add one so the shell lands on a new line
    assert err.endswith(">>> \n")


def test_ctrl_d_in_continuation_submits_and_continues(monkeypatch, runner):
    # Setup: line1 is held (continuation), then ^D on "..." → should force-submit and
    # continue (not exit), then line2 succeeds, then final ^D exits.
    class EOFInContinuation:
        def __init__(self):
            self._calls = 0

        isatty = lambda self: True

        @property
        def buffer(self):
            return self

        def read1(self, n=-1):
            self._calls += 1
            if self._calls == 1:
                return b"hello\n"      # held in buffer
            if self._calls == 2:
                return b""             # ^D in continuation: should force-submit and continue
            if self._calls == 3:
                return b"world\n"      # returned after continuing
            return b""                 # final ^D exits

    monkeypatch.setattr(sys, "stdin", EOFInContinuation())
    handler = RecordingHandler(results=[b"hello\n", b"", b""])
    runner.run(["-"], handler)
    # ^D in continuation force-submits buffer and loops — "world\n" is processed.
    assert len(handler.calls) == 3
    assert handler.calls[2][0] == b"world\n"


def test_blank_line_submission_resets_to_fresh_prompt_when_evaluate_succeeds(monkeypatch, runner, capsys):
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"hello\n", b"\n", b""]))
    handler = RecordingHandler(results=[b"hello\n", b""])
    runner.run(["-"], handler)
    _, err = capsys.readouterr()
    assert err.count(">>> ") >= 2
