# Run report — run-20261030T152829Z

### run-20261030T152829Z (LIVE mainnet)
- Started 20261030T152829Z UTC; epoch 1072, first planned slot ≈ 463335759
- RPC `https://api.mainnet-beta.solana.com` (node 4.3.2); send path `https://api.mainnet-beta.solana.com`; send offset -1.0 slot(s) from window start
- Probe: CU limit 5000, priority levels (µlamports/CU) [0, 1000, 10000, 50000, 200000, 1000000, 4000000, 16000000], seed 20261030
- Batches fired: 128; skipped (late): 0; measured slot time 214 ms
- Actual spend: 0.024536 SOL (worst-case ledger 0.024671 SOL, cap 0.035 SOL)
- Unavailable slots (skipped by leader or not served): 0

Where probes landed relative to the target window (slot 0 = first slot of the window):

- `run-20261030T152829Z`: after_window: 156, 0: 95, 1: 720, 2: 426, 3: 132

## Primary evidence: our probes, per validator

tau > 0 means: higher priority fee (resp. earlier send) ⇒ earlier in the block. p = within-block permutation test (null: random order).

| validator | client | landed in window / sent | other leader | lost | blocks w/ 2+ | τ fee (p) | τ send (p) | verdict (independent probes) | verdict (conflicting probes) |
|---|---|---|---|---|---|---|---|---|---|
| `5Us18hLZ…` | Agave | 95/96 | 1 | 0 | 12 | -0.07 (0.697) | 0.21 (0.186) | no rule detected - consistent with noise | no rule detected - consistent with noise |
| `7QQGNm3p…` | Agave | 92/96 | 4 | 0 | 11 | -0.25 (0.178) | 0.23 (0.243) | no rule detected - consistent with noise | no rule detected - consistent with noise |
| `5Cchr1XG…` | AgaveBam | 80/96 | 15 | 1 | 11 | 0.35 (0.046) | 0.06 (0.744) | weak evidence only (fee tau=0.35, p=0.046) | weak evidence only (fee tau=0.67, p=0.014) |
| `DRpbCBMx…` | AgaveBam | 93/96 | 3 | 0 | 9 | 0.20 (0.194) | 0.31 (0.021) | weak evidence only (arrival tau=0.31, p=0.021) | no rule detected - consistent with noise |
| `9jxgosAf…` | FireBAM | 72/96 | 24 | 0 | 7 | 0.42 (0.002) | 0.02 (0.872) | priority-fee order (partial, tau=0.42) | weak evidence only (fee tau=0.56, p=0.020) |
| `A4hyMd3F…` | FireBAM | 65/96 | 31 | 0 | 9 | 0.31 (0.154) | 0.14 (0.539) | no rule detected - consistent with noise | priority-fee order (strict, tau=0.94) |
| `9eGrDohd…` | Firedancer | 87/96 | 9 | 0 | 9 | 0.42 (0.005) | 0.07 (0.692) | priority-fee order (partial, tau=0.42) | priority-fee order (strong, tau=0.71) |
| `EvnRmnMr…` | Firedancer | 89/96 | 4 | 3 | 11 | 0.10 (0.604) | 0.05 (0.805) | no rule detected - consistent with noise | no rule detected - consistent with noise |
| `CAo1dCGY…` | HarmonicAgave | 85/96 | 11 | 0 | 10 | 0.11 (0.535) | 0.28 (0.090) | no rule detected - consistent with noise | no rule detected - consistent with noise |
| `Fd7btgyS…` | HarmonicAgave | 88/96 | 8 | 0 | 11 | 0.52 (<0.001) | 0.25 (0.145) | priority-fee order (partial, tau=0.52) | no rule detected - consistent with noise |
| `Awes4Tr6…` | HarmonicFiredancer | 96/96 | 0 | 0 | 11 | 0.35 (0.006) | 0.06 (0.622) | priority-fee order (partial, tau=0.35) | no rule detected - consistent with noise |
| `JUPiTERr…` | HarmonicFiredancer | 86/96 | 7 | 3 | 12 | -0.03 (0.900) | 0.28 (0.136) | no rule detected - consistent with noise | no rule detected - consistent with noise |
| `E1r4Psq8…` | JitoLabs | 89/96 | 7 | 0 | 10 | -0.02 (0.878) | 0.35 (0.018) | weak evidence only (arrival tau=0.35, p=0.018) | no rule detected - consistent with noise |
| `HEL1USMZ…` | JitoLabs | 78/96 | 18 | 0 | 9 | 0.06 (0.783) | 0.32 (0.100) | no rule detected - consistent with noise | weak evidence only (arrival tau=0.52, p=0.027) |
| `E3mDbFMr…` | Rakurai | 85/96 | 11 | 0 | 10 | -0.04 (0.848) | 0.07 (0.735) | no rule detected - consistent with noise | no rule detected - consistent with noise |
| `ana2y2Yv…` | Rakurai | 93/96 | 3 | 0 | 10 | 0.14 (0.410) | 0.41 (0.006) | arrival order (partial, tau=0.41) | arrival order (partial, tau=0.54) |

