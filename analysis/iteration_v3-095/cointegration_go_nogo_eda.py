"""iter-v3/095 Phase-1 GO/NO-GO EDA — crypto cointegration / relative-value stat-arb.

The user has chosen the iter-v3/095 direction: cointegration pairs trading — a
genuinely different STRATEGY CLASS from everything v3 has tried (per-symbol
directional triple-barrier, cross-sectional ranking, regime overlays all extract
edge from FORECASTING DIRECTION; cointegration extracts edge from the
market-neutral MEAN-REVERSION of a stationary spread between cointegrated
symbols).

This is a hard FAIL-FAST GO/NO-GO checkpoint (memory `feedback_fail_fast.md`).
The known risk with crypto cointegration is INSTABILITY: pairs cointegrated in
one window decohere in the next (the cycle-4 prep memo Candidate-B caveat —
"altcoin-universe instability + turnover drag"). This EDA tests EXACTLY that
BEFORE any expensive build or backtest.

DECISIVE QUESTIONS
  1. Cointegration PREVALENCE + PERSISTENCE — over a candidate universe, run the
     cointegration test per walk-forward formation window. Do pairs cointegrated
     in window N stay cointegrated and tradeable in window N+1? Is cointegration
     PERSISTENT enough for a walk-forward strategy, or does it decohere too fast?
  2. Spread TRADEABILITY + COST viability — for the persistent pairs, does the
     spread z-score mean-revert with enough amplitude/frequency to beat
     turnover-based costs? A market-neutral pairs book trades TWO legs.

NO CHEATING
  - IS-ONLY. Every measurement restricted to open_time < OOS_CUTOFF_MS
    (2025-03-24). OOS is first seen in Phase 7. OOS_CUTOFF_DATE and
    training_months=24 are IMMUTABLE.
  - WALK-FORWARD-FAITHFUL (memory `feedback_v3_eda_walkforward_faithful.md`):
    the EDA replicates the v3 walk-forward — a 24-MONTH formation window, a
    1-MONTH trading window, stepping monthly. Cointegration is tested on the
    formation window ONLY; tradeability is measured on the SUBSEQUENT 1-month
    trading window — i.e. genuinely out-of-formation, the way a walk-forward
    pairs strategy would actually select and trade.

UNIVERSE
  The 22-symbol cross-sectional XS_UNIVERSE (non-v1/v2 liquid Binance-USDT
  perps; the V3_EXCLUDED_SYMBOLS check is satisfied by construction — XS_UNIVERSE
  was built to exclude every v1/v2 symbol). Cointegration needs breadth — the
  3-symbol BCH/LDO/TRX V3_MODELS set yields only 3 pairs and is far too thin.
  22 symbols → C(22,2) = 231 candidate pairs.

OUTPUT
  T1 — cointegration prevalence per formation window (CSV).
  T2 — pair-level persistence: cointegrated in window N -> still cointegrated
       in N+1? (CSV) — THE DECISIVE PERSISTENCE TABLE.
  T3 — spread half-life distribution + stability across windows (CSV).
  T4 — out-of-formation tradeability: z-score round-trips + net-of-cost PnL on
       the trading window for the persistent pairs (CSV).
  Console — the GO/NO-GO verdict with the decisive numbers.
"""

from __future__ import annotations

import itertools
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller, coint

# ----------------------------------------------------------------------------
# Constants — IMMUTABLE sacred constants imported by value (no src/ import here;
# this is a QR analysis script, not production code).
# ----------------------------------------------------------------------------
OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 00:00:00 UTC — config.OOS_CUTOFF_MS
TRAINING_MONTHS = 24  # config training_months — the walk-forward formation window
INTERVAL_MS = 8 * 60 * 60 * 1000  # 8h candle
BARS_PER_MONTH = 30 * 3  # ~90 8h bars per 30-day month
DATA_DIR = Path("data")
OUT_DIR = Path("analysis/iteration_v3-095")

# The 22-symbol cross-sectional XS_UNIVERSE (cross_sectional.py:61-84). Verified
# to exclude every v1/v2 symbol (V3_EXCLUDED_SYMBOLS) by construction.
XS_UNIVERSE = (
    "ADAUSDT", "AVAXUSDT", "FILUSDT", "FTMUSDT", "BCHUSDT", "GALAUSDT",
    "EOSUSDT", "CRVUSDT", "AAVEUSDT", "SANDUSDT", "ATOMUSDT", "LDOUSDT",
    "AXSUSDT", "TRXUSDT", "RUNEUSDT", "MANAUSDT", "ICPUSDT", "ALGOUSDT",
    "GRTUSDT", "THETAUSDT", "VETUSDT", "HBARUSDT",
)

