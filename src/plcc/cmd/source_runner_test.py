import io
import sys
from types import SimpleNamespace

import pytest

from .source_runner import SourceRunner, SubmitOn, _InteractiveState

HINT = "Enter input. Press ^D (EOF) when done."


class RecordingHandler:
    """Captures feed() calls for assertions."""
    def __init__(self, results=None):
        # results: iterator of booleans to return from feed(); defaults to all True
        self._results = iter(results or [])
        self.calls = []  # list of (content, source)
        self.eof_flags = []  # parallel list of eof values

    def feed(self, content, source, eof=False):
        self.calls.append((content, source))
        self.eof_flags.append(eof)
        try:
            return next(self._results)
        except StopIteration:
            return True


@pytest.fixture()
def runner():
    return SourceRunner(submit_on=SubmitOn.EOL)


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
    """Fake TTY stdin yielding lines from a list; empty bytes signals EOF."""
    buf = io.BytesIO(b"".join(l if isinstance(l, bytes) else l.encode() for l in lines))
    return SimpleNamespace(isatty=lambda: True, buffer=buf)


def _read1_tty(reads):
    """Fake TTY stdin that honors the n argument of read1().

    Non-empty entries in `reads` are concatenated into a single buffer;
    a b'' entry marks the end of input (subsequent read1() calls return b'').
    Each read1(n) call returns at most n bytes, allowing tests to exercise
    the boundary behavior of large reads.
    """
    data = b"".join(r for r in reads if r)
    view = memoryview(data)
    pos = [0]
    eof = len(data)

    class _Buf:
        def read1(self, n):
            start = pos[0]
            if start >= eof:
                return b""
            end = min(start + n, eof)
            pos[0] = end
            return bytes(view[start:end])

        def readline(self):
            raise AssertionError("readline() called in EOF mode")

    return SimpleNamespace(isatty=lambda: True, buffer=_Buf())


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


def test_blank_line_during_continuation_submits_buffer_with_newline(monkeypatch, runner):
    # line1 returns False (continuation), blank line submits buffer + blank line
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"line1\n", b"\n", b""]))
    handler = RecordingHandler(results=[False, True])
    runner.run(["-"], handler)
    assert handler.calls[1][0] == b"line1\n\n"


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


# --- Return value ---

def test_run_returns_true_when_all_feeds_succeed(tmp_path, runner):
    f = tmp_path / "f.txt"
    f.write_bytes(b"ok")
    handler = RecordingHandler(results=[True])
    assert runner.run([str(f)], handler) is True


def test_run_returns_false_when_file_feed_returns_false(tmp_path, runner):
    f = tmp_path / "f.txt"
    f.write_bytes(b"partial")
    handler = RecordingHandler(results=[False])
    assert runner.run([str(f)], handler) is False


def test_run_returns_false_when_non_tty_stdin_feed_returns_false(monkeypatch, runner):
    monkeypatch.setattr(sys, "stdin", SimpleNamespace(
        isatty=lambda: False,
        buffer=io.BytesIO(b"partial"),
    ))
    handler = RecordingHandler(results=[False])
    assert runner.run(["-"], handler) is False


def test_run_returns_true_for_interactive_even_if_feed_returns_false(monkeypatch, runner):
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"partial\n", b""]))
    handler = RecordingHandler(results=[False])
    assert runner.run(["-"], handler) is True


def test_ctrl_c_with_empty_buffer_exits_130(monkeypatch, runner):
    class ImmediateInterrupt:
        isatty = lambda self: True

        @property
        def buffer(self):
            return self

        def readline(self):
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

        def readline(self):
            self._calls += 1
            if self._calls == 1:
                return b"partial\n"   # builds the buffer
            if self._calls == 2:
                raise KeyboardInterrupt  # ^C with non-empty buffer
            if self._calls == 3:
                return b"hello\n"
            return b""

    monkeypatch.setattr(sys, "stdin", InterruptAfterLine())
    handler = RecordingHandler(results=[False, True])
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


def test_interactive_state_pending_exit_defaults_false():
    state = _InteractiveState(buffer=b"", prompt=">>> ")
    assert state.pending_exit is False


def test_interactive_state_pending_exit_can_be_set():
    state = _InteractiveState(buffer=b"", prompt=">>> ", pending_exit=True)
    assert state.pending_exit is True


# --- Predicate methods ---

def test_is_eof_true_for_empty_bytes(runner):
    assert runner._is_eof(b"") is True


def test_is_eof_false_for_nonempty(runner):
    assert runner._is_eof(b"hello\n") is False


def test_is_partial_eof_true_for_line_without_newline(runner):
    assert runner._is_partial_eof(b"partial") is True


def test_is_partial_eof_false_for_line_with_newline(runner):
    assert runner._is_partial_eof(b"complete\n") is False


