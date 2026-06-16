"""
Risk Engineer Phase 4.7 — IS-only risk analysis for iter-v1/002 (BTCUSDT).

IS-ONLY. Every number below is derived strictly from trades whose
``close_time < OOS_CUTOFF_MS`` (2025-03-24). The R1 cooldown-gating decision is
keyed off ``open_time`` (entry candle), so for any entry-suppression simulation
we additionally require ``open_time < OOS_CUTOFF_MS``. No OOS data is ever read.

Outputs (printed; the brief quotes these):
  1. Loss clustering: exit-reason mix, consecutive-SL streak histogram, the
     worst drawdown sequence, NATR vol-bucket PnL, monthly PnL.
  2. R1 consecutive-SL cooldown simulation (naive entry-suppression estimate,
     flagged as an UPPER BOUND because the v1 position model is sequential).
  3. Fractional-Kelly sizing from IS win-rate + payoff ratio + variance.
  4. Stress matrix inputs: vol-spike windows, regime (NATR-tercile) split,
     tail-loss (worst trade / worst day).

Run:
  uv run python analysis/BTCUSDT/iteration_v1-002/risk_is_analysis.py
"""
# ruff: noqa: E501, N803, N806
#   E501: print() report lines are intentionally wide for tabular readability.
#   N803/N806: K, C, b, p, q are math-convention symbols (Kelly / streak limits).

from __future__ import annotations

import csv
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

# ── Sacred constants (IMMUTABLE) ────────────────────────────────────────────
OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 00:00:00 UTC
CANDLE_MS = 8 * 60 * 60 * 1000  # 8h cadence (3 candles/day)

REPO = Path(__file__).resolve().parents[3]
TRADES = REPO / "reports-v1/BTCUSDT/iteration_v1-001/in_sample/trades.csv"
DAILY = REPO / "reports-v1/BTCUSDT/iteration_v1-001/in_sample/daily_pnl.csv"
FEATS = REPO / "data/features/BTCUSDT_8h_features.parquet"


def _ms_to_date(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=UTC).strftime("%Y-%m-%d")


def load_is_trades() -> pd.DataFrame:
    rows = list(csv.DictReader(open(TRADES)))
    df = pd.DataFrame(rows)
    for c in ("open_time", "close_time"):
        df[c] = df[c].astype(np.int64)
    for c in ("net_pnl_pct", "weighted_pnl", "weight_factor", "confidence", "pnl_pct"):
        df[c] = df[c].astype(float)
    # IS accounting half — closed before the cutoff (matches report convention).
    df = df[df["close_time"] < OOS_CUTOFF_MS].reset_index(drop=True)
    df = df.sort_values("open_time").reset_index(drop=True)
    return df


def attach_natr(df: pd.DataFrame) -> pd.DataFrame:
    """Attach vol_natr_14 known at signal time.

    The trades CSV's ``open_time`` field is actually the *signal candle's
    close_time* (timestamps end in ...999, i.e. candle-close, not candle-open).
    The feature parquet keys ``vol_natr_14`` by candle ``close_time``; that row
    is the past-only NATR fully observable at signal time. So we merge the trade
    ``open_time`` against the parquet ``close_time`` — no look-ahead.
    """
    feats = pd.read_parquet(FEATS, columns=["close_time", "vol_natr_14"])
    feats = feats.rename(columns={"close_time": "open_time", "vol_natr_14": "natr_at_entry"})
    merged = df.merge(feats, on="open_time", how="left")
    return merged


