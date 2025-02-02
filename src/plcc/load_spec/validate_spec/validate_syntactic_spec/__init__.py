from ...errors import InvalidLhsAltNameError, InvalidLhsNameError, ValidationError
from ...structs import Divider, Include, Line, SyntacticRule, SyntacticSpec
from .validate_syntactic_spec import validate_syntactic_spec

from ...parse_spec.parse_syntactic_spec import (
    parse_syntactic_spec,
)

from ...errors import (
    DuplicateLhsError,
)
from ...load_rough_spec.parse_lines import parse_lines
from ...load_rough_spec.parse_includes import parse_includes
from ...load_rough_spec.parse_dividers import parse_dividers
from ...load_rough_spec.parse_rough import parse_rough
