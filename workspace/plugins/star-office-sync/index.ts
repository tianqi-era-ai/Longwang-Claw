import fs from "node:fs/promises";
import { createWriteStream } from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawn } from "node:child_process";
import type { OpenClawPluginApi } from "openclaw/plugin-sdk/core";

type SyncConfig = {
  repoPath: string;
  stateFile: string;
  enabledForAgentIds: string[];
  minUpdateMs: number;
  backendPort: number;
  cloudflaredBin: string;
  busyDetail: string;
  idleDetail: string;
  researchingDetail: string;
  executingDetail: string;
  writingDetail: string;
  errorDetail: string;
};

type OfficeState = {
  state?: string;
  detail?: string;
  progress?: number;
  updated_at?: string;
  ttl_seconds?: number;
  [key: string]: unknown;
};

type ManagedProcessRecord = {
  pid?: number;
  url?: string;
  startedAt?: string;
  logFile?: string;
  kind?: string;
};

const DEFAULT_REPO_PATH = path.join(os.homedir(), "Documents", "Star-Office-UI");
const DEFAULT_ENABLED_AGENT_IDS = ["main"];
const RESEARCH_TOOLS = new Set(["web_search", "web_fetch", "browser"]);
const EXECUTE_TOOLS = new Set([
  "exec",
  "process",
  "sessions_spawn",
  "sessions_send",
  "subagents",
  "canvas",
  "nodes",
]);
const WRITE_TOOLS = new Set(["write", "edit"]);
const QUICK_TUNNEL_REGEX = /https:\/\/[a-z0-9-]+\.trycloudflare\.com/i;