def section(title: str) -> None:
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def main() -> None:
    df = load_is_trades()
    df = attach_natr(df)
    n = len(df)

    section("0. IS WINDOW + HEADLINE (close_time < OOS_CUTOFF, 2025-03-24)")
    print(f"IS trades (closed in-sample): {n}")
    print(f"IS window: {_ms_to_date(df.open_time.min())} .. {_ms_to_date(df.close_time.max())}")
    print(f"net PnL sum (unweighted %):   {df.net_pnl_pct.sum():.4f}")
    print(f"net PnL sum (weighted %):     {df.weighted_pnl.sum():.4f}")
    print(f"mean net_pnl_pct/trade:       {df.net_pnl_pct.mean():.4f}")
    print(f"win rate:                     {(df.net_pnl_pct > 0).mean() * 100:.1f}%")

    # ── 1. EXIT-REASON MIX ──────────────────────────────────────────────────
    section("1. EXIT-REASON MIX (IS)")
    g = df.groupby("exit_reason").agg(
        trades=("net_pnl_pct", "size"),
        net_pnl=("net_pnl_pct", "sum"),
        avg_pnl=("net_pnl_pct", "mean"),
        win_rate=("net_pnl_pct", lambda s: (s > 0).mean() * 100),
    )
    print(g.round(4).to_string())
    sl = df[df.exit_reason == "stop_loss"]
    print(f"\nstop_loss share of trades: {len(sl) / n * 100:.1f}%")
    print(
        f"stop_loss net PnL contribution: {sl.net_pnl_pct.sum():.4f} "
        f"({sl.net_pnl_pct.sum() / df.net_pnl_pct.sum() * 100 if df.net_pnl_pct.sum() else float('nan'):.1f}% of total)"
    )

    # ── 2. CONSECUTIVE-SL STREAK STRUCTURE ──────────────────────────────────
    section("2. CONSECUTIVE-SL STREAK STRUCTURE (IS, ordered by open_time)")
    is_sl = (df.exit_reason == "stop_loss").to_numpy()
    streak_lengths: list[int] = []
    # Record completed streak lengths and how many trades sit at depth>=k.
    depth_counts: dict[int, int] = {}
    cur = 0
    for flag in is_sl:
        if flag:
            cur += 1
            depth_counts[cur] = depth_counts.get(cur, 0) + 1
        else:
            if cur > 0:
                streak_lengths.append(cur)
            cur = 0
    if cur > 0:
        streak_lengths.append(cur)
    print("Completed SL-run length histogram (consecutive SL closes, entry-ordered):")
    runs = pd.Series(streak_lengths)
    print(runs.value_counts().sort_index().to_string())
    print(f"\nLongest consecutive-SL run: {runs.max()} trades")
    print(
        "Trades occurring at SL-streak depth >= k (these are what an R1 limit=k would gate AFTER):"
    )
    for k in (2, 3, 4, 5):
        print(f"  depth>={k}: {sum(v for d, v in depth_counts.items() if d >= k)} trades")

    # ── 3. RUNNING-DRAWDOWN SEQUENCE ────────────────────────────────────────
    section("3. RUNNING-DRAWDOWN SEQUENCE (IS, cumulative weighted PnL, entry-ordered)")
    cum = df.weighted_pnl.cumsum().to_numpy()
    peak = np.maximum.accumulate(cum)
    dd = cum - peak  # <= 0, in pct points of weighted PnL
    worst_dd = dd.min()
    worst_idx = int(dd.argmin())
    print(f"Worst running drawdown (weighted-PnL points): {worst_dd:.4f}")
    print(
        f"  reached at trade #{worst_idx} closing {_ms_to_date(int(df.close_time.iloc[worst_idx]))}"
    )
    # How many trades were taken while >7% below peak (R2 trigger candidate)?
    for trig in (5.0, 7.0, 10.0):
        below = int((dd <= -trig).sum())
        below_pnl = df.weighted_pnl.to_numpy()[dd <= -trig].sum()
        print(
            f"  trades entered* while DD <= -{trig:.0f}%: {below}  (their weighted PnL sum: {below_pnl:.4f})"
        )
    print(
        "  *approx: DD measured at close; R2 gates at entry on prior closes — directional, not exact."
    )

    # ── 4. NATR VOL-BUCKET PnL ──────────────────────────────────────────────
    section("4. NATR VOL-BUCKET PnL (vol_natr_14 at entry candle, IS terciles)")
    valid = df.dropna(subset=["natr_at_entry"]).copy()
    print(f"trades with NATR available: {len(valid)}/{n}")
    if len(valid):
        q = valid["natr_at_entry"].quantile([0, 1 / 3, 2 / 3, 1.0]).to_numpy()
        print(f"NATR terciles (IS): low<={q[1]:.3f}  mid<={q[2]:.3f}  high<={q[3]:.3f}")
        valid["natr_bucket"] = pd.cut(
            valid["natr_at_entry"],
            bins=[-1e9, q[1], q[2], 1e9],
            labels=["low", "mid", "high"],
        )
        gb = valid.groupby("natr_bucket", observed=True).agg(
            trades=("net_pnl_pct", "size"),
            net_pnl=("net_pnl_pct", "sum"),
            avg_pnl=("net_pnl_pct", "mean"),
            win_rate=("net_pnl_pct", lambda s: (s > 0).mean() * 100),
            sl_rate=("exit_reason", lambda s: (s == "stop_loss").mean() * 100),
        )
        print(gb.round(4).to_string())

    # ── 5. MONTHLY PnL (loss clustering in time) ────────────────────────────
    section("5. MONTHLY net PnL (IS)")
    df["month"] = df["close_time"].apply(lambda m: _ms_to_date(int(m))[:7])
    m = df.groupby("month").agg(
        trades=("net_pnl_pct", "size"),
        net_pnl=("net_pnl_pct", "sum"),
        sl=("exit_reason", lambda s: (s == "stop_loss").sum()),
    )
    worst_months = m.sort_values("net_pnl").head(6)
    print("Worst 6 IS months by net PnL:")
    print(worst_months.round(4).to_string())
    print(f"\nSum of those 6 worst months: {worst_months.net_pnl.sum():.4f}")
    print(f"Total IS net PnL:            {df.net_pnl_pct.sum():.4f}")

    # ── 6. R1 CONSECUTIVE-SL COOLDOWN SIMULATION ────────────────────────────
    section("6. R1 CONSECUTIVE-SL COOLDOWN — NAIVE entry-suppression estimate")
    print("Semantics (backtest.py L394-405, L535-536): after K consecutive SL")
    print("closes, arm a cooldown that blocks ANY new entry whose open_time <")
    print("close_time_of_Kth_SL + C*candle_ms. Streak resets on the trigger AND")
    print("on any non-SL close. We replay the IS roster and, for each candidate")
    print("(K, C), count trades whose ENTRY would fall inside an armed window.")
    print("NOTE: UPPER-BOUND only. The v1 model is sequential — suppressing an")
    print("entry frees the slot, so later trades shift. Only the Phase-6 backtest")
    print("is the verdict. (skill NO-CHEATING rule on offline trade subtraction).\n")

    ot = df["open_time"].to_numpy()
    ct = df["close_time"].to_numpy()
    er = df["exit_reason"].to_numpy()
    npnl = df["net_pnl_pct"].to_numpy()
    wpnl = df["weighted_pnl"].to_numpy()

    def simulate_r1(K: int, C: int):
        streak = 0
        cooldown_until = 0
        suppressed_idx = []
        for i in range(len(df)):
            # Gate at entry: is this entry inside an armed cooldown?
            if ot[i] < cooldown_until:
                suppressed_idx.append(i)
                # A suppressed trade does not execute -> does not affect streak.
                continue
            # Executes -> update streak on its close.
            if er[i] == "stop_loss":
                streak += 1
                if streak >= K:
                    cooldown_until = ct[i] + C * CANDLE_MS
                    streak = 0
            else:
                streak = 0
        return suppressed_idx

    print(
        f"{'K':>2} {'C':>3} {'suppressed':>11} {'supp_netPnL':>12} {'supp_wPnL':>10} {'supp_SLrate':>11}"
    )
    for K, C in [(2, 9), (3, 9), (3, 18), (3, 27), (4, 27), (2, 18)]:
        idx = simulate_r1(K, C)
        if idx:
            spct = (er[idx] == "stop_loss").mean() * 100
            print(
                f"{K:>2} {C:>3} {len(idx):>11} {npnl[idx].sum():>12.4f} "
                f"{wpnl[idx].sum():>10.4f} {spct:>10.1f}%"
            )
        else:
            print(f"{K:>2} {C:>3} {0:>11} {'-':>12} {'-':>10} {'-':>11}")
    print("\nInterpretation: positive supp_wPnL removed = the rule would have CUT")
    print("losses (good); negative = it would have removed net winners (cost).")

    # ── 7. FRACTIONAL-KELLY SIZING ──────────────────────────────────────────
    section("7. FRACTIONAL-KELLY SIZING (from IS edge + variance)")
    wins = npnl[npnl > 0]
    losses = npnl[npnl <= 0]
    p = len(wins) / n
    q = 1 - p
    avg_win = wins.mean() if len(wins) else 0.0
    avg_loss = abs(losses.mean()) if len(losses) else 0.0
    b = avg_win / avg_loss if avg_loss else float("nan")  # payoff ratio
    kelly = (b * p - q) / b if b else float("nan")  # classic Kelly fraction
    # Continuous (Gaussian) Kelly = mean / variance of per-trade return.
    mu = npnl.mean()
    var = npnl.var(ddof=1)
    kelly_cont = mu / var if var else float("nan")
    print(f"IS win rate p:         {p:.4f}")
    print(f"avg win  (net %):      {avg_win:.4f}")
    print(f"avg loss (net %, abs): {avg_loss:.4f}")
    print(f"payoff ratio b:        {b:.4f}")
    print(f"per-trade mean mu:     {mu:.4f}")
    print(f"per-trade var:         {var:.4f}")
    print(f"per-trade std:         {np.sqrt(var):.4f}")
    print(f"classic Kelly f*:      {kelly:.4f}")
    print(f"continuous Kelly mu/var: {kelly_cont:.4f}")
    print(f"quarter-Kelly (0.25*f*): {0.25 * kelly:.4f}")
    print(f"half-Kelly    (0.50*f*): {0.50 * kelly:.4f}")
    print("Edge is NEGATIVE on IS (mu<0) -> full Kelly is <=0 (don't bet / minimum size).")
    print("Implication: keep sizing CONSERVATIVE; do NOT raise weight_factor/max_amount.")

    # ── 8. TAIL-LOSS ────────────────────────────────────────────────────────
    section("8. TAIL-LOSS (IS)")
    worst_trade = df.loc[df.net_pnl_pct.idxmin()]
    print(
        f"Worst single IS trade: {worst_trade.net_pnl_pct:.4f}% net "
        f"({worst_trade.exit_reason}, dir {int(worst_trade.direction)}, "
        f"closed {_ms_to_date(int(worst_trade.close_time))})"
    )
    print(f"5th percentile per-trade net_pnl_pct: {np.percentile(npnl, 5):.4f}")
    print(f"1st percentile per-trade net_pnl_pct: {np.percentile(npnl, 1):.4f}")
    # Worst day
    dd_daily = pd.DataFrame(csv.DictReader(open(DAILY)))
    dd_daily["pnl_pct"] = dd_daily["pnl_pct"].astype(float)
    dd_daily["date"] = pd.to_datetime(dd_daily["date"])
    dd_is = dd_daily[dd_daily["date"] < pd.Timestamp("2025-03-24")]
    worst_day = dd_is.loc[dd_is.pnl_pct.idxmin()]
    print(
        f"Worst IS day: {worst_day.date.date()}  {worst_day.pnl_pct:.4f}%  "
        f"({worst_day.trade_count} trades)"
    )
    print("Worst 3 IS days:")
    print(
        dd_is.sort_values("pnl_pct")
        .head(3)[["date", "pnl_pct", "trade_count"]]
        .to_string(index=False)
    )

    # ── 9. STRESS-MATRIX INPUTS: VOL-SPIKE WINDOWS ──────────────────────────
    section("9. VOL-SPIKE WINDOW REPLAY (top-NATR-quintile entries, IS)")
    if len(valid):
        thr = valid["natr_at_entry"].quantile(0.80)
        spike = valid[valid["natr_at_entry"] >= thr]
        rest = valid[valid["natr_at_entry"] < thr]
        print(f"NATR 80th-pct threshold: {thr:.3f}")
        print(f"Top-quintile (vol-spike) entries: {len(spike)} trades")
        print(
            f"  net PnL: {spike.net_pnl_pct.sum():.4f}  avg: {spike.net_pnl_pct.mean():.4f}  "
            f"WR: {(spike.net_pnl_pct > 0).mean() * 100:.1f}%  SLrate: {(spike.exit_reason == 'stop_loss').mean() * 100:.1f}%"
        )
        print(f"Remaining (calmer) entries: {len(rest)} trades")
        print(
            f"  net PnL: {rest.net_pnl_pct.sum():.4f}  avg: {rest.net_pnl_pct.mean():.4f}  "
            f"WR: {(rest.net_pnl_pct > 0).mean() * 100:.1f}%  SLrate: {(rest.exit_reason == 'stop_loss').mean() * 100:.1f}%"
        )

    print("\nDONE. All numbers IS-only (close_time/open_time < OOS_CUTOFF_MS).")


if __name__ == "__main__":
    main()
