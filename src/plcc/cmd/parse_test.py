import json
import subprocess
import sys
from types import SimpleNamespace

import pytest

from plcc.verbose import VerboseContext
from .parse import ParseHandler
import plcc.cmd.parse as _parse_module
from .parse import _render_trace
from ._test_helpers import (
    _proc, _tree_record, _error_record, _error_record_with_source,
    _eof_error_record, _parse_step_record, _shift_step_record, _complete_step_record,
)


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


def test_feed_prints_error_to_stdout(monkeypatch, handler, capsys):
    procs = iter([_proc(), _proc(stdout=_error_record("oops"))])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    handler.feed(b"bad\n", "-")
    out, _ = capsys.readouterr()
    assert "oops" in out


def test_feed_error_shows_location_in_stdout(monkeypatch, handler, capsys):
    procs = iter([_proc(), _proc(stdout=_error_record_with_source("bad char", file="-", line=1, col=1))])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    handler.feed(b"@\n", "-")
    out, _ = capsys.readouterr()
    assert "-:1:1" in out


def test_feed_error_renders_file_line_col(monkeypatch, handler, capsys):
    procs = iter([_proc(), _proc(stdout=_error_record_with_source("bad", file="foo.txt", line=3, col=7))])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    handler.feed(b"bad\n", "-")
    out, _ = capsys.readouterr()
    assert "foo.txt:3:7" in out
    assert "bad" in out


def test_feed_mixed_tree_and_error_renders_both(monkeypatch, handler, capsys):
    combined = _tree_record() + _error_record_with_source("trailing")
    procs = iter([_proc(), _proc(stdout=combined)])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    handler.feed(b"input\n", "-")
    out, _ = capsys.readouterr()
    assert "program" in out
    assert "trailing" in out
    assert handler.had_error is True


def test_feed_sets_had_error_on_error_record(monkeypatch, handler):
    procs = iter([_proc(), _proc(stdout=_error_record())])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    handler.feed(b"bad\n", "-")
    assert handler.had_error is True


def test_feed_does_not_set_had_error_on_success(monkeypatch, handler):
    procs = iter([_proc(), _proc(stdout=_tree_record())])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    handler.feed(b"ok\n", "-")
    assert handler.had_error is False


def test_feed_error_with_no_location_shows_stage(monkeypatch, handler, capsys):
    procs = iter([_proc(), _proc(stdout=_error_record("bad char", stage="plcc-tokens"))])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    handler.feed(b"@\n", "-")
    out, _ = capsys.readouterr()
    assert "plcc-tokens: error: bad char" in out


def test_feed_returns_false_for_eof_only_error_when_trial(monkeypatch, handler):
    procs = iter([_proc(), _proc(stdout=_eof_error_record())])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    assert handler.feed(b"1+\n", "-", eof=False) is False


def test_feed_returns_true_for_eof_only_error_when_force_submit(monkeypatch, handler):
    procs = iter([_proc(), _proc(stdout=_eof_error_record())])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    assert handler.feed(b"1+\n", "-", eof=True) is True


def test_feed_suppresses_output_for_eof_error_when_trial(monkeypatch, handler, capsys):
    procs = iter([_proc(), _proc(stdout=_eof_error_record("expected PLUS"))])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    handler.feed(b"1+\n", "-", eof=False)
    out, _ = capsys.readouterr()
    assert out == ""


def test_feed_shows_output_for_eof_error_when_force_submit(monkeypatch, handler, capsys):
    procs = iter([_proc(), _proc(stdout=_eof_error_record("expected PLUS"))])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    handler.feed(b"1+\n", "-", eof=True)
    out, _ = capsys.readouterr()
    assert "expected PLUS" in out


def test_feed_returns_true_for_genuine_error_regardless_of_eof_param(monkeypatch, handler):
    procs = iter([_proc(), _proc(stdout=_error_record("bad token"))])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    # _error_record has no "found" field → genuine error → always True
    assert handler.feed(b"@\n", "-", eof=False) is True


