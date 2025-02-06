
from plccng.load_spec.errors import ValidationError

from ..structs import Divider
from ..structs import Block
from ..structs import RoughSpec


def validate_rough_spec(rough_spec:RoughSpec):
    errorList = []
    errorList.extend(check_no_blocks_in_lexicalSection(rough_spec))
    errorList.extend(check_no_blocks_in_syntacticSection(rough_spec))
    return errorList


def check_no_blocks_in_lexicalSection(rough_spec:RoughSpec):
    errorList = []
    for i in rough_spec.lexicalSection:
        if isinstance(i, Block):
            m = f"The lexical section must not have a Block: {i.lines[0]}"
            errorList.append(ValidationError(line=i.lines[0], message=m))
    return errorList


def check_no_blocks_in_syntacticSection(rough_spec:RoughSpec):
    errorList = []
    for i in rough_spec.syntacticSection:
        if isinstance(i, Block):
            m = f"The syntactic section must not have a Block: {i.lines[0]}"
            errorList.append(ValidationError(line=i.lines[0], message=m))
    return errorList
