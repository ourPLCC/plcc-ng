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


def test_lex_error_emits_error_record_to_stdout(capsys, monkeypatch, fs):
    fs.create_file('/spec.json', contents=json.dumps(_SPEC))
    monkeypatch.setattr('sys.stdin', io.StringIO('@\n'))
    # Verify it does not raise SystemExit (exits 0)
    try:
        run_main(['/spec.json'])
    except SystemExit as e:
        pytest.fail(f"run_main raised SystemExit({e.code}), expected normal return")
    out, err = capsys.readouterr()
    lines = [l for l in out.strip().splitlines() if l]
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record['kind'] == 'error'
    assert record['stage'] == 'plcc-tokens'
    assert record['severity'] == 'error'
    assert record['lexeme'] == '@'
    assert record['pos'] == {'file': '-', 'line': 1, 'column': 1}
    assert record['message'] == 'unrecognized character'
    assert err == ''


def test_lex_error_and_token_appear_in_stream_order(capsys, monkeypatch, fs):
    fs.create_file('/spec.json', contents=json.dumps(_SPEC))
    # '@' is unrecognized, then '42' is a valid NUM token
    monkeypatch.setattr('sys.stdin', io.StringIO('@42\n'))
    run_main(['/spec.json'])
    out, err = capsys.readouterr()
    lines = [l for l in out.strip().splitlines() if l]
    assert len(lines) == 2
    assert json.loads(lines[0])['kind'] == 'error'
    assert json.loads(lines[1])['kind'] == 'token'
    assert json.loads(lines[1])['name'] == 'NUM'


def test_stdin_labels_tokens_with_dash(capsys, monkeypatch, fs):
    fs.create_file('/spec.json', contents=json.dumps(_SPEC))
    monkeypatch.setattr('sys.stdin', io.StringIO('42\n'))
    run_main(['/spec.json'])
    out, _ = capsys.readouterr()
    record = json.loads(out.strip())
    assert record['source']['file'] == '-'


def test_named_file_arg_labels_tokens_with_filename(capsys, fs):
    fs.create_file('/spec.json', contents=json.dumps(_SPEC))
    fs.create_file('/src.txt', contents='42\n')
    run_main(['/spec.json', '/src.txt'])
    out, _ = capsys.readouterr()
    record = json.loads(out.strip())
    assert record['source']['file'] == '/src.txt'
