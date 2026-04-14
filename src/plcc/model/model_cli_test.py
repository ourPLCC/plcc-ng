import io
import json
import pytest
import docopt

from .model_cli import main as run_main


# Shape matches actual plcc-spec output (rhsSymbolList, not rhs)
_TRIVIAL_SPEC_JSON = json.dumps({
    "lexical": {"ruleList": [
        {
            "name": "NUM",
            "pattern": "\\d+",
            "isSkip": False,
            "line": {"string": "token NUM '\\d+'", "number": 1, "file": None}
        }
    ]},
    "syntax": {"rules": [
        {
            "line": {"string": "<program> ::= NUM", "number": 3, "file": None},
            "lhs": {"name": "program", "isTerminal": False, "altName": None, "isCapturing": False},
            "rhsSymbolList": [
                {"name": "NUM", "isTerminal": True, "isCapturing": True}
            ]
        }
    ]},
    "semantics": [{"language": "PlantUML", "tool": "diagram", "codeFragmentList": []}]
})


def test_no_args_reads_from_stdin(capsys, monkeypatch):
    # SPEC_JSON is optional; omitting it defaults to reading from stdin (same as '-').
    monkeypatch.setattr('sys.stdin', io.StringIO(_TRIVIAL_SPEC_JSON))
    run_main([])
    out, err = capsys.readouterr()
    model = json.loads(out)
    assert model['start'] == 'program'


def test_help(capsys):
    with pytest.raises(SystemExit):
        run_main(['--help'])
    out, err = capsys.readouterr()
    assert 'Usage' in out


def test_reads_spec_from_file(capsys, fs):
    fs.create_file('/spec.json', contents=_TRIVIAL_SPEC_JSON)
    run_main(['/spec.json'])
    out, err = capsys.readouterr()
    model = json.loads(out)
    assert 'classes' in model
    assert model['start'] == 'program'


def test_reads_spec_from_stdin(capsys, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(_TRIVIAL_SPEC_JSON))
    run_main(['-'])
    out, err = capsys.readouterr()
    model = json.loads(out)
    assert model['start'] == 'program'
