# tradfi-cup-01 — Seeded mechanism-family menu

One family per team, registered BEFORE building, approved first-come-first-served
(`registry.jsonl` is the record). Off-menu proposals are welcome and encouraged — the menu
seeds diversity, it does not bound it. Each family below is a DISTINCT mechanism; two teams
may not register the same one.

**RESERVED — not registrable:** bear-gated TSMOM overlays on multi-horizon momentum (the
incumbent production book's family).

| # | Family | Mechanism sketch |
|---|---|---|
| 1 | Cross-sectional momentum (12-1 class) | Relative winners keep winning; skip the last month (reversal zone) |
| 2 | Short-horizon reversal | 1-5 day losers bounce; liquidity provision premium |
| 3 | Sector-relative mean reversion | Names snap back toward their sector basket after idiosyncratic gaps |
| 4 | Per-name time-series trend | Each name vs its own history (not cross-sectional); sign of k-month return |
| 5 | Low-vol / betting-against-beta | Low-vol names outperform risk-adjusted; short the lottery end |
| 6 | Volume & liquidity anomalies | Volume shocks, Amihud illiquidity premia, volume-price divergence |
| 7 | VIX-conditional regime books | Different cross-sectional books under calm vs stressed VIX states |
| 8 | Sector pairs / cointegration stat-arb | Long/short cointegrated pairs within sector on spread z-score |
| 9 | Residual (beta-stripped) momentum | Momentum on the market/sector-residual return component |
| 10 | Overnight-vs-intraday gap decomposition | Split close→open vs open→close returns; trade the persistent component |
| 11 | 52-week-high proximity / anchoring | Distance to trailing high as an underreaction anchor |
| 12 | Skewness / lottery (short MAX) | Short recent extreme-daily-return names; long the boring |
| 13 | (reserve) Intra-sector lead-lag | Large-cap moves propagate to smaller sector peers with a lag |

Registration line (the orchestrator runs it after approving):
```
uv run python analysis/portfolio/tradfi/tournament/cli.py register-family \
  --team team-NN --family-id tNN-<slug>-v1 --summary "<one-line mechanism>"
```
