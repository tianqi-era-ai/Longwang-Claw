const fs = require('node:fs');
const path = require('node:path');

function readDefaultModelFromConfig(cfg) {
  const model = cfg?.agents?.defaults?.model;
  if (typeof model === 'string') return model.trim() || undefined;
  if (model && typeof model === 'object' && typeof model.primary === 'string') {
    return model.primary.trim() || undefined;
  }
  return undefined;
}

function describeConfiguredDefaultModel(cfg) {
  const primary = readDefaultModelFromConfig(cfg) || '(unset)';
  return [
    '# RUNTIME_DEFAULT_MODEL.md',
    '',
    '- Deterministic bootstrap note: this file is injected by a local `agent:bootstrap` hook.',
    `- Current configured default model: \`${primary}\``,
    '- Source of truth: `agents.defaults.model.primary` in the active OpenClaw config.',
    '- If runtime model differs from this value, treat this injected value as the current config-backed default model.',
    ''
  ].join('\n');
}

module.exports = async function injectRuntimeDefaultModel(event) {
  if (!event || event.type !== 'agent' || event.action !== 'bootstrap') return;

  const cfg = event.context?.cfg;
  const workspaceDir = event.context?.workspaceDir;
  const bootstrapFiles = event.context?.bootstrapFiles;
  if (!cfg || !workspaceDir || !Array.isArray(bootstrapFiles)) return;

  const syntheticPath = path.join(workspaceDir, '.openclaw-generated', 'RUNTIME_DEFAULT_MODEL.md');
  const content = describeConfiguredDefaultModel(cfg);

  try {
    fs.mkdirSync(path.dirname(syntheticPath), { recursive: true });
    fs.writeFileSync(syntheticPath, content, 'utf8');
  } catch {
    // If writing fails, still inject the synthetic content directly.
  }

  const next = bootstrapFiles.filter((file) => file?.path !== syntheticPath);
  next.push({
    name: 'RUNTIME_DEFAULT_MODEL.md',
    path: syntheticPath,
    content
  });
  event.context.bootstrapFiles = next;
};
