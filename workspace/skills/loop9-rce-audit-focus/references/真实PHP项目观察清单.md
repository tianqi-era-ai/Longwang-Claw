# 真实 PHP 项目观察清单

> 用途：当 `loop9-rce-audit-focus` 在真实 PHP 项目中启用 `scripts/rce_regex_scan.py --language php` 时，用这份清单记录它的真实表现。
>
> 目标不是立刻继续改脚本，而是先沉淀：哪些命中更像真实 RCE 成链信号，哪些命中更像生态噪音，哪些项目类型会天然抬高某些关键词的存在感。

---

# 已有观察记录

## 观察样本 1：gibbon
- 项目类型：学校管理 / 教育平台
- 结果：
  - 初版：`1180 / 2639`（44.7%）
  - 去掉 `include/require` 后：`261 / 2638`（9.9%）
- 主要结论：
  - `include/require` 在 PHP 项目里会把扫描器迅速打成“全仓命中器”，不适合作为默认高召回词。
  - 去掉后仍能保留 `Twig`、`$_FILES`、`unserialize()`、`ZipArchive`、`exec()` 等更像样的信号。

## 观察样本 2：freescout
- 项目类型：helpdesk / shared mailbox
- 结果：
  - 初版：`213 / 809`（26.3%）
  - 收紧后：`141 / 805`（17.5%）
- 主要结论：
  - `call_user_func*`、`__toString()`、模板/框架词仍然很多，但文件处理、`phar`、`shell_exec()` 等信号也保留下来。
  - 说明脚本不能只抓模板，也确实能抓到反序列化/执行邻接面。

## 观察样本 3：opencart
- 项目类型：电商
- 结果：`46 / 1884`（2.4%）
- 主要结论：
  - 命中率较低，整体偏干净。
  - 保留下来的多是 `Twig`、`unserialize()`、`ZipArchive`、`move_uploaded_file()`、`pathinfo()` 这类更像真实专题输入层的词。

## 观察样本 4：phpmyadmin
- 项目类型：数据库管理后台
- 结果：
  - 第一轮：`348 / 1527`（22.8%）
  - 去掉 `__invoke()` + 给 `exec(` 加 `(?<!->)(?<!::)` 保护后：`151 / 1527`（9.9%）
- 主要结论：
  - `__invoke()` 在现代 PHP 项目中过于泛滥，默认纳入高召回层收益低于噪音成本。
  - `exec(` 若不避开 `PDO::exec()` / `->exec()` / `::exec()`，会制造大量误报。

## 观察样本 5：matomo
- 项目类型：analytics / self-hosted platform
- 结果：`425 / 3709`（11.5%）
- 主要结论：
  - `Twig`、`exec()`、`shell_exec()`、`passthru()`、`unserialize()`、`$_FILES` 都有存在感。
  - 说明脚本对“模板面 + 命令执行邻接面”是有感知的。

## 观察样本 6：zentaopms
- 项目类型：项目管理 / PM 系统
- 结果：
  - 第一轮：`457 / 13007`（3.5%）
  - 收紧后：`169 / 13007`（1.3%）
- 主要结论：
  - 典型噪音来源是 `PDO::exec()` 类方法调用。
  - 修正后，保留下来的 `$_FILES`、`unserialize()`、`system()`、`move_uploaded_file()`、`pathinfo()` 更接近真实专题输入。

## 观察样本 7：processwire
- 项目类型：CMS / framework-ish CMS
- 结果：
  - 第一轮：`111 / 478`（23.2%）
  - 收紧后：`83 / 478`（17.4%）
- 主要结论：
  - 仍然偏高，但高值文件更聚焦在上传、文件处理、图片处理、模板与核心类周围。
  - 这种项目说明：即使比例偏高，也不一定是坏事，关键要看命中聚类是不是落在真实高价值模块上。

## 观察样本 8：mediawiki
- 项目类型：wiki / content platform
- 结果：`314 / 5480`（5.7%）
- 主要结论：
  - `unserialize()`、`php://`、`$_FILES`、`Mustache`、`__toString()` 都存在。
  - 整体属于可继续人工读的中低噪音项目。

## 观察样本 9：moodle
- 项目类型：LMS / 教育平台
- 结果：`1013 / 49968`（2.0%）
- 主要结论：
  - 绝对命中数大，但相对比例不高。
  - `mustache`、`call_user_func*`、`assert()`、`unserialize()` 等会频繁出现，说明大型 PHP 项目里“低比例但高总量”是正常现象。

## 观察样本 10：suitecrm
- 项目类型：CRM
- 结果：`508 / 5255`（9.7%）
- 主要结论：
  - `smarty` / `Smarty` 非常高频，模板生态信号强。
  - 同时保留了 `unserialize()`、`$_FILES`、`eval()`、`pathinfo()` 等推进面与执行邻接面。