def test_feed_prints_empty_annotation_for_childless_tree(monkeypatch, handler, capsys):
    childless_tree = json.dumps({
        "kind": "tree", "rule": "exp2",
        "source": {}, "children": []
    }).encode() + b"\n"
    procs = iter([_proc(), _proc(stdout=childless_tree)])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    handler.feed(b"1\n", "-")
    out, _ = capsys.readouterr()
    assert "exp2 (empty)" in out


def test_feed_does_not_annotate_tree_with_children(monkeypatch, handler, capsys):
    token_child = {"kind": "token", "name": "NUM", "lexeme": "1",
                   "source": {"file": "-", "line": 1, "column": 1}}
    tree_with_child = json.dumps({
        "kind": "tree", "rule": "exp",
        "source": {}, "children": [["n", token_child]]
    }).encode() + b"\n"
    procs = iter([_proc(), _proc(stdout=tree_with_child)])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    handler.feed(b"1\n", "-")
    out, _ = capsys.readouterr()
    assert "exp (empty)" not in out
    assert "exp\n" in out or out.startswith("exp")


def test_feed_reformats_child_verbose_events(monkeypatch, capsys):
    verbose = VerboseContext("test", None, level=1, fmt="text")
    handler = ParseHandler(
        spec_path="build/spec.json",
        ll1_path="build/ll1.json",
        child_flags=[],
        verbose=verbose,
    )
    tokens_stderr = (
        b'{"stage": "plcc-tokens", "event": "started", "message": "tokenizing"}\n'
    )
    procs = iter([
        _proc(stderr=tokens_stderr),
        _proc(stdout=_tree_record(), stderr=b""),
    ])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    handler.feed(b"1\n", "-")
    _, err = capsys.readouterr()
    assert "plcc-tokens: started: tokenizing" in err


def test_feed_stops_at_first_error(monkeypatch, handler, capsys):
    # Two error records arrive (e.g. two lex errors from 'ab').
    # Only the first should be printed; the second is silently dropped.
    two_errors = (
        _error_record_with_source("first error", col=1) +
        _error_record_with_source("second error", col=2)
    )
    procs = iter([_proc(), _proc(stdout=two_errors)])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    handler.feed(b"ab\n", "-")
    out, _ = capsys.readouterr()
    assert "first error" in out
    assert "second error" not in out




def test_feed_prints_arbno_children(monkeypatch, handler, capsys):
    # Arbno fields carry a list of nodes: [field, [node, node, ...]].
    # _print_tree must iterate the list rather than calling .get() on it.
    arbno_tree = json.dumps({
        "kind": "tree", "rule": "prog", "source": {},
        "children": [["s", [
            {"kind": "tree", "rule": "stmt", "source": {}, "children": []},
            {"kind": "tree", "rule": "stmt", "source": {}, "children": []},
        ]]],
    }).encode() + b"\n"
    procs = iter([_proc(), _proc(stdout=arbno_tree)])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    handler.feed(b"a = 1 b = 2\n", "-")
    out, _ = capsys.readouterr()
    assert out.count("stmt") == 2


def _setup_parse_main(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "grammar.plcc").write_text("")
    build = tmp_path / "build"
    build.mkdir()
    (build / ".grammar").write_text(str(tmp_path / "grammar.plcc"))
    (build / "spec.json").write_text("{}")
    (build / "ll1.json").write_text("{}")
    monkeypatch.setattr("subprocess.run",
                        lambda *a, **kw: SimpleNamespace(returncode=0, stderr=b""))
    monkeypatch.setattr(_parse_module, "SourceRunner",
                        lambda **kw: type("R", (), {"run": lambda self, s, h: True})())
    monkeypatch.setattr("plcc.cmd.parse.get_version", lambda: "1.2.3")


def test_parse_main_banner_contains_version(monkeypatch, tmp_path, capsys):
    _setup_parse_main(monkeypatch, tmp_path)
    from .parse import main as parse_main
    parse_main([])
    out, _ = capsys.readouterr()
    assert "plcc-ng 1.2.3" in out


