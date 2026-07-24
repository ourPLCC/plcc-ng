# ECMA-262 keywords, plus the words reserved in strict mode (generated
# JavaScript class bodies are always strict), including `eval` and `arguments`
# which are illegal as formal parameter names, and the `enum` future-reserved word.
RESERVED_WORDS = frozenset({
    'arguments', 'break', 'case', 'catch', 'class', 'const', 'continue', 'debugger',
    'default', 'delete', 'do', 'else', 'enum', 'eval', 'export', 'extends',
    'false', 'finally', 'for', 'function', 'if', 'implements', 'import',
    'in', 'instanceof', 'interface', 'let', 'new', 'null', 'package',
    'private', 'protected', 'public', 'return', 'static', 'super',
    'switch', 'this', 'throw', 'true', 'try', 'typeof', 'var', 'void',
    'while', 'with', 'yield',
})
