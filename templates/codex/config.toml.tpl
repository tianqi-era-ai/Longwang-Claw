model_provider = {{toml:models.codex.provider}}
model = {{toml:models.codex.model}}
service_tier = {{toml:models.codex.serviceTier}}
model_reasoning_effort = {{toml:models.codex.reasoningEffort}}
disable_response_storage = {{toml:codex.disableResponseStorage}}

[model_providers.{{raw:models.codex.provider}}]
name = {{toml:models.providers.openai.name}}
base_url = {{toml:models.providers.openai.baseUrl}}
env_key = {{toml:models.providers.openai.apiKeyEnv}}
wire_api = "responses"
requires_openai_auth = false

[projects.{{toml:paths.openclawRoot}}]
trust_level = "trusted"

[projects.{{toml:paths.workspaceRoot}}]
trust_level = "trusted"

[projects.{{toml:paths.super8Root}}]
trust_level = "trusted"

[features]
unified_exec = true
fast_mode = false

[mcp_servers.filesystem]
type = "stdio"
command = "npx"
args = ["-y", "@modelcontextprotocol/server-filesystem", {{toml:paths.workspaceRoot}}]
