# Inside the Block — how Solana leaders order transactions

A measurement tool and dataset for the Superteam Ukraine bounty *"Inside the Block: How Solana
Validators Order Transactions"*.  We send our own small transactions into the leader windows of
chosen mainnet validators that run different clients / forks, fetch the resulting blocks, and test
from the block positions which rule decided the order: **priority fee**, **arrival (send) order**,
or **no detectable rule**.

```
docker compose up                         # mainnet DRY-RUN: plans, builds & signs probes, fetches blocks, analyses — sends nothing
LIVE=1 docker compose up                  # live: same, but probes are sent (asks you to type YES)
LIVE=1 YES=1 MAX_SPEND_SOL=0.05 docker compose up   # live, unattended, hard spend cap
```

**Written analysis, measurement dates and "what went wrong": [`REPORT.md`](REPORT.md).**
Generated tables for both live runs pooled: [`data/combined/REPORT.md`](data/combined/REPORT.md);
per run: [`data/run-20261030T145010Z/`](data/run-20261030T145010Z/),
[`data/run-20261030T152829Z/`](data/run-20261030T152829Z/).

### Results at a glance
Two live mainnet runs on 2026-10-30 (after Alpenglow), 184 leader windows of 17 validators across
8 client families, 2 208 probes, 2 188 landed, total spend 0.0352 SOL.  Pooled per family
(independent probes, within-block permutation test):

| client family (gossip `clientId`) | ordering inside a block | τ fee (p) | τ send (p) |
|---|---|---|---|
| Agave (vanilla) | arrival order, partial | −0.04 (0.69) | **0.32 (0.002)** |
| JitoLabs (Jito-Solana) | arrival order, partial | −0.07 (0.51) | **0.26 (0.007)** |
| Rakurai | arrival order, partial | 0.13 (0.24) | **0.33 (0.002)** |
| AgaveBam | priority fee, partial | **0.37 (<0.001)** | 0.16 (0.13) |
| FireBAM | priority fee, partial | **0.34 (0.009)** | 0.16 (0.23) |
| Firedancer | priority fee, partial | **0.27 (<0.001)** | 0.11 (0.23) |
| HarmonicAgave | priority fee, partial | **0.31 (<0.001)** | 0.23 (0.015) |
| HarmonicFiredancer | no rule detected | 0.18 (0.054) | 0.12 (0.22) |

No family sorts a block strictly (τ = 1); the rules hold *partially* and vary between validators of
the same family.  Priority fee did not change whether or how fast a probe landed.  Details,
per-validator results and caveats: [`REPORT.md`](REPORT.md).

---

## 1. The question, made testable

For a validator *V* we want to know: when *V* is leader, what decides that transaction A sits
before transaction B in *V*'s block?

Every block is a sequence; `getBlock` returns transactions in that sequence (entry order, which is
also execution order).  Our own transactions ("probes") are identical except for two things we
control, so any systematic difference in their positions can only come from those two things:

| variable | how it is set | what it would mean if it predicts position |
|---|---|---|
| **priority fee** (µlamports per CU) | 8 log-spaced levels `0 … 16 000 000`, randomly permuted per batch | the scheduler sorts by fee / reward-per-cost |
| **send order** | an independent random permutation per batch; probes leave 3 ms apart | the scheduler is FIFO / arrival-ordered |

Because the two permutations are independent, "ordered by fee" and "ordered by arrival" make
different predictions in every batch.  If neither explains the positions, the honest answer is
*no rule / noise* — the analysis reports that explicitly.

## 2. Experiment design

### Probes
Each probe is `[SetComputeUnitLimit(5000), SetComputeUnitPrice(p), Memo("o<batch>.<i>")]`.
Same instructions, same requested CU limit ⇒ the same cost-model units for every probe, so ordering
by *fee*, by *fee per CU* and by *reward per cost unit* are all the same ranking for our probes.
The memo only makes transactions unique and lets anyone find them in the block.

### Two groups per batch (interaction of our own transactions)
* **IND — 8 independent probes**, each paid by its own fee payer.  The fee payer is the only
  writable account, so these probes share **no write locks** with each other (or with anyone else).
  A scheduler is free to put them anywhere and to run them on different threads in parallel.
* **CONF — 4 conflicting probes** paid by **one shared payer**, so every pair conflicts on a write
  lock.  A scheduler must serialize them; this shows how a client orders *conflicting* work, which
  can differ from how it orders independent work.

