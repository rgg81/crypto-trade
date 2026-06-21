"""Candle-integrity check — the signal CLOSE must be a COMPLETE candle, never the forming one.

A classic look-ahead bug is letting the in-progress (forming) candle's close leak into the signal
data. The fetcher drops forming candles (`fetcher.py`: keep only k.close_time < now_ms), and the
strategy injects the forming candle ONLY as a close-proxy OPEN (its close never feeds a signal).
This monitor verifies that invariant holds in the data the bot reads — defense in depth.

Checks every refreshed coin CSV's LAST row:
  - FORMING LEAK: last candle's close_time > now -> an incomplete candle leaked into the signal
    data (the look-ahead bug the user flagged). HARD bad.
  - STALE: the freshest last-complete candle is older than ~9h -> the engine missed a refresh at
    the last 8h boundary (signals running on old data).

Fast (reads only open_time per CSV, no universe load). Prints `CANDLE: OK | BAD` + detail. Exit 0.
"""

from __future__ import annotations

import glob
import os
import time

import pandas as pd

STEP_MS = 8 * 60 * 60 * 1000
STALE_MS = 9 * 60 * 60 * 1000          # last complete candle older than this => missed a refresh
DATA_GLOB = "data/*USDT/8h.csv"


def main() -> None:
    now_ms = int(time.time() * 1000)
    forming: list[tuple[str, int]] = []      # (sym, last_open_ms) with an incomplete last candle
    freshest_close = 0                        # max close_time of any coin's last (complete) candle
    n = 0
    for p in sorted(glob.glob(DATA_GLOB)):
        try:
            last_ot = int(pd.read_csv(p, usecols=["open_time"])["open_time"].iloc[-1])
        except Exception:
            continue
        n += 1
        close_t = last_ot + STEP_MS
        if close_t > now_ms:
            forming.append((os.path.basename(os.path.dirname(p)), last_ot))
        elif close_t > freshest_close:
            freshest_close = close_t

    flags: list[str] = []
    if forming:
        flags.append(f"FORMING-CANDLE LEAK in {len(forming)} coin(s): "
                     + ", ".join(s for s, _ in forming[:6]))
    stale_min = (now_ms - freshest_close) // 60_000 if freshest_close else -1
    if freshest_close and (now_ms - freshest_close) > STALE_MS:
        flags.append(f"STALE data: freshest complete candle closed {stale_min}min ago "
                     f"(> {STALE_MS // 3_600_000}h -> missed a refresh)")

    status = "BAD" if flags else "OK"
    last_complete = pd.to_datetime(freshest_close, unit="ms") if freshest_close else "n/a"
    print(f"CANDLE: {status}  (coins={n}, last complete candle={last_complete}, "
          f"{stale_min}min ago, forming-leaks={len(forming)})")
    for f in flags:
        print(f"  BAD: {f}")
    print(f"  checked {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")


if __name__ == "__main__":
    main()
