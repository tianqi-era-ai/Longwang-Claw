#!/usr/bin/env python3

import argparse
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

DEFAULT_REGISTRY = Path("/root/openclaw-runtime/docker-resource-registry.json")
UTC = timezone.utc
CLASS_ORDER = [
    "published-final",
    "operator-keep",
    "historical-cold-snapshot",
    "stopped-intermediate",
    "scratch-orphan",
    "non-docker-published-final",
]
CLASS_TITLES = {
    "published-final": "Published Final Runtimes",
    "operator-keep": "Operator Keep Runtimes",
    "historical-cold-snapshot": "Historical Cold Snapshots",
    "stopped-intermediate": "Stopped Intermediate Runtimes",
    "scratch-orphan": "Scratch / Orphan Containers",
    "non-docker-published-final": "Non-Docker Published Final Runtimes",
}


def _run(args: List[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        check=False,
    )


def _run_json(args: List[str], *, default: Any) -> Any:
    proc = _run(args)
    if proc.returncode != 0:
        return default
    raw = proc.stdout.strip()
    if not raw:
        return default
    try:
        return json.loads(raw)
    except Exception:
        return default


def _run_json_lines(args: List[str]) -> List[Dict[str, Any]]:
    proc = _run(args)
    if proc.returncode != 0:
        return []
    rows: List[Dict[str, Any]] = []
    for line in proc.stdout.splitlines():
        text = line.strip()
        if not text:
            continue
        try:
            payload = json.loads(text)
        except Exception:
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def _clean_timestamp(raw: Any) -> str:
    text = str(raw or "").strip()
    if not text or text.startswith("0001-01-01T00:00:00"):
        return ""
    return text


def _parse_timestamp(raw: Any) -> Optional[datetime]:
    text = _clean_timestamp(raw)
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    if "." in text:
        head, tail = text.split(".", 1)
        sign = ""
        offset = ""
        if "+" in tail:
            frac, offset = tail.split("+", 1)
            sign = "+"
        elif "-" in tail:
            frac, offset = tail.split("-", 1)
            sign = "-"
        else:
            frac = tail
        frac = (frac + "000000")[:6]
        text = head + "." + frac
        if sign and offset:
            text += sign + offset
    try:
        dt = datetime.fromisoformat(text)
    except Exception:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _container_last_activity(created_at: str, started_at: str, finished_at: str) -> Tuple[str, str]:
    candidates = [
        ("startedAt", _parse_timestamp(started_at)),
        ("finishedAt", _parse_timestamp(finished_at)),
        ("createdAt", _parse_timestamp(created_at)),
    ]
    valid = [(label, dt) for label, dt in candidates if dt is not None]
    if not valid:
        return "", ""
    label, dt = max(valid, key=lambda item: item[1])
    return dt.isoformat(), label


def _docker_container_rows() -> List[Dict[str, Any]]:
    ps_rows = _run_json_lines(["docker", "ps", "-a", "--format", "{{json .}}"])
    ps_by_name = {str(row.get("Names") or "").strip(): row for row in ps_rows}

    ids_proc = _run(["docker", "ps", "-aq"])
    if ids_proc.returncode != 0:
        return []
    ids = [line.strip() for line in ids_proc.stdout.splitlines() if line.strip()]
    if not ids:
        return []

    inspect_rows = _run_json(["docker", "inspect", *ids], default=[])
    if not isinstance(inspect_rows, list):
        return []

    rows: List[Dict[str, Any]] = []
    for payload in inspect_rows:
        if not isinstance(payload, dict):
            continue
        name = str(payload.get("Name") or "").lstrip("/")
        state = payload.get("State") or {}
        config = payload.get("Config") or {}
        labels = config.get("Labels") or {}
        ps_row = ps_by_name.get(name, {})
        created_at = _clean_timestamp(payload.get("Created"))
        started_at = _clean_timestamp(state.get("StartedAt"))
        finished_at = _clean_timestamp(state.get("FinishedAt"))
        last_activity_at, last_activity_source = _container_last_activity(created_at, started_at, finished_at)
        rows.append(
            {
                "name": name,
                "id": str(payload.get("Id") or "")[:12],
                "state": str(state.get("Status") or ps_row.get("State") or "").strip(),
                "status": str(ps_row.get("Status") or "").strip(),
                "image": str(config.get("Image") or ps_row.get("Image") or "").strip(),
                "ports": str(ps_row.get("Ports") or "").strip(),
                "compose_project": str(labels.get("com.docker.compose.project") or "").strip(),
                "compose_service": str(labels.get("com.docker.compose.service") or "").strip(),
                "created_at": created_at,
                "started_at": started_at,
                "finished_at": finished_at,
                "last_activity_at": last_activity_at,
                "last_activity_source": last_activity_source,
            }
        )
    return rows


def _docker_compose_rows() -> List[Dict[str, Any]]:
    rows = _run_json(["docker", "compose", "ls", "--all", "--format", "json"], default=[])
    return rows if isinstance(rows, list) else []


def _systemd_status(name: str) -> str:
    try:
        proc = _run(["systemctl", "is-active", name])
    except FileNotFoundError:
        return "systemctl-unavailable"
    text = (proc.stdout or proc.stderr).strip()
    return text or "unknown"


def _load_registry(path: Path) -> Dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("registry root must be an object")
    return data


def _matches_exact_or_prefix(value: str, exacts: List[str], prefixes: List[str]) -> bool:
    if value in exacts:
        return True
    return any(value.startswith(prefix) for prefix in prefixes)


def _match_unit(
    unit: Dict[str, Any],
    containers: List[Dict[str, Any]],
    compose_rows: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    match = unit.get("match") or {}
    exact_container_names = [str(v) for v in match.get("container_names") or []]
    container_prefixes = [str(v) for v in match.get("container_prefixes") or []]
    exact_projects = [str(v) for v in match.get("compose_projects") or []]
    project_prefixes = [str(v) for v in match.get("compose_project_prefixes") or []]
    systemd_services = [str(v) for v in match.get("systemd_services") or []]

    matched_containers: List[Dict[str, Any]] = []
    for row in containers:
        name = str(row.get("name") or "")
        project = str(row.get("compose_project") or "")
        if _matches_exact_or_prefix(name, exact_container_names, container_prefixes):
            matched_containers.append(row)
            continue
        if project and _matches_exact_or_prefix(project, exact_projects, project_prefixes):
            matched_containers.append(row)

    matched_projects: List[Dict[str, Any]] = []
    for row in compose_rows:
        name = str(row.get("Name") or "")
        if _matches_exact_or_prefix(name, exact_projects, project_prefixes):
            matched_projects.append(row)

    matched_systemd = [{"name": name, "state": _systemd_status(name)} for name in systemd_services]
    return matched_containers, matched_projects, matched_systemd


def _summarize_unit(
    unit: Dict[str, Any],
    containers: List[Dict[str, Any]],
    projects: List[Dict[str, Any]],
    systemd_rows: List[Dict[str, Any]],
) -> Dict[str, Any]:
    state_counts = Counter(str(row.get("state") or "unknown") for row in containers)
    return {
        "unit_key": str(unit.get("unit_key") or ""),
        "repo_slug": str(unit.get("repo_slug") or ""),
        "display_name": str(unit.get("display_name") or unit.get("unit_key") or ""),
        "class": str(unit.get("class") or "unclassified"),
        "carrier": str(unit.get("carrier") or ""),
        "runtime_root": unit.get("runtime_root"),
        "public_urls": unit.get("public_urls") or [],
        "start_command": unit.get("start_command"),
        "stop_command": unit.get("stop_command"),
        "notes": unit.get("notes") or "",
        "containers": containers,
        "compose_projects": projects,
        "systemd": systemd_rows,
        "state_counts": dict(state_counts),
    }


def _build_inventory(registry: Dict[str, Any]) -> Dict[str, Any]:
    containers = _docker_container_rows()
    compose_rows = _docker_compose_rows()
    summaries: List[Dict[str, Any]] = []
    matched_container_names: set[str] = set()

    for unit in registry.get("units") or []:
        if not isinstance(unit, dict):
            continue
        matched_containers, matched_projects, matched_systemd = _match_unit(unit, containers, compose_rows)
        for row in matched_containers:
            matched_container_names.add(str(row.get("name") or ""))
        summaries.append(_summarize_unit(unit, matched_containers, matched_projects, matched_systemd))

    unknown_containers = [row for row in containers if str(row.get("name") or "") not in matched_container_names]
    grouped: Dict[str, List[Dict[str, Any]]] = {key: [] for key in CLASS_ORDER}
    grouped["unclassified"] = []
    for item in summaries:
        grouped.setdefault(str(item.get("class") or "unclassified"), []).append(item)
    return {
        "schema": "openclaw.docker-inventory.output.v1",
        "registry": {
            "path": str(DEFAULT_REGISTRY),
            "schema": registry.get("schema"),
            "updated_at": registry.get("updated_at"),
            "host_alias": registry.get("host_alias"),
            "policy": registry.get("policy") or {},
        },
        "groups": grouped,
        "unknown_containers": unknown_containers,
    }


def _render_unit(item: Dict[str, Any]) -> List[str]:
    lines = [f"- {item['display_name']} [{item['carrier'] or 'n/a'}]"]
    state_counts = item.get("state_counts") or {}
    if state_counts:
        state_text = ", ".join(f"{key}={value}" for key, value in sorted(state_counts.items()))
        lines.append(f"  state_counts: {state_text}")
    if item.get("public_urls"):
        lines.append(f"  public: {', '.join(str(v) for v in item['public_urls'])}")
    if item.get("runtime_root"):
        lines.append(f"  runtime_root: {item['runtime_root']}")
    for project in item.get("compose_projects") or []:
        lines.append(
            "  compose: "
            f"{project.get('Name')} [{project.get('Status')}] "
            f"{project.get('ConfigFiles')}"
        )
    for row in item.get("containers") or []:
        tail = f" image={row.get('image')}"
        if row.get("ports"):
            tail += f" ports={row.get('ports')}"
        last_activity = str(row.get("last_activity_at") or "").strip()
        if last_activity:
            source = str(row.get("last_activity_source") or "").strip()
            tail += f" last_activity={last_activity}"
            if source:
                tail += f"({source})"
        lines.append(f"  container: {row.get('name')} [{row.get('state')}] {tail}")
    for row in item.get("systemd") or []:
        lines.append(f"  systemd: {row.get('name')} [{row.get('state')}]")
    if item.get("start_command"):
        lines.append(f"  start: {item['start_command']}")
    if item.get("stop_command"):
        lines.append(f"  stop: {item['stop_command']}")
    if item.get("notes"):
        lines.append(f"  notes: {item['notes']}")
    return lines


def _render_text(inventory: Dict[str, Any], classes: List[str], *, unknown_only: bool) -> str:
    lines = [
        "OpenClaw Docker Inventory",
        f"registry_path: {inventory['registry']['path']}",
        f"registry_schema: {inventory['registry'].get('schema') or 'unknown'}",
        f"registry_updated_at: {inventory['registry'].get('updated_at') or 'unknown'}",
    ]
    policy = inventory["registry"].get("policy") or {}
    cleanup_age = policy.get("cleanup_min_age_hours")
    if cleanup_age:
        lines.append(f"cleanup_min_age_hours: {cleanup_age}")
    cleanup_age_basis = str(policy.get("cleanup_age_basis") or "").strip()
    if cleanup_age_basis:
        lines.append(f"cleanup_age_basis: {cleanup_age_basis}")
    ai_read = policy.get("ai_read_order") or []
    if ai_read:
        lines.append("ai_read_order:")
        for item in ai_read:
            lines.append(f"  - {item}")

    if not unknown_only:
        for class_name in classes:
            items = inventory["groups"].get(class_name) or []
            if not items:
                continue
            lines.append("")
            lines.append(CLASS_TITLES.get(class_name, class_name))
            for item in items:
                lines.extend(_render_unit(item))

    unknown = inventory.get("unknown_containers") or []
    if unknown:
        lines.append("")
        lines.append("Unclassified Containers")
        for row in unknown:
            tail = f" image={row.get('image')}"
            if row.get("ports"):
                tail += f" ports={row.get('ports')}"
            project = str(row.get("compose_project") or "").strip()
            if project:
                tail += f" compose_project={project}"
            last_activity = str(row.get("last_activity_at") or "").strip()
            if last_activity:
                source = str(row.get("last_activity_source") or "").strip()
                tail += f" last_activity={last_activity}"
                if source:
                    tail += f"({source})"
            lines.append(f"- {row.get('name')} [{row.get('state')}] {tail}")
    elif unknown_only:
        lines.append("No unclassified containers.")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Render the authoritative Tencent CVM docker runtime inventory.")
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY), help="Path to docker-resource-registry.json")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    parser.add_argument(
        "--class",
        dest="classes",
        action="append",
        default=[],
        help="Only render the specified class. Repeatable.",
    )
    parser.add_argument("--unknown-only", action="store_true", help="Only render unclassified containers")
    args = parser.parse_args()

    registry_path = Path(args.registry).expanduser()
    if not registry_path.exists():
        print(f"registry not found: {registry_path}", file=sys.stderr)
        return 2

    registry = _load_registry(registry_path)
    inventory = _build_inventory(registry)
    inventory["registry"]["path"] = str(registry_path)

    if args.json:
        print(json.dumps(inventory, ensure_ascii=False, indent=2))
        return 0

    classes = args.classes or CLASS_ORDER
    print(_render_text(inventory, classes, unknown_only=bool(args.unknown_only)), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
