# crypto-cup-01 — Mechanism-Family Menu

Each team registers EXACTLY ONE mechanism family before building (CHARTER §6). First-come-
first-served on overlap; vetoed teams redraw. Off-menu families are welcome — register them
the same way. **No families are reserved**: diversity is enforced between teams only.

A "family" is an economic MECHANISM, not a parameterization. Two teams both doing "momentum
with different lookbacks" are the SAME family; momentum-of-price vs momentum-of-OI are
different families.

Seeded menu (~14, deliberately crypto-native — the aux panels exist for a reason):

1. **funding-carry cross-section** — harvest the funding-rate premium: short the coins the
   crowd pays to be long, long the ones shorts pay for. Level- or percentile-based.
2. **OI-crowding fade** — open-interest build-ups against price stagnation mark crowded
   trades; fade them / position for the unwind (aux `oi`, `oi_value`).
3. **taker-flow imbalance** — cross-sectional aggressive-buyer pressure from
   `taker_buy_volume / volume`; flow leads or fades price depending on horizon.
4. **liquidation / short-squeeze reversal** — wipeout candles (extreme range + OI collapse)
   overshoot; trade the snap-back.
5. **long/short-ratio contrarian** — fade extreme retail/top-trader positioning
   (aux `ls_accounts`, `tt_ls_accounts`, `tt_ls_positions`, `taker_ls_vol`).
6. **volatility structure** — vol-risk-premium / vol-regime cross-section: rank by realized
   vol dynamics (compression/expansion), long the profile that pays.
7. **breakout / channel** — per-name range breakouts, N-candle-high anchoring, congestion
   escapes; crypto's reflexive trend-ignition mechanism.
8. **short-horizon reversal** — 1-3 day overreaction fade within the top-40 cross-section.
9. **BTC-beta-residual momentum** — momentum on the component orthogonal to BTC/market beta;
   alt-specific persistence without the market factor.
10. **time-series trend** — per-name multi-horizon trend following (sign or magnitude).
11. **dispersion / correlation regime** — trade the cross-section differently when pairwise
    correlation is high (macro regime) vs low (idiosyncratic regime).
12. **liquidity / size premium** — systematic tilts between the liquid mega-caps and the
    thinner tail of the top-40, conditioned on regime.
13. **seasonality** — time-of-day / day-of-week / weekend structural effects in perp returns.
14. **volume–price divergence** — Amihud-style illiquidity or volume-confirmation signals;
    price moves without volume mean-revert, confirmed moves persist.

Registration line format (the QR writes this, the orchestrator approves/vetoes via
`cli.py register-family`):

```json
{"team_id": "team-NN", "family_id": "tNN-<slug>-v1", "summary": "<one-line mechanism>"}
```
