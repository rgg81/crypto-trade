"""Compare a fresh baseline backtest's trades.csv against trades in testnet.db.

For every backtest trade, find a matching DB row by (model_name, symbol, open_time).
Verify the SIGNAL (direction) matches. Entry/exit prices for Binance-side trades
will differ due to MARKET-order slippage — those are reported but not failures.

Reports four buckets:
  - MATCH: same (model, symbol, open_time, direction) in both
  - DIRECTION_MISMATCH: same key, different direction → FAIL
  - MISSING_IN_DB: backtest has trade, DB has nothing for that key → FAIL
  - EXTRA_IN_DB: DB has trade, backtest doesn't → informational

Usage:
  uv run python scripts/compare_baseline_vs_db.py --track v1
  uv run python scripts/compare_baseline_vs_db.py --track v2
"""

from __future__ import annotations

import argparse
import csv
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

SYMBOL_TO_MODEL_V1: dict[str, str] = {
    "BTCUSDT": "A",
    "ETHUSDT": "A",
    "LINKUSDT": "C",
    "LTCUSDT": "D",
    "DOTUSDT": "E",
}

SYMBOL_TO_MODEL_V2: dict[str, str] = {
    "DOGEUSDT": "V2-DOGE",
    "SOLUSDT": "V2-SOL",
    "XRPUSDT": "V2-XRP",
    "NEARUSDT": "V2-NEAR",
}


def load_backtest_trades(csv_paths: list[Path], sym_to_model: dict[str, str]) -> list[dict]:
    """Read every CSV row, return list of {model, symbol, direction, open_time, entry, exit, ...}."""
    rows: list[dict] = []
    for p in csv_paths:
        if not p.exists():
            print(f"  WARN: missing {p}")
            continue
        with open(p) as f:
            reader = csv.DictReader(f)
            for r in reader:
                sym = r["symbol"]
                model = sym_to_model.get(sym)
                if model is None:
                    continue
                rows.append({
                    "model": model,
                    "symbol": sym,
                    "direction": int(r["direction"]),
                    "open_time": int(r["open_time"]),
                    "entry_price": float(r["entry_price"]),
                    "exit_price": float(r["exit_price"]),
                    "exit_reason": r["exit_reason"],
                    "source": p.name,
                })
    return rows


def load_db_trades(db_path: Path, models: set[str]) -> list[dict]:
    """Pull every trade for the given models from testnet.db (open or closed)."""
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    placeholders = ",".join("?" for _ in models)
    cur.execute(
        f"""SELECT id, model_name, symbol, direction, entry_price, exit_price,
                   exit_reason, status, open_time, entry_order_id
            FROM trades WHERE model_name IN ({placeholders})""",
        sorted(models),
    )
    rows = []
    for r in cur.fetchall():
        tid, model, sym, direction, entry, ex, reason, status, ot, eid = r
        rows.append({
            "id": tid,
            "model": model,
            "symbol": sym,
            "direction": int(direction),
            "entry_price": float(entry) if entry else None,
            "exit_price": float(ex) if ex else None,
            "exit_reason": reason,
            "status": status,
            "open_time": int(ot),
            "entry_order_id": eid,
            "is_real_binance": eid is not None and eid != "SEEDED"
                              and not eid.startswith("CATCHUP-")
                              and not eid.startswith("DRY-"),
        })
    con.close()
    return rows