def test_parse_main_banner_contains_grammar_path(monkeypatch, tmp_path, capsys):
    _setup_parse_main(monkeypatch, tmp_path)
    from .parse import main as parse_main
    parse_main([])
    out, _ = capsys.readouterr()
    assert str(tmp_path / "grammar.plcc") in out


def test_parse_main_banner_goes_to_stdout(monkeypatch, tmp_path, capsys):
    _setup_parse_main(monkeypatch, tmp_path)
    from .parse import main as parse_main
    parse_main([])
    _, err = capsys.readouterr()
    assert "plcc-ng" not in err


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
    def capturing_run(cmd, **kw):
        calls.append(list(cmd))
        return SimpleNamespace(returncode=0, stderr=b"")
    monkeypatch.setattr("subprocess.run", capturing_run)
    from .parse import main as parse_main
    parse_main([])
    make_calls = [c for c in calls if c and c[0] == "plcc-make"]
    assert make_calls, "plcc-make was not called"
    assert any("--no-banner" in c for c in make_calls)


# --- _render_trace tests ---

def test_render_trace_empty_produces_no_output(capsys):
    _render_trace([])
    out, _ = capsys.readouterr()
    assert out == ""


def test_render_trace_single_rule_with_token(capsys):
    steps = [
        {"kind": "parse-step", "event": "predict", "sym": "program",
         "production": "program", "depth": 0},
        {"kind": "parse-step", "event": "shift", "name": "NUM", "lexeme": "42",
         "source": {"file": "-", "line": 1, "column": 1}, "depth": 1},
        {"kind": "parse-step", "event": "complete", "rule": "program", "depth": 0},
    ]
    _render_trace(steps)
    out, _ = capsys.readouterr()
    lines = out.splitlines()
    assert lines[0] == "program"
    assert lines[1] == "  NUM '42' [-:1:1]"


def test_render_trace_empty_rule_shows_empty_annotation(capsys):
    steps = [
        {"kind": "parse-step", "event": "predict", "sym": "NilRest",
         "production": "NilRest", "depth": 2},
        {"kind": "parse-step", "event": "complete", "rule": "NilRest", "depth": 2},
    ]
    _render_trace(steps)
    out, _ = capsys.readouterr()
    assert out.splitlines()[0] == "    NilRest (empty)"


def test_render_trace_nested_rules_indented_correctly(capsys):
    steps = [
        {"kind": "parse-step", "event": "predict", "sym": "program",
         "production": "program", "depth": 0},
        {"kind": "parse-step", "event": "predict", "sym": "expr",
         "production": "expr", "depth": 1},
        {"kind": "parse-step", "event": "shift", "name": "NUM", "lexeme": "1",
         "source": {"file": "-", "line": 1, "column": 1}, "depth": 2},
        {"kind": "parse-step", "event": "complete", "rule": "expr", "depth": 1},
        {"kind": "parse-step", "event": "complete", "rule": "program", "depth": 0},
    ]
    _render_trace(steps)
    out, _ = capsys.readouterr()
    lines = out.splitlines()
    assert lines[0] == "program"
    assert lines[1] == "  expr"
    assert lines[2] == "    NUM '1' [-:1:1]"


def test_render_trace_incomplete_rules_flushed_at_error(capsys):
    # Error occurred: no shift, no complete events
    steps = [
        {"kind": "parse-step", "event": "predict", "sym": "program",
         "production": "program", "depth": 0},
        {"kind": "parse-step", "event": "predict", "sym": "expr",
         "production": "expr", "depth": 1},
    ]
    _render_trace(steps)
    out, _ = capsys.readouterr()
    lines = out.splitlines()
    assert lines[0] == "program"
    assert lines[1] == "  expr"
    assert "(empty)" not in out


def test_render_trace_uses_production_name_not_sym(capsys):
    # When a rule has an alternative, production holds the class name
    steps = [
        {"kind": "parse-step", "event": "predict", "sym": "exprRest",
         "production": "AddRest", "depth": 0},
        {"kind": "parse-step", "event": "shift", "name": "PLUS", "lexeme": "+",
         "source": {"file": "-", "line": 1, "column": 3}, "depth": 1},
        {"kind": "parse-step", "event": "complete", "rule": "AddRest", "depth": 0},
    ]
    _render_trace(steps)
    out, _ = capsys.readouterr()
    assert out.splitlines()[0] == "AddRest"
    assert "exprRest" not in out


