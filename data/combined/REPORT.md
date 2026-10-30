# Run report — run-20261030T145010Z, run-20261030T152829Z

### run-20261030T145010Z (LIVE mainnet)
- Started 20261030T145010Z UTC; epoch 1072, first planned slot ≈ 463325009
- RPC `https://api.mainnet-beta.solana.com` (node 4.3.2); send path `https://api.mainnet-beta.solana.com`; send offset 0.0 slot(s) from window start
- Probe: CU limit 5000, priority levels (µlamports/CU) [0, 1000, 10000, 50000, 200000, 1000000, 4000000, 16000000], seed 20261030
- Batches fired: 56; skipped (late): 0; measured slot time 214 ms
- Actual spend: 0.010659 SOL (worst-case ledger 0.010777 SOL, cap 0.05 SOL)
- Unavailable slots (skipped by leader or not served): 0

### run-20261030T152829Z (LIVE mainnet)
- Started 20261030T152829Z UTC; epoch 1072, first planned slot ≈ 463335759
- RPC `https://api.mainnet-beta.solana.com` (node 4.3.2); send path `https://api.mainnet-beta.solana.com`; send offset -1.0 slot(s) from window start
- Probe: CU limit 5000, priority levels (µlamports/CU) [0, 1000, 10000, 50000, 200000, 1000000, 4000000, 16000000], seed 20261030
- Batches fired: 128; skipped (late): 0; measured slot time 214 ms
- Actual spend: 0.024536 SOL (worst-case ledger 0.024671 SOL, cap 0.035 SOL)
- Unavailable slots (skipped by leader or not served): 0

Where probes landed relative to the target window (slot 0 = first slot of the window):

- `run-20261030T145010Z`: after_window: 95, 1: 44, 2: 333, 3: 187
- `run-20261030T152829Z`: after_window: 156, 0: 95, 1: 720, 2: 426, 3: 132

## Primary evidence: our probes, per validator

tau > 0 means: higher priority fee (resp. earlier send) ⇒ earlier in the block. p = within-block permutation test (null: random order).

| validator | client | landed in window / sent | other leader | lost | blocks w/ 2+ | τ fee (p) | τ send (p) | verdict (independent probes) | verdict (conflicting probes) |
|---|---|---|---|---|---|---|---|---|---|
| `5Us18hLZ…` | Agave | 139/144 | 5 | 0 | 20 | 0.02 (0.866) | 0.38 (0.004) | arrival order (partial, tau=0.38) | no rule detected - consistent with noise |
| `7QQGNm3p…` | Agave | 117/144 | 27 | 0 | 13 | -0.14 (0.391) | 0.24 (0.133) | no rule detected - consistent with noise | no rule detected - consistent with noise |
| `5Cchr1XG…` | AgaveBam | 126/144 | 15 | 3 | 16 | 0.40 (0.003) | 0.04 (0.754) | priority-fee order (partial, tau=0.40) | priority-fee order (strong, tau=0.61) |
| `DRpbCBMx…` | AgaveBam | 140/144 | 4 | 0 | 15 | 0.33 (0.011) | 0.27 (0.041) | weak evidence only (fee tau=0.33, p=0.011; arrival tau=0.27, p=0.041) | no rule detected - consistent with noise |
| `9jxgosAf…` | FireBAM | 95/144 | 49 | 0 | 11 | 0.36 (0.025) | 0.17 (0.328) | weak evidence only (fee tau=0.36, p=0.025) | priority-fee order (strong, tau=0.63) |
| `A4hyMd3F…` | FireBAM | 65/96 | 31 | 0 | 9 | 0.31 (0.154) | 0.14 (0.539) | no rule detected - consistent with noise | priority-fee order (strict, tau=0.94) |
| `9eGrDohd…` | Firedancer | 134/144 | 10 | 0 | 14 | 0.52 (<0.001) | -0.00 (0.993) | priority-fee order (partial, tau=0.52) | priority-fee order (strong, tau=0.69) |
| `EvnRmnMr…` | Firedancer | 89/96 | 4 | 3 | 11 | 0.10 (0.604) | 0.05 (0.805) | no rule detected - consistent with noise | no rule detected - consistent with noise |
| `JD549Hsb…` | Firedancer | 48/48 | 0 | 0 | 6 | -0.01 (0.961) | 0.49 (0.009) | arrival order (partial, tau=0.49) | no rule detected - consistent with noise |
| `CAo1dCGY…` | HarmonicAgave | 122/144 | 22 | 0 | 13 | 0.15 (0.294) | 0.25 (0.061) | no rule detected - consistent with noise | no rule detected - consistent with noise |
| `Fd7btgyS…` | HarmonicAgave | 133/144 | 8 | 3 | 15 | 0.44 (<0.001) | 0.21 (0.130) | priority-fee order (partial, tau=0.44) | priority-fee order (partial, tau=0.55) |
| `Awes4Tr6…` | HarmonicFiredancer | 129/144 | 11 | 4 | 16 | 0.33 (0.009) | 0.05 (0.728) | priority-fee order (partial, tau=0.33) | no rule detected - consistent with noise |
| `JUPiTERr…` | HarmonicFiredancer | 134/144 | 7 | 3 | 16 | 0.04 (0.820) | 0.19 (0.183) | no rule detected - consistent with noise | no rule detected - consistent with noise |
| `E1r4Psq8…` | JitoLabs | 128/144 | 13 | 3 | 14 | -0.15 (0.289) | 0.27 (0.054) | no rule detected - consistent with noise | no rule detected - consistent with noise |
| `HEL1USMZ…` | JitoLabs | 116/144 | 27 | 1 | 13 | 0.01 (0.925) | 0.25 (0.075) | no rule detected - consistent with noise | weak evidence only (arrival tau=0.47, p=0.021) |
| `E3mDbFMr…` | Rakurai | 85/96 | 11 | 0 | 10 | -0.04 (0.848) | 0.07 (0.735) | no rule detected - consistent with noise | no rule detected - consistent with noise |
| `ana2y2Yv…` | Rakurai | 137/144 | 7 | 0 | 15 | 0.24 (0.077) | 0.50 (<0.001) | arrival order (partial, tau=0.50) | arrival order (partial, tau=0.58) |

