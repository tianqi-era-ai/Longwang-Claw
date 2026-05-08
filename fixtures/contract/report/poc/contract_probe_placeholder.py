#!/usr/bin/env python3
"""Delivery report copy of the contract-only placeholder."""

from __future__ import annotations

import json


def main() -> int:
    print(json.dumps({"status": "contract-only", "finding_id": "LWCONTRACT-001"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