def test_render_trace_token_location_uses_bracket_format(capsys):
    steps = [
        {"kind": "parse-step", "event": "predict", "sym": "program",
         "production": "program", "depth": 0},
        {"kind": "parse-step", "event": "shift", "name": "NUM", "lexeme": "99",
         "source": {"file": "foo.txt", "line": 3, "column": 7}, "depth": 1},
        {"kind": "parse-step", "event": "complete", "rule": "program", "depth": 0},
    ]
    _render_trace(steps)
    out, _ = capsys.readouterr()
    assert "NUM '99' [foo.txt:3:7]" in out


def test_render_trace_arbno_predict_does_not_corrupt_stack(capsys):
    # ARBNO predict events have production=None and no matching complete in the
    # raw parser output. After the fix to _parse_arbno, each iteration emits a
    # complete event, so the stack stays balanced. This test verifies that given
    # balanced ARBNO events the output is correct and "program" is not duplicated.
    steps = [
        {"kind": "parse-step", "event": "predict", "sym": "program",
         "production": "program", "depth": 0},
        {"kind": "parse-step", "event": "predict", "sym": "items",
         "production": None, "depth": 1},
        {"kind": "parse-step", "event": "shift", "name": "NUM", "lexeme": "1",
         "source": {"file": "-", "line": 1, "column": 1}, "depth": 2},
        {"kind": "parse-step", "event": "complete", "rule": "items", "depth": 1},
        {"kind": "parse-step", "event": "complete", "rule": "program", "depth": 0},
    ]
    _render_trace(steps)
    out, _ = capsys.readouterr()
    lines = out.splitlines()
    assert lines == ["program", "  items", "    NUM '1' [-:1:1]"]


# --- ParseHandler.feed() trace buffering tests ---

def test_feed_on_error_renders_trace_before_error(monkeypatch, handler, capsys):
    step = _parse_step_record(event="predict", sym="program",
                               production="program", depth=0)
    procs = iter([_proc(), _proc(stdout=step + _error_record("oops"))])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    handler.feed(b"bad\n", "-")
    out, _ = capsys.readouterr()
    rule_pos = out.index("program")
    error_pos = out.index("oops")
    assert rule_pos < error_pos


def test_feed_on_error_does_not_show_old_trace_vocabulary(monkeypatch, handler, capsys):
    step = _parse_step_record(event="predict", sym="program",
                               production="program", depth=0)
    procs = iter([_proc(), _proc(stdout=step + _error_record("oops"))])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    handler.feed(b"bad\n", "-")
    out, _ = capsys.readouterr()
    assert "predict" not in out
    assert "shift" not in out
    assert "complete" not in out


def test_feed_on_success_does_not_render_trace(monkeypatch, capsys):
    # Use a rule name different from "program" so we can distinguish trace from tree
    handler = ParseHandler(spec_path="build/spec.json", ll1_path="build/ll1.json",
                           child_flags=[])
    step = _parse_step_record(event="predict", sym="traceSentinel",
                               production="traceSentinel", depth=0)
    procs = iter([_proc(), _proc(stdout=step + _tree_record())])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    handler.feed(b"42\n", "-")
    out, _ = capsys.readouterr()
    assert "traceSentinel" not in out


def test_feed_on_error_with_shift_shows_token_in_trace(monkeypatch, handler, capsys):
    predict = _parse_step_record(event="predict", sym="program",
                                  production="program", depth=0)
    shift = _shift_step_record(name="NUM", lexeme="42", depth=1)
    procs = iter([_proc(), _proc(stdout=predict + shift + _error_record("oops"))])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    handler.feed(b"42\n", "-")
    out, _ = capsys.readouterr()
    assert "NUM '42'" in out
    assert "program" in out
