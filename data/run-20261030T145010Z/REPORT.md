# Run report — run-20261030T145010Z

### run-20261030T145010Z (LIVE mainnet)
- Started 20261030T145010Z UTC; epoch 1072, first planned slot ≈ 463325009
- RPC `https://api.mainnet-beta.solana.com` (node 4.3.2); send path `https://api.mainnet-beta.solana.com`; send offset 0.0 slot(s) from window start
- Probe: CU limit 5000, priority levels (µlamports/CU) [0, 1000, 10000, 50000, 200000, 1000000, 4000000, 16000000], seed 20261030
- Batches fired: 56; skipped (late): 0; measured slot time 214 ms
- Actual spend: 0.010659 SOL (worst-case ledger 0.010777 SOL, cap 0.05 SOL)
- Unavailable slots (skipped by leader or not served): 0

Where probes landed relative to the target window (slot 0 = first slot of the window):

- `run-20261030T145010Z`: after_window: 95, 1: 44, 2: 333, 3: 187

## Primary evidence: our probes, per validator

tau > 0 means: higher priority fee (resp. earlier send) ⇒ earlier in the block. p = within-block permutation test (null: random order).

| validator | client | landed in window / sent | other leader | lost | blocks w/ 2+ | τ fee (p) | τ send (p) | verdict (independent probes) | verdict (conflicting probes) |
|---|---|---|---|---|---|---|---|---|---|
| `5Us18hLZ…` | Agave | 44/48 | 4 | 0 | 8 | 0.16 (0.537) | 0.62 (0.005) | arrival order (strong, tau=0.62) | no rule detected - consistent with noise |
| `7QQGNm3p…` | Agave | 25/48 | 23 | 0 | 2 | 0.47 (0.061) | 0.31 (0.209) | inconclusive (only 2 blocks with 2+ probes) | inconclusive (only 2 blocks with 2+ probes) |
| `5Cchr1XG…` | AgaveBam | 46/48 | 0 | 2 | 5 | 0.53 (0.004) | 0.01 (0.971) | priority-fee order (partial, tau=0.53) | inconclusive (only 4 blocks with 2+ probes) |
| `DRpbCBMx…` | AgaveBam | 47/48 | 1 | 0 | 6 | 0.52 (0.034) | 0.22 (0.448) | weak evidence only (fee tau=0.52, p=0.034) | no rule detected - consistent with noise |
| `9jxgosAf…` | FireBAM | 23/48 | 25 | 0 | 4 | 0.27 (0.542) | 0.43 (0.335) | inconclusive (only 4 blocks with 2+ probes) | inconclusive (only 3 blocks with 2+ probes) |
| `9eGrDohd…` | Firedancer | 47/48 | 1 | 0 | 5 | 0.69 (<0.001) | -0.13 (0.462) | priority-fee order (strong, tau=0.69) | inconclusive (only 4 blocks with 2+ probes) |
| `JD549Hsb…` | Firedancer | 48/48 | 0 | 0 | 6 | -0.01 (0.961) | 0.49 (0.009) | arrival order (partial, tau=0.49) | no rule detected - consistent with noise |
| `CAo1dCGY…` | HarmonicAgave | 37/48 | 11 | 0 | 3 | 0.27 (0.115) | 0.14 (0.413) | inconclusive (only 3 blocks with 2+ probes) | weak evidence only (arrival tau=0.67, p=0.047) |
| `Fd7btgyS…` | HarmonicAgave | 45/48 | 0 | 3 | 4 | 0.23 (0.157) | 0.08 (0.617) | inconclusive (only 4 blocks with 2+ probes) | priority-fee order (strong, tau=0.89) |
| `Awes4Tr6…` | HarmonicFiredancer | 33/48 | 11 | 4 | 5 | 0.28 (0.404) | 0.02 (0.949) | no rule detected - consistent with noise | inconclusive (only 3 blocks with 2+ probes) |
| `JUPiTERr…` | HarmonicFiredancer | 48/48 | 0 | 0 | 4 | 0.22 (0.140) | -0.08 (0.606) | inconclusive (only 4 blocks with 2+ probes) | no rule detected - consistent with noise |
| `E1r4Psq8…` | JitoLabs | 39/48 | 6 | 3 | 4 | -0.46 (0.072) | 0.08 (0.888) | inconclusive (only 4 blocks with 2+ probes) | no rule detected - consistent with noise |
| `HEL1USMZ…` | JitoLabs | 38/48 | 9 | 1 | 4 | -0.08 (0.670) | 0.10 (0.580) | inconclusive (only 4 blocks with 2+ probes) | weak evidence only (fee tau=0.89, p=0.021) |
| `ana2y2Yv…` | Rakurai | 44/48 | 4 | 0 | 5 | 0.45 (0.033) | 0.66 (<0.001) | arrival order (strong, tau=0.66) | weak evidence only (arrival tau=0.67, p=0.036) |

### Across the whole window (probes of one batch ordered by slot, then position)