const plugin = {
  id: "star-office-sync",
  name: "Star Office Sync",
  description: "Lightweight Star Office UI state sync for main-agent lifecycle and key tool phases.",
  register(api: OpenClawPluginApi) {
    const cfg = resolveConfig(api);
    const stateRoot = path.join(api.runtime.state.resolveStateDir(), "star-office-sync");
    const backendMetaFile = path.join(stateRoot, "backend.json");
    const tunnelMetaFile = path.join(stateRoot, "tunnel.json");
    const backendLogFile = path.join(stateRoot, "backend.log");
    const tunnelLogFile = path.join(stateRoot, "cloudflared.log");
    let writeChain = Promise.resolve();
    let lastWriteAt = 0;
    let lastState = "";
    let lastDetail = "";
    let warnedMissingPath = false;

    function shouldHandleAgent(agentId?: string): boolean {
      const allow = cfg.enabledForAgentIds;
      if (!allow.length) return true;
      const effective = (agentId ?? "main").trim() || "main";
      return allow.includes(effective);
    }

    function localBaseUrl(): string {
      return `http://127.0.0.1:${cfg.backendPort}`;
    }

    async function exists(filePath: string): Promise<boolean> {
      try {
        await fs.access(filePath);
        return true;
      } catch {
        return false;
      }
    }

    async function readJson<T>(filePath: string): Promise<T | null> {
      try {
        const raw = await fs.readFile(filePath, "utf8");
        return JSON.parse(raw) as T;
      } catch {
        return null;
      }
    }

    async function writeJson(filePath: string, value: unknown): Promise<void> {
      await fs.mkdir(path.dirname(filePath), { recursive: true });
      await fs.writeFile(filePath, `${JSON.stringify(value, null, 2)}\n`, "utf8");
    }

    function isPidAlive(pid?: number): boolean {
      if (!pid || !Number.isFinite(pid)) return false;
      try {
        process.kill(pid, 0);
        return true;
      } catch {
        return false;
      }
    }

    async function killPid(pid?: number): Promise<boolean> {
      if (!isPidAlive(pid)) return false;
      try {
        process.kill(pid!, "SIGTERM");
      } catch {
        return false;
      }
      for (let i = 0; i < 20; i += 1) {
        if (!isPidAlive(pid)) return true;
        await sleep(250);
      }
      try {
        process.kill(pid!, "SIGKILL");
      } catch {
        return !isPidAlive(pid);
      }
      return !isPidAlive(pid);
    }

    async function fetchHealth(): Promise<boolean> {
      try {
        const res = await fetch(`${localBaseUrl()}/health`, { signal: AbortSignal.timeout(2000) });
        return res.ok;
      } catch {
        return false;
      }
    }

    async function loadState(): Promise<OfficeState> {
      try {
        const raw = await fs.readFile(cfg.stateFile, "utf8");
        const parsed = JSON.parse(raw);
        return parsed && typeof parsed === "object" ? parsed : {};
      } catch {
        return {};
      }
    }

    async function writeState(nextState: string, detail: string): Promise<void> {
      const stateFileExists = await exists(cfg.stateFile);
      if (!stateFileExists) {
        if (!warnedMissingPath) {
          warnedMissingPath = true;
          api.logger.warn(`[star-office-sync] state file missing, skipping sync: ${cfg.stateFile}`);
        }
        return;
      }

      const current = await loadState();
      const now = Date.now();
      const currentState = typeof current.state === "string" ? current.state : "";
      const currentDetail = typeof current.detail === "string" ? current.detail : "";

      if (currentState === nextState && currentDetail === detail) {
        lastWriteAt = now;
        lastState = nextState;
        lastDetail = detail;
        return;
      }

      if (nextState === lastState && detail === lastDetail && now - lastWriteAt < cfg.minUpdateMs) {
        return;
      }

      const next: OfficeState = {
        ...current,
        state: nextState,
        detail,
        updated_at: new Date().toISOString(),
      };

      if (nextState === "idle") next.progress = 0;

      await fs.mkdir(path.dirname(cfg.stateFile), { recursive: true });
      await fs.writeFile(cfg.stateFile, `${JSON.stringify(next, null, 2)}\n`, "utf8");
      lastWriteAt = now;
      lastState = nextState;
      lastDetail = detail;
      api.logger.debug?.(`[star-office-sync] ${nextState} :: ${detail}`);
    }

    function queueState(nextState: string, detail: string): void {
      writeChain = writeChain.then(() => writeState(nextState, detail)).catch((err) => {
        api.logger.warn(`[star-office-sync] sync failed: ${String(err)}`);
      });
    }

    function classifyTool(toolName: string): { state: string; detail: string } | null {
      if (RESEARCH_TOOLS.has(toolName)) return { state: "researching", detail: cfg.researchingDetail };
      if (WRITE_TOOLS.has(toolName)) return { state: "writing", detail: cfg.writingDetail };
      if (EXECUTE_TOOLS.has(toolName)) return { state: "executing", detail: cfg.executingDetail };
      return null;
    }

    async function spawnDetached(command: string, args: string[], cwd: string, logFile: string): Promise<number> {
      await fs.mkdir(path.dirname(logFile), { recursive: true });
      await fs.writeFile(logFile, "", "utf8");
      const out = createWriteStream(logFile, { flags: "a" });
      const child = spawn(command, args, {
        cwd,
        detached: true,
        stdio: ["ignore", "pipe", "pipe"],
        env: process.env,
      });
      child.stdout?.pipe(out);
      child.stderr?.pipe(out);
      child.unref();
      return child.pid ?? 0;
    }

    async function ensureBackendStarted(forceRestart: boolean = false): Promise<{ ok: boolean; text: string }> {
      const current = await readJson<ManagedProcessRecord>(backendMetaFile);
      if (forceRestart && current?.pid) {
        await killPid(current.pid);
      }
      if (!forceRestart && (await fetchHealth())) {
        return { ok: true, text: `Star Office UI backend is running.\n${localBaseUrl()}` };
      }
      const runScript = path.join(cfg.repoPath, "backend", "run.sh");
      if (!(await exists(runScript))) {
        return { ok: false, text: `Backend launcher not found:\n${runScript}` };
      }
      const pid = await spawnDetached(runScript, [], cfg.repoPath, backendLogFile);
      await writeJson(backendMetaFile, {
        pid,
        startedAt: new Date().toISOString(),
        logFile: backendLogFile,
        kind: "backend",
      } satisfies ManagedProcessRecord);

      for (let i = 0; i < 16; i += 1) {
        if (await fetchHealth()) {
          return { ok: true, text: `✅ Star Office UI backend started.\n${localBaseUrl()}` };
        }
        await sleep(500);
      }

      return {
        ok: false,
        text:
          `Tried to start backend, but health check is still failing.\n` +
          `Local URL: ${localBaseUrl()}\n` +
          `Log: ${backendLogFile}`,
      };
    }

    async function extractQuickTunnelUrl(): Promise<string | null> {
      try {
        const raw = await fs.readFile(tunnelLogFile, "utf8");
        const match = raw.match(QUICK_TUNNEL_REGEX);
        return match?.[0] ?? null;
      } catch {
        return null;
      }
    }

    async function ensureTunnelStarted(forceRestart: boolean = false): Promise<{ ok: boolean; text: string }> {
      const backend = await ensureBackendStarted(false);
      if (!backend.ok) return backend;

      const current = await readJson<ManagedProcessRecord>(tunnelMetaFile);
      if (forceRestart && current?.pid) {
        await killPid(current.pid);
      }

      if (!forceRestart && current?.pid && isPidAlive(current.pid)) {
        const url = current.url || (await extractQuickTunnelUrl());
        if (url) {
          if (url !== current.url) {
            await writeJson(tunnelMetaFile, { ...current, url });
          }
          return {
            ok: true,
            text: `🌍 Cloudflare Tunnel is running.\nPublic URL: ${url}\nLocal URL: ${localBaseUrl()}`,
          };
        }
      }

      const pid = await spawnDetached(
        cfg.cloudflaredBin,
        ["tunnel", "--no-autoupdate", "--url", localBaseUrl()],
        cfg.repoPath,
        tunnelLogFile,
      );
      await writeJson(tunnelMetaFile, {
        pid,
        startedAt: new Date().toISOString(),
        logFile: tunnelLogFile,
        kind: "cloudflared",
      } satisfies ManagedProcessRecord);

      for (let i = 0; i < 30; i += 1) {
        const url = await extractQuickTunnelUrl();
        if (url) {
          await writeJson(tunnelMetaFile, {
            pid,
            url,
            startedAt: new Date().toISOString(),
            logFile: tunnelLogFile,
            kind: "cloudflared",
          } satisfies ManagedProcessRecord);
          return {
            ok: true,
            text:
              `✅ Cloudflare Tunnel started.\n` +
              `Public URL: ${url}\n` +
              `Local URL: ${localBaseUrl()}\n` +
              `Note: this is a temporary quick tunnel URL and may change after restart.`,
          };
        }
        await sleep(500);
      }

      return {
        ok: false,
        text:
          `Started cloudflared, but did not capture a public URL yet.\n` +
          `Log: ${tunnelLogFile}`,
      };
    }

    async function stopTunnel(): Promise<string> {
      const current = await readJson<ManagedProcessRecord>(tunnelMetaFile);
      if (!current?.pid || !isPidAlive(current.pid)) {
        return "Cloudflare Tunnel is already stopped.";
      }
      await killPid(current.pid);
      return "Cloudflare Tunnel stopped.";
    }

    async function officeStatus(): Promise<string> {
      const backendMeta = await readJson<ManagedProcessRecord>(backendMetaFile);
      const tunnelMeta = await readJson<ManagedProcessRecord>(tunnelMetaFile);
      const healthy = await fetchHealth();
      const publicUrl = tunnelMeta?.url || (await extractQuickTunnelUrl()) || "(none)";
      const backendStatus = healthy
        ? `backend: running (${localBaseUrl()})`
        : backendMeta?.pid && isPidAlive(backendMeta.pid)
          ? `backend: process alive but health check failing (${backendLogFile})`
          : "backend: stopped";
      const tunnelStatus = tunnelMeta?.pid && isPidAlive(tunnelMeta.pid)
        ? `tunnel: running (${publicUrl})`
        : "tunnel: stopped";
      return ["Star Office status:", `- ${backendStatus}`, `- ${tunnelStatus}`].join("\n");
    }

    api.on("before_agent_start", async (_event, ctx) => {
      if (!shouldHandleAgent(ctx.agentId)) return;
      queueState("executing", cfg.busyDetail);
    });

    api.on("before_tool_call", async (event, ctx) => {
      if (!shouldHandleAgent(ctx.agentId)) return;
      const next = classifyTool(event.toolName);
      if (!next) return;
      queueState(next.state, next.detail);
    });

    api.on("after_tool_call", async (event, ctx) => {
      if (!shouldHandleAgent(ctx.agentId)) return;
      if (!event.error) return;
      queueState("error", cfg.errorDetail);
    });

    api.on("agent_end", async (_event, ctx) => {
      if (!shouldHandleAgent(ctx.agentId)) return;
      queueState("idle", cfg.idleDetail);
    });

    api.on("before_reset", async (_event, ctx) => {
      if (!shouldHandleAgent(ctx.agentId)) return;
      queueState("idle", cfg.idleDetail);
    });

    api.registerCommand({
      name: "office",
      description: "Start/check Star Office UI and Cloudflare Tunnel from chat.",
      acceptsArgs: true,
      handler: async (ctx) => {
        const rawArgs = ctx.args?.trim() ?? "";
        const tokens = rawArgs.split(/\s+/).filter(Boolean);
        const action = (tokens[0] ?? "help").toLowerCase();
        const modifier = (tokens[1] ?? "").toLowerCase();

        if (action === "help") {
          return {
            text: [
              "Office commands:",
              "",
              "/office status  — 查看当前后端 / tunnel 状态",
              "/office start  — 启动 Star Office UI 后端",
              "/office start restart  — 重启后端",
              "/office tunnel  — 启动并返回 Cloudflare Tunnel 公网链接",
              "/office tunnel restart  — 重开一个新的公网链接",
              "/office tunnel stop  — 停止 tunnel",
            ].join("\n"),
          };
        }
        if (action === "status") {
          return { text: await officeStatus() };
        }
        if (action === "start") {
          const res = await ensureBackendStarted(modifier === "restart");
          return { text: res.text };
        }
        if (action === "tunnel") {
          if (modifier === "stop") return { text: await stopTunnel() };
          const res = await ensureTunnelStarted(modifier === "restart");
          return { text: res.text };
        }
        return {
          text: [
            "Office commands:",
            "",
            "/office status",
            "/office start",
            "/office start restart",
            "/office tunnel",
            "/office tunnel restart",
            "/office tunnel stop",
          ].join("\n"),
        };
      },
    });

    api.logger.info?.(`[star-office-sync] ready -> ${cfg.stateFile}`);
  },
};

