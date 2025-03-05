from plccng.spec.lexical.LexicalParser import LexicalParser


def parse_from_lines_without_validation(lines):
    return LexicalParser(lines).parseLexicalSpec()
