import io
import json
import pytest

from plcc.ll1.ll1_cli import main as run_main


def test_stub_emits_is_ll1_true_and_exits_zero(capsys, monkeypatch, fs):
    spec = {"lexical": {"ruleList": []}, "syntax": {"rules": []}, "semantics": []}
    fs.create_file('/spec.json', contents=json.dumps(spec))
    run_main(['/spec.json'])
    out, err = capsys.readouterr()
    record = json.loads(out)
    assert record['is_ll1'] is True
    assert record['conflicts'] == []
    assert record['left_recursion'] == []


def test_stub_accepts_stdin(capsys, monkeypatch):
    spec = {"lexical": {"ruleList": []}, "syntax": {"rules": []}, "semantics": []}
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(spec)))
    run_main(['-'])
    out, _ = capsys.readouterr()
    record = json.loads(out)
    assert record['is_ll1'] is True
