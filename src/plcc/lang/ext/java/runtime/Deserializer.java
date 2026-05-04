package runtime;

import org.json.*;
import java.lang.reflect.*;
import java.util.*;

public class Deserializer {
    private final Registry registry;

    public Deserializer(Registry registry) {
        this.registry = registry;
    }

    public Node deserialize(JSONObject tree) throws Exception {
        String kind = tree.getString("kind");
        if ("token".equals(kind)) {
            return new Token(tree.getString("name"), tree.getString("lexeme"));
        }
        String rule = tree.getString("rule");
        JSONArray children = tree.getJSONArray("children");
        Map<String, Object> fields = new LinkedHashMap<>();
        for (int i = 0; i < children.length(); i++) {
            JSONArray pair = children.getJSONArray(i);
            String name = pair.getString(0);
            fields.put(name, deserializeValue(pair.get(1)));
        }
        Class<? extends Node> cls = registry.lookup(rule, fields.keySet());
        Constructor<? extends Node> ctor = cls.getConstructor(Map.class);
        return ctor.newInstance(fields);
    }

    private Object deserializeValue(Object val) throws Exception {
        if (val instanceof JSONObject) {
            return deserialize((JSONObject) val);
        }
        if (val instanceof JSONArray) {
            JSONArray arr = (JSONArray) val;
            List<Object> list = new ArrayList<>();
            for (int i = 0; i < arr.length(); i++) {
                list.add(deserializeValue(arr.get(i)));
            }
            return list;
        }
        return val;
    }
}
