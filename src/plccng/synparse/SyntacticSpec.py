from dataclasses import dataclass


@dataclass
class SyntacticSpec(list):
    nonTerminals: set[str]
    def __init__(self, rules=None ):
        if rules: super().__init__(rules)
        self.nonTerminals = set()

    def getNonTerminals(self):
        if len(self.nonTerminals) > 0:
            return self.nonTerminals
        for rule in self:
            self.nonTerminals.add(rule.lhs.name)
        return self.nonTerminals
    pass