### Across the whole window (probes of one batch ordered by slot, then position)

| validator | client | windows | τ fee (p) | τ send (p) |
|---|---|---|---|---|
| `5Us18hLZ…` | Agave | 12 | 0.05 (0.497) | 0.22 (<0.001) |
| `7QQGNm3p…` | Agave | 11 | 0.06 (0.484) | 0.45 (<0.001) |
| `5Cchr1XG…` | AgaveBam | 11 | 0.13 (0.061) | 0.21 (0.002) |
| `DRpbCBMx…` | AgaveBam | 12 | 0.25 (<0.001) | 0.35 (<0.001) |
| `9jxgosAf…` | FireBAM | 9 | 0.37 (<0.001) | 0.37 (<0.001) |
| `A4hyMd3F…` | FireBAM | 6 | 0.39 (<0.001) | 0.28 (0.007) |
| `9eGrDohd…` | Firedancer | 12 | 0.27 (<0.001) | 0.15 (0.037) |
| `EvnRmnMr…` | Firedancer | 8 | 0.20 (0.020) | 0.20 (0.018) |
| `JD549Hsb…` | Firedancer | 4 | -0.09 (0.441) | 0.41 (<0.001) |
| `CAo1dCGY…` | HarmonicAgave | 10 | 0.09 (0.216) | 0.22 (<0.001) |
| `Fd7btgyS…` | HarmonicAgave | 12 | 0.28 (<0.001) | 0.24 (<0.001) |
| `Awes4Tr6…` | HarmonicFiredancer | 12 | 0.22 (0.009) | 0.22 (0.009) |
| `JUPiTERr…` | HarmonicFiredancer | 12 | 0.08 (0.297) | 0.16 (0.024) |
| `E1r4Psq8…` | JitoLabs | 12 | -0.19 (0.010) | 0.29 (<0.001) |
| `HEL1USMZ…` | JitoLabs | 11 | -0.04 (0.596) | 0.37 (<0.001) |
| `E3mDbFMr…` | Rakurai | 7 | -0.07 (0.423) | 0.17 (0.041) |
| `ana2y2Yv…` | Rakurai | 12 | -0.01 (0.894) | 0.38 (<0.001) |

## Per client family (independent probes pooled)