def test_is_blank_true_for_newline_only(runner):
    assert runner._is_blank(b"\n") is True


def test_is_blank_false_for_whitespace_only_line(runner):
    assert runner._is_blank(b"  \n") is False


def test_is_blank_false_for_content_line(runner):
    assert runner._is_blank(b"hello\n") is False


def test_is_interrupted_true_for_none(runner):
    assert runner._is_interrupted(None) is True


def test_is_interrupted_false_for_bytes(runner):
    assert runner._is_interrupted(b"") is False


def test_ctrl_d_on_fresh_prompt_prints_newline(monkeypatch, runner, capsys):
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b""]))
    runner.run(["-"], RecordingHandler())
    _, err = capsys.readouterr()
    # Prompt is ">>> " (no newline); ^D should add one so the shell lands on a new line
    assert err.endswith(">>> \n")


def test_first_ctrl_d_on_empty_prompt_prints_warning(monkeypatch, runner, capsys):
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b""]))
    runner.run(["-"], RecordingHandler())
    _, err = capsys.readouterr()
    assert "(press ^D again to exit)" in err


def test_second_ctrl_d_on_empty_prompt_exits_without_feed(monkeypatch, runner):
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b""]))
    handler = RecordingHandler()
    runner.run(["-"], handler)
    assert handler.calls == []


def test_input_after_ctrl_d_warning_clears_pending_exit(monkeypatch, runner):
    # ^D warns; user types a line (clears pending_exit); next ^D warns again instead
    # of exiting immediately. The presence of the feed call proves the session continued.
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"", b"hello\n", b""]))
    handler = RecordingHandler(results=[True])
    runner.run(["-"], handler)
    assert len(handler.calls) == 1
    assert handler.calls[0][0] == b"hello\n"


def test_ctrl_d_in_continuation_submits_and_continues(monkeypatch, runner):
    # Setup: line1 fails (continuation), then ^D on empty "..." → should submit and
    # continue (not exit), then line2 succeeds, then final ^D exits.
    class EOFInContinuation:
        def __init__(self):
            self._calls = 0

        isatty = lambda self: True

        @property
        def buffer(self):
            return self

        def readline(self):
            self._calls += 1
            if self._calls == 1:
                return b"hello\n"      # returns False from handler
            if self._calls == 2:
                return b""             # ^D in continuation: should submit and continue
            if self._calls == 3:
                return b"world\n"      # returned after continuing
            return b""                 # final ^D exits

    monkeypatch.setattr(sys, "stdin", EOFInContinuation())
    handler = RecordingHandler(results=[False, True, True])
    runner.run(["-"], handler)
    # With fix: ^D in continuation submits buffer and loops — "world\n" is processed.
    # Without fix: ^D exits immediately after submitting — "world\n" is never read.
    assert len(handler.calls) == 3
    assert handler.calls[2][0] == b"world\n"


def test_ctrl_d_after_partial_text_force_submits(monkeypatch, runner):
    # "hello\n" fails → continuation.
    # "world" (no \n, simulates ^D after text) → should force-submit buffer+"world".
    # Without fix: "world" treated as normal line; evaluate fails; then ^D (020a fix)
    #   submits the same buffer again — 3 calls total.
    # With fix: "world" detected as partial-eof, force-submitted — 2 calls total.
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"hello\n", b"world", b""]))
    handler = RecordingHandler(results=[False, True])
    runner.run(["-"], handler)
    assert len(handler.calls) == 2
    assert handler.calls[1][0] == b"hello\nworld"


def test_blank_line_submission_resets_to_fresh_prompt_when_evaluate_succeeds(monkeypatch, runner, capsys):
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"hello\n", b"\n", b""]))
    handler = RecordingHandler(results=[False, True])
    runner.run(["-"], handler)
    _, err = capsys.readouterr()
    assert err.count(">>> ") >= 2


def test_blank_line_force_submit_exits_with_error_when_handler_rejects(monkeypatch, runner, capsys):
    # Force-submitting via blank line and getting False back is a PLCC internal error.
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"hello\n", b"\n"]))
    handler = RecordingHandler(results=[False, False])
    with pytest.raises(SystemExit) as exc_info:
        runner.run(["-"], handler)
    assert exc_info.value.code == 1
    _, err = capsys.readouterr()
    assert "PLCC internal error" in err


def test_ctrl_d_in_continuation_force_submit_exits_with_error_when_handler_rejects(monkeypatch, runner, capsys):
    # Force-submitting via ^D in continuation and getting False back is a PLCC internal error.
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"hello\n", b""]))
    handler = RecordingHandler(results=[False, False])
    with pytest.raises(SystemExit) as exc_info:
        runner.run(["-"], handler)
    assert exc_info.value.code == 1
    _, err = capsys.readouterr()
    assert "PLCC internal error" in err


