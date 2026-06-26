from ..SpecError import SpecError


class UndefinedBlockError(SpecError):
    def __init__(self, line):
        super().__init__(
            line=line,
            column=1,
            message=(
                f"class name '{line.string.strip()}' must be "
                "immediately followed by '%%%' on the next line"
            ),
        )