# v1/v2 symbols — the V3_EXCLUDED_SYMBOLS guard (must be empty intersection).
V3_EXCLUDED_SYMBOLS = (
    "BTCUSDT", "ETHUSDT", "LINKUSDT", "LTCUSDT", "DOTUSDT", "BNBUSDT",
    "SOLUSDT", "XRPUSDT", "DOGEUSDT", "NEARUSDT", "MKRUSDT",
)

# --- EDA parameters (pre-registered) -----------------------------------------
COINT_PVALUE = 0.05  # Engle-Granger p-value threshold for "cointegrated"
ZSCORE_LOOKBACK = 45  # spread z-score rolling window (bars) — ~15 days at 8h
Z_ENTRY = 2.0  # |z| >= 2.0 to open the pair
Z_EXIT = 0.5  # |z| <= 0.5 to close the pair
# Round-trip cost for a market-neutral pair: 4 leg-fills (open long+short,
# close long+short). Binance futures taker = 0.05%/leg; pair round-trip cost
# ~= 4 x 0.05% = 0.20% of one leg's notional. Conservative for an 8h book.
COST_PER_ROUNDTRIP = 0.0020
MIN_FORMATION_BARS = int(TRAINING_MONTHS * BARS_PER_MONTH * 0.80)  # >=80% coverage


def load_log_prices() -> pd.DataFrame:
    """Load IS-only 8h close prices for XS_UNIVERSE, return log-price panel.

    Strictly IS-only: every row has open_time < OOS_CUTOFF_MS. Returns a panel
    indexed by open_time (epoch ms), one column per symbol, NaN where missing.
    """
    # Universe-purity guard — XS_UNIVERSE must not contain a v1/v2 symbol.
    contaminated = set(XS_UNIVERSE) & set(V3_EXCLUDED_SYMBOLS)
    assert not contaminated, f"V3_EXCLUDED_SYMBOLS leak: {contaminated}"

    series: dict[str, pd.Series] = {}
    for sym in XS_UNIVERSE:
        path = DATA_DIR / sym / "8h.csv"
        if not path.exists():
            print(f"  WARN: {sym} has no 8h.csv — dropped")
            continue
        df = pd.read_csv(path, usecols=["open_time", "close", "quote_volume"])
        df = df[df["open_time"] < OOS_CUTOFF_MS]  # IS-ONLY HARD FILTER
        if df.empty:
            continue
        df = df.set_index("open_time").sort_index()
        # log-price; quote_volume retained for the liquidity screen
        series[sym] = pd.Series(np.log(df["close"].astype(float)), name=sym)
        series[f"{sym}__qv"] = pd.Series(df["quote_volume"].astype(float))

    price_cols = {k: v for k, v in series.items() if not k.endswith("__qv")}
    panel = pd.DataFrame(price_cols).sort_index()
    qv_cols = {k[:-4]: v for k, v in series.items() if k.endswith("__qv")}
    qv = pd.DataFrame(qv_cols).sort_index()
    return panel, qv


def make_formation_windows(panel: pd.DataFrame) -> list[dict]:
    """Build the walk-forward windows the v3 backtest would use.

    Each window: a 24-month FORMATION span (cointegration tested here) followed
    by a 1-month TRADING span (tradeability measured here, out-of-formation).
    Steps monthly. All within the IS span (open_time < OOS_CUTOFF_MS).
    """
    times = panel.index.to_numpy()
    t0, t1 = int(times.min()), int(times.max())
    # Month boundaries as epoch-ms steps of ~30 days (8h-bar-aligned approximation
    # — the production runner uses calendar months; this monthly cadence is
    # faithful enough for a prevalence/persistence GO/NO-GO).
    month_ms = BARS_PER_MONTH * INTERVAL_MS
    formation_ms = TRAINING_MONTHS * month_ms

    windows = []
    cursor = t0 + formation_ms
    while cursor + month_ms <= t1:
        form_lo, form_hi = cursor - formation_ms, cursor
        trade_lo, trade_hi = cursor, cursor + month_ms
        windows.append(
            dict(
                idx=len(windows),
                form_lo=form_lo, form_hi=form_hi,
                trade_lo=trade_lo, trade_hi=trade_hi,
            )
        )
        cursor += month_ms
    return windows


