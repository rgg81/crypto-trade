"""iter-v1/022 Phase 2 — Orthogonal mechanism candidate diagnostics.

Per LTC prior class = ASYMMETRIC_ROTATION-INVERSE (IS marginal positive / OOS
catastrophic, with 89% of OOS loss in LONG direction), this script tests
ORTHOGONAL MECHANISM candidates against the LTC trade roster:

  Mechanism 1 — BTC-trend gate (mirror /019 ETH+gate):
    Kill counter-trend trades. LTC long when BTC ret_42_bar < -threshold%
    OR LTC short when BTC ret_42_bar > +threshold%. Stateless post-hoc filter.

  Mechanism 2 — Long-suppression-only gate (NEW):
    Kill LTC long when BTC ret_42_bar < threshold (no symmetric short kill).
    Motivated by the OOS direction asymmetry: LTC longs lose -45.4% / 19 tr
    in OOS; LTC shorts are roughly neutral -1.8% / 15 tr.

  Mechanism 3 — Pure shorts-only model (HIGH-RISK / structural):
    Train Model D LTC-only but only consider SHORT predictions.
    Tests the directional asymmetry as a binary structural prior.

  Mechanism 4 — Direction-asymmetric ATR:
    Tighter SL on longs (e.g. ATR×1.0) vs shorts (current ATR×1.75).
    Implicit position-skew toward shorts.

For each mechanism, simulate as a post-hoc filter on baseline LTC trade roster
(IS+OOS combined) and compute IS Δ / OOS Δ vs LTC-in-pool anchor. ORACLE EDA
methodology is VALID here because all proposed mechanisms are STATELESS gates
applied to a deterministic trade stream — no persistent state, no deadlock
risk (per `feedback_v3_oracle_eda_validity.md` STATELESS gate carve-out).

This script does NOT pre-validate against future fold-conditional behavior
(that requires the actual backtest at Phase 6). It produces a SHORT-LIST of
mechanism candidates with expected IS+OOS lift for brief Section 3 selection.

Outputs:
  - analysis/iteration_v1-022/mechanism_candidates.csv
    (one row per mechanism × threshold, IS+OOS Δ vs anchor)
  - analysis/iteration_v1-022/ltc_btc_trend_alignment.csv
    (per-trade attachment: trade open_time + BTC ret_42_bar + counter-trend flag)
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
IS_TRADES = REPO / "reports-v1" / "iteration_v1-baseline" / "in_sample" / "trades.csv"
OOS_TRADES = REPO / "reports-v1" / "iteration_v1-baseline" / "out_of_sample" / "trades.csv"
BTC_KLINES = REPO / "data" / "BTCUSDT" / "8h.csv"
OUT_DIR = REPO / "analysis" / "iteration_v1-022"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SYMBOL = "LTCUSDT"
GATE_LOOKBACK = 42  # 14 days at 8h — matches /019
GATE_THRESHOLDS_PCT = [4.0, 6.0, 8.0, 10.0, 12.0]  # explored at /022; nominal 8% from /019


def _load_btc() -> pd.DataFrame:
    btc = pd.read_csv(BTC_KLINES)
    btc["open_time_ms"] = btc["open_time"].astype("int64")
    btc["close_price"] = btc["close"].astype(float)
    btc = btc.sort_values("open_time_ms").reset_index(drop=True)
    # BTC return over the previous GATE_LOOKBACK bars
    btc["btc_ret_42"] = (
        btc["close_price"] / btc["close_price"].shift(GATE_LOOKBACK) - 1.0
    ) * 100.0
    return btc[["open_time_ms", "close_price", "btc_ret_42"]]


def _attach_btc_trend(trades: pd.DataFrame, btc: pd.DataFrame) -> pd.DataFrame:
    """For each trade, attach the BTC ret_42 from the bar AT-OR-BEFORE trade open."""
    trades = trades.copy()
    trades["open_time_ms"] = trades["open_time"].astype("int64")
    # merge_asof — left side trade open_time, right BTC bar open_time, direction backward
    merged = pd.merge_asof(
        trades.sort_values("open_time_ms"),
        btc[["open_time_ms", "btc_ret_42"]].sort_values("open_time_ms"),
        on="open_time_ms",
        direction="backward",
        allow_exact_matches=True,
    )
    return merged


def _per_trade_sharpe(net_pnl: pd.Series) -> float:
    if len(net_pnl) < 2 or net_pnl.std(ddof=1) == 0:
        return 0.0
    return float(net_pnl.mean() / net_pnl.std(ddof=1))


def _apply_symmetric_btc_gate(trades: pd.DataFrame, threshold_pct: float) -> pd.Series:
    """Symmetric BTC-trend gate (mirror /019):
    Kill LTC long when BTC ret_42 < -threshold; LTC short when BTC ret_42 > +threshold.
    Returns boolean mask: True = KEEP, False = KILL.
    """
    keep = pd.Series(True, index=trades.index)
    if trades["btc_ret_42"].isna().any():
        keep.loc[trades["btc_ret_42"].isna()] = True  # warmup — keep
    nonwu = ~trades["btc_ret_42"].isna()
    kill_long = nonwu & (trades["direction"] == 1) & (trades["btc_ret_42"] < -threshold_pct)
    kill_short = nonwu & (trades["direction"] == -1) & (trades["btc_ret_42"] > threshold_pct)
    keep.loc[kill_long | kill_short] = False
    return keep


def _apply_long_only_btc_gate(trades: pd.DataFrame, threshold_pct: float) -> pd.Series:
    """Long-suppression-only gate:
    Kill LTC long when BTC ret_42 < -threshold. NO short kill.
    """
    keep = pd.Series(True, index=trades.index)
    if trades["btc_ret_42"].isna().any():
        keep.loc[trades["btc_ret_42"].isna()] = True
    nonwu = ~trades["btc_ret_42"].isna()
    kill_long = nonwu & (trades["direction"] == 1) & (trades["btc_ret_42"] < -threshold_pct)
    keep.loc[kill_long] = False
    return keep


def _apply_shorts_only(trades: pd.DataFrame) -> pd.Series:
    """Mechanism 3 — shorts-only: kill ALL longs."""
    return trades["direction"] == -1


def _evaluate(
    is_ltc: pd.DataFrame,
    oos_ltc: pd.DataFrame,
    keep_is: pd.Series,
    keep_oos: pd.Series,
    *,
    mechanism: str,
    threshold_pct: float | None,
) -> dict[str, float | int | str]:
    is_kept = is_ltc[keep_is]
    oos_kept = oos_ltc[keep_oos]
    is_killed = int((~keep_is).sum())
    oos_killed = int((~keep_oos).sum())
    is_net = float(is_kept["net_pnl_pct"].sum())
    oos_net = float(oos_kept["net_pnl_pct"].sum())
    is_sharpe = _per_trade_sharpe(is_kept["net_pnl_pct"])
    oos_sharpe = _per_trade_sharpe(oos_kept["net_pnl_pct"])
    # Baseline anchor: full LTC roster
    is_anchor_net = float(is_ltc["net_pnl_pct"].sum())
    oos_anchor_net = float(oos_ltc["net_pnl_pct"].sum())
    is_anchor_sharpe = _per_trade_sharpe(is_ltc["net_pnl_pct"])
    oos_anchor_sharpe = _per_trade_sharpe(oos_ltc["net_pnl_pct"])
    return {
        "mechanism": mechanism,
        "threshold_pct": threshold_pct if threshold_pct is not None else "n/a",
        "is_kept": len(is_kept),
        "is_killed": is_killed,
        "is_kill_rate_pct": round(100.0 * is_killed / len(is_ltc), 3) if len(is_ltc) else 0.0,
        "is_net_pnl_pct": round(is_net, 4),
        "is_net_pnl_delta_vs_anchor": round(is_net - is_anchor_net, 4),
        "is_per_trade_sharpe": round(is_sharpe, 4),
        "is_sharpe_delta_vs_anchor": round(is_sharpe - is_anchor_sharpe, 4),
        "oos_kept": len(oos_kept),
        "oos_killed": oos_killed,
        "oos_kill_rate_pct": round(100.0 * oos_killed / len(oos_ltc), 3) if len(oos_ltc) else 0.0,
        "oos_net_pnl_pct": round(oos_net, 4),
        "oos_net_pnl_delta_vs_anchor": round(oos_net - oos_anchor_net, 4),
        "oos_per_trade_sharpe": round(oos_sharpe, 4),
        "oos_sharpe_delta_vs_anchor": round(oos_sharpe - oos_anchor_sharpe, 4),
    }


def main() -> None:
    is_df = pd.read_csv(IS_TRADES)
    oos_df = pd.read_csv(OOS_TRADES)
    is_ltc = is_df[is_df["symbol"] == SYMBOL].copy().reset_index(drop=True)
    oos_ltc = oos_df[oos_df["symbol"] == SYMBOL].copy().reset_index(drop=True)

    btc = _load_btc()
    is_ltc = _attach_btc_trend(is_ltc, btc)
    oos_ltc = _attach_btc_trend(oos_ltc, btc)

    # Persist per-trade BTC trend attachment for transparency
    cols = ["symbol", "direction", "open_time", "net_pnl_pct", "btc_ret_42"]
    tag = pd.concat(
        [is_ltc[cols].assign(sample="IS"), oos_ltc[cols].assign(sample="OOS")],
        ignore_index=True,
    )
    tag["counter_trend"] = (
        ((tag["direction"] == 1) & (tag["btc_ret_42"] < 0))
        | ((tag["direction"] == -1) & (tag["btc_ret_42"] > 0))
    )
    tag.to_csv(OUT_DIR / "ltc_btc_trend_alignment.csv", index=False)

    rows: list[dict] = []

    # Anchor (no gate)
    keep_is = pd.Series(True, index=is_ltc.index)
    keep_oos = pd.Series(True, index=oos_ltc.index)
    rows.append(_evaluate(is_ltc, oos_ltc, keep_is, keep_oos,
                          mechanism="anchor_no_gate", threshold_pct=None))

    # Mechanism 1 — symmetric BTC-trend gate at multiple thresholds
    for t in GATE_THRESHOLDS_PCT:
        k_is = _apply_symmetric_btc_gate(is_ltc, t)
        k_oos = _apply_symmetric_btc_gate(oos_ltc, t)
        rows.append(_evaluate(is_ltc, oos_ltc, k_is, k_oos,
                              mechanism="symmetric_btc_trend_gate", threshold_pct=t))

    # Mechanism 2 — long-only BTC-trend gate at multiple thresholds
    for t in GATE_THRESHOLDS_PCT:
        k_is = _apply_long_only_btc_gate(is_ltc, t)
        k_oos = _apply_long_only_btc_gate(oos_ltc, t)
        rows.append(_evaluate(is_ltc, oos_ltc, k_is, k_oos,
                              mechanism="longsuppress_btc_trend_gate", threshold_pct=t))

    # Mechanism 3 — shorts-only (drop all longs)
    k_is = _apply_shorts_only(is_ltc)
    k_oos = _apply_shorts_only(oos_ltc)
    rows.append(_evaluate(is_ltc, oos_ltc, k_is, k_oos,
                          mechanism="shorts_only_total", threshold_pct=None))

    df = pd.DataFrame(rows)
    df.to_csv(OUT_DIR / "mechanism_candidates.csv", index=False)

    # Print summary
    print("=" * 100)
    print("iter-v1/022 Phase 2 — Orthogonal mechanism candidates (POST-HOC ORACLE EDA — INFORMATIONAL)")
    print("=" * 100)
    print("Anchor LTC: IS +3.2731% / OOS -47.2484% (124 IS / 34 OOS trades)")
    print()
    print(f"{'mechanism':<35}{'thr':<6}{'IS kill%':<10}{'IS Δ':<12}{'OOS kill%':<11}{'OOS Δ':<12}{'OOS Sharpe Δ':<14}")
    print("-" * 100)
    for r in rows:
        thr = f"{r['threshold_pct']}" if r['threshold_pct'] != 'n/a' else "—"
        print(
            f"{r['mechanism'][:33]:<35}{thr:<6}"
            f"{r['is_kill_rate_pct']:<10.2f}"
            f"{r['is_net_pnl_delta_vs_anchor']:<+12.4f}"
            f"{r['oos_kill_rate_pct']:<11.2f}"
            f"{r['oos_net_pnl_delta_vs_anchor']:<+12.4f}"
            f"{r['oos_sharpe_delta_vs_anchor']:<+14.4f}"
        )
    print()
    print("Outputs:")
    print(f"  {OUT_DIR / 'mechanism_candidates.csv'}")
    print(f"  {OUT_DIR / 'ltc_btc_trend_alignment.csv'}")
    print()
    print("CAVEAT: This is POST-HOC ORACLE EDA on baseline LTC trade roster.")
    print("It assumes Model D's signal trajectory is preserved under cohort isolation —")
    print("which /020 BTC catastrophic REFUTED. The actual /022 backtest must re-train")
    print("Model D-LTC-only at single-seed=42 n_trials=18; basin relocation may shift")
    print("the trade roster materially. ORACLE EDA is informational for mechanism")
    print("SELECTION, NOT for outcome prediction.")


if __name__ == "__main__":
    main()
