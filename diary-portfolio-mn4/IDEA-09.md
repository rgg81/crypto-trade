# IDEA-09 — Diary (Calendar / Seasonality Tilt, DIRECTIONAL)

**Decision: NOT reveal-eligible (positive sense). NULL at the pre-registered gate. Banked for the holdout reveal as a NULL candidate.**
**Model: Opus 4.8** (Fable rate-limited this session; user-directed per charter). Disclosed per the charter's mandate.
**IS-only. Holdout SEALED. Zero holdout reads.** `mn3_split` guard fired with `reveal_token=None`.

---

## What worked

- **The pre-registration held.** I locked weekend as the PRIMARY effect (domain prior: most-cited crypto calendar anomaly) and a principle-anchored gate (G1 \|t\|≥2, G2 per-year sign ≥4/5, G4 contrast ≥2 bps, G3 2×-cost survival) **before** looking at any IS result. When the primary came back null, I did not switch to the secondary (TOM, t=+3.27) — that would be selection-by-peeking. The discipline held even though TOM looked tempting.
- **The leak battery is clean.** Crisis scalar corrupt-future past-identical/future-changed; calendar scalar deterministic; inert-default byte-identity; decision-lag [k−1]; placebo negative-control (shuffled-dow t=−1.48 < 2.0). All 15 unit tests pass. The engine integration is byte-honest.
- **The crisis overlay (C1 vol-spike + C2 200d-trend) materially reduced drawdown** — from −78% (no overlay) to −50% (with overlay). C2 (200d-SMA) catches the entire 2022 bear (BTC below 200d-SMA → flat); C1 (vol>80%) catches acute spikes. Both principle-anchored, not IS-fitted.
- **The measurement was rigorous.** Welch t-tests pooled across BTC+ETH, per-year sign-stability across 5 IS year-slices, full DOW ANOVA + per-bucket breakdown, TOM as a second candidate with its own per-year sign check. Three candidates measured, multiplicity disclosed.

## What failed

- **The weekend effect is statistically null on this IS.** Pooled BTC+ETH t = **−0.362** (p=0.72). BTC and ETH **disagree on sign** (BTC weekday > weekend; ETH weekend > weekday). Per-year sign flips in 2 of 5 years. Contrast −1.58 bps/8h is economically trivial. The most-cited crypto calendar anomaly does not exist in this data at a tradeable magnitude.
- **The turn-of-month effect (t=+3.27) is not per-year stable.** Strong pooled t, but sign flips in 2/5 IS years → fails the pre-registered G2 robustness floor. A calendar anomaly that doesn't reproduce across years is not a stable behavioral edge; it's regime coincidence.
- **DOW breakdown (ANOVA F=1.80, p=0.096)** does not clear 0.05, let alone Bonferroni-7.
- **CRITICAL — the calendar tilt actively destroys Sharpe.** Attribution:
  - Crisis-only (trend filter, NO calendar): Sharpe **+1.42**, maxDD −40%, turn 7.7×/yr.
  - ARM-A (calendar × crisis): Sharpe **+0.86**, maxDD −50%, turn 62.6×/yr.
  - **Calendar marginal contribution = −0.55 Sharpe**, plus 8× more turnover. The construction's entire IS positivity is a **trend-filter beta artifact** (idea 08's domain), not a calendar edge.

## Lessons (generalizable)

1. **Crypto calendar anomalies are not robust at the daily cadence.** The "weekend effect" lore appears to be either (a) an artifact of early-period data (2017–2019) that has since arbitrated away, (b) a 24/7-market illusion (no overnight gap → the equity weekend effect's mechanics don't transfer), or (c) real but far below the 2bps/candle floor needed to cover crisis-overlay occupancy. Crypto trades 24/7 with no session gaps; the equity weekend-effect mechanism (closed market → gap on open) structurally does not apply. This is a genuine crypto-native structural reason to doubt calendar effects ex ante, which the IS data confirms.
2. **Always run the attribution baseline.** Without the crisis-only baseline (Sharpe +1.42), I might have reported ARM-A Sharpe +0.86 as "the calendar tilt works." The attribution decomposition (calendar marginal = −0.55) is the honest finding. **A risk primitive that earns the Sharpe is NOT a signal edge.** This is the same lesson as MN3-G's "diagnostic-sleeve Sharpe ≠ executable book" — reified here as "overlay Sharpe ≠ signal Sharpe."
3. **Pre-registration discipline held under temptation.** TOM at t=+3.27 was a real temptation to switch. The Bonferroni-2 + per-year-sign-stability bar correctly rejected it (3/5 < 4). Without that bar, I would have shipped an IS-peeked TOM book that, given its per-year instability, would almost certainly fail the holdout. The multiplicity infrastructure earned its keep.
4. **Directional long/flat on BTC+ETH is fundamentally a beta book.** Even the clean trend-filter baseline (Sharpe +1.42, maxDD −40%) carries β_BTC ≈ +0.4 and draws down −40% in 2022-adjacent stress. This is idea 08's thesis (managed-variance), NOT idea 09's. The two ideas are structurally distinct; idea 09 cannot claim idea 08's beta Sharpe.

