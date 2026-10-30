"""Cluster snapshot: who runs what, how much stake, and when they lead."""
import collections
import json
import time

# Order in which client families are preferred when picking targets.
DEFAULT_CLIENTS = ["AgaveBam", "JitoLabs", "HarmonicAgave", "HarmonicFiredancer",
                   "Firedancer", "FireBAM", "Agave", "Rakurai"]

SLOTS_PER_WINDOW = 4


async def snapshot(rpc):
    """Everything needed to plan, captured once and saved with the run."""
    nodes = await rpc.call("getClusterNodes")
    votes = await rpc.call("getVoteAccounts")
    epoch = await rpc.call("getEpochInfo")
    sched = await rpc.call("getLeaderSchedule")
    version = await rpc.call("getVersion")
    return {"captured_at": time.time(), "epoch": epoch, "nodes": nodes,
            "votes": votes, "leader_schedule": sched, "rpc_version": version}


def validator_table(snap):
    stake = {v["nodePubkey"]: v["activatedStake"] for v in snap["votes"]["current"]}
    total = sum(stake.values()) or 1
    out = {}
    for n in snap["nodes"]:
        s = stake.get(n["pubkey"], 0)
        if not s:
            continue
        tpu = n.get("tpuQuic") or ""
        gossip = n.get("gossip") or ""
        out[n["pubkey"]] = {
            "identity": n["pubkey"],
            "client": n.get("clientId") or "Unknown",
            "version": n.get("version"),
            "stake_share": s / total,
            "tpu_quic": tpu,
            "gossip": gossip,
            # TPU IP different from gossip IP => transactions are received by a
            # separate box (relayer / block-building front-end) before the leader.
            "tpu_is_remote": bool(tpu and gossip and tpu.rsplit(":", 1)[0] != gossip.rsplit(":", 1)[0]),
        }
    return out


def client_summary(table):
    agg = collections.defaultdict(lambda: {"validators": 0, "stake_share": 0.0,
                                           "versions": collections.Counter(),
                                           "remote_tpu": 0})
    for v in table.values():
        a = agg[v["client"]]
        a["validators"] += 1
        a["stake_share"] += v["stake_share"]
        a["versions"][v["version"]] += 1
        a["remote_tpu"] += v["tpu_is_remote"]
    return {k: {**a, "versions": dict(a["versions"].most_common(4))}
            for k, a in sorted(agg.items(), key=lambda x: -x[1]["stake_share"])}


def leader_windows(snap, identity):
    """Absolute start slots of each 4-slot window led by `identity` this epoch."""
    first = snap["epoch"]["absoluteSlot"] - snap["epoch"]["slotIndex"]
    rel = sorted(snap["leader_schedule"].get(identity, []))
    starts, prev = [], None
    for r in rel:
        a = first + r
        if prev is None or a != prev + 1 or (a - first) % SLOTS_PER_WINDOW == 0:
            if (a - first) % SLOTS_PER_WINDOW == 0:
                starts.append(a)
        prev = a
    return starts


def pick_targets(snap, clients=None, per_client=2, windows_per_target=4,
                 horizon_slots=9000, min_gap_slots=50, start_after_slot=None):
    """Pick the highest-stake validators of each client family that lead often
    enough in the next `horizon_slots`, then lay out a non-overlapping schedule."""
    clients = clients or DEFAULT_CLIENTS
    table = validator_table(snap)
    now = start_after_slot or (snap["epoch"]["absoluteSlot"] + 100)  # ~40 s to fund/start
    epoch_end = snap["epoch"]["absoluteSlot"] - snap["epoch"]["slotIndex"] + snap["epoch"]["slotsInEpoch"]
    end = min(now + horizon_slots, epoch_end)  # schedule is only known for this epoch
    chosen = []
    for c in clients:
        cands = sorted((v for v in table.values() if v["client"] == c),
                       key=lambda v: -v["stake_share"])
        got = 0
        for v in cands:
            ws = [w for w in leader_windows(snap, v["identity"]) if now < w < end - SLOTS_PER_WINDOW]
            if len(ws) >= windows_per_target:
                chosen.append((v, ws))
                got += 1
            if got >= per_client:
                break
    # greedy schedule: earliest windows first, keep a gap between our batches
    plan, used = [], []
    want = {v["identity"]: windows_per_target for v, _ in chosen}
    events = sorted((w, v["identity"]) for v, ws in chosen for w in ws)
    for w, ident in events:
        if want[ident] <= 0:
            continue
        if any(abs(w - u) < min_gap_slots for u in used):
            continue
        plan.append({"window_start": w, "leader": ident, **{k: table[ident][k] for k in
                     ("client", "version", "stake_share", "tpu_quic", "gossip", "tpu_is_remote")}})
        used.append(w)
        want[ident] -= 1
    plan.sort(key=lambda p: p["window_start"])
    return plan, [v for v, _ in chosen]


def save(obj, path):
    with open(path, "w") as f:
        json.dump(obj, f, indent=1, default=str)
