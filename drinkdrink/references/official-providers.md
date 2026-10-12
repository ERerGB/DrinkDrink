# Official provider surfaces

Checked 2026-10-13. Each entry has a separate manifest in `providers/manifests/`; run `python3 drinkdrink/scripts/provider_catalog.py list` from the repository root to inspect them. This inventory records official public entry points. Connection and buyer login are separate steps.

| Module | Current scope | Source |
|---|---|---|
| `luckin_mcp` | Consumer MCP: stores, products, preview, order, status, cancellation | [瑞幸 MCP](https://open.lkcoffee.com/mcp), [tool docs](https://open.lkcoffee.com/docs) |
| `luckin_cli` | Official CLI distribution; no command adapter yet | [瑞幸 CLI](https://open.lkcoffee.com/cli) |
| `luckin_skill` | Official My Coffee Skill distribution; not bundled here | [瑞幸 Skill](https://open.lkcoffee.com/skill) |
| `mcd_china_mcp` | Consumer MCP: stores, menu, coupons, price calculation, order, status, cancellation | [麦当劳中国官方仓库](https://github.com/M-China/mcd-mcp-server) |
| `meituan_developer` | Research only: developer portal; consumer ordering access unverified | [美团开放平台](https://developer.meituan.com/) |

瑞幸 MCP uses Streamable HTTP at `https://gwmcp.lkcoffee.com/order/user/mcp`; the buyer obtains a Bearer token through the [official platform](https://open.lkcoffee.com/mcp). Its preview may return coupon and payable fields. A preview is still channel and session specific, and its payment outcome must be observed after the order. The official [CLI](https://open.lkcoffee.com/cli) and [Skill](https://open.lkcoffee.com/skill) are independent upstream distributions; DrinkDrink does not download or execute them.

麦当劳中国 documents Streamable HTTP at `https://mcp.mcd.cn` and token setup on its [official MCP site](https://open.mcd.cn/mcp). Its [tool list](https://github.com/M-China/mcd-mcp-server/blob/main/README.md) includes price calculation, coupon lookup, delivery and pickup ordering, and order queries. The mapped `auto-bind-coupons` claims all currently available 麦麦省 coupons, so it is an account mutation and requires an explicit buyer instruction. Follow the vendor terms and keep tokens outside the repository.

美团's official [developer portal](https://developer.meituan.com/) advertises MCP/Skills, but the public material checked here did not establish a buyer-account ordering endpoint. Keep it research only until an official consumer access contract is verified. Starbucks' official app and mini-program routes can still be inspected through the buyer's session; this catalog does not claim an official public consumer MCP or CLI for them.

The provider call layer does not prove coupon eligibility, normalize checkout totals, or select a payment method. It returns upstream data for the agent to inspect and compare under [the quote contract](quote-format.md). Source checks should revisit authentication, tool names and argument schemas, coupon behavior, monetary units, fulfillment coverage, terms, and the distinction between order creation and completed payment.
