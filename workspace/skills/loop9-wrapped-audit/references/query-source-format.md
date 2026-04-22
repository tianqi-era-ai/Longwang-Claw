# 查询来源格式（主动目标发现模式）

## 目的

为多平台主动发现提供稳定输入。

当前不再把这一层理解为“GitHub 搜索输入格式”，而是：
- 先表达要搜哪类来源
- 再表达平台偏好与归属偏好
- 最终服务于更符合微步潜规则的 discovery

## 推荐 JSON 数组格式

```json
[
  {
    "query": "企业 OA 开源 中国",
    "source_kind": "gitee-vendor",
    "source_platform": "gitee",
    "project_type": "common-web",
    "language": "php",
    "ownership_preference": "vendor",
    "limit": 10
  }
]
```

## 字段说明

- `query`：搜索查询（必填）
- `source_kind`：查询意图来源（必填）
  - `weibu-listed`
  - `gitee-vendor`
  - `gitee-user`
  - `gitcode-vendor`
  - `gitcode-user`
  - `github-exception`
  - `360-reference`
- `source_platform`：平台偏好（强烈建议）
  - `gitee`
  - `gitcode`
  - `github`
  - `mixed`
- `project_type`：可选，默认 `other`
- `language`：可选；会作为补充标签写入候选，而不是强制搜索条件
- `ownership_preference`：可选
  - `vendor`
  - `company`
  - `personal`
  - `mixed`
- `limit`：单条查询最多取多少结果，默认 10

## 当前边界

- 这一层只负责把“查询意图”喂给搜索层
- 不负责最终筛选
- 结果仍要进入候选事实核对与最终选择阶段

## 当前提醒

- 默认应先写 Gitee 查询，再写 GitCode 查询
- GitHub 查询默认只用于窄例外通道
- 不要在查询层就把“热门 / 常见 / 高星”误当成最终准入事实
