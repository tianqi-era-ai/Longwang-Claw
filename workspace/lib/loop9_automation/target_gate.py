from __future__ import annotations

import json
import re
import shutil
import subprocess
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

WEIBU_RECENCY_DAYS = 183
TARGET_METADATA_FILES = [
    '.openclaw-target-eligibility.json',
    '.loop9-target-eligibility.json',
]
ORIGIN_PATTERNS = [
    re.compile(r'^https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?/?$'),
    re.compile(r'^git@github\.com:(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?$'),
    re.compile(r'^https://gitee\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?/?$'),
    re.compile(r'^git@gitee\.com:(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?$'),
]
REMOTE_FACTS_TIMEOUT_SECONDS = 20
GITHUB_HTML_STAR_RE = re.compile(r'aria-label="([0-9][0-9,]*) users starred this repository"', re.I)
GITEE_HTML_STAR_RE = re.compile(r'action-social-count\s+"\s+title="([0-9][0-9,]*)"\s+href="/[^\"]+/stargazers"', re.I)


def _run_git(target_path: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ['git', *args],
        cwd=str(target_path),
        capture_output=True,
        text=True,
        check=False,
    )


def _git_head_commit_ts(target_path: Path) -> int | None:
    result = _run_git(target_path, ['log', '-1', '--format=%ct'])
    if result.returncode != 0:
        return None
    raw = result.stdout.strip()
    try:
        return int(raw)
    except Exception:
        return None


def _git_origin_url(target_path: Path) -> str | None:
    result = _run_git(target_path, ['remote', 'get-url', 'origin'])
    if result.returncode != 0:
        return None
    raw = result.stdout.strip()
    return raw or None


def _parse_iso_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith('Z'):
        text = text[:-1] + '+00:00'
    try:
        dt = datetime.fromisoformat(text)
    except Exception:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _parse_origin_repo(origin_url: str | None) -> dict[str, str] | None:
    if not origin_url:
        return None
    raw = origin_url.strip()
    for pattern in ORIGIN_PATTERNS:
        match = pattern.match(raw)
        if not match:
            continue
        owner = match.group('owner')
        repo = match.group('repo')
        provider = 'github' if 'github.com' in raw else 'gitee'
        return {
            'provider': provider,
            'owner': owner,
            'repo': repo,
        }
    return None


def _remote_api_url(repo_info: dict[str, str]) -> str:
    provider = repo_info['provider']
    owner = repo_info['owner']
    repo = repo_info['repo']
    if provider == 'github':
        return f'https://api.github.com/repos/{owner}/{repo}'
    if provider == 'gitee':
        return f'https://gitee.com/api/v5/repos/{owner}/{repo}'
    raise ValueError(f'unsupported provider: {provider}')


def _remote_html_url(repo_info: dict[str, str]) -> str:
    provider = repo_info['provider']
    owner = repo_info['owner']
    repo = repo_info['repo']
    if provider == 'github':
        return f'https://github.com/{owner}/{repo}'
    if provider == 'gitee':
        return f'https://gitee.com/{owner}/{repo}'
    raise ValueError(f'unsupported provider: {provider}')


def _normalize_remote_facts(repo_info: dict[str, str], payload: dict[str, Any], source: str) -> dict[str, Any]:
    owner = payload.get('owner') if isinstance(payload.get('owner'), dict) else {}
    return {
        'provider': repo_info['provider'],
        'owner': repo_info['owner'],
        'repo': repo_info['repo'],
        'source': source,
        'starCount': payload.get('stargazers_count') if payload.get('stargazers_count') is not None else payload.get('starCount'),
        'pushedAt': payload.get('pushed_at') if payload.get('pushed_at') is not None else payload.get('pushedAt'),
        'updatedAt': payload.get('updated_at') if payload.get('updated_at') is not None else payload.get('updatedAt'),
        'ownerType': owner.get('type') if owner else payload.get('ownerType'),
        'htmlUrl': payload.get('html_url') if payload.get('html_url') is not None else payload.get('htmlUrl'),
    }


