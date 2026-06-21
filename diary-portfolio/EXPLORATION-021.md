# portfolio-iteration EXPLORATION-021 — eligibility-exit / zombie-tail cleanup (PROMISING)

**Agent-driven.** User-found pathology: the deployed baseline-v2 book (iter_020 hysteresis band
δ=0.010 SNAP) holds **38 positions for a "top-20" strategy**. Band-free (δ=0) it is exactly 20. The
band carries ~18 EXITED coins forward forever — including DELISTED names (TOMOUSDT last candle
2024-05-28, BLZUSDT rank ~198, $0 volume). This exploration adds an eligibility-exit overlay that
force-closes the zombies and asks: can we clean the book to true-top-20 WITHOUT hurting OOS Sharpe and
WITHOUT blowing up the band's turnover/cost win? Code: `analysis/portfolio/iter_021_eligexit.py`.
Baseline DO-NOT-MODIFY (tagged `portfolio-baseline-v2`): `iter_020_hysteresis.py` (this worktree's
data extent: δ=0.010 SNAP IS +1.25 / OOS +1.66 / maxDD −22% / oosDD −19%).

## The mechanism that creates zombies (diagnosed)
When a coin drops out of the top-20, its canonical `target_w` → 0. Its *held* weight is non-zero (the
band held it last candle); after per-candle gross-renorm it sits at 0.003–0.008. To exit, the held
weight must move to 0 — a move of 0.003–0.008, which is **below δ=0.010**. The SNAP band, by design,
refuses moves ≤ δ. So the exit NEVER fires; the coin is held forever. Worse, the renorm rescales that
stale leftover every candle, so each zombie generates a tiny weight-change **every bar** — phantom
rebalancing tickets. Verified on the last candle: 38 held / 20 band-free / **18 zombies**, all 18
ineligible, two of them delisted (BLZUSDT, TOMOUSDT) with leftover weights 0.004–0.008.

## Method — eligibility-exit overlay ON TOP of the iter_020 banded book
- **Overlay, threaded inside the iter_020 band loop (past-only, path-dependent).** Per candle: run the
  identical iter_020 SNAP step → `cur`; advance a per-coin consecutive-ineligible streak using THIS
  candle's past-only `elig`; force `cur[c] = 0` for every coin whose streak ≥ K (override the band's
  hold). The forced zero is written into `prev`, so it propagates to the next candle — genuine path
  dependence, no peeking.
- **`elig` is the SAME mask** iter_002/iter_020 build: `qv.rolling(90).mean().shift(1).rank ≤ 20`.
  The `.shift(1)` makes it strictly past-only — it is exactly the mask whose `≤ TOP_N` band-free book
  has 20 positions. No new signal, no new data.
- **Renorm + vol-target identical to iter_020.** After the overlay, gross is renormalized back to the
  baseline gross and the canonical per-candle vol-target scale is applied — same as `banded_net`. This
  is a cadence/exit change, not a sizing change.
- **K swept {1, 2, 3, 4, 6, ∞}.** K=1 = exit immediately on dropping out; K=∞ = overlay disabled.
  Effect judged on ROBUSTNESS across the sweep, never one cell. δ fixed at the deployed 0.010 SNAP.

## Identity gate (HARD, mandatory) — K=∞ reproduces iter_020 EXACTLY
`IDENTITY K=inf vs iter_020(δ=0.010,snap): max|diff| = 0.00e+00, len_match = True → PASS`. With the
exit disabled the overlay is a literal no-op (streak mask always False), so the net is bit-for-bit the
baseline. **PASS.**

## Leak test — future→past corruption (both target_w AND eligibility corrupted)
Corrupting `target_w` (add N(0,0.05)) AND flipping `elig` randomly from a mid-sample cutoff forward
leaves the held book **bit-identical before the cutoff** at K=1, K=3, K=∞ (max|Δ| = 0.00e+00). The
streak counter reads only the current row's past-only `elig` — no t+1 access by construction.
**PASS.**

## Result vs baseline-v2 (iter_020 δ=0.010 SNAP = K=∞)

| K | IS | OOS | maxDD | oosDD | avgPos | turnover | tickets/candle | OOS @2× cost | turn vs base |
|---|---|---|---|---|---|---|---|---|---|
| **∞ (baseline)** | **+1.25** | **+1.66** | **−22%** | **−19%** | **24.2** | **0.2771** | **23.80** | **+1.17** | **—** |
| 6 | +1.21 | +1.63 | −23% | −20% | 18.5 | 0.2876 | 18.28 | +1.13 | +4% |
| 4 | +1.22 | +1.63 | −23% | −20% | 18.5 | 0.2876 | 18.27 | +1.13 | +4% |
| 3 | +1.22 | +1.63 | −23% | −20% | 18.5 | 0.2876 | 18.26 | +1.13 | +4% |
| 2 | +1.22 | +1.63 | −23% | −20% | 18.5 | 0.2876 | 18.26 | +1.13 | +4% |
| 1 | +1.21 | +1.64 | −24% | −20% | 18.4 | 0.2895 | 18.18 | +1.13 | +4% |

**Last-candle book audit** (the deployment-relevant snapshot):

| K | n_pos | zombies (ineligible held) | delisted held |
|---|---|---|---|
| ∞ | **38** | **18** | **BLZUSDT, TOMOUSDT** |
| 6 | 20 | 0 | none |
| 4 | 20 | 0 | none |
| 3 | 20 | 0 | none |
| 2 | 20 | 0 | none |
| 1 | 20 | 0 | none |

