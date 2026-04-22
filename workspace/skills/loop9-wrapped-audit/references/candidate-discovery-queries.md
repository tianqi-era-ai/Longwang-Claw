# 候选发现查询模板（weibu-submission）

## 目的

为主动目标发现模式提供一组**薄、可替换**的查询模板。

注意：
- 这里不是最终决策器
- 这里只负责帮助产出“候选 URL / 仓库名”
- 当前主轴不再是“默认去 GitHub 上找 common web app”
- 后续仍要进入候选事实核对与最终收敛阶段

## 当前优先顺序

1. 微步已列好的项目/范围
2. Gitee
3. GitCode（防镜像误伤）
4. GitHub 例外通道

## 四类来源对应的查询思路

### 1. 微步已列好的项目/范围

使用方式：
- 先把微步给出的项目名、范围、关键词整理成候选 URL 或仓库名
- 再标准化成 `weibu-listed` 来源候选

### 2. Gitee（主战场）

优先找：
- 厂商/公司官方组织
- 中国大陆常见 CMS / OA / 常见 WEB 应用 / 管理系统 / 协同系统
- 有官网、文档、厂商品牌痕迹的项目

示例查询模板（按需改写）：
- `site:gitee.com 企业 OA 开源`
- `site:gitee.com CMS 开源 中国`
- `site:gitee.com 项目管理 开源 企业`
- `site:gitee.com 客服系统 开源 企业`
- `site:gitee.com ERP CRM 开源 中国`

### 3. GitCode（次选）

使用方式：
- 作为补充来源
- 默认要额外检查是否只是 GitHub 镜像
- 如果镜像味道很重，不要因为表面 star/活跃度就直接纳入主候选

示例查询模板（按需改写）：
- `site:gitcode.com 企业 OA 开源`
- `site:gitcode.com CMS 开源 中国`
- `site:gitcode.com 厂商 开源 管理系统`

### 4. GitHub 例外通道

只搜索这几类：
- 微步明确点名
- 国内大量使用的通用组件
- 海外项目但中国大陆政府/国企/大厂实际使用很多

示例查询模板（按需改写）：
- `site:github.com apache shiro framework security`
- `site:github.com 中国 大量使用 开源 CMS OA`
- `site:github.com government enterprise china self-hosted app`

## 当前阶段的建议

- 每轮不要铺太大面
- 先收集少量候选 URL / 仓库名
- 先过业务口径，再谈 stars / 活跃度
- 目标是最后只留下 **1 个** 合适仓库

## 重要澄清：查询层不负责最终准入

不要把查询关键词里的“热门 / 常见 / stars”之类词语，当成最终事实判断。

最终准入至少还要确认：

- 是否符合中国大陆使用导向
- 是否属于公司/厂商项目，还是个人项目
- `stars` 是否满足：公司/厂商 `>=1000`，个人 `>=1500`
- 是否非本地已处理 / 已在跑
- 是否非靶场
- GitHub 候选是否属于窄例外通道
- GitCode 候选是否存在明显镜像风险
