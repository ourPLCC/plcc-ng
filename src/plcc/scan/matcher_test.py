from ..lines import parseLines
from ..spec import parseSpec
from . import matcher
from .LexError import LexError
from .Skip import Skip
from .Token import Token


def test_empty_line():
    matcher = makeMatcher(r'''token MINUS '-' ''')
    emptyLine = parseLine('')
    result = matcher.match(emptyLine, index = 0)
    assert result.__class__ == LexError

def test_empty_spec():
    emptySpec = []
    matcher = makeMatcher(emptySpec)
    line = parseLine("This is a test.")
    result = matcher.match(line, index=0)
    assert result.__class__ == LexError

def test_match_token():
    matcher = makeMatcher(r'''token MINUS '-' ''')
    line = parseLine("-")
    result = matcher.match(line, index=0)
    assert result == Token(lexeme="-", name="MINUS", line = line, column=1)

def test_match_skip():
    matcher = makeMatcher(r'''skip MINUS '-' ''')
    line = parseLine("-")
    result = matcher.match(line, index=0)
    assert result == Skip(lexeme="-", name="MINUS", line = line, column=1)

def test_match_token_with_multiple_rules():
    matcher = makeMatcher(r'''
        token MINUS '-'
        token NUMBER '\d+'
    ''')
    line = parseLine("11--")
    result = matcher.match(line, index=0)
    assert result == Token(lexeme="11", name="NUMBER", line = line, column=1)

def test_match_longest_rule():
    matcher = makeMatcher(r'''
        token NUMBER '\d+'
        token ONETWOTHREE '123'
    ''')
    line = parseLine("1235564")
    result = matcher.match(line, index=0)
    assert result == Token(lexeme="1235564", name="NUMBER", line = line, column=1)

    # order should not matter
    matcher = makeMatcher(r'''
        token ONETWOTHREE '123'
        token NUMBER '\d+'
    ''')
    line = parseLine("1235564")
    result = matcher.match(line, index=0)
    assert result == Token(lexeme="1235564", name="NUMBER", line = line, column=1)

def test_match_first_longest_rule():
    matcher = makeMatcher(r'''
        token ONETWOTHREE '123'
        token NUMBER '\d+'
    ''')
    line = parseLine("123")
    result = matcher.match(line, index=0)
    assert result == Token(lexeme="123", name = "ONETWOTHREE", line = line, column=1)

    # order matters
    matcher = makeMatcher(r'''
        token NUMBER '\d+'
        token ONETWOTHREE '123'
    ''')
    line = parseLine("123")
    result = matcher.match(line, index=0)
    assert result == Token(lexeme="123", name = "NUMBER", line = line, column=1)

def test_skip_wins_if_it_matches_before_any_token_rules():
    matcher = makeMatcher(r'''
        skip ONE '1'
        token NUMBER '\d+'
    ''')
    line = parseLine("123")
    result = matcher.match(line, index=0)
    assert result == Skip(lexeme='1', name='ONE', line = line, column=1)


def test_once_a_token_matches_subsequent_skip_are_ignored():
    # ONETWOTHREE cannot win, even though it is the longest match,
    # because there is at least one matching token rule earlier than
    # the skip rule in the spec.
    matcher = makeMatcher(r'''
        token ONETWO '12'
        skip ONETWOTHREE '123'
        token NUMBER '\d+'
    ''')
    line = parseLine("123")
    result = matcher.match(line, index=0)
    assert result == Token(lexeme='123', name='NUMBER', line = line, column=1)


def test_match_mid_string():
    matcher = makeMatcher(r'''
        skip ONE '1'
        token NUMBER '\d+'
    ''')
    line = parseLine("hi 123")
    result = matcher.match(line, index=3)
    assert result == Skip(lexeme='1', name='ONE', line = line, column=4)
    result = matcher.match(line, index=4)
    assert result == Token(lexeme='23', name='NUMBER', line = line, column=5)


def test_pattern_always_set_on_token():
    m = makeMatcher(r"token NUM '\d+'")
    line = parseLine("42")
    result = m.match(line, index=0)
    assert isinstance(result, Token)
    assert result.pattern == r'\d+'

def test_pattern_always_set_on_skip():
    m = makeMatcher(r"skip WS '\s+'")
    line = parseLine(" ")
    result = m.match(line, index=0)
    assert isinstance(result, Skip)
    assert result.pattern == r'\s+'

def test_attempts_empty_by_default():
    m = makeMatcher(r"token NUM '\d+'")
    line = parseLine("42")
    result = m.match(line, index=0)
    assert result.attempts == []

def test_record_attempts_token_win():
    m = makeMatcher(r"""
        token ONE '\d'
        token NUM '\d+'
    """, record_attempts=True)
    line = parseLine("42")
    result = m.match(line, index=0)
    assert isinstance(result, Token)
    assert result.name == "NUM"
    assert len(result.attempts) == 2
    winners = [a for a in result.attempts if a['winner']]
    assert len(winners) == 1
    assert winners[0]['name'] == "NUM"
    losers = [a for a in result.attempts if not a['winner']]
    assert len(losers) == 1
    assert losers[0]['name'] == "ONE"

def test_record_attempts_skip_win_includes_token_candidates():
    # skip appears before token in definition order AND both match '42'.
    # Skip short-circuits: result is the Skip, but NUM should appear in
    # attempts as a non-winning candidate.
    m = makeMatcher(r"""
        skip WS '\d+'
        token NUM '\d+'
    """, record_attempts=True)
    line = parseLine("42")
    result = m.match(line, index=0)
    assert isinstance(result, Skip)
    assert len(result.attempts) == 2
    winners = [a for a in result.attempts if a['winner']]
    assert len(winners) == 1
    assert winners[0]['name'] == "WS"
    assert winners[0]['is_skip'] is True
    losers = [a for a in result.attempts if not a['winner']]
    assert len(losers) == 1
    assert losers[0]['name'] == "NUM"
    assert losers[0]['is_skip'] is False

def test_record_attempts_token_wins_over_later_skip():
    # TOKEN appears before SKIP in definition order, so short-circuit does
    # not fire. SKIP should still appear in attempts as non-winner.
    m = makeMatcher(r"""
        token NUM '\d+'
        skip  WS  '\d'
    """, record_attempts=True)
    line = parseLine("42")
    result = m.match(line, index=0)
    assert isinstance(result, Token)
    names = [a['name'] for a in result.attempts]
    assert 'NUM' in names
    assert 'WS' in names
    winner = next(a for a in result.attempts if a['winner'])
    assert winner['name'] == 'NUM'

def test_attempts_entry_fields():
    m = makeMatcher(r"token NUM '\d+'", record_attempts=True)
    line = parseLine("42")
    result = m.match(line, index=0)
    a = result.attempts[0]
    assert a['name'] == 'NUM'
    assert a['regex'] == r'\d+'
    assert a['lexeme'] == '42'
    assert a['char_count'] == 2
    assert a['is_skip'] is False
    assert a['winner'] is True


#helper methods

def makeMatcher(spec, record_attempts=False):
    if isinstance(spec, str):
        spec, errors = parseSpec(spec)
        return matcher.Matcher(spec.lexical.ruleList, record_attempts=record_attempts)
    else:
        return matcher.Matcher(spec, record_attempts=record_attempts)


def parseLine(string):
    return list(parseLines(string + '\n'))[0]