### Across the whole window (probes of one batch ordered by slot, then position)

| validator | client | windows | τ fee (p) | τ send (p) |
|---|---|---|---|---|
| `5Us18hLZ…` | Agave | 8 | -0.03 (0.747) | 0.20 (0.009) |
| `7QQGNm3p…` | Agave | 8 | 0.00 (0.961) | 0.37 (<0.001) |
| `5Cchr1XG…` | AgaveBam | 7 | -0.01 (0.917) | 0.11 (0.204) |
| `DRpbCBMx…` | AgaveBam | 8 | 0.21 (0.011) | 0.32 (<0.001) |
| `9jxgosAf…` | FireBAM | 6 | 0.35 (<0.001) | 0.24 (0.008) |
| `A4hyMd3F…` | FireBAM | 6 | 0.39 (<0.001) | 0.28 (0.007) |
| `9eGrDohd…` | Firedancer | 8 | 0.24 (0.008) | 0.22 (0.018) |
| `EvnRmnMr…` | Firedancer | 8 | 0.20 (0.020) | 0.20 (0.018) |
| `CAo1dCGY…` | HarmonicAgave | 7 | 0.02 (0.820) | 0.13 (0.133) |
| `Fd7btgyS…` | HarmonicAgave | 8 | 0.31 (<0.001) | 0.23 (0.008) |
| `Awes4Tr6…` | HarmonicFiredancer | 8 | 0.24 (0.004) | 0.27 (<0.001) |
| `JUPiTERr…` | HarmonicFiredancer | 8 | 0.05 (0.578) | 0.12 (0.166) |
| `E1r4Psq8…` | JitoLabs | 8 | -0.12 (0.171) | 0.29 (<0.001) |
| `HEL1USMZ…` | JitoLabs | 7 | -0.02 (0.818) | 0.41 (<0.001) |
| `E3mDbFMr…` | Rakurai | 7 | -0.07 (0.423) | 0.17 (0.041) |
| `ana2y2Yv…` | Rakurai | 8 | -0.07 (0.403) | 0.31 (<0.001) |

## Per client family (independent probes pooled)

