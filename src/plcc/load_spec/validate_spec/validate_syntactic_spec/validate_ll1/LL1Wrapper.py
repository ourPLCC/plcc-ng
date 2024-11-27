def wrap_ll1(name: str, spec_object: object):
    return LL1Wrapper(name, spec_object)

class LL1Wrapper:
    def __init__(self, name: str, specObject: object):
        self.name = name
        self.specObject = specObject

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, LL1Wrapper):
            return False
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def __repr__(self) -> str:
        return f"LL1Wrapper({self.name}, {self.specObject})"
