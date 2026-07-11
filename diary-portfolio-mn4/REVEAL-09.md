# REVEAL-09 — Calendar/Seasonality Tilt — Holdout Scorecard

**Token MN4-09 spent.** Authorized by the orchestrator (REVEAL-INSTRUCTIONS-MN4.md) + the user's Phase-B mandate ("reveal all strategies"). This was the SINGLE authorized holdout read for idea 09; the 2-year window `[2024-07-01, 2026-07-01)` is now spent. **Model: Opus 4.8** (Fable suspended; user-directed per charter).

**Construction (frozen byte-exact from Phase A):** `ew_long{BTC,ETH}`, `rebal=3` (daily), `gross=1.0`, weekend calendar scalar (direction=−1, long-weekday per IS sign) × crisis scalar (C1 vol>0.80ann OR C2 BTC<200d-SMA → flat), `CostModel(5, 2.5, funding=True)` + 2×-GT twin. Scalars built on the full panel (IS warmup faithful to a live deployment); holdout window sliced out for scoring. **No IS candle scored. No Stage-3 candle read** (30 Stage-3 candles present, untouched; boundary assert verified).

---

## VERDICT: **FAIL** (PRIMARY gate G1 & G2 & G4 all fail; G3 cost-survival also fails). Idea-09 is **CLOSED**.

The IS-null **generalized**: the weekend effect remains statistically null on the holdout, and the construction lost money. The pre-registered gate worked exactly as designed — it correctly refused to certify a non-edge, and the holdout confirms that refusal.

---

## Holdout headline

| Variant | Sharpe | maxDD | ann | vol | turn/yr |
|---|---|---|---|---|---|
| **ARM-A 1×** | **−0.328** | **−38.38%** | **−16.05%** | 34.1% | 63.1× |
| ARM-A 2×-GT | **−0.466** | −39.21% | −19.91% | — | — |
| Crisis-only (trend filter, NO calendar) 1× | +0.114 | — | — | — | — |

- **Calendar marginal contribution (holdout) = −0.328 − +0.114 = −0.442.** Identical sign and near-identical magnitude to IS (IS: −0.553). **The calendar reliably destroys value** — this is the single most robust finding of the reveal: not noise, but a repeatable negative.
- Crisis-only trend-filter baseline decayed from IS Sharpe +1.42 → holdout +0.11 (marginally positive). The trend filter's strong IS was partly regime luck; it barely survived the holdout.
- Cost coverage: turnover 63.1×/yr, drag @1× ≈ 473 bps/yr. The 2×/1× Sharpe "ratio" of 1.42 is **both negative divided** — meaningless; G3 correctly fails because Sharpe(1×) ≤ 0.

## Per-half path (net)

| Half | n | net | Sharpe | mean (bps) |
|---|---|---|---|---|
| 2024-H2 | 552 | **−5.92%** | −0.17 | −0.54 |
| 2025-H1 | 543 | **−12.79%** | −0.37 | −1.55 |
| 2025-H2 | 552 | **−13.19%** | −0.60 | −1.97 |
| 2026-H1 | 543 | **0.00%** | NaN | 0.00 |

The book lost money in every half it was active. **2026-H1 is exactly flat** — the crisis scalar (vol>0.80 OR BTC<200d-SMA) was flat for the entire half (BTC spent 2026-H1 below its 200d-SMA and/or in acute-vol regimes), so the calendar had zero opportunity. The crisis overlay's de-risking worked as designed, but it also confirms the calendar adds nothing when it matters most.

## Regime buckets (holdout)

| Bucket | n | mean (bps) | β_BTC |
|---|---|---|---|
| CRASH | 270 | −6.93 | **+0.16** (de-risked by crisis overlay) |
| CHOP | 1811 | −1.92 | +0.47 |
| MANIA | 109 | +28.55 | +0.81 |

