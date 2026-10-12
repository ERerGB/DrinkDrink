# Channel adapter contract

This is the contract for merchant or app integrations. The official MCP catalog implements a tool-call boundary; it does not itself log in or convert upstream responses into verified checkout quotes. Prefer supported connectors. A UI adapter may use the buyer's accessible app session. Never publish tokens, addresses, screenshots, or real orders.

An adapter may implement only the capabilities it can actually verify:

| Capability | Output or requirement |
|---|---|
| Discover | Drink name, store, variant, price indication, availability, fulfillment, ETA, observation time |
| Checkout quote | A `quote-format.md` path with item and fee lines, applied discounts, payment method, payable, and evidence from the selected cart or final page |
| Submit | One order action on buyer instruction, followed by a confirmed order identifier or an explicit uncertain result; never retry an uncertain submission blindly |
| Observe status | Merchant-visible order, payment, preparation, delivery/pickup, and refund states with observation time |

The adapter should declare its platform, access method, supported capabilities, and known gaps. It must report `gap` when login, a payment choice, coupon wallet, or checkout cannot be read. It cannot promote a wallet coupon to an applied discount, infer a payment offer from advertising, or treat a stored-value balance as savings. Coupon rules are evaluated for the selected product, store, channel, time, minimum spend, and stacking conditions in the live session.

One checkout quote is one selected payment and fulfillment path. If switching payment method changes the payable amount, create another path. If a channel cannot expose final checkout, it may return a provisional quote but must not mark `checkout.verified` true. Product and order screenshots belong only in private local working files.

## Official MCP modules

`providers/manifests/*.json` stores one official surface per file. `providers/catalog.py` loads and validates the manifest, maps common actions to documented tool names, and calls an injected, already authenticated MCP transport. Pass the host's live tool names to `available_tools` when possible; a manifest alone does not establish live availability. The transport receives the endpoint, upstream tool name and unmodified arguments, and its raw result is returned. Inspect live tool schemas and prices before building a `quote-format.md` record; never infer a monetary unit from an example response.

For `create_order`, `cancel_order`, `claim_coupon`, or any action not classified as read-only, supply `MutationAuthorization(action, argument_digest(arguments), instruction)` from the buyer's instruction for the exact final arguments. Recheck the approved checkout before creating an order. Do not automatically retry an uncertain tool result. The object is a local guard, not an authentication token or proof of vendor acceptance. Classify newly added actions only after checking their account effects in current vendor documentation.

When maintaining a module, update its official source link, mapping, scope, notes and `verified_on` only after inspecting the current vendor documentation. Run `scripts/provider_catalog.py audit` to find entries that need rechecking. A CLI or Skill entry with no capability map is an upstream distribution reference, not an executable adapter.
