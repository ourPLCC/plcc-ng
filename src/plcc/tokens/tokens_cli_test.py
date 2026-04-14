import io
import json
import pytest
import docopt

from .tokens_cli import main as run_main


def test_no_args_prints_usage():
    with pytest.raises((docopt.DocoptExit, SystemExit)):
        run_main([])


def test_help(capsys):
    with pytest.raises(SystemExit):
        run_main(['--help'])
    out, err = capsys.readouterr()
    assert 'Usage' in out


def test_outputs_token_jsonl(capsys, monkeypatch, fs):
    spec = {
        "lexical": {"ruleList": [
            {"name": "NUM", "pattern": "\\d+", "isSkip": False,
             "line": {"string": "", "number": 1, "file": None}}
        ]},
        "syntax": {"rules": []},
        "semantics": []
    }
    import json as _json
    fs.create_file('/spec.json', contents=_json.dumps(spec))
    monkeypatch.setattr('sys.stdin', io.StringIO('42\n'))
    run_main(['/spec.json'])
    out, err = capsys.readouterr()
    lines = [l for l in out.strip().splitlines() if l]
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record['kind'] == 'token'
    assert record['name'] == 'NUM'
    assert record['lexeme'] == '42'


def test_lex_error_is_inband(capsys, monkeypatch, fs):
    spec = {
        "lexical": {"ruleList": [
            {"name": "NUM", "pattern": "\\d+", "isSkip": False,
             "line": {"string": "", "number": 1, "file": None}}
        ]},
        "syntax": {"rules": []},
        "semantics": []
    }
    import json as _json
    fs.create_file('/spec.json', contents=_json.dumps(spec))
    monkeypatch.setattr('sys.stdin', io.StringIO('abc\n'))  # not a NUM
    run_main(['/spec.json'])
    out, err = capsys.readouterr()
    lines = [l for l in out.strip().splitlines() if l]
    assert any(json.loads(l)['kind'] == 'error' for l in lines)
    # stderr must be empty — errors are in-band
    assert err == ''
