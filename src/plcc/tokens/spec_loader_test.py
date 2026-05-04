import json
import pytest
from pyfakefs.fake_filesystem_unittest import Patcher

from .spec_loader import load_lexical_rules


def test_loads_lexical_rules(fs):
    spec = {
        "lexical": {
            "ruleList": [
                {"name": "NUM", "pattern": "\\d+", "isSkip": False,
                 "line": {"string": "", "number": 1, "file": None}}
            ]
        },
        "syntax": {"rules": []},
        "semantics": []
    }
    fs.create_file('/spec.json', contents=json.dumps(spec))
    rules = load_lexical_rules('/spec.json')
    assert len(rules) == 1
    assert rules[0].name == 'NUM'
    assert rules[0].pattern == '\\d+'
    assert rules[0].isSkip is False


def test_empty_rule_list(fs):
    spec = {"lexical": {"ruleList": []}, "syntax": {"rules": []}, "semantics": []}
    fs.create_file('/empty.json', contents=json.dumps(spec))
    rules = load_lexical_rules('/empty.json')
    assert rules == []
