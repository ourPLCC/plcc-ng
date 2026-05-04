package runtime;

import java.util.*;

public class Registry {
    private final Map<String, Map<Set<String>, Class<? extends Node>>> byRule = new HashMap<>();

    public void register(Class<?>... classes) throws Exception {
        for (Class<?> cls : classes) {
            String ruleName = (String) cls.getField("_RULE_NAME").get(null);
            String[] fieldsArr = (String[]) cls.getField("_FIELDS").get(null);
            Set<String> fieldSet = new HashSet<>(Arrays.asList(fieldsArr));
            byRule.computeIfAbsent(ruleName, k -> new HashMap<>())
                  .put(fieldSet, cls.asSubclass(Node.class));
        }
    }

    public Class<? extends Node> lookup(String ruleName, Set<String> fieldNames) {
        Map<Set<String>, Class<? extends Node>> candidates = byRule.get(ruleName);
        if (candidates == null)
            throw new RuntimeException("No class registered for rule '" + ruleName + "'");
        Class<? extends Node> cls = candidates.get(fieldNames);
        if (cls == null)
            throw new RuntimeException(
                "No class for rule '" + ruleName + "' with fields " + fieldNames);
        return cls;
    }
}
