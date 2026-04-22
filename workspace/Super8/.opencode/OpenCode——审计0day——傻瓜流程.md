# 1、提示词文件
优先直接使用 wrapper 自动生成 prompt。

如果你确实要手工写 prompt 文件，也可以自己准备一份本地 markdown 文件，再把它路径传给 `/loop9`。

## 模板填充

### 必填
填充你存放【源码项目】的本地绝对路径即可。

### 选填
其它的【项目特征】等等，可填、可不填。（不填，就把对应段落删掉。）

# 2、原生启动命令

启动 opencode，在 `Super8` 项目目录下输入：
`/loop9 请参照 '<你写好的提示词的位置>'`

# 3、更稳定的一键入口（推荐）

如果你已经有一个本地待审计项目路径，可以直接执行：

```bash
./.opencode/_scripts/loop9_authorized_review.py '<本地项目路径>'
```

这个脚本默认会自动：
1. 基于仓库内模板生成 prompt 文件
2. 自动填入目标项目名和绝对路径
3. 在 `Super8` 目录启动 OpenCode，并直接指定 `loop9-controller`

默认生成的 prompt 文件位置：
`./temp/loop9-prompts/<target>-<timestamp>.md`

## 4、两种启动模式

### 模式 A：command 默认模式（推荐）

```bash
./.opencode/_scripts/loop9_authorized_review.py '<本地项目路径>'
```

走 `opencode run --command loop9 --agent loop9-controller`，作为当前最稳的默认路径。

当前 command 分支会显式要求：
- 先读取任务文件
- 把文件内容当作唯一任务规格
- 不要先总结
- 不要先反问
- 直接启动完整流程并落盘

### 模式 B：agent 保留模式（不推荐）

```bash
./.opencode/_scripts/loop9_authorized_review.py --mode agent '<本地项目路径>'
```

这个模式会直接走 `--agent loop9-controller` 路径。

当前经验判断是：
- agent 模式比 command 模式更不稳定
- 容易不遵从预设流程
- 甚至会自己跑偏，不走预期 Loop9 编排

因此它只作为保留/排查入口，不作为默认入口。

## 避免【Loop9相关Skill】的干扰

之前写过一个 Skill，但效果不佳；当前推荐直接按上面的命令 / 脚本走项目内 command + agents 链路。
