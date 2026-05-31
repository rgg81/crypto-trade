"""EDA for iter-v1/039 — per-symbol drawdown BINARY KILL brake.

Mechanism under study:
    For each symbol, maintain a per-symbol cumulative net_pnl_pct series at
    bar cadence (8h). Compute rolling-30d realized drawdown:
        peak_30d = max of cum_pnl over trailing ~90 bars (30 days at 8h)
        dd = peak_30d - cum_pnl
    When dd > threshold_sym  -> brake ON: skip ALL new entries on that symbol.
    Brake OFF when dd < threshold_sym * recovery_factor (default 0.5).

EDA goal:
    1. Per-symbol distribution of rolling-30d realized DD (percentile table)
    2. Recommended threshold per symbol (75th percentile of trailing-DD)
    3. Bucket IS trades by DD-status-at-entry decile -> net PnL per decile.
       Mechanism load-bearing check: are skipped trades (top deciles) more
       negative than retained?
    4. Trade-impact prediction: how many trades skipped at the recommended threshold?
    5. Recovery oscillation test: ON/OFF transitions per symbol with recovery=0.5
    6. STATEFUL deadlock risk assessment (no-trade equilibrium).

Bar cadence: 8h. 30 days = 90 bars. Trailing window for peak = 90 bars.

Data source: IS roster (open_time as 8h-bar boundary). We reconstruct per-symbol
cum_pnl on a SYNTHETIC 8h grid spanning the IS window:
    - Initialize cum_pnl_sym(t) = 0 at IS start.
    - Each closed trade contributes weighted_pnl to cum_pnl_sym at close_time.
    - Between trade closes the curve is flat (no mark-to-market; this is the
      same ORACLE-baseline-roster simplification flagged in the brief).

Critical caveat (STATEFUL): this EDA is ORACLE on the realized roster -- it
does NOT close the loop. Stateful deadlock risk is addressed separately in
brief Section 2.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from statistics import median

REPO = Path("/home/roberto/crypto-trade/.worktrees/quant-research")
TRADES_CSV = REPO / "reports-v1/iteration_v1-baseline/in_sample/trades.csv"
OUT_DIR = REPO / "analysis/iteration_v1-039"
OUT_DIR.mkdir(parents=True, exist_ok=True)

BAR_MS = 8 * 60 * 60 * 1000  # 8h in ms
WINDOW_BARS = 90  # 30 days at 8h cadence
RECOVERY_FACTOR = 0.5

UNIVERSE = ("BTCUSDT", "ETHUSDT", "LINKUSDT", "LTCUSDT", "DOTUSDT")
PERCENTILES = (50, 75, 85, 90, 95, 99)


def percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    if len(s) == 1:
        return s[0]
    k = (len(s) - 1) * (q / 100.0)
    f = int(k)
    c = min(f + 1, len(s) - 1)
    if f == c:
        return s[f]
    return s[f] + (s[c] - s[f]) * (k - f)


def load_trades() -> list[dict]:
    rows: list[dict] = []
    with TRADES_CSV.open() as f:
        reader = csv.DictReader(f)
        for r in reader:
            r["open_time"] = int(r["open_time"])
            r["close_time"] = int(r["close_time"])
            r["weighted_pnl"] = float(r["weighted_pnl"])
            r["net_pnl_pct"] = float(r["net_pnl_pct"])
            rows.append(r)
    return rows


def build_pnl_curves(trades: list[dict]) -> dict[str, tuple[list[int], list[float]]]:
    """Build per-symbol bar-cadence cum_pnl curve over IS window.

    Returns dict: symbol -> (bar_times, cum_pnls).
    At each bar, cum_pnl is the sum of weighted_pnl from all trades CLOSED at
    or before that bar's close.
    """
    if not trades:
        return {}

    is_start = min(t["open_time"] for t in trades)
    is_end = max(t["close_time"] for t in trades)
    # Align to bar boundaries
    start_bar = (is_start // BAR_MS) * BAR_MS
    end_bar = ((is_end // BAR_MS) + 1) * BAR_MS

    bar_times: list[int] = []
    t = start_bar
    while t <= end_bar:
        bar_times.append(t)
        t += BAR_MS

    curves: dict[str, tuple[list[int], list[float]]] = {}
    for sym in UNIVERSE:
        sym_trades = sorted(
            [tr for tr in trades if tr["symbol"] == sym],
            key=lambda r: r["close_time"],
        )
        cum = 0.0
        cum_series: list[float] = []
        ti = 0  # pointer into sym_trades
        for bar in bar_times:
            while ti < len(sym_trades) and sym_trades[ti]["close_time"] <= bar:
                cum += sym_trades[ti]["weighted_pnl"]
                ti += 1
            cum_series.append(cum)
        curves[sym] = (bar_times, cum_series)
    return curves


def rolling_dd(cum: list[float], window: int) -> list[float]:
    """Rolling peak-to-current drawdown over trailing `window` bars.

    dd[i] = max(cum[max(0, i-window+1):i+1]) - cum[i]
    """
    dd = [0.0] * len(cum)
    for i in range(len(cum)):
        lo = max(0, i - window + 1)
        peak = max(cum[lo : i + 1])
        dd[i] = peak - cum[i]
    return dd


def find_bar_index(bar_times: list[int], t: int) -> int:
    """Index of the bar whose close_time is the LATEST <= t.

    Used for DD-status-at-entry lookup: the brake decision at open_time t
    uses information from the most recent CLOSED bar.
    """
    # Binary search
    lo, hi = 0, len(bar_times) - 1
    if t < bar_times[0]:
        return 0
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if bar_times[mid] <= t:
            lo = mid
        else:
            hi = mid - 1
    return lo


def simulate_brake(
    dd_series: list[float], threshold: float, recovery_factor: float
) -> tuple[list[bool], int]:
    """Simulate the binary brake.

    Returns (brake_on_per_bar, n_transitions).
    Brake state machine:
      - Initially OFF.
      - If brake OFF and dd > threshold: turn ON.
      - If brake ON  and dd < threshold * recovery_factor: turn OFF.
    """
    on_series: list[bool] = [False] * len(dd_series)
    on = False
    transitions = 0
    recover = threshold * recovery_factor
    for i, d in enumerate(dd_series):
        if not on and d > threshold:
            on = True
            transitions += 1
        elif on and d < recover:
            on = False
            transitions += 1
        on_series[i] = on
    return on_series, transitions


def main() -> None:
    trades = load_trades()
    print(f"[load] {len(trades)} IS trades")
    is_start = min(t["open_time"] for t in trades)
    is_end = max(t["close_time"] for t in trades)
    print(f"[load] IS span: {is_start} -> {is_end} ({(is_end - is_start) / BAR_MS / 90:.1f} months)")

    curves = build_pnl_curves(trades)

    # --- Per-symbol DD percentile table ---
    pct_rows = []  # (sym, p50, p75, p85, p90, p95, p99, n_bars, max_dd)
    dd_by_sym: dict[str, tuple[list[int], list[float]]] = {}
    for sym in UNIVERSE:
        bar_times, cum = curves[sym]
        dd = rolling_dd(cum, WINDOW_BARS)
        dd_by_sym[sym] = (bar_times, dd)
        ps = [percentile(dd, q) for q in PERCENTILES]
        pct_rows.append((sym, *ps, len(dd), max(dd) if dd else 0.0))
        print(
            f"[dd-pctile] {sym}: "
            + ", ".join(f"p{q}={p:.3f}%" for q, p in zip(PERCENTILES, ps))
            + f", n_bars={len(dd)}, max_dd={max(dd):.3f}%"
        )

    # --- Recommended thresholds (75th percentile per symbol) ---
    print("\n[threshold] Recommended threshold = 75th percentile of rolling-30d DD")
    thresholds = {sym: percentile(dd_by_sym[sym][1], 75) for sym in UNIVERSE}
    for sym, thr in thresholds.items():
        print(f"   {sym}: threshold={thr:.3f}%  recovery={thr * RECOVERY_FACTOR:.3f}%")

    # --- Trade-impact: for each trade, look up DD at open_time bar ---
    # Bucket trades by per-symbol DD-status decile of THEIR symbol's dd distribution.
    # And count trades that would be SKIPPED at the recommended threshold.
    print("\n[trade-bucket] Per-symbol IS trades bucketed by DD-status-at-entry decile")
    bucket_rows = []  # (sym, decile, n_trades, net_pnl_pct_sum, mean_weighted_pnl)
    skip_summary = []  # (sym, n_total, n_skip, retained_mean_w_pnl, skipped_mean_w_pnl)
    impact_rows = []  # for CSV

    for sym in UNIVERSE:
        bar_times, dd = dd_by_sym[sym]
        sym_trades = [t for t in trades if t["symbol"] == sym]

        # Compute dd-at-entry for each trade
        for tr in sym_trades:
            idx = find_bar_index(bar_times, tr["open_time"])
            tr["_dd_at_entry"] = dd[idx]

        sym_trades_sorted = sorted(sym_trades, key=lambda r: r["_dd_at_entry"])
        n = len(sym_trades_sorted)
        # Decile bucketing
        for dec in range(10):
            lo = int(dec * n / 10)
            hi = int((dec + 1) * n / 10)
            chunk = sym_trades_sorted[lo:hi]
            if not chunk:
                bucket_rows.append((sym, dec + 1, 0, 0.0, 0.0, 0.0))
                continue
            mean_dd = sum(c["_dd_at_entry"] for c in chunk) / len(chunk)
            sum_w_pnl = sum(c["weighted_pnl"] for c in chunk)
            mean_w_pnl = sum_w_pnl / len(chunk)
            bucket_rows.append((sym, dec + 1, len(chunk), mean_dd, sum_w_pnl, mean_w_pnl))
            print(
                f"   {sym} D{dec + 1:>2}: n={len(chunk):>3}  "
                f"mean_dd@entry={mean_dd:>6.3f}%  "
                f"sum_w_pnl={sum_w_pnl:>+7.2f}%  mean={mean_w_pnl:>+5.3f}%"
            )

        # Skip-rate: trades with dd_at_entry > threshold
        thr = thresholds[sym]
        skipped = [t for t in sym_trades if t["_dd_at_entry"] > thr]
        retained = [t for t in sym_trades if t["_dd_at_entry"] <= thr]
        skip_pct = 100.0 * len(skipped) / max(1, len(sym_trades))
        skipped_mean = (
            sum(t["weighted_pnl"] for t in skipped) / len(skipped) if skipped else 0.0
        )
        retained_mean = (
            sum(t["weighted_pnl"] for t in retained) / len(retained) if retained else 0.0
        )
        skipped_sum = sum(t["weighted_pnl"] for t in skipped)
        retained_sum = sum(t["weighted_pnl"] for t in retained)
        skip_summary.append(
            (sym, len(sym_trades), len(skipped), skip_pct, retained_mean, skipped_mean,
             retained_sum, skipped_sum)
        )
        print(
            f"   {sym} SKIP@thr={thr:.2f}%: total={len(sym_trades)} skipped={len(skipped)}"
            f" ({skip_pct:.1f}%) retained_mean={retained_mean:+.3f}%"
            f" skipped_mean={skipped_mean:+.3f}%  retained_sum={retained_sum:+.2f}%"
            f" skipped_sum={skipped_sum:+.2f}%"
        )
        impact_rows.append((sym, thr, len(sym_trades), len(skipped), skip_pct,
                            retained_sum, skipped_sum, retained_mean, skipped_mean))

    # --- Oscillation test ---
    print("\n[oscillation] ON/OFF transitions per symbol (recovery_factor=0.5)")
    osc_rows = []
    for sym in UNIVERSE:
        bar_times, dd = dd_by_sym[sym]
        on_series, transitions = simulate_brake(dd, thresholds[sym], RECOVERY_FACTOR)
        n_on = sum(1 for x in on_series if x)
        on_share = 100.0 * n_on / max(1, len(on_series))
        n_bars = len(on_series)
        # Total span in days for context
        span_days = n_bars / 3  # 3 bars/day at 8h
        osc_rows.append((sym, thresholds[sym], transitions, n_on, n_bars, on_share, span_days))
        print(
            f"   {sym}: transitions={transitions}  on_bars={n_on}/{n_bars}"
            f" ({on_share:.1f}%)  over {span_days:.0f} days"
            f"  -> {transitions / max(1, span_days / 365):.2f} transitions/year"
        )

    # --- Deadlock formal check ---
    # Question: can the brake enter a permanent ON state with no trades?
    # In ORACLE (this EDA), brake state is computed from the realized cum_pnl
    # curve which keeps moving regardless of brake state. So the OFF transition
    # eventually fires when dd recovers via subsequent positive trades.
    # In CLOSED LOOP (live): brake ON -> no new entries -> but open trades still
    # have exits; cum_pnl still moves via closing trades. ONLY if the brake
    # turns ON between two trades AND there are no open trades AND no new
    # entries can fire, the cum_pnl is frozen. dd = peak - cum is constant.
    # If dd > threshold at that instant -> dd stays > threshold*0.5 -> DEADLOCK.
    print("\n[deadlock] Checking for ORACLE-window dynamics that risk closed-loop deadlock")
    deadlock_risk = []
    for sym in UNIVERSE:
        bar_times, dd = dd_by_sym[sym]
        on_series, _ = simulate_brake(dd, thresholds[sym], RECOVERY_FACTOR)
        # Find longest contiguous ON window in ORACLE
        max_on_run = 0
        cur_run = 0
        for x in on_series:
            if x:
                cur_run += 1
                max_on_run = max(max_on_run, cur_run)
            else:
                cur_run = 0
        max_on_days = max_on_run / 3
        deadlock_risk.append((sym, max_on_run, max_on_days))
        print(
            f"   {sym}: longest_on_window={max_on_run} bars ({max_on_days:.1f} days)"
            f"  -- in ORACLE; closed-loop risk is HIGHER (see brief Sec 2)"
        )

    # --- Write CSV outputs ---
    with (OUT_DIR / "dd_percentiles.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["symbol", *[f"p{q}" for q in PERCENTILES], "n_bars", "max_dd"])
        for row in pct_rows:
            w.writerow([row[0], *[f"{x:.4f}" for x in row[1 : 1 + len(PERCENTILES)]],
                       row[1 + len(PERCENTILES)], f"{row[2 + len(PERCENTILES)]:.4f}"])

    with (OUT_DIR / "trade_buckets.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["symbol", "decile", "n_trades", "mean_dd_at_entry",
                    "sum_weighted_pnl_pct", "mean_weighted_pnl_pct"])
        for row in bucket_rows:
            w.writerow([row[0], row[1], row[2], f"{row[3]:.4f}",
                       f"{row[4]:.4f}", f"{row[5]:.4f}"])

    with (OUT_DIR / "skip_impact.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["symbol", "threshold_pct", "n_total", "n_skipped", "skip_rate_pct",
                    "retained_sum_w_pnl", "skipped_sum_w_pnl",
                    "retained_mean_w_pnl", "skipped_mean_w_pnl"])
        for row in impact_rows:
            w.writerow([row[0], f"{row[1]:.4f}", row[2], row[3], f"{row[4]:.2f}",
                       f"{row[5]:.4f}", f"{row[6]:.4f}", f"{row[7]:.4f}", f"{row[8]:.4f}"])

    with (OUT_DIR / "oscillation.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["symbol", "threshold_pct", "transitions", "on_bars",
                    "total_bars", "on_share_pct", "span_days"])
        for row in osc_rows:
            w.writerow([row[0], f"{row[1]:.4f}", row[2], row[3], row[4],
                       f"{row[5]:.2f}", f"{row[6]:.1f}"])

    with (OUT_DIR / "deadlock_risk.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["symbol", "longest_oracle_on_window_bars", "longest_oracle_on_days"])
        for row in deadlock_risk:
            w.writerow([row[0], row[1], f"{row[2]:.2f}"])

    print(f"\n[write] Outputs in {OUT_DIR}")
    print("   dd_percentiles.csv, trade_buckets.csv, skip_impact.csv,")
    print("   oscillation.csv, deadlock_risk.csv")


if __name__ == "__main__":
    main()
