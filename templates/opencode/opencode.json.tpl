{
  "$schema": {{json:opencode.schema}},
  "experimental": {
    "disable_paste_summary": {{json:opencode.disablePasteSummary}}
  },
  "plugin": {{json:opencode.plugins}},
  "provider": {
    {{json:models.default.provider}}: {
      "name": {{json:models.providers.openai.name}},
      "npm": "@ai-sdk/openai-compatible",
      "options": {
        "baseURL": {{json:models.providers.openai.baseUrl}},
        "apiKey": {{json:models.providers.openai.apiKey}}
      },
      "models": {
        {{json:models.default.model}}: {
          "name": {{json:models.default.model}},
          "limit": {
            "context": 200000,
            "output": 32000
          }
        },
        {{json:models.opencode.agentModel}}: {
          "name": {{json:models.default.model}},
          "limit": {
            "context": 200000,
            "output": 32000
          }
        }
      }
    }
  }
}
