# JLS 3.9 "reserved words": keywords plus the true/false/null reserved
# literals. `var` is deliberately excluded — it's a reserved *type name*
# only in local-variable-type-inference contexts, not in a field
# declaration (how field.name is used in class_file.java.jinja).
RESERVED_WORDS = frozenset({
    'abstract', 'assert', 'boolean', 'break', 'byte', 'case', 'catch',
    'char', 'class', 'const', 'continue', 'default', 'do', 'double',
    'else', 'enum', 'extends', 'false', 'final', 'finally', 'float',
    'for', 'goto', 'if', 'implements', 'import', 'instanceof', 'int',
    'interface', 'long', 'native', 'new', 'null', 'package', 'private',
    'protected', 'public', 'return', 'short', 'static', 'strictfp',
    'super', 'switch', 'synchronized', 'this', 'throw', 'throws',
    'transient', 'true', 'try', 'void', 'volatile', 'while',
})
