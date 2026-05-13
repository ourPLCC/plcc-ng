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