| validator | client | windows | τ fee (p) | τ send (p) |
|---|---|---|---|---|
| `5Us18hLZ…` | Agave | 4 | 0.19 (0.120) | 0.26 (0.031) |
| `7QQGNm3p…` | Agave | 3 | 0.22 (0.393) | 0.65 (0.001) |
| `5Cchr1XG…` | AgaveBam | 4 | 0.38 (<0.001) | 0.39 (<0.001) |
| `DRpbCBMx…` | AgaveBam | 4 | 0.35 (0.002) | 0.41 (<0.001) |
| `9jxgosAf…` | FireBAM | 3 | 0.41 (0.040) | 0.63 (<0.001) |
| `9eGrDohd…` | Firedancer | 4 | 0.33 (0.003) | 0.00 (0.984) |
| `JD549Hsb…` | Firedancer | 4 | -0.09 (0.441) | 0.41 (<0.001) |
| `CAo1dCGY…` | HarmonicAgave | 3 | 0.25 (0.063) | 0.43 (<0.001) |
| `Fd7btgyS…` | HarmonicAgave | 4 | 0.24 (0.050) | 0.25 (0.033) |
| `Awes4Tr6…` | HarmonicFiredancer | 4 | 0.16 (0.487) | 0.12 (0.574) |
| `JUPiTERr…` | HarmonicFiredancer | 4 | 0.13 (0.291) | 0.23 (0.040) |
| `E1r4Psq8…` | JitoLabs | 4 | -0.34 (0.015) | 0.30 (0.035) |
| `HEL1USMZ…` | JitoLabs | 4 | -0.08 (0.577) | 0.29 (0.035) |
| `ana2y2Yv…` | Rakurai | 4 | 0.11 (0.361) | 0.50 (<0.001) |

## Per client family (independent probes pooled)

| client | validators | blocks | τ fee (p) | τ send (p) | verdict (independent) | verdict (conflicting) | across window: τ fee / τ send (p) |
|---|---|---|---|---|---|---|---|
| Agave | 2 | 10 | 0.22 (0.272) | 0.56 (0.001) | arrival order (partial, tau=0.56) | no rule detected - consistent with noise | 0.20 (0.108) / 0.42 (<0.001) |
| AgaveBam | 2 | 11 | 0.53 (<0.001) | 0.13 (0.511) | priority-fee order (partial, tau=0.53) | weak evidence only (fee tau=0.52, p=0.038) | 0.37 (<0.001) / 0.40 (<0.001) |
| FireBAM | 1 | 4 | 0.27 (0.542) | 0.43 (0.335) | inconclusive (only 4 blocks with 2+ probes) | inconclusive (only 3 blocks with 2+ probes) | 0.41 (0.040) / 0.63 (<0.001) |
| Firedancer | 2 | 11 | 0.31 (0.019) | 0.21 (0.110) | weak evidence only (fee tau=0.31, p=0.019) | no rule detected - consistent with noise | 0.12 (0.136) / 0.21 (0.009) |
| HarmonicAgave | 2 | 7 | 0.25 (0.034) | 0.11 (0.357) | weak evidence only (fee tau=0.25, p=0.034) | priority-fee order (strong, tau=0.78) | 0.24 (0.005) / 0.33 (<0.001) |
| HarmonicFiredancer | 2 | 9 | 0.26 (0.185) | -0.02 (0.893) | no rule detected - consistent with noise | no rule detected - consistent with noise | 0.14 (0.234) / 0.17 (0.130) |
| JitoLabs | 2 | 8 | -0.27 (0.108) | 0.09 (0.650) | no rule detected - consistent with noise | weak evidence only (arrival tau=0.58, p=0.042) | -0.21 (0.037) / 0.29 (0.004) |
| Rakurai | 1 | 5 | 0.45 (0.033) | 0.66 (<0.001) | arrival order (strong, tau=0.66) | weak evidence only (arrival tau=0.67, p=0.036) | 0.11 (0.361) / 0.50 (<0.001) |

## Landing by priority level

| group:µlamports/CU | target window | other leader | not landed | other |
|---|---|---|---|---|
| CONF:10000 | 44 | 10 | 2 | 0 |
| CONF:200000 | 47 | 8 | 1 | 0 |
| CONF:1000000 | 48 | 7 | 1 | 0 |
| CONF:4000000 | 48 | 8 | 0 | 0 |
| IND:0 | 46 | 8 | 2 | 0 |
| IND:1000 | 48 | 7 | 1 | 0 |
| IND:10000 | 47 | 8 | 1 | 0 |
| IND:50000 | 50 | 6 | 0 | 0 |
| IND:200000 | 47 | 7 | 2 | 0 |
| IND:1000000 | 45 | 9 | 2 | 0 |
| IND:4000000 | 46 | 10 | 0 | 0 |
| IND:16000000 | 48 | 7 | 1 | 0 |

## Supplementary evidence: all transactions in the target blocks

Spearman ρ between block position and fee per cost unit (negative ⇒ higher-paying transactions sit earlier). Computed over every non-vote transaction in the 4 slots of each targeted window, whether or not our probes landed.

| client | blocks | median ρ | median ρ (no Jito-tip txs) | median share of adjacent pairs in descending density | median relative position of tip txs |
|---|---|---|---|---|---|
| Agave | 32 | -0.02 | -0.02 | 0.53 | 0.55 |
| AgaveBam | 32 | -0.08 | -0.08 | 0.57 | 0.54 |
| FireBAM | 16 | -0.06 | -0.09 | 0.58 | 0.56 |
| Firedancer | 32 | -0.24 | -0.28 | 0.59 | 0.50 |
| HarmonicAgave | 32 | -0.09 | -0.09 | 0.56 | 0.51 |
| HarmonicFiredancer | 32 | -0.10 | -0.11 | 0.57 | 0.59 |
| JitoLabs | 32 | -0.01 | -0.02 | 0.54 | 0.63 |
| Rakurai | 16 | -0.02 | -0.04 | 0.55 | 0.65 |

Files: `probes.jsonl` (every probe: signature, fee level, send order, send/ack time), `statuses.json`, `blocks/<slot>.json.gz` (block order of every transaction + full JSON of our probes), `analysis/probe_landing.csv`, `analysis/passive_blocks.csv`, `analysis/results.json`.
