"""Load lexical rules from a spec JSON file for use by plcc-tokens."""

import json

from ..spec.lexical.TokenRule import TokenRule
from ..spec.lexical.SkipRule import SkipRule


def load_lexical_rules(spec_json_path):
    """Return a list of TokenRule/SkipRule objects from a spec JSON file."""
    with open(spec_json_path) as f:
        data = json.load(f)
    rules = []
    for r in data['lexical']['ruleList']:
        RuleClass = SkipRule if r['isSkip'] else TokenRule
        rules.append(RuleClass(
            name=r['name'],
            pattern=r['pattern'],
            line=None,
        ))
    return rules
