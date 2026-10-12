#!/usr/bin/env python3
"""Compare observed drink checkout paths without inventing discounts."""

import argparse
import json
import sys
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path


class QuoteError(ValueError):
    pass


def money(value, label):
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError) as exc:
        raise QuoteError(f"{label}: invalid money amount") from exc
    if not amount.is_finite() or amount < 0 or amount.as_tuple().exponent < -2:
        raise QuoteError(f"{label}: expected a nonnegative amount with at most 2 decimals")
    return amount


def timestamp(value, label):
    try:
        parsed = datetime.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise QuoteError(f"{label}: expected an ISO timestamp") from exc
    if parsed.tzinfo is None:
        raise QuoteError(f"{label}: timezone is required")
    return parsed


def required(mapping, key, label):
    if not isinstance(mapping, dict) or key not in mapping:
        raise QuoteError(f"{label}.{key}: required")
    return mapping[key]


def evaluate(data, now=None):
    now = now or datetime.now(timezone.utc)
    request = required(data, "request", "input")
    category = required(request, "category", "request")
    temperature = required(request, "temperature", "request")
    quantity = int(required(request, "quantity", "request"))
    min_volume = int(required(request, "min_volume_ml", "request"))
    allowed = required(request, "allowed_fulfillment", "request")
    currency = required(request, "currency", "request")
    max_age = int(request.get("max_age_minutes", 30))
    max_eta = request.get("max_eta_minutes")
    if not isinstance(allowed, list) or not allowed or min_volume <= 0 or quantity <= 0 or max_age <= 0:
        raise QuoteError("request: invalid fulfillment, quantity, volume, or age limit")
    if max_eta is not None and int(max_eta) < 0:
        raise QuoteError("request.max_eta_minutes: must be nonnegative")

    coverage = required(data, "coverage", "input")
    quotes = required(data, "quotes", "input")
    if not isinstance(coverage, list) or not coverage or not isinstance(quotes, list):
        raise QuoteError("input: coverage must be nonempty and quotes must be a list")
    path_status = {}
    gaps = []
    for row in coverage:
        path_id = required(row, "path_id", "coverage")
        required(row, "channel", f"coverage[{path_id}]")
        required(row, "fulfillment", f"coverage[{path_id}]")
        required(row, "payment_method", f"coverage[{path_id}]")
        status = required(row, "status", f"coverage[{path_id}]")
        if status not in {"checked", "gap", "excluded"} or path_id in path_status:
            raise QuoteError(f"coverage[{path_id}]: invalid or duplicate status")
        path_status[path_id] = row
        if status != "checked":
            reason = row.get("reason")
            if not reason:
                raise QuoteError(f"coverage[{path_id}].reason: required")
            if status == "gap":
                gaps.append(f"{path_id}: {reason}")

    ranked = []
    excluded = []
    provisional = []
    seen_ids = set()
    for quote in quotes:
        quote_id = required(quote, "id", "quote")
        if quote_id in seen_ids:
            raise QuoteError(f"quote {quote_id}: duplicate id")
        seen_ids.add(quote_id)
        path_id = required(quote, "path_id", quote_id)
        path = path_status.get(path_id)
        if not path or path["status"] != "checked":
            raise QuoteError(f"quote {quote_id}: path must have checked coverage")
        channel = required(quote, "channel", quote_id)
        for field in ("channel", "fulfillment", "payment_method"):
            if quote.get(field) != path[field]:
                raise QuoteError(f"quote {quote_id}: {field} differs from coverage path")
        product = required(quote, "product", quote_id)
        fulfillment = required(quote, "fulfillment", quote_id)
        volume = int(required(product, "volume_ml", f"{quote_id}.product"))
        eta = int(required(quote, "eta_minutes", quote_id))
        if volume <= 0 or eta < 0:
            raise QuoteError(f"quote {quote_id}: invalid volume or ETA")
        mismatch = []
        if product.get("category") != category or product.get("temperature") != temperature:
            mismatch.append("different drink or temperature")
        if int(required(product, "quantity", f"{quote_id}.product")) != quantity:
            mismatch.append("different quantity")
        if volume < min_volume:
            mismatch.append("volume below minimum")
        if fulfillment not in allowed:
            mismatch.append("fulfillment not accepted")
        if max_eta is not None and eta > int(max_eta):
            mismatch.append("ETA exceeds limit")
        if mismatch:
            excluded.append({"id": quote_id, "reasons": mismatch})
            continue

        observed = timestamp(required(quote, "observed_at", quote_id), f"{quote_id}.observed_at")
        issues = []
        age_minutes = (now - observed).total_seconds() / 60
        if age_minutes < -2:
            raise QuoteError(f"quote {quote_id}: observation is in the future")
        if age_minutes > max_age:
            issues.append("quote is stale")
        valid_until = quote.get("valid_until")
        if valid_until and now > timestamp(valid_until, f"{quote_id}.valid_until"):
            issues.append("offer expired")
        if quote.get("currency", currency) != currency:
            raise QuoteError(f"quote {quote_id}: currency mismatch")

        checkout = required(quote, "checkout", quote_id)
        item_price = money(required(checkout, "item_price", f"{quote_id}.checkout"), f"{quote_id}.item_price")
        fees = required(checkout, "fees", f"{quote_id}.checkout")
        if not isinstance(fees, dict):
            raise QuoteError(f"quote {quote_id}: fees must be an object")
        fee_total = sum((money(value, f"{quote_id}.fees.{key}") for key, value in fees.items()), Decimal("0"))
        discounts = checkout.get("discounts", [])
        if not isinstance(discounts, list):
            raise QuoteError(f"quote {quote_id}: discounts must be a list")
        discount_total = sum((money(required(d, "amount", "discount"), f"{quote_id}.discount") for d in discounts), Decimal("0"))
        payable = money(required(checkout, "payable", f"{quote_id}.checkout"), f"{quote_id}.payable")
        wallet_used = money(checkout.get("wallet_used", "0"), f"{quote_id}.wallet_used")
        cash_due = money(required(checkout, "cash_due", f"{quote_id}.checkout"), f"{quote_id}.cash_due")
        if item_price + fee_total - discount_total != payable:
            raise QuoteError(f"quote {quote_id}: payable does not equal item + fees - discounts")
        if payable - wallet_used != cash_due:
            raise QuoteError(f"quote {quote_id}: cash_due does not equal payable - wallet_used")

        incentives = quote.get("incentives", [])
        if not isinstance(incentives, list):
            raise QuoteError(f"quote {quote_id}: incentives must be a list")
        applied_discounts = set()
        for incentive in incentives:
            name = required(incentive, "name", f"{quote_id}.incentive")
            kind = required(incentive, "kind", f"{quote_id}.incentive")
            if kind not in {"merchant_coupon", "platform_coupon", "payment_offer", "instant_promotion"}:
                raise QuoteError(f"quote {quote_id}: invalid incentive kind")
            outcome = required(incentive, "outcome", f"{quote_id}.incentive")
            if outcome not in {"applied", "incompatible", "ineligible", "untested"}:
                raise QuoteError(f"quote {quote_id}: invalid incentive outcome")
            if outcome in {"incompatible", "ineligible"} and not incentive.get("reason"):
                raise QuoteError(f"quote {quote_id}: {name} needs a reason")
            if outcome == "applied":
                applied_discounts.add((name, kind))
            if outcome == "untested":
                issues.append(f"untested incentive: {name}")
        discount_keys = [(required(d, "name", f"{quote_id}.discount"), required(d, "kind", f"{quote_id}.discount")) for d in discounts]
        if len(discount_keys) != len(set(discount_keys)) or set(discount_keys) != applied_discounts:
            raise QuoteError(f"quote {quote_id}: applied incentives and discount lines differ")
        if not quote.get("incentives_reviewed", False):
            issues.append("incentives not fully reviewed")
        if not checkout.get("verified", False):
            issues.append("checkout not verified")
        elif not checkout.get("evidence"):
            raise QuoteError(f"quote {quote_id}: verified checkout needs evidence")
        row = {
            "id": quote_id,
            "merchant": required(quote, "merchant", quote_id),
            "channel": channel,
            "fulfillment": fulfillment,
            "payment_method": required(quote, "payment_method", quote_id),
            "volume_ml": volume,
            "eta_minutes": eta,
            "payable": f"{payable:.2f}",
            "wallet_used": f"{wallet_used:.2f}",
            "cash_due": f"{cash_due:.2f}",
            "issues": issues,
        }
        ranked.append(row)
        if issues:
            provisional.append(quote_id)

    for row in coverage:
        path_id = row["path_id"]
        if row["status"] == "checked" and not row.get("reason") and not any(q.get("path_id") == path_id for q in quotes):
            gaps.append(f"{path_id}: checked but no quote or no-offer reason")

    ranked.sort(key=lambda row: (Decimal(row["payable"]), row["eta_minutes"], row["id"]))
    verified = [row for row in ranked if not row["issues"]]
    winner = verified[0]["id"] if verified and not gaps and not provisional else None
    return {"currency": currency, "winner": winner, "best_observed": ranked[0]["id"] if ranked else None,
            "ranked": ranked, "excluded": excluded, "coverage_gaps": gaps,
            "verdict": "verified" if winner else "provisional" if ranked else "no_comparable_quote"}


