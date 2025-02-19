from ...errors import InvalidLhsAltNameError, InvalidLhsNameError, ValidationError
from ...structs import Divider, Include, Line, SyntacticRule, SyntacticSpec
from .validate_syntactic_spec import validate_syntactic_spec

from ...parse_spec.parse_syntactic_spec import (
    parse_syntactic_spec,
)

from ...errors import (
    DuplicateLhsError,
)
from ...parse_rough.parse_includes import parse_includes
from ...parse_rough.parse_dividers import parse_dividers
from ...parse_rough.parse_rough import from_string
