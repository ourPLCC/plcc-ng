"""Load lexical rules from a spec JSON file for use by plcc-tokens."""

import json

from ..spec.lexical import TokenRule, SkipRule


def load_lexical_rules(spec_json_path):
    """Return a list of LexicalRule objects from a spec JSON file."""
    with open(spec_json_path) as f:
        data = json.load(f)
    return [
        (SkipRule if r['isSkip'] else TokenRule)(
            name=r['name'],
            pattern=r['pattern'],
            line=None,
        )
        for r in data['lexical']['ruleList']
    ]
