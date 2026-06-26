from ..SpecError import SpecError


class UndefinedTargetLocatorError(SpecError):
    def __init__(self, line):
        super().__init__(
            line=line,
            column=1,
            message="'%%%' block has no preceding class name",
        )
