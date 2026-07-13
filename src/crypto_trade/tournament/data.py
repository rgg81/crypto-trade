"""Point-in-time universe and data-manifest helpers for the Top-40 tournament."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Sequence
from pathlib import Path

import numpy as np
import pandas as pd

STABLE_BASES = frozenset(
    {
        "BUSD",
        "DAI",
        "FDUSD",
        "TUSD",
        "USDC",
        "USDP",
        "USDT",
        # TerraClassicUSD remains a stablecoin base for universe-classification purposes even
        # after its depeg; volatility or a broken peg does not turn it into an alpha asset.
        "USTC",
    }
)
# Binance currently classifies tokenized precious metals as ``underlyingType=COIN``.  They are
# tradable tokens, but their economic underlying is not crypto and the tournament excludes them.
NON_CRYPTO_BASES = frozenset({"PAXG", "XAUT"})
# Exact legacy leveraged-token bases. Suffix matching is unsafe because legitimate coins such as
# JUP and SYRUP end in ``UP``. Binance's USD-M archive currently has no leveraged-token futures,
# but this denylist keeps the rule deterministic if a legacy symbol is encountered.
LEVERAGED_BASES = frozenset(
    {
        "1INCHDOWN",
        "1INCHUP",
        "AAVEDOWN",
        "AAVEUP",
        "ADADOWN",
        "ADAUP",
        "BCHDOWN",
        "BCHUP",
        "BNBDOWN",
        "BNBUP",
        "BTCDOWN",
        "BTCUP",
        "DOTDOWN",
        "DOTUP",
        "EOSDOWN",
        "EOSUP",
        "ETHBEAR",
        "ETHBULL",
        "ETHDOWN",
        "ETHUP",
        "FILDOWN",
        "FILUP",
        "LINKDOWN",
        "LINKUP",
        "LTCDOWN",
        "LTCUP",
        "SUSHIDOWN",
        "SUSHIUP",
        "SXPDOWN",
        "SXPUP",
        "TRXDOWN",
        "TRXUP",
        "UNIDOWN",
        "UNIUP",
        "XLMDOWN",
        "XLMUP",
        "XRPDOWN",
        "XRPUP",
        "YFIDOWN",
        "YFIUP",
    }
)


def is_eligible_usdt_perpetual(symbol: str) -> bool:
    """Apply deterministic name-level exclusions before point-in-time liquidity selection."""
    if not symbol.endswith("USDT") or not symbol.isascii():
        return False
    base = symbol[:-4]
    if base in STABLE_BASES or base in NON_CRYPTO_BASES or base in LEVERAGED_BASES:
        return False
    return bool(base)


def point_in_time_top40(
    bars: pd.DataFrame,
    contract_metadata: pd.DataFrame,
    reconstitution_times: Sequence[pd.Timestamp],
    *,
    top_n: int = 40,
    trailing_days: int = 30,
    min_history_days: int = 30,
    bars_per_day: int = 3,
) -> pd.DataFrame:
    """Build weekly/monthly Top-N membership using only completed prior UTC days.

    Input columns are ``open_time``, ``symbol``, and ``quote_volume``.  The caller decides the
    reconstitution cadence; the charter uses Monday 00:00 UTC.  A symbol must have observations on
    at least ``min_history_days`` distinct prior dates and on the immediately preceding UTC date.
    Ties are resolved by symbol, making the output deterministic.
    """
    required = {"open_time", "symbol", "quote_volume"}
    missing = required - set(bars.columns)
    if missing:
        raise ValueError(f"bars missing columns: {sorted(missing)}")
    metadata_required = {
        "symbol",
        "contract_type",
        "quote_asset",
        "margin_asset",
        "is_crypto",
        "onboard_date",
        "delivery_date",
    }
    metadata_missing = metadata_required - set(contract_metadata.columns)
    if metadata_missing:
        raise ValueError(f"contract_metadata missing columns: {sorted(metadata_missing)}")
    if top_n < 1 or trailing_days < 1 or min_history_days < 1 or bars_per_day < 1:
        raise ValueError(
            "top_n, trailing_days, min_history_days, and bars_per_day must be positive"
        )

    frame = bars.loc[:, ["open_time", "symbol", "quote_volume"]].copy()
    frame["open_time"] = pd.to_datetime(frame["open_time"], utc=True)
    frame = frame[frame["symbol"].map(is_eligible_usdt_perpetual)]
    frame["date"] = frame["open_time"].dt.floor("D")
    daily = frame.groupby(["date", "symbol"], as_index=False, observed=True).agg(
        quote_volume=("quote_volume", "sum"), bars=("open_time", "nunique")
    )
    daily = daily[daily["bars"] == bars_per_day].sort_values(["date", "symbol"])
    metadata = contract_metadata.loc[:, sorted(metadata_required)].copy()
    if metadata["symbol"].duplicated().any():
        raise ValueError("contract_metadata contains duplicate symbols")
    if any(not isinstance(value, (bool, np.bool_)) for value in metadata["is_crypto"]):
        raise ValueError("contract_metadata.is_crypto must contain booleans")
    metadata["onboard_date"] = pd.to_datetime(metadata["onboard_date"], utc=True)
    metadata["delivery_date"] = pd.to_datetime(metadata["delivery_date"], utc=True)

    rows: list[dict[str, object]] = []
    for raw_time in sorted(pd.to_datetime(list(reconstitution_times), utc=True)):
        as_of = pd.Timestamp(raw_time)
        if as_of.weekday() != 0 or as_of != as_of.floor("D"):
            raise ValueError("reconstitution_times must be Monday 00:00 UTC")
        active_metadata = metadata[
            (metadata["contract_type"] == "PERPETUAL")
            & (metadata["quote_asset"] == "USDT")
            & (metadata["margin_asset"] == "USDT")
            & metadata["is_crypto"]
            & (metadata["onboard_date"] <= as_of)
            & (metadata["delivery_date"].isna() | (metadata["delivery_date"] > as_of))
        ]
        active_symbols = set(active_metadata["symbol"])
        start = as_of.floor("D") - pd.Timedelta(days=trailing_days)
        prior_date = as_of.floor("D") - pd.Timedelta(days=1)
        history = daily[(daily["date"] >= start) & (daily["date"] < as_of.floor("D"))]
        if history.empty:
            continue
        stats = history.groupby("symbol", observed=True).agg(
            trailing_quote_volume=("quote_volume", "median"),
            history_days=("date", "nunique"),
            last_date=("date", "max"),
        )
        eligible = stats[
            (stats["history_days"] >= min_history_days) & (stats["last_date"] == prior_date)
        ].copy()
        eligible = eligible.loc[eligible.index.isin(active_symbols)]
        eligible = eligible.sort_values(
            ["trailing_quote_volume"], ascending=False, kind="mergesort"
        )
        # A second stable symbol sort resolves exact volume ties without peeking forward.
        eligible = (
            eligible.reset_index()
            .sort_values(
                ["trailing_quote_volume", "symbol"],
                ascending=[False, True],
                kind="mergesort",
            )
            .head(top_n)
        )
        for rank, record in enumerate(eligible.itertuples(index=False), start=1):
            rows.append(
                {
                    "reconstitution_time": as_of,
                    "symbol": record.symbol,
                    "liquidity_rank": rank,
                    "trailing_quote_volume": float(record.trailing_quote_volume),
                }
            )
    return pd.DataFrame(
        rows,
        columns=(
            "reconstitution_time",
            "symbol",
            "liquidity_rank",
            "trailing_quote_volume",
        ),
    )


def eligible_at(membership: pd.DataFrame, timestamp: pd.Timestamp) -> tuple[str, ...]:
    """Return the most recent point-in-time constituent set at ``timestamp``."""
    if membership.empty:
        return ()
    times = pd.to_datetime(membership["reconstitution_time"], utc=True)
    timestamp = pd.Timestamp(timestamp)
    timestamp = (
        timestamp.tz_localize("UTC") if timestamp.tzinfo is None else timestamp.tz_convert("UTC")
    )
    valid_times = times[times <= timestamp]
    if valid_times.empty:
        return ()
    latest = valid_times.max()
    mask = times == latest
    return tuple(membership.loc[mask].sort_values("liquidity_rank")["symbol"])


def sha256_manifest(
    paths: Iterable[str | Path], *, root: str | Path
) -> tuple[str, list[dict[str, object]]]:
    """Hash file names, sizes, and bytes into one reproducible dataset manifest digest."""
    root_path = Path(root).resolve()
    digest = hashlib.sha256()
    entries: list[dict[str, object]] = []
    for raw_path in sorted((Path(path).resolve() for path in paths), key=lambda path: str(path)):
        relative = raw_path.relative_to(root_path).as_posix()
        file_digest = hashlib.sha256()
        with raw_path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                file_digest.update(chunk)
        entry = {
            "path": relative,
            "size": raw_path.stat().st_size,
            "sha256": file_digest.hexdigest(),
        }
        entries.append(entry)
        digest.update(f"{relative}\0{entry['size']}\0{entry['sha256']}\n".encode())
    return digest.hexdigest(), entries
