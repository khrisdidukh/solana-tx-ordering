"""Turn raw run data into per-validator / per-client conclusions.

Primary evidence: our own probes.
  For every block that contains >= 2 of our probes from one batch we compute
  Kendall's tau between block position and (a) priority fee, (b) send order.
  tau = +1  -> "higher fee is always earlier" / "earlier-sent is always earlier"
  tau =  0  -> no relation.  The null hypothesis "positions are a random
  permutation" is tested with a within-block permutation test, so the test
  is exact for small n and does not assume pairs are independent.

Supplementary evidence: every other transaction in the same blocks
  (Spearman correlation between position and fee per cost unit).
"""
import collections
import csv
import glob
import gzip
import json
import math
import os
import random

from .collect import read_jsonl


# ---------------- statistics ----------------
def kendall_tau(xs, ys):
    """tau-b without scipy."""
    n = len(xs)
    c = d = tx = ty = 0
    for i in range(n):
        for j in range(i + 1, n):
            dx, dy = xs[i] - xs[j], ys[i] - ys[j]
            if dx == 0 and dy == 0:
                continue
            if dx == 0:
                tx += 1
            elif dy == 0:
                ty += 1
            elif (dx > 0) == (dy > 0):
                c += 1
            else:
                d += 1
    denom = math.sqrt((c + d + tx) * (c + d + ty))
    return (c - d) / denom if denom else float("nan")


