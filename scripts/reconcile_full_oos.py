"""Full-OOS-window reconciliation: live dry_run.db vs backtest CSVs.

Compares trades from the live engine's catch-up output to the backtest
trades.csv files for v1 and v2. Reports field-by-field divergences
across the entire OOS window (2025-03-24 onwards) with extra detail on
March 2026 and April 2026 specifically.

Usage (legacy iteration_186 / v1 + v2 mode):
    uv run python scripts/reconcile_full_oos.py [--db data/dry_run.db]

Usage (BUNDLE-002 mode — iter-v1/082, 4-specialist V1-{DOT,ETH,BTC,AAVE}):
    uv run python scripts/reconcile_full_oos.py --bundle-002 [--db data/dry_run.db]
    uv run python scripts/reconcile_full_oos.py --bundle-002 \\
        --reports-dir reports-v1/iteration_v1-082

BUNDLE-002 mode differences vs legacy:
  - Compares V1-{DOT,ETH,BTC,AAVE} symbols against the /082 16-col trade schema.
  - Loads both in_sample and out_of_sample CSVs from the --reports-dir directory.
  - The /082 schema has 4 extra columns vs legacy: stop_loss_price, take_profit_price,
    timeout_time, confidence.  Comparison is schema-driven: only columns present in
    BOTH the CSV and TRADE_COLS_BUNDLE are compared.
  - end_of_data -> timeout data-extent exception applies (same as legacy).
  - Tolerance: 5e-4 on all numeric fields.
  - Per-symbol breakdown included in the summary.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
from tests.live.test_backtest_parity_v2 import (  # noqa: E402
    TRADE_COLS,
    _read_closed_trades_from_db,
)

# ---------------------------------------------------------------------------
# Legacy (iteration_186) constants
# ---------------------------------------------------------------------------

V1_TRADES_CSV = Path("reports/iteration_186/out_of_sample/trades.csv")
V2_TRADES_CSV = Path("reports-v2/iteration_v2-069/out_of_sample/trades.csv")
V1_SYMS = {"BTCUSDT", "ETHUSDT", "LINKUSDT", "LTCUSDT", "DOTUSDT"}
V2_SYMS = {"DOGEUSDT", "SOLUSDT", "XRPUSDT", "NEARUSDT"}

OOS_CUTOFF_MS = pd.Timestamp("2025-03-24", tz="UTC").value // 1_000_000
MAR_2026_MS = pd.Timestamp("2026-03-01", tz="UTC").value // 1_000_000
APR_2026_MS = pd.Timestamp("2026-04-01", tz="UTC").value // 1_000_000

# ---------------------------------------------------------------------------
# BUNDLE-002 (iteration_v1-082) constants
# ---------------------------------------------------------------------------

BUNDLE_002_DEFAULT_REPORTS_DIR = Path("reports-v1/iteration_v1-082")
BUNDLE_002_SYMS = {"DOTUSDT", "ETHUSDT", "BTCUSDT", "AAVEUSDT"}

# Model name prefix used by the live engine for V1 specialists.
# The DB stores model_name "V1-DOT", "V1-ETH", etc.; each owns one symbol.
BUNDLE_002_MODEL_NAMES = {"V1-DOT", "V1-ETH", "V1-BTC", "V1-AAVE"}

# The /082 CSV schema (16 columns).  Comparison is restricted to the
# intersection of these and the columns actually present in each CSV.
TRADE_COLS_BUNDLE: list[str] = [
    "symbol",
    "direction",
    "entry_price",
    "exit_price",
    "weight_factor",
    "open_time",
    "close_time",
    "exit_reason",
    "pnl_pct",
    "fee_pct",
    "net_pnl_pct",
    "weighted_pnl",
    "stop_loss_price",
    "take_profit_price",
    "timeout_time",
    "confidence",
]

# Numeric tolerance — matches the 4dp precision of CSV output.
_TOL = 5e-4

# Columns where only string/exact equality is meaningful.
_STRING_COLS = {"symbol", "direction", "exit_reason"}

# Columns where the end_of_data → timeout exception applies.
_EXIT_REASON_COL = "exit_reason"


# ---------------------------------------------------------------------------
# Shared helpers (legacy + bundle modes)
# ---------------------------------------------------------------------------


def _key(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["_key"] = df["symbol"].astype(str) + "|" + df["open_time"].astype(str)
    return df


def _diff_shared(li: pd.DataFrame, bi: pd.DataFrame, label: str) -> int:
    """Compare every TRADE_COLS field on shared keys. Tolerance 5e-4 (CSV is 4dp)."""
    common = sorted(set(li.index) & set(bi.index))
    if not common:
        print(f"  {label}: no shared trades")
        return 0
    diffs: dict[str, list[tuple]] = {c: [] for c in TRADE_COLS}
    for k in common:
        for c in TRADE_COLS:
            a, b = li.at[k, c], bi.at[k, c]
            if isinstance(a, str):
                if a != b:
                    diffs[c].append((k, a, b))
            else:
                d = abs(float(a) - float(b))
                if d > 5e-4:
                    diffs[c].append((k, float(a), float(b), d))
    print(f"\n  {label}: {len(common)} shared trades")
    total_div = 0
    for c, items in diffs.items():
        if not items:
            print(f"    {c}: 0 ✓")
        else:
            total_div += len(items)
            print(f"    {c}: {len(items)} mismatches")
            for x in items[:3]:
                if len(x) == 4:
                    k, a, b, d = x
                    ot = pd.to_datetime(int(k.split("|")[1]), unit="ms", utc=True).strftime(
                        "%Y-%m-%d %H:%M"
                    )
                    sym = k.split("|")[0]
                    print(f"      {ot} {sym:9s} live={a:.6f} bt={b:.6f} Δ={d:.6f}")
                else:
                    k, a, b = x
                    print(f"      {k} live={a} bt={b}")
    return total_div


def _compare_window(
    label: str,
    live: pd.DataFrame,
    bt: pd.DataFrame,
    syms: set[str],
    floor_ms: int,
    ceil_ms: int | None = None,
) -> int:
    """Compare live vs bt over [floor_ms, ceil_ms). Returns total divergences."""
    cond_l = live["symbol"].isin(syms) & (live["open_time"] >= floor_ms)
    cond_b = bt["symbol"].isin(syms) & (bt["open_time"] >= floor_ms)
    if ceil_ms is not None:
        cond_l = cond_l & (live["open_time"] < ceil_ms)
        cond_b = cond_b & (bt["open_time"] < ceil_ms)
    live_w = _key(live[cond_l].sort_values("open_time"))
    bt_w = _key(bt[cond_b].sort_values("open_time"))

    only_live = sorted(set(live_w["_key"]) - set(bt_w["_key"]))
    only_bt = sorted(set(bt_w["_key"]) - set(live_w["_key"]))

    print("=" * 78)
    print(f"{label}: live={len(live_w)}  backtest={len(bt_w)}")
    print("=" * 78)
    print(f"  set match: {len(set(live_w['_key']) & set(bt_w['_key']))} shared")
    if only_live:
        print(f"  only-in-live ({len(only_live)}):")
        for k in only_live[:8]:
            ot = pd.to_datetime(int(k.split("|")[1]), unit="ms", utc=True).strftime(
                "%Y-%m-%d %H:%M"
            )
            sym = k.split("|")[0]
            print(f"    {ot} {sym}")
    if only_bt:
        print(f"  only-in-backtest ({len(only_bt)}):")
        for k in only_bt[:8]:
            ot = pd.to_datetime(int(k.split("|")[1]), unit="ms", utc=True).strftime(
                "%Y-%m-%d %H:%M"
            )
            sym = k.split("|")[0]
            print(f"    {ot} {sym}")

    total = len(only_live) + len(only_bt)
    if shared := set(live_w["_key"]) & set(bt_w["_key"]):
        li = live_w.set_index("_key")
        bi = bt_w.set_index("_key")
        # Restrict to shared keys for field comparison
        li = li.loc[sorted(shared)]
        bi = bi.loc[sorted(shared)]
        total += _diff_shared(li, bi, "field-by-field")
    return total


# ---------------------------------------------------------------------------
# BUNDLE-002 helpers
# ---------------------------------------------------------------------------


def _load_bundle_bt_trades(reports_dir: Path) -> pd.DataFrame:
    """Load and concatenate in_sample + out_of_sample /082 trade CSVs.

    Schema-driven: loads whatever columns the CSV contains, then restricts
    comparison to TRADE_COLS_BUNDLE intersection later.
    """
    frames = []
    for split in ("in_sample", "out_of_sample"):
        csv_path = reports_dir / split / "trades.csv"
        if not csv_path.exists():
            print(f"  WARNING: {csv_path} not found — skipped (Phase 2 regen pending)")
            continue
        df = pd.read_csv(csv_path)
        df["_split"] = split
        frames.append(df)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def _active_compare_cols(csv_df: pd.DataFrame) -> list[str]:
    """Return TRADE_COLS_BUNDLE columns that are actually present in the CSV."""
    csv_cols = set(csv_df.columns)
    return [c for c in TRADE_COLS_BUNDLE if c in csv_cols]


def _diff_shared_bundle(
    li: pd.DataFrame,
    bi: pd.DataFrame,
    compare_cols: list[str],
    label: str,
) -> int:
    """Field-by-field diff for BUNDLE-002 /082 16-col schema.

    end_of_data -> timeout: live engine closes a trade as 'timeout' when
    data extends past the backtest CSV cutoff.  For exit_reason, the pair
    (end_of_data in BT, timeout in live) is accepted as equivalent.
    Tolerance: 5e-4 on numeric fields; exact equality on string fields.
    """
    common = sorted(set(li.index) & set(bi.index))
    if not common:
        print(f"  {label}: no shared trades")
        return 0

    total_div = 0
    col_diffs: dict[str, list[str]] = {c: [] for c in compare_cols}

    for k in common:
        for c in compare_cols:
            a = li.at[k, c]
            b = bi.at[k, c]

            # exit_reason: end_of_data (backtest) == timeout (live) exception.
            if c == _EXIT_REASON_COL:
                # Normalize the pair; any other mismatch is a real divergence.
                bt_val = str(b)
                live_val = str(a)
                if bt_val == "end_of_data" and live_val == "timeout":
                    continue
                if live_val != bt_val:
                    col_diffs[c].append(f"      key={k} live={live_val!r} bt={bt_val!r}")
                continue

            # Numeric columns.
            if c not in _STRING_COLS:
                try:
                    fa, fb = float(a), float(b)
                    d = abs(fa - fb)
                    if d > _TOL:
                        ot = pd.to_datetime(
                            int(str(k).split("|")[1]), unit="ms", utc=True
                        ).strftime("%Y-%m-%d %H:%M")
                        sym = str(k).split("|")[0]
                        col_diffs[c].append(
                            f"      {ot} {sym:9s} live={fa:.6f} bt={fb:.6f} Δ={d:.6f}"
                        )
                    continue
                except (ValueError, TypeError):
                    pass

            # String / categorical columns.
            if str(a) != str(b):
                col_diffs[c].append(f"      key={k} live={a!r} bt={b!r}")

    print(f"\n  {label}: {len(common)} shared trades (cols compared: {compare_cols})")
    for c, items in col_diffs.items():
        if not items:
            print(f"    {c}: 0 ✓")
        else:
            total_div += len(items)
            print(f"    {c}: {len(items)} mismatches")
            for line in items[:3]:
                print(line)
            if len(items) > 3:
                print(f"      ... ({len(items) - 3} more)")

    return total_div


def _compare_bundle_window(
    label: str,
    live: pd.DataFrame,
    bt: pd.DataFrame,
    syms: set[str],
    compare_cols: list[str],
    floor_ms: int,
    ceil_ms: int | None = None,
) -> int:
    """Compare BUNDLE-002 live vs backtest over [floor_ms, ceil_ms)."""
    cond_l = live["symbol"].isin(syms) & (live["open_time"] >= floor_ms)
    cond_b = bt["symbol"].isin(syms) & (bt["open_time"] >= floor_ms)
    if ceil_ms is not None:
        cond_l = cond_l & (live["open_time"] < ceil_ms)
        cond_b = cond_b & (bt["open_time"] < ceil_ms)

    live_w = _key(live[cond_l].sort_values(["open_time", "symbol"]))
    bt_w = _key(bt[cond_b].sort_values(["open_time", "symbol"]))

    only_live = sorted(set(live_w["_key"]) - set(bt_w["_key"]))
    only_bt = sorted(set(bt_w["_key"]) - set(live_w["_key"]))

    print("=" * 78)
    print(f"{label}: live={len(live_w)}  backtest={len(bt_w)}")
    print("=" * 78)
    shared_keys = set(live_w["_key"]) & set(bt_w["_key"])
    print(f"  set match: {len(shared_keys)} shared")

    if only_live:
        print(f"  only-in-live ({len(only_live)}):")
        for k in only_live[:8]:
            ot = pd.to_datetime(int(k.split("|")[1]), unit="ms", utc=True).strftime(
                "%Y-%m-%d %H:%M"
            )
            sym = k.split("|")[0]
            print(f"    {ot} {sym}")
        if len(only_live) > 8:
            print(f"    ... ({len(only_live) - 8} more)")
    if only_bt:
        print(f"  only-in-backtest ({len(only_bt)}):")
        for k in only_bt[:8]:
            ot = pd.to_datetime(int(k.split("|")[1]), unit="ms", utc=True).strftime(
                "%Y-%m-%d %H:%M"
            )
            sym = k.split("|")[0]
            print(f"    {ot} {sym}")
        if len(only_bt) > 8:
            print(f"    ... ({len(only_bt) - 8} more)")

    total = len(only_live) + len(only_bt)
    if shared_keys:
        li = live_w.set_index("_key").loc[sorted(shared_keys)]
        bi = bt_w.set_index("_key").loc[sorted(shared_keys)]
        # Restrict bt to only the compare_cols we know exist.
        li_cols = [c for c in compare_cols if c in li.columns]
        bi_cols = [c for c in compare_cols if c in bi.columns]
        common_cols = [c for c in li_cols if c in bi_cols]
        total += _diff_shared_bundle(li, bi, common_cols, "field-by-field")

    return total


def _bundle_per_symbol_summary(live: pd.DataFrame, bt: pd.DataFrame, oos_only: bool = True) -> None:
    """Print per-symbol trade count + first/last open_time from live and bt."""
    if oos_only:
        live = live[live["open_time"] >= OOS_CUTOFF_MS]
        bt = bt[bt["open_time"] >= OOS_CUTOFF_MS]

    print("\nPer-symbol summary (OOS only):")
    for sym in sorted(BUNDLE_002_SYMS):
        lc = len(live[live["symbol"] == sym])
        bc = len(bt[bt["symbol"] == sym])
        status = "OK" if lc == bc else "MISMATCH"
        print(f"  {sym:12s}  live={lc:4d}  bt={bc:4d}  [{status}]")


def _read_bundle_live_trades(db: Path) -> pd.DataFrame:
    """Read closed trades from the live DB, filtered to BUNDLE_002 symbols.

    Uses the same _read_closed_trades_from_db as the legacy mode but then
    adds the extra /082 columns (stop_loss_price, take_profit_price,
    timeout_time, confidence) by pulling them from the LiveTrade record
    if available.
    """
    from crypto_trade.live.state_store import StateStore
    from crypto_trade.live.trade_logger import to_trade_result

    store = StateStore(db)
    rows: list[dict] = []
    for trade in store.get_all_trades():
        if trade.status != "closed":
            continue
        if trade.symbol not in BUNDLE_002_SYMS:
            continue
        result = to_trade_result(trade, fee_pct=0.1)
        if result is None:
            continue
        row: dict = {
            "symbol": result.symbol,
            "direction": result.direction,
            "entry_price": result.entry_price,
            "exit_price": result.exit_price,
            "weight_factor": result.weight_factor,
            "open_time": result.open_time,
            "close_time": result.close_time,
            "exit_reason": result.exit_reason,
            "pnl_pct": result.pnl_pct,
            "fee_pct": result.fee_pct,
            "net_pnl_pct": result.net_pnl_pct,
            "weighted_pnl": result.weighted_pnl,
            # /082 extra columns — filled from live trade record when available.
            "stop_loss_price": getattr(trade, "stop_loss_price", None),
            "take_profit_price": getattr(trade, "take_profit_price", None),
            "timeout_time": getattr(trade, "timeout_time", None),
            "confidence": getattr(trade, "confidence", None),
        }
        rows.append(row)

    if not rows:
        return pd.DataFrame(columns=TRADE_COLS_BUNDLE)

    df = pd.DataFrame(rows)
    # Ensure all expected columns are present even if the DB records lack them.
    for c in TRADE_COLS_BUNDLE:
        if c not in df.columns:
            df[c] = None
    return df[TRADE_COLS_BUNDLE]


# ---------------------------------------------------------------------------
# Main entry
# ---------------------------------------------------------------------------


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Field-by-field reconciliation: live engine vs backtest trades CSVs."
    )
    ap.add_argument("--db", default="data/dry_run.db", type=str)
    ap.add_argument(
        "--bundle-002",
        action="store_true",
        help="Run in BUNDLE-002 mode: compare V1-{DOT,ETH,BTC,AAVE} against /082 CSVs.",
    )
    ap.add_argument(
        "--reports-dir",
        default=str(BUNDLE_002_DEFAULT_REPORTS_DIR),
        type=str,
        help="Path to the iteration_v1-082 reports directory (BUNDLE-002 mode only).",
    )
    args = ap.parse_args()

    db = Path(args.db)
    if not db.exists():
        sys.exit(f"DB not found: {db}")

    if args.bundle_002:
        _run_bundle_002(db, Path(args.reports_dir))
    else:
        _run_legacy(db)


def _run_legacy(db: Path) -> None:
    """Original iteration_186 + v2 reconciliation mode."""
    live = _read_closed_trades_from_db(db)
    print(f"Loaded {len(live)} closed trades from {db}")

    v1_bt = pd.read_csv(V1_TRADES_CSV)
    v2_bt = pd.read_csv(V2_TRADES_CSV)
    v2_bt = v2_bt[v2_bt["weight_factor"] > 0]
    print(f"Backtest: v1={len(v1_bt)}, v2 (nonzero weight)={len(v2_bt)}\n")

    div_total = 0

    # ---- FULL OOS WINDOW ----
    print("\n┌────────────────────────────────────────────────────────────────────────────┐")
    print("│ FULL OOS WINDOW (open_time ≥ 2025-03-24)                                  │")
    print("└────────────────────────────────────────────────────────────────────────────┘")
    div_total += _compare_window("V1 full OOS", live, v1_bt, V1_SYMS, OOS_CUTOFF_MS)
    div_total += _compare_window("V2 full OOS", live, v2_bt, V2_SYMS, OOS_CUTOFF_MS)

    # ---- MARCH 2026 SPECIFICALLY ----
    print("\n┌────────────────────────────────────────────────────────────────────────────┐")
    print("│ MARCH 2026 (2026-03-01 ≤ open_time < 2026-04-01)                          │")
    print("└────────────────────────────────────────────────────────────────────────────┘")
    div_total += _compare_window("V1 March 2026", live, v1_bt, V1_SYMS, MAR_2026_MS, APR_2026_MS)
    div_total += _compare_window("V2 March 2026", live, v2_bt, V2_SYMS, MAR_2026_MS, APR_2026_MS)

    # ---- APRIL 2026 SPECIFICALLY ----
    print("\n┌────────────────────────────────────────────────────────────────────────────┐")
    print("│ APRIL 2026 (open_time ≥ 2026-04-01)                                       │")
    print("└────────────────────────────────────────────────────────────────────────────┘")
    div_total += _compare_window("V1 April 2026", live, v1_bt, V1_SYMS, APR_2026_MS)
    div_total += _compare_window("V2 April 2026", live, v2_bt, V2_SYMS, APR_2026_MS)

    print("\n" + "=" * 78)
    if div_total == 0:
        print("RESULT: ALL WINDOWS IDENTICAL — full backtest parity achieved")
    else:
        print(f"RESULT: {div_total} divergences across all windows — investigate above")
    print("=" * 78)


def _run_bundle_002(db: Path, reports_dir: Path) -> None:
    """BUNDLE-002 mode: compare V1-{DOT,ETH,BTC,AAVE} live trades vs /082 CSVs."""
    print(f"[BUNDLE-002 mode] DB: {db}")
    print(f"[BUNDLE-002 mode] Reports dir: {reports_dir}")

    # Load backtest CSVs (both IS + OOS splits).
    bt_all = _load_bundle_bt_trades(reports_dir)
    if bt_all.empty:
        print(
            "WARNING: No backtest CSVs found in reports dir — "
            "skipping comparison (Phase 2 regen pending)."
        )
        print("\nRESULT: SKIPPED — no backtest CSVs available")
        return

    print(f"Loaded {len(bt_all)} backtest trades (IS + OOS combined) from {reports_dir}")
    print(f"  Symbols in BT: {sorted(bt_all['symbol'].unique())}")

    # Determine compare columns from the CSV (schema-driven).
    compare_cols = _active_compare_cols(bt_all)
    print(f"  Columns compared: {compare_cols}")

    # Load live DB trades filtered to BUNDLE_002 symbols.
    live = _read_bundle_live_trades(db)
    print(f"Loaded {len(live)} BUNDLE-002 closed trades from {db}\n")

    div_total = 0

    # ---- IS WINDOW (open_time < OOS_CUTOFF_MS) ----
    is_floor_ms = 0  # from the beginning of backtest data
    print("\n┌────────────────────────────────────────────────────────────────────────────┐")
    print("│ IS WINDOW (open_time < 2025-03-24)                                        │")
    print("└────────────────────────────────────────────────────────────────────────────┘")
    # IS window: open_time < OOS_CUTOFF (floor=0, ceil=OOS_CUTOFF)
    bt_is = bt_all[bt_all["open_time"] < OOS_CUTOFF_MS]
    div_total += _compare_bundle_window(
        "BUNDLE-002 IS",
        live,
        bt_is,
        BUNDLE_002_SYMS,
        compare_cols,
        floor_ms=is_floor_ms,
        ceil_ms=OOS_CUTOFF_MS,
    )

    # ---- FULL OOS WINDOW ----
    bt_oos = bt_all[bt_all["open_time"] >= OOS_CUTOFF_MS]
    print("\n┌────────────────────────────────────────────────────────────────────────────┐")
    print("│ FULL OOS WINDOW (open_time ≥ 2025-03-24)                                  │")
    print("└────────────────────────────────────────────────────────────────────────────┘")
    div_total += _compare_bundle_window(
        "BUNDLE-002 full OOS",
        live,
        bt_oos,
        BUNDLE_002_SYMS,
        compare_cols,
        floor_ms=OOS_CUTOFF_MS,
    )

    # ---- MARCH 2026 ----
    print("\n┌────────────────────────────────────────────────────────────────────────────┐")
    print("│ MARCH 2026 (2026-03-01 ≤ open_time < 2026-04-01)                          │")
    print("└────────────────────────────────────────────────────────────────────────────┘")
    div_total += _compare_bundle_window(
        "BUNDLE-002 March 2026",
        live,
        bt_all,
        BUNDLE_002_SYMS,
        compare_cols,
        floor_ms=MAR_2026_MS,
        ceil_ms=APR_2026_MS,
    )

    # ---- APRIL 2026 ----
    print("\n┌────────────────────────────────────────────────────────────────────────────┐")
    print("│ APRIL 2026 (open_time ≥ 2026-04-01)                                       │")
    print("└────────────────────────────────────────────────────────────────────────────┘")
    div_total += _compare_bundle_window(
        "BUNDLE-002 April 2026",
        live,
        bt_all,
        BUNDLE_002_SYMS,
        compare_cols,
        floor_ms=APR_2026_MS,
    )

    # ---- PER-SYMBOL SUMMARY ----
    _bundle_per_symbol_summary(live, bt_all, oos_only=True)

    print("\n" + "=" * 78)
    if div_total == 0:
        print("RESULT: ALL WINDOWS IDENTICAL — BUNDLE-002 backtest parity achieved")
    else:
        print(f"RESULT: {div_total} divergences across all windows — investigate above")
    print("=" * 78)


if __name__ == "__main__":
    main()
