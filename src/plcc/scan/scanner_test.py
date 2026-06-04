import pytest

from ..lines import parseLines
from ..spec import parseSpec
from .scanner import Scanner
from .LexError import LexError
from .Skip import Skip
from .Token import Token
from . import matcher as matcherModule


@pytest.fixture
def errorRaisingMatcher():
    class ErrorRaisingMatcher:
        def match(self, line, index):
            return LexError(line=line, column=index+1)
    return ErrorRaisingMatcher()


@pytest.fixture
def tabSkipMatcher():
    class TabSkipMatcher():
        def match(self, line, index):
            if line.string[index] == "\t":
                return Skip(name="whitespace", lexeme="\t", line=line, column=index+1)
            else:
                return LexError(line=line, column=index+1)
    return TabSkipMatcher()


@pytest.fixture
def fiveCharacterMatcher():
    class FiveCharacterMatcher():
        def match(self, line, index):
            return Token(name="Token", lexeme=line.string[index:index+5], line=line, column=index+1)
    return FiveCharacterMatcher()


def test_None_returns_empty():
    scanner = Scanner(matcher=None)
    results = scanner.scan(None)
    assert list(results) == []


def test_empty_returns_empty():
    scanner = Scanner(matcher=None)
    results = scanner.scan([])
    assert list(results) == []


def test_LexError(errorRaisingMatcher):
    scanner = Scanner(errorRaisingMatcher)
    oneLineWithError = parseLines('''\
blah blah
''')
    result = list(scanner.scan(oneLineWithError))
    assertLexErrors(result, lineNumber=1, startColumn=1)


def test_LexError_at_start_goes_through_whole_line_one_character_at_a_time(errorRaisingMatcher):
    scanner = Scanner(errorRaisingMatcher)
    twoLinesWithErrors = parseLines('''\
0123456789
0123456789
''')
    scanner = Scanner(errorRaisingMatcher)
    results = list(scanner.scan(twoLinesWithErrors))
    assertLexErrors(results[0:11], lineNumber=1, startColumn=1)
    assertLexErrors(results[11:], lineNumber=2, startColumn=1)


def test_LexError_in_middle_of_a_line(tabSkipMatcher):
    twoLines = parseLines('''\
\terrors\tmore
''')
    scanner = Scanner(tabSkipMatcher)
    results = list(scanner.scan(twoLines))
    assert isinstance(results[0], Skip)
    assertLexErrors(results[1:7], lineNumber=1, startColumn=2)
    assert isinstance(results[7], Skip)
    assertLexErrors(results[8:], lineNumber=1, startColumn=9)

def test_can_match_multiple_tokens(fiveCharacterMatcher):
    lines = parseLines('''\
12345123451234512345
1234512345
''')
    scanner = Scanner(fiveCharacterMatcher)
    results = list(scanner.scan(lines))
    assert len(results) == 8


def test_scanner_does_not_hang_on_zero_length_skip():
    spec_str = r"skip WS '\s*'" + "\n" + r"token NUM '\d+'"
    spec, _ = parseSpec(spec_str)
    m = matcherModule.Matcher(spec.lexical.ruleList)
    scanner = Scanner(m)
    lines = parseLines("2\n")
    results = list(scanner.scan(lines))
    tokens = [r for r in results if isinstance(r, Token)]
    assert len(tokens) == 1
    assert tokens[0].name == "NUM"
    assert tokens[0].lexeme == "2"


from ..spec.lexical.TokenRule import TokenRule
from ..spec.lexical.SkipRule import SkipRule
from .BlockOpened import BlockOpened
from .UnclosedBlockError import UnclosedBlockError


def test_block_token_single_line():
    """Open and close on the same line emits one Token with content between delimiters."""
    rule = TokenRule(line=None, name='BODY', pattern=r'<<<', close_pattern=r'>>>')
    scanner = Scanner(matcher=makeMatcher([rule]))
    lines = parseLines('<<<hello>>>')
    results = list(scanner.scan(lines))
    assert len(results) == 1
    assert isinstance(results[0], Token)
    assert results[0].name == 'BODY'
    assert results[0].lexeme == 'hello'


def test_block_token_multi_line():
    """Content spanning multiple lines is collected into a single Token."""
    rule = TokenRule(line=None, name='BODY', pattern=r'<<<', close_pattern=r'>>>')
    scanner = Scanner(matcher=makeMatcher([rule]))
    lines = parseLines('<<<line1\nline2\n>>>')
    results = list(scanner.scan(lines))
    assert len(results) == 1
    assert isinstance(results[0], Token)
    assert results[0].lexeme == 'line1\nline2\n'


