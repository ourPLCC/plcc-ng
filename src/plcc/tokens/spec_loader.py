"""Load lexical rules from a spec JSON file for use by plcc-tokens."""

import json

# plcc.spec.lexical.LexicalRule can be imported without circular dependency,
# so we use it directly rather than defining a private dataclass.
from ..spec.lexical import LexicalRule


def load_lexical_rules(spec_json_path):
    """Return a list of LexicalRule objects from a spec JSON file."""
    with open(spec_json_path) as f:
        data = json.load(f)
    return [
        LexicalRule(
            name=r['name'],
            pattern=r['pattern'],
            isSkip=r['isSkip'],
            line=None,
        )
        for r in data['lexical']['ruleList']
    ]