def eligible_symbols(panel: pd.DataFrame, qv: pd.DataFrame, lo: int, hi: int) -> list[str]:
    """Symbols with enough history + liquidity in [lo, hi) to be a coint candidate."""
    seg = panel[(panel.index >= lo) & (panel.index < hi)]
    qseg = qv[(qv.index >= lo) & (qv.index < hi)]
    out = []
    for sym in panel.columns:
        col = seg[sym].dropna()
        if len(col) < MIN_FORMATION_BARS:
            continue
        # Liquidity screen: median 8h quote-volume >= $2M (a market-neutral pair
        # trades two legs; thin legs make the cost model fictional).
        qmed = qseg[sym].dropna().median() if sym in qseg else 0.0
        if not np.isfinite(qmed) or qmed < 2_000_000:
            continue
        out.append(sym)
    return out


def engle_granger(y: pd.Series, x: pd.Series) -> tuple[float, float, float]:
    """Engle-Granger 2-step. Returns (coint p-value, hedge ratio beta, half-life).

    half-life from an AR(1) fit on the spread: spread_t = a + rho*spread_{t-1};
    HL = -ln(2)/ln(rho) bars. NaN if rho out of (0,1) (non-mean-reverting).
    """
    aligned = pd.concat([y, x], axis=1).dropna()
    if len(aligned) < 60:
        return np.nan, np.nan, np.nan
    yv, xv = aligned.iloc[:, 0].to_numpy(), aligned.iloc[:, 1].to_numpy()
    # Engle-Granger coint test (statsmodels) — its internal regression gives the
    # OLS residual; we recompute beta explicitly for the spread/half-life.
    try:
        _, pval, _ = coint(yv, xv)
    except Exception:
        return np.nan, np.nan, np.nan
    # hedge ratio via OLS with intercept
    X = np.column_stack([np.ones_like(xv), xv])
    beta_full, *_ = np.linalg.lstsq(X, yv, rcond=None)
    beta = beta_full[1]
    spread = yv - (beta_full[0] + beta * xv)
    # AR(1) on the spread for half-life
    s_lag, s_now = spread[:-1], spread[1:]
    Xs = np.column_stack([np.ones_like(s_lag), s_lag])
    ar, *_ = np.linalg.lstsq(Xs, s_now, rcond=None)
    rho = ar[1]
    if 0.0 < rho < 1.0:
        half_life = -np.log(2.0) / np.log(rho)
    else:
        half_life = np.nan
    return pval, beta, half_life