def test_partial_eof_force_submit_exits_with_error_when_handler_rejects(monkeypatch, runner, capsys):
    # Force-submitting via ^D after partial text and getting False back is a PLCC internal error.
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"hello\n", b"world"]))
    handler = RecordingHandler(results=[False, False])
    with pytest.raises(SystemExit) as exc_info:
        runner.run(["-"], handler)
    assert exc_info.value.code == 1
    _, err = capsys.readouterr()
    assert "PLCC internal error" in err


# --- SubmitOn enum and EOF mode ---

def _eof_runner():
    return SourceRunner(submit_on=SubmitOn.EOF)


def test_submit_on_required():
    with pytest.raises(TypeError):
        SourceRunner()


def test_eol_mode_submits_after_each_line(monkeypatch):
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"line1\n", b""]))
    handler = RecordingHandler(results=[True])
    SourceRunner(submit_on=SubmitOn.EOL).run(["-"], handler)
    assert len(handler.calls) == 1
    assert handler.calls[0][0] == b"line1\n"


def test_eof_mode_regular_line_accumulates_without_feed(monkeypatch):
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b""]))
    handler = RecordingHandler()
    _eof_runner().run(["-"], handler)
    # ^D on empty buffer exits without calling feed
    assert handler.calls == []


def test_eof_mode_enter_accumulates_both_lines(monkeypatch):
    # Enter never calls feed; only ^D submits. Both lines must arrive in one call.
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"line1\n", b"line2\n", b""]))
    handler = RecordingHandler(results=[True])
    _eof_runner().run(["-"], handler)
    assert len(handler.calls) == 1
    assert handler.calls[0][0] == b"line1\nline2\n"


def test_eof_mode_ctrl_d_with_buffer_calls_feed(monkeypatch):
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"hello\n", b"world\n", b""]))
    handler = RecordingHandler(results=[True])
    _eof_runner().run(["-"], handler)
    assert len(handler.calls) == 1
    assert handler.calls[0][0] == b"hello\nworld\n"


def test_eof_mode_blank_line_accumulates_during_continuation(monkeypatch):
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"hello\n", b"\n", b""]))
    handler = RecordingHandler(results=[True])
    _eof_runner().run(["-"], handler)
    assert len(handler.calls) == 1
    assert handler.calls[0][0] == b"hello\n\n"


def test_eof_mode_enter_shows_continuation_prompt(monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"hello\n", b""]))
    handler = RecordingHandler(results=[True])
    _eof_runner().run(["-"], handler)
    _, err = capsys.readouterr()
    assert "... " in err


def test_eof_mode_partial_eof_force_submits_buffer_plus_partial(monkeypatch):
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"hello\n", b"world", b""]))
    handler = RecordingHandler(results=[True])
    _eof_runner().run(["-"], handler)
    assert len(handler.calls) == 1
    assert handler.calls[0][0] == b"hello\nworld"


def test_eof_mode_enter_then_ctrl_d_submits(monkeypatch):
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"hello\n", b""]))
    handler = RecordingHandler(results=[True])
    _eof_runner().run(["-"], handler)
    assert len(handler.calls) == 1
    assert handler.calls[0][0] == b"hello\n"


def test_eof_mode_ctrl_d_without_enter_submits_immediately(monkeypatch):
    # In EOF mode, typing content then pressing ^D (no Enter) must submit on the
    # FIRST ^D. In Unix canonical mode, ^D flushes typed bytes to the read buffer
    # without a newline. readline() would block waiting for \n or a second ^D;
    # read1() returns immediately with the flushed bytes.
    # Simulate: read1() returns b"42" (typed then ^D), then b"" (exit).
    buf = _read1_tty([b"42", b""])
    monkeypatch.setattr(sys, "stdin", buf)
    handler = RecordingHandler(results=[True])
    _eof_runner().run(["-"], handler)
    assert len(handler.calls) == 1
    assert handler.calls[0][0] == b"42"


def test_eof_mode_long_line_not_misclassified_as_partial_eof(monkeypatch):
    # A line longer than 4096 bytes must not be force-submitted as partial EOF.
    # Linux's MAX_CANON = 4096: read1(4096) would return the first 4096 bytes
    # without the trailing \n, which _is_partial_eof() would misidentify as ^D.
    # read1(65536) fits any canonical line in one call, so only a genuine ^D
    # (no \n) triggers the partial-EOF path.
    long_line = b"x" * 5000 + b"\n"
    buf = _read1_tty([long_line, b""])
    monkeypatch.setattr(sys, "stdin", buf)
    handler = RecordingHandler(results=[True])
    _eof_runner().run(["-"], handler)
    assert len(handler.calls) == 1
    assert handler.calls[0][0] == long_line


