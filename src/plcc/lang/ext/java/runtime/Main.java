import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class Main {
    private static final Pattern KIND_PATTERN = Pattern.compile("\"kind\"\\s*:\\s*\"([^\"]+)\"");
    private static final Pattern RULE_PATTERN = Pattern.compile("\"rule\"\\s*:\\s*\"([^\"]+)\"");

    public static void main(String[] args) throws Exception {
        BufferedReader reader = new BufferedReader(new InputStreamReader(System.in));
        String line;
        while ((line = reader.readLine()) != null) {
            line = line.trim();
            if (line.isEmpty()) continue;
            String kind = extract(KIND_PATTERN, line, "unknown");
            String rule = extract(RULE_PATTERN, line, "unknown");
            System.out.println("evaluated: " + rule + " (" + kind + ")");
            System.out.flush();
        }
    }

    private static String extract(Pattern p, String s, String def) {
        Matcher m = p.matcher(s);
        return m.find() ? m.group(1) : def;
    }
}
