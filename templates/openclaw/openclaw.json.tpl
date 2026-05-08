{
  "meta": {
    "profile": {{json:profileName}},
    "generatedBy": "LongWangClaw render_longwang_config.py"
  },
  "models": {
    "mode": "providers",
    "providers": {
      {{json:models.default.provider}}: {
        "api": "openai-compatible",
        "baseUrl": {{json:models.providers.openai.baseUrl}},
        "apiKey": {{json:models.providers.openai.apiKey}},
        "models": {{json:models.providers.openai.models}}
      }
    }
  },
  "agents": {
    "defaults": {
      "workspace": {{json:paths.workspaceRoot}},
      "model": {
        "primary": {{json:models.default.qualified}},
        "fallbacks": []
      },
      "thinkingDefault": {{json:models.default.thinking}},
      "timeoutSeconds": {{json:models.default.timeoutSeconds}},
      "maxConcurrent": {{json:openclaw.maxConcurrent}},
      "subagents": {
        "maxConcurrent": {{json:openclaw.subagentMaxConcurrent}},
        "model": {{json:models.default.qualified}},
        "thinking": {{json:models.default.thinking}}
      },
      "heartbeat": {
        "every": {{json:openclaw.heartbeat.every}},
        "target": {{json:openclaw.heartbeat.target}},
        "includeReasoning": {{json:openclaw.heartbeat.includeReasoning}}
      }
    },
    "list": [
      {
        "id": {{json:openclaw.agentId}},
        "model": {{json:models.default.qualified}}
      }
    ]
  },
  "channels": {
    "feishu": {
      "enabled": {{json:feishu.enabled}},
      "domain": {{json:feishu.domain}},
      "appId": {{json:feishu.appId}},
      "appSecret": {{json:feishu.appSecret}},
      "connectionMode": {{json:feishu.connectionMode}},
      "requireMention": {{json:feishu.requireMention}},
      "accounts": {{json:feishu.accounts}}
    },
    "telegram": {
      "enabled": {{json:telegram.enabled}},
      "botToken": {{json:telegram.botToken}},
      "groupPolicy": "allowlist",
      "groups": {
        {{json:telegram.announceChat}}: {
          "enabled": {{json:telegram.enabled}}
        }
      }
    }
  },
  "plugins": {
    "allow": [
      "openclaw-lark"
    ],
    "entries": {
      "openclaw-lark": {
        "enabled": true
      }
    },
    "load": {
      "paths": [
        "~/.openclaw/extensions/openclaw-lark"
      ]
    }
  },
  "hooks": {
    "internal": {
      "enabled": true,
      "handlers": [
        "~/.openclaw/workspace/hooks/handlers/inject-runtime-default-model.js"
      ]
    }
  },
  "gateway": {
    "mode": {{json:openclaw.gateway.mode}},
    "bind": {{json:openclaw.gateway.bind}},
    "port": {{json:openclaw.gateway.port}},
    "auth": {
      "mode": "token",
      "token": {{json:openclaw.gateway.authToken}}
    }
  },
  "commands": {
    "native": "enabled",
    "nativeSkills": "enabled",
    "restart": true
  },
  "tools": {
    "exec": {
      "security": "workspace",
      "ask": "on-demand"
    }
  },
  "skills": {
    "install": {
      "nodeManager": "npm"
    }
  }
}