## Dead-paths catalog entry (for future MN cycles)

- **MN4-09 weekend calendar tilt (BTC+ETH, daily rebal):** NULL at gate (t=−0.36, sign 3/5). Calendar marginal Sharpe vs trend-filter baseline = **−0.55**. The trend-filter baseline (crisis-only, Sharpe +1.42, maxDD −40%) is NOT a calendar result — it belongs to the vol-targeted/managed-variance family (idea 08). Do NOT re-mine crypto calendar effects at ≤daily cadence without a NEW mechanism (e.g., a funding-settlement-cycle effect at the 8h funding cadence, which is a structurally different timescale and was not tested here).
- **MN4-09 turn-of-month (BTC+ETH, daily rebal):** pooled t=+3.27 but per-year sign 3/5 → **fails robustness floor**. Do not revive without a structural reason for year-to-year sign stability.

## Next-iteration ideas (if a calendar-research axis is ever re-opened)

1. **Funding-cycle calendar** (NOT a day-of-week calendar). Binance/OKX/Bybit funding settles every 8h at 00/08/16 UTC. A "funding-cycle effect" — systematic return pattern *within* the 8h funding window, or at settlement boundaries — is a structurally crypto-native calendar that has never been tested in this track. This is the right crypto-native calendar axis (matches the agent canon's "8h is special because funding-cycle alignment"), and it is distinct from the equity-transplanted weekend/TOM effects that failed here.
2. **BTC halving-cycle as a regime gate** (not a tilt). With 2 halvings now in the holdout window (2024-04 inside IS-boundary; the next structural event would be 2028), a "halving-adjacent regime" gate could modulate gross exposure. But this is a regime primitive, not a calendar tilt — and with N=1.5 events it cannot be subsample-validated. Park for now.
3. **Cross-sectional calendar** (relative day-of-week effects across the altcoin universe, not on the majors). The majors may be too efficient; alts with thinner liquidity may retain a day-of-week effect. This would be a market-NEUTRAL book (long the favorable-day alts, short the unfavorable-day alts) — structurally different from this directional tilt. Untested in MN4-09.

None of these is recommended for this tournament — the verdict on idea 09 is NULL, and that is the deliverable. They are listed for completeness per the diary template.

## Honest cost/turnover note

The charter suggested "ultra-low turnover (weekly/monthly rebal)." Daily rebal (rebal=3) is the minimum cadence that can resolve day-of-week, and it produces 62.6× annual one-way turnover — not "ultra-low." The trend-filter baseline turns over only 7.7×/yr (slow crisis overlay). So the "cost-immune by construction" claim was **only ever true for the trend filter, not for the calendar** — the calendar adds 8× turnover for negative edge. The honest characterization: the calendar mechanism cannot be made ultra-low-turnover at the cadence it requires, and it has no edge to pay for the cost. The cost wall didn't kill this idea (the trend filter survives it); the *signal wall* did.

## Final

**Banked-for-reveal: YES, as a NULL candidate.** The construction is frozen byte-exact; the gate is frozen; the pre-registered verdict is NULL. The tournament may reveal it on the 2-year holdout to confirm null generalization (expected) or to detect an OOS materialization (unlikely given IS sign-instability). Per the charter: a FAIL is the methodology working, not a disappointment.

**Test/ruff status:** `uv run pytest tests/test_mn4_idea09_calendar_tilt.py` → **15 passed**. `uv run ruff check analysis/portfolio/mn4_idea09_calendar_tilt.py tests/test_mn4_idea09_calendar_tilt.py` → **All checks passed.**
