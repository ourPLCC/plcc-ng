package runtime;

public class LanguageError extends RuntimeException {
    public LanguageError(String message) {
        super(message);
    }
}
