import copy
import importlib.util
import json
import unittest
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("compare", ROOT / "drinkdrink/scripts/compare.py")
compare = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(compare)
NOW = datetime.fromisoformat("2026-10-13T09:05:00+08:00")


class CompareTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / "examples/quotes.json").read_text(encoding="utf-8"))

    def test_verified_winner_uses_payable_not_wallet_remainder(self):
        result = compare.evaluate(self.data, NOW)
        self.assertEqual(result["winner"], "pickup-wechat")
        self.assertEqual(result["ranked"][-1]["id"], "brand-delivery-wallet")
        self.assertEqual(result["ranked"][-1]["cash_due"], "25.00")

    def test_gap_or_untested_incentive_blocks_verified_winner(self):
        gap = copy.deepcopy(self.data)
        gap["coverage"][2]["status"] = "gap"
        gap["coverage"][2]["reason"] = "app unavailable"
        gap["quotes"] = [q for q in gap["quotes"] if q["channel"] != "Delivery marketplace"]
        self.assertIsNone(compare.evaluate(gap, NOW)["winner"])

        untested = copy.deepcopy(self.data)
        untested["quotes"][0]["incentives"].append({"name": "Bank coupon", "kind": "payment_offer", "outcome": "untested"})
        result = compare.evaluate(untested, NOW)
        self.assertIsNone(result["winner"])
        self.assertEqual(result["verdict"], "provisional")

    def test_wrong_checkout_arithmetic_is_rejected(self):
        self.data["quotes"][0]["checkout"]["payable"] = "18.00"
        with self.assertRaisesRegex(compare.QuoteError, "payable does not equal"):
            compare.evaluate(self.data, NOW)

    def test_size_and_fulfillment_filter(self):
        self.data["request"]["min_volume_ml"] = 475
        self.data["request"]["allowed_fulfillment"] = ["delivery"]
        result = compare.evaluate(self.data, NOW)
        self.assertEqual(result["winner"], "marketplace-alipay")
        self.assertEqual({q["id"] for q in result["excluded"]}, {"pickup-wechat", "brand-delivery-wallet"})

    def test_stale_quote_is_provisional(self):
        self.data["quotes"][0]["observed_at"] = "2026-10-13T08:00:00+08:00"
        result = compare.evaluate(self.data, NOW)
        self.assertIsNone(result["winner"])
        self.assertIn("quote is stale", result["ranked"][0]["issues"])

    def test_unchecked_payment_path_is_a_visible_gap(self):
        self.data["coverage"].append({
            "path_id": "pickup-alipay", "channel": "Brand pickup", "fulfillment": "pickup",
            "payment_method": "Alipay", "status": "gap", "reason": "payment page unavailable",
        })
        result = compare.evaluate(self.data, NOW)
        self.assertIsNone(result["winner"])
        self.assertIn("pickup-alipay: payment page unavailable", result["coverage_gaps"])

    def test_quote_must_match_its_declared_path(self):
        self.data["quotes"][0]["payment_method"] = "Alipay"
        with self.assertRaisesRegex(compare.QuoteError, "differs from coverage path"):
            compare.evaluate(self.data, NOW)


if __name__ == "__main__":
    unittest.main()
