"""
iter-v1/089 — BUNDLE-003 ASSEMBLY composition + decision metrics.

BUNDLE-003 candidate = BUNDLE-002 {DOT, ETH, BTC, AAVE} + XRP/088.
Mirrors analysis/iteration_v1-082/compose_bundle_002.py structure; adds:
  - 5th component XRP/088 (standalone specialist run)
  - IS-only weights from weight_calibration.py (weights.json)
  - BTC-trend regime tagging (NON-degenerate; /082 carried a single "N/A" bucket)
  - Deflated Sharpe Ratio (single-config bundle, N_eff=1)
  - BUNDLE-002 vs BUNDLE-003 head-to-head (headline + per-regime Pareto)
  - Falsifier (a): cross-track v2-overlap — XRP share of BUNDLE-003 PnL/notional
  - Falsifier (b): regime-conditionality — XRP incremental OOS Sharpe with vs
    without XRP's post-Nov-2025 months

Components (pairwise-disjoint coin universe; HARD Check 16):
  DOT  = /063 (from /082 partition)   owns {DOTUSDT}
  ETH  = /064 (from /082 partition)   owns {ETHUSDT}
  BTC  = /065 (from /082 partition)   owns {BTCUSDT}
  AAVE = /078 (from /082 partition)   owns {AAVEUSDT}
  XRP  = /088 (standalone)            owns {XRPUSDT}

Backtest-live parity (HARD Check 15): the bundle is the UNION of the 5 component
trade streams with NO post-hoc netting/aggregation. A weight w_c is a deterministic
multiplier on component c's per-trade net_pnl_pct, identical in backtest and live.

DECISION (read-only on OOS until the metrics block). MERGE RULE
(feedback_v1_merge_relative_regime_pareto): BUNDLE-003 becomes baseline iff it is
Pareto-better-or-equal vs BUNDLE-002 on EVERY tagged regime (within sigma_R) AND
strictly better on >=1 regime AND methodology intact.
"""

from __future__ import annotations

import csv
import datetime
import json
import math
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
REPORTS = REPO / "reports-v1"
ANALYSIS = REPO / "analysis" / "iteration_v1-089"
OUT_DIR = REPORTS / "iteration_v1-089"
WEIGHTS_JSON = ANALYSIS / "weights.json"
BTC_KLINES = REPO / "data" / "BTCUSDT" / "8h.csv"

OOS_CUTOFF = datetime.date(2025, 3, 24)  # sacred constant
POST_NOV = datetime.date(2025, 11, 1)  # falsifier (b) boundary

# BUNDLE-002 incumbent components (from /082 partition) + XRP/088.
COMPONENTS = [
    ("DOT", "iteration_v1-082", "DOTUSDT"),
    ("ETH", "iteration_v1-082", "ETHUSDT"),
    ("BTC", "iteration_v1-082", "BTCUSDT"),
    ("AAVE", "iteration_v1-082", "AAVEUSDT"),
    ("XRP", "iteration_v1-088", "XRPUSDT"),
]
# BUNDLE-002 = first 4 components only (the incumbent baseline to beat).
BUNDLE_002_NAMES = {"DOT", "ETH", "BTC", "AAVE"}

# BUNDLE-002 published headline (validated reproduction): IS +0.7157 / OOS +1.0043
B2_IS_SHARPE = 0.7157
B2_OOS_SHARPE = 1.0043


# ---------------------------------------------------------------------------
# Generic metric helpers (mirror /082)
# ---------------------------------------------------------------------------
def monthly_sharpe(monthly_returns: list[float]) -> float:
    if len(monthly_returns) < 2:
        return float("nan")
    m = sum(monthly_returns) / len(monthly_returns)
    var = sum((r - m) ** 2 for r in monthly_returns) / (len(monthly_returns) - 1)
    s = math.sqrt(var) if var > 0 else 0.0
    return (m / s) * math.sqrt(12) if s > 0 else float("nan")


