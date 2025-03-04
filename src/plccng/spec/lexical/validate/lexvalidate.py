from ..LexicalSpec import LexicalSpec
from .check_for_duplicate_names import check_for_duplicate_names
from .check_for_unrecognized_lines import check_for_unrecognized_lines
from .check_format_of_names import check_format_of_names
from .check_format_of_patterns import check_format_of_patterns


def lexvalidate(lexicalSpec: LexicalSpec):
    if not lexicalSpec.ruleList:
        return []
    errors = []
    errors.extend(check_for_duplicate_names(lexicalSpec.ruleList))
    errors.extend(check_format_of_names(lexicalSpec.ruleList))
    errors.extend(check_format_of_patterns(lexicalSpec.ruleList))
    errors.extend(check_for_unrecognized_lines(lexicalSpec.ruleList))
    return errors