def spearman(xs, ys):
    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(v):
            j = i
            while j + 1 < len(v) and v[order[j + 1]] == v[order[i]]:
                j += 1
            for k in range(i, j + 1):
                r[order[k]] = (i + j) / 2.0
            i = j + 1
        return r
    if len(xs) < 3:
        return float("nan")
    rx, ry = ranks(xs), ranks(ys)
    mx, my = sum(rx) / len(rx), sum(ry) / len(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return num / den if den else float("nan")


def perm_test(groups, n_iter=4000, seed=7):
    """groups: list of (key_values, positions) per block.
    Statistic = mean tau(key, -position) over blocks (positive = 'higher key
    earlier').  Null: positions randomly permuted within each block."""
    groups = [(k, p) for k, p in groups if len(k) >= 2 and len(set(k)) >= 2]
    if not groups:
        return float("nan"), float("nan"), 0
    obs = sum(kendall_tau(k, [-x for x in p]) for k, p in groups) / len(groups)
    rng = random.Random(seed)
    ge = 0
    for _ in range(n_iter):
        s = 0.0
        for k, p in groups:
            q = p[:]
            rng.shuffle(q)
            s += kendall_tau(k, [-x for x in q])
        if abs(s / len(groups)) >= abs(obs) - 1e-12:
            ge += 1
    return obs, (ge + 1) / (n_iter + 1), len(groups)


# ---------------- loading ----------------
def load_blocks(run_dir):
    blocks = {}
    for p in glob.glob(os.path.join(run_dir, "blocks", "*.json.gz")):
        with gzip.open(p, "rt") as f:
            b = json.load(f)
        blocks[b["slot"]] = b
    return blocks


def verdict(tp, pp, ts, ps, n):
    if n == 0:
        return "no data (no block contained 2+ of our probes)"
    sp = pp < 0.01 and tp > 0
    ss = ps < 0.01 and ts > 0
    if sp and not ss:
        s = "strict" if tp >= 0.9 else "strong" if tp >= 0.6 else "partial"
        return f"priority-fee order ({s}, tau={tp:.2f})"
    if ss and not sp:
        s = "strict" if ts >= 0.9 else "strong" if ts >= 0.6 else "partial"
        return f"arrival order ({s}, tau={ts:.2f})"
    if sp and ss:
        return f"mixed: fee (tau={tp:.2f}) and arrival (tau={ts:.2f}) both matter"
    if n < 5:
        return f"inconclusive (only {n} blocks with 2+ probes)"
    return "no rule detected - consistent with noise"


def analyze(run_dir, log=print):
    probes = read_jsonl(os.path.join(run_dir, "probes.jsonl"))
    batches = {b["batch"]: b for b in read_jsonl(os.path.join(run_dir, "batches.jsonl"))
               if "batch" in b}
    blocks = load_blocks(run_dir)
    st_path = os.path.join(run_dir, "statuses.json")
    statuses = json.load(open(st_path)) if os.path.exists(st_path) else {}

    # where each probe ended up (verified against the fetched block, not only the status)
    pos_of = {}
    for slot, b in blocks.items():
        for sig, v in b["our_probes"].items():
            pos_of[sig] = (slot, v["pos"], b["n_tx"], b["leader"])
    landing_rows = []
    for p in probes:
        if p.get("send_error") == "dry-run":
            continue
        sig = p["signature"]
        ws = p["window_start"]
        where = "not_landed"
        slot = pos = ntx = leader = None
        if sig in pos_of:
            slot, pos, ntx, leader = pos_of[sig]
            where = ("target_window" if ws <= slot < ws + 4 and leader == p["leader"]
                     else "other_leader")
        elif statuses.get(sig):
            slot = statuses[sig]["slot"]
            where = "landed_block_not_fetched"
        landing_rows.append({**{k: p[k] for k in ("batch", "probe", "group", "cu_price", "send_rank",
                                                  "client", "leader", "window_start", "signature")},
                             "landed": where, "slot": slot, "slot_in_window": (slot - ws) if slot else None,
                             "pos": pos, "block_n_tx": ntx, "block_leader": leader,
                             "send_error": p.get("send_error")})

    # ------- primary: within-block ordering of our probes -------
    by_block = collections.defaultdict(list)
    for r in landing_rows:
        if r["landed"] == "target_window":
            by_block[(r["leader"], r["batch"], r["slot"])].append(r)
    window_groups = collections.defaultdict(list)
    for r in landing_rows:
        if r["landed"] == "target_window":
            window_groups[(r["leader"], r["batch"])].append(r)

    def tests(rows_by_key, group=None, across_window=False):
        prio, send = [], []
        for key, rows in rows_by_key.items():
            rows = [r for r in rows if group is None or r["group"] == group]
            if len(rows) < 2:
                continue
            posv = [(r["slot"] * 100000 + r["pos"]) if across_window else r["pos"] for r in rows]
            prio.append(([r["cu_price"] for r in rows], posv))
            send.append(([-r["send_rank"] for r in rows], posv))
        tp, pp, n = perm_test(prio)
        ts, ps, _ = perm_test(send)
        return {"tau_fee": tp, "p_fee": pp, "tau_send": ts, "p_send": ps, "n_blocks": n}

    leaders = sorted({r["leader"] for r in landing_rows})
    per_val = {}
    for ld in leaders:
        rows = [r for r in landing_rows if r["leader"] == ld]
        sub = {k: v for k, v in by_block.items() if k[0] == ld}
        subw = {k: v for k, v in window_groups.items() if k[0] == ld}
        res = {
            "client": rows[0]["client"],
            "batches": len({r["batch"] for r in rows}),
            "probes_sent": len(rows),
            "landed_target_window": sum(r["landed"] == "target_window" for r in rows),
            "landed_other_leader": sum(r["landed"] == "other_leader" for r in rows),
            "not_landed": sum(r["landed"] == "not_landed" for r in rows),
            "independent": tests(sub, "IND"),
            "conflicting": tests(sub, "CONF"),
            "all_in_block": tests(sub),
            "across_window": tests(subw, None, across_window=True),
        }
        a = res["independent"]
        res["verdict_independent"] = verdict(a["tau_fee"], a["p_fee"], a["tau_send"], a["p_send"], a["n_blocks"])
        c = res["conflicting"]
        res["verdict_conflicting"] = verdict(c["tau_fee"], c["p_fee"], c["tau_send"], c["p_send"], c["n_blocks"])
        per_val[ld] = res

    per_client = {}
    for cl in sorted({r["client"] for r in landing_rows}):
        sub = {k: v for k, v in by_block.items() if per_val[k[0]]["client"] == cl}
        t = tests(sub, "IND")
        tc = tests(sub, "CONF")
        per_client[cl] = {"validators": sum(v["client"] == cl for v in per_val.values()),
                          "independent": t, "conflicting": tc,
                          "verdict_independent": verdict(t["tau_fee"], t["p_fee"], t["tau_send"], t["p_send"], t["n_blocks"]),
                          "verdict_conflicting": verdict(tc["tau_fee"], tc["p_fee"], tc["tau_send"], tc["p_send"], tc["n_blocks"])}

    # landing by fee level (competition / QoS)
    by_level = collections.defaultdict(lambda: collections.Counter())
    for r in landing_rows:
        by_level[(r["group"], r["cu_price"])][r["landed"]] += 1

    # ------- supplementary: whole-block fee-density vs position -------
    passive = []
    window_leader = {}
    for b in batches.values():
        for s in range(b["window_start"], b["window_start"] + 4):
            window_leader[s] = (b["leader"], b["client"])
    for slot, b in sorted(blocks.items()):
        if slot not in window_leader:
            continue
        ld, cl = window_leader[slot]
        txs = [t for t in b["txs"] if not t["vote"] and t["cost"]]
        if len(txs) < 10:
            continue
        dens = [t["fee"] / t["cost"] for t in txs]
        posv = [t["pos"] for t in txs]
        nontip = [t for t in txs if not t["jito_tip"]]
        tip_pos = [t["pos"] / max(1, b["n_tx"] - 1) for t in txs if t["jito_tip"]]
        passive.append({
            "slot": slot, "leader": ld, "client": cl, "fetched_leader": b["leader"], "n_tx": b["n_tx"],
            "rho_density_vs_pos": spearman(dens, posv),
            "rho_density_vs_pos_no_tip": spearman([t["fee"] / t["cost"] for t in nontip],
                                                  [t["pos"] for t in nontip]),
            "frac_desc_adjacent": (sum(1 for a, b2 in zip(dens, dens[1:]) if a >= b2) / (len(dens) - 1)),
            "tip_txs": len(tip_pos),
            "tip_median_rel_pos": (sorted(tip_pos)[len(tip_pos) // 2] if tip_pos else None),
        })
    pas_client = collections.defaultdict(list)
    for r in passive:
        pas_client[r["client"]].append(r)

    def med(v):
        v = sorted(x for x in v if x == x and x is not None)
        return v[len(v) // 2] if v else None

    passive_summary = {cl: {"blocks": len(rs),
                            "median_rho": med([r["rho_density_vs_pos"] for r in rs]),
                            "median_rho_no_tip": med([r["rho_density_vs_pos_no_tip"] for r in rs]),
                            "median_frac_desc_adjacent": med([r["frac_desc_adjacent"] for r in rs]),
                            "median_tip_rel_pos": med([r["tip_median_rel_pos"] for r in rs])}
                       for cl, rs in sorted(pas_client.items())}

    out = {"per_validator": per_val, "per_client": per_client,
           "landing_by_fee_level": {f"{g}:{p}": dict(c) for (g, p), c in sorted(by_level.items())},
           "passive_by_client": passive_summary}
    adir = os.path.join(run_dir, "analysis")
    os.makedirs(adir, exist_ok=True)
    with open(os.path.join(adir, "results.json"), "w") as f:
        json.dump(out, f, indent=1)
    _csv(os.path.join(adir, "probe_landing.csv"), landing_rows)
    _csv(os.path.join(adir, "passive_blocks.csv"), passive)
    log(f"analysis written to {adir}")
    return out


def _csv(path, rows):
    if not rows:
        open(path, "w").close()
        return
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