| client | validators | blocks | τ fee (p) | τ send (p) | verdict (independent) | verdict (conflicting) | across window: τ fee / τ send (p) |
|---|---|---|---|---|---|---|---|
| Agave | 2 | 23 | -0.16 (0.190) | 0.22 (0.066) | no rule detected - consistent with noise | weak evidence only (arrival tau=0.35, p=0.043) | -0.01 (0.858) / 0.29 (<0.001) |
| AgaveBam | 2 | 20 | 0.28 (0.013) | 0.17 (0.150) | weak evidence only (fee tau=0.28, p=0.013) | weak evidence only (fee tau=0.37, p=0.042) | 0.11 (0.076) / 0.22 (<0.001) |
| FireBAM | 2 | 16 | 0.36 (0.002) | 0.09 (0.505) | priority-fee order (partial, tau=0.36) | priority-fee order (strong, tau=0.75) | 0.37 (<0.001) / 0.26 (<0.001) |
| Firedancer | 2 | 20 | 0.24 (0.044) | 0.06 (0.633) | weak evidence only (fee tau=0.24, p=0.044) | priority-fee order (partial, tau=0.59) | 0.22 (<0.001) / 0.21 (<0.001) |
| HarmonicAgave | 2 | 21 | 0.32 (0.004) | 0.27 (0.024) | priority-fee order (partial, tau=0.32) | no rule detected - consistent with noise | 0.17 (0.004) / 0.18 (0.003) |
| HarmonicFiredancer | 2 | 23 | 0.15 (0.182) | 0.18 (0.132) | no rule detected - consistent with noise | no rule detected - consistent with noise | 0.15 (0.019) / 0.19 (0.001) |
| JitoLabs | 2 | 19 | 0.01 (0.910) | 0.34 (0.005) | arrival order (partial, tau=0.34) | no rule detected - consistent with noise | -0.07 (0.248) / 0.35 (<0.001) |
| Rakurai | 2 | 20 | 0.05 (0.700) | 0.24 (0.042) | weak evidence only (arrival tau=0.24, p=0.042) | weak evidence only (arrival tau=0.38, p=0.016) | -0.07 (0.247) / 0.25 (<0.001) |

## Landing by priority level

| group:µlamports/CU | target window | other leader | not landed | other |
|---|---|---|---|---|
| CONF:10000 | 117 | 11 | 0 | 0 |
| CONF:200000 | 115 | 13 | 0 | 0 |
| CONF:1000000 | 116 | 12 | 0 | 0 |
| CONF:4000000 | 115 | 13 | 0 | 0 |
| IND:0 | 112 | 14 | 2 | 0 |
| IND:1000 | 116 | 12 | 0 | 0 |
| IND:10000 | 111 | 16 | 1 | 0 |
| IND:50000 | 115 | 12 | 1 | 0 |
| IND:200000 | 115 | 13 | 0 | 0 |
| IND:1000000 | 112 | 15 | 1 | 0 |
| IND:4000000 | 115 | 12 | 1 | 0 |
| IND:16000000 | 114 | 13 | 1 | 0 |

## Supplementary evidence: all transactions in the target blocks

Spearman ρ between block position and fee per cost unit (negative ⇒ higher-paying transactions sit earlier). Computed over every non-vote transaction in the 4 slots of each targeted window, whether or not our probes landed.

| client | blocks | median ρ | median ρ (no Jito-tip txs) | median share of adjacent pairs in descending density | median relative position of tip txs |
|---|---|---|---|---|---|
| Agave | 64 | -0.06 | -0.06 | 0.52 | 0.45 |
| AgaveBam | 64 | -0.10 | -0.10 | 0.55 | 0.56 |
| FireBAM | 64 | -0.06 | -0.07 | 0.57 | 0.59 |
| Firedancer | 64 | -0.14 | -0.15 | 0.55 | 0.47 |
| HarmonicAgave | 64 | -0.10 | -0.09 | 0.55 | 0.55 |
| HarmonicFiredancer | 64 | -0.08 | -0.09 | 0.57 | 0.54 |
| JitoLabs | 64 | -0.02 | -0.04 | 0.54 | 0.56 |
| Rakurai | 64 | -0.08 | -0.09 | 0.55 | 0.54 |

Files: `probes.jsonl` (every probe: signature, fee level, send order, send/ack time), `statuses.json`, `blocks/<slot>.json.gz` (block order of every transaction + full JSON of our probes), `analysis/probe_landing.csv`, `analysis/passive_blocks.csv`, `analysis/results.json`.
