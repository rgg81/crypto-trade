"""Extend a rolling forward snapshot so the desks always have the freshest data available.

**The frozen snapshot is never touched.** ``data/top40/snapshot-v3`` and its manifest are bound by
the activation freeze -- they are the tournament's evidence, and re-fetching into them would
rewrite the record the desks are measured against. This builds a *separate* snapshot under
``data/top40/forward`` from a config that differs from the frozen one in exactly two fields: the
output directory and ``hard_end_exclusive``.

Everything else is identical, and that is the point. The universe rule, the parser version, the
checksum policy, the intervals and the warmup are the same bytes, so the forward snapshot is the
frozen one plus more days rather than a different construction that happens to overlap.

``resume=True`` makes this incremental: verified raw archives are cached and re-used, so a refresh
fetches the months that are missing and nothing else. The first run is long; later ones are short.

Fetches route through the local binance-proxy when it is up. Going direct works until it doesn't --
the repeated full-history fetches this job makes are exactly what earned a 418 ban on other desks,
and the proxy exists because of that.

Usage::

    uv run python scripts/top40v5_refresh_forward.py --check
    uv run python scripts/top40v5_refresh_forward.py
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import urllib.request
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
FROZEN_CONFIG = REPO / "tournament" / "top40-v5" / "SNAPSHOT-BUILD.toml"
FORWARD_CONFIG = REPO / "tournament" / "top40-v5" / "SNAPSHOT-FORWARD.toml"
FROZEN_DIR = REPO / "data" / "top40" / "snapshot-v3"
FORWARD_DIR = REPO / "data" / "top40" / "forward"
FORWARD_MANIFEST = REPO / "tournament" / "top40-v5" / "forward-manifest.json"
PROXY = "http://127.0.0.1:8000"


def _proxy_is_up() -> bool:
    """Probe an endpoint the proxy actually serves.

    It answers 404 on /fapi/v1/time -- it is a klines cache, not a full mirror -- so probing that
    reported the proxy down while it was up and serving, which would have sent every refresh
    straight at Binance.
    """

    probe = f"{PROXY}/fapi/v1/klines?symbol=BTCUSDT&interval=8h&limit=1"
    try:
        with urllib.request.urlopen(probe, timeout=4) as response:
            return response.status == 200 and response.read(1) == b"["
    except Exception:  # noqa: BLE001 - any failure means "go direct"
        return False


def _target_end(now: pd.Timestamp) -> pd.Timestamp:
    """The first day of the current month -- the furthest the canonical builder can reach.

    This is a hard property of the data source, not a conservative choice. The snapshot is built
    from data.binance.vision monthly archives with checksum verification, and
    ``_require_active_hard_end_coverage`` refuses to publish when an active contract has no archive
    covering the hard end. Binance publishes a month's archive only after that month closes, so
    asking for today's date fails with "active transaction_8h contract 0GUSDT lacks hard-end
    archive 2026-08" -- correctly, because that archive does not exist.

    The consequence is a sawtooth: the forward snapshot is current to the last complete month and
    catches up within a few days of each month ending, when the archives publish. Reaching further
    means REST klines instead of checksummed archives, which is a weaker provenance claim than the
    snapshot makes everywhere else -- a deliberate decision rather than something to slip in here.
    """

    return now.normalize().replace(day=1)


def write_forward_config(end_exclusive: pd.Timestamp, *, use_proxy: bool) -> str:
    body = FROZEN_CONFIG.read_text(encoding="utf-8")
    body = body.replace(
        'hard_end_exclusive = "2026-08-01"',
        f'hard_end_exclusive = "{end_exclusive.date()}"',
    )
    body = body.replace(
        'snapshot_dir = "data/top40/snapshot-v3"', 'snapshot_dir = "data/top40/forward"'
    )
    body = body.replace(
        'manifest_path = "tournament/top40-v5/data-manifest.json"',
        'manifest_path = "tournament/top40-v5/forward-manifest.json"',
    )
    body = body.replace(
        'common_report_dir = "reports-top40-v5/common"',
        'common_report_dir = "reports-top40-v5/forward-common"',
    )
    # The REST endpoints stay on the official host, deliberately.
    #
    # The snapshot builder refuses a funding URL that is not official Binance USD-M -- "canonical
    # funding REST fallback requires official Binance USD-M" -- and that guard is right: funding
    # provenance is part of what makes the snapshot canonical, and a cache in front of it is not
    # the same claim. The other desks reached the same split independently: klines through the
    # proxy, funding and exchangeInfo direct.
    #
    # The 418 risk that justifies the proxy comes from repeated full-history fetches. With
    # resume=True this backfills the months that are missing and re-reads nothing else, so the
    # exposure is a month of API calls per refresh rather than six years.
    _ = use_proxy
    header = (
        "# GENERATED by scripts/top40v5_refresh_forward.py -- do not edit.\n"
        "#\n"
        "# The operational twin of SNAPSHOT-BUILD.toml. It differs in the output directory and in\n"
        "# hard_end_exclusive, and nothing else, so the forward snapshot is the frozen one plus\n"
        "# more days rather than a second construction that happens to overlap. The frozen\n"
        "# snapshot is bound by the activation freeze and is never rebuilt.\n"
    )
    FORWARD_CONFIG.write_text(header + body, encoding="utf-8")
    return str(FORWARD_CONFIG.relative_to(REPO))


def _extent(snapshot: Path) -> pd.Timestamp | None:
    bars = snapshot / "bars.parquet"
    if not bars.is_file():
        return None
    return pd.Timestamp(pd.read_parquet(bars, columns=["open_time"])["open_time"].max())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="report state, fetch nothing")
    parser.add_argument("--as-of", default=None)
    arguments = parser.parse_args()

    as_of = arguments.as_of
    now = pd.Timestamp(as_of, tz="UTC") if as_of else pd.Timestamp.now(tz="UTC")
    target = _target_end(now)
    frozen_extent = _extent(FROZEN_DIR)
    forward_extent = _extent(FORWARD_DIR)

    print(f"now              {now}")
    print(f"frozen snapshot  through {frozen_extent}  (never rebuilt)")
    print(f"forward snapshot through {forward_extent or 'not built yet'}")
    print(f"target end       {target.date()}")

    if forward_extent is not None and forward_extent >= target - pd.Timedelta(hours=8):
        print("\nforward snapshot is already current; nothing to fetch")
        return 0

    use_proxy = _proxy_is_up()
    print(
        f"binance-proxy    (klines cache) "
        f"{'up, routing API calls through it' if use_proxy else 'down, going direct'}"
    )
    if not use_proxy:
        print(
            "  (repeated full-history fetches direct to Binance are what earned 418 bans"
            " on other desks; prefer bringing the proxy up)"
        )

    config = write_forward_config(target, use_proxy=use_proxy)
    print(f"wrote {config}")

    if arguments.check:
        print("\ncheck only; nothing fetched")
        return 0

    # Seed from the frozen snapshot's verified raw cache so the first build does not re-download
    # six years of archives it already has on disk.
    frozen_raw, forward_raw = FROZEN_DIR / "raw", FORWARD_DIR / "raw"
    if frozen_raw.is_dir() and not forward_raw.exists():
        print(f"seeding raw cache from {frozen_raw.relative_to(REPO)} (hardlinks, no copy)")
        FORWARD_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copytree(frozen_raw, forward_raw, copy_function=lambda s, d: Path(d).hardlink_to(s))

    from crypto_trade.tournament.snapshot import build_snapshot

    print("\nbuilding (resume=True: cached archives are reused, missing months fetched)...")
    summary = build_snapshot(
        FORWARD_CONFIG,
        FORWARD_DIR,
        FORWARD_MANIFEST,
        REPO / "reports-top40-v5" / "forward-common",
        resume=True,
    )
    new_extent = _extent(FORWARD_DIR)
    print(f"\nforward snapshot now through {new_extent}")
    print(
        json.dumps({k: v for k, v in summary.items() if isinstance(v, (int, str))}, indent=2)[:600]
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
