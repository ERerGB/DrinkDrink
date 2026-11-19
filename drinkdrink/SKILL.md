---
name: drinkdrink
description: Plan and complete a drink order across delivery apps, brand mini programs, and pickup using the buyer's actual coupons, payment offers, checkout totals, fulfillment, and follow-up. Use for coffee, tea, and other drink purchase requests.
---

# DrinkDrink

Compare drinks on the buyer's actual purchase paths, then carry out only the
requested stage. A path includes merchant, channel, store, variant, fulfillment,
coupons and payment method; delivery/pickup and differing payment offers are
separate paths. Resolve only missing constraints that change the choice: size,
quantity, temperature, dietary/caffeine needs, timing, budget and allowed alternatives.

## Compare without submitting

Inspect the requested/relevant channels and equivalent products. Read coupon and
payment-offer eligibility for that exact product/store/channel/time, threshold and
stack. A wallet coupon or advertisement is not an applied discount. Capture final
checkout item/fee/discount lines, payable amount, funding, ETA and observation time.
Stored balance/prepaid credit is the buyer's money, not savings.

Use [the quote format](references/quote-format.md) and
`python3 <skill-dir>/scripts/compare.py quotes.json` for arithmetic, freshness,
coverage and matching checks. It cannot verify the live checkout for you. Record
unavailable channels and untested incentives; recommend a verified winner only
within checked coverage, otherwise explain the best observed provisional choice.
Keep addresses, account data, screenshots and session tokens private.

## Order and follow through when requested

Recheck the exact product, store, fulfillment/location, coupon lines, payment,
fees, total and ETA against the buyer's authorization before submission. Unexpected
price increases, substitutions or new commitments need a decision. Confirm the
result in the app/order history; reconcile an uncertain submission before retrying.

Report only observed order/payment/preparation/delivery/pickup/receipt/refund states.
Help resolve an actual issue through the app; distinguish payment from acceptance.
Capture useful buyer feedback without inventing receipt or satisfaction. For
cross-session tracking, use the optional [local journal](references/journal.md).

Prefer a supported connector or the buyer's accessible app UI. When configuring
an integration, read [official providers](references/official-providers.md) and
verify current live tools, authentication, monetary units and prices; a catalog
entry does not establish access. New adapters use [the adapter contract](references/adapter-contract.md).
`android_capture.py` only lists devices/saves screenshots; it does not tap, order
or pay. Ordinary comparisons need neither adapter development nor a new login.
