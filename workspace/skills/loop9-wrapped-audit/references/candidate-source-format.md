# 候选来源格式（主动目标发现模式）

## 目的

统一承接多类候选来源，并把对微步新口径真正重要的事实字段显式带上。

后续发现链的第一步，不是直接决策，而是先把候选统一成同一种结构，再交给选择阶段。

## 推荐 JSON 数组格式

```json
[
  {
    "name": "zentao",
    "repo_url": "https://gitee.com/easysoft/zentaopms",
    "source_kind": "gitee-vendor",
    "source_platform": "gitee",
    "ownership_kind": "vendor",
    "project_type": "common-web",
    "language": "php",
    "vendor_name": "禅道",
    "vendor_domain": "www.zentao.net",
    "mainland_use_evidence": "中国大陆常见研发协同/项目管理软件",
    "overseas_exception_kind": "none",
    "mirror_risk": "low",
    "audit_roi": "medium-high",
    "notes": "optional free text"
  }
]
```

## 字段说明

- `name`：仓库/项目名（必填）
- `repo_url`：仓库 URL（强烈建议）
- `source_kind`：候选来源（必填）
  - `weibu-listed`
  - `gitee-vendor`
  - `gitee-user`
  - `gitcode-vendor`
  - `gitcode-user`
  - `github-exception`
  - `360-reference`
- `source_platform`：来源平台（必填）
  - `gitee`
  - `gitcode`
  - `github`
  - `other`
- `ownership_kind`：归属类型（强烈建议）
  - `vendor`
  - `company`
  - `personal`
  - `foundation`
  - `community`
- `project_type`：项目大类（可选）
  - `common-web`
  - `ics-web`
  - `network-web`
  - `other`
- `language`：主语言（可选）
- `vendor_name`：厂商/品牌名（可选但强烈建议）
- `vendor_domain`：官网/联系域名（可选但强烈建议）
- `mainland_use_evidence`：为何认为它更符合中国大陆使用导向（强烈建议）
- `overseas_exception_kind`：海外例外类型（若不是海外例外则填 `none`）
  - `none`
  - `weibu-listed`
  - `widely-used-component-in-china`
  - `widely-used-foreign-product-in-china`
- `mirror_risk`：镜像风险（GitCode 尤其重要）
  - `low`
  - `medium`
  - `high`
- `audit_roi`：审计性价比粗分（可选）
  - `high`
  - `medium-high`
  - `medium`
  - `low`
- `notes`：说明（可选）

## 当前阶段的使用方式

- 允许多个 JSON 文件分别代表不同来源
- 先 merge 成统一候选池
- 再进入选择阶段

## 当前边界

- 这一层只负责“候选标准化”
- 不负责最后选择
- 不负责下载
- 不负责发起审计
- 但它必须把“国内使用性 / 公司归属 / 海外例外 / 镜像风险 / 性价比”这些关键事实显式带出来
