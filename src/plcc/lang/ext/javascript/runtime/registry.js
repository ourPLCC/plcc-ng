class Registry {
    constructor() {
        this._byRule = {};
    }

    register(...classes) {
        for (const cls of classes) {
            const ruleName = cls._RULE_NAME;
            const key = JSON.stringify([...cls._FIELDS].sort());
            if (!this._byRule[ruleName]) {
                this._byRule[ruleName] = {};
            }
            this._byRule[ruleName][key] = cls;
        }
    }

    lookup(ruleName, fieldNames) {
        const candidates = this._byRule[ruleName];
        if (!candidates) {
            throw new Error(`No class registered for rule '${ruleName}'`);
        }
        const key = JSON.stringify([...fieldNames].sort());
        const cls = candidates[key];
        if (!cls) {
            throw new Error(`No class for rule '${ruleName}' with fields [${[...fieldNames].join(', ')}]`);
        }
        return cls;
    }
}

module.exports = { Registry };
