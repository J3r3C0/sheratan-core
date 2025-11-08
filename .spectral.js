module.exports = {
  extends: ['spectral:oas'],
  formats: ['oas3'],
  functions: {
    has2xx: (targetVal) => {
      if (!targetVal || typeof targetVal !== 'object') {
        return [{ message: 'responses object missing' }];
      }
      const ok = Object.keys(targetVal).some((k) => /^(2\\d\\d|2XX)$/i.test(k));
      return ok ? [] : [{ message: 'At least one 2xx response is required.' }];
    },
  },
  rules: {
    "openapi-version-3": {
      given: "$.openapi",
      severity: "error",
      then: { function: "pattern", functionOptions: { match: "^3\\." } }
    },
    "info-title-required": {
      given: "$.info.title",
      severity: "error",
      then: { function: "truthy" }
    },
    "info-version-required": {
      given: "$.info.version",
      severity: "error",
      then: { function: "truthy" }
    },
    "op-summary-required": {
      description: "Each operation should have a summary.",
      given: "$.paths[*][*]",
      severity: "warn",
      then: { field: "summary", function: "truthy" }
    },
    "op-tags-min-one": {
      description: "Each operation should have at least one tag.",
      given: "$.paths[*][*]",
      severity: "warn",
      then: {
        field: "tags",
        function: "schema",
        functionOptions: { schema: { type: "array", minItems: 1 } }
      }
    },
    "op-has-2xx-response": {
      description: "Operations should define at least one 2xx response.",
      given: "$.paths[*][*].responses",
      severity: "warn",
      then: { function: "has2xx" }
    },
    "metrics-plaintext-ok": {
      given: "$.paths['/metrics'].get.responses['200'].content['text/plain'].schema.type",
      severity: "off",
      then: { function: "truthy" }
    }
  }
};