| client | validators | blocks | τ fee (p) | τ send (p) | verdict (independent) | verdict (conflicting) | across window: τ fee / τ send (p) |
|---|---|---|---|---|---|---|---|
| Agave | 2 | 33 | -0.04 (0.693) | 0.32 (0.002) | arrival order (partial, tau=0.32) | weak evidence only (arrival tau=0.35, p=0.025) | 0.05 (0.331) / 0.33 (<0.001) |
| AgaveBam | 2 | 31 | 0.37 (<0.001) | 0.16 (0.125) | priority-fee order (partial, tau=0.37) | priority-fee order (partial, tau=0.42) | 0.20 (<0.001) / 0.29 (<0.001) |
| FireBAM | 2 | 20 | 0.34 (0.009) | 0.16 (0.228) | priority-fee order (partial, tau=0.34) | priority-fee order (strong, tau=0.76) | 0.38 (<0.001) / 0.34 (<0.001) |
| Firedancer | 3 | 31 | 0.27 (<0.001) | 0.11 (0.230) | priority-fee order (partial, tau=0.27) | priority-fee order (partial, tau=0.49) | 0.19 (<0.001) / 0.21 (<0.001) |
| HarmonicAgave | 2 | 28 | 0.31 (<0.001) | 0.23 (0.015) | priority-fee order (partial, tau=0.31) | priority-fee order (partial, tau=0.49) | 0.20 (<0.001) / 0.23 (<0.001) |
| HarmonicFiredancer | 2 | 32 | 0.18 (0.054) | 0.12 (0.224) | no rule detected - consistent with noise | no rule detected - consistent with noise | 0.15 (0.008) / 0.19 (0.001) |
| JitoLabs | 2 | 27 | -0.07 (0.509) | 0.26 (0.007) | arrival order (partial, tau=0.26) | arrival order (partial, tau=0.42) | -0.12 (0.019) / 0.33 (<0.001) |
| Rakurai | 2 | 25 | 0.13 (0.235) | 0.33 (0.002) | arrival order (partial, tau=0.33) | arrival order (partial, tau=0.43) | -0.03 (0.537) / 0.30 (<0.001) |

## Landing by priority level

| group:µlamports/CU | target window | other leader | not landed | other |
|---|---|---|---|---|
| CONF:10000 | 161 | 21 | 2 | 0 |
| CONF:200000 | 162 | 21 | 1 | 0 |
| CONF:1000000 | 164 | 19 | 1 | 0 |
| CONF:4000000 | 163 | 21 | 0 | 0 |
| IND:0 | 158 | 22 | 4 | 0 |
| IND:1000 | 164 | 19 | 1 | 0 |
| IND:10000 | 158 | 24 | 2 | 0 |
| IND:50000 | 165 | 18 | 1 | 0 |
| IND:200000 | 162 | 20 | 2 | 0 |
| IND:1000000 | 157 | 24 | 3 | 0 |
| IND:4000000 | 161 | 22 | 1 | 0 |
| IND:16000000 | 162 | 20 | 2 | 0 |

## Supplementary evidence: all transactions in the target blocks

Spearman ρ between block position and fee per cost unit (negative ⇒ higher-paying transactions sit earlier). Computed over every non-vote transaction in the 4 slots of each targeted window, whether or not our probes landed.

| client | blocks | median ρ | median ρ (no Jito-tip txs) | median share of adjacent pairs in descending density | median relative position of tip txs |
|---|---|---|---|---|---|
| Agave | 96 | -0.05 | -0.05 | 0.52 | 0.47 |
| AgaveBam | 96 | -0.09 | -0.10 | 0.56 | 0.56 |
| FireBAM | 80 | -0.06 | -0.07 | 0.57 | 0.59 |
| Firedancer | 96 | -0.18 | -0.20 | 0.56 | 0.47 |
| HarmonicAgave | 96 | -0.10 | -0.09 | 0.55 | 0.55 |
| HarmonicFiredancer | 96 | -0.10 | -0.10 | 0.57 | 0.55 |
| JitoLabs | 96 | -0.02 | -0.03 | 0.54 | 0.59 |
| Rakurai | 80 | -0.06 | -0.07 | 0.55 | 0.56 |

Files: `probes.jsonl` (every probe: signature, fee level, send order, send/ack time), `statuses.json`, `blocks/<slot>.json.gz` (block order of every transaction + full JSON of our probes), `analysis/probe_landing.csv`, `analysis/passive_blocks.csv`, `analysis/results.json`.
