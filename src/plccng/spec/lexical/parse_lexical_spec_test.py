from plccng.lines import Line
from .parse_lexical_spec import from_string


def test_None_yields_nothing():
    assertIsEmpty(None)


def test_empty_yields_nothing():
    assertIsEmpty('')


def test_blank_lines_skipped():
    assertIsEmpty(
        '''
        '''
    )


def test_comment_only_lines_skipped():
    assertIsEmpty(
        '''
        # This is a comment.
        # Another comment.
        '''
    )


def test_skip_rule():
    assertIsRule("skip WHITESPACE ','",
        isSkip=True,
        name='WHITESPACE',
        pattern=','
    )


def test_token_rule():
    assertIsRule("token MINUS '\\-'",
        isSkip=False,
        name='MINUS',
        pattern='\\-'
    )


def test_implicit_token_rule():
    assertIsRule("MINUS '\\-'",
        isSkip=False,
        name='MINUS',
        pattern='\\-'
    )


def test_trailing_comment():
    assertIsRule("MINUS '\\-'   # eol comments are ignored",
        isSkip=False,
        name='MINUS',
        pattern='\\-'
    )


def test_non_rules_are_passed_through():
    assertIsLine('This line is complete gibberish please ignore')


def test_hashtag_in_pattern_is_not_a_comment():
    assertIsRule("skip COMMENT '#'",
               isSkip=True,
               name='COMMENT',
               pattern='#')


def test_starting_whitespace_is_ignored():
    assertIsRule("  skip WHITESPACE ','",
                 isSkip=True,
                 name='WHITESPACE',
                 pattern=',')


def assertIsEmpty(string):
    lexical_spec = from_string(string)
    assert lexical_spec.ruleList == []


def assertIsRule(string, isSkip, name, pattern):
    spec = from_string(string)
    rule = spec.ruleList[0]
    assert rule.line is not None
    assert rule.isSkip == isSkip
    assert rule.name == name
    assert rule.pattern == pattern


def assertIsLine(string):
    assert isinstance(from_string(string).ruleList[0], Line)
