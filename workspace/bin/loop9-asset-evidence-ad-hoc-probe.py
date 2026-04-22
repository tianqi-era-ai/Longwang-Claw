#!/usr/bin/env python3
import argparse
import base64
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional


# Personal local-use defaults requested by the user.
# Intentionally NOT committed to git history unless the user explicitly asks.
DEFAULT_FOFA_KEY = "17a769fba461f167271e33ae95313663"
DEFAULT_HUNTER_API_KEY = "90245b4b52e0da12bd26da228b61103621ae66be2403281cbf83ed17f732dac4"
DEFAULT_SHODAN_KEY = "PlfpBbn7mI1u3Yp8sPeAQy9kfOfxPeYs"

DEFAULT_HUNTER_FIELDS = "url,web_title,company,number,component,updated_at"
DEFAULT_FOFA_FIELDS = "host,ip,title,server,port,domain"
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
HISTORY_CASES_PATH = WORKSPACE_ROOT / "skills" / "loop9-asset-evidence" / "references" / "history-cases.md"


def jprint(obj: Dict[str, Any]) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def http_get(url: str, params: Dict[str, Any], timeout: int = 20) -> Dict[str, Any]:
    query = urllib.parse.urlencode(params)
    final_url = f"{url}?{query}"
    req = urllib.request.Request(final_url, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8", errors="replace")
        return {
            "http_status": getattr(resp, "status", None),
            "body": body,
            "url": final_url,
        }


def resolve_secret(env_name: str, default_value: Optional[str]) -> Optional[str]:
    return os.environ.get(env_name) or default_value


def cmd_hunter(args: argparse.Namespace) -> int:
    api_key = resolve_secret(args.api_key_env, DEFAULT_HUNTER_API_KEY)
    if not api_key:
        jprint({
            "status": "blocked",
            "provider": "hunter",
            "reason": f"missing env {args.api_key_env} and no default configured",
            "query": args.query,
        })
        return 2

    search = base64.urlsafe_b64encode(args.query.encode("utf-8")).decode("ascii")
    params = {
        "api-key": api_key,
        "search": search,
        "page": args.page,
        "page_size": args.page_size,
        "is_web": args.is_web,
        "fields": args.fields or DEFAULT_HUNTER_FIELDS,
    }
    try:
        out = http_get("https://hunter.qianxin.com/openApi/search", params, timeout=args.timeout)
        data = json.loads(out["body"])
        arr = (((data or {}).get("data") or {}).get("arr") or [])[: args.preview]
        jprint({
            "status": "ok",
            "provider": "hunter",
            "query": args.query,
            "http_status": out["http_status"],
            "total": ((data or {}).get("data") or {}).get("total"),
            "consume_quota": ((data or {}).get("data") or {}).get("consume_quota"),
            "rest_quota": ((data or {}).get("data") or {}).get("rest_quota"),
            "preview": arr,
        })
        return 0
    except Exception as e:
        jprint({
            "status": "error",
            "provider": "hunter",
            "query": args.query,
            "reason": str(e),
        })
        return 1


def cmd_fofa_info(args: argparse.Namespace) -> int:
    key = resolve_secret(args.key_env, DEFAULT_FOFA_KEY)
    if not key:
        jprint({
            "status": "blocked",
            "provider": "fofa",
            "reason": f"missing env {args.key_env} and no default configured",
        })
        return 2
    try:
        out = http_get("https://fofa.info/api/v1/info/my", {"key": key}, timeout=args.timeout)
        data = json.loads(out["body"])
        jprint({
            "status": "ok",
            "provider": "fofa",
            "http_status": out["http_status"],
            "email": data.get("email"),
            "username": data.get("username"),
            "isvip": data.get("isvip"),
            "fofa_point": data.get("fofa_point"),
        })
        return 0
    except Exception as e:
        jprint({
            "status": "error",
            "provider": "fofa",
            "reason": str(e),
        })
        return 1


def cmd_fofa_stats(args: argparse.Namespace) -> int:
    key = resolve_secret(args.key_env, DEFAULT_FOFA_KEY)
    if not key:
        jprint({
            "status": "blocked",
            "provider": "fofa",
            "reason": f"missing env {args.key_env} and no default configured",
            "query": args.query,
        })
        return 2
    qbase64 = base64.b64encode(args.query.encode("utf-8")).decode("ascii")
    try:
        out = http_get("https://fofa.info/api/v1/search/stats", {"key": key, "qbase64": qbase64}, timeout=args.timeout)
        data = json.loads(out["body"])
        size = data.get("size")
        if size is None and isinstance(data.get("data"), dict):
            size = data["data"].get("size")
        jprint({
            "status": "ok",
            "provider": "fofa",
            "query": args.query,
            "http_status": out["http_status"],
            "size": size,
            "raw_keys": sorted(list(data.keys())),
        })
        return 0
    except Exception as e:
        jprint({
            "status": "error",
            "provider": "fofa",
            "query": args.query,
            "reason": str(e),
        })
        return 1


def cmd_fofa_sample(args: argparse.Namespace) -> int:
    key = resolve_secret(args.key_env, DEFAULT_FOFA_KEY)
    if not key:
        jprint({
            "status": "blocked",
            "provider": "fofa",
            "reason": f"missing env {args.key_env} and no default configured",
            "query": args.query,
        })
        return 2
    qbase64 = base64.b64encode(args.query.encode("utf-8")).decode("ascii")
    try:
        out = http_get(
            "https://fofa.info/api/v1/search/all",
            {"key": key, "qbase64": qbase64, "size": args.size, "fields": args.fields or DEFAULT_FOFA_FIELDS},
            timeout=args.timeout,
        )
        data = json.loads(out["body"])
        results = data.get("results")
        if results is None and isinstance(data.get("data"), dict):
            results = data["data"].get("results")
        jprint({
            "status": "ok",
            "provider": "fofa",
            "query": args.query,
            "http_status": out["http_status"],
            "size": args.size,
            "results": results,
        })
        return 0
    except Exception as e:
        jprint({
            "status": "error",
            "provider": "fofa",
            "query": args.query,
            "reason": str(e),
        })
        return 1


def _extract_field(raw: str, label: str) -> str:
    match = re.search(rf'^- {re.escape(label)}：(.*)$', raw, re.MULTILINE)
    if not match:
        return ''
    value = match.group(1).strip()
    if value.startswith('`') and value.endswith('`') and len(value) >= 2:
        value = value[1:-1]
    return value.strip()


def _parse_history_sections(text: str) -> tuple[str, list[dict[str, str]]]:
    pattern = re.compile(r'^## 案例 \d+：', re.MULTILINE)
    matches = list(pattern.finditer(text))
    if not matches:
        return text.rstrip() + "\n", []
    intro = text[:matches[0].start()].rstrip() + "\n\n"
    sections: list[dict[str, str]] = []
    for idx, match in enumerate(matches):
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        raw = text[start:end].strip() + "\n"
        title_match = re.match(r'^## 案例 \d+：(.+)$', raw.splitlines()[0])
        sections.append({
            'title': title_match.group(1).strip() if title_match else '',
            'product_name': _extract_field(raw, '产品名'),
            'repo_url': _extract_field(raw, '仓库地址'),
            'api_counts': _extract_field(raw, 'API 数量'),
            'gaps': _extract_field(raw, '还差/为 0'),
            'rating': _extract_field(raw, '当前评级'),
            'product_attr': _extract_field(raw, '属性'),
            'coverage_status': _extract_field(raw, '覆盖状态'),
        })
    return intro, sections


def _render_history_section(index: int, *, title: str, product_name: str, repo_url: str, api_counts: str, gaps: str, rating: str, product_attr: str, coverage_status: str) -> str:
    return (
        f"## 案例 {index}：{title}\n"
        f"- 产品名：`{product_name}`\n"
        f"- 仓库地址：`{repo_url}`\n"
        f"- API 数量：`{api_counts}`\n"
        f"- 还差/为 0：`{gaps}`\n"
        f"- 当前评级：`{rating}`\n"
        f"- 属性：`{product_attr}`\n"
        f"- 覆盖状态：`{coverage_status}`\n"
    )


def cmd_history_upsert(args: argparse.Namespace) -> int:
    path = Path(args.path or HISTORY_CASES_PATH).expanduser()
    if not path.exists():
        jprint({'status': 'error', 'reason': f'history-cases not found: {path}'})
        return 1

    text = path.read_text(encoding='utf-8')
    intro, sections = _parse_history_sections(text)
    title = (args.case_title or args.product_name).strip()
    new_section = {
        'title': title,
        'product_name': args.product_name.strip(),
        'repo_url': args.repo_url.strip(),
        'api_counts': args.api_counts.strip(),
        'gaps': args.gaps.strip(),
        'rating': args.rating.strip(),
        'product_attr': args.product_attr.strip(),
        'coverage_status': args.coverage_status.strip(),
    }

    target_index: Optional[int] = None
    for idx, section in enumerate(sections):
        if new_section['repo_url'] and section['repo_url'] == new_section['repo_url']:
            target_index = idx
            break
        if section['product_name'] == new_section['product_name']:
            target_index = idx
            break
        if section['title'] == title:
            target_index = idx
            break

    action = 'inserted'
    if target_index is None:
        sections.append(new_section)
    else:
        action = 'updated'
        sections[target_index] = new_section

    rendered_sections = [
        _render_history_section(
            idx,
            title=section['title'],
            product_name=section['product_name'],
            repo_url=section['repo_url'],
            api_counts=section['api_counts'],
            gaps=section['gaps'],
            rating=section['rating'],
            product_attr=section['product_attr'],
            coverage_status=section['coverage_status'],
        ).rstrip()
        for idx, section in enumerate(sections, start=1)
    ]

    output = intro + "\n\n".join(rendered_sections).rstrip() + "\n"
    path.write_text(output, encoding='utf-8')
    jprint({
        'status': 'ok',
        'action': action,
        'path': str(path),
        'title': title,
        'repo_url': new_section['repo_url'],
    })
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Thin ad-hoc asset evidence probe runner")
    sub = p.add_subparsers(dest="cmd", required=True)

    ph = sub.add_parser("hunter-query")
    ph.add_argument("--query", required=True)
    ph.add_argument("--api-key-env", default="HUNTER_API_KEY")
    ph.add_argument("--page", type=int, default=1)
    ph.add_argument("--page-size", type=int, default=10)
    ph.add_argument("--is-web", type=int, default=1)
    ph.add_argument("--fields", default=DEFAULT_HUNTER_FIELDS)
    ph.add_argument("--preview", type=int, default=3)
    ph.add_argument("--timeout", type=int, default=20)
    ph.set_defaults(func=cmd_hunter)

    pfi = sub.add_parser("fofa-info")
    pfi.add_argument("--key-env", default="FOFA_KEY")
    pfi.add_argument("--timeout", type=int, default=20)
    pfi.set_defaults(func=cmd_fofa_info)

    pfs = sub.add_parser("fofa-stats")
    pfs.add_argument("--query", required=True)
    pfs.add_argument("--key-env", default="FOFA_KEY")
    pfs.add_argument("--timeout", type=int, default=20)
    pfs.add_argument("--retries", type=int, default=2)
    pfs.add_argument("--retry-delay", type=int, default=20)
    pfs.set_defaults(func=cmd_fofa_stats)

    pfa = sub.add_parser("fofa-sample")
    pfa.add_argument("--query", required=True)
    pfa.add_argument("--key-env", default="FOFA_KEY")
    pfa.add_argument("--size", type=int, default=5)
    pfa.add_argument("--fields", default=DEFAULT_FOFA_FIELDS)
    pfa.add_argument("--timeout", type=int, default=20)
    pfa.add_argument("--retries", type=int, default=2)
    pfa.add_argument("--retry-delay", type=int, default=20)
    pfa.set_defaults(func=cmd_fofa_sample)

    phu = sub.add_parser("history-upsert")
    phu.add_argument("--product-name", required=True)
    phu.add_argument("--repo-url", required=True)
    phu.add_argument("--api-counts", required=True)
    phu.add_argument("--gaps", required=True)
    phu.add_argument("--rating", required=True)
    phu.add_argument("--product-attr", required=True)
    phu.add_argument("--coverage-status", required=True)
    phu.add_argument("--case-title")
    phu.add_argument("--path")
    phu.set_defaults(func=cmd_history_upsert)

    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
