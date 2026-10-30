"""The experiment loop.

For every planned leader window we send one *batch* of probes timed to reach
the target leader while it is producing:

  group IND  - N_IND probes, each from its own fee payer (no lock conflicts)
  group CONF - N_CONF probes from ONE shared payer (write-lock conflict)

Inside every batch the priority-fee level of each probe and the order in which
probes are sent are two independent random permutations, so "ordered by fee"
and "ordered by arrival" predict different block positions and can be told
apart.  Dry-run (the default) does everything except the send.
"""
import asyncio
import json
import os
import random
import time

from solders.hash import Hash
from solders.keypair import Keypair

from . import cluster, txs
from .spend import SpendLedger

DEFAULT_LEVELS = [0, 1_000, 10_000, 50_000, 200_000, 1_000_000, 4_000_000, 16_000_000]
CONF_LEVELS = [10_000, 200_000, 1_000_000, 4_000_000]


class SlotClock:
    """Polls getSlot(processed) and extrapolates between polls."""

    def __init__(self, rpc, poll_s=0.4):  # public RPC: <=40 calls/10 s per method
        self.rpc, self.poll_s = rpc, poll_s
        self.slot, self.t = None, None
        self.slot_s = 0.4
        self.samples = []
        self._task = None

    async def start(self):
        await self._poll_once()
        self._task = asyncio.create_task(self._loop())

    async def stop(self):
        if self._task:
            self._task.cancel()

    async def _poll_once(self):
        s = await self.rpc.call("getSlot", [{"commitment": "processed"}])
        now = time.time()
        if self.slot is None or s > self.slot:
            self.samples.append((now, s))
            self.samples = self.samples[-200:]
            if len(self.samples) > 20:
                (t0, s0), (t1, s1) = self.samples[0], self.samples[-1]
                if s1 > s0:
                    self.slot_s = (t1 - t0) / (s1 - s0)
            self.slot, self.t = s, now

    async def _loop(self):
        while True:
            try:
                await self._poll_once()
            except Exception:  # noqa: BLE001 - keep the clock alive
                pass
            await asyncio.sleep(self.poll_s)

    def now(self) -> float:
        return self.slot + (time.time() - self.t) / self.slot_s

    async def wait_until(self, target: float):
        while self.now() < target:
            await asyncio.sleep(min(0.02, max(0.0, (target - self.now()) * self.slot_s)))


