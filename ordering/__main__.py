"""CLI.  Dry-run is the default everywhere; only `--live` sends transactions.

  python -m ordering keygen            create the experiment wallet (keys/ volume)
  python -m ordering wallet            show its address and balance
  python -m ordering plan              snapshot the cluster and print the target plan
  python -m ordering run [--live]      plan + send + collect + analyze + report
  python -m ordering collect RUN_DIR   (re)fetch statuses and blocks for a run
  python -m ordering analyze RUN_DIR   (re)compute analysis and report
  python -m ordering sweep             return all sub-payer lamports to the wallet
"""
import argparse
import asyncio
import datetime
import json
import os
import sys

from . import analyze as an
from . import cluster, report, txs
from .collect import collect
from .rpc import Rpc
from .run import DEFAULT_LEVELS, Experiment


def env(k, d):
    return os.environ.get(k, d)


def args():
    ap = argparse.ArgumentParser(prog="ordering")
    ap.add_argument("cmd", choices=["keygen", "wallet", "plan", "run", "collect", "analyze", "sweep", "combine"])
    ap.add_argument("run_dir", nargs="?")
    ap.add_argument("more_runs", nargs="*", help="combine: further run directories")
    ap.add_argument("--out", default=env("OUT_DIR", "data/combined"), help="combine: output directory")
    ap.add_argument("--rpc", default=env("RPC_URL", "https://api.mainnet-beta.solana.com"))
    ap.add_argument("--send-rpc", default=env("SEND_RPC_URL", ""),
                    help="RPC used for sendTransaction (default: same as --rpc)")
    ap.add_argument("--keypair", default=env("KEYPAIR", "keys/wallet.json"))
    ap.add_argument("--keys-dir", default=env("KEYS_DIR", "keys"))
    ap.add_argument("--data-dir", default=env("DATA_DIR", "data"))
    ap.add_argument("--live", action="store_true", default=env("LIVE", "0") == "1",
                    help="actually send transactions (otherwise dry-run)")
    ap.add_argument("--max-spend-sol", type=float, default=float(env("MAX_SPEND_SOL", "0.05")))
    ap.add_argument("--clients", default=env("CLIENTS", ",".join(cluster.DEFAULT_CLIENTS)))
    ap.add_argument("--per-client", type=int, default=int(env("PER_CLIENT", "2")))
    ap.add_argument("--windows", type=int, default=int(env("WINDOWS_PER_VALIDATOR", "4")))
    ap.add_argument("--horizon-slots", type=int, default=int(env("HORIZON_SLOTS", "9000")))
    ap.add_argument("--send-offset", type=float, default=float(env("SEND_OFFSET_SLOTS", "0")),
                    help="fire at window_start + offset (slots)")
    ap.add_argument("--cu-limit", type=int, default=int(env("CU_LIMIT", "5000")))
    ap.add_argument("--seed", type=int, default=int(env("SEED", "20261030")))
    ap.add_argument("--yes", action="store_true", default=env("YES", "0") == "1",
                    help="skip the interactive confirmation before a live run")
    return ap.parse_args()


