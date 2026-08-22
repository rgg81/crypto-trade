#!/usr/bin/env python
"""Freeze each desk's historical 8h stream, once, for live-prefix parity.

Every tick re-runs the whole replay and compares its historical portion -- everything before the
sealed window ends -- against this frozen file, exactly. That is what makes the forward record a
continuation of the tournament's own result rather than a separate backtest that happens to run
later: if the past ever changes, the desk stops instead of quietly publishing a different history.

The stream is produced through the SAME path the tick uses -- the current generation appended to
the frozen partitions by build_forward_snapshot, then replay_desk -- rather than from a stitched
snapshot that ought to be equivalent. The historical rows should be identical either way, and
"should be" is exactly the assumption a parity check exists to stop anyone making.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.dont_write_bytecode = True

from crypto_trade.cup50v2_desk.authority import load_desk, paper_root, repository_root  # noqa: E402
from crypto_trade.cup50v2_desk.live_data import (  # noqa: E402
    PublicMarketDataClient,
    refresh_generation,
)
from crypto_trade.cup50v2_desk.snapshot_forward import (  # noqa: E402
    build_forward_snapshot,
    derive_forward_membership,
)
from crypto_trade.cup50v2_desk.tick import (  # noqa: E402
    HISTORICAL_PREFIX,
    _historical_stream,
    replay_desk,
)

DESKS = ("winner", "runner-up-1", "runner-up-2", "ensemble-eq3")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=None)
    parser.add_argument("--desk", action="append", default=None)
    parser.add_argument("--boundary", required=True, help="the launch boundary, ISO-8601 UTC")
    parser.add_argument("--verify", action="store_true", help="compare an existing prefix")
    arguments = parser.parse_args()
    root = Path(arguments.root).resolve() if arguments.root else repository_root()
    boundary = pd.Timestamp(arguments.boundary)
    boundary = (
        boundary.tz_localize("UTC") if boundary.tzinfo is None else boundary.tz_convert("UTC")
    )

    with PublicMarketDataClient() as client:
        generation, membership = refresh_generation(
            root / "paper-cup50v2" / "market-cache",
            boundary=boundary,
            resolve_membership=lambda path, edge: derive_forward_membership(path, edge, root=root),
            client=client,
        )
    snapshot = build_forward_snapshot(generation, membership, boundary, root=root)

    for desk_id in tuple(arguments.desk) if arguments.desk else DESKS:
        desk = load_desk(desk_id, root)
        replay = replay_desk(desk, snapshot, root=root)
        stream = _historical_stream(replay)
        destination = paper_root(desk, root) / HISTORICAL_PREFIX
        if destination.exists():
            existing = pd.read_parquet(destination)
            if not arguments.verify:
                raise SystemExit(f"{destination} already exists; a prefix is frozen once")
            pd.testing.assert_frame_equal(
                stream, existing.loc[:, stream.columns], check_exact=True, check_dtype=True
            )
            print(f"{desk_id:<14} verified {len(stream):>6} rows")
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        stream.to_parquet(destination, index=False)
        print(f"{desk_id:<14} froze    {len(stream):>6} rows -> {destination.name}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
