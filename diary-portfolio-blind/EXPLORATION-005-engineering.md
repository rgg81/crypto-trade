# EXPLORATION-005 — Engineering Report (weekly re-cadence of the mid-vol tail-capped neutral)

- **Track:** baseline-blind top-20 L/S portfolio (worktree `quant-portfolio-blind`)
- **Branch:** `quant-portfolio-blind`
- **The one change vs EXPLORATION-002 (frozen):** `rebal: 6 → 21` (2-day → weekly).
  Everything else byte-identical to /002: `lowvol_signal(window=12)`,
  `pit_topn_universe(top_n=20, lookback=30)`, `weighting="midvol_short"`,
  `long_frac=0.5` / `short_frac=0.25`, `gross=1.0`, `CostModel(5.0, 2.5, True)`,
  `load_funding(panel)` ON. So the +0.09 → +0.91 Sharpe delta is attributable
  SOLELY to cadence.
- **IS-only. OOS sealed at `OOS_CUTOFF = 2025-03-24`. Not looked at.**
- **Artifacts:**
  - `analysis/portfolio/blind_exploration_005.py` (new — full characterization + cadence table)
  - `tests/test_blind_engine.py` (+1 leak test at rebal=21; 33 total)
- **No engine code changes. No commits (per task instruction).**

---

## 1. Test suite: 33/33 green

`uv run pytest tests/test_blind_engine.py -q` → **33 passed in 1.13s**.

- Existing 32 tests byte-identical (no regression — no engine edits).
- **NEW:** `test_future_corruption_leaves_past_identical_midvol_rebal21` — the
  load-bearing leak positive-control at the weekly cadence (brief §6.4). Mirrors
  `test_future_corruption_leaves_past_identical_midvol` (rebal=6) but at
  `rebal=21` WITH funding corruption included. Corrupts `signal + open + funding`
  from `cutoff=260` forward (260 % 21 = 8 → falls BETWEEN rebal steps, the general
  case) and asserts past `weights / turnover / equity / funding_rets` are
  bit-identical (`np.testing.assert_array_equal`). Non-vacuous check confirms the
  corruption actually changes post-cutoff weights. **PASS** — no cadence-dependent
  look-ahead manifests at the sparser weekly decision points.

---

## 2. Primary book @ rebal=21 — full characterization (brief §6.2)

`run_backtest(panel_is, lowvol_signal, pit_topn_universe(20,30), CostModel(5,2.5,True),
gross=1.0, rebal=21, funding=load_funding, weighting="midvol_short")`

### 2.1 Headline (post-warmup, warmup=63)

| metric | value | (2x-cost) |
|---|---|---|
| **Sharpe** | **+0.913** | +0.771 |
| ann return | +25.5% | — |
| **maxDD** | **−32.99%** | — |
| **turnover** | **55.4x/yr one-way** | — |
| win rate | 53.5% | — |
| final equity | 3.232 | — |
| n_periods | 5663 | — |

### 2.2 Per-year Sharpe + per-year maxDD (G4 input)

| year | Sharpe | maxDD |
|---|---|---|
| 2020 | +1.51 | −23.4% |
| 2021 | +1.10 | −19.6% |
| 2022 | +1.07 | −17.3% |
| 2023 | **+0.35** | −32.5% |
| 2024 | +0.46 | −33.0% |
| 2025Q1 | +2.15 | −9.3% |

**min per-year Sharpe = +0.35 (2023).** All 6 regimes positive. The two most
diagnostic years — 2021 (shorts usually blow up in mania) and 2022 (longs usually
crash in deleveraging) — are BOTH strongly positive (+1.10 / +1.07).

### 2.3 Benchmarks (IS, same cadence)

| benchmark | Sharpe | maxDD | turn/yr |
|---|---|---|---|
| **primary midvol_short @ rebal=21** | **+0.913** | **−33.0%** | 55x |
| EW-top-20 @ rebal=21 | +0.420 | −90.2% | 21x |
| B&H BTC | +1.075 | — | — |

G2 read-out: primary +0.91 vs EW +0.42 → **delta +0.49** (threshold +0.15).

### 2.4 Funding attribution @ rebal=21 (bps of equity; + = drag, − = income)

| year | total_net | long_leg_pays | short_leg_pays |
|---|---|---|---|
| 2020 | +160.2 | +1148.2 | **−988.0** |
| 2021 | **−208.0** | +2037.1 | **−2245.1** |
| 2022 | +313.3 | −161.7 | +475.1 |
| 2023 | +882.8 | +162.3 | +720.4 |
| 2024 | −149.3 | +565.0 | −714.3 |
| 2025 | +131.8 | +31.9 | +99.9 |
| **TOTAL** | **+1130.8** | **+3782.8** | **−2652.0** |

