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

module.exports = { Node, Token };
