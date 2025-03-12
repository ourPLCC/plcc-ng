from . import validate
from .parse_from_lines_without_validation import parse_from_lines_without_validation


def parse_from_lines(lines):
    rough_ = parse_from_lines_without_validation(lines)
    errors = validate.lexvalidate(rough_)
    return rough_, errors
