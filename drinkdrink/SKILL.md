---
name: drinkdrink
description: Plan and complete a drink order across delivery apps, brand mini programs, and pickup using the buyer's actual coupons, payment offers, checkout totals, fulfillment, and follow-up. Use for coffee, tea, and other drink purchase requests.
---

# DrinkDrink

Help the buyer complete a drink's life cycle: an idea or craving, product discovery, channel comparison, order and payment, fulfillment, receipt, and a useful follow-up. A purchase path is a merchant, channel, fulfillment mode, store, drink variant, coupon stack, and payment method. Treat delivery and pickup as different paths, including Starbucks 专星送 and 啡快. Never infer that a coupon in one path works in another.

## Work from the buyer's request

Translate the buyer's idea into drink type, temperature, minimum acceptable size, quantity, dietary or caffeine constraints, delivery or pickup preference, latest useful arrival time, budget, and any merchant preference. Ask only for a constraint that changes the choice and cannot be observed. If alternatives are allowed, compare equivalent drinks and show material differences in volume or ingredients. Suggest a short list before searching every possible merchant.

## Compare actual paths

1. Inspect relevant available channels. For each, identify the exact drink and store, fulfillment method, item price, fees, ETA, and applicable account coupons. Include channels the buyer names; record any unavailable channel as a coverage gap.
2. Read each coupon's product, store, channel, time, threshold, cap, and stacking conditions. Check the discount in that path's cart or checkout. Mark untested claims explicitly. A coupon shown in a wallet is not proof it applies.
3. Inspect payment offers for the selected payment method at checkout. Verify whether they stack with the chosen coupon. Record store credit, prepaid cards, and wallet balances as payment funding, not savings.
4. Capture the final payable amount and payment funding. Do not submit an order while gathering quotes. Keep account data, addresses, screenshots, and session tokens out of the repository and public examples.
5. Use [the quote format](references/quote-format.md) and `python3 scripts/compare.py quotes.json` to check arithmetic, freshness, coverage, and comparable products. Model each payment method as a separate quote when it changes the payable total. The script ranks complete paths and marks gaps; it cannot establish coupon eligibility by itself.
6. Recommend the lowest verified payable path satisfying the buyer's constraints. Explain timing and any tradeoff. If coverage or incentives remain unverified, present the best observed path as provisional instead of claiming a verified cheapest option.

When the buyer asks to place the order, use the connected app or permitted UI path. Before submission, recheck the selected product, store, fulfillment, address or pickup location, coupon lines, payment method, fees, total, and ETA on the final page. Follow the buyer's existing authorization for the order; an unexpected price increase, substituted item, or new commitment requires their decision. Confirm success from the resulting order page or order history, and do not repeat a submission whose status is uncertain.

After submission, distinguish submitted, paid, accepted, preparing, ready for pickup or in transit, received, and completed. Report only states observed in the merchant app. If there is a problem, help with the app's remedy or refund flow and track its actual result. At receipt, check whether the drink and temperature match, then record the buyer's feedback only if useful for a future choice. Use `python3 scripts/journal.py` for an optional local lifecycle record; read [the journal guide](references/journal.md) when tracking an order across sessions. Keep private order records local and out of public repositories.

The skill does not require a particular platform API. Use a platform's supported connector when available or the buyer's accessible app UI. For a connected Android phone, `scripts/android_capture.py` lists devices and saves local screenshots for inspection; it does not tap, order, or pay. Do not assume any third-party GitHub project has merchant authorization or access to a buyer's account. When implementing a new channel adapter, read [the adapter contract](references/adapter-contract.md); ordinary orders do not need that reference.
