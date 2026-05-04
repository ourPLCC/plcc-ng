package runtime;

public class Token extends Node {
    public final String kind;
    public final String lexeme;

    public Token(String kind, String lexeme) {
        this.kind = kind;
        this.lexeme = lexeme;
    }

    @Override
    public String toString() {
        return lexeme;
    }
}
