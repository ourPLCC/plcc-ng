import enum
import json

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS


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
