from .LexicalSpec import LexicalSpec
from .LexicalRule import LexicalRule
from .validations import (
    DuplicateRuleName,
    InvalidRuleName,
    InvalidRulePattern,
    InvalidRule,
)
from .parse_lexical_spec import from_string
from .parse_lexical_spec import from_lines
