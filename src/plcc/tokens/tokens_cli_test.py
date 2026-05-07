import io
import json
import pytest
import docopt

from .tokens_cli import main as run_main


_SPEC = {
    "lexical": {"ruleList": [
        {"name": "NUM", "pattern": "\\d+", "isSkip": False,
         "line": {"string": "", "number": 1, "file": None}}
    ]},
    "syntax": {"rules": []},
    "semantics": []
}


def test_no_args_prints_usage():
    with pytest.raises((docopt.DocoptExit, SystemExit)):
        run_main([])


def test_help(capsys):
    with pytest.raises(SystemExit):
        run_main(['--help'])
    out, err = capsys.readouterr()
    assert 'Usage' in out


def test_outputs_token_jsonl(capsys, monkeypatch, fs):
    fs.create_file('/spec.json', contents=json.dumps(_SPEC))
    monkeypatch.setattr('sys.stdin', io.StringIO('42\n'))
    run_main(['/spec.json'])
    out, err = capsys.readouterr()
    lines = [l for l in out.strip().splitlines() if l]
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record['kind'] == 'token'
    assert record['name'] == 'NUM'
    assert record['lexeme'] == '42'


def test_lex_error_goes_to_stderr_and_exits_nonzero(capsys, monkeypatch, fs):
    fs.create_file('/spec.json', contents=json.dumps(_SPEC))
    monkeypatch.setattr('sys.stdin', io.StringIO('abc\n'))  # not a NUM
    with pytest.raises(SystemExit) as excinfo:
        run_main(['/spec.json'])
    assert excinfo.value.code != 0
    out, err = capsys.readouterr()
    # stdout may contain zero or more token lines but no error records
    for line in out.strip().splitlines():
        if not line:
            continue
        record = json.loads(line)
        assert record['kind'] == 'token'
    # stderr carries the error
    assert 'error' in err
    assert 'plcc-tokens' in err


def test_lex_error_json_format(capsys, monkeypatch, fs):
    fs.create_file('/spec.json', contents=json.dumps(_SPEC))
    monkeypatch.setattr('sys.stdin', io.StringIO('abc\n'))
    with pytest.raises(SystemExit):
        run_main(['/spec.json', '--verbose-format=json'])
    _, err = capsys.readouterr()
    records = [json.loads(l) for l in err.strip().splitlines() if l.strip()]
    error_records = [r for r in records if r.get('event') == 'error']
    assert len(error_records) >= 1
    assert error_records[0]['stage'] == 'plcc-tokens'
    assert error_records[0]['severity'] == 'error'
    assert 'pos' in error_records[0]


def test_continue_on_error_continues_after_bad_char(capsys, monkeypatch, fs):
    fs.create_file('/spec.json', contents=json.dumps(_SPEC))
    monkeypatch.setattr('sys.stdin', io.StringIO('@ 42\n'))
    with pytest.raises(SystemExit) as excinfo:
        run_main(['/spec.json', '--continue-on-error'])
    assert excinfo.value.code != 0
    out, err = capsys.readouterr()
    lines = [l for l in out.strip().splitlines() if l]
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record['kind'] == 'token'
    assert record['name'] == 'NUM'
    assert record['lexeme'] == '42'
    assert 'error' in err


def test_continue_on_error_bad_char_only_exits_nonzero(capsys, monkeypatch, fs):
    fs.create_file('/spec.json', contents=json.dumps(_SPEC))
    monkeypatch.setattr('sys.stdin', io.StringIO('@\n'))
    with pytest.raises(SystemExit) as excinfo:
        run_main(['/spec.json', '--continue-on-error'])
    assert excinfo.value.code != 0
    out, err = capsys.readouterr()
    assert 'error' in err


def test_default_still_exits_on_first_error(capsys, monkeypatch, fs):
    fs.create_file('/spec.json', contents=json.dumps(_SPEC))
    monkeypatch.setattr('sys.stdin', io.StringIO('@ 42\n'))
    with pytest.raises(SystemExit) as excinfo:
        run_main(['/spec.json'])
    assert excinfo.value.code != 0
    out, _ = capsys.readouterr()
    lines = [l for l in out.strip().splitlines() if l]
    assert len(lines) == 0


def test_continue_on_error_valid_input_exits_zero(capsys, monkeypatch, fs):
    fs.create_file('/spec.json', contents=json.dumps(_SPEC))
    monkeypatch.setattr('sys.stdin', io.StringIO('42\n'))
    run_main(['/spec.json', '--continue-on-error'])
    out, _ = capsys.readouterr()
    lines = [l for l in out.strip().splitlines() if l]
    assert len(lines) == 1
    assert json.loads(lines[0])['name'] == 'NUM'
