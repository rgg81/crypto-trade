# team-07 — IS report — family `t07-vol-structure-v1`

Submission: **sustained vol-regime expansion cross-section** — long the top-40 names whose
short-horizon realized vol is persistently elevated vs their own long-horizon norm, short the
own-vol-compressed (attention-starved) tail. Spec frozen in `research_brief.md` §7;
implemented verbatim in `strategy.py` (QE); harness PASS 6/6; team tests 8 passed.

All numbers in §1–§2 are from **`out/is_metrics.json`** (team-run output, window 2020-01-01
→ 2024-07-01 exclusive, n_months = 54). Numbers in §4 marked *[scratch]* are evaluator-
computed in `out/scratch/` runs (ledger ids given) and are NOT team-run artifacts.

## 1. Headline (net, after taker + liquidity-scaled slippage + native funding)

| metric | @1× | @2×-stress |
|---|---|---|
| **net IS Sharpe (monthly, √12)** | **+1.0247** | **+0.8260** |
| max drawdown | −31.13% | −32.80% |
| total return | +312.1% | +197.5% |
| ann. turnover | 70.47 | 70.47 |
| median names long / short | 20 / 20 | 20 / 20 |
| mean gross / mean net | 0.9924 / ~0 (5e-16) | 0.9924 / ~0 |
| total funding P&L (raw sum) | +0.1169 | +0.1169 |
| total cost (raw sum) | 0.1988 | 0.3976 |

Notes: turnover ~70/yr is the lowest in the field per the orchestrator — the score-side EMA
(halflife 72 candles ≈ 24 days) was selected exactly to survive the 2×-stress tier, and the
1×→2× Sharpe degradation is correspondingly mild (−0.20). Breadth is maximal (20/20 vs the
≥5 floor). mean_net ≈ 0 at float precision: the book is cross-sectional by construction —
no directional or vol-timing channel (the engine owns portfolio vol-targeting).

## 2. Per-regime Sharpe (fixed pre-registered regime tags)

| regime | @1× | @2×-stress |
|---|---|---|
| bull | +1.4399 | +1.2677 |
| bear | +1.2029 | +0.9665 |
| chop | +0.2824 | +0.0875 |

**3/3 regime buckets positive at BOTH cost tiers.** Chop is the weak bucket and is disclosed
as such (see §5); the strategy is not a single-regime artifact.

## 3. The two-stage falsifier story — stated plainly

1. **The pre-registered hypothesis FIRED.** The brief pre-registered a low-vol lottery
   premium (long calm / short high-vol) with a plateau falsifier. e01/e02 (ledger-stamped
   before results were read): all 10 estimator×window configs NEGATIVE at 1× (best −0.140,
   worst −0.780), and the long-calm book *paid* ~0.17–0.26 cumulative funding instead of
   collecting it — inside the top-40, the persistent positive funding baseline sits on the
   low-vol MAJORS, not on the high-vol tail. The lottery-premium story is dead in this
   universe and is documented as such (brief §A1). *[scratch: e01, e02]*
2. **The stricter-bar dynamics branch cleared.** Because any sign/branch change after seeing
   data is data-informed, the surviving branches were pre-registered with a RAISED bar
   (3-window-neighborhood mean ≥ +0.35 @1×, 2× > 0, breadth ≥ 5/side, ≥2/3 regimes
   positive) before being run (brief §A1, ledger e03/e06). The vol-LEVEL branch failed it at
   either sign (best neighborhood +0.242; both §4 turnover overlays rejected by the
   pre-registered adoption rule — e04/e05). The vol-DYNAMICS branch — **long sustained
   vol-expansion / short compression** — cleared it decisively: selection neighborhood
   +0.992, every cell of the 4-pair × halflife robustness grid ≥ +0.73 @1× and ≥ +0.53
   @2×, an interior optimum (halflife rollover at ≈72 candles) found under a pre-committed
   grid-extension limit. *[scratch: e03–e11]*

## 4. Robustness detail (evaluator-computed, scratch provenance — not team-run artifacts)

- Parameter plateau: 2D grid (s,l) ∈ {12/84, 21/84, 21/126, 12/126} × hl ∈ {36,48}: 1×
  Sharpe range +0.731…+1.025; 2×-stress range +0.526…+0.826. *[scratch: e10, e11]*
- Halflife profile at 12/84: 0.899 (36) → 0.991 (48) → **1.025 (72)** → 0.961 (108) →
  0.931 (144) — interior optimum, not an endpoint. *[scratch: e08, e10, e11]*
- Sub-period halves @1×: 2020-01→2022-03 **+1.223**; 2022-04→2024-06 **+0.801**.
  *[scratch: e12]*
- **Last 12 IS months (2023-07→2024-07): +0.438** — disclosed as the closest analog to the
  sealed holdout's starting regime. Positive, but well below the full-IS headline; a
  12-month monthly-Sharpe estimate also carries a very large standard error. *[scratch: e12]*
- Estimator robustness: Parkinson-ratio variant at identical parameters +0.927 @1× /
  +0.771 @2× — the mechanism is not an artifact of the close-close estimator.
  *[scratch: e12]*
- Funding share: **11.7%** of pre-cost P&L (pre-cost cross-sectional spread +1.001, funding
  +0.117) — the edge is price alpha, not funding carry; consistent with the team-run raw
  sums in §1. *[scratch: e12; §1 raw sums from is_metrics.json]*
- Sign structure: long-compression mirrors are strongly negative everywhere (monotone across
  all pairs) — the sign is structural, not fitted noise. *[scratch: e06]*

## 5. Honest expectations for the sealed holdout

The IS trend is decay-shaped: +1.22 (first half) → +0.80 (second half) → +0.44 (last 12
months). The mechanism (attention/flow persistence at multi-week halflife) should survive,
but the honest central expectation for the 24-month holdout is the **recent run-rate, not
the headline: roughly +0.3 to +0.7 net Sharpe @1×**. With only 24 monthly points, the
1-SE noise band on a Sharpe estimate is roughly ±0.7: outcomes anywhere from ≈ −0.3 to
≈ +1.3 would NOT be surprising; a result below ≈ −0.5 would indicate genuine mechanism
decay (crowding-out of the expansion premium, or a chop-dominated holdout — chop is our
weakest bucket at +0.28/+0.09) rather than sampling noise. The strategy's structural
protections for an adverse holdout: lowest-in-field turnover (cost resilience, mild 2×
degradation), maximal breadth (20/20), zero net tilt, and NaN-tolerant column-agnostic
construction for the new listings the holdout universe will contain.

## 6. Artifacts

- Headline source: `out/is_metrics.json` (+ `out/net_is.csv`); harness: `out/harness.json`.
- Ledger: `experiments.jsonl` — 12 evaluator-stamped entries (e01–e12), all logged before
  results were read; 28 of 40 budget unused.
- Scratch scripts backing §4: `out/scratch/` (excluded from the frozen bundle).
- Spec: `research_brief.md` §7 (frozen); provenance: `provenance.md`.
