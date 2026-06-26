from ..SpecError import SpecError


class InvalidClassNameError(SpecError):
    def __init__(self, line):
        super().__init__(
            line=line,
            column=1,
            message=(
                f"invalid class name '{line.string.strip()}' — "
                "must start with an uppercase letter followed by letters, digits, or underscores"
            ),
        )

    @property
    def hint(self):
        if self.line.string.strip().startswith('%%'):
            return "did you mean '%%%' instead of '%%{' or '%%}'?"
        return None
