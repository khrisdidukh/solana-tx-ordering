"""Render analysis/results.json into REPORT.md inside the run directory."""
import json
import os

from .collect import read_jsonl


def _f(x, nd=2):
    if x is None or (isinstance(x, float) and x != x):
        return "–"
    return f"{x:.{nd}f}" if isinstance(x, float) else str(x)


def _p(x):
    if x is None or x != x:
        return "–"
    return "<0.001" if x < 0.001 else f"{x:.3f}"


def write(run_dir):
    res = json.load(open(os.path.join(run_dir, "analysis", "results.json")))
    meta = json.load(open(os.path.join(run_dir, "run_meta.json")))
    batches = read_jsonl(os.path.join(run_dir, "batches.jsonl"))
    skipped = json.load(open(os.path.join(run_dir, "skipped_slots.json"))) \
        if os.path.exists(os.path.join(run_dir, "skipped_slots.json")) else []
    spend = os.path.join(run_dir, "spend_actual.json")
    spend = json.load(open(spend)) if os.path.exists(spend) else None

    L = []
    L.append(f"# Run report — {meta['started_utc']} ({'LIVE mainnet' if meta['live'] else 'DRY-RUN'})\n")
    L.append(f"- RPC: `{meta['rpc']}` (node {meta['rpc_version'].get('solana-core')}), send path: `{meta['send_rpc']}`")
    L.append(f"- Epoch {meta['epoch']['epoch']}, first planned slot ≈ {meta['epoch']['absoluteSlot']}")
    L.append(f"- Probe: CU limit {meta['cu_limit']}, priority levels (µlamports/CU) {meta['levels']}, seed {meta['seed']}")
    sent = [b for b in batches if b.get("status") in ("sent", "dry_run")]
    if sent:
        L.append(f"- Batches fired: {len(sent)}; skipped (late): {sum(b.get('status')=='skipped_late' for b in batches)}")
        L.append(f"- Measured slot time during run: {_f(sum(b['slot_time_ms'] for b in sent)/len(sent),0)} ms")
    if spend:
        L.append(f"- Actual spend: {spend['actual_spend_lamports']/1e9:.6f} SOL "
                 f"(worst-case ledger {spend['ledger_worst_case_lamports']/1e9:.6f} SOL, cap {meta['max_spend_sol']} SOL)")
    L.append(f"- Unavailable slots (skipped by leader or not served): {len(skipped)}\n")

    pv = res["per_validator"]
    if pv:
        L.append("## Primary evidence: our probes, per validator\n")
        L.append("tau > 0 means: higher priority fee (resp. earlier send) ⇒ earlier in the block. "
                 "p = within-block permutation test (null: random order).\n")
        L.append("| validator | client | landed in window / sent | other leader | lost | blocks w/ 2+ | τ fee (p) | τ send (p) | verdict (independent probes) | verdict (conflicting probes) |")
        L.append("|---|---|---|---|---|---|---|---|---|---|")
        for ld, r in sorted(pv.items(), key=lambda x: x[1]["client"]):
            a = r["independent"]
            L.append(f"| `{ld[:8]}…` | {r['client']} | {r['landed_target_window']}/{r['probes_sent']} | "
                     f"{r['landed_other_leader']} | {r['not_landed']} | {a['n_blocks']} | "
                     f"{_f(a['tau_fee'])} ({_p(a['p_fee'])}) | {_f(a['tau_send'])} ({_p(a['p_send'])}) | "
                     f"{r['verdict_independent']} | {r['verdict_conflicting']} |")
        L.append("\n## Per client family (independent probes pooled)\n")
        L.append("| client | validators | blocks | τ fee (p) | τ send (p) | verdict | conflicting-probe verdict |")
        L.append("|---|---|---|---|---|---|---|")
        for cl, r in res["per_client"].items():
            a = r["independent"]
            L.append(f"| {cl} | {r['validators']} | {a['n_blocks']} | {_f(a['tau_fee'])} ({_p(a['p_fee'])}) | "
                     f"{_f(a['tau_send'])} ({_p(a['p_send'])}) | {r['verdict_independent']} | {r['verdict_conflicting']} |")
        L.append("\n## Landing by priority level\n")
        L.append("| group:µlamports/CU | target window | other leader | not landed | other |")
        L.append("|---|---|---|---|---|")
        for k, c in res["landing_by_fee_level"].items():
            other = sum(v for kk, v in c.items() if kk not in ("target_window", "other_leader", "not_landed"))
            L.append(f"| {k} | {c.get('target_window',0)} | {c.get('other_leader',0)} | {c.get('not_landed',0)} | {other} |")

    L.append("\n## Supplementary evidence: all transactions in the target blocks\n")
    L.append("Spearman ρ between block position and fee per cost unit (negative ⇒ higher-paying "
             "transactions sit earlier). Computed over every non-vote transaction in the 4 slots "
             "of each targeted window, whether or not our probes landed.\n")
    L.append("| client | blocks | median ρ | median ρ (no Jito-tip txs) | median share of adjacent pairs in descending density | median relative position of tip txs |")
    L.append("|---|---|---|---|---|---|")
    for cl, r in res["passive_by_client"].items():
        L.append(f"| {cl} | {r['blocks']} | {_f(r['median_rho'])} | {_f(r['median_rho_no_tip'])} | "
                 f"{_f(r['median_frac_desc_adjacent'])} | {_f(r['median_tip_rel_pos'])} |")
    L.append("\nFiles: `probes.jsonl` (every probe: signature, fee level, send order, send/ack time), "
             "`statuses.json`, `blocks/<slot>.json.gz` (block order of every transaction + full JSON of our probes), "
             "`analysis/probe_landing.csv`, `analysis/passive_blocks.csv`, `analysis/results.json`.")
    with open(os.path.join(run_dir, "REPORT.md"), "w") as f:
        f.write("\n".join(L) + "\n")
