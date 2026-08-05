"""Acquire raw Binance USD-M data, derive the CUP-20 top-20 universe, write both snapshots."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from crypto_trade.cup20.config import IS_END, SEALED_END, load_config
from crypto_trade.cup20.snapshot import resolve_is_start, write_split_snapshots
from crypto_trade.cup20.universe import build_membership, weekly_reconstitution_times
from crypto_trade.tournament.pure_crypto_universe_v6 import (
    REVIEWED_ARCHIVE_ONLY_CRYPTO,
    current_contract_violations,
    symbol_policy_violations,
)
from crypto_trade.tournament.snapshot import build_snapshot

ACQUISITION_CONFIG = Path("tournament/cup20/snapshot-config.toml")
ACQUISITION_DIR = Path("data/cup20/acquisition")
TOURNAMENT_CONFIG = Path("tournament/cup20/config.toml")

# Two summaries, not one. The organiser's own summary describes BOTH sides of the cutoff -- how many
# distinct names the universe ever held, which of them enter it only during the holdout, how many
# reconstitutions there are in total -- and every one of those is a fact about the sealed window's
# composition. `sealed_only_members` named all sixteen outright, and `distinct_members` minus
# `distinct_is_members` re-derives the count even with the names removed. None of it is a team
# input; teams never need to know anything about the holdout's membership.
#
# So the team-visible file carries IS-window facts only (PUBLIC_SUMMARY_FIELDS below), and
# everything else -- along with the full-universe pure-crypto audit, which repeats the same roster
# and additionally identifies the post-cutoff delistings by name, undoing the contract-metadata
# censoring in snapshot.py -- moves under `private/`, which is gitignored, named in
# FORBIDDEN_PATTERNS and prohibited by the playbook. The audit stays hash-bound by the activation
# record from its new path: it is the attestation that cleared the WHOLE universe, and restricting
# it to IS members would both weaken the attestation and fail to close the leak anyway, since the
# post-cutoff delisters are themselves IS members.
PRIVATE_DIR = Path("tournament/cup20/private")
SUMMARY_PATH = Path("tournament/cup20/universe-summary.json")
PRIVATE_SUMMARY_PATH = PRIVATE_DIR / "universe-summary.json"
AUDIT_PATH = PRIVATE_DIR / "pure-crypto-audit.json"

# Selected explicitly by name rather than by removing sealed-side keys, so a field added to the
# organiser's summary later is private by default and becomes visible only by a deliberate edit
# here. Every one of these is already derivable by a team from the IS snapshot it holds.
PUBLIC_SUMMARY_FIELDS: tuple[str, ...] = (
    "is_start",
    "is_warmup_start",
    "is_end",
    "is_reconstitutions",
    "distinct_is_members",
    "is_manifest_sha256",
)


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


def pure_crypto_audit(
    members: list[str], metadata: pd.DataFrame, exchange_info: dict[str, object]
) -> dict[str, object]:
    """Verify every shipped CUP-20 member is a native crypto USDT-margined perpetual.

    NOT ``crypto_trade.tournament.pure_crypto_universe_v6.audit_pure_crypto_universe``. That
    function looks reusable and is not: it is an attestation of one specific frozen artifact, with
    ``tournament/top40/data_manifest.json`` and its SHA-256 compiled in as module constants
    (``DATA_MANIFEST_PATH`` / ``DATA_MANIFEST_SHA256``), so pointed at any other snapshot it fails
    on the binding rather than on the universe. Its *predicates*, though, are pure and carry the
    reviewed policy, so they are reused verbatim here and the snapshot-specific shell is not.

    Fails closed. Every member is checked at three independent levels -- the symbol's own name, the
    acquisition's contract metadata, and, for a contract still listed at build time, live
    exchangeInfo including underlying type and subtype. A member absent from live exchangeInfo has
    already delisted and has no contract left to inspect; it is reported rather than silently
    accepted, and separately flagged when it is not in the previously reviewed archive-only set.
    """
    records = {str(row["symbol"]): row for _, row in metadata.iterrows() if pd.notna(row["symbol"])}
    raw_symbols = exchange_info.get("symbols", [])
    contracts = {
        str(item["symbol"]): item
        for item in (raw_symbols if isinstance(raw_symbols, list) else [])
        if isinstance(item, dict) and item.get("symbol")
    }
    violations: dict[str, list[str]] = {}
    archive_only: list[str] = []
    for symbol in members:
        reasons = list(symbol_policy_violations(symbol))
        record = records.get(symbol)
        if record is None:
            reasons.append("metadata-row-missing")
        else:
            if not bool(record["is_crypto"]):
                reasons.append("metadata-is-crypto-false")
            for column, expected in (
                ("contract_type", "PERPETUAL"),
                ("quote_asset", "USDT"),
                ("margin_asset", "USDT"),
            ):
                if str(record[column]) != expected:
                    reasons.append(f"metadata-{column.replace('_', '-')}-not-{expected.lower()}")
        contract = contracts.get(symbol)
        if contract is None:
            archive_only.append(symbol)
        else:
            reasons.extend(current_contract_violations(contract, expected_symbol=symbol))
        if reasons:
            violations[symbol] = sorted(dict.fromkeys(reasons))
    if violations:
        raise SystemExit(f"CUP-20 pure-crypto audit failed: {json.dumps(violations, indent=2)}")
    return {
        "policy_id": "cup20-pure-crypto-usdt-perpetual-v1",
        "status": "PURE_CRYPTO_UNIVERSE_VERIFIED",
        "members_audited": len(members),
        "live_contracts_checked": sorted(set(members) & set(contracts)),
        "archive_only_members": sorted(archive_only),
        "archive_only_members_outside_reviewed_set": sorted(
            symbol for symbol in archive_only if symbol not in REVIEWED_ARCHIVE_ONLY_CRYPTO
        ),
    }


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
        minimum_scored_members=int(universe["minimum_scored_members"]),
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

    bars = pd.read_parquet(ACQUISITION_DIR / "bars.parquet")
    funding = pd.read_parquet(ACQUISITION_DIR / "funding.parquet")
    marks = pd.read_parquet(ACQUISITION_DIR / "mark_prices.parquet")
    metadata = pd.read_parquet(ACQUISITION_DIR / "contract_metadata.parquet")
    acquired = pd.read_parquet(ACQUISITION_DIR / "membership.parquet")
    exchange_info = json.loads((ACQUISITION_DIR / "exchange_info.json").read_text())

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

    # Persisted, not merely printed: the activation record binds this file, so the audit that
    # cleared the universe is frozen alongside the data it cleared. It lives under `private/`
    # because it necessarily names every member -- including the sixteen that enter the universe
    # only during the holdout -- and reports which of them had already delisted at build time,
    # which is precisely the fact snapshot.py censors out of the IS contract metadata.
    audit = pure_crypto_audit(members, metadata, exchange_info)
    PRIVATE_DIR.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print(f"pure-crypto audit: {audit['status']} over {audit['members_audited']} members")

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
    boundaries = pd.to_datetime(membership["reconstitution_time"], utc=True)
    summary = {
        "is_start": str(is_start),
        "is_warmup_start": str(pd.to_datetime(is_bars["open_time"], utc=True).min()),
        "is_end": str(IS_END),
        "sealed_end": str(SEALED_END),
        "distinct_members": len(members),
        "distinct_is_members": len(is_members),
        "sealed_only_members": sealed_only,
        "reconstitutions": int(boundaries.nunique()),
        "is_reconstitutions": int(boundaries[boundaries < IS_END].nunique()),
        "is_manifest_sha256": json.loads(is_paths.manifest.read_text())["manifest_sha256"],
        "sealed_manifest_sha256": json.loads(sealed_paths.manifest.read_text())["manifest_sha256"],
    }
    PRIVATE_SUMMARY_PATH.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")

    public = {field: summary[field] for field in PUBLIC_SUMMARY_FIELDS}
    public_text = json.dumps(public, indent=2, sort_keys=True) + "\n"
    # Post-condition, not a comment: no sealed-only member may be named in the team-visible file,
    # and the sealed side's own totals may not appear either. A future field whose VALUE happens to
    # carry a holdout name -- not only a field obviously called `sealed_...` -- fails the build
    # here rather than shipping.
    for name in sealed_only:
        if name in public_text:
            raise SystemExit(f"team-visible universe summary names sealed-only member {name}")
    if set(public) - set(PUBLIC_SUMMARY_FIELDS):
        raise SystemExit("team-visible universe summary carries an undeclared field")
    SUMMARY_PATH.write_text(public_text)
    print(public_text)


if __name__ == "__main__":
    main()