The book lost in CHOP (the dominant regime) and CRASH; it made money only in brief MANIA windows (n=109 of 2190). Pooled β_BTC = **+0.43**, rolling-270 median **+0.48** (p10 0.00, p90 +1.05) — material directional beta, not crisis-robust (the charter's "winner in EVERY market condition" mandate is not met; the book is a beta rider that draws down with the trend).

## The weekend effect on holdout (the key falsification check)

| Symbol | n_we | n_wd | mean_we (bps) | mean_wd (bps) | contrast (bps) | t | p |
|---|---|---|---|---|---|---|---|
| BTCUSDT | 624 | 1566 | −0.60 | +1.12 | −1.72 | −0.32 | 0.75 |
| ETHUSDT | 624 | 1566 | −0.08 | −2.12 | +2.04 | +0.24 | 0.81 |
| **POOLED** | 1248 | 3132 | −0.34 | −0.50 | **+0.16** | **+0.033** | **0.974** |

**The IS-null generalized, and then some.** Pooled holdout contrast = **+0.16 bps** (vs IS −1.58 bps); pooled t = **+0.033** (vs IS −0.362). The sign even flipped — both numbers are effectively zero. BTC and ETH **still disagree on sign** (BTC −1.72, ETH +2.04), exactly as in IS (BTC −4.47, ETH +1.31). This is the signature of pure noise, not a behavioral edge.

Per-half sign stability (holdout analog of IS per-year): the weekend-weekday contrast flipped sign across 3 of 4 holdout halves (2024-H2 −6.64, 2025-H1 −16.75, 2025-H2 +26.07, 2026-H1 −1.99 bps). **1/4 consistent** — far below the IS gate's 4/5 requirement and its holdout proportional analog (≥3/4).

## Gate-by-gate verdict (holdout value vs FROZEN threshold)

| Gate | Threshold | Holdout value | PASS/FAIL |
|---|---|---|---|
| **G1** Welch \|t\| weekend-vs-weekday pooled | ≥ 2.0 | **+0.033** | **FAIL** |
| **G2** per-half sign stability | ≥ 3/4 (holdout analog of IS 4/5) | **1/4** | **FAIL** |
| **G3** cost-survival (Sharpe1×>0 AND 2×/1×≥0.60) | — | Sharpe1× = **−0.328** | **FAIL** |
| **G4** \|contrast\| economic-relevance floor | ≥ 2.0 bps | **0.16 bps** | **FAIL** |
| **PRIMARY** (G1 & G2 & G4) | — | — | **FAIL** |

All four gates fail. The construction is **closed** — no rescue, no second reveal.

---

## HONEST generalization read (one paragraph, no spin)

The IS-null **generalized exactly as expected**, and the construction actually performed *worse* on the unseen holdout (Sharpe +0.86 → −0.33; the calendar marginal contribution stayed reliably negative at −0.44 vs IS −0.55). The weekend-effect t-stat moved from −0.36 (IS) to +0.03 (holdout) — both indistinguishable from zero, with a sign flip that confirms pure noise; BTC and ETH continue to disagree on sign in both windows. The most robust finding of the entire exercise is that the **calendar tilt reliably destroys value** (negative marginal Sharpe in both IS and holdout) while the *trend-filter* baseline carries all the positivity — and even that baseline decayed materially (IS +1.42 → holdout +0.11). No crash-robustness was ever claimed for this directional book (β_BTC pooled +0.43, CRASH-bucket β +0.16 only because the crisis overlay flattened exposure), and the holdout confirms it: the book lost in CHOP and CRASH, made money only in brief MANIA windows, and drew down −38%. This is a textbook null generalization — the pre-registered gate correctly refused to certify a non-edge, the holdout confirms the refusal, and the idea is closed. **A FAIL on unseen data is the methodology working, not a disappointment.**

---

## Files (namespaced, no git commit, no ledger edit)

- `analysis/portfolio/mn4_idea09_reveal.py` — the reveal script (frozen construction re-run on full panel, holdout sliced).
- `data/mn4_idea09/holdout_scorecard.json` — full holdout scorecard.
- `data/mn4_reveal/spend_MN4-09.json` — spend marker (`result: FAIL`, `holdout_sharpe_2x: −0.466`, `holdout_maxdd: −0.384`).
- `diary-portfolio-mn4/REVEAL-09.md` — this file.

**REVEAL-LEDGER.md not edited** (per instructions — orchestrator consolidates markers). **No git commit.** One look; honest numbers; the verdict stands.
