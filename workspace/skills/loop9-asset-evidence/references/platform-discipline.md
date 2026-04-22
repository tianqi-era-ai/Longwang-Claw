# platform-discipline.md

## 目标

记录 Hunter / FOFA / Shodan 的低额度纪律、已验证坑点、以及必须保持的操作边界。

这个文件只负责程序侧、规则侧的精确部分；
不负责最终“这个目标值不值得做”的模糊判断。

---

## 总原则

1. 先统计
2. 再收敛指纹
3. 再极小样本验证
4. 最后沉淀证据卡

禁止：
- 一上来重翻多页
- 一上来导出全量明细
- 为了追求“更稳”而无节制增加请求

---

## Hunter

### 调用纪律
- 优先 `/openApi/search`
- `search` 使用 base64url
- `fields` 只取必要字段
- `page_size` 取平台允许的最小合法值
- 对正式价值判断，优先保留“最近一年”这一层；最近 3 个月过窄时，不要误把空结果当成真实弱信号

### 已验证经验
- `app.name` 不一定稳定
- 必要时切到：
  - `web.title`
  - `web.body`
  - 组件别名
- 高价值信号查询不要过早只锁死在 `县`
- 当前应保留一组更宽的 ICP/后缀补充面：
  - `icp.name="县"` / `icp.name="局"` / `icp.name="政"` / `icp.name="厅"` / `icp.name="国家"` / `icp.name="中国"` / `icp.name="人民"`
  - `icp.name="教育"` / `icp.name="学校"` / `icp.name="大学"` / `icp.name="学院"` / `icp.name="医院"` / `icp.name="人民政府"` / `icp.name="教育局"` / `icp.name="水务"`
  - `icp.type="政府"` / `(icp.type="政府" || icp.type="机关" || icp.type="事业单位")`
  - `icp.type!="企业" and (icp.type="政府" || icp.type="机关" || icp.type="事业单位")`
  - `icp.web_name="政府门户"` / `icp.web_name="集团"` / `icp.name="集团"`
  - `domain.suffix="gov.cn"` / `domain.suffix="edu.cn"`
  - FOFA `host=".gov.cn"` / `host=".edu.cn"` / `host=".org.cn"`
- 这些都首先是查询/筛选线索，不是脚本里的刚性评分器；命中的主体语境仍需模型判断
- 这里说的 `政 / 厅 / 国家 / 中国 / 人民`，应理解为 `icp.name="政"` 这类 ICP 字段查询，不是普通标题/正文词面命中

### 当前保留字段思路
初期常用字段：
- `url`
- `web_title`
- `company`
- `number`
- `component`
- `province`
- `city`
- `updated_at`
- `icp.name`
- `icp.type`
- `icp.web_name`

补充纪律：
- 不要只把“纯数字统计”交给 AI
- 对正式判断，必须保留少量可读样本，让 AI 看 ICP 单位名 / web_name / title / company 再做模糊判断
- Python 负责抓字段、裁剪样本、保存结果；AI 负责判断这些单位到底是政府/机关/事业单位/大型集团，还是普通企业噪音

---

## FOFA

### 调用纪律
- 优先先确认鉴权形态
- `stats` 优先
- 只有 `stats` 值得继续时，才做 `search/all size=5`
- 连续请求要显式节流，避免 429

### 已验证经验
- 当前机器上 key-only 可通
- `.gov.cn` 是非常有价值的政务域名补强技巧
- `search/all size=5` 是很好的极小样本补刀起点
- `app=` 不一定有现成规则，必要时切到：
  - `title=`
  - `body=`
  - `host=`
  - `server=`

### 必须保留的经验点
- `FOFA stats on .gov.cn`
- `FOFA search/all size=5` 作为最小明细验证

---

## Shodan

### 调用纪律
- `count` 优先
- 只在确有必要时取少量明细
- 在当前中国政务偏好路线中，它是补充平台，不是主证据平台

---

## 禁止事项

- 不把 API key 写入 skill 文件
- 不把平台逻辑膨胀成新的资产导出器
- 不让脚本接管最终模糊判断
- 不把“查询执行器”误当成“优先级判断器”

---

## 角色分工提醒

### 程序 / 脚本负责
- 编码
- 查询调用
- 字段裁剪
- 小样本获取
- 结果归档

### AI 负责
- 识别面切换判断
- 样本画像判断
- 强/中/弱信号判断
- 读取少量 ICP / 单位名 / 标题样本后做分流判断
- 判断 `县` / `政` / `厅` / `国家` / `中国` / `人民` / `集团` 这些 **ICP 字段命中** 到底是真高价值信号，还是仅仅企业/普通机构名称里的弱线索
- 最终保守优先级表达

一句话：

> 程序负责精确部分，AI 负责模糊部分；不要为了程序好写，就把判断层写死。
