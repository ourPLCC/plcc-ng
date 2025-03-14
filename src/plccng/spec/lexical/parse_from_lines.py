from .Parser import Parser

def parse_from_lines(lines):
    return Parser().parseLexicalSpec(lines)
