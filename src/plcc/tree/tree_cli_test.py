import io
import json
import pytest
import docopt

from .tree_cli import main as run_main


_ONE_TOKEN = json.dumps({
    'kind': 'token', 'name': 'NUM', 'lexeme': '42',
    'source': {'file': '<stdin>', 'line': 1, 'column': 1}
})

_ONE_ERROR = json.dumps({
    'kind': 'error', 'stage': 'plcc-tokens',
    'source': {'file': '<stdin>', 'line': 1, 'column': 1}
})


def test_no_args_prints_usage():
    with pytest.raises((docopt.DocoptExit, SystemExit)):
        run_main([])


def test_help(capsys):
    with pytest.raises(SystemExit):
        run_main(['--help'])
    out, err = capsys.readouterr()
    assert 'Usage' in out


def test_token_stream_produces_tree(capsys, monkeypatch, tmp_path):
    # --spec must be a path to spec JSON (output of plcc-spec), not a grammar file.
    # Phase 1 implementation accepts but ignores the spec content.
    spec_json = tmp_path / 'trivial.spec.json'
    spec_json.write_text('{}')  # content ignored in Phase 1
    monkeypatch.setattr('sys.stdin', io.StringIO(_ONE_TOKEN + '\n'))
    run_main([f'--spec={spec_json}'])
    out, err = capsys.readouterr()
    lines = [l for l in out.strip().splitlines() if l]
    assert len(lines) == 1
    tree = json.loads(lines[0])
    assert tree['kind'] == 'tree'
    assert tree['rule'] == 'program'


def test_error_record_passes_through(capsys, monkeypatch, tmp_path):
    spec_json = tmp_path / 'trivial.spec.json'
    spec_json.write_text('{}')  # content ignored in Phase 1
    monkeypatch.setattr('sys.stdin', io.StringIO(_ONE_ERROR + '\n'))
    run_main([f'--spec={spec_json}'])
    out, err = capsys.readouterr()
    lines = [l for l in out.strip().splitlines() if l]
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record['kind'] == 'error'
    assert err == ''  # error stays in-band
