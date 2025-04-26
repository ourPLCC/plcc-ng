import io
import json

import docopt
import pytest

from .spec_cli import run


def test_no_args_prints_usage(capsys):
    with pytest.raises(docopt.DocoptExit, match="Usage"):
        run(['spec'])


def test_h_prints_usage(capsys):
    with pytest.raises(SystemExit):
        run('spec -h'.split())
    out, err = capsys.readouterr()
    assert 'Usage' in out


def test_help_prints_usage(capsys):
    with pytest.raises(SystemExit):
        run('spec --help'.split())
    out, err = capsys.readouterr()
    assert 'Usage' in out


def test_spec_from_file(capsys, fs, oneRuleSpec):
    file = createFile(fs, oneRuleSpec)
    run(f'spec {file}'.split())
    assertStdoutContainsJsonSpec(capsys, ruleCount=1)


def test_spec_from_stdin(monkeypatch, capsys, oneRuleSpec):
    setStdin(monkeypatch, oneRuleSpec)
    run('spec -'.split())
    assertStdoutContainsJsonSpec(capsys, ruleCount=1)


def test_spec_with_one_error(capsys, fs, specWithNameExpectedError):
    file = createFile(fs, specWithNameExpectedError)
    with pytest.raises(SystemExit) as info:
        run(f'spec {file}'.split())
    assert info.value.code == 1
    assertStderrContains(capsys, 'NameExpected')


def test_no_json(capsys, fs, oneRuleSpec):
    file = createFile(fs, oneRuleSpec)
    run(f'spec --no-json {file}'.split())
    out, err = capsys.readouterr()
    assert not out


def test_status(monkeypatch, capsys, oneRuleSpec):
    setStdin(monkeypatch, oneRuleSpec)
    run('spec -'.split())
    out, err = capsys.readouterr()
    assert 'Reading' in err


def test_no_status(monkeypatch, capsys, oneRuleSpec):
    setStdin(monkeypatch, oneRuleSpec)
    run('spec --no-status -'.split())
    out, err = capsys.readouterr()
    assert 'Reading' not in err


def createFile(fs, oneRuleSpec):
    fs.create_file("/spec.plcc", contents=oneRuleSpec)
    return "/spec.plcc"


def setStdin(monkeypatch, string):
    monkeypatch.setattr('sys.stdin', io.StringIO(string))


def assertStderrContains(capsys, string):
    out, err = capsys.readouterr()
    assert string in err


def assertStdoutContainsJsonSpec(capsys, ruleCount):
    out, err = capsys.readouterr()
    result = json.loads(out)
    assert len(result['lexical']['ruleList']) == ruleCount


@pytest.fixture
def oneRuleSpec():
    return '''

            A 'a'

    '''

@pytest.fixture
def specWithNameExpectedError():
    return '''

            a 'a'

    '''
