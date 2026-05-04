import io
import json
import pytest

from plcc.ll1.ll1_cli import main as run_main


def _trivial_spec():
    return {
        "lexical": {"ruleList": []},
        "syntax": {"rules": [
            {
                "line": {"string": "<program> ::= NUM", "number": 3, "file": ""},
                "lhs": {"name": "program", "isTerminal": False, "altName": None, "isCapturing": False},
                "rhsSymbolList": [{"name": "NUM", "isTerminal": True, "isCapturing": False}],
            }
        ]},
        "semantics": [],
    }


def _empty_spec():
    return {"lexical": {"ruleList": []}, "syntax": {"rules": []}, "semantics": []}


def test_exits_zero_and_emits_json(capsys, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(_trivial_spec())))
    run_main([])
    out, _ = capsys.readouterr()
    result = json.loads(out)
    assert isinstance(result, dict)


def test_emits_start_symbol(capsys, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(_trivial_spec())))
    run_main([])
    out, _ = capsys.readouterr()
    assert json.loads(out)["start_symbol"] == "program"


def test_is_ll1_true_for_trivial_grammar(capsys, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(_trivial_spec())))
    run_main([])
    out, _ = capsys.readouterr()
    assert json.loads(out)["is_ll1"] is True


def test_first_sets_populated(capsys, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(_trivial_spec())))
    run_main([])
    out, _ = capsys.readouterr()
    result = json.loads(out)
    assert result["first_sets"]["program"] == ["NUM"]


def test_empty_spec_is_ll1_true(capsys, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(_empty_spec())))
    run_main([])
    out, _ = capsys.readouterr()
    result = json.loads(out)
    assert result["is_ll1"] is True
    assert result["start_symbol"] is None


def test_malformed_json_exits_nonzero(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("not json"))
    with pytest.raises(SystemExit) as exc:
        run_main([])
    assert exc.value.code != 0


def test_verbose_started_emitted(capsys, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(_trivial_spec())))
    run_main(["--verbose=1", "--verbose-format=json"])
    _, err = capsys.readouterr()
    events = [json.loads(line) for line in err.strip().splitlines() if line]
    assert any(e["event"] == "started" for e in events)


def test_verbose_finished_emitted(capsys, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(_trivial_spec())))
    run_main(["--verbose=1", "--verbose-format=json"])
    _, err = capsys.readouterr()
    events = [json.loads(line) for line in err.strip().splitlines() if line]
    assert any(e["event"] == "finished" for e in events)


def test_verbose_level2_first_set_events(capsys, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(_trivial_spec())))
    run_main(["--verbose=2", "--verbose-format=json"])
    _, err = capsys.readouterr()
    events = [json.loads(line) for line in err.strip().splitlines() if line]
    assert any(e["event"] == "first-set" for e in events)
