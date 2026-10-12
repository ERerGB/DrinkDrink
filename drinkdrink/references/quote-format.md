# Quote format

The comparator reads one local JSON file. Prices are decimal strings in the same currency. Keep personal details out of shared examples. An agent or person must observe checkout; this format never guesses eligibility from coupon names.

```json
{
  "request": {
    "category": "iced_latte",
    "temperature": "iced",
    "quantity": 1,
    "min_volume_ml": 450,
    "allowed_fulfillment": ["delivery", "pickup"],
    "max_eta_minutes": 45,
    "currency": "CNY",
    "max_age_minutes": 30
  },
  "coverage": [
    {"path_id": "pickup-wechat", "channel": "Brand pickup", "fulfillment": "pickup", "payment_method": "WeChat Pay", "status": "checked"},
    {"path_id": "delivery-wechat", "channel": "Brand delivery", "fulfillment": "delivery", "payment_method": "WeChat Pay", "status": "checked", "reason": "no matching offers"},
    {"path_id": "marketplace-alipay", "channel": "Delivery marketplace", "fulfillment": "delivery", "payment_method": "Alipay", "status": "gap", "reason": "login unavailable"}
  ],
  "quotes": [
    {
      "id": "pickup-1",
      "path_id": "pickup-wechat",
      "merchant": "Example Coffee",
      "channel": "Brand pickup",
      "store": "Example store",
      "fulfillment": "pickup",
      "product": {"name": "Iced latte", "category": "iced_latte", "temperature": "iced", "quantity": 1, "volume_ml": 473},
      "eta_minutes": 15,
      "observed_at": "2026-10-13T09:00:00+08:00",
      "payment_method": "WeChat Pay",
      "incentives_reviewed": true,
      "incentives": [
        {"name": "Drink coupon", "kind": "merchant_coupon", "outcome": "applied"},
        {"name": "Card offer", "kind": "payment_offer", "outcome": "ineligible", "reason": "minimum spend not met"}
      ],
      "checkout": {
        "verified": true,
        "evidence": "final checkout preview in app",
        "item_price": "38.00",
        "fees": {"packaging": "0.00", "delivery": "0.00", "service": "0.00"},
        "discounts": [{"name": "Drink coupon", "kind": "merchant_coupon", "amount": "19.00"}],
        "payable": "19.00",
        "wallet_used": "0.00",
        "cash_due": "19.00"
      }
    }
  ]
}
```

`coverage.status`: `checked`, `gap`, or `excluded`. Give a reason for a gap or exclusion. A checked path must have a quote or a reason such as “no matching offers.” Each `path_id` represents a channel, fulfillment method, and payment method. Include relevant options in the declared coverage; a quote must use the same path values. This makes a missing payment method visible instead of silently assuming it was checked.

`incentives.outcome`: `applied`, `incompatible`, `ineligible`, or `untested`. Allowed kinds are `merchant_coupon`, `platform_coupon`, `payment_offer`, and `instant_promotion`. Applied discounts must have a matching name and kind in `checkout.discounts`. Give a reason for incompatible or ineligible offers. Mark any untested coupon or payment offer as `untested`; that quote remains provisional. Compare a different payment method as a separate quote.

`checkout.payable` is the total after instant discounts and before spending wallet credit. `cash_due = payable - wallet_used`. Rank by `payable`: an existing balance is the buyer's money. Do not include future cashback or points in `discounts`; mention them separately. `checkout.verified` means the lines were read on the selected cart or final checkout page, without placing the order; supply a short `checkout.evidence` description. The tool checks consistency, while the agent or buyer remains responsible for observing the real page.

The tool excludes nonmatching or late paths. It marks expired or stale paths provisional and reports malformed totals as an error. It declares a verified winner within the declared channel coverage only when every comparable quote and channel has been checked. Use `--format json` for machine-readable output and `--at ISO_TIMESTAMP` for a reproducible evaluation time.
