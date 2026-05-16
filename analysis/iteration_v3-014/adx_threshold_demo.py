"""
iter-v3/014 — ADX threshold perturbation analysis (gate-ADX-axis EXPLORATION).

Per Critic FINAL Recommendation 1 of iter-v3/013 review (SHA 1ee0213): the
SEVENTH EXPLORATION axis is the ADX threshold gate (currently 20.0 in
RiskV2Config; tested 25.0 in this iteration — tighter, only allow trades when
trend strength is high). ADX threshold is structurally orthogonal to all 5
prior axis representations (features × 2, labeling × 1, gate-zscore × 1,
gate-btc-trend × 1, universe × 1) and NOT subject to mechanical-accretion
artifact (changing ADX threshold DOES change behavior at the trade-roster
level for all 3 retained symbols).

Per `feedback_axis_saturation_predictor.md` (added after iter-v3/012's
NULL-RESULT): brief Section 2 must include a behavioral-effect predictor
with a falsifier triggered when observed change is below predicted lower
bound. Per Critic FINAL Recommendation 3 (iter-v3/013 SHA 1ee0213): the
falsifier threshold MUST be derived as
``ceil(1.2 × counterfactual_n_trades)`` rather than hardcoded — robust
against single-axis universe variations.

Methodology — counterfactual ADX-kill estimate
==============================================
Trades.csv does NOT include ADX at entry time (the ADX gate fires inside
RiskV3Wrapper before the trade is created). To estimate which iter-v3/013
trades would be killed by tighter ADX>=25, we:

1. Load iter-v3/013's IS+OOS trade rosters (209 IS + 85 OOS).
2. For each trade entry (open_time, symbol), compute the 14-period Wilder
   ADX on the symbol's 8h OHLC series ending at the candle BEFORE open_time
   (past-only, no look-ahead). This mirrors the RiskV3Wrapper computation.
3. Bucket trades by ADX bucket: (-inf, 20), [20, 25), [25, +inf).
4. The ADX-(20, 25) bucket = trades the tighter threshold would kill.
5. counterfactual_n_trades = iter-v3/013's IS trades − ADX-(20, 25) bucket
   trades (these are the survivors under tighter threshold).
6. saturation_falsifier_threshold = ceil(1.2 × counterfactual_n_trades).

Disclaimer — this is FIRST-ORDER. The realized iter-v3/014 run will
diverge from the counterfactual because:
- Optuna re-optimizes hyperparameters under the new gate config (different
  optimal params; per-cell PBO/CPCV partitioning unchanged but trial
  trajectories will diverge).
- Risk gates compose (z-score OOD, BTC trend, low-vol, Hurst): a trade
  killed by ADX in iter-v3/013 might have been killed by another gate
  upstream too, so naive ADX-only counting overcounts the kill rate.
  In iter-v3/013 the ADX gate fired AFTER passing earlier gates, so the
  ADX-(20, 25) bucket is an upper bound on the additional kills.
- Cooldown logic: removing one trade may free downstream candles from
  cooldown lockout, occasionally adding new trades that did not exist
  in iter-v3/013.

The counterfactual establishes the DIRECTION + ORDER OF MAGNITUDE of
the ADX-tightening effect; the realized run will be in this neighborhood
but not identical.

Inputs:
- reports-v3/iteration_v3-013/in_sample/trades.csv  (209 IS rows)
- reports-v3/iteration_v3-013/out_of_sample/trades.csv  (85 OOS rows)
- data/<SYMBOL>/8h.csv  (OHLC for ADX computation)

Outputs (committed BEFORE the brief, per Phase 5.5):
- analysis/iteration_v3-014/expected_adx_kill.csv  (per-bucket aggregate)
- analysis/iteration_v3-014/synthesis.md  (1-paragraph narrative + falsifier)
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]
SOURCE_REPORT_DIR = ROOT / "reports-v3" / "iteration_v3-013"
IS_TRADES_CSV = SOURCE_REPORT_DIR / "in_sample" / "trades.csv"
OOS_TRADES_CSV = SOURCE_REPORT_DIR / "out_of_sample" / "trades.csv"
DATA_DIR = ROOT / "data"
OUT_DIR = ROOT / "analysis" / "iteration_v3-014"
OUT_KILL_CSV = OUT_DIR / "expected_adx_kill.csv"
OUT_SYNTHESIS = OUT_DIR / "synthesis.md"

ADX_PERIOD = 14  # matches RiskV2Config.adx_period default
OLD_THRESHOLD = 20.0
NEW_THRESHOLD = 25.0

# 3-symbol v3 universe (BCH+LDO+TRX), inherited from iter-v3/013
SYMBOLS = ("BCHUSDT", "LDOUSDT", "TRXUSDT")


# ---------------------------------------------------------------------------
# ADX computation — copy of risk_v2._compute_adx (Wilder smoothing)
# ---------------------------------------------------------------------------


def compute_adx(
    high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14
) -> np.ndarray:
    """Average Directional Index (Wilder smoothing).

    Mirror of ``crypto_trade.strategies.ml.risk_v2._compute_adx`` so this
    analysis script does not need to import the runtime gate code (and so
    the script keeps working if the runtime ADX implementation is later
    refactored — it captures the iter-v3/013 production semantics).
    """
    n = len(high)
    if n < 2 * period + 1:
        return np.full(n, np.nan)

    up_move = np.diff(high, prepend=high[0])
    down_move = np.diff(-low, prepend=-low[0])
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

    prev_close = np.concatenate([[close[0]], close[:-1]])
    tr = np.maximum.reduce(
        [high - low, np.abs(high - prev_close), np.abs(low - prev_close)]
    )

    def _wilder(series: np.ndarray) -> np.ndarray:
        out = np.full_like(series, np.nan, dtype=np.float64)
        if n < period:
            return out
        out[period - 1] = np.sum(series[:period])
        for i in range(period, n):
            out[i] = out[i - 1] - (out[i - 1] / period) + series[i]
        return out

    atr_w = _wilder(tr)
    plus_dm_w = _wilder(plus_dm)
    minus_dm_w = _wilder(minus_dm)

    with np.errstate(invalid="ignore", divide="ignore"):
        plus_di = 100.0 * plus_dm_w / atr_w
        minus_di = 100.0 * minus_dm_w / atr_w
        dx = 100.0 * np.abs(plus_di - minus_di) / (plus_di + minus_di)

    adx = np.full(n, np.nan, dtype=np.float64)
    first_valid = 2 * period - 1
    if first_valid < n:
        adx[first_valid] = np.nanmean(dx[period - 1 : first_valid + 1])
        for i in range(first_valid + 1, n):
            if not np.isnan(dx[i]) and not np.isnan(adx[i - 1]):
                adx[i] = ((adx[i - 1] * (period - 1)) + dx[i]) / period
    return adx


# ---------------------------------------------------------------------------
# Load OHLC + compute ADX series per symbol (cached per-run)
# ---------------------------------------------------------------------------


def load_ohlc_and_adx() -> dict[str, pd.DataFrame]:
    """Return {symbol: DataFrame with columns [close_time, adx]}.

    ADX is computed Wilder-smoothed over the 8h candle series. We index by
    ``close_time`` (millisecond epoch) — the runtime gate fires on the
    candle's close, and trades.csv stores ``open_time`` equal to the prior
    candle's ``close_time`` (entry boundary). So we look up ADX at the
    candle whose ``close_time == trade.open_time``.
    """
    out: dict[str, pd.DataFrame] = {}
    for sym in SYMBOLS:
        path = DATA_DIR / sym / "8h.csv"
        if not path.exists():
            raise SystemExit(f"SETUP DRIFT: OHLC not found for {sym} at {path}.")
        df = pd.read_csv(path)
        df = df.sort_values("open_time").reset_index(drop=True)
        h = df["high"].astype(float).to_numpy()
        l = df["low"].astype(float).to_numpy()  # noqa: E741
        c = df["close"].astype(float).to_numpy()
        adx = compute_adx(h, l, c, period=ADX_PERIOD)
        out[sym] = pd.DataFrame(
            {"close_time": df["close_time"].astype("int64"), "adx": adx}
        )
    return out


# ---------------------------------------------------------------------------
# Annotate trades with ADX at entry candle
# ---------------------------------------------------------------------------


def annotate_with_adx(trades: pd.DataFrame, adx_by_sym: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """For each trade, look up ADX at the entry candle's close.

    The runtime gate fires at candle close BEFORE the trade is opened; the
    ADX value used by the gate is the ADX at the candle whose ``close_time``
    matches the trade's ``open_time`` (entry boundary in
    ``backtest.py``). Mirrors the ``RiskV2Wrapper._adx_gate_fails`` lookup
    pattern (which uses ``searchsorted`` on the same boundary).
    """
    annotated = []
    for sym, sym_trades in trades.groupby("symbol"):
        if sym not in adx_by_sym:
            raise SystemExit(f"Trade roster contains unknown symbol {sym}; expected {SYMBOLS}.")
        adx_df = adx_by_sym[sym]
        # Trade open_time = prior candle close_time. Merge on that boundary.
        merged = sym_trades.merge(
            adx_df, left_on="open_time", right_on="close_time", how="left"
        )
        annotated.append(merged)
    out = pd.concat(annotated, ignore_index=True)
    return out


def bucket_adx(value: float) -> str:
    if not math.isfinite(value):
        return "nan"
    if value < OLD_THRESHOLD:
        return f"<{OLD_THRESHOLD:g}_GHOST"  # would not have entered under iter-v3/013
    if value < NEW_THRESHOLD:
        return f"[{OLD_THRESHOLD:g},{NEW_THRESHOLD:g})_KILL"  # killed by tighter
    return f">={NEW_THRESHOLD:g}_KEEP"  # survives tighter


def aggregate_buckets(annotated: pd.DataFrame, label: str) -> pd.DataFrame:
    if annotated.empty:
        return pd.DataFrame(
            columns=[
                "slice",
                "bucket",
                "n_trades",
                "n_wins",
                "win_rate_pct",
                "weighted_pnl_total",
                "share_of_slice_pct",
            ]
        )
    work = annotated.copy()
    work["bucket"] = work["adx"].apply(bucket_adx)
    total = float(work["weighted_pnl"].sum())
    rows = []
    for bucket, sub in work.groupby("bucket"):
        n = int(len(sub))
        n_wins = int((sub["net_pnl_pct"] > 0).sum())
        wr = (n_wins / n) * 100.0 if n else float("nan")
        wpnl = float(sub["weighted_pnl"].sum())
        share = (wpnl / total * 100.0) if abs(total) > 1e-9 else float("nan")
        rows.append(
            {
                "slice": label,
                "bucket": bucket,
                "n_trades": n,
                "n_wins": n_wins,
                "win_rate_pct": round(wr, 2),
                "weighted_pnl_total": round(wpnl, 4),
                "share_of_slice_pct": round(share, 2),
            }
        )
    return pd.DataFrame(rows).sort_values("bucket").reset_index(drop=True)


# ---------------------------------------------------------------------------
# Synthesis
# ---------------------------------------------------------------------------


def write_synthesis(
    is_buckets: pd.DataFrame,
    oos_buckets: pd.DataFrame,
    is_total: int,
    oos_total: int,
    is_kill_n: int,
    oos_kill_n: int,
    is_kill_wpnl: float,
    oos_kill_wpnl: float,
) -> tuple[int, int, Path]:
    """Returns (counterfactual_n_trades_IS, falsifier_threshold_IS, path)."""
    counterfactual_n_trades_is = is_total - is_kill_n
    counterfactual_n_trades_oos = oos_total - oos_kill_n
    falsifier_threshold_is = math.ceil(1.2 * counterfactual_n_trades_is)
    falsifier_threshold_oos = math.ceil(1.2 * counterfactual_n_trades_oos)

    is_kill_pct = (is_kill_n / is_total * 100.0) if is_total else float("nan")
    oos_kill_pct = (oos_kill_n / oos_total * 100.0) if oos_total else float("nan")

    text = (
        "# iter-v3/014 — ADX threshold (20 → 25) counterfactual synthesis\n\n"
        "Per Critic FINAL Recommendation 1 of iter-v3/013 review (SHA "
        "`1ee0213`): the SEVENTH EXPLORATION axis is the ADX threshold gate. "
        "Currently 20.0 in `RiskV2Config`; this iteration tightens to 25.0 "
        "(only allow trades when trend strength is high). ADX threshold is "
        "structurally orthogonal to all 5 prior axes (features × 2, labeling "
        "× 1, gate-zscore × 1, gate-btc-trend × 1, universe × 1) and NOT "
        "subject to mechanical-accretion artifact: changing the ADX gate DOES "
        "change behavior at the trade-roster level for all 3 retained symbols "
        "(BCH+LDO+TRX inherited from iter-v3/013).\n\n"
        "## ADX-bucket distribution at iter-v3/013 trade entry candles\n\n"
        "Each iter-v3/013 trade is annotated with the 14-period Wilder ADX at "
        "the candle whose `open_time` matches the trade's entry `open_time` "
        "(mirroring the runtime `RiskV2Wrapper` ADX lookup). Trades are then "
        "bucketed by ADX:\n"
        "- `<20_GHOST`: would not have entered under the iter-v3/013 gate "
        "(should be 0 — sanity check).\n"
        "- `[20,25)_KILL`: killed by tighter ADX>=25; the new threshold's "
        "additional kill set.\n"
        "- `>=25_KEEP`: survives the tighter threshold.\n\n"
        f"### IS (iter-v3/013 in_sample, total {is_total} trades)\n\n"
        f"{is_buckets.to_markdown(index=False)}\n\n"
        f"### OOS (iter-v3/013 out_of_sample, total {oos_total} trades)\n\n"
        f"{oos_buckets.to_markdown(index=False)}\n\n"
        "## Counterfactual + falsifier\n\n"
        f"- IS [20,25) kill bucket: **{is_kill_n} trades** "
        f"(**{is_kill_pct:.1f}%** of {is_total}; weighted_pnl_total = "
        f"**{is_kill_wpnl:+.2f}** removed).\n"
        f"- IS counterfactual_n_trades = {is_total} − {is_kill_n} = "
        f"**{counterfactual_n_trades_is}**.\n"
        f"- IS saturation falsifier_threshold = ceil(1.2 × "
        f"{counterfactual_n_trades_is}) = **{falsifier_threshold_is}** — "
        "if observed iter-v3/014 IS trades > this threshold, the ADX axis "
        "did not propagate (per `feedback_axis_saturation_predictor.md`).\n"
        f"- OOS [20,25) kill bucket: **{oos_kill_n} trades** "
        f"(**{oos_kill_pct:.1f}%** of {oos_total}; weighted_pnl_total = "
        f"**{oos_kill_wpnl:+.2f}** removed). Informational under EXPLORATION.\n"
        f"- OOS counterfactual_n_trades = {oos_total} − {oos_kill_n} = "
        f"**{counterfactual_n_trades_oos}**.\n"
        f"- OOS saturation falsifier_threshold (informational) = ceil(1.2 × "
        f"{counterfactual_n_trades_oos}) = "
        f"**{falsifier_threshold_oos}**.\n\n"
        "## Direction summary\n\n"
        "Tightening ADX from 20 to 25 is a more selective trend filter — "
        "only candles with stronger directional movement pass through. The "
        "counterfactual estimates the upper bound of additional kills (some "
        "[20,25) trades may have been killed upstream by other gates, so the "
        "realized iter-v3/014 kill set may be smaller). Whether the IS Sharpe "
        "improves depends on the per-trade economics of the killed bucket: "
        "if [20,25) trades were systematically losing or noisy, killing them "
        "improves Sharpe; if they were a representative sample, killing them "
        "merely shrinks the trade roster without improving edge. Brief "
        "Section 4 will commit a predicted Sharpe band [+0.50, +1.30] "
        "(iter-v3/013's +1.01 ±0.30) and a falsifier on the IS roster size.\n"
    )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_SYNTHESIS.write_text(text, encoding="utf-8")
    return counterfactual_n_trades_is, falsifier_threshold_is, OUT_SYNTHESIS


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def main() -> int:
    if not IS_TRADES_CSV.exists():
        raise SystemExit(f"SETUP DRIFT: {IS_TRADES_CSV} not found.")
    if not OOS_TRADES_CSV.exists():
        raise SystemExit(f"SETUP DRIFT: {OOS_TRADES_CSV} not found.")

    is_df = pd.read_csv(IS_TRADES_CSV)
    oos_df = pd.read_csv(OOS_TRADES_CSV)
    print(f"Loaded {len(is_df)} IS trades, {len(oos_df)} OOS trades from iter-v3/013.")

    # Sanity: iter-v3/013 must be 3-symbol BCH+LDO+TRX, no MKR
    is_syms = set(is_df["symbol"].unique())
    oos_syms = set(oos_df["symbol"].unique())
    assert is_syms <= set(SYMBOLS), f"IS roster has unexpected symbols: {is_syms - set(SYMBOLS)}"
    assert oos_syms <= set(SYMBOLS), f"OOS roster has unexpected: {oos_syms - set(SYMBOLS)}"
    assert "MKRUSDT" not in is_syms and "MKRUSDT" not in oos_syms, "MKR present in iter-v3/013 roster"

    print("Computing ADX series for 3 symbols (Wilder, period=14)...")
    adx_by_sym = load_ohlc_and_adx()
    for sym, df in adx_by_sym.items():
        finite = df["adx"].dropna()
        print(
            f"  {sym}: {len(df)} bars; "
            f"ADX finite {len(finite)}; "
            f"min={finite.min():.2f} median={finite.median():.2f} max={finite.max():.2f}"
        )

    is_annot = annotate_with_adx(is_df, adx_by_sym)
    oos_annot = annotate_with_adx(oos_df, adx_by_sym)

    # Sanity: any iter-v3/013 trade with ADX < 20 implies the gate was disabled
    # (would have been killed at iter-v3/013). Should be zero.
    n_is_ghost = int((is_annot["adx"] < OLD_THRESHOLD).sum())
    n_oos_ghost = int((oos_annot["adx"] < OLD_THRESHOLD).sum())
    n_is_nan = int(is_annot["adx"].isna().sum())
    n_oos_nan = int(oos_annot["adx"].isna().sum())
    print(
        f"Sanity (should be 0): IS trades with ADX<20={n_is_ghost} ADX=NaN={n_is_nan}; "
        f"OOS ADX<20={n_oos_ghost} ADX=NaN={n_oos_nan}"
    )

    # Bucket aggregates
    is_buckets = aggregate_buckets(is_annot, "IS")
    oos_buckets = aggregate_buckets(oos_annot, "OOS")

    # KILL bucket extraction
    def _kill(buckets: pd.DataFrame) -> tuple[int, float]:
        kill_label = f"[{OLD_THRESHOLD:g},{NEW_THRESHOLD:g})_KILL"
        row = buckets[buckets["bucket"] == kill_label]
        if row.empty:
            return 0, 0.0
        return int(row.iloc[0]["n_trades"]), float(row.iloc[0]["weighted_pnl_total"])

    is_kill_n, is_kill_wpnl = _kill(is_buckets)
    oos_kill_n, oos_kill_wpnl = _kill(oos_buckets)

    # Combine + write CSV
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    combined = pd.concat([is_buckets, oos_buckets], ignore_index=True)
    combined.to_csv(OUT_KILL_CSV, index=False)
    print(f"\nWROTE: {OUT_KILL_CSV}")
    print("\n--- IS buckets ---")
    print(is_buckets.to_string(index=False))
    print("\n--- OOS buckets ---")
    print(oos_buckets.to_string(index=False))

    cf_is, falsifier_is, synth_path = write_synthesis(
        is_buckets,
        oos_buckets,
        is_total=int(len(is_df)),
        oos_total=int(len(oos_df)),
        is_kill_n=is_kill_n,
        oos_kill_n=oos_kill_n,
        is_kill_wpnl=is_kill_wpnl,
        oos_kill_wpnl=oos_kill_wpnl,
    )
    print(f"\nWROTE: {synth_path}")
    print(
        f"\ncounterfactual_n_trades (IS) = {cf_is}  "
        f"falsifier_threshold (IS) = ceil(1.2 × {cf_is}) = {falsifier_is}"
    )
    print("PASS — iter-v3/014 ADX-threshold counterfactual analysis complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
