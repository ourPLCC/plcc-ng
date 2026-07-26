# Haskell 2010 Report §2.4 reserved identifiers. The generated .cabal
# file pins `default-language: Haskell2010` (see _write_cabal in
# emit.py), so GHC-extension-only keywords (mdo, family, forall, ...)
# are deliberately excluded.
RESERVED_WORDS = frozenset({
    'case', 'class', 'data', 'default', 'deriving', 'do', 'else',
    'foreign', 'if', 'import', 'in', 'infix', 'infixl', 'infixr',
    'instance', 'let', 'module', 'newtype', 'of', 'then', 'type',
    'where', '_',
})