class Experiment:
    def __init__(self, rpc, send_rpcs, out_dir, keys_dir, live=False, max_spend_sol=0.05,
                 cu_limit=5000, levels=None, conf_levels=None, send_offset=0.0,
                 stagger_ms=3.0, seed=None, log=print):
        self.rpc, self.send_rpcs = rpc, send_rpcs
        self.out_dir, self.keys_dir = out_dir, keys_dir
        self.live = live
        self.cu_limit = cu_limit
        self.levels = levels or DEFAULT_LEVELS
        self.conf_levels = conf_levels or CONF_LEVELS
        self.send_offset = send_offset
        self.stagger = stagger_ms / 1000.0
        self.rng = random.Random(seed)
        self.seed = seed
        self.log = log
        self.n_ind = len(self.levels)
        self.ledger = SpendLedger(os.path.join(out_dir, "spend.json"),
                                  cap_lamports=int(max_spend_sol * 1e9))
        os.makedirs(out_dir, exist_ok=True)
        self.sent_path = os.path.join(out_dir, "probes.jsonl")
        self.batches_path = os.path.join(out_dir, "batches.jsonl")
        self.payers = []
        self.conf_payer = None
        self.blockhash, self.bh_t = None, 0

    # ---------- keys ----------
    def load_payers(self):
        path = os.path.join(self.keys_dir, "subpayers.json")
        if os.path.exists(path):
            with open(path) as f:
                ks = [Keypair.from_bytes(bytes(k)) for k in json.load(f)]
        else:
            ks = [Keypair() for _ in range(self.n_ind + 1)]
            if self.live:  # only persist keys that may ever hold funds
                os.makedirs(self.keys_dir, exist_ok=True)
                with open(path, "w") as f:
                    json.dump([list(bytes(k)) for k in ks], f)
                os.chmod(path, 0o600)
        if len(ks) < self.n_ind + 1:
            raise SystemExit("subpayers.json has fewer keys than fee levels; delete it after sweeping")
        self.payers, self.conf_payer = ks[:self.n_ind], ks[self.n_ind]

    # ---------- budget ----------
    def batch_max_cost(self):
        return (sum(txs.max_fee(self.cu_limit, p) for p in self.levels)
                + sum(txs.max_fee(self.cu_limit, p) for p in self.conf_levels))

    def payer_needs(self, n_batches):
        """Lamports each sub-payer must hold to pay for every batch."""
        per_ind = max(txs.max_fee(self.cu_limit, p) for p in self.levels) * n_batches
        per_conf = sum(txs.max_fee(self.cu_limit, p) for p in self.conf_levels) * n_batches
        return per_ind, per_conf

    # ---------- blockhash ----------
    async def fresh_blockhash(self):
        if self.blockhash is None or time.time() - self.bh_t > 20:
            r = await self.rpc.call("getLatestBlockhash", [{"commitment": "confirmed"}])
            self.blockhash = Hash.from_string(r["value"]["blockhash"])
            self.bh_t = time.time()
        return self.blockhash

    # ---------- batch ----------
    def build_batch(self, batch_id, bh):
        fee_perm = self.rng.sample(self.levels, len(self.levels))
        conf_perm = self.rng.sample(self.conf_levels, len(self.conf_levels))
        probes = []
        for i, price in enumerate(fee_perm):
            probes.append({"group": "IND", "payer_idx": i, "cu_price": price})
        for j, price in enumerate(conf_perm):
            probes.append({"group": "CONF", "payer_idx": self.n_ind, "cu_price": price})
        order = self.rng.sample(range(len(probes)), len(probes))
        for rank, k in enumerate(order):
            probes[k]["send_rank"] = rank
        for k, p in enumerate(probes):
            payer = self.payers[p["payer_idx"]] if p["group"] == "IND" else self.conf_payer
            memo = f"o{batch_id:x}.{k:x}"
            tx = txs.probe_tx(payer, bh, self.cu_limit, p["cu_price"], memo)
            p.update({"batch": batch_id, "probe": k, "memo": memo, "payer": str(payer.pubkey()),
                      "cu_limit": self.cu_limit, "signature": str(tx.signatures[0]),
                      "max_fee": txs.max_fee(self.cu_limit, p["cu_price"]),
                      "_wire": txs.b64(tx)})
        return probes

    async def send_batch(self, probes):
        """Fire requests in send_rank order, `stagger` apart, without waiting
        for each response (a response round-trip would spread the batch over
        several slots)."""
        ordered = sorted(probes, key=lambda p: p["send_rank"])
        tasks = []
        t0 = time.time()
        for i, p in enumerate(ordered):
            await asyncio.sleep(max(0.0, t0 + i * self.stagger - time.time()))
            tasks.append(asyncio.create_task(self.send_rpcs[0].send_raw(p["_wire"])))
        res = await asyncio.gather(*tasks)
        for p, (sig, err, ta, tb) in zip(ordered, res):
            p.update({"rpc_sig": sig, "send_error": err, "t_send": ta, "t_ack": tb,
                      "send_rpc": self.send_rpcs[0].url})

    # ---------- funding ----------
    async def fund(self, main: Keypair, n_batches):
        per_ind, per_conf = self.payer_needs(n_batches)
        rent = await self.rpc.call("getMinimumBalanceForRentExemption", [0])
        targets = [(p, per_ind + rent) for p in self.payers] + [(self.conf_payer, per_conf + rent)]
        transfers = []
        for kp, want in targets:
            bal = (await self.rpc.call("getBalance", [str(kp.pubkey())]))["value"]
            if bal < want:
                transfers.append((main.pubkey(), kp.pubkey(), want - bal))
        if not transfers:
            return 0
        need = sum(t[2] for t in transfers) + txs.BASE_FEE_PER_SIG
        main_bal = (await self.rpc.call("getBalance", [str(main.pubkey())]))["value"]
        if main_bal < need + 5000:
            raise SystemExit(f"Wallet {main.pubkey()} has {main_bal/1e9:.6f} SOL, needs "
                             f"{need/1e9:.6f} SOL to fund {len(transfers)} sub-payers. Top it up.")
        bh = await self.fresh_blockhash()
        tx = txs.transfer_tx(main, transfers, bh)
        self.ledger.add(txs.BASE_FEE_PER_SIG, "funding tx fee")
        sig = await self.rpc.call("sendTransaction", [txs.b64(tx), {"encoding": "base64"}])
        self.log(f"funding tx {sig}  ({len(transfers)} sub-payers, {sum(t[2] for t in transfers)/1e9:.6f} SOL parked, refundable)")
        await self.confirm(sig)
        return sum(t[2] for t in transfers)

    async def confirm(self, sig, timeout=60):
        t = time.time()
        while time.time() - t < timeout:
            st = (await self.rpc.call("getSignatureStatuses", [[sig]]))["value"][0]
            if st and st.get("confirmationStatus") in ("confirmed", "finalized"):
                if st.get("err"):
                    raise SystemExit(f"tx {sig} failed: {st['err']}")
                return st
            await asyncio.sleep(1)
        raise SystemExit(f"tx {sig} not confirmed in {timeout}s")

    async def sweep(self, main: Keypair, per_tx=4):
        """Send everything left on the sub-payers back to the main wallet.

        The main wallet pays the fees and each sub-payer transfers its whole
        balance, which closes it.  (A sub-payer cannot pay its own sweep fee
        when its balance is exactly the rent-exempt minimum: a fee payer must
        stay rent-exempt after the fee is taken.)"""
        self.load_payers()
        bh = await self.fresh_blockhash()
        out = []
        funded = []
        for kp in self.payers + [self.conf_payer]:
            bal = (await self.rpc.call("getBalance", [str(kp.pubkey()), {"commitment": "confirmed"}]))["value"]
            if bal > 0:
                funded.append((kp, bal))
        for i in range(0, len(funded), per_tx):
            chunk = funded[i:i + per_tx]
            tx = txs.transfer_tx(main, [(kp.pubkey(), main.pubkey(), bal) for kp, bal in chunk], bh,
                                 extra_signers=[kp for kp, _ in chunk])
            fee = txs.BASE_FEE_PER_SIG * (1 + len(chunk))
            self.ledger.add(fee, "sweep tx fee")
            sig = await self.rpc.call("sendTransaction", [txs.b64(tx), {"encoding": "base64"}])
            for kp, bal in chunk:
                out.append((str(kp.pubkey()), bal, sig))
        for sig in dict.fromkeys(s for _, _, s in out):
            try:
                await self.confirm(sig)
            except SystemExit as e:
                self.log(str(e))
        return out

    # ---------- main loop ----------
    async def run(self, plan, main: Keypair = None, smoke_first=True):
        self.load_payers()
        n = len(plan)
        cost = self.batch_max_cost()
        self.log(f"plan: {n} windows, worst-case fees {cost/1e9:.6f} SOL/batch, "
                 f"{n*cost/1e9:.5f} SOL total, cap {self.ledger.cap/1e9:.5f} SOL, "
                 f"mode={'LIVE' if self.live else 'DRY-RUN'}")
        if self.live:
            if n * cost + self.ledger.spent > self.ledger.cap:
                n = max(0, (self.ledger.cap - self.ledger.spent - 20 * txs.BASE_FEE_PER_SIG) // cost)
                plan = plan[:n]
                self.log(f"spend cap trims the plan to {n} windows")
            await self.fund(main, len(plan))
        clock = SlotClock(self.rpc)
        await clock.start()
        self.log(f"slot {clock.slot}, measured slot time ~{clock.slot_s*1000:.0f} ms")
        done = 0
        try:
            for bi, w in enumerate(plan):
                target = w["window_start"] + self.send_offset
                if clock.now() > target - 2:
                    self.log(f"skip window {w['window_start']} ({w['client']}): already passing")
                    self._write(self.batches_path, {**w, "batch": bi, "status": "skipped_late"})
                    continue
                # pre-build 3 slots ahead so signing is off the critical path
                await clock.wait_until(target - 3)
                bh = await self.fresh_blockhash()
                probes = self.build_batch(bi, bh)
                await clock.wait_until(target)
                fire_slot = clock.now()
                if self.live:
                    worst = sum(p["max_fee"] for p in probes)
                    if not self.ledger.can_spend(worst):
                        self.log("spend cap reached, stopping")
                        break
                    self.ledger.add(worst, f"batch {bi} (worst case)")
                    await self.send_batch(probes)
                else:
                    for p in probes:
                        p.update({"rpc_sig": None, "send_error": "dry-run", "t_send": time.time(),
                                  "t_ack": None, "send_rpc": None})
                # ground truth for the clock: the RPC's own processed slot right after firing
                try:
                    slot_after = await self.rpc.call("getSlot", [{"commitment": "processed"}], retry=False)
                except Exception:  # noqa: BLE001
                    slot_after = None
                for p in probes:
                    p.pop("_wire", None)
                    self._write(self.sent_path, {**p, "leader": w["leader"], "client": w["client"],
                                                 "window_start": w["window_start"],
                                                 "est_slot_at_fire": fire_slot})
                self._write(self.batches_path, {**w, "batch": bi, "status": "sent" if self.live else "dry_run",
                                                "est_slot_at_fire": fire_slot,
                                                "rpc_slot_after_fire": slot_after,
                                                "slot_time_ms": clock.slot_s * 1000})
                done += 1
                errs = sum(1 for p in probes if p.get("send_error") not in (None, "dry-run"))
                self.log(f"[{bi+1}/{len(plan)}] window {w['window_start']} {w['client']:<18} "
                         f"{w['leader'][:8]} fired at slot {fire_slot:.2f}"
                         + (f"  send errors: {errs}" if errs else ""))
        finally:
            await clock.stop()
        return done

    @staticmethod
    def _write(path, obj):
        with open(path, "a") as f:
            f.write(json.dumps(obj) + "\n")