**Near-neutrality dodge survives weekly cadence.** 2021 is NET INCOME (−208 bps):
shorts received +2245 bps, longs paid +2037 bps. /002 at rebal=6 reported 2021
−240 bps / total +1355 bps; here 2021 −208 bps / total +1131 bps — same sign
structure, same order of magnitude. Shorts receive income in mania years
(2020/2021/2024/2025: positive funding regimes), pay in stress years (2022/2023).

### 2.5 Long-leg vs short-leg per-year PRICE P&L (fraction of equity)

| year | long_leg | short_leg |
|---|---|---|
| 2020 | +0.6043 | −0.1343 |
| 2021 | +1.0897 | −0.7255 |
| 2022 | **−0.6245** | **+0.9414** |
| 2023 | +0.4820 | −0.2474 |
| 2024 | +0.3985 | −0.2147 |
| 2025 | −0.1455 | +0.3175 |
| **TOTAL** | **+1.8044** | **−0.0629** |

Both legs contribute. **The short leg's value is regime insurance:** in the 2022
crash the long leg lost −0.62 while the short leg delivered +0.94 → net +0.32 in
the worst crypto year. /002 at rebal=6 reported short-leg 2022 +0.9280; here
+0.9414 — the bear-dampening property is preserved (slightly stronger) at weekly
cadence. The short leg loses modestly in bull years (expected — shorts lose when
prices rise); the long leg carries the bull alpha (+1.80 total).

### 2.6 Structural invariants @ rebal=21

| invariant | observed | note |
|---|---|---|
| gross leverage | mean **1.0044**, max 1.94, min_active 0.49 | target 1.0; intra-rebal drift ±~2x |
| dollar neutrality | mean\|sum(w)\| **1.0e-17**, max 5.6e-17 | machine-epsilon perfect at all 271 rebal steps |
| max per-name \|w\| | **−0.3612** (ORDIUSDT, k=4304) | **> 20% — flagged** (see note) |

**Dollar neutrality** at rebal=21 is cleaner than /002's rebal=6 values (mean
4.7e-4, max 0.25). Reason: /002's divergence came from the warmup-edge force-exit
on invalid prices (coins not yet trading at k=6,12,18...). At rebal=21 the first
rebal is k=21, by which point all top-20 coins have valid prices → no force-exit
divergence → perfect neutrality by construction.