def iso(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--track", choices=["v1", "v2"], required=True)
    parser.add_argument("--db", default="data/testnet.db")
    args = parser.parse_args()

    if args.track == "v1":
        csv_paths = [
            Path("reports/iteration_186/in_sample/trades.csv"),
            Path("reports/iteration_186/out_of_sample/trades.csv"),
        ]
        sym_to_model = SYMBOL_TO_MODEL_V1
    else:
        csv_paths = [
            Path("reports-v2/iteration_v2-069/in_sample/trades.csv"),
            Path("reports-v2/iteration_v2-069/out_of_sample/trades.csv"),
        ]
        sym_to_model = SYMBOL_TO_MODEL_V2

    print(f"=== Comparison for {args.track} ===\n")
    print("CSV sources:")
    for p in csv_paths:
        print(f"  {p}")
    print()

    backtest = load_backtest_trades(csv_paths, sym_to_model)
    models = set(sym_to_model.values())
    db = load_db_trades(Path(args.db), models)
    print(f"Backtest trades: {len(backtest)}")
    print(f"DB trades:       {len(db)}")
    print()

    # Index DB by (model, symbol, open_time). Per (model, symbol) the natural key
    # is unique (enforced by UNIQUE INDEX on trades).
    db_by_key: dict[tuple[str, str, int], dict] = {}
    for r in db:
        key = (r["model"], r["symbol"], r["open_time"])
        if key in db_by_key:
            print(f"  WARN: duplicate DB row for key {key}")
        db_by_key[key] = r

    matches = []
    dir_mismatch = []
    missing = []
    seen_db_keys: set[tuple[str, str, int]] = set()

    for b in backtest:
        key = (b["model"], b["symbol"], b["open_time"])
        d = db_by_key.get(key)
        if d is None:
            missing.append(b)
            continue
        seen_db_keys.add(key)
        if d["direction"] != b["direction"]:
            dir_mismatch.append((b, d))
        else:
            matches.append((b, d))

    extra = [r for r in db if (r["model"], r["symbol"], r["open_time"]) not in seen_db_keys]

    print(f"=== RESULTS ===")
    print(f"  MATCH                 : {len(matches)}")
    print(f"  DIRECTION_MISMATCH    : {len(dir_mismatch)}")
    print(f"  MISSING_IN_DB         : {len(missing)}")
    print(f"  EXTRA_IN_DB           : {len(extra)}")
    print()

    if dir_mismatch:
        print("=== DIRECTION MISMATCHES (FAIL) ===")
        for b, d in dir_mismatch:
            print(
                f"  {b['symbol']:9} ot={iso(b['open_time'])}  "
                f"backtest dir={b['direction']:+d}  DB dir={d['direction']:+d} "
                f"(id={d['id']})"
            )
        print()

    if missing:
        print("=== BACKTEST TRADES MISSING FROM DB (FAIL) ===")
        for b in missing:
            print(
                f"  {b['model']:8} {b['symbol']:9} ot={iso(b['open_time'])} "
                f"dir={b['direction']:+d}  src={b['source']}  exit={b['exit_reason']}"
            )
        print()

    if extra:
        print("=== DB TRADES NOT IN BACKTEST ===")
        # Bucket by whether the DB row is paper or real Binance
        real = [r for r in extra if r["is_real_binance"]]
        paper = [r for r in extra if not r["is_real_binance"]]
        print(f"  (Paper / CATCHUP / SEEDED / etc.): {len(paper)}")
        for r in paper[:20]:
            print(
                f"    {r['model']:8} {r['symbol']:9} ot={iso(r['open_time'])} "
                f"dir={r['direction']:+d}  status={r['status']}  reason={r['exit_reason']}  "
                f"eid={r['entry_order_id']}"
            )
        if len(paper) > 20:
            print(f"    ... +{len(paper) - 20} more")
        print(f"  (Real Binance — should match backtest if they were live-tick opens):")
        for r in real:
            print(
                f"    {r['model']:8} {r['symbol']:9} ot={iso(r['open_time'])} "
                f"dir={r['direction']:+d}  status={r['status']}  reason={r['exit_reason']}  "
                f"eid={r['entry_order_id']}"
            )
        print()

    # Verdict
    print(f"=== VERDICT ===")
    if dir_mismatch:
        print("  ❌ FAIL — direction mismatch on at least one trade")
        return 1
    if missing:
        print("  ❌ FAIL — backtest trade not present in DB")
        return 1
    real_extras = [r for r in extra if r["is_real_binance"]]
    if real_extras:
        print(
            f"  ⚠️  {len(real_extras)} real Binance trade(s) in DB without a backtest counterpart. "
            "Investigate before declaring full match."
        )
        return 2
    print(f"  ✅ All {len(backtest)} backtest trades match DB on (model, symbol, open_time, direction).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