def per_trade_sharpe(pnl_list: list[float]) -> float:
    if len(pnl_list) < 2:
        return float("nan")
    m = sum(pnl_list) / len(pnl_list)
    var = sum((p - m) ** 2 for p in pnl_list) / len(pnl_list)
    s = math.sqrt(var) if var > 0 else 0.0
    return m / s if s > 0 else float("nan")


def max_drawdown_pct(pnl_ordered: list[float]) -> float:
    equity = 100.0
    peak = equity
    max_dd = 0.0
    for r in pnl_ordered:
        equity += r
        if equity > peak:
            peak = equity
        dd = (peak - equity) / peak * 100.0 if peak > 0 else 0.0
        if dd > max_dd:
            max_dd = dd
    return max_dd


def deflated_sharpe(sr_obs: float, pnl_list: list[float], n_trials: int = 1) -> float:
    """Deflated Sharpe Ratio (Bailey & Lopez de Prado 2014).

    sr_obs = observed per-trade Sharpe; T = trade count; skew/kurt from pnl_list.
    For a single pre-registered bundle config N_eff = n_trials = 1, so the
    expected-max-SR haircut is 0 and DSR reduces to PSR vs benchmark 0.
    """
    t = len(pnl_list)
    if t < 3 or math.isnan(sr_obs):
        return float("nan")
    m = sum(pnl_list) / t
    var = sum((p - m) ** 2 for p in pnl_list) / t
    sd = math.sqrt(var) if var > 0 else 0.0
    if sd == 0:
        return float("nan")
    skew = sum(((p - m) / sd) ** 3 for p in pnl_list) / t
    kurt = sum(((p - m) / sd) ** 4 for p in pnl_list) / t
    # Expected max Sharpe over n_trials independent trials (=0 when n=1).
    if n_trials > 1:
        import statistics

        e = 0.5772156649
        z1 = statistics.NormalDist().inv_cdf(1 - 1.0 / n_trials)
        z2 = statistics.NormalDist().inv_cdf(1 - 1.0 / (n_trials * math.e))
        sr_star = (1 - e) * z1 + e * z2  # in per-trade Sharpe units (benchmark std ~ approx 1)
        sr_star = sr_star / math.sqrt(t)  # scale to per-trade SR sampling std
    else:
        sr_star = 0.0
    denom = math.sqrt(1 - skew * sr_obs + (kurt - 1) / 4.0 * sr_obs**2)
    if denom <= 0:
        return float("nan")
    z = (sr_obs - sr_star) * math.sqrt(t - 1) / denom
    return statistics_normal_cdf(z)


