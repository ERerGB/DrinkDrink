import tempfile
import unittest
from pathlib import Path

from drinkdrink.providers import (
    AuthorizationError, CatalogError, MutationAuthorization,
    argument_digest, load_catalog,
)


class ProviderTests(unittest.TestCase):
    def setUp(self):
        self.catalog = load_catalog()
        self.calls = []

    def invoke(self, endpoint, tool, arguments):
        self.calls.append((endpoint, tool, arguments))
        return {"upstream": "raw result"}

    def test_catalog_declares_only_verified_consumer_mcp_actions(self):
        self.assertEqual(len(self.catalog), 5)
        self.assertTrue(self.catalog["luckin_mcp"].supports("preview_order"))
        self.assertTrue(self.catalog["mcd_china_mcp"].supports("my_coupons"))
        self.assertFalse(self.catalog["meituan_developer"].supports("create_order"))
        self.assertFalse(self.catalog["luckin_cli"].supports("create_order"))

    def test_read_call_uses_injected_transport_and_preserves_result(self):
        module = self.catalog["luckin_mcp"]
        args = {"deptId": "example-store", "productList": []}
        result = module.call("preview_order", args, self.invoke, available_tools={"previewOrder"})
        self.assertEqual(result, {"upstream": "raw result"})
        self.assertEqual(self.calls, [(module.endpoint, "previewOrder", args)])

    def test_mutation_requires_exact_authorized_arguments(self):
        module = self.catalog["luckin_mcp"]
        args = {"orderId": "example-order"}
        with self.assertRaises(AuthorizationError):
            module.call("cancel_order", args, self.invoke)
        authorization = MutationAuthorization(
            "cancel_order", argument_digest(args), "Buyer requested cancellation of this order"
        )
        with self.assertRaises(AuthorizationError):
            module.call("cancel_order", {"orderId": "another-order"}, self.invoke,
                        authorization=authorization)
        self.assertEqual(self.calls, [])
        module.call("cancel_order", args, self.invoke, authorization=authorization)
        self.assertEqual(self.calls[-1][1], "cancelOrder")

    def test_unlisted_tool_cannot_be_called(self):
        module = self.catalog["mcd_china_mcp"]
        with self.assertRaises(CatalogError):
            module.call("preview_order", {}, self.invoke, available_tools={"query-meals"})
        self.assertEqual(self.calls, [])

    def test_unclassified_action_defaults_to_authorization(self):
        module = self.catalog["luckin_mcp"]
        with self.assertRaises(AuthorizationError):
            module.call("switch_product", {}, self.invoke)
        self.assertEqual(self.calls, [])

    def test_invalid_source_rejected(self):
        root = Path(__file__).resolve().parents[1]
        source = root / "drinkdrink/providers/manifests/luckin_mcp.json"
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "luckin_mcp.json"
            target.write_text(source.read_text().replace("https://open.lkcoffee.com/mcp", "http://example.test"))
            with self.assertRaisesRegex(CatalogError, "HTTPS"):
                load_catalog(Path(tmp))


if __name__ == "__main__":
    unittest.main()