async def main():
    a = args()
    if a.cmd == "keygen":
        if os.path.exists(a.keypair):
            print(f"{a.keypair} already exists, not overwriting")
        else:
            from solders.keypair import Keypair
            txs.save_keypair(Keypair(), a.keypair)
        kp = txs.load_keypair(a.keypair)
        print(f"experiment wallet address: {kp.pubkey()}")
        return

    rpc = Rpc(a.rpc)
    send_rpc = Rpc(a.send_rpc) if a.send_rpc else rpc
    try:
        if a.cmd == "wallet":
            kp = txs.load_keypair(a.keypair)
            bal = (await rpc.call("getBalance", [str(kp.pubkey())]))["value"]
            print(f"address {kp.pubkey()}  balance {bal/1e9:.6f} SOL")
            return

        if a.cmd == "plan":
            snap = await cluster.snapshot(rpc)
            table = cluster.validator_table(snap)
            print(json.dumps(cluster.client_summary(table), indent=1))
            plan, targets = cluster.pick_targets(snap, a.clients.split(","), a.per_client,
                                                 a.windows, a.horizon_slots)
            for p in plan:
                print(p["window_start"], p["client"], p["leader"], p["version"],
                      f"{p['stake_share']*100:.2f}%", "remote-tpu" if p["tpu_is_remote"] else "")
            span = (plan[-1]["window_start"] - snap["epoch"]["absoluteSlot"]) if plan else 0
            print(f"{len(plan)} windows, {len(targets)} validators, "
                  f"{len({p['client'] for p in plan})} clients, last window in ~{span*0.215/60:.0f} min (at ~215 ms/slot)")
            return

        if a.cmd == "sweep":
            main_kp = txs.load_keypair(a.keypair)
            exp = Experiment(rpc, [send_rpc], os.path.join(a.data_dir, "_sweep"), a.keys_dir,
                             live=True, max_spend_sol=a.max_spend_sol)
            for pk, bal, sig in await exp.sweep(main_kp):
                print(f"swept {bal/1e9:.6f} SOL from {pk}: {sig}")
            return

        if a.cmd == "combine":
            if not a.run_dir:
                sys.exit("usage: combine RUN_DIR [RUN_DIR ...] --out DIR")
            os.makedirs(a.out, exist_ok=True)
            an.analyze(a.run_dir, extra_runs=a.more_runs, out_dir=os.path.join(a.out, "analysis"))
            report.write(a.run_dir, extra_runs=a.more_runs, out_dir=a.out)
            print(f"combined report: {os.path.join(a.out, 'REPORT.md')}")
            return

        if a.cmd in ("collect", "analyze"):
            if not a.run_dir:
                sys.exit("give the run directory, e.g. data/run-20261030T190000Z")
            if a.cmd == "collect":
                await collect(rpc, a.run_dir)
            an.analyze(a.run_dir)
            report.write(a.run_dir)
            return

        # ---------------- run ----------------
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        run_dir = os.path.join(a.data_dir, f"run-{stamp}{'' if a.live else '-dryrun'}")
        os.makedirs(run_dir, exist_ok=True)
        snap = await cluster.snapshot(rpc)
        cluster.save({k: v for k, v in snap.items() if k != "leader_schedule"},
                     os.path.join(run_dir, "cluster_snapshot.json"))
        table = cluster.validator_table(snap)
        cluster.save(table, os.path.join(run_dir, "validators.json"))
        plan, targets = cluster.pick_targets(snap, a.clients.split(","), a.per_client,
                                             a.windows, a.horizon_slots)
        cluster.save(plan, os.path.join(run_dir, "plan.json"))
        meta = {"started_utc": stamp, "live": a.live, "rpc": a.rpc, "send_rpc": send_rpc.url,
                "max_spend_sol": a.max_spend_sol, "cu_limit": a.cu_limit, "levels": DEFAULT_LEVELS,
                "seed": a.seed, "send_offset_slots": a.send_offset,
                "rpc_version": snap["rpc_version"], "epoch": snap["epoch"]}
        cluster.save(meta, os.path.join(run_dir, "run_meta.json"))
        print(f"run dir: {run_dir}")
        print(f"{len(plan)} windows over {len(targets)} validators / "
              f"{len({p['client'] for p in plan})} clients")
        main_kp = None
        exp = Experiment(rpc, [send_rpc], run_dir, a.keys_dir, live=a.live,
                         max_spend_sol=a.max_spend_sol, cu_limit=a.cu_limit,
                         send_offset=a.send_offset, seed=a.seed)
        if a.live:
            main_kp = txs.load_keypair(a.keypair)
            bal = (await rpc.call("getBalance", [str(main_kp.pubkey())]))["value"]
            print(f"LIVE run from {main_kp.pubkey()} (balance {bal/1e9:.6f} SOL), "
                  f"spend cap {a.max_spend_sol} SOL")
            if not a.yes:
                if input("type YES to send real transactions: ").strip() != "YES":
                    sys.exit("aborted")
        try:
            await exp.run(plan, main_kp)
            if a.live:
                print("waiting 40 s for finalization before collecting...")
                await asyncio.sleep(40)
            try:
                await collect(rpc, run_dir)
                an.analyze(run_dir)
                report.write(run_dir)
            except Exception as e:  # noqa: BLE001 - raw data is already on disk
                print(f"collect/analyze failed ({e!r}); raw data is saved, re-run: collect {run_dir}")
        finally:
            if a.live:
                await _finish_live(rpc, exp, main_kp, bal, run_dir, a)
        print(f"done. report: {os.path.join(run_dir, 'REPORT.md')}")
    finally:
        await rpc.close()
        if send_rpc is not rpc:
            await send_rpc.close()


async def _finish_live(rpc, exp, main_kp, bal, run_dir, a):
    """Always runs after a live run, even if collection failed: return funds."""
    if True:
        print("returning sub-payer balances to the wallet...")
        for pk, b, sig in await exp.sweep(main_kp):
            print(f"  swept {b/1e9:.6f} SOL from {pk}")
        end = (await rpc.call("getBalance", [str(main_kp.pubkey())]))["value"]
        cluster.save({"start_lamports": bal, "end_lamports": end,
                      "actual_spend_lamports": bal - end,
                      "ledger_worst_case_lamports": exp.ledger.spent},
                     os.path.join(run_dir, "spend_actual.json"))
        print(f"actual spend: {(bal-end)/1e9:.6f} SOL (cap {a.max_spend_sol})")


if __name__ == "__main__":
    asyncio.run(main())
