# Report — how Solana mainnet leaders ordered our transactions (October 2026)

Raw data and generated tables: [`data/combined/REPORT.md`](data/combined/REPORT.md) (both runs
pooled), `data/run-*/` (per run).  Method: [`README.md`](README.md).

## 1. Measurements and dates

All measurements were taken on Solana mainnet-beta **after** the Alpenglow upgrade of October 21
(epoch 1072; no vote transactions appear in any fetched block).  Times are UTC.

| run | first probe sent | last probe sent | slots | windows | validators / families | probes sent / landed | send offset | actual spend |
|---|---|---|---|---|---|---|---|---|
| [`run-20261030T145010Z`](data/run-20261030T145010Z/) | 2026-10-30 14:50:34 | 2026-10-30 15:09:53 | 463 325 116 – 463 330 543 | 56 | 14 / 8 | 672 / 659 | 0 slots | 0.010 659 SOL |
| [`run-20261030T152829Z`](data/run-20261030T152829Z/) | 2026-10-30 15:28:51 | 2026-10-30 16:57:54 | 463 335 863 – 463 360 839 | 128 | 16 / 8 | 1 536 / 1 529 | −1 slot | 0.024 536 SOL |
| **total** | | | | **184** | **17 / 8** | **2 208 / 2 188** | | **0.035 195 SOL** |

Every probe the RPC accepted landed on chain.  The 20 probes that did not land are exactly the 20
whose `sendTransaction` call was rejected by the public RPC with HTTP 429 (13 in run 1, 7 in run 2),
so they never left our machine.  Spend is the wallet balance before minus after each run, including
funding and sweep fees; sub-payer lamports were swept back.

Client families come from gossip `clientId` at the time of each run (`validators.json` in each run
directory).  Per validator, the number of windows measured: 12 for most, 8 for `A4hyMd3F…`
(FireBAM), `E3mDbFMr…` (Rakurai) and `EvnRmnMr…` (Firedancer), which entered the target set in run 2,
and 4 for `JD549Hsb…` (Firedancer), measured only in run 1.

Spot check: three probes chosen at random from `probe_landing.csv` were looked up with a fresh
`getBlock`; their index in the block's signature list matched `pos` in all three cases
(slots 463 340 205, 463 329 114, 463 342 041).

## 2. What we found

### 2.1 The ordering rule inside a block, per client family

Independent probes (no shared write lock), pooled per family.  τ is Kendall's τ between block
position and the variable (τ > 0: higher fee / earlier send ⇒ earlier in the block); p is the
within-block permutation test.  "Blocks" = blocks containing ≥ 2 of our probes from one batch.

| family | validators | blocks | τ fee (p) | τ send (p) | rule |
|---|---|---|---|---|---|
| Agave (vanilla) | 2 | 33 | −0.04 (0.69) | **0.32 (0.002)** | arrival order |
| JitoLabs | 2 | 27 | −0.07 (0.51) | **0.26 (0.007)** | arrival order |
| Rakurai | 2 | 25 | 0.13 (0.24) | **0.33 (0.002)** | arrival order |
| AgaveBam | 2 | 31 | **0.37 (<0.001)** | 0.16 (0.13) | priority fee |
| FireBAM | 2 | 20 | **0.34 (0.009)** | 0.16 (0.23) | priority fee |
| Firedancer | 3 | 31 | **0.27 (<0.001)** | 0.11 (0.23) | priority fee |
| HarmonicAgave | 2 | 28 | **0.31 (<0.001)** | 0.23 (0.015) | priority fee (arrival: weak) |
| HarmonicFiredancer | 2 | 32 | 0.18 (0.054) | 0.12 (0.22) | no rule detected |

What this means, stated as narrowly as the data allows:

