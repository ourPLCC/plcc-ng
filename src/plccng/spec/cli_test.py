import io
import json

import docopt
import pytest

from .cli import cli


def test_no_args_prints_usage():
    with pytest.raises(docopt.DocoptExit, match=r'Usage'):
        cli(['spec'])


def test_h_prints_usage(capsys):
    with pytest.raises(SystemExit):
        cli('spec -h'.split())
    assertStdoutContains(capsys, 'Usage')


def test_help_prints_usage(capsys):
    with pytest.raises(SystemExit):
        cli('spec --help'.split())
    assertStdoutContains(capsys, 'Usage')


def assertStdoutContains(capsys, string):
    out, err = capsys.readouterr()
    assert string in out


def test_spec_from_file(capsys, fs, oneRuleSpec):
    file = createFile(fs, oneRuleSpec)
    cli(f'spec {file}'.split())
    assertStdoutContainsJsonSpec(capsys, ruleCount=1)


def test_spec_from_stdin(monkeypatch, capsys, oneRuleSpec):
    setStdin(monkeypatch, oneRuleSpec)
    cli('spec -'.split())
    assertStdoutContainsJsonSpec(capsys, ruleCount=1)


def test_spec_with_one_error(capsys, fs, specWithNameExpectedError):
    file = createFile(fs, specWithNameExpectedError)
    cli(f'spec {file}'.split())
    assertStdoutContains(capsys, 'NameExpected')


def createFile(fs, oneRuleSpec):
    fs.create_file("/spec.plcc", contents=oneRuleSpec)
    return "/spec.plcc"


def setStdin(monkeypatch, string):
    monkeypatch.setattr('sys.stdin', io.StringIO(string))


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
