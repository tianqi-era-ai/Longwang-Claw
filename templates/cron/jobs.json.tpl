{
  "version": 1,
  "jobs": [
    {
      "agentId": {{json:cron.defaultAgentId}},
      "sessionKey": {{json:cron.defaultSessionKey}},
      "name": {{json:cron.jobs.publish.name}},
      "enabled": {{json:cron.enabled}},
      "schedule": {
        "kind": "cron",
        "expr": {{json:cron.jobs.publish.expr}},
        "tz": {{json:cron.timezone}}
      },
      "sessionTarget": "isolated",
      "wakeMode": "now",
      "payload": {
        "kind": "agentTurn",
        "message": "读取 {{raw:cron.jobs.publish.promptFile}}，严格按其中流程运行一次。若没有可执行候选，输出具体原因和情况。",
        "model": {{json:cron.jobs.publish.model}},
        "thinking": {{json:cron.jobs.publish.thinking}},
        "timeoutSeconds": {{json:cron.jobs.publish.timeoutSeconds}}
      },
      "delivery": {
        "mode": {{json:cron.delivery.mode}},
        "channel": {{json:cron.delivery.channel}},
        "to": {{json:cron.delivery.publishTo}}
      }
    },
    {
      "agentId": {{json:cron.defaultAgentId}},
      "sessionKey": {{json:cron.defaultSessionKey}},
      "name": {{json:cron.jobs.audit.name}},
      "enabled": {{json:cron.enabled}},
      "schedule": {
        "kind": "cron",
        "expr": {{json:cron.jobs.audit.expr}},
        "tz": {{json:cron.timezone}}
      },
      "sessionTarget": "isolated",
      "wakeMode": "now",
      "payload": {
        "kind": "agentTurn",
        "message": "读取 {{raw:cron.jobs.audit.promptFile}}，严格按其中流程运行一次。若没有可执行候选，输出具体原因和情况。",
        "model": {{json:cron.jobs.audit.model}},
        "thinking": {{json:cron.jobs.audit.thinking}},
        "timeoutSeconds": {{json:cron.jobs.audit.timeoutSeconds}}
      },
      "delivery": {
        "mode": {{json:cron.delivery.mode}},
        "channel": {{json:cron.delivery.channel}},
        "to": {{json:cron.delivery.auditTo}}
      }
    },
    {
      "agentId": {{json:cron.defaultAgentId}},
      "sessionKey": {{json:cron.defaultSessionKey}},
      "name": {{json:cron.jobs.realPoc.name}},
      "enabled": {{json:cron.enabled}},
      "schedule": {
        "kind": "cron",
        "expr": {{json:cron.jobs.realPoc.expr}},
        "tz": {{json:cron.timezone}}
      },
      "sessionTarget": "isolated",
      "wakeMode": "now",
      "payload": {
        "kind": "agentTurn",
        "message": "读取 {{raw:cron.jobs.realPoc.promptFile}}，严格按其中流程运行一次。若没有可执行候选，输出具体原因和情况。",
        "model": {{json:cron.jobs.realPoc.model}},
        "thinking": {{json:cron.jobs.realPoc.thinking}},
        "timeoutSeconds": {{json:cron.jobs.realPoc.timeoutSeconds}}
      },
      "delivery": {
        "mode": {{json:cron.delivery.mode}},
        "channel": {{json:cron.delivery.channel}},
        "to": {{json:cron.delivery.pocTo}}
      }
    },
    {
      "agentId": {{json:cron.feishuAgentId}},
      "sessionKey": {{json:cron.feishuSessionKey}},
      "name": {{json:cron.jobs.deliveryReportPublisher.name}},
      "enabled": {{json:cron.enabled}},
      "schedule": {
        "kind": "cron",
        "expr": {{json:cron.jobs.deliveryReportPublisher.expr}},
        "tz": {{json:cron.timezone}}
      },
      "sessionTarget": "isolated",
      "wakeMode": "now",
      "payload": {
        "kind": "agentTurn",
        "message": "读取 {{raw:cron.jobs.deliveryReportPublisher.promptFile}}，严格按其中流程运行一次。不要自行发送 Telegram/Feishu；让 cron delivery 负责发送最终状态。",
        "model": {{json:cron.jobs.deliveryReportPublisher.model}},
        "thinking": {{json:cron.jobs.deliveryReportPublisher.thinking}},
        "timeoutSeconds": {{json:cron.jobs.deliveryReportPublisher.timeoutSeconds}}
      },
      "delivery": {
        "mode": {{json:cron.delivery.mode}},
        "channel": {{json:cron.delivery.channel}},
        "to": {{json:cron.delivery.deliveryPublishTo}},
        "bestEffort": false
      }
    },
    {
      "agentId": {{json:cron.feishuAgentId}},
      "sessionKey": {{json:cron.feishuSessionKey}},
      "name": {{json:cron.jobs.verifyV4AutoRunner.name}},
      "description": "Run loop9-verify-v4-auto-run.sh hourly through isolated OpenClaw cron agentTurn; script owns prompt/lock/log behavior.",
      "enabled": {{json:cron.enabled}},
      "schedule": {
        "kind": "cron",
        "expr": {{json:cron.jobs.verifyV4AutoRunner.expr}},
        "tz": {{json:cron.timezone}},
        "staggerMs": 0
      },
      "sessionTarget": "isolated",
      "wakeMode": "now",
      "payload": {
        "kind": "agentTurn",
        "message": "读取 {{raw:cron.jobs.verifyV4AutoRunner.promptFile}}，严格按其中流程运行一次。不要自行发送 Telegram/Feishu；让 cron delivery 负责发送最终状态。",
        "model": {{json:cron.jobs.verifyV4AutoRunner.model}},
        "thinking": {{json:cron.jobs.verifyV4AutoRunner.thinking}},
        "timeoutSeconds": {{json:cron.jobs.verifyV4AutoRunner.timeoutSeconds}}
      },
      "delivery": {
        "mode": {{json:cron.delivery.mode}},
        "channel": {{json:cron.delivery.channel}},
        "to": {{json:cron.delivery.verifyTo}},
        "bestEffort": false
      }
    }
  ]
}