function resolveConfig(api: OpenClawPluginApi): SyncConfig {
  const raw = (api.pluginConfig ?? {}) as Record<string, unknown>;
  const repoPath = asString(raw.repoPath) || DEFAULT_REPO_PATH;
  const stateFile = asString(raw.stateFile) || path.join(repoPath, "state.json");
  const enabledForAgentIds = Array.isArray(raw.enabledForAgentIds)
    ? raw.enabledForAgentIds.filter((v): v is string => typeof v === "string" && v.trim().length > 0)
    : DEFAULT_ENABLED_AGENT_IDS;

  return {
    repoPath,
    stateFile,
    enabledForAgentIds,
    minUpdateMs: asNumber(raw.minUpdateMs, 5000),
    backendPort: asNumber(raw.backendPort, 19000),
    cloudflaredBin: asString(raw.cloudflaredBin) || "cloudflared",
    busyDetail: asString(raw.busyDetail) || "正在处理任务",
    idleDetail: asString(raw.idleDetail) || "待命中",
    researchingDetail: asString(raw.researchingDetail) || "正在查阅资料",
    executingDetail: asString(raw.executingDetail) || "正在执行命令或任务",
    writingDetail: asString(raw.writingDetail) || "正在写入内容",
    errorDetail: asString(raw.errorDetail) || "刚刚遇到错误，正在恢复",
  };
}

function asString(value: unknown): string {
  return typeof value === "string" ? value.trim() : "";
}

function asNumber(value: unknown, fallback: number): number {
  return typeof value === "number" && Number.isFinite(value) ? value : fallback;
}

async function sleep(ms: number): Promise<void> {
  await new Promise((resolve) => setTimeout(resolve, ms));
}

export default plugin;
