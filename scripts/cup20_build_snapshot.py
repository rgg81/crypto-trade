"""Acquire raw Binance USD-M data, derive the CUP-20 top-20 universe, write both snapshots."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from crypto_trade.cup20.config import IS_END, SEALED_END, load_config
from crypto_trade.cup20.snapshot import resolve_is_start, write_split_snapshots
from crypto_trade.cup20.universe import build_membership, weekly_reconstitution_times
from crypto_trade.tournament.pure_crypto_universe_v6 import audit_pure_crypto_universe
from crypto_trade.tournament.snapshot import build_snapshot

ACQUISITION_CONFIG = Path("tournament/cup20/snapshot-config.toml")
ACQUISITION_DIR = Path("data/cup20/acquisition")
TOURNAMENT_CONFIG = Path("tournament/cup20/config.toml")
SUMMARY_PATH = Path("tournament/cup20/universe-summary.json")
# Persisted, not merely printed: the activation record binds this file, so the audit that cleared
# the universe of non-crypto contracts is frozen alongside the data it cleared.
AUDIT_PATH = Path("tournament/cup20/pure-crypto-audit.json")


def acquire() -> None:
    """Download, checksum-verify and publish the wide acquisition snapshot."""
    build_snapshot(
        ACQUISITION_CONFIG,
        ACQUISITION_DIR,
        Path("tournament/cup20/data_manifest.json"),
        Path("reports-cup20/common"),
        resume=True,
    )


def daily_quote_volume(bars: pd.DataFrame) -> pd.DataFrame:
    """Sum 8h quote volume into UTC days: index=day, columns=symbol."""
    frame = bars[["open_time", "symbol", "quote_volume"]].copy()
    frame["day"] = pd.to_datetime(frame["open_time"], utc=True).dt.normalize()
    pivot = frame.pivot_table(index="day", columns="symbol", values="quote_volume", aggfunc="sum")
    full_days = pd.date_range(pivot.index.min(), pivot.index.max(), freq="D", tz="UTC")
    return pivot.reindex(full_days)


def eligibility(volume: pd.DataFrame, metadata: pd.DataFrame) -> pd.DataFrame:
    """A symbol is eligible on a day when it traded and its contract passes the crypto policy."""
    allowed = set(
        metadata.loc[
            metadata["is_crypto"].astype(bool)
            & metadata["contract_type"].astype(str).eq("PERPETUAL")
            & metadata["quote_asset"].astype(str).eq("USDT")
            & metadata["margin_asset"].astype(str).eq("USDT"),
            "symbol",
        ].astype(str)
    )
    frame = volume.notna()
    for column in frame.columns:
        if column not in allowed:
            frame[column] = False
    return frame


def _is_visible_symbols(membership: pd.DataFrame) -> set[str]:
    """Symbols that actually appear in membership STRICTLY BEFORE the IS cutoff.

    This is the only symbol set an in-sample observer is entitled to see price data for.
    Restricting the IS side of every split to the union of IS and sealed membership -- the obvious
    reading, and the one this script's first draft used -- would ship full in-sample bars, funding
    and mark prices for a symbol that onboarded before the cutoff but only ever enters the top-20
    during the SEALED window. That symbol's in-sample rows are individually innocent, but its
    PRESENCE in the IS snapshot is future universe composition: it tells a team, before it has run
    a single backtest, which of today's mid-cap perpetuals the organiser already knows will matter
    later. Exactly the leak class ``crypto_trade/cup20/snapshot.py`` censors out of
    ``contract_metadata``, arriving instead through the price panel.

    ``< IS_END``, not ``<=``: ``write_split_snapshots`` puts a reconstitution AT the cutoff on the
    sealed side, so a boundary-time membership row is a sealed fact and must not widen the IS
    symbol set.
    """
    times = pd.to_datetime(membership["reconstitution_time"], utc=True)
    return set(membership.loc[times < IS_END, "symbol"].astype(str))


def build_universe(
    bars: pd.DataFrame, metadata: pd.DataFrame, universe: dict[str, object]
) -> tuple[pd.DataFrame, pd.Timestamp]:
    """Derive point-in-time CUP-20 membership and the first boundary that reaches target size."""
    lookback_days = int(universe["lookback_days"])
    target_size = int(universe["target_size"])
    volume = daily_quote_volume(bars)
    eligible = eligibility(volume, metadata)
    boundaries = weekly_reconstitution_times(
        pd.Timestamp(volume.index.min()) + pd.Timedelta(days=lookback_days),
        SEALED_END,
        weekday=int(universe["reconstitution_weekday"]),
    )
    membership = build_membership(
        volume,
        eligible=eligible,
        reconstitution_times=boundaries,
        lookback_days=lookback_days,
        target_size=target_size,
        entry_rank=int(universe["entry_rank"]),
        exit_rank=int(universe["exit_rank"]),
    )
    return membership, resolve_is_start(membership, target_size=target_size)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the CUP-20 IS and sealed snapshots")
    parser.add_argument("--skip-acquire", action="store_true", help="reuse the acquisition dir")
    parser.add_argument(
        "--acquire-only",
        action="store_true",
        help="run only the raw acquisition and stop (the long pole; safe to run detached)",
    )
    arguments = parser.parse_args()

    if not arguments.skip_acquire:
        acquire()
    if arguments.acquire_only:
        print("acquisition complete; re-run with --skip-acquire to derive the universe")
        return

    audit = audit_pure_crypto_universe(ACQUISITION_DIR)
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(json.dumps(audit, indent=2, sort_keys=True, default=str) + "\n")
    print(f"pure-crypto audit: {audit.get('status', audit)}")

    bars = pd.read_parquet(ACQUISITION_DIR / "bars.parquet")
    funding = pd.read_parquet(ACQUISITION_DIR / "funding.parquet")
    marks = pd.read_parquet(ACQUISITION_DIR / "mark_prices.parquet")
    metadata = pd.read_parquet(ACQUISITION_DIR / "contract_metadata.parquet")
    acquired = pd.read_parquet(ACQUISITION_DIR / "membership.parquet")

    config = dict(load_config(TOURNAMENT_CONFIG).raw["universe"])
    membership, is_start = build_universe(bars, metadata, config)
    membership = membership.loc[membership["reconstitution_time"] >= is_start].reset_index(
        drop=True
    )

    # Containment: every CUP-20 member must exist in the audited acquisition universe. Checked on
    # the SHIPPED membership, after the IS_START filter: the CUP-20 grid begins as soon as any
    # symbol has a full lookback, which is earlier than the acquisition's own evaluation start, and
    # a mismatch confined to boundaries that are then discarded is not a fact about the tournament.
    missing = set(membership["symbol"]) - set(acquired["symbol"].astype(str))
    if missing:
        raise SystemExit(f"CUP-20 members absent from the acquisition universe: {sorted(missing)}")

    members = sorted(set(membership["symbol"].astype(str)))
    is_members = _is_visible_symbols(membership)
    sealed_only = sorted(set(members) - is_members)

    def restrict(frame: pd.DataFrame, column: str) -> pd.DataFrame:
        """Keep IS-side rows only for IS-visible symbols; sealed-side rows for every member.

        A single frame is enough because ``write_split_snapshots`` splits on the same cutoff: rows
        kept below ``IS_END`` land in the IS snapshot and rows kept at or above it land in the
        sealed one, so per-side symbol scoping composes with the per-side time slicing.

        No lower time bound. The charter's evidence-layer table defines the warm-up window as
        "symbol listing -> IS_START", so an IS-visible symbol ships every bar the acquisition holds
        for it. Truncating warm-up to ``is_start - lookback_days`` would supply exactly enough
        history to reconstruct membership and not one bar more, silently capping the formation
        horizons lanes 01, 03 and 06 are chartered to explore -- and earlier history can never be a
        leak, since a row before the cutoff says nothing about a row after it.
        """
        times = pd.to_datetime(frame[column], utc=True)
        symbols = frame["symbol"].astype(str)
        in_sample = (times < IS_END) & symbols.isin(is_members)
        sealed = (times >= IS_END) & symbols.isin(members)
        return frame.loc[in_sample | sealed]

    is_paths, sealed_paths = write_split_snapshots(
        restrict(bars, "open_time"),
        restrict(funding, "funding_time"),
        restrict(marks, "mark_time"),
        membership,
        # IS-visible symbols only, on BOTH sides. `write_split_snapshots` ships the timeless
        # metadata frame whole into each split, so scoping it is the only way to keep a
        # sealed-only member's row out of the IS snapshot -- and a metadata row for a symbol with
        # no bars is both the same future-composition leak and an inconsistency naive team code
        # would trip over. The organiser's full-truth metadata, including sealed-only members,
        # remains in data/cup20/acquisition/contract_metadata.parquet, pinned by
        # tournament/cup20/data_manifest.json; nothing in the evaluation path reads the split
        # snapshots' copy.
        metadata.loc[metadata["symbol"].astype(str).isin(is_members)],
        is_root="data/cup20/is",
        sealed_root="data/cup20/sealed",
        is_end=IS_END,
        sealed_end=SEALED_END,
    )
    is_bars = pd.read_parquet(is_paths.bars, columns=["open_time"])
    summary = {
        "is_start": str(is_start),
        "is_warmup_start": str(pd.to_datetime(is_bars["open_time"], utc=True).min()),
        "is_end": str(IS_END),
        "sealed_end": str(SEALED_END),
        "distinct_members": len(members),
        "distinct_is_members": len(is_members),
        "sealed_only_members": sealed_only,
        "reconstitutions": int(membership["reconstitution_time"].nunique()),
        "is_manifest_sha256": json.loads(is_paths.manifest.read_text())["manifest_sha256"],
        "sealed_manifest_sha256": json.loads(sealed_paths.manifest.read_text())["manifest_sha256"],
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
