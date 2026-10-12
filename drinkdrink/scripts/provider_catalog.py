#!/usr/bin/env python3
"""Inspect the official provider catalog without contacting or logging in to vendors."""

import argparse
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from providers import load_catalog  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["list", "show", "audit"])
    parser.add_argument("provider", nargs="?", help="module id for show")
    parser.add_argument("--at", type=date.fromisoformat, default=date.today(), help="audit date, YYYY-MM-DD")
    parser.add_argument("--max-age-days", type=int, default=90)
    args = parser.parse_args()
    catalog = load_catalog()
    if args.command == "list":
        for item in catalog.values():
            actions = ", ".join(item.capabilities) or "reference only"
            print(f"{item.id}\t{item.surface}\t{item.status}\t{actions}")
    elif args.command == "show":
        if not args.provider or args.provider not in catalog:
            parser.error("show requires a known provider id")
        item = catalog[args.provider]
        print(json.dumps({
            "id": item.id, "brand": item.brand, "surface": item.surface,
            "audience": item.audience, "status": item.status,
            "verified_on": item.verified_on.isoformat(), "source_urls": item.source_urls,
            "endpoint": item.endpoint, "capabilities": item.capabilities,
            "notes": item.notes,
        }, ensure_ascii=False, indent=2))
    else:
        if args.max_age_days < 0:
            parser.error("--max-age-days must be nonnegative")
        stale = [item for item in catalog.values()
                 if (args.at - item.verified_on).days > args.max_age_days]
        for item in stale:
            print(f"STALE\t{item.id}\tverified {item.verified_on.isoformat()}")
        print(f"{len(catalog)} modules; {len(stale)} need source review")
        return 1 if stale else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
