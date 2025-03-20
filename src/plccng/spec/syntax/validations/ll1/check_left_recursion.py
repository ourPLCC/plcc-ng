from collections import defaultdict

def check_left_recursion(grammar):
    return LeftRecursionChecker(grammar).check()
    
class LeftRecursionChecker:
    def __init__(self, grammar):
        self.grammar = grammar

    def check(self):
        return