import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("journal", ROOT / "drinkdrink/scripts/journal.py")
journal = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(journal)


class JournalTests(unittest.TestCase):
    def test_full_pickup_lifecycle_with_independent_payment(self):
        state = {"version": 1, "orders": []}
        order = journal.start(state, "iced tea")
        for event in ("discovered", "quoted", "selected", "submitted"):
            journal.record(state, order["id"], event, evidence="app confirmation" if event == "submitted" else "")
        journal.record(state, order["id"], "payment_paid", evidence="payment success in app")
        journal.record(state, order["id"], "accepted", evidence="merchant accepted in app")
        journal.record(state, order["id"], "ready_for_pickup")
        journal.record(state, order["id"], "received", evidence="buyer confirmed")
        journal.record(state, order["id"], "completed")
        self.assertEqual(order["stage"], "completed")
        self.assertEqual(len(order["events"]), 10)

    def test_cannot_infer_submission_or_payment(self):
        state = {"version": 1, "orders": []}
        order = journal.start(state, "latte")
        with self.assertRaisesRegex(ValueError, "before a path is selected"):
            journal.record(state, order["id"], "payment_paid", evidence="none")
        journal.record(state, order["id"], "discovered")
        journal.record(state, order["id"], "quoted")
        journal.record(state, order["id"], "selected")
        with self.assertRaisesRegex(ValueError, "requires observed evidence"):
            journal.record(state, order["id"], "submitted")
        self.assertEqual(order["stage"], "selected")


if __name__ == "__main__":
    unittest.main()