def _fetch_github_repo_facts_via_gh(repo_info: dict[str, str]) -> tuple[dict[str, Any] | None, str | None]:
    gh_bin = shutil.which('gh')
    if not gh_bin:
        return None, 'gh-missing'
    try:
        completed = subprocess.run(
            [gh_bin, 'api', f'repos/{repo_info["owner"]}/{repo_info["repo"]}'],
            capture_output=True,
            text=True,
            timeout=REMOTE_FACTS_TIMEOUT_SECONDS,
            check=False,
        )
    except Exception as exc:
        return None, f'gh-api-failed:{exc.__class__.__name__}'
    if completed.returncode != 0:
        stderr = (completed.stderr or '').strip().splitlines()
        detail = stderr[-1] if stderr else f'code-{completed.returncode}'
        return None, f'gh-api-nonzero:{detail}'
    try:
        payload = json.loads(completed.stdout)
    except Exception:
        return None, 'gh-api-invalid-json'
    return _normalize_remote_facts(repo_info, payload, 'github-gh-api'), None


def _fetch_remote_repo_facts_via_api(repo_info: dict[str, str]) -> tuple[dict[str, Any] | None, str | None]:
    url = _remote_api_url(repo_info)
    request = urllib.request.Request(url, headers={'User-Agent': 'openclaw-loop9-target-gate'})
    try:
        with urllib.request.urlopen(request, timeout=REMOTE_FACTS_TIMEOUT_SECONDS) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        return None, f'remote-api-http-{exc.code}'
    except Exception as exc:
        return None, f'remote-api-failed:{exc.__class__.__name__}'
    facts = _normalize_remote_facts(repo_info, payload, f'{repo_info["provider"]}-public-api')
    facts['apiUrl'] = url
    return facts, None


def _fetch_remote_repo_facts_via_html(repo_info: dict[str, str]) -> tuple[dict[str, Any] | None, str | None]:
    url = _remote_html_url(repo_info)
    request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(request, timeout=REMOTE_FACTS_TIMEOUT_SECONDS) as response:
            html = response.read().decode('utf-8', errors='ignore')
    except urllib.error.HTTPError as exc:
        return None, f'remote-html-http-{exc.code}'
    except Exception as exc:
        return None, f'remote-html-failed:{exc.__class__.__name__}'

    if repo_info['provider'] == 'github':
        star_match = GITHUB_HTML_STAR_RE.search(html)
        star_count = int(star_match.group(1).replace(',', '')) if star_match else None
        facts = {
            'provider': 'github',
            'owner': repo_info['owner'],
            'repo': repo_info['repo'],
            'source': 'github-html',
            'starCount': star_count,
            'pushedAt': None,
            'updatedAt': None,
            'ownerType': None,
            'htmlUrl': url,
        }
        if star_count is None:
            return None, 'github-html-parse-miss'
        return facts, None

    if repo_info['provider'] == 'gitee':
        star_match = GITEE_HTML_STAR_RE.search(html)
        star_count = int(star_match.group(1).replace(',', '')) if star_match else None
        facts = {
            'provider': 'gitee',
            'owner': repo_info['owner'],
            'repo': repo_info['repo'],
            'source': 'gitee-html',
            'starCount': star_count,
            'pushedAt': None,
            'updatedAt': None,
            'ownerType': None,
            'htmlUrl': url,
        }
        if star_count is None:
            return None, 'gitee-html-parse-miss'
        return facts, None

    return None, 'unsupported-provider-html'


def _fetch_remote_repo_facts(origin_url: str | None) -> tuple[dict[str, Any] | None, str | None]:
    repo_info = _parse_origin_repo(origin_url)
    if not repo_info:
        return None, 'unsupported-origin-url'

    attempts: list[tuple[str, callable]] = []
    if repo_info['provider'] == 'github':
        attempts.append(('github-gh-api', _fetch_github_repo_facts_via_gh))
    attempts.append((f'{repo_info["provider"]}-public-api', _fetch_remote_repo_facts_via_api))
    attempts.append((f'{repo_info["provider"]}-html', _fetch_remote_repo_facts_via_html))

    errors: list[str] = []
    partial: dict[str, Any] | None = None
    for _name, fn in attempts:
        facts, err = fn(repo_info)
        if facts:
            if partial:
                for key in ['starCount', 'pushedAt', 'updatedAt', 'ownerType', 'htmlUrl']:
                    if facts.get(key) is None and partial.get(key) is not None:
                        facts[key] = partial.get(key)
                notes = list(partial.get('fallbackNotes') or [])
                facts['fallbackNotes'] = notes
            return facts, None
        if err:
            errors.append(err)
        if facts is None:
            continue
        if partial is None:
            partial = facts
        else:
            for key in ['starCount', 'pushedAt', 'updatedAt', 'ownerType', 'htmlUrl']:
                if partial.get(key) is None and facts.get(key) is not None:
                    partial[key] = facts.get(key)
            partial.setdefault('fallbackNotes', []).append(err or 'partial-fallback-used')

    if partial:
        partial.setdefault('fallbackNotes', []).extend(errors)
        return partial, ';'.join(errors) if errors else 'partial-facts-only'
    return None, ';'.join(errors) if errors else 'remote-facts-unavailable'