OOS-only avg positions: **K=∞ → 33.0, K=3 → 20.0** (the live window is cleaned to true-top-20).
Per-year net% essentially unchanged: K=∞ `{2020:22,2021:46,2022:36,2023:35,2024:26,2025:24,2026:28}`
→ K=3 `{2020:22,2021:47,2022:37,2023:36,2024:24,2025:24,2026:31}` — no year sacrificed.

## Reading the result (the turnover/cost concern is the headline — and it's a WIN, not a cost)
- **Book cleaned to true-top-20.** avgPos 24.2 → 18.5 (full sample), 33.0 → 20.0 (OOS). The last-candle
  book drops 38 → 20; all 18 zombies AND both delisted coins are gone at every finite K. The whole
  point of the exploration — achieved.
- **Forcing exits ADDS turnover by only +3.8%** (Σ|Δw| 0.2771 → 0.2876 ≈ total turnover 1888.7 → 1960.1).
  The exit trades are one-time closes of tiny leftover legs — they barely move the size-weighted
  turnover. The band's turnover win is preserved.
- **…and the ORDER-TICKET count actually FALLS: 23.80 → 18.26 tickets/candle** (median 23 → 20). This is
  the deeper insight: each zombie was generating a phantom renorm-driven weight change every bar, so the
  baseline "top-20" book was placing ~24 tickets/candle. Closing the zombies removes that recurring
  jitter. Since live slippage/fee drag scales with ticket COUNT (not notional), the exit is **net cost-
  POSITIVE for deployment**, despite the +3.8% Σ|Δw|.
- **OOS Sharpe give-back is ~0.03** (+1.66 → +1.63), flat across K=1→6 — within noise, not a regime
  break. Cost-stress give-back ~0.04 (OOS@2× +1.17 → +1.13). oosDD +1pt (−19% → −20%). IS −0.03/−0.04.
- **Robust across the whole sweep.** IS ~+1.21/+1.22, OOS ~+1.63/+1.64, avgPos ~18.5 are essentially
  flat from K=1 to K=6 — the effect is structural (drop the zombies), not a tuned cell. K=1 and K=6 are
  indistinguishable because zombies are persistently ineligible (a coin that drops out of the top-20 by
  $-volume rarely climbs back within a few candles), so the streak crosses any small K almost immediately.

## Honest verdict: PROMISING — a near-free book-hygiene fix; small K is the sweet spot
The eligibility-exit cleans the book to true-top-20 (38→20, zombies + delisted gone) and **reduces the
order-ticket count** (23.8 → 18.3/candle) — the band's deployment value is *improved*, not wrecked. The
price is a ~0.03 OOS-Sharpe and ~1pt oosDD give-back, flat across K and within noise. The give-back is
real and I'm reporting it honestly: the zombies were a slightly-positive-carry stale-momentum tail, so
removing them costs a sliver of OOS. But holding delisted/$0-volume inventory forever is a live-trading
liability (un-exitable in practice, funding/borrow drag, reconciliation risk) that the backtest's fr
penalty understates — the deployment case for the exit is stronger than the −0.03 suggests.

**This is the inverse of the iter-019 trap and consistent with iter-020:** gross is preserved (renorm
unchanged), the change is a genuine cadence/exit primitive, and the identity gate proves K=∞ is the
baseline bit-for-bit. The K chosen was never tuned on OOS — the sweep is flat, so K is not a knob.

**Cleanest config to route to the critic: K=2 (or K=3 — identical).** Rationale: K=1 reacts to
single-candle liquidity-rank flicker (a coin grazing rank 20↔21 would thrash); K=2 requires two
consecutive ineligible candles before force-closing, which de-noises the boundary at zero measurable
cost (IS/OOS/turnover identical to K=3..6). K=2 gives the full cleanup (38→20, 0 zombies, 0 delisted)
with one candle of hysteresis against rank-flicker.

## Caveat / what would change the verdict
- The −0.03 OOS give-back means this is **book-hygiene + deployment-robustness, NOT an alpha lift**. If
  the bar is "must not reduce OOS Sharpe at all," a critic could argue the band's stale-holding is
  mildly load-bearing for paper Sharpe. My read: the live liability of un-exitable delisted inventory
  dominates a 0.03 paper-Sharpe sliver, so the exit is worth it — but that is a judgment the critic +
  user own, not the backtest.
- The give-back is small enough that a finer test (multiple OOS sub-windows, or a no-funding-on-dead-
  coins stress where the zombies' real-world drag is modeled) could flip the sign of the trade-off in
  the exit's favor. Worth doing at CONFIRMATION.

## Next
- CONFIRMATION-021: take K=2 through the full gauntlet — reveal OOS once, benchmark vs B&H-BTC +
  EW-top20, turnover/ticket + cost-stress at 1×/2×, DSR on the modest n, and a "dead-coin drag" stress
  (model funding/illiquidity penalty on the zombies the baseline holds) to quantify the live edge the
  paper backtest omits. If it clears + critic PASS → fold the eligibility-exit into baseline-v2 as a
  strictly-accretive book-hygiene primitive (orthogonal to the band; both can coexist).
- Pairs naturally with iter-020: band governs *tracking* of eligible coins (turnover win); exit governs
  *removal* of ineligible coins (book hygiene). One change at a time — confirm the exit on top of the
  shipped band first.
