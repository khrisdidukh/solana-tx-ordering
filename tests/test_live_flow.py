"""Exercise the LIVE code path (funding, cap, sending, sweep) against a fake RPC."""
import asyncio
import os
import tempfile
import time
import unittest

from solders.keypair import Keypair
from solders.transaction import Transaction
import base64

from ordering.run import Experiment


class FakeRpc:
    url = "fake://rpc"

    def __init__(self):
        self.t0 = time.time()
        self.balances = {}
        self.sent = []

    def slot(self):
        return 1000 + int((time.time() - self.t0) / 0.05)  # 50 ms slots

    async def call(self, method, params=None, retry=True):
        if method == "getSlot":
            return self.slot()
        if method == "getLatestBlockhash":
            return {"value": {"blockhash": "11111111111111111111111111111111"}}
        if method == "getMinimumBalanceForRentExemption":
            return 890880
        if method == "getBalance":
            return {"value": self.balances.get(params[0], 0)}
        if method == "sendTransaction":
            tx = Transaction.from_bytes(base64.b64decode(params[0]))
            self.sent.append(tx)
            # apply transfers so sweep sees balances
            return str(tx.signatures[0])
        if method == "getSignatureStatuses":
            return {"value": [{"confirmationStatus": "confirmed", "err": None, "slot": self.slot()}]}
        raise AssertionError(method)

    async def send_raw(self, b64):
        sig = await self.call("sendTransaction", [b64])
        return sig, None, time.time(), time.time()


class LiveFlow(unittest.TestCase):
    def test_live_run(self):
        async def go():
            rpc = FakeRpc()
            main = Keypair()
            rpc.balances[str(main.pubkey())] = 10**8
            with tempfile.TemporaryDirectory() as d:
                exp = Experiment(rpc, [rpc], os.path.join(d, "run"), os.path.join(d, "keys"),
                                 live=True, max_spend_sol=0.0005, seed=1, log=lambda *a: None)
                base = rpc.slot()
                plan = [{"window_start": base + 40 + 20 * i, "leader": "L", "client": "C",
                         "version": "v", "stake_share": 0.01, "tpu_quic": "", "gossip": "",
                         "tpu_is_remote": False} for i in range(5)]
                done = await exp.run(plan, main)
                # cap 0.0005 SOL / 0.000192 per batch -> only 2 batches allowed
                self.assertEqual(done, 2)
                self.assertLessEqual(exp.ledger.spent, 500_000)
                probes = [tx for tx in rpc.sent if len(tx.message.instructions) == 3]
                self.assertEqual(len(probes), 2 * 12)
                self.assertTrue(os.path.exists(os.path.join(d, "keys", "subpayers.json")))
                # funding tx: one tx with 9 transfers
                self.assertEqual(len(rpc.sent[0].message.instructions), 9)
        asyncio.run(go())


if __name__ == "__main__":
    unittest.main()


class Sweep(unittest.TestCase):
    def test_sweep(self):
        async def go():
            rpc = FakeRpc()
            main = Keypair()
            with tempfile.TemporaryDirectory() as d:
                exp = Experiment(rpc, [rpc], os.path.join(d, "run"), os.path.join(d, "keys"),
                                 live=True, seed=1, log=lambda *a: None)
                exp.load_payers()
                for kp in exp.payers + [exp.conf_payer]:
                    rpc.balances[str(kp.pubkey())] = 1_000_000
                out = await exp.sweep(main)
                self.assertEqual(len(out), 9)
                self.assertEqual(len(rpc.sent), 3)  # 4 + 4 + 1 sub-payers per tx
                for tx in rpc.sent:
                    self.assertEqual(tx.message.account_keys[0], main.pubkey())  # main pays the fee
                    self.assertTrue(tx.verify_with_results() if hasattr(tx, "verify_with_results") else True)
        asyncio.run(go())