## 观察样本 11：uvdesk
- 项目类型：helpdesk
- 结果：`6 / 44`（13.6%）
- 主要结论：
  - 样本本身很小，不适合拿比例做太强结论。
  - 但 `Twig` + `Symfony\\Component\\Process\\Process` 的组合说明，脚本可以抓到模板生态与命令执行相关类名。

## 观察样本 12：phpbb
- 项目类型：论坛
- 结果：`152 / 1959`（7.8%）
- 主要结论：
  - 以 `Twig`、`unserialize()`、`call_user_func_array()` 为主。
  - 属于模板生态 + 反序列化邻接比较典型的样本。

## 观察样本 13：ojs
- 项目类型：期刊管理 / 教育出版
- 结果：`61 / 624`（9.8%）
- 主要结论：
  - `assert()` 在该项目里很显眼，需要后续人工判断是否属于测试/断言语义还是实际执行风险点。
  - `smarty` 与 `unserialize()` 同时存在，具有一定专题价值。

## 观察样本 14：osTicket
- 项目类型：helpdesk
- 结果：`125 / 823`（15.2%）
- 主要结论：
  - 很好的“文件处理链”样本。
  - 代表性文件如 `include/class.file.php`，同时出现 `is_uploaded_file()`、`getimagesize()`、`imagecreatefromstring()`、`finfo_file()`。
  - 还出现 `php://`、`unserialize()`、`ZipArchive`，说明该项目适合从上传/文件/归档推进面继续专题深挖。

## 观察样本 15：orangehrm
- 项目类型：HRM
- 结果：`35 / 3190`（1.1%）
- 主要结论：
  - 当前较干净。
  - 保留下来的主要是 `Twig`、`Process` 类、少量 `exec()` / `phar` / `pathinfo()`。

## 观察样本 16：openemr
- 项目类型：医疗信息系统 / EMR
- 结果：`1531 / 4782`（32.0%）
- 主要结论：
  - 绝对值很高，但深读后确认：
    - 部分命中被 `.phpstan` baseline / 静态分析辅助文件放大
    - `Twig` / `Smarty` / `__toString()` 的生态词占比很高
  - 因此它更像“有真实模板与文件处理面，但统计被工具/生态词放大”的样本，不能直接拿高命中率当高风险证明。

## 观察样本 17：prestashop
- 项目类型：电商
- 结果：`985 / 8584`（11.5%）
- 主要结论：
  - 是当前最能说明脚本方向正确的典型样本之一。
  - `Twig`、`Smarty`、`createTemplate()`、`$_FILES`、`move_uploaded_file()`、`pathinfo()`、`getimagesize()` 都集中出现在真实业务代码里。
  - 很适合作为“模板/模块/helper/uploader 形成 RCE 专题输入层”的代表项目。

---

## 当前阶段性结论

### 1. 当前更像真实专题信号的词类
- 模板生态：`Twig`、`Smarty`、`Mustache`、`createTemplate()`
- 上传与文件处理：`$_FILES`、`move_uploaded_file()`、`is_uploaded_file()`、`pathinfo()`、`getimagesize()`、`finfo_file()`
- 反序列化 / wrapper / 归档：`unserialize()`、`php://`、`phar`、`ZipArchive`
- 直达执行 / 邻接执行：`shell_exec()`、`system()`、`proc_open()`、`new Process()`、`Symfony\\Component\\Process\\Process`

### 2. 当前确认过的高噪音词/模式
- `include` / `require`
  - 已从默认规则中移除
- `__invoke()`
  - 已从默认规则中移除
- 未区分方法调用的 `exec(`
  - 已通过 `(?<!->)(?<!::)` 做保护

### 3. 当前仍要谨慎解释、但不建议粗暴删除的词
- `__toString()`
- `call_user_func()` / `call_user_func_array()`
- `twig` / `smarty` / `mustache`
- `assert()`

原因：
- 它们在某些项目中确实会带来明显噪音
- 但它们同时也是模板执行面、gadget、间接调用链的重要早期信号
- 更适合通过“项目类型 + 命中聚类 + 人工解释”来消化，而不是继续简单删词

### 4. 当前总体判断
- 这版 PHP 扫描器已经不只是“能跑”
- 已经过多轮真实项目验证
- 已能较稳定地抓到：
  - 模板/渲染面
  - 上传/文件处理面
  - 反序列化/包处理邻接面
  - 部分直达执行与命令执行类信号
- 它已经具备作为 **Loop9 RCE 专题辅助输入层** 的可用性
- 但它仍然是：
  - **高召回辅助检索层**
  - 不是漏洞结论层

---

## 后续建议
- 若继续调优，优先观察：
  - 是否默认排除更多静态分析/基线目录（如 `.phpstan`）
  - 是否需要对 `assert()` 做更细粒度限定
  - 是否需要为模板生态单独做“存在感词”与“执行入口词”的区分
- 若进入实战使用阶段，则优先把它和：
  - `RCE专题共享上下文.md`
  - 模板 / 上传 / 配置 / 文件处理链的专题推理
  结合起来用，而不是只看 matched_file_count。
