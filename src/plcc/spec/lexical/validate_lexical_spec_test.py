from .validate_lexical_spec import validate_lexical_spec


def test_returns_empty_list_for_any_spec():
    assert validate_lexical_spec({'lexical': {'ruleList': []}}) == []

def test_returns_empty_list_for_empty_dict():
    assert validate_lexical_spec({}) == []
