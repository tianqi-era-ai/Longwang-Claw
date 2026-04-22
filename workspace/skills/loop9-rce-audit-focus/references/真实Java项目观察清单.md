# 真实 Java 项目观察清单

> 用途：当 `loop9-rce-audit-focus` 在真实 Java/JVM 项目中启用 `scripts/rce_regex_scan.py --language java` 时，用这份清单观察其实际表现。
>
> 目标不是重新设计，而是收集真实反馈，判断后续是否只需微调文件范围策略。

---

# 已有观察记录

## 观察样本 1：RuoYi-official
- 项目类型：偏业务系统
- 命令：`python3 scripts/rce_regex_scan.py <repo> --language java --max-matches-per-file 5 --output json`
- 结果：
  - `scanned_file_count = 315`
  - `matched_file_count = 87`
- 后缀分布：
  - `.java = 79`
  - `.xml = 7`
  - `.yml = 1`
- 代表性命中：
  - `pom.xml` → `fastjson` / `jackson`
  - `ruoyi-quartz/pom.xml` → `quartz` / `定时任务`
  - `application.yml` → `jackson`
  - 若干 `.java` 文件 → `eval`
- 当前判断：
  - 可以用
  - 噪音存在，但在业务系统里相对可控
  - `.java` 仍然是最主要的有效承载
  - `pom.xml` / 少量配置文件提供的是线索，不应直接当风险结论

## 观察样本 2：apache-shiro
- 项目类型：偏安全框架 / 基础设施类项目
- 命令：`python3 scripts/rce_regex_scan.py <repo> --language java --max-matches-per-file 5 --output json`
- 结果：
  - `scanned_file_count = 1151`
  - `matched_file_count = 323`
- 后缀分布：
  - `.java = 257`
  - `.xml = 47`
  - `.groovy = 16`
  - `.yaml = 1`
  - `.yml = 1`
  - `.properties = 1`
- 代表性命中：
  - `.pre-commit-config.yaml` → `exec`
  - `pom.xml` / `core/pom.xml` → `quartz` / `exec` / `concurrent`
  - `.github/dependabot.yml` → `runtime`
  - `checkstyle.xml` → `Exec`
  - 若干 `.java` 文件 → `RUNTIME` / `concurrent`
- 当前判断：
  - 也能用，但噪音明显更高
  - 在框架型项目里，配置/构建/工具侧文件更容易产生“语义相关但不够值钱”的命中
  - 后续如果要微调，优先考虑收紧部分配置/工具文件的扫描权重或范围，而不是动长正则本体

## 当前阶段性结论
- Java 长正则扫描器已经在两个真实 Java 项目中验证可运行
- 结论进一步收敛为：
  - **高召回成立**
  - **框架型项目噪声更重**
  - 后续更值得观察的是“文件范围策略”，不是长正则本体

---

## 1. 基本记录
- 项目名：
- 仓库路径：
- 启动时间：
- 是否明显属于 Java/JVM 项目：
- 触发原因：
  - [ ] 早期轻量预扫
  - [ ] 强信号深挖
  - [ ] 其它：

---

## 2. 扫描输入
- 使用命令：
- `--limit-files`：
- `--max-matches-per-file`：
- 输出格式：

---

## 3. 噪音观察
- 扫描文件总数：
- 命中文件总数：
- 首眼判断：
  - [ ] 噪音偏低
  - [ ] 可接受
  - [ ] 偏高
  - [ ] 很高

### 哪些命中明显偏噪音
- 

### 哪些命中明显有价值
- 

---

## 4. 文件范围观察
### 当前最有价值的后缀/文件
- 

### 当前明显噪音较大的后缀/文件
- 

### 当前是否有值得新增的文件类型
- 

### 当前是否有值得排除的目录/文件类型
- 

---

## 5. 与主审计配合情况
- 是否帮助主审计更快聚焦高价值区域：
- 是否帮助形成成链假设：
- 是否帮助写 `RCE专题共享上下文.md`：
- 是否过于打断主审计节奏：

---

## 6. 结论
### 当前总体评价
- [ ] 值得保留当前策略
- [ ] 只需微调文件范围
- [ ] 需要明显收紧扫描范围
- [ ] 需要改变调用时机

### 下一步建议
- 
