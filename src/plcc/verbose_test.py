import enum
import json

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS, reap_pipeline


class SampleEvents(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def test_verbose_options_is_a_string():
    assert isinstance(VERBOSE_OPTIONS, str)
    assert "--verbose" in VERBOSE_OPTIONS
    assert "--verbose-format" in VERBOSE_OPTIONS


def test_from_args_defaults():
    args = {"--verbose": "0", "--verbose-format": "text"}
    ctx = VerboseContext.from_args("plcc-test", SampleEvents, args)
    assert ctx.stage == "plcc-test"
    assert ctx.level == 0
    assert ctx.fmt == "text"


def test_from_args_with_values():
    args = {"--verbose": "2", "--verbose-format": "json"}
    ctx = VerboseContext.from_args("plcc-test", SampleEvents, args)
    assert ctx.level == 2
    assert ctx.fmt == "json"


def test_emit_text_format(capsys):
    args = {"--verbose": "1", "--verbose-format": "text"}
    ctx = VerboseContext.from_args("plcc-test", SampleEvents, args)
    ctx.emit(SampleEvents.STARTED, message="reading spec")
    captured = capsys.readouterr()
    assert captured.out == ""  # nothing on stdout
    assert "plcc-test: started: reading spec" in captured.err


def test_emit_json_format(capsys):
    args = {"--verbose": "1", "--verbose-format": "json"}
    ctx = VerboseContext.from_args("plcc-test", SampleEvents, args)
    ctx.emit(SampleEvents.STARTED, message="reading spec")
    captured = capsys.readouterr()
    assert captured.out == ""
    record = json.loads(captured.err.strip())
    assert record["stage"] == "plcc-test"
    assert record["event"] == "started"
    assert record["message"] == "reading spec"
    assert "time" in record


def test_emit_suppressed_when_level_too_low(capsys):
    args = {"--verbose": "0", "--verbose-format": "text"}
    ctx = VerboseContext.from_args("plcc-test", SampleEvents, args)
    ctx.emit(SampleEvents.STARTED, level=1, message="should not appear")
    captured = capsys.readouterr()
    assert captured.err == ""


def test_child_flags_returns_unchanged():
    args = {"--verbose": "2", "--verbose-format": "text"}
    ctx = VerboseContext.from_args("plcc-test", SampleEvents, args)
    flags = ctx.child_flags()
    assert "--verbose=2" in flags
    assert "--verbose-format=text" in flags


def test_child_flags_for_orchestrator_forces_json():
    args = {"--verbose": "1", "--verbose-format": "text"}
    ctx = VerboseContext.from_args("plcc-test", SampleEvents, args)
    flags = ctx.child_flags_for_orchestrator(min_level=2)
    assert "--verbose=2" in flags
    assert "--verbose-format=json" in flags


def test_child_flags_for_orchestrator_keeps_higher_user_level():
    args = {"--verbose": "3", "--verbose-format": "text"}
    ctx = VerboseContext.from_args("plcc-test", SampleEvents, args)
    flags = ctx.child_flags_for_orchestrator(min_level=1)
    assert "--verbose=3" in flags


def test_parse_child_events_roundtrip(capsys):
    args = {"--verbose": "1", "--verbose-format": "json"}
    ctx = VerboseContext.from_args("plcc-test", SampleEvents, args)
    ctx.emit(SampleEvents.STARTED, message="hello")
    captured = capsys.readouterr()
    events = ctx.parse_child_events(captured.err)
    assert len(events) == 1
    assert events[0]["event"] == "started"


def test_reformat_child_events_to_text(capsys):
    json_line = json.dumps({"stage": "plcc-child", "time": 0, "event": "started", "message": "hi"})
    args = {"--verbose": "1", "--verbose-format": "text"}
    ctx = VerboseContext.from_args("plcc-parent", SampleEvents, args)
    events = ctx.parse_child_events(json_line + "\n")
    ctx.reformat_child_events(events)
    captured = capsys.readouterr()
    assert "plcc-child: started: hi" in captured.err


def test_parity_both_renderers_handle_all_events(capsys):
    """Every event in the enum is handled by both text and json renderers."""
    for fmt in ("text", "json"):
        args = {"--verbose": "1", "--verbose-format": fmt}
        ctx = VerboseContext.from_args("plcc-test", SampleEvents, args)
        for event in SampleEvents:
            ctx.emit(event, message="test")
        captured = capsys.readouterr()
        assert captured.err != ""


def test_emit_error_text_format(capsys):
    ctx = VerboseContext("plcc-tokens", SampleEvents, level=0, fmt="text")
    ctx.emit_error(
        pos={"file": "prog.txt", "line": 4, "column": 12},
        message="unrecognized character '$'",
    )
    out, err = capsys.readouterr()
    assert out == ""
    assert err == "plcc-tokens: prog.txt:4:12: error: unrecognized character '$'\n"


def test_emit_error_text_format_no_file(capsys):
    ctx = VerboseContext("plcc-tokens", SampleEvents, level=0, fmt="text")
    ctx.emit_error(
        pos={"file": None, "line": 1, "column": 1},
        message="unrecognized character",
    )
    _, err = capsys.readouterr()
    assert err == "plcc-tokens: <stdin>:1:1: error: unrecognized character\n"


def test_emit_error_json_format(capsys):
    ctx = VerboseContext("plcc-tokens", SampleEvents, level=0, fmt="json")
    ctx.emit_error(
        pos={"file": "prog.txt", "line": 4, "column": 12},
        message="unrecognized character '$'",
        codepoint=36,
    )
    out, err = capsys.readouterr()
    assert out == ""
    lines = err.strip().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["stage"] == "plcc-tokens"
    assert record["event"] == "error"
    assert record["severity"] == "error"
    assert record["pos"] == {"file": "prog.txt", "line": 4, "column": 12}
    assert record["message"] == "unrecognized character '$'"
    assert record["codepoint"] == 36


def test_emit_error_ignores_verbose_level(capsys):
    ctx = VerboseContext("plcc-tokens", SampleEvents, level=0, fmt="text")
    ctx.emit_error(
        pos={"file": "prog.txt", "line": 1, "column": 1},
        message="boom",
    )
    _, err = capsys.readouterr()
    assert "error: boom" in err


def _dummy_proc(stderr_bytes, returncode):
    """Build a minimal Popen-like object for unit testing reap_pipeline."""
    class P:
        pass
    p = P()
    p.returncode = returncode
    p.stderr_captured = stderr_bytes
    return p


def test_reap_pipeline_all_success():
    tokens_stderr = b'{"stage":"plcc-tokens","event":"started"}\n'
    tree_stderr = b'{"stage":"plcc-tree","event":"started"}\n'
    stages = [
        (_dummy_proc(tokens_stderr, 0), "plcc-tokens"),
        (_dummy_proc(tree_stderr, 0), "plcc-tree"),
    ]
    result = reap_pipeline(stages)
    assert result.failed_stage is None
    assert result.exit_code == 0
    # All non-error events are kept for reformatting
    assert len(result.events_to_render) == 2


def test_reap_pipeline_upstream_failure_suppresses_downstream():
    tokens_err = (
        b'{"stage":"plcc-tokens","event":"error","severity":"error",'
        b'"pos":{"file":"p.txt","line":1,"column":3},'
        b'"message":"unrecognized character"}\n'
    )
    tree_err = (
        b'{"stage":"plcc-tree","event":"error","severity":"error",'
        b'"pos":{"file":"p.txt","line":1,"column":0},'
        b'"message":"unexpected end of input"}\n'
    )
    stages = [
        (_dummy_proc(tokens_err, 1), "plcc-tokens"),
        (_dummy_proc(tree_err, 1), "plcc-tree"),
    ]
    result = reap_pipeline(stages)
    assert result.failed_stage == "plcc-tokens"
    assert result.exit_code == 1
    # Only the upstream-failing stage's error events render
    rendered_stages = {ev["stage"] for ev in result.events_to_render}
    assert rendered_stages == {"plcc-tokens"}


def test_reap_pipeline_downstream_failure_reports_downstream():
    # Upstream succeeded; downstream failed (e.g. parser hit a syntax error)
    tokens_ok = b'{"stage":"plcc-tokens","event":"finished"}\n'
    parser_err = (
        b'{"stage":"plcc-parser-table","event":"error","severity":"error",'
        b'"pos":{"file":"p.txt","line":4,"column":12},'
        b'"message":"expected IDENT"}\n'
    )
    stages = [
        (_dummy_proc(tokens_ok, 0), "plcc-tokens"),
        (_dummy_proc(parser_err, 2), "plcc-tree"),
    ]
    result = reap_pipeline(stages)
    assert result.failed_stage == "plcc-tree"
    assert result.exit_code == 2
