import sys

import docopt
import pytest
import json

from .cli import cli


def test_no_args_prints_usage(capsys, fs):
    with pytest.raises(docopt.DocoptExit, match=r'Usage'):
        cli(['spec'])


def test_h_prints_usage(capsys, fs):
    with pytest.raises(SystemExit):
        cli('spec -h'.split())
    out, err = capsys.readouterr()
    assert 'Usage' in out


def test_help_prints_usage(capsys, fs):
    with pytest.raises(SystemExit):
        cli('spec --help'.split())
    out, err = capsys.readouterr()
    assert 'Usage' in out


def test_spec_from_file(capsys, fs):
    fs.create_file("/spec.plcc", contents='''\

            A 'a'

    ''')
    cli('spec /spec.plcc'.split())
    out, err = capsys.readouterr()
    result = json.loads(out)
    assert len(result['lexical']['ruleList']) == 1