* **Two groups of families behave differently.**  In blocks produced by vanilla Agave, Jito-Solana
  and Rakurai, the order of our probes follows the order in which we sent them, and the priority fee
  has no measurable effect.  In blocks produced by the BAM families (AgaveBam, FireBAM), Firedancer
  and HarmonicAgave, higher-fee probes sit earlier, and send order has no significant effect (except
  a weak one for HarmonicAgave).
* **No family sorts strictly.**  The largest pooled τ is 0.37; individual blocks frequently violate the
  rule.  These are *tendencies*, not strict sorts — consistent with schedulers that order work in
  small batches as it streams in, rather than sorting the whole block.
* **Validators of one family do not always agree.**  For Firedancer, `9eGrDohd…` is fee-ordered
  (τ 0.52, p < 0.001), `JD549Hsb…` looks arrival-ordered (τ_send 0.49, p 0.009, only 4 windows) and
  `EvnRmnMr…` shows no rule.  `9eGrDohd…` and `JD549Hsb…` both reported version 26.10.5;
  `EvnRmnMr…` reported 26.10.4 in run 2 — and in the run 1 snapshot, one hour earlier, the same
  identity was advertising `clientId` JitoLabs 4.3.2 (it was only targeted in run 2, as Firedancer).
  For HarmonicFiredancer, `Awes4Tr6…` is fee-ordered (τ 0.33, p 0.009) while `JUPiTERr…` shows
  nothing, with identical version strings (26.10.5) and both behind a remote TPU.  Where versions
  match, the difference is likely configuration (scheduler settings, block-engine / relayer setup)
  that gossip does not expose.  Family-level statements above are only as strong as this
  heterogeneity allows, and a gossip `clientId` is a snapshot, not a guarantee.
* **HarmonicFiredancer**: the pooled result is a null result.  With 32 blocks it is not a lack of
  data; it is a mix of one fee-ordering and one apparently unordered validator.

### 2.2 Conflicting transactions (shared write lock)

The four probes that share a fee payer must be serialized.  Their order followed the same split:
priority fee for AgaveBam (τ 0.42), FireBAM (0.76), Firedancer (0.49) and HarmonicAgave (0.49);
arrival for JitoLabs (τ_send 0.42) and Rakurai (0.43); weak arrival evidence for Agave (0.35,
p 0.025); nothing for HarmonicFiredancer.  For several validators the fee ordering of conflicting
probes is stronger than that of independent ones (e.g. FireBAM `A4hyMd3F…` τ 0.94), which is what
one expects if non-conflicting transactions are spread over parallel execution threads while
conflicting ones are forced into a single, priority-ordered queue.

### 2.3 Which slot of the window a probe lands in

Across the whole window (ordering probes of a batch by slot, then position), **send order predicts
the slot for every family** (τ_send 0.19–0.34, all p ≤ 0.001 pooled): a probe that arrives later is
more likely to miss the current block and land in the next one.  For the fee-ordering families the
fee also predicts the slot (τ 0.19–0.38, p < 0.001; HarmonicFiredancer τ 0.15, p 0.008), i.e. low-fee probes are more often pushed into
the next block.  JitoLabs shows the opposite sign (τ_fee −0.12, p 0.019) — higher-fee probes landing
*later* in the window.  We have no explanation for this and report it as observed.

### 2.4 Priority fee and landing

Priority fee did **not** affect whether a probe landed, nor whether it landed with the target or the
next leader: across all levels from 0 to 16 000 000 µlamports/CU, 85–90 % landed in the target window
and the rest with the following leader (`Landing by priority level` in the combined report).  At
the time of measurement the network was not congested enough for our probes to be crowded out.

### 2.5 Whole blocks are not fee-sorted

Over all non-vote transactions in the targeted blocks, the Spearman correlation between position and
fee per cost unit is weak for every family (median ρ between −0.02 for JitoLabs and −0.18 for
Firedancer).  Even fee-ordering families produce blocks that, as a whole, are far from sorted by fee.
This matches §2.1: ordering is local (within what the scheduler sees at a time), not global.