### Leader schedule, leader windows and leader types
* `getLeaderSchedule` gives each validator's slots for the epoch; leaders own **4-slot windows**
  (verified on the live schedule: 105 669 runs of exactly 4 slots, the rest are 8/12 = same leader
  twice in a row).  We fire one batch per window: at the window's first slot in run 1, one slot
  before it in run 2 (`SEND_OFFSET_SLOTS=-1`, chosen after run 1 showed the send→inclusion latency).
* The *client / fork* of each validator comes from gossip (`getClusterNodes` → `clientId`,
  `version`), joined with stake from `getVoteAccounts`.  Snapshot at the time of our run (staked
  validators only):

  | clientId (gossip) | share of stake | version strings seen | TPU address ≠ gossip IP |
  |---|---|---|---|
  | AgaveBam | 35.4 % | 4.3.2, 4.4.0(-rc.1) | yes (BAM node, port 5010) |
  | JitoLabs (Jito-Solana) | 24.5 % | 4.3.2, 4.4.0(-rc.1) | no |
  | HarmonicAgave | 21.7 % | 4.3.2, 4.4.0-rc.1 | yes (Harmonic relayer) |
  | HarmonicFiredancer | 8.7 % | 26.10.4/5 | yes (Harmonic relayer) |
  | Firedancer | 5.6 % | 26.10.4/5, 0.1.1 | no |
  | FireBAM | 1.9 % | 26.10.5 | yes (BAM node) |
  | Rakurai | 1.1 % | 4.3.2 | no |
  | Agave (vanilla) | 1.0 % | 4.3.2, 4.5.0-alpha | no |

  The full snapshot of every run is saved (`cluster_snapshot.json`, `validators.json`).
* **Target selection** (`ordering/cluster.py`): for each client family, the highest-stake
  validators that lead at least *W* times within the planning horizon (default 2 validators ×
  4 windows × 8 families = up to 64 windows, ≥ 6 validators / ≥ 3 clients guaranteed by the
  defaults).  Windows are laid out so our batches are ≥ 50 slots (≈ 11 s) apart: they never overlap, and the 12 sends of a batch never meet the public RPC's per-method rate limit (40 / 10 s) together with another batch.
* "Leader type" matters for interpretation: for **BAM** and **Harmonic** validators the TPU address
  advertised in gossip belongs to a different machine (we record `tpu_is_remote`), i.e. our
  transactions are received and possibly ordered *before* they reach the validator.  For those
  families the measured rule is the rule of the whole block-assembly pipeline, not of the
  validator's own banking stage — we cannot separate the two from the outside (see §6).

### Timing
`SlotClock` polls `getSlot(processed)` every 400 ms (public-RPC rate limits: ≤ 40 calls per method per 10 s) and extrapolates with the measured slot time
(≈ 215 ms on mainnet during our measurements, post-Alpenglow).  Probes are built and signed 3 slots
before the window and fired when the estimated slot reaches the window start.  Right after firing
we read the RPC's slot again (`rpc_slot_after_fire` in `batches.jsonl`) so the timing error is
measured, not assumed.  Measured result: firing at the window's first slot, **no** probe landed in
slot 0 of the window (run 1: slot 1: 44, slot 2: 333, slot 3: 187, after the window: 95); firing one
slot early (run 2): slot 0: 95, slot 1: 720, slot 2: 426, slot 3: 132, after: 156.  The public-RPC path
therefore takes roughly 1.5–2 slots (≈ 300–450 ms) from send to inclusion.

### The path of a transaction, and what that means for the data
```
this tool ──HTTPS sendTransaction──▶ RPC node ──QUIC──▶ TPU address in gossip ──▶ scheduler ──▶ block
           (skipPreflight, maxRetries=0)           (validator itself, or a BAM node /
                                                    Harmonic relayer for those families)
```
* `maxRetries: 0` makes the RPC forward each probe **once** — no RPC-side rebroadcast that would
  re-inject a probe later and scramble arrival order.  `skipPreflight` removes simulation latency.
