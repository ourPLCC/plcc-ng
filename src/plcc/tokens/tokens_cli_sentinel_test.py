import io
import json
import pytest

from .tokens_cli import main as run_main


_SPEC = {
    "lexical": {"ruleList": [
        {"name": "NUM", "pattern": "\\d+", "isSkip": False,
         "line": {"string": "", "number": 1, "file": None}}
    ]},
    "syntax": {"rules": []},
    "semantics": []
}


def test_tokens_emits_dollar_sentinel_at_eof(capsys, monkeypatch, fs):
    fs.create_file('/spec.json', contents=json.dumps(_SPEC))
    monkeypatch.setattr('sys.stdin', io.StringIO('42\n'))
    run_main(['/spec.json'])
    out, _ = capsys.readouterr()
    records = [json.loads(l) for l in out.strip().splitlines() if l]
    last = records[-1]
    assert last["kind"] == "token"
    assert last["name"] == "$"
    assert last["lexeme"] == ""


def test_tokens_dollar_sentinel_has_source(capsys, monkeypatch, fs):
    fs.create_file('/spec.json', contents=json.dumps(_SPEC))
    monkeypatch.setattr('sys.stdin', io.StringIO('42\n'))
    run_main(['/spec.json'])
    out, _ = capsys.readouterr()
    records = [json.loads(l) for l in out.strip().splitlines() if l]
    last = records[-1]
    assert "source" in last


def test_tokens_dollar_sentinel_on_empty_input(capsys, monkeypatch, fs):
    fs.create_file('/spec.json', contents=json.dumps(_SPEC))
    monkeypatch.setattr('sys.stdin', io.StringIO(''))
    run_main(['/spec.json'])
    out, _ = capsys.readouterr()
    records = [json.loads(l) for l in out.strip().splitlines() if l]
    assert len(records) == 1
    assert records[0]["name"] == "$"