def markdown(result):
    lines = [f"Verdict: {result['verdict']}"]
    if result["winner"]:
        lines.append(f"Verified winner among checked paths: {result['winner']}")
    elif result["best_observed"]:
        lines.append(f"Best observed: {result['best_observed']} (not a verified cheapest claim)")
    lines.extend(["", "| Path | Payable | Cash due | ETA | Status |", "|---|---:|---:|---:|---|"])
    for row in result["ranked"]:
        status = "; ".join(row["issues"]) or "verified"
        lines.append(f"| {row['id']} ({row['channel']}) | {row['payable']} | {row['cash_due']} | {row['eta_minutes']} min | {status} |")
    if result["coverage_gaps"]:
        lines.extend(["", "Coverage gaps:"] + [f"- {gap}" for gap in result["coverage_gaps"]])
    if result["excluded"]:
        lines.extend(["", "Excluded:"] + [f"- {row['id']}: {', '.join(row['reasons'])}" for row in result["excluded"]])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("quotes", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--at", help="Evaluation time as ISO timestamp with timezone")
    args = parser.parse_args()
    try:
        data = json.loads(args.quotes.read_text(encoding="utf-8"))
        result = evaluate(data, timestamp(args.at, "--at") if args.at else None)
    except (OSError, json.JSONDecodeError, QuoteError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.format == "json" else markdown(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