**Max per-name |w| = 0.36 FLAG:** this is INTRA-REBAL DRIFT, not a target weight.
Under `midvol_short` the TARGET per-short weight is 0.5/5 = 0.10. k=4304 is NOT a
rebal step (4304 % 21 = 20) — it's the 20th candle after the last rebal. ORDIUSDT
(a short) was squeezed (price rose ~3.6x relative to equity), so its effective
short weight grew from ~0.10 to ~0.36 before the next weekly rebal clamped it
back. At rebal=6 (/002) this drift is ~3x smaller (more frequent clamping). This
is the **weekly-cadence tradeoff**: lower turnover cost (55x vs 138x) but larger
intra-rebal drift (max |w| 0.36 vs /002's warmup-edge-only excursions). It did
NOT break G3 (maxDD −33% passes) — the drift was absorbed. Flagged for the
Critic's awareness; not a gate failure.

---

## 3. CADENCE-ROBUSTNESS TABLE {6, 21, 42, 63} (brief §6.3 — LOAD-BEARING anti-cherry-pick)

Same construction, only `rebal` varies. IS-only, funding ON.

| rebal | cad | Sharpe | 2x-cost | maxDD | turn/yr | ann | min-PY | per-year Sharpe |
|---|---|---|---|---|---|---|---|---|
| 6 | 2d | **+0.09** | −0.29 | −48.5% | 138x | −1.3% | **−0.79** | 2020:+0.81 2021:−0.38 2022:+0.89 2023:−0.79 2024:−0.34 2025:+3.18 |
| **21** | **1wk** | **+0.91** | +0.77 | **−33.0%** | 55x | +25.5% | **+0.35** | 2020:+1.51 2021:+1.10 2022:+1.07 2023:+0.35 2024:+0.46 2025:+2.15 |
| 42 | 2wk | **+0.97** | +0.90 | −41.0% | 30x | +29.0% | **+0.60** | 2020:+0.62 2021:+0.87 2022:+1.38 2023:+0.60 2024:+0.98 2025:+3.92 |
| 63 | 3wk | +0.84 | +0.80 | −48.5% | 21x | +28.0% | −0.16 | 2020:+0.64 2021:+0.52 2022:+1.68 2023:−0.16 2024:+2.64 2025:+3.39 |

### Honest read-out (observed facts, not a verdict)

- **Robust (no fragile spike at 21): YES.** The slow regime {21, 42, 63} is a
  clean plateau: Sharpe ∈ [0.84, 0.97], 2x-cost ∈ [0.77, 0.90]. The fast outlier
  {6} is far below at +0.09 / −0.29. There is no isolated spike at exactly 21.
- **Monotone in Sharpe: NO — it is hump-shaped.** Sharpe rises 6→21→42 (+0.09 →
  +0.91 → +0.97) then FALLS 42→63 (+0.97 → +0.84). **42 is the table Sharpe-max,
  not 21.** min-per-year-Sharpe follows the same hump (−0.79 → +0.35 → +0.60 →
  −0.16).
- **Monotone in turnover: YES.** 138x → 55x → 30x → 21x, strictly decreasing —
  the mechanical cost-drag direction is monotone in cadence, as the brief §3(b)
  mechanism predicts.
- **Implication for the selection-bias defense:** the brief §3(b) claims a
  "monotone slow>fast regime." That is literally true for turnover (the
  mechanical cause) but NOT for Sharpe (hump-shaped). The stronger observation:
  **the a-priori hypothesis (21) is NOT the table Sharpe-max** — 42 edges it out
  (+0.97 vs +0.91). If the cadence had been mined for the best IS Sharpe, 42
  would have been selected, not 21. The fact that 21 was pre-registered and 42
  slightly beats it is consistent with pre-registration rather than data-mining.
  The Critic owns the cherry-pick verdict.

---

## 4. Parity check (brief §6.5 — regression guard)

| metric | rebal=6 observed | /002 target | delta | verdict |
|---|---|---|---|---|
| Sharpe | +0.088 | +0.09 | −0.002 | OK (±0.005) |
| maxDD | −48.47% | −48% | −0.005 | OK (±2%) |
| turnover | 138x | 138x | −0.2 | OK (±5x) |

**PARITY OK.** The rebal=6 row reproduces /002's frozen construction exactly →
the +0.09 → +0.91 delta is purely the cadence change, not a construction drift.

---

## 5. Funding-coverage assertion @ rebal=21 (brief §6.4 deliverable)

`assert_funding_coverage(panel_is, fund, univ_is, strict=False)` → **1 missing
member: LITUSDT.** This is the carried /002 residual (LITUSDT is an IS-universe
member for ~35 candles whose funding CSV starts 2025-12-23, post-IS). Universe is
FROZEN; no new gaps introduced by the cadence change (universe is cadence-
invariant). Impact is a small positive bias on the short book's reported P&L
(a short in LITUSDT would have PAID funding we did not model) — single-digit bps,
immaterial. Documented in /002; unchanged here.

---

## 6. G1–G6 raw observations (gate verdicts are QR's Phase-7 call)

| # | gate | threshold | observed | status |
|---|---|---|---|---|
| G1 | IS Sharpe | ≥ +0.60 | +0.913 | PASS |
| G2 | IS Sharpe ≥ EW + 0.15 | ≥ +0.60 (Δ≥0.15) | +0.91 vs +0.42, Δ+0.49 | PASS |
| G3 | maxDD | ≥ −50% | −32.99% | PASS |
| G4 | per-year Sharpe all ≥ 0 | all ≥ 0 | min +0.35 (2023) | PASS |
| G5 | 2x-cost Sharpe | ≥ +0.50 | +0.771 | PASS |
| G6 | turnover | ≤ 100x/yr | 55.4x | PASS |

All six clear. **Gate verdicts are the QR's call; this table states observed
values only.**

---

## 7. Anomaly / forensic notes

1. **Intra-rebal per-name weight drift (max |w| 0.36 at ORDIUSDT, k=4304).** Not
   a warmup-edge artifact (k=4304 ≫ warmup=63); it's a genuine weekly-cadence
   property. Effective short weights can drift to ~3.6x target between weekly
   rebalances. Absorbed by the book (G3 passes at −33%); flagged for Critic
   awareness. A hysteresis / eligibility-exit buffer (REVIEW-002 S1) is the
   named complement path if this drift deepens OOS.
2. **Gross leverage max 1.94 / min_active 0.49.** Same intra-rebal drift
   mechanism at the book level: sum|w| can nearly double or halve between
   weekly rebalances before clamping. Mean 1.004 confirms no systematic drift.
3. **63-cadence min-per-year −0.16 (2023).** The slowest cadence (3-week) flips
   2023 slightly negative — the sparsest rebalancing under-fits the 2023 chop
   regime. 21 and 42 keep 2023 positive (+0.35 / +0.60). This is why the Sharpe
   curve is hump-shaped, not monotone.
4. **Leak@rebal=21 PASS with funding corruption included.** The cadence change
   moves decision points to every 21st candle; a cadence-dependent look-ahead
   would manifest at the new sparse points. None found — past weights/turnover/
   equity/funding_rets bit-identical under future corruption of signal+open+
   funding. Closes the QR's load-bearing ask.

---

## 8. Status

**OVERALL = READY-FOR-PHASE-7**

IS-only characterization complete. OOS sealed. Parity confirmed. Leak@rebal=21
passes. Cadence table delivered. Gate verdicts (G1–G6) and the selection-bias /
MERGE verdict are the QR's and Critic's calls respectively.
