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


def write(run_dir, extra_runs=(), out_dir=None):
    """REPORT.md for one run, or for several pooled runs (out_dir given)."""
    runs = [run_dir, *extra_runs]
    adir = os.path.join(out_dir, "analysis") if out_dir else os.path.join(run_dir, "analysis")
    res = json.load(open(os.path.join(adir, "results.json")))
    L = []
    L.append("# Run report — " + ", ".join(os.path.basename(os.path.normpath(r)) for r in runs) + "\n")
    for rd in runs:
        meta = json.load(open(os.path.join(rd, "run_meta.json")))
        batches = read_jsonl(os.path.join(rd, "batches.jsonl"))
        sk = os.path.join(rd, "skipped_slots.json")
        skipped = json.load(open(sk)) if os.path.exists(sk) else []
        sp = os.path.join(rd, "spend_actual.json")
        spend = json.load(open(sp)) if os.path.exists(sp) else None
        sent = [b for b in batches if b.get("status") in ("sent", "dry_run")]
        L.append(f"### {os.path.basename(os.path.normpath(rd))} ({'LIVE mainnet' if meta['live'] else 'DRY-RUN'})")
        L.append(f"- Started {meta['started_utc']} UTC; epoch {meta['epoch']['epoch']}, first planned slot ≈ {meta['epoch']['absoluteSlot']}")
        L.append(f"- RPC `{meta['rpc']}` (node {meta['rpc_version'].get('solana-core')}); send path `{meta['send_rpc']}`; "
                 f"send offset {meta.get('send_offset_slots', 0)} slot(s) from window start")
        L.append(f"- Probe: CU limit {meta['cu_limit']}, priority levels (µlamports/CU) {meta['levels']}, seed {meta['seed']}")
        if sent:
            L.append(f"- Batches fired: {len(sent)}; skipped (late): {sum(b.get('status')=='skipped_late' for b in batches)}; "
                     f"measured slot time {_f(sum(b['slot_time_ms'] for b in sent)/len(sent),0)} ms")
        if spend:
            L.append(f"- Actual spend: {spend['actual_spend_lamports']/1e9:.6f} SOL "
                     f"(worst-case ledger {spend['ledger_worst_case_lamports']/1e9:.6f} SOL, cap {meta['max_spend_sol']} SOL)")
        L.append(f"- Unavailable slots (skipped by leader or not served): {len(skipped)}\n")
    if res.get("slot_in_window_by_run"):
        L.append("Where probes landed relative to the target window (slot 0 = first slot of the window):\n")
        for run, d in res["slot_in_window_by_run"].items():
            L.append(f"- `{run}`: " + ", ".join(f"{k}: {v}" for k, v in d.items()))
        L.append("")

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
        L.append("\n### Across the whole window (probes of one batch ordered by slot, then position)\n")
        L.append("| validator | client | windows | τ fee (p) | τ send (p) |")
        L.append("|---|---|---|---|---|")
        for ld, r in sorted(pv.items(), key=lambda x: x[1]["client"]):
            w = r["across_window"]
            L.append(f"| `{ld[:8]}…` | {r['client']} | {w['n_blocks']} | {_f(w['tau_fee'])} ({_p(w['p_fee'])}) | "
                     f"{_f(w['tau_send'])} ({_p(w['p_send'])}) |")
        L.append("\n## Per client family (independent probes pooled)\n")
        L.append("| client | validators | blocks | τ fee (p) | τ send (p) | verdict (independent) | verdict (conflicting) | across window: τ fee / τ send (p) |")
        L.append("|---|---|---|---|---|---|---|---|")
        for cl, r in res["per_client"].items():
            a = r["independent"]
            w = r.get("across_window") or {}
            L.append(f"| {cl} | {r['validators']} | {a['n_blocks']} | {_f(a['tau_fee'])} ({_p(a['p_fee'])}) | "
                     f"{_f(a['tau_send'])} ({_p(a['p_send'])}) | {r['verdict_independent']} | {r['verdict_conflicting']} | "
                     f"{_f(w.get('tau_fee'))} ({_p(w.get('p_fee'))}) / {_f(w.get('tau_send'))} ({_p(w.get('p_send'))}) |")
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
    with open(os.path.join(out_dir or run_dir, "REPORT.md"), "w") as f:
        f.write("\n".join(L) + "\n")
