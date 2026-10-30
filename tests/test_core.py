import os
import random
import tempfile
import unittest

from ordering.analyze import kendall_tau, perm_test, spearman, verdict
from ordering.spend import SpendLedger
from ordering import txs
from ordering.cluster import leader_windows


class Stats(unittest.TestCase):
    def test_kendall(self):
        self.assertAlmostEqual(kendall_tau([1, 2, 3, 4], [1, 2, 3, 4]), 1.0)
        self.assertAlmostEqual(kendall_tau([1, 2, 3, 4], [4, 3, 2, 1]), -1.0)

    def test_spearman(self):
        self.assertAlmostEqual(spearman([1, 2, 3, 4], [10, 20, 30, 40]), 1.0)

    def test_perm_detects_fee_order(self):
        # higher fee always earlier (smaller position) in 10 blocks of 6 probes
        rng = random.Random(1)
        groups = []
        for _ in range(10):
            fees = rng.sample(range(100), 6)
            pos = [sorted(fees, reverse=True).index(f) * 7 + 3 for f in fees]
            groups.append((fees, pos))
        tau, p, n = perm_test(groups, n_iter=500)
        self.assertEqual(n, 10)
        self.assertAlmostEqual(tau, 1.0)
        self.assertLess(p, 0.01)

    def test_perm_null(self):
        rng = random.Random(2)
        groups = [(rng.sample(range(100), 6), rng.sample(range(500), 6)) for _ in range(10)]
        tau, p, n = perm_test(groups, n_iter=500)
        self.assertGreater(p, 0.01)

    def test_verdict(self):
        self.assertIn("priority-fee", verdict(0.95, 0.001, 0.0, 0.8, 12))
        self.assertIn("arrival", verdict(0.0, 0.7, 0.8, 0.001, 12))
        self.assertIn("noise", verdict(0.05, 0.5, 0.02, 0.6, 12))
        self.assertIn("inconclusive", verdict(0.05, 0.5, 0.02, 0.6, 2))


class Spend(unittest.TestCase):
    def test_cap_and_persistence(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "spend.json")
            led = SpendLedger(p, 100_000)
            led.add(60_000, "a")
            self.assertFalse(led.can_spend(50_000))
            with self.assertRaises(SystemExit):
                led.add(50_000, "b")
            self.assertEqual(SpendLedger(p, 100_000).spent, 60_000)  # survives restart

    def test_max_fee(self):
        self.assertEqual(txs.max_fee(5000, 0), 5000)
        self.assertEqual(txs.max_fee(5000, 1_000_000), 10_000)
        self.assertEqual(txs.max_fee(5000, 1), 5001)  # rounds up


class Windows(unittest.TestCase):
    def test_window_starts(self):
        snap = {"epoch": {"absoluteSlot": 1000, "slotIndex": 0},
                "leader_schedule": {"A": [0, 1, 2, 3, 8, 9, 10, 11, 12, 13, 14, 15]}}
        self.assertEqual(leader_windows(snap, "A"), [1000, 1008, 1012])


if __name__ == "__main__":
    unittest.main()
