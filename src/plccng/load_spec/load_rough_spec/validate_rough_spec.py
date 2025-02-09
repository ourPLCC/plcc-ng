from ..errors import ValidationError
from ..structs import Block


def validate_rough_spec(roughSpec):
    errorList = []
    errorList.extend(check_no_blocks_in_lexicalSection(roughSpec))
    errorList.extend(check_no_blocks_in_syntacticSection(roughSpec))
    return errorList


def check_no_blocks_in_lexicalSection(roughSpec):
    errorList = []
    for i in roughSpec.lexicalSection:
        if isinstance(i, Block):
            m = f"The lexical section must not have a Block: {i.lines[0]}"
            errorList.append(ValidationError(line=i.lines[0], message=m))
    return errorList


def check_no_blocks_in_syntacticSection(roughSpec):
    errorList = []
    for i in roughSpec.syntacticSection:
        if isinstance(i, Block):
            m = f"The syntactic section must not have a Block: {i.lines[0]}"
            errorList.append(ValidationError(line=i.lines[0], message=m))
    return errorList