### 2.6 Path latency

Firing at the first slot of the window (run 1), not one probe landed in slot 0; most landed in slots
2–3 and 14 % after the window.  Firing one slot early (run 2) moved the distribution to slots 0–2 and
reduced "after the window" to 10 %.  The public-RPC path therefore adds roughly 1.5–2 slots
(≈ 300–450 ms at the measured 214 ms slot time) between our `sendTransaction` and inclusion.

## 3. What went wrong

* **No free end-to-end test network.**  The devnet and testnet RPC faucets are closed
  (`requestAirdrop` → *"The RPC faucet is closed on this cluster"*), and the web faucet requires a
  captcha.  The transaction format was therefore validated with `simulateTransaction` on mainnet
  (signature verification off, nothing sent), the live code path with unit tests against a fake RPC,
  and the timing with a mainnet dry-run.  Run 1 was the first real send.
* **Direct-to-TPU sending was dropped.**  We wrote a QUIC TPU sender, but the development
  environment allows only HTTPS egress, so it could not be tested; we removed it rather than ship
  untested code.  All probes went through the public RPC, which adds a hop we do not control (§6 of
  the README).
* **Run 1 fired too late in the window.**  With the send at slot 0 of the window, no probe landed in
  slot 0 and 14 % landed with the next leader.  Run 2 fired one slot early.
* **The public RPC rate-limited us.**  20 `sendTransaction` calls got HTTP 429 (those probes never
  left our machine), and in run 1 block collection crashed on repeated 429 responses to `getBlock`.
  The raw data (signatures, send order, fees) was already on disk; the collector was fixed
  (honours `Retry-After`, longer back-off, one request at a time, never aborts) and the blocks for
  run 1 were fetched afterwards with the same code (`python -m ordering collect <run>`).  Because the
  crash happened before the automatic sweep, run 1's sub-payers were swept with the separate
  `sweep` command.
* **The sweep failed on one sub-payer in run 2.**  The conflicting-group payer was left holding
  exactly the rent-exempt minimum (650 240 lamports); a fee payer must remain rent-exempt after the
  fee is charged, so it could not pay for its own sweep (`InsufficientFundsForRent`).  The sweep now
  lets the main wallet pay the fees; the remaining 0.00065 SOL was recovered with it.
* **The slot clock sometimes fired late.**  In 8 of 56 batches (run 1) and 14 of 128 (run 2) the RPC's
  own slot, read right after firing, was ≥ 5 slots past the window start, and most of those probes
  landed with a later leader.  The likely cause is the public RPC reporting a lagging slot to our
  clock (it is load-balanced across nodes); our clock only extrapolates from what the RPC reports.
  These probes are classified `other_leader` and excluded from every ordering test; the batches are
  identifiable in `batches.jsonl` (`rpc_slot_after_fire`).
* **Both runs used the same random seed** (20261030), so batch *k* in run 2 used the same fee and
  send-order permutations as batch *k* in run 1.  The batches went to different validators and the
  permutation test is computed within each block, so the tests stay valid, but the two runs are not
  independent randomisations of the same design.  Future runs should vary `SEED`.
* **Statistical power per validator is modest.**  A batch spreads over 2–3 slots, so each block holds
  only 2–6 of our probes; with 8–12 windows per validator that gives 6–20 usable blocks.
  Per-validator verdicts with p between 0.01 and 0.05 are reported as "weak evidence" and are not
  claimed.
* **Cosmetic:** the first log line prints the clock's initial slot-time guess (400 ms) before it has
  measured the real value (214 ms).

## 4. Limits of interpretation

The full list is in README §6.  The most important for reading §2: for BAM and Harmonic validators
the TPU address in gossip belongs to another machine (a BAM node or Harmonic relayer), so the order we
measure is that of the whole block-assembly pipeline, not necessarily of the validator's own
scheduler; we control send order, not arrival order; and a single public RPC path was used for all
probes.
