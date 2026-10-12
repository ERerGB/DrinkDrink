# Channel adapter contract

This is a design contract for future merchant or app integrations, not a claim that an integration exists. Prefer supported connectors. A UI adapter may use the buyer's accessible app session. Never publish tokens, addresses, screenshots, or real orders.

An adapter may implement only the capabilities it can actually verify:

| Capability | Output or requirement |
|---|---|
| Discover | Drink name, store, variant, price indication, availability, fulfillment, ETA, observation time |
| Checkout quote | A `quote-format.md` path with item and fee lines, applied discounts, payment method, payable, and evidence from the selected cart or final page |
| Submit | One order action on buyer instruction, followed by a confirmed order identifier or an explicit uncertain result; never retry an uncertain submission blindly |
| Observe status | Merchant-visible order, payment, preparation, delivery/pickup, and refund states with observation time |

The adapter should declare its platform, access method, supported capabilities, and known gaps. It must report `gap` when login, a payment choice, coupon wallet, or checkout cannot be read. It cannot promote a wallet coupon to an applied discount, infer a payment offer from advertising, or treat a stored-value balance as savings. Coupon rules are evaluated for the selected product, store, channel, time, minimum spend, and stacking conditions in the live session.

One checkout quote is one selected payment and fulfillment path. If switching payment method changes the payable amount, create another path. If a channel cannot expose final checkout, it may return a provisional quote but must not mark `checkout.verified` true. Product and order screenshots belong only in private local working files.
