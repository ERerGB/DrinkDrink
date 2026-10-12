#!/usr/bin/env python3
"""Keep an optional local, append-only timeline for a drink order."""

import argparse
import json
import os
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path


TRANSITIONS = {
    "idea": {"discovered", "cancelled"},
    "discovered": {"quoted", "cancelled"},
    "quoted": {"selected", "discovered", "cancelled"},
    "selected": {"submitted", "quoted", "cancelled"},
    "submitted": {"accepted", "cancelled", "issue_reported"},
    "accepted": {"in_transit", "ready_for_pickup", "received", "issue_reported", "cancelled"},
    "in_transit": {"received", "issue_reported"},
    "ready_for_pickup": {"received", "issue_reported"},
    "received": {"completed", "issue_reported"},
    "issue_reported": {"refund_pending", "resolved", "received"},
    "refund_pending": {"refunded", "resolved"},
    "completed": {"issue_reported"}, "resolved": set(), "refunded": set(), "cancelled": set(),
}
PAYMENT_EVENTS = {"payment_pending", "payment_paid", "payment_failed", "payment_refunded"}


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load(path):
    if not path.exists():
        return {"version": 1, "orders": []}
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("version") != 1 or not isinstance(value.get("orders"), list):
        raise ValueError("unsupported journal format")
    return value


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=".drinkdrink-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def start(journal, idea):
    if not idea.strip():
        raise ValueError("idea cannot be empty")
    order = {"id": uuid.uuid4().hex[:12], "idea": idea.strip(), "stage": "idea",
             "events": [{"at": now_iso(), "event": "idea", "note": idea.strip()}]}
    journal["orders"].append(order)
    return order


def record(journal, order_id, event, note="", evidence=""):
    order = next((item for item in journal["orders"] if item["id"] == order_id), None)
    if order is None:
        raise ValueError("order id not found")
    if event in TRANSITIONS:
        if event not in TRANSITIONS[order["stage"]]:
            raise ValueError(f"invalid stage transition: {order['stage']} -> {event}")
        if event in {"submitted", "accepted", "received", "refunded"} and not evidence.strip():
            raise ValueError(f"{event} requires observed evidence")
        order["stage"] = event
    elif event in PAYMENT_EVENTS:
        if order["stage"] in {"idea", "discovered", "quoted"}:
            raise ValueError("payment event before a path is selected")
        if event in {"payment_paid", "payment_refunded"} and not evidence.strip():
            raise ValueError(f"{event} requires observed evidence")
    else:
        raise ValueError("unknown event")
    row = {"at": now_iso(), "event": event}
    if note.strip():
        row["note"] = note.strip()
    if evidence.strip():
        row["evidence"] = evidence.strip()
    order["events"].append(row)
    return order


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", type=Path, default=Path("drinkdrink.journal.json"))
    commands = parser.add_subparsers(dest="command", required=True)
    begin = commands.add_parser("start")
    begin.add_argument("--idea", required=True)
    update = commands.add_parser("record")
    update.add_argument("--id", required=True)
    update.add_argument("--event", required=True)
    update.add_argument("--note", default="")
    update.add_argument("--evidence", default="")
    show = commands.add_parser("show")
    show.add_argument("--id")
    args = parser.parse_args()
    try:
        journal = load(args.file)
        if args.command == "start":
            result = start(journal, args.idea)
            save(args.file, journal)
        elif args.command == "record":
            result = record(journal, args.id, args.event, args.note, args.evidence)
            save(args.file, journal)
        else:
            result = next((item for item in journal["orders"] if item["id"] == args.id), None) if args.id else journal
            if result is None:
                raise ValueError("order id not found")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
