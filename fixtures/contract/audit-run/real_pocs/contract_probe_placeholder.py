#!/usr/bin/env python3
"""Contract-only placeholder.

This file intentionally performs no network request, exploit attempt, or target
interaction. It exists so publish/report tooling can verify PoC file handling
without shipping a real vulnerability demo.
"""

from __future__ import annotations

import json


def main() -> int:
    print(json.dumps({"status": "contract-only", "finding_id": "LWCONTRACT-001"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