* The RPC forwards to the leader *current at receipt* and the next one(s).  That is why we fire at
  the first slot of the target window, and why every probe's landing is classified:
  `target_window` (in one of the target's 4 slots, verified by slot leader), `other_leader`, or
  `not_landed`.  Only `target_window` probes are used to infer the target's rule.
* The RPC → leader hop is QUIC with stake-weighted QoS; our probes travel with whatever stake the
  RPC node has.  Probes may be dropped before the scheduler ever sees them.  Landing rate per fee
  level is reported separately so QoS/competition effects are visible and are not mistaken for
  ordering.
* We send through a public RPC deliberately: it is what ordinary users do, it needs no API keys, and
  it makes the experiment reproducible by anyone.  `SEND_RPC_URL` lets you route probes through
  any other RPC (e.g. a staked one) to test whether the path changes the result.
* Probes leave 3 ms apart in the intended send order (`send_rank`); the request and acknowledgement
  timestamps are logged (`t_send`, `t_ack`).  Arrival order at the leader is **not observable**; we
  can only control send order.  Network reordering therefore weakens an arrival-order signal (biases
  `τ_send` towards 0); it cannot create a fake fee-order signal, because fee level is independent of
  send order by construction.

### Competition inside the block
Our probes share each block with hundreds of other transactions.  We never claim anything from the
absolute position of a probe; the tests use only the *relative* order of our own probes in the same
block.  The fee levels deliberately span the market: from 0 (24 % of non-vote mainnet
transactions in the fetched blocks pay no priority fee) through the median (~17 000 µlamports per
cost unit) to the 99th percentile (~16.5 M), measured over 424 979 transactions in the blocks we
fetched.
As supplementary evidence, for every block in every targeted window we also compute the Spearman
correlation between position and fee-per-cost-unit over **all** transactions (Jito-tip transactions
flagged), which shows whether a block as a whole looks fee-sorted.

### Noise vs. rule
* For each block containing ≥ 2 of our probes from one batch we compute Kendall's τ between position
  and fee level, and between position and send order (τ > 0 ⇒ "higher fee / earlier sent is
  earlier").
* Significance: a **within-block permutation test** (positions shuffled within each block, 4 000
  iterations, two-sided on the mean τ).  This is exact for tiny blocks of probes and does not
  pretend that pairs from one block are independent.
* Verdicts per validator and per client family: *priority-fee order (strict/strong/partial)*,
  *arrival order*, *mixed*, *inconclusive* (too few blocks) or *no rule detected — consistent with
  noise*.  A null result is reported as a result.
* Replication: several windows per validator and two validators per family; per-validator and
  pooled-family results are both shown, so a family-level claim is visible only if individual
  validators agree.
* Probes from one batch that land in *different* slots of the same window are also compared
  (`across_window`: earlier slot ⇒ earlier).

### Alpenglow (October 21)
All measurements are **after** the Alpenglow upgrade (epoch 1072 onwards, the run timestamps are in
every file).  Consistent with that, the fetched blocks contain no vote transactions.

## 3. Safety: dry-run, spend cap, keys
* **Dry-run is the default.**  Without `LIVE=1`/`--live` the tool plans, builds and signs probes with
  throw-away keys, fires nothing, and still fetches and analyses the target blocks.
* **Spend cap** (`MAX_SPEND_SOL`, default 0.05 SOL): `ordering/spend.py` books the *worst-case* fee
  (5 000 lamports + CU limit × price) of every transaction before it is sent, persists the ledger
  after every entry (so a restart continues from what was already spent) and refuses anything that
  would cross the cap.  The plan is trimmed up front if it could exceed the cap.  Worst case for the
  default plan: 0.000192 SOL per batch, ≈ 0.012 SOL for 64 batches.
* Sub-payers are funded from the wallet with exactly the fees they can need plus rent-exemption
  (refundable) and are **swept back** to the wallet at the end (`sweep` can be re-run any time).
  Lamports parked on sub-payers are not counted as spend; the actual spend (wallet balance before vs
  after) is written to `spend_actual.json`.
* **Keys only via volume / env**: the wallet is `keys/wallet.json` (mounted volume, path overridable
  with `KEYPAIR`), sub-payer keys are `keys/subpayers.json`; `keys/` is git-ignored and
  docker-ignored.  A live run asks you to type `YES` unless `YES=1`.

## 4. Running it

Docker (one command):
```
docker compose up                                   # dry-run against mainnet
docker compose run --rm ordering keygen             # create keys/wallet.json, prints the address
docker compose run --rm ordering wallet             # balance
LIVE=1 docker compose up                            # live run (send ~0.1 SOL to the wallet first)
docker compose run --rm ordering sweep              # return sub-payer lamports (also done automatically)
docker compose run --rm ordering analyze data/<run> # recompute analysis from raw data
```
Without Docker: `./scripts/run_native.sh <same commands>` (uses `uv` to provision Python 3.12) —
this is how the two submitted live runs were executed (macOS, arm64).
Pool several runs: `python -m ordering combine data/run-A data/run-B --out data/combined`.

Useful knobs (env or flags): `PER_CLIENT`, `WINDOWS_PER_VALIDATOR`, `CLIENTS`, `SEND_RPC_URL`,
`SEND_OFFSET_SLOTS`, `CU_LIMIT`, `SEED`.  `python -m ordering plan` prints the plan without running.

### Development path we used
* **mainnet dry-run** – real leader schedule and windows, probes built and signed but not sent; this
  is where we checked that we hit the windows (timing error recorded per batch).
* **mainnet simulation** – `simulateTransaction` (sigVerify off, nothing sent) to confirm the probe
  executes and to size the CU limit (memo cost grows ~400 CU per byte, so the memo is kept short).
* **mainnet live** – with the spend cap: run 1 (56 windows, 0.0107 SOL) and run 2 (128 windows,
  0.0245 SOL), together 0.0352 SOL.
* devnet/testnet end-to-end runs were not possible: both clusters' RPC faucets are closed
  (`requestAirdrop` → *"The RPC faucet is closed"*); see "what went wrong" in the report.

## 5. Raw data and how to verify any claim
Each run directory `data/run-<UTC timestamp>/` contains:

| file | content |
|---|---|
| `run_meta.json` | start time, RPC, node version, epoch, all parameters, seed |
| `cluster_snapshot.json`, `validators.json` | gossip + stake snapshot used for planning |
| `plan.json`, `batches.jsonl` | target windows; per batch the estimated and the RPC's real slot at firing |
| `probes.jsonl` | every probe: **signature**, batch, group, fee level, send rank, payer, send/ack time, send error |
| `statuses.json` | `getSignatureStatuses` for every probe (**slot**, error) |
| `blocks/<slot>.json.gz` | every fetched block in block order: position, signature, fee, cost units, CU consumed, flags, plus the full RPC JSON of our probes |
| `analysis/probe_landing.csv` | per probe: landed where, slot, position, block size |
| `analysis/passive_blocks.csv` | per block: fee-density/position correlations |
| `analysis/results.json`, `REPORT.md` | all statistics and verdicts |
| `spend.json`, `spend_actual.json` | worst-case ledger and actual wallet delta |

To check a probe: take its `signature` and `slot` from `probe_landing.csv`, call
`getBlock <slot>` (`maxSupportedTransactionVersion: 1`), and find the signature's index in
`transactions` — it must equal `pos`.

## 6. What this design does NOT separate
* **Relayer / BAM / Harmonic vs. validator.**  For families whose TPU is remote we measure the
  ordering of the whole pipeline; we cannot tell whether the relayer, the builder or the validator's
  scheduler made the decision.
* **Arrival order at the leader.**  We control send order, not arrival order; the RPC hop and QUIC
  can reorder.  A weak or zero `τ_send` does not prove that arrival order is irrelevant.
* **QoS drop vs. scheduler drop.**  A probe that does not land may have been dropped by the RPC,
  by stake-weighted QoS, by a relayer, or by the scheduler.
* **Parallel execution.**  Independent probes may be executed on different banking threads at
  nearly the same time; their relative position then reflects thread interleaving rather than an
  explicit decision.  This is exactly why the IND and CONF groups are reported separately.
* **Bundles and tips** (Jito, BAM) are out of scope by the bounty's definition; our probes are
  plain transactions.  Tip-paying transactions are only *flagged* in the supplementary analysis.
* **One path.**  All live probes in the submitted run use one public RPC; results for a staked or a
  direct-QUIC path may differ (`SEND_RPC_URL` exists to test that).

## 7. Code map
```
ordering/
  cluster.py   gossip/stake/leader-schedule snapshot, client families, target & window planning
  txs.py       probe / transfer construction, fee bounds
  run.py       SlotClock, batch construction (randomised fee & send order), sending, funding, sweep
  spend.py     persistent worst-case spend ledger with hard cap
  collect.py   signature statuses, slot leaders, block fetch → compact per-block tables
  analyze.py   Kendall τ, within-block permutation tests, verdicts, supplementary block analysis
  report.py    REPORT.md renderer (single run or pooled runs)
  __main__.py  CLI (keygen, wallet, plan, run, collect, analyze, combine, sweep)
tests/         unit tests for the statistics and the spend cap (python -m unittest)
```