def statistics_normal_cdf(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def ms_to_month(ms: int) -> str:
    return datetime.datetime.fromtimestamp(ms / 1000, datetime.UTC).strftime("%Y-%m")


def ms_to_date(ms: int) -> datetime.date:
    return datetime.datetime.fromtimestamp(ms / 1000, datetime.UTC).date()


# ---------------------------------------------------------------------------
# BTC-trend regime tagging — IS-computable, lagged (uses only data < entry).
# Regime at a trade's open_time = sign of BTC's trailing 30x8h (=10-day) return,
# evaluated on BTC closes STRICTLY BEFORE the trade's open_time (no look-ahead).
#   ret >  +THRESH -> BTC_UP
#   ret <  -THRESH -> BTC_DOWN
#   else           -> BTC_FLAT
# ---------------------------------------------------------------------------
REGIME_LOOKBACK = 30  # 30 x 8h candles = 10 days
REGIME_THRESH = 0.05  # +/-5% over 10 days


def load_btc_closes() -> list[tuple[int, float]]:
    """Return [(close_time_ms, close_px), ...] sorted ascending. close_time is the
    candle's CLOSE timestamp — only candles whose close < trade open_time are usable
    (a candle that has not closed by entry time is not knowable)."""
    out = []
    with open(BTC_KLINES) as fh:
        for row in csv.DictReader(fh):
            out.append((int(row["close_time"]), float(row["close"])))
    out.sort()
    return out


def build_regime_tagger(btc: list[tuple[int, float]]):
    times = [t for t, _ in btc]
    closes = [c for _, c in btc]
    import bisect

    def tag(open_time_ms: int) -> str:
        # Last BTC candle that has CLOSED strictly before this trade's entry.
        idx = bisect.bisect_left(times, open_time_ms) - 1
        if idx < REGIME_LOOKBACK:
            return "BTC_FLAT"  # not enough history -> neutral
        now = closes[idx]
        past = closes[idx - REGIME_LOOKBACK]
        if past <= 0:
            return "BTC_FLAT"
        ret = (now - past) / past
        if ret > REGIME_THRESH:
            return "BTC_UP"
        if ret < -REGIME_THRESH:
            return "BTC_DOWN"
        return "BTC_FLAT"

    return tag


# ---------------------------------------------------------------------------
# Load a component's trades for a window, apply weight, tag regime.
# Each trade row gets:
#   net  = float(net_pnl_pct) * weight_c   (component-weighted contribution)
#   month, regime
# IS/OOS re-split on strict close-day rule.
# ---------------------------------------------------------------------------
def load_component(run_dir: str, symbol: str, weight: float, tagger) -> list[dict]:
    path = REPORTS / run_dir  # both in_sample + out_of_sample read, re-split below
    rows = []
    for window in ("in_sample", "out_of_sample"):
        fpath = path / window / "trades.csv"
        with open(fpath) as fh:
            for r in csv.DictReader(fh):
                if r["symbol"] != symbol:
                    continue
                open_ms = int(r["open_time"])
                close_ms = int(r["close_time"])
                close_d = ms_to_date(close_ms)
                rows.append(
                    {
                        "symbol": symbol,
                        "open_time": open_ms,
                        "close_time": close_ms,
                        "net": float(r["net_pnl_pct"]) * weight,
                        "net_raw": float(r["net_pnl_pct"]),
                        "weight": weight,
                        "month": ms_to_month(close_ms),
                        "is_oos": "OOS" if close_d >= OOS_CUTOFF else "IS",
                        "regime": tagger(open_ms),
                        "close_date": close_d,
                    }
                )
    return rows


def window_metrics(trades: list[dict]) -> dict:
    if not trades:
        return {"n": 0}
    pnl = [t["net"] for t in trades]
    monthly = defaultdict(float)
    for t in trades:
        monthly[t["month"]] += t["net"]
    monthly_vals = list(monthly.values())
    by_close = sorted(trades, key=lambda t: t["close_time"])
    mdd = max_drawdown_pct([t["net"] for t in by_close])
    pts = per_trade_sharpe(pnl)
    return {
        "n": len(trades),
        "total_pnl": sum(pnl),
        "monthly_sharpe": monthly_sharpe(monthly_vals),
        "per_trade_sharpe": pts,
        "max_dd_pct": mdd,
        "n_months": len(monthly),
        "monthly": dict(monthly),
        "dsr": deflated_sharpe(pts, pnl, n_trials=1),
        "win_rate": sum(1 for p in pnl if p > 0) / len(pnl) * 100,
    }


def per_symbol_pnl(trades: list[dict]) -> dict[str, float]:
    d = defaultdict(float)
    for t in trades:
        d[t["symbol"]] += t["net"]
    return dict(d)


def per_regime_sharpe(trades: list[dict]) -> dict[str, dict]:
    """Per-regime monthly Sharpe + total PnL + trade count."""
    byreg: dict[str, list[dict]] = defaultdict(list)
    for t in trades:
        byreg[t["regime"]].append(t)
    out = {}
    for reg, rows in byreg.items():
        monthly = defaultdict(float)
        for t in rows:
            monthly[t["month"]] += t["net"]
        out[reg] = {
            "sharpe": monthly_sharpe(list(monthly.values())),
            "total_pnl": sum(t["net"] for t in rows),
            "n": len(rows),
            "n_months": len(monthly),
        }
    return out


def top_symbol_concentration(trades: list[dict]) -> tuple[str, float]:
    """N-aware top-symbol concentration (H3 fix): denom = max(total, sum_positives)."""
    ps = per_symbol_pnl(trades)
    total = sum(ps.values())
    sum_pos = sum(v for v in ps.values() if v > 0)
    if not ps:
        return ("", 0.0)
    top_sym = max(ps, key=lambda s: ps[s])
    denom = max(total, sum_pos)
    conc = ps[top_sym] / denom * 100 if denom != 0 else 0.0
    return (top_sym, conc)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    print("=== BUNDLE-003 ASSEMBLY — iter-v1/089 ===\n")
    weights_payload = json.loads(WEIGHTS_JSON.read_text())
    eq_w = weights_payload["equal_weights"]
    rp_w = weights_payload["rp_weights"]

    btc = load_btc_closes()
    tagger = build_regime_tagger(btc)
    print(f"Loaded {len(btc)} BTC 8h candles for regime tagging "
          f"(lookback={REGIME_LOOKBACK}x8h, thresh=+/-{REGIME_THRESH:.0%})\n")

    # ---- Build the 5 components under EQUAL weight (PRIMARY, mirrors /082) ----
    comp_eq: dict[str, list[dict]] = {}
    for name, run_dir, sym in COMPONENTS:
        comp_eq[name] = load_component(run_dir, sym, eq_w[name], tagger)

    # Pairwise-disjoint assertion (HARD Check 16)
    sym_owner: dict[str, str] = {}
    for name, _, sym in COMPONENTS:
        syms = {t["symbol"] for t in comp_eq[name]}
        assert syms == {sym}, f"DISJOINT VIOLATION: {name} owns {syms}, expected {{{sym}}}"
        for s in syms:
            assert s not in sym_owner, f"OVERLAP: {s} owned by {sym_owner[s]} and {name}"
            sym_owner[s] = name
    print("[PASS] Pairwise-disjoint coin universe (Check 16): "
          + ", ".join(f"{n}->{s}" for n, _, s in COMPONENTS) + "\n")

    # ---- BUNDLE-003 (5 comp) and BUNDLE-002 (4 comp) union streams ----
    b3_all = [t for name in comp_eq for t in comp_eq[name]]
    b2_all = [t for name in comp_eq if name in BUNDLE_002_NAMES for t in comp_eq[name]]

    b3_is = [t for t in b3_all if t["is_oos"] == "IS"]
    b3_oos = [t for t in b3_all if t["is_oos"] == "OOS"]
    b2_is = [t for t in b2_all if t["is_oos"] == "IS"]
    b2_oos = [t for t in b2_all if t["is_oos"] == "OOS"]

    b3_is_m = window_metrics(b3_is)
    b3_oos_m = window_metrics(b3_oos)
    b2_is_m = window_metrics(b2_is)
    b2_oos_m = window_metrics(b2_oos)

    # ---- Headline comparison ----
    print("=== HEADLINE: BUNDLE-003 vs BUNDLE-002 (equal weight, net_pnl_pct) ===")
    print(f"{'metric':<26}{'B2 (4)':>12}{'B3 (5)':>12}{'delta':>10}")

    def row(label, a, b):
        d = b - a if not (math.isnan(a) or math.isnan(b)) else float("nan")
        print(f"{label:<26}{a:>12.4f}{b:>12.4f}{d:>10.4f}")

    row("IS monthly Sharpe", b2_is_m["monthly_sharpe"], b3_is_m["monthly_sharpe"])
    row("OOS monthly Sharpe", b2_oos_m["monthly_sharpe"], b3_oos_m["monthly_sharpe"])
    row("IS total PnL %", b2_is_m["total_pnl"], b3_is_m["total_pnl"])
    row("OOS total PnL %", b2_oos_m["total_pnl"], b3_oos_m["total_pnl"])
    row("IS MaxDD %", b2_is_m["max_dd_pct"], b3_is_m["max_dd_pct"])
    row("OOS MaxDD %", b2_oos_m["max_dd_pct"], b3_oos_m["max_dd_pct"])
    print(f"{'IS trades':<26}{b2_is_m['n']:>12}{b3_is_m['n']:>12}")
    print(f"{'OOS trades':<26}{b2_oos_m['n']:>12}{b3_oos_m['n']:>12}")
    print(f"{'OOS DSR (N_eff=1)':<26}{b2_oos_m['dsr']:>12.4f}{b3_oos_m['dsr']:>12.4f}")

    # ---- Concentration ----
    b3_top_sym, b3_conc = top_symbol_concentration(b3_oos)
    b2_top_sym, b2_conc = top_symbol_concentration(b2_oos)
    print("\nTop-symbol OOS concentration:")
    print(f"  BUNDLE-002: {b2_top_sym} = {b2_conc:.2f}%")
    print(f"  BUNDLE-003: {b3_top_sym} = {b3_conc:.2f}%   (gate <=30%)")

    # ---- Per-specialist OOS trade-rate floor (>=50/specialist) ----
    print("\n=== Per-specialist OOS trade counts (floor >= 50) ===")
    oos_months_span = 0
    for name, _, sym in COMPONENTS:
        oos_n = sum(1 for t in comp_eq[name] if t["is_oos"] == "OOS")
        oos_ms = len({t["month"] for t in comp_eq[name] if t["is_oos"] == "OOS"})
        oos_months_span = max(oos_months_span, oos_ms)
        flag = "OK" if oos_n >= 50 else ("WATCH(30-49)" if oos_n >= 30 else "REJECT(<30)")
        print(f"  {name:<4} {sym:<9} OOS_trades={oos_n:>3}  OOS_months={oos_ms:>2}  [{flag}]")
    print(f"  BUNDLE-003 OOS total = {b3_oos_m['n']} trades over ~{oos_months_span} months "
          f"({b3_oos_m['n'] / max(oos_months_span, 1):.1f}/mo)")

    # ---- Per-regime Pareto comparison ----
    print("\n=== PER-REGIME monthly Sharpe (BTC-trend tag) — Pareto comparison ===")
    b2_reg_is = per_regime_sharpe(b2_is)
    b3_reg_is = per_regime_sharpe(b3_is)
    b2_reg_oos = per_regime_sharpe(b2_oos)
    b3_reg_oos = per_regime_sharpe(b3_oos)
    regimes = ["BTC_UP", "BTC_FLAT", "BTC_DOWN"]

    def reg_block(label, b2r, b3r):
        print(f"\n  -- {label} --")
        print(f"  {'regime':<10}{'B2_Sharpe':>11}{'B3_Sharpe':>11}{'delta':>9}"
              f"{'B2_n':>6}{'B3_n':>6}")
        pareto_ok = True
        strictly_better = False
        for reg in regimes:
            b2s = b2r.get(reg, {}).get("sharpe", float("nan"))
            b3s = b3r.get(reg, {}).get("sharpe", float("nan"))
            b2n = b2r.get(reg, {}).get("n", 0)
            b3n = b3r.get(reg, {}).get("n", 0)
            delta = (b3s - b2s) if not (math.isnan(b2s) or math.isnan(b3s)) else float("nan")
            print(f"  {reg:<10}{b2s:>11.4f}{b3s:>11.4f}{delta:>9.4f}{b2n:>6}{b3n:>6}")
        return pareto_ok, strictly_better

    reg_block("IN-SAMPLE", b2_reg_is, b3_reg_is)
    reg_block("OUT-OF-SAMPLE", b2_reg_oos, b3_reg_oos)

    # Pareto verdict on OOS regimes with a sigma_R tolerance band.
    # sigma_R approx = per-regime Sharpe sampling SE ~ sqrt((1+0.5*S^2)/n_months)*sqrt(12).
    print("\n  -- OOS Pareto verdict (tolerance band sigma_R per regime) --")
    pareto_better_equal = True
    strictly_better_somewhere = False
    for reg in regimes:
        b2s = b2_reg_oos.get(reg, {}).get("sharpe", float("nan"))
        b3s = b3_reg_oos.get(reg, {}).get("sharpe", float("nan"))
        nm = b3_reg_oos.get(reg, {}).get("n_months", 0)
        if math.isnan(b2s) and math.isnan(b3s):
            continue
        # sampling SE of an annualized monthly Sharpe
        s_for_se = b3s if not math.isnan(b3s) else 0.0
        sigma_r = (
            math.sqrt((1 + 0.5 * (s_for_se / math.sqrt(12)) ** 2) / nm) * math.sqrt(12)
            if nm >= 2
            else float("inf")
        )
        delta = (b3s - b2s) if not (math.isnan(b2s) or math.isnan(b3s)) else float("nan")
        verdict = "n/a"
        if not math.isnan(delta):
            if delta >= -sigma_r:
                verdict = "WITHIN/BETTER"
                if delta > sigma_r:
                    strictly_better_somewhere = True
                    verdict = "STRICTLY BETTER"
            else:
                verdict = "WORSE (>sigma_R)"
                pareto_better_equal = False
        print(f"  {reg:<10} delta={delta:>8.4f}  sigma_R={sigma_r:>7.4f}  -> {verdict}")

    pareto_dominates = pareto_better_equal and strictly_better_somewhere

    # ---- FALSIFIER (a): cross-track v2-overlap — XRP share of B3 ----
    print("\n=== FALSIFIER (a): XRP cross-track (v2-live) exposure share ===")
    xrp_oos_pnl = sum(t["net"] for t in b3_oos if t["symbol"] == "XRPUSDT")
    xrp_is_pnl = sum(t["net"] for t in b3_is if t["symbol"] == "XRPUSDT")
    b3_oos_total = b3_oos_m["total_pnl"]
    b3_is_total = b3_is_m["total_pnl"]
    # Notional share proxy: each component is equal-weighted, so XRP notional
    # share = (#components active) ^-1 on co-trading days. As a simple static
    # proxy report XRP's share of total weighted exposure = w_XRP / sum(w).
    notional_share = eq_w["XRP"] / sum(eq_w.values()) * 100
    xrp_oos_pnl_share = xrp_oos_pnl / b3_oos_total * 100 if b3_oos_total != 0 else float("nan")
    xrp_is_pnl_share = xrp_is_pnl / b3_is_total * 100 if b3_is_total != 0 else float("nan")
    print(f"  XRP notional share of BUNDLE-003 (equal weight) : {notional_share:.2f}%")
    print(f"  XRP IS  PnL share  : {xrp_is_pnl_share:.2f}%  (XRP IS  PnL={xrp_is_pnl:.3f}%)")
    print(f"  XRP OOS PnL share  : {xrp_oos_pnl_share:.2f}%  (XRP OOS PnL={xrp_oos_pnl:.3f}%)")
    print("  NOTE: XRPUSDT is also a v2-live symbol. Combined v1(BUNDLE-003)+v2")
    print("        XRP exposure must be reconciled in the DEPLOY PARITY AUDIT.")
    print("        Informational for v1-assembly; NOT an assembly blocker.")

    # ---- FALSIFIER (b): regime-conditionality of XRP incremental OOS ----
    print("\n=== FALSIFIER (b): XRP incremental OOS Sharpe — temporal complementarity ===")
    # Incremental = B3_OOS_Sharpe - B2_OOS_Sharpe (full OOS).
    incr_full = b3_oos_m["monthly_sharpe"] - b2_oos_m["monthly_sharpe"]
    # Recompute B3 OOS EXCLUDING XRP's post-Nov-2025 months (drop XRP trades that
    # close >= 2025-11-01; keep all incumbent trades and pre-Nov XRP trades).
    b3_oos_ex_postnov = [
        t
        for t in b3_oos
        if not (t["symbol"] == "XRPUSDT" and t["close_date"] >= POST_NOV)
    ]
    b3_oos_ex_m = window_metrics(b3_oos_ex_postnov)
    incr_ex_postnov = b3_oos_ex_m["monthly_sharpe"] - b2_oos_m["monthly_sharpe"]
    xrp_postnov_n = sum(
        1 for t in b3_oos if t["symbol"] == "XRPUSDT" and t["close_date"] >= POST_NOV
    )
    xrp_prenov_n = sum(
        1 for t in b3_oos if t["symbol"] == "XRPUSDT" and t["close_date"] < POST_NOV
    )
    xrp_postnov_pnl = sum(
        t["net"] for t in b3_oos if t["symbol"] == "XRPUSDT" and t["close_date"] >= POST_NOV
    )
    xrp_prenov_pnl = sum(
        t["net"] for t in b3_oos if t["symbol"] == "XRPUSDT" and t["close_date"] < POST_NOV
    )
    print(f"  B2 OOS Sharpe                         : {b2_oos_m['monthly_sharpe']:.4f}")
    print(f"  B3 OOS Sharpe (full)                  : {b3_oos_m['monthly_sharpe']:.4f}")
    print(f"  B3 OOS Sharpe (XRP post-Nov excluded) : {b3_oos_ex_m['monthly_sharpe']:.4f}")
    print(f"  XRP incremental OOS Sharpe (full)     : {incr_full:+.4f}")
    print(f"  XRP incremental OOS Sharpe (pre-Nov)  : {incr_ex_postnov:+.4f}")
    print(f"  XRP OOS trades  pre-Nov={xrp_prenov_n} (PnL {xrp_prenov_pnl:+.3f}%) "
          f"| post-Nov={xrp_postnov_n} (PnL {xrp_postnov_pnl:+.3f}%)")
    if incr_full > 0 and incr_ex_postnov <= 0:
        print("  FLAG: XRP's OOS contribution is REGIME-CONTINGENT on post-Nov-2025.")
    elif incr_full > 0 and incr_ex_postnov > 0:
        print("  XRP contribution is TEMPORALLY BROAD (helps both pre- and post-Nov).")
    else:
        print("  XRP does not raise OOS Sharpe in either window.")

    # ---- Risk-parity robustness pass (SECONDARY) ----
    comp_rp = {}
    for name, run_dir, sym in COMPONENTS:
        comp_rp[name] = load_component(run_dir, sym, rp_w[name], tagger)
    b3_rp_oos = [t for name in comp_rp for t in comp_rp[name] if t["is_oos"] == "OOS"]
    b3_rp_is = [t for name in comp_rp for t in comp_rp[name] if t["is_oos"] == "IS"]
    b3_rp_oos_m = window_metrics(b3_rp_oos)
    b3_rp_is_m = window_metrics(b3_rp_is)
    print("\n=== ROBUSTNESS: BUNDLE-003 under inverse-IS-vol (risk-parity) weights ===")
    print(f"  IS  monthly Sharpe (RP): {b3_rp_is_m['monthly_sharpe']:.4f} "
          f"(equal: {b3_is_m['monthly_sharpe']:.4f})")
    print(f"  OOS monthly Sharpe (RP): {b3_rp_oos_m['monthly_sharpe']:.4f} "
          f"(equal: {b3_oos_m['monthly_sharpe']:.4f})")

    # ---- Final verdict block ----
    print("\n" + "=" * 64)
    print("VERDICT SUMMARY")
    print("=" * 64)
    raises_oos = b3_oos_m["monthly_sharpe"] >= b2_oos_m["monthly_sharpe"]
    conc_ok = b3_conc <= 30.0
    xrp_floor_ok = sum(1 for t in comp_eq["XRP"] if t["is_oos"] == "OOS") >= 50
    print(f"  B3 OOS Sharpe {b3_oos_m['monthly_sharpe']:.4f} vs B2 {b2_oos_m['monthly_sharpe']:.4f}"
          f"  -> raises/holds: {raises_oos}")
    print(f"  Top-symbol concentration {b3_conc:.2f}% <= 30%: {conc_ok} ({b3_top_sym})")
    print(f"  XRP OOS trade floor >= 50: {xrp_floor_ok}")
    print(f"  OOS per-regime Pareto-better-or-equal everywhere: {pareto_better_equal}")
    print(f"  OOS strictly-better on >=1 regime: {strictly_better_somewhere}")
    print(f"  => PARETO-DOMINATES BUNDLE-002: {pareto_dominates}")

    # Persist machine-readable summary for the diary/Critic.
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    summary = {
        "bundle_002": {
            "is_sharpe": b2_is_m["monthly_sharpe"],
            "oos_sharpe": b2_oos_m["monthly_sharpe"],
            "is_trades": b2_is_m["n"],
            "oos_trades": b2_oos_m["n"],
            "oos_top_sym": b2_top_sym,
            "oos_concentration_pct": b2_conc,
        },
        "bundle_003": {
            "is_sharpe": b3_is_m["monthly_sharpe"],
            "oos_sharpe": b3_oos_m["monthly_sharpe"],
            "is_dsr": b3_is_m["dsr"],
            "oos_dsr": b3_oos_m["dsr"],
            "is_trades": b3_is_m["n"],
            "oos_trades": b3_oos_m["n"],
            "is_total_pnl": b3_is_m["total_pnl"],
            "oos_total_pnl": b3_oos_m["total_pnl"],
            "is_maxdd_pct": b3_is_m["max_dd_pct"],
            "oos_maxdd_pct": b3_oos_m["max_dd_pct"],
            "oos_top_sym": b3_top_sym,
            "oos_concentration_pct": b3_conc,
            "oos_sharpe_rp_weights": b3_rp_oos_m["monthly_sharpe"],
            "is_sharpe_rp_weights": b3_rp_is_m["monthly_sharpe"],
        },
        "per_regime_oos": {
            reg: {
                "b2_sharpe": b2_reg_oos.get(reg, {}).get("sharpe"),
                "b3_sharpe": b3_reg_oos.get(reg, {}).get("sharpe"),
                "b2_n": b2_reg_oos.get(reg, {}).get("n", 0),
                "b3_n": b3_reg_oos.get(reg, {}).get("n", 0),
            }
            for reg in regimes
        },
        "falsifier_a_xrp_share": {
            "notional_share_pct": notional_share,
            "is_pnl_share_pct": xrp_is_pnl_share,
            "oos_pnl_share_pct": xrp_oos_pnl_share,
            "note": "XRPUSDT also v2-live; reconcile combined exposure in deploy parity audit",
        },
        "falsifier_b_regime_conditionality": {
            "incr_full": incr_full,
            "incr_ex_postnov": incr_ex_postnov,
            "xrp_oos_prenov_n": xrp_prenov_n,
            "xrp_oos_postnov_n": xrp_postnov_n,
            "xrp_oos_prenov_pnl": xrp_prenov_pnl,
            "xrp_oos_postnov_pnl": xrp_postnov_pnl,
            "regime_contingent": bool(incr_full > 0 and incr_ex_postnov <= 0),
        },
        "verdict": {
            "raises_or_holds_oos": raises_oos,
            "concentration_ok": conc_ok,
            "xrp_floor_ok": xrp_floor_ok,
            "pareto_better_equal_all_regimes": pareto_better_equal,
            "strictly_better_somewhere": strictly_better_somewhere,
            "pareto_dominates_bundle_002": pareto_dominates,
        },
    }
    (OUT_DIR / "bundle_003_summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print(f"\nWrote summary: {OUT_DIR / 'bundle_003_summary.json'}")

    # Also write composed bundle trade files (union, sorted by open_time) for parity.
    b3_all_sorted = sorted(b3_all, key=lambda t: t["open_time"])
    for window, subset in (("in_sample", b3_is), ("out_of_sample", b3_oos)):
        wdir = OUT_DIR / window
        wdir.mkdir(parents=True, exist_ok=True)
        with open(wdir / "trades.csv", "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["symbol", "open_time", "close_time", "net_weighted", "net_raw",
                        "weight", "month", "regime"])
            for t in sorted(subset, key=lambda x: x["open_time"]):
                w.writerow([t["symbol"], t["open_time"], t["close_time"],
                            f"{t['net']:.6f}", f"{t['net_raw']:.6f}", f"{t['weight']:.4f}",
                            t["month"], t["regime"]])
    print(f"Wrote composed trades: {OUT_DIR}/in_sample/trades.csv + out_of_sample/trades.csv")
    print(f"  (union of {len(b3_all_sorted)} component trades, no post-hoc netting — Check 15)")


if __name__ == "__main__":
    main()
