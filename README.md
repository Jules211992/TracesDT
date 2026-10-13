# TracesDT: Safeguarding Agentic Cyber Response Under Compromised Digital Twin States in Industrial IoT
### Tennessee Eastman Process + Qwen3:8b Agent + Cyber-Physical Safeguard + Hyperledger Fabric + IPFS | IEEE TIFS Submission

> **Reproducibility repository** for the paper:
> *"TracesDT: Safeguarding Agentic Cyber Response Under Compromised Digital Twin States in Industrial IoT"*
> Submitted to IEEE Transactions on Information Forensics and Security

---

## Table of Contents

1. [Overview](#1-overview)
2. [System Architecture](#2-system-architecture)
3. [Testbed: 14-VM Infrastructure](#3-testbed-14-vm-infrastructure)
4. [Prerequisites](#4-prerequisites)
5. [Repository Structure](#5-repository-structure)
6. [Safeguard Decision Logic](#6-safeguard-decision-logic)
7. [Attack Scenarios and Methods](#7-attack-scenarios-and-methods)
8. [Evaluation Campaigns](#8-evaluation-campaigns)
9. [Generating the Figures](#9-generating-the-figures)
10. [Expected Results Summary](#10-expected-results-summary)
11. [Data Provenance and Integrity](#11-data-provenance-and-integrity)
12. [Citation](#12-citation)
13. [License](#13-license)

---

## 1. Overview

TracesDT treats every output of an AI cyber-response agent as an **untrusted proposal**. Before any physical action reaches an industrial process, a cyber-physical safeguard validates the proposal against an independent safety reference and returns one of four decisions: `EXECUTE`, `BLOCK`, `CORRECT`, or `ESCALATE`. Physical execution additionally requires **action-bound 2-of-3 authorization** on Hyperledger Fabric, and the complete decision evidence is stored in a private **IPFS cluster** and anchored on the ledger.

| Layer | Technology | Role |
|---|---|---|
| **Physical process** | Tennessee Eastman Process (TEP), closed loop, 1-s step | Ground-truth physical state $X_t^P$ |
| **Digital twin** | 41-measurement twin of TEP | Agent-visible state $X_t^{DT}$ (attack surface) |
| **Agent** | Qwen3:8b served locally with Ollama | Structured action proposal (ACT01–ACT10) |
| **Safeguard** | Python (`phases/P07_safeguard`) | Compromise alarm $z_t$ and decision $d_t$ |
| **Authorization** | Hyperledger Fabric, 3 orgs, 3 RAFT orderers | 2-of-3 action-bound endorsement |
| **Evidence** | Private IPFS cluster, 5 nodes, $r=3$ | Content-addressed evidence bundle $E_t$ |

**Key results (from the paper):**

| Metric | Value |
|---|---|
| Unsafe executions, B0 (no safeguard), R01 | 30/180 (UER 16.7%) |
| Unsafe executions, B3 (TracesDT), R01 | 0/180 (UER 0%) |
| Successful responses, B3, R01 | 180/180 (RSR 100%) |
| Safe proposals wrongly blocked, R02 | 0/60 (FABR 0%) |
| Post-validation substitutions executed (R07A): B1 / B2 / B3 | 20/20 / 20/20 / 0/20 |
| Evidence-chain violations detected (R07) | 90/90 |
| Authentic Qwen3:8b ACT03 proposals corrected to ACT06 (R12) | 30/30 |
| Peak Fabric throughput (Caliper) | 1,589.2 TPS |
| Safeguard check latency (10 seeds, B3/A1/S1) | 0.082–0.103 ms |
| Agent inference latency (10 seeds, B3/A1/S1) | 31.5–52.8 s (median 33.1 s) |

---

## 2. System Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│  PHYSICAL PROCESS: Tennessee Eastman Process (closed loop, 1-s step) │
│  X_t^P : 41 XMEAS measurements, XMV actuators                        │
└───────────────┬──────────────────────────────────────▲───────────────┘
                │ measurements                         │ authorized action only
                ▼                                      │
┌───────────────────────────────┐        ┌─────────────┴────────────────┐
│ DIGITAL TWIN  X_t^DT          │        │ EXECUTION GATEWAY            │
│ (attack surface: A1–A6)       │        │ executes â_t iff α_t = 1     │
└───────────────┬───────────────┘        └─────────────▲────────────────┘
                │ observed state                       │
                ▼                                      │
┌───────────────────────────────┐        ┌─────────────┴────────────────┐
│ AI AGENT  Qwen3:8b (Ollama)   │        │ HYPERLEDGER FABRIC           │
│ proposal p_t = (a_t, ...)     │        │ 3 orgs · 3 RAFT orderers     │
│ temperature 0, stateless      │        │ 2-of-3 action-bound endorse. │
└───────────────┬───────────────┘        │ R_t^auth  /  R_t^audit (CID) │
                │ untrusted proposal     └─────────────▲───────▲────────┘
                ▼                                      │       │ CID anchoring
┌───────────────────────────────────────────────┐      │  ┌────┴─────────────┐
│ CYBER-PHYSICAL SAFEGUARD                      │      │  │ IPFS CLUSTER     │
│ diagnostic checks → compromise alarm z_t      │──────┘  │ 5 nodes, r = 3   │
│ action safety + authorization → decision d_t  │────────▶│ evidence E_t     │
│ EXECUTE | BLOCK | CORRECT | ESCALATE          │         └──────────────────┘
└───────────────────────────────────────────────┘
        ▲ independent safety reference R_t (trusted physical measurements)
```

---

## 3. Testbed: 14-VM Infrastructure

All infrastructure VMs run on the Beluga cloud (Digital Research Alliance of Canada). The allocation uses all 80 available vCPUs, with larger allocations for the Fabric peers and RAFT orderers so that ordering and validation do not dominate the measured throughput.

| # | Role | VMs | vCPUs | RAM | Storage |
|---|---|---|---|---|---|
| 1–3 | Fabric peers | 3 | 8 | 16 GB | 80 GB |
| 4–6 | RAFT orderers | 3 | 6 | 12 GB | 60 GB |
| 7–11 | IPFS nodes | 5 | 4 | 8 GB | 80 GB |
| 12 | Edge gateway | 1 | 8 | 16 GB | 80 GB |
| 13 | Baseline PostgreSQL | 1 | 6 | 12 GB | 80 GB |
| 14 | Monitoring | 1 | 4 | 8 GB | 40 GB |
| | **Total** | **14** | **80** | **160 GB** | **≈1 TB** |

The vCPU, RAM, and storage columns are per VM.

---

## 4. Prerequisites

### Figure regeneration (any machine)
```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```
Tested with Python 3.13, matplotlib 3.11.2, pandas 3.0.5, numpy 2.5.3.

### Full experimental stack
- Tennessee Eastman simulator: open-source `jkitchin/tennessee-eastman-profbraatz`
- Ollama with the `qwen3:8b` model (temperature 0, thinking disabled, 120-s timeout)
- Hyperledger Fabric (3 organizations, 3 peers, 3 RAFT orderers)
- Private IPFS cluster (5 nodes, replication factor 3)
- Hyperledger Caliper (Fabric capacity benchmark)

---

## 5. Repository Structure

```
tracesdt/
├── README.md
├── LICENSE
├── requirements.txt
│
├── phases/                              # Experimental pipeline (original project layout)
│   └── P07_safeguard/
│       └── scripts/
│           ├── safeguard_v1.py          # Checks: state, temporal, freshness,
│           │                            # reference, physical consistency, authorization
│           └── safeguard_v3.py          # Final two-output policy (alarm z_t, decision d_t)
│
├── analysis/
│   ├── make_figures.py                  # Builds every paper figure from source data only
│   ├── verify_sources.py                # Checks SHA-256 of all figure source files
│   └── reproduce_figures.sh             # Regenerates Figs. 3, 4, 6–10 with paper file names
│
├── data/
│   ├── figure_sources/                  # Exact source files read by make_figures.py
│   │   ├── FIG_3/ … FIG_9/
│   │   └── FILES_SHA256_PROVENANCE.{csv,json}
│   └── manifest/
│       └── TRACES_DT_ALL_RESULTS_MANIFEST.{csv,json}   # 7,229 result files, SHA-256
│
└── figures/                             # Figures exactly as in the paper (PDF)
    ├── Fig3.pdf  Fig4.pdf  Fig6.pdf  Fig7.pdf
    └── Fig8.pdf  Fig9.pdf  Fig10.pdf
```

---

## 6. Safeguard Decision Logic

The safeguard separates **diagnosis** from **enforcement** (`safeguard_v3.py`):

- **Diagnostic checks** (state validation, physical consistency, temporal consistency, freshness) only raise the compromise alarm $z_t$.
- **Enforcement** decides $d_t$ in the following priority order:

| Priority | Condition | Decision |
|---|---|---|
| 1 | Safety reference invalid or sequence-mismatched | `ESCALATE` |
| 2 | Agent proposed human escalation (ACT09) | `ESCALATE` |
| 3 | Proposal or command not authorized (differs from frozen catalog) | `BLOCK` |
| 4 | Eligible set $M_t$ from reference contains the proposed action | `EXECUTE` |
| 5 | $M_t=\varnothing$ for a physical action | `BLOCK` |
| 6 | $\lvert M_t\rvert = 1$ (single eligible alternative) | `CORRECT` |
| 7 | Otherwise (ambiguous eligible set) | `ESCALATE` |

For ACT10 (no action) with $M_t=\varnothing$, the decision is `EXECUTE`. Only `EXECUTE` and `CORRECT` generate a Fabric authorization request.

---

## 7. Attack Scenarios and Methods

| ID | Attack | Target | S1 | S2 | S3 |
|---|---|---|---|---|---|
| A1 | False data injection | XMEAS(12) | 47.001% | 43.501% | 38.135% |
| A2 | Replay | XMEAS(1)–XMEAS(41) | 1 s | 19 s | 342 s |
| A3 | Time desynchronization | Source timestamp | 220 ms | 1000 ms | 19,000 ms |
| A4 | Selective sensor poisoning | XMEAS(15) | 46.935% (25%) | 43.468% (50%) | 36.628% (100%) |
| A5 | Actuator-state spoofing | XMV_DT(7) | 44.973% | 72.486% | 94.497% |
| A6 | Coordinated stealth | XMEAS(12) + XMV_DT(7) | A1 + A5 | A1 + A5 | A1 + A5 |

| Method | Description |
|---|---|
| **B0** | No pre-execution protection |
| **B1** | Schema, critical bounds, freshness, and residual validation |
| **B2** | Rule-based guard against trusted physical measurements |
| **B3** | **TracesDT** |
| **Oracle** | Same agent observing $X_t^P$, no safeguard |

Main campaign: 6 attacks × 3 severities × 4 methods × 10 seeds = 720, plus 180 Oracle runs = **900 evaluations**. Seeds 20260919–20260928. 600-s warm-up; attack active from sequence 600 for 300 s; one agent decision at sequence 600.

---

## 8. Evaluation Campaigns

| ID | Purpose | Population |
|---|---|---|
| R01 | Main CPS campaign | 900 evaluations |
| R02 | Legitimate-action preservation | 60 trials per method |
| R03C | Safeguard mechanism isolation and policy replay | 7 unit tests; 6 isolation tests; 240 replayed records |
| R04 | Fabric authorization semantics | 30 trials; 80 rejection checks |
| R05 | Explicit-quorum finalization load | 2 offered-load points |
| R06 | Physical outcome of ACT06 vs. no actuation; ACT01 mitigation | 10 paired seeds |
| R07 | End-to-end evidence integrity | 30 chains; 120 negative checks |
| R07A | Post-validation action substitution | 60 evaluations |
| R10 | Honest and forged-fresh replay | 30 seeds; 1530 decision cases; 150 trajectories |
| R11 | Fabric read latency | 30 reads per query |
| R12 | Authentic agent outputs | 30 seeds |
| P14 | Fabric fault probes | 3 probes |

Campaigns differ in protocol and population; their results are reported separately and are not pooled.

---

## 9. Generating the Figures

All figures are built **only** from the source files in `data/figure_sources/`; no value is simulated, interpolated, or estimated.

```bash
source venv/bin/activate
bash analysis/reproduce_figures.sh            # output: figures_regenerated/
```

The script writes `Fig3.pdf`, `Fig4.pdf`, `Fig6.pdf`–`Fig10.pdf` together with one `PLOTTED_VALUES_*.csv` file per figure listing every plotted value. The regenerated PDFs are pixel-identical to those in `figures/`. Single figures can be rebuilt with:

```bash
python3 analysis/make_figures.py data/figure_sources out/ 4,8
```

| Paper figure | Function | Campaign | Content |
|---|---|---|---|
| Fig. 3 | `fig3d` | R01 | XMV(7) commands after the agent decision, B0, A6-S3 |
| Fig. 4 | `fig4` | R01 | UPR, UER, and PSV per method (Wilson 95% CIs) |
| Fig. 6 | `fig6` | IPFS | IPFS performance versus object size |
| Fig. 7 | `fig7c` | R01 | Agent inference and safeguard-check latency, B3/A1-S1 |
| Fig. 8 | `fig8` | R10 | Decision and eligibility changes under replay |
| Fig. 9 | `fig9` | R12 | Authentic Qwen3:8b outputs and safeguard decisions |
| Fig. 10 | `fig10h` | R11, P14 | Fabric read latency and fault probes |

---

## 10. Expected Results Summary

### R01 — Main CPS campaign (Table V)
| Method | UPR | UER | RSR | PSV |
|---|---|---|---|---|
| B0 | 16.7% (30/180) | 16.7% (30/180) | 83.3% (150/180) | 1.1% (2/180) |
| B1 | 16.7% (30/180) | 0% (0/180) | 100% (180/180) | 0% |
| B2 | 16.7% (30/180) | 0% (0/180) | 100% (180/180) | 0% |
| **B3 (TracesDT)** | 16.7% (30/180) | **0% (0/180)** | **100% (180/180)** | **0%** |
| Oracle | 0% (0/180) | 0% (0/180) | 100% (180/180) | 0% |

B3 vs. B0, seed-clustered exact McNemar with Holm adjustment: $p_{\mathrm{Holm}} = 0.00586$ (UER and RSR). The two B0 PSV rows share one physical-event signature.

### R07A — Post-validation action substitution
| Method | UER | RSR |
|---|---|---|
| B1 | 100% (20/20) | 0% (0/20) |
| B2 | 100% (20/20) | 0% (0/20) |
| **B3 (TracesDT)** | **0% (0/20)** | **100% (20/20)** |

Exact McNemar with Holm adjustment: $p_{\mathrm{Holm}} = 3.81\times10^{-6}$; seed-clustered: $p_{\mathrm{Holm}} = 0.00390625$.

### Fabric capacity (Caliper) and explicit quorum (R05)
| Protocol | Offered TPS | Achieved | p50 | p95 | p99 |
|---|---|---|---|---|---|
| Caliper | 3000 | 1321.3 TPS | 0.891 s | 2.223 s | 2.974 s |
| Caliper | 4500 | **1589.2 TPS** | 0.499 s | 0.764 s | 0.828 s |
| Caliper | 6000 | 1333.5 TPS | 4.043 s | 20.621 s | 22.622 s |
| Explicit quorum | 3000 | 718.4 fin./s | 8.850 s | 10.720 s | 11.229 s |
| Explicit quorum | 4500 | 466.3 fin./s (saturation) | 10.069 s | 11.210 s | 11.438 s |

### IPFS evidence availability
| Condition | Nodes available | Retrieved | Hash verified | Mean GET (s) |
|---|---|---|---|---|
| N0 | 5/5 | 9/9 | 9/9 | 0.140 |
| N1 | 4/5 | 9/9 | 9/9 | 0.138 |
| N2 | 3/5 | 9/9 | 9/9 | 0.143 |

### Ablation and robustness
| Test | Result |
|---|---|
| Diagnostic-check isolation (R03C) | Each check raises its alarm; ablation removes it |
| Gate isolation (R03C) | Ablating Action Safety or Authorization turns `BLOCK` into `EXECUTE` |
| B3 policy replay (R03C) | 240/240 replayed; alarms 180/180 (R01), 0/60 (R02) |
| Fabric quorum semantics (R04) | Single-org and duplicate approvals rejected 30/30 each; quorum 30/30 |
| Evidence integrity (R07) | 30/30 chains reconstructed; 90/90 violations detected |
| Honest vs. forged-fresh replay (R10) | Decision changed in 120/120 vs. 0/120 cases per set |
| Authentic agent outputs (R12) | 30/30 ACT03 proposals corrected to ACT06 |

### End-to-end pilot (B3/A1/S1, single observation)
| Component | Time |
|---|---|
| Digital-twin update | 0.118 ms |
| Agent reasoning | 51.036 s |
| Safeguard evaluation | 0.424 ms |
| Evidence finalization (IPFS + Fabric) | 5.018 s |
| **Event-to-audit total** | **56.055 s** |

---

## 11. Data Provenance and Integrity

- `data/figure_sources/FILES_SHA256_PROVENANCE.csv` lists the SHA-256 of every source file used for the figures.
- `data/manifest/TRACES_DT_ALL_RESULTS_MANIFEST.csv` catalogs the 7,229 JSON/CSV result files produced by the campaigns (3,257 unique SHA-256), with source archive, internal path, and size.

Verify every figure source file against its recorded hash:

```bash
python3 analysis/verify_sources.py
```

---

## 12. Citation

```bibtex
@article{mbara2026tracesdt,
  author  = {Mbara, Jules Martial Yin-Belta and Jaafar, Fehmi and Tardif, Pierre-Martin},
  title   = {{TracesDT}: Safeguarding Agentic Cyber Response Under Compromised Digital Twin States in Industrial {IoT}},
  journal = {IEEE Transactions on Information Forensics and Security},
  note    = {Under review},
  year    = {2026}
}
```

---

## 13. License

This project is licensed under the MIT License — see [LICENSE](LICENSE).
The Tennessee Eastman simulator (`jkitchin/tennessee-eastman-profbraatz`), Hyperledger Fabric (Apache 2.0), IPFS (MIT/Apache 2.0), Ollama, and Qwen3 are distributed under their own licenses.

<p align="center">
  <em>Developed at the Université du Québec à Chicoutimi (UQAC)
  and Université de Sherbrooke — IEEE TIFS Submission 2026</em>
</p>
