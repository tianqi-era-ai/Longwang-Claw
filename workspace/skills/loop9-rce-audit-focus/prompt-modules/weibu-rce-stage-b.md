6、当审计过程中出现以下强信号时，应考虑调用 `loop9-rce-audit-focus` 做专题深挖，并增量更新 `RCE专题共享上下文.md`：
- 上传 / 导入导出 / 远程文件抓取
- 模板 / 主题 / email-template / preview / render / compile / expression
- webhook / callback / test connection / scheduler / hook / plugin / package
- JWT / SSO / auth-provider / user-source / config
- 自注册后可达后台能力
- guest / editor / support / marketing 等低权限角色接近高价值功能面
- 越权 / 弱鉴权 / 权限模型异常，与执行面存在连接可能

注意：
- 这里限制的是“强信号阶段”这一类调用场景，不是只能调用一次
- 如果强信号连续出现，可以多次跟进
- 当线索质量足够高时，允许投入较多时间和 token 成本
- 重点不是扩大噪声，而是把高价值链路压实
