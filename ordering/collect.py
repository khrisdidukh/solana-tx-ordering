"""Collect evidence after a run: where every probe landed, and the blocks.

For every fetched block we keep a compact per-transaction table in block
order (position, signature, fee, cost units, CU consumed, flags) plus the
full RPC JSON of our own probes.  Anyone can re-check any claim with
`getBlock <slot>` and compare positions/signatures.
"""
import asyncio
import gzip
import json
import os

from .rpc import BLOCK_OPTS, RpcError

JITO_TIP_ACCOUNTS = {
    "96gYZGLnJYVFmbjzopPSU6QiEV5fGqZNyN9nmNhvrZU5", "HFqU5x63VTqvQss8hp11i4wVV8bD44PvwucfZ2bU7gRe",
    "Cw8CFyM9FkoMi7K7Crf6HNQqf4uEMzpKw6QNghXLvLkY", "ADaUMid9yfUytqMBgopwjb2DTLSokTSzL1zt6iGPaS49",
    "DfXygSm4jCyNCybVYYK6DwvWqjKee8pbDmJGcLWNDXjh", "ADuUkR4vqLUMWXxW9gh6D6L8pMSawimctcNZ5pGwDcEt",
    "DttWaMuVvTiduZRnguLF7jNxTgiMBZ1hyAumKUiL2KRL", "3AVi9Tg9Uo68tJfuvoKvqKNWKkC5wPdSSdeBnizKZ6jT",
}
VOTE_PROGRAM = "Vote111111111111111111111111111111111111111"


def read_jsonl(path):
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def compact_block(slot, leader, block, probe_sigs):
    rows, ours = [], {}
    for i, t in enumerate(block["transactions"]):
        msg = t["transaction"]["message"]
        keys = list(msg["accountKeys"])
        meta = t.get("meta") or {}
        lw = meta.get("loadedAddresses") or {}
        all_keys = keys + lw.get("writable", []) + lw.get("readonly", [])
        sig = t["transaction"]["signatures"][0]
        nsig = msg["header"]["numRequiredSignatures"]
        rows.append({
            "pos": i, "sig": sig, "fee": meta.get("fee"),
            "cost": meta.get("costUnits"), "cu": meta.get("computeUnitsConsumed"),
            "nsig": nsig, "ok": meta.get("err") is None,
            "vote": VOTE_PROGRAM in keys,
            "jito_tip": any(k in JITO_TIP_ACCOUNTS for k in all_keys),
            "payer": keys[0],
        })
        if sig in probe_sigs:
            ours[sig] = {"pos": i, "raw": t}
    return {"slot": slot, "leader": leader, "blockhash": block.get("blockhash"),
            "parentSlot": block.get("parentSlot"), "blockTime": block.get("blockTime"),
            "blockHeight": block.get("blockHeight"), "n_tx": len(rows),
            "txs": rows, "our_probes": ours}


async def statuses(rpc, sigs):
    out = {}
    for i in range(0, len(sigs), 200):
        chunk = sigs[i:i + 200]
        r = await rpc.call("getSignatureStatuses", [chunk, {"searchTransactionHistory": True}])
        for s, st in zip(chunk, r["value"]):
            out[s] = st
    return out


async def collect(rpc, run_dir, log=print, concurrency=1, pause_s=0.4):
    probes = read_jsonl(os.path.join(run_dir, "probes.jsonl"))
    batches = read_jsonl(os.path.join(run_dir, "batches.jsonl"))
    live = [p for p in probes if p.get("rpc_sig") or p.get("send_error") in (None,)]
    sigs = [p["signature"] for p in probes if p.get("send_error") != "dry-run"]
    st = await statuses(rpc, sigs) if sigs else {}
    landed = {s: v for s, v in st.items() if v}
    with open(os.path.join(run_dir, "statuses.json"), "w") as f:
        json.dump(st, f, indent=1)
    log(f"probes sent: {len(sigs)}, landed: {len(landed)}")

    slots = set(v["slot"] for v in landed.values())
    for b in batches:
        if b.get("status") in ("sent", "dry_run"):
            slots.update(range(b["window_start"], b["window_start"] + 4))
    slots = sorted(slots)
    bdir = os.path.join(run_dir, "blocks")
    os.makedirs(bdir, exist_ok=True)

    leaders = {}
    if slots:
        lo, hi = slots[0], slots[-1]
        for start in range(lo, hi + 1, 4000):
            lim = min(4000, hi + 1 - start)
            for k, ident in enumerate(await rpc.call("getSlotLeaders", [start, lim])):
                leaders[start + k] = ident

    probe_sigs = set(sigs)
    sem = asyncio.Semaphore(concurrency)
    skipped, failed = [], []

    async def one(slot):
        path = os.path.join(bdir, f"{slot}.json.gz")
        if os.path.exists(path):
            return
        async with sem:
            try:
                blk = await rpc.call("getBlock", [slot, BLOCK_OPTS])
            except RpcError as e:  # skipped slot / not available
                skipped.append({"slot": slot, "leader": leaders.get(slot), "error": e.err})
                return
            except Exception as e:  # noqa: BLE001 - rate limit / network: keep going, re-run collect later
                failed.append({"slot": slot, "error": repr(e)[:200]})
                return
            finally:
                await asyncio.sleep(pause_s)  # public RPC getBlock rate limit
        if blk is None:
            skipped.append({"slot": slot, "leader": leaders.get(slot), "error": "null"})
            return
        with gzip.open(path, "wt") as f:
            json.dump(compact_block(slot, leaders.get(slot), blk, probe_sigs), f)

    await asyncio.gather(*(one(s) for s in slots))
    with open(os.path.join(run_dir, "skipped_slots.json"), "w") as f:
        json.dump(skipped, f, indent=1)
    log(f"blocks fetched: {len(slots) - len(skipped) - len(failed)}, skipped/unavailable: {len(skipped)}"
        + (f", failed (re-run `collect {run_dir}` to retry): {len(failed)}" if failed else ""))
    return len(slots)