def _load_target_metadata(target_path: Path) -> tuple[dict[str, Any] | None, Path | None]:
    for name in TARGET_METADATA_FILES:
        path = target_path / name
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
        except Exception:
            data = None
        if isinstance(data, dict):
            return data, path
    return None, None


def _star_threshold(meta: dict[str, Any]) -> int | None:
    if meta.get('minStarsRequired') is not None:
        try:
            return int(meta['minStarsRequired'])
        except Exception:
            return None

    provider = str(meta.get('provider') or '').strip().lower()
    owner_type = str(meta.get('ownerType') or meta.get('ownershipClass') or '').strip().lower()

    # Gitee owner.type is too noisy to be a hard classifier here.
    # For the current thin policy we treat it as advisory-only and fall back to
    # the more permissive vendor/company threshold unless the user materializes
    # a stronger explicit sidecar rule.
    if provider == 'gitee':
        return 1000

    if owner_type in {'company', 'vendor', 'org', 'organization', 'enterprise'}:
        return 1000
    if owner_type in {'personal', 'individual', 'user'}:
        return 1500
    return 1000 if provider == 'github' else None


def check_target_policy(target_path: Path, policy: str) -> dict[str, Any]:
    payload: dict[str, Any] = {
        'ok': True,
        'policy': policy,
        'targetPath': str(target_path),
        'reasons': [],
        'notes': [],
        'facts': {},
    }

    if policy != 'weibu-submission':
        payload['notes'].append('policy-does-not-require-local-target-gate')
        return payload

    head_ts = _git_head_commit_ts(target_path)
    origin_url = _git_origin_url(target_path)
    meta, meta_path = _load_target_metadata(target_path)
    remote_facts, remote_error = _fetch_remote_repo_facts(origin_url)

    facts = payload['facts']
    facts['originUrl'] = origin_url
    facts['metadataPath'] = str(meta_path) if meta_path else None
    facts['remoteFacts'] = remote_facts
    facts['remoteError'] = remote_error

    cutoff = datetime.now(timezone.utc) - timedelta(days=WEIBU_RECENCY_DAYS)
    facts['recencyCutoffAt'] = cutoff.isoformat()

    if head_ts is not None:
        head_dt = datetime.fromtimestamp(head_ts, tz=timezone.utc)
        facts['headCommitAt'] = head_dt.isoformat()
        facts['headCommitAgeDays'] = int((datetime.now(timezone.utc) - head_dt).total_seconds() // 86400)
    else:
        payload['notes'].append('local-head-timestamp-missing')

    effective: dict[str, Any] = {}
    effective_sources: list[str] = []
    if remote_facts:
        effective['provider'] = remote_facts.get('provider')
        effective['starCount'] = remote_facts.get('starCount')
        effective['pushedAt'] = remote_facts.get('pushedAt')
        effective['ownerType'] = remote_facts.get('ownerType')
        effective['htmlUrl'] = remote_facts.get('htmlUrl')
        effective_sources.append(str(remote_facts.get('source') or 'remote'))
    if meta:
        if effective.get('starCount') is None:
            effective['starCount'] = meta.get('starCount')
        if effective.get('pushedAt') is None:
            effective['pushedAt'] = meta.get('pushedAt') or meta.get('lastPushedAt')
        if effective.get('ownerType') is None:
            effective['ownerType'] = meta.get('ownerType') or meta.get('ownershipClass')
        if meta.get('minStarsRequired') is not None:
            effective['minStarsRequired'] = meta.get('minStarsRequired')
        effective_sources.append('sidecar-metadata')
    if effective.get('pushedAt') is None and head_ts is not None:
        effective['pushedAt'] = datetime.fromtimestamp(head_ts, tz=timezone.utc).isoformat()
        effective_sources.append('local-head-commit')
    if not effective:
        payload['ok'] = False
        payload['reasons'].append({
            'code': 'missing-remote-eligibility-facts',
            'message': f'unable to fetch remote repo facts for star/pushedAt check: {remote_error or "unknown"}',
        })
        if head_ts is None:
            payload['reasons'].append({
                'code': 'missing-git-head-timestamp',
                'message': 'unable to read local git HEAD commit timestamp',
            })
        return payload

    facts['effectiveEligibilitySource'] = ' + '.join(effective_sources) if effective_sources else None
    facts['effectiveStarCount'] = effective.get('starCount')
    facts['effectiveOwnerType'] = effective.get('ownerType')
    pushed_at = _parse_iso_datetime(effective.get('pushedAt'))
    facts['effectivePushedAt'] = pushed_at.isoformat() if pushed_at else None
    threshold = _star_threshold(effective)
    facts['effectiveStarThreshold'] = threshold

    if threshold is None:
        payload['notes'].append('star-threshold-not-derivable')
    else:
        try:
            star_value = int(effective.get('starCount')) if effective.get('starCount') is not None else None
        except Exception:
            star_value = None
        if star_value is None:
            payload['ok'] = False
            payload['reasons'].append({
                'code': 'missing-effective-star-count',
                'message': f'unable to parse starCount from {effective.get("source")}',
            })
        elif star_value < threshold:
            payload['ok'] = False
            payload['reasons'].append({
                'code': 'stars-below-threshold',
                'message': f'starCount={star_value} < required={threshold}',
            })

    if pushed_at is None:
        payload['ok'] = False
        payload['reasons'].append({
            'code': 'missing-effective-pushedAt',
            'message': f'unable to parse pushedAt from {effective.get("source")}',
        })
    elif pushed_at < cutoff:
        payload['ok'] = False
        payload['reasons'].append({
            'code': 'effective-pushedAt-too-old',
            'message': f'effective pushedAt is older than {WEIBU_RECENCY_DAYS} days: {pushed_at.isoformat()}',
        })

    if head_ts is not None:
        head_dt = datetime.fromtimestamp(head_ts, tz=timezone.utc)
        if pushed_at and head_dt < cutoff and pushed_at >= cutoff:
            payload['notes'].append('local-clone-stale-but-remote-recency-pass')
        elif head_dt < cutoff and pushed_at and pushed_at < cutoff:
            payload['notes'].append('local-and-remote-both-old')

    return payload


def format_target_gate_block(result: dict[str, Any]) -> str:
    facts = result.get('facts') or {}
    lines = [
        '[loop9-target-gate] Launch blocked for local target',
        f'- policy={result.get("policy")}',
        f'- targetPath={result.get("targetPath")}',
    ]
    if facts.get('originUrl'):
        lines.append(f'- originUrl={facts.get("originUrl")}')
    if facts.get('headCommitAt'):
        lines.append(f'- headCommitAt={facts.get("headCommitAt")}')
    if facts.get('headCommitAgeDays') is not None:
        lines.append(f'- headCommitAgeDays={facts.get("headCommitAgeDays")}')
    if facts.get('metadataPath'):
        lines.append(f'- metadataPath={facts.get("metadataPath")}')
    if facts.get('effectiveEligibilitySource'):
        lines.append(f'- effectiveEligibilitySource={facts.get("effectiveEligibilitySource")}')
    if facts.get('effectiveStarCount') is not None:
        lines.append(f'- effectiveStarCount={facts.get("effectiveStarCount")}')
    if facts.get('effectiveStarThreshold') is not None:
        lines.append(f'- effectiveStarThreshold={facts.get("effectiveStarThreshold")}')
    if facts.get('effectivePushedAt'):
        lines.append(f'- effectivePushedAt={facts.get("effectivePushedAt")}')
    if facts.get('remoteError'):
        lines.append(f'- remoteError={facts.get("remoteError")}')
    for row in result.get('reasons', []):
        lines.append(f'- {row.get("code")}: {row.get("message")}')
    for note in result.get('notes', []):
        lines.append(f'- note: {note}')
    return '\n'.join(lines)
