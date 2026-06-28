class Node {}

class Token {
    constructor(kind, lexeme) {
        this.kind = kind;
        this.lexeme = lexeme;
    }

    toString() {
        return this.lexeme;
    }
}

class LanguageError extends Error {
    constructor(message) {
        super(message);
        this.name = 'LanguageError';
    }
}

module.exports = { Node, Token, LanguageError };