def simulate_pair_tradeability(
    panel: pd.DataFrame, sym_y: str, sym_x: str, beta: float,
    form_lo: int, form_hi: int, trade_lo: int, trade_hi: int,
) -> dict:
    """Simulate the z-score pairs signal on the OUT-OF-FORMATION trading window.

    The spread mean/std are estimated on the FORMATION window (no look-ahead);
    the z-score and the entry/exit signal are evaluated on the TRADING window.
    Cost is charged per round-trip. Returns trade count + net-of-cost PnL.
    """
    form = panel[(panel.index >= form_lo) & (panel.index < form_hi)]
    trade = panel[(panel.index >= trade_lo) & (panel.index < trade_hi)]
    f = pd.concat([form[sym_y], form[sym_x]], axis=1).dropna()
    t = pd.concat([trade[sym_y], trade[sym_x]], axis=1).dropna()
    if len(f) < 60 or len(t) < 10:
        return dict(n_trades=0, gross=0.0, net=0.0, ok=False)

    # FORMATION-window spread stats — the only thing carried forward.
    fy, fx = f.iloc[:, 0].to_numpy(), f.iloc[:, 1].to_numpy()
    f_intercept = np.mean(fy - beta * fx)
    f_spread = fy - (f_intercept + beta * fx)
    mu, sd = float(np.mean(f_spread)), float(np.std(f_spread))
    if sd <= 0:
        return dict(n_trades=0, gross=0.0, net=0.0, ok=False)

    # TRADING-window spread + z-score using FORMATION stats (no look-ahead).
    ty, tx = t.iloc[:, 0].to_numpy(), t.iloc[:, 1].to_numpy()
    t_spread = ty - (f_intercept + beta * tx)
    z = (t_spread - mu) / sd

    # z-score signal: enter when |z| >= Z_ENTRY (short spread if z>0, long if z<0),
    # exit when |z| <= Z_EXIT. Spread PnL per round-trip = move in spread captured.
    pos = 0  # +1 long-spread, -1 short-spread, 0 flat
    entry_spread = 0.0
    n_trades = 0
    gross = 0.0
    for i in range(len(z)):
        if pos == 0:
            if z[i] >= Z_ENTRY:
                pos, entry_spread = -1, t_spread[i]  # short the spread
            elif z[i] <= -Z_ENTRY:
                pos, entry_spread = +1, t_spread[i]  # long the spread
        else:
            if abs(z[i]) <= Z_EXIT:
                # PnL of the spread move; spread is in log-price units, so the
                # captured move ~= fractional return of the market-neutral pair.
                gross += pos * (t_spread[i] - entry_spread)
                n_trades += 1
                pos = 0
    # close any open position at window end (mark, not a fee event)
    if pos != 0:
        gross += pos * (t_spread[-1] - entry_spread)
        n_trades += 1
    net = gross - n_trades * COST_PER_ROUNDTRIP
    return dict(n_trades=n_trades, gross=gross, net=net, ok=True)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 78)
    print("iter-v3/095 Phase-1 GO/NO-GO EDA — crypto cointegration stat-arb")
    print("=" * 78)
    print(f"IS-only: open_time < OOS_CUTOFF_MS={OOS_CUTOFF_MS} (2025-03-24)")
    print(f"Walk-forward: {TRAINING_MONTHS}-month formation + 1-month trading, monthly step")
    print(f"Universe: 22-symbol XS_UNIVERSE -> C(22,2)={len(list(itertools.combinations(XS_UNIVERSE,2)))} candidate pairs")
    print()

    panel, qv = load_log_prices()
    print(f"Loaded IS log-price panel: {panel.shape[0]} bars x {panel.shape[1]} symbols")
    print(f"  IS span: {panel.index.min()} .. {panel.index.max()}")
    windows = make_formation_windows(panel)
    print(f"Walk-forward windows (24m formation + 1m trade, in IS): {len(windows)}")
    print()

    # ------------------------------------------------------------------
    # T1 — cointegration prevalence per formation window
    # T2 — persistence: cointegrated in window N -> in N+1?
    # T3 — half-life distribution + stability
    # ------------------------------------------------------------------
    # coint_by_window[w] = set of cointegrated pair-tuples in window w
    coint_by_window: dict[int, set] = {}
    t1_rows = []
    t3_rows = []
    pair_betas: dict[tuple, dict] = {}  # (w, pair) -> {beta, hl}

    for w in windows:
        elig = eligible_symbols(panel, qv, w["form_lo"], w["form_hi"])
        seg = panel[(panel.index >= w["form_lo"]) & (panel.index < w["form_hi"])]
        coint_pairs = set()
        n_tested = 0
        half_lives = []
        for a, b in itertools.combinations(elig, 2):
            pval, beta, hl = engle_granger(seg[a], seg[b])
            if np.isnan(pval):
                continue
            n_tested += 1
            if pval < COINT_PVALUE:
                coint_pairs.add((a, b))
                pair_betas[(w["idx"], (a, b))] = dict(beta=beta, hl=hl)
                if np.isfinite(hl):
                    half_lives.append(hl)
        coint_by_window[w["idx"]] = coint_pairs
        prevalence = len(coint_pairs) / n_tested if n_tested else 0.0
        t1_rows.append(
            dict(
                window=w["idx"], n_eligible=len(elig), n_pairs_tested=n_tested,
                n_cointegrated=len(coint_pairs), prevalence=round(prevalence, 4),
            )
        )
        if half_lives:
            t3_rows.append(
                dict(
                    window=w["idx"], n_coint=len(coint_pairs),
                    hl_median=round(float(np.median(half_lives)), 2),
                    hl_p25=round(float(np.percentile(half_lives, 25)), 2),
                    hl_p75=round(float(np.percentile(half_lives, 75)), 2),
                    hl_frac_tradeable=round(
                        float(np.mean([(2 <= h <= 60) for h in half_lives])), 4
                    ),
                )
            )

    t1 = pd.DataFrame(t1_rows)
    t1.to_csv(OUT_DIR / "T1_coint_prevalence.csv", index=False)
    t3 = pd.DataFrame(t3_rows)
    t3.to_csv(OUT_DIR / "T3_halflife.csv", index=False)

    # ---- T2 persistence: for each consecutive window pair (N, N+1) ----
    t2_rows = []
    for i in range(len(windows) - 1):
        prev = coint_by_window.get(i, set())
        nxt = coint_by_window.get(i + 1, set())
        if not prev:
            continue
        survived = prev & nxt
        persist = len(survived) / len(prev)
        t2_rows.append(
            dict(
                window_n=i, window_n1=i + 1,
                n_coint_n=len(prev), n_coint_n1=len(nxt),
                n_survived=len(survived),
                persistence_rate=round(persist, 4),
            )
        )
    t2 = pd.DataFrame(t2_rows)
    t2.to_csv(OUT_DIR / "T2_persistence.csv", index=False)

    # ------------------------------------------------------------------
    # T4 — out-of-formation tradeability for PERSISTENT pairs.
    # A "persistent pair at window N" = cointegrated in window N AND N-1.
    # We trade it on window N's TRADING span (out-of-formation) and check
    # net-of-cost PnL. This is the strategy a walk-forward book would run:
    # select pairs that were cointegrated in the formation window AND the
    # window before (a persistence filter), then trade them next.
    # ------------------------------------------------------------------
    t4_rows = []
    for i in range(1, len(windows)):
        w = windows[i]
        prev = coint_by_window.get(i - 1, set())
        cur = coint_by_window.get(i, set())
        persistent = prev & cur  # cointegrated in BOTH formation windows
        for pair in persistent:
            meta = pair_betas.get((i, pair))
            if meta is None or not np.isfinite(meta["beta"]):
                continue
            res = simulate_pair_tradeability(
                panel, pair[0], pair[1], meta["beta"],
                w["form_lo"], w["form_hi"], w["trade_lo"], w["trade_hi"],
            )
            if not res["ok"]:
                continue
            t4_rows.append(
                dict(
                    window=i, pair=f"{pair[0]}-{pair[1]}",
                    half_life=round(meta["hl"], 2) if np.isfinite(meta["hl"]) else np.nan,
                    n_trades=res["n_trades"],
                    gross_pnl=round(res["gross"], 5),
                    net_pnl=round(res["net"], 5),
                )
            )
    t4 = pd.DataFrame(t4_rows)
    t4.to_csv(OUT_DIR / "T4_tradeability.csv", index=False)

    # ------------------------------------------------------------------
    # VERDICT
    # ------------------------------------------------------------------
    print("-" * 78)
    print("T1 — COINTEGRATION PREVALENCE per formation window")
    print("-" * 78)
    print(t1.to_string(index=False))
    print(f"\n  mean prevalence: {t1['prevalence'].mean():.4f}"
          f"  | mean #cointegrated pairs/window: {t1['n_cointegrated'].mean():.1f}")

    print()
    print("-" * 78)
    print("T2 — PERSISTENCE (DECISIVE): cointegrated in window N -> still in N+1?")
    print("-" * 78)
    print(t2.to_string(index=False))
    mean_persist = t2["persistence_rate"].mean() if not t2.empty else 0.0
    print(f"\n  MEAN PERSISTENCE RATE: {mean_persist:.4f}")
    # Random-decoherence baseline: if a pair's window-N+1 cointegration were
    # independent of window N, the persistence rate would equal the base
    # prevalence. Persistence MATERIALLY above prevalence => genuine structure.
    base_prev = t1["prevalence"].mean()
    print(f"  base prevalence (random-decoherence baseline): {base_prev:.4f}")
    print(f"  persistence LIFT over random: {mean_persist - base_prev:+.4f}")

    print()
    print("-" * 78)
    print("T3 — SPREAD HALF-LIFE distribution + stability")
    print("-" * 78)
    if not t3.empty:
        print(t3.to_string(index=False))
        print(f"\n  median half-life across windows: {t3['hl_median'].median():.2f} bars"
              f"  ({t3['hl_median'].median() * 8 / 24:.1f} days)")
        print(f"  mean frac with tradeable HL (2-60 bars): {t3['hl_frac_tradeable'].mean():.4f}")
    else:
        print("  (no finite half-lives — spreads not mean-reverting)")

    print()
    print("-" * 78)
    print("T4 — OUT-OF-FORMATION TRADEABILITY of PERSISTENT pairs (net of cost)")
    print("-" * 78)
    if not t4.empty:
        n_pair_windows = len(t4)
        n_traded = int((t4["n_trades"] > 0).sum())
        total_trades = int(t4["n_trades"].sum())
        mean_net = t4["net_pnl"].mean()
        mean_gross = t4["gross_pnl"].mean()
        frac_net_pos = float((t4["net_pnl"] > 0).mean())
        # Per-traded-pair-window (only the ones that actually fired a trade)
        traded = t4[t4["n_trades"] > 0]
        net_pos_when_traded = float((traded["net_pnl"] > 0).mean()) if len(traded) else 0.0
        print(f"  persistent pair-windows evaluated:        {n_pair_windows}")
        print(f"  pair-windows that fired >=1 trade:        {n_traded}")
        print(f"  total round-trip trades (out-of-form):    {total_trades}")
        print(f"  mean GROSS pnl per pair-window:           {mean_gross:+.5f}")
        print(f"  mean NET   pnl per pair-window:           {mean_net:+.5f}")
        print(f"  frac pair-windows NET-positive (all):     {frac_net_pos:.4f}")
        print(f"  frac NET-positive | fired a trade:        {net_pos_when_traded:.4f}")
        # Aggregate net edge: sum of net PnL over a roughly self-financing book.
        agg_net = t4["net_pnl"].sum()
        agg_gross = t4["gross_pnl"].sum()
        print(f"  aggregate GROSS pnl (all pair-windows):    {agg_gross:+.4f}")
        print(f"  aggregate NET   pnl (all pair-windows):    {agg_net:+.4f}")
        if agg_gross > 0:
            print(f"  cost drag (1 - net/gross):                {1 - agg_net/agg_gross:.4f}")
    else:
        print("  (no persistent pairs to trade — persistence is the binding failure)")

    # ------------------------------------------------------------------
    # GO / NO-GO decision logic — pre-registered thresholds.
    # ------------------------------------------------------------------
    print()
    print("=" * 78)
    print("GO / NO-GO VERDICT")
    print("=" * 78)
    # Pre-registered GO criteria (ALL must hold):
    #  (P) PERSISTENCE: mean persistence rate >= 0.55 AND a material lift over
    #      the random-decoherence baseline (>= +0.15) — pairs must STAY
    #      cointegrated, not re-roll the dice each window.
    #  (H) HALF-LIFE: median half-life in the tradeable 2-60 bar band AND mean
    #      frac-tradeable >= 0.50 — spreads must mean-revert on a horizon a
    #      monthly-rebalanced 8h book can actually exploit.
    #  (T) TRADEABILITY: aggregate NET pnl > 0 AND >= 55% of traded pair-windows
    #      NET-positive — the spread must beat the two-leg turnover cost.
    crit_P = (mean_persist >= 0.55) and ((mean_persist - base_prev) >= 0.15)
    if not t3.empty:
        med_hl = t3["hl_median"].median()
        crit_H = (2 <= med_hl <= 60) and (t3["hl_frac_tradeable"].mean() >= 0.50)
    else:
        crit_H = False
    if not t4.empty:
        agg_net = t4["net_pnl"].sum()
        traded = t4[t4["n_trades"] > 0]
        net_pos_when_traded = float((traded["net_pnl"] > 0).mean()) if len(traded) else 0.0
        crit_T = (agg_net > 0) and (net_pos_when_traded >= 0.55)
    else:
        crit_T = False

    print(f"  (P) PERSISTENCE  — mean rate {mean_persist:.4f} >= 0.55"
          f" AND lift {mean_persist - base_prev:+.4f} >= +0.15  -> {'PASS' if crit_P else 'FAIL'}")
    print(f"  (H) HALF-LIFE    — median in [2,60] bars"
          f" AND frac-tradeable >= 0.50  -> {'PASS' if crit_H else 'FAIL'}")
    print(f"  (T) TRADEABILITY — aggregate NET > 0"
          f" AND >=55% traded pair-windows NET+  -> {'PASS' if crit_T else 'FAIL'}")
    print()
    verdict = "GO" if (crit_P and crit_H and crit_T) else "NO-GO"
    print(f"  >>> VERDICT: {verdict} <<<")
    if verdict == "NO-GO":
        print("  Crypto cointegration on v3's IS data does not clear the")
        print("  persistence / tradeability bar for a walk-forward pairs strategy.")
        print("  Per feedback_fail_fast.md: STOP at the EDA. No brief, no backtest.")
    else:
        print("  Genuine, persistent, tradeable cointegration. Proceed to Phases 2-5.")
    print("=" * 78)
    print(f"\nArtifacts: {OUT_DIR}/T1_coint_prevalence.csv, T2_persistence.csv,")
    print(f"           T3_halflife.csv, T4_tradeability.csv")


if __name__ == "__main__":
    main()