def test_block_token_open_line_column():
    """Token carries the opening delimiter's line and column."""
    rule = TokenRule(line=None, name='BODY', pattern=r'<<<', close_pattern=r'>>>')
    other = TokenRule(line=None, name='WORD', pattern=r'\w+')
    scanner = Scanner(matcher=makeMatcher([rule, other]))
    lines = parseLines('abc<<<stuff>>>')
    results = list(scanner.scan(lines))
    block_tok = next(r for r in results if r.name == 'BODY')
    assert block_tok.column == 4   # '<<<' starts at column 4


def test_block_skip_emits_Skip():
    """A block skip emits a Skip, not a Token."""
    rule = SkipRule(line=None, name='COMMENT', pattern=r'/\*', close_pattern=r'\*/')
    scanner = Scanner(matcher=makeMatcher([rule]))
    lines = parseLines('/* hello */')
    results = list(scanner.scan(lines))
    assert len(results) == 1
    assert isinstance(results[0], Skip)
    assert results[0].name == 'COMMENT'
    assert results[0].lexeme == ' hello '


def test_block_token_tail_of_close_line_scanned():
    """Content after the close delimiter on the same line is scanned normally."""
    rule = TokenRule(line=None, name='BODY', pattern=r'<<<', close_pattern=r'>>>')
    num = TokenRule(line=None, name='NUM', pattern=r'\d+')
    ws = SkipRule(line=None, name='WS', pattern=r'\s+')
    scanner = Scanner(matcher=makeMatcher([rule, num, ws]))
    lines = parseLines('<<<stuff>>> 42\n')
    results = [r for r in scanner.scan(lines) if not isinstance(r, Skip)]
    assert len(results) == 2
    assert results[0].name == 'BODY'
    assert results[1].name == 'NUM'
    assert results[1].lexeme == '42'


def test_unclosed_block_emits_UnclosedBlockError():
    """EOF before the close delimiter yields an UnclosedBlockError."""
    rule = TokenRule(line=None, name='BODY', pattern=r'<<<', close_pattern=r'>>>')
    scanner = Scanner(matcher=makeMatcher([rule]))
    lines = parseLines('<<<no close here\n')
    results = list(scanner.scan(lines))
    assert len(results) == 1
    assert isinstance(results[0], UnclosedBlockError)
    assert results[0].column == 1


def test_block_token_multi_line_no_doubled_newlines():
    """Regression for issue-061: file-style lines (string includes \\n) must not produce doubled newlines in the lexeme."""
    from ..lines.parse_from_strings import parse_from_strings
    rule = TokenRule(line=None, name='BODY', pattern=r'<<<', close_pattern=r'>>>')
    ws = SkipRule(line=None, name='WS', pattern=r'\s+')
    scanner = Scanner(matcher=makeMatcher([rule, ws]))
    lines = list(parse_from_strings(['<<<line1\n', 'line2\n', '>>>\n']))
    body_tokens = [r for r in scanner.scan(lines) if isinstance(r, Token) and r.name == 'BODY']
    assert len(body_tokens) == 1
    assert body_tokens[0].lexeme == 'line1\nline2\n'


def test_newline_token_rule_matches_line_endings():
    """token NEWLINE '\\n' can match each line ending when Line.string includes the trailing newline."""
    from ..lines.parse_from_strings import parse_from_strings
    nl_rule = TokenRule(line=None, name='NL', pattern=r'\n')
    word_rule = TokenRule(line=None, name='WORD', pattern=r'\w+')
    scanner = Scanner(matcher=makeMatcher([nl_rule, word_rule]))
    lines = list(parse_from_strings(['hello\n', 'world\n']))
    results = list(scanner.scan(lines))
    token_names = [r.name for r in results if isinstance(r, Token)]
    assert token_names == ['WORD', 'NL', 'WORD', 'NL']


def makeMatcher(rules):
    from .matcher import Matcher
    return Matcher(rules)


def assertLexErrors(results, lineNumber, startColumn):
    c = startColumn
    for r in results:
        assertLexErrorAtLineNumberAndColumn(r, lineNumber, c)
        c += 1


def assertLexErrorAtLineNumberAndColumn(result, lineNumber, column):
    assert isinstance(result, LexError)
    assert result.line.number == lineNumber
    assert result.column == column
