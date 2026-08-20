"""A team-visible snapshot the evaluator can replay, for unlimited research runs.

CUP-50 gave teams twelve charged trials and no way to run anything else, so nothing was iterated and
the field was twelve unchanged seeds. Research needs a loop that costs nothing, and a loop needs an
executable snapshot -- but the team-visible export deliberately carries no transaction open and no
mark price, because those are the organizer's and a strategy that can see them can optimise against
them.

So this synthesises the missing execution columns from what a team may already see: the open becomes
the previous bar's close, and every mark becomes the close of the bar it falls in. That is an
approximation, and it is the *only* thing separating a research run from an official one -- the
same evaluator, caps, risk unit and scorer run on top. The approximation is disclosed on every
result, and the official path cannot load one of these: a research snapshot announces itself and
`load_snapshot` refuses it.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from crypto_trade.cup50v2.regimes import monthly_regime_labels
from crypto_trade.cup50v2.snapshot import Snapshot

RESEARCH_NAMESPACE = "cup50v2-research-approximate"
EXECUTION_MODE = "research-approximate"


def _read(root: Path, name: str) -> pd.DataFrame:
    path = root / f"{name}.parquet"
    if not path.is_file():
        raise ValueError(f"team-visible snapshot is missing {name}")
    return pd.read_parquet(path)


def research_snapshot_from_team_visible(root: str | Path, *, regimes=None) -> Snapshot:
    """Build a replayable snapshot from the sanitized team-visible export.

    The synthesised open is the previous close of the same symbol, so a fill is priced at the last
    thing the strategy could have seen. Real execution happens at the next bar's open, which differs
    by the overnight gap; a research result is therefore close to an official one and never equal to
    it, and a team that tunes to the difference is tuning to nothing.
    """
    source = Path(root)
    bars = _read(source, "bars").copy()
    funding = _read(source, "funding").copy()
    membership = _read(source, "membership")
    metadata = _read(source, "contract_metadata")

    for column in ("open_time", "close_time"):
        bars[column] = pd.DatetimeIndex(pd.to_datetime(bars[column], utc=True))
    bars = bars.sort_values(["symbol", "open_time"], ignore_index=True)
    if "open" in bars:
        raise ValueError("team-visible bars must not carry a transaction open")
    # The first bar of a symbol has no previous close, so it opens at its own close: a fill there is
    # priced at the only observation that exists.
    previous = bars.groupby("symbol", sort=False)["close"].shift(1)
    bars["open"] = previous.fillna(bars["close"]).astype(float)

    funding["funding_time"] = pd.DatetimeIndex(pd.to_datetime(funding["funding_time"], utc=True))
    funding["settlement_time"] = funding["funding_time"].dt.floor("h")
    closes = bars.loc[:, ["symbol", "open_time", "close"]].rename(columns={"close": "mark_price"})
    closes["bar"] = closes["open_time"].dt.floor("8h")
    funding["bar"] = funding["settlement_time"].dt.floor("8h")
    funding = funding.merge(
        closes.loc[:, ["symbol", "bar", "mark_price"]], on=["symbol", "bar"], how="left"
    ).drop(columns=["bar"])
    funding["mark_price"] = funding.groupby("symbol", sort=False)["mark_price"].ffill().bfill()
    funding = funding.dropna(subset=["mark_price"]).reset_index(drop=True)

    marks = (
        bars.loc[:, ["symbol", "open_time", "close"]]
        .rename(columns={"open_time": "mark_time", "close": "mark_price"})
        .reset_index(drop=True)
    )
    terminal = pd.Timestamp(bars["open_time"].max()) + pd.Timedelta(hours=8)
    tail = (
        bars.sort_values("open_time")
        .groupby("symbol", sort=False)
        .tail(1)
        .loc[:, ["symbol", "close"]]
        .rename(columns={"close": "mark_price"})
    )
    tail["mark_time"] = terminal
    marks = pd.concat(
        [marks, tail.loc[:, ["mark_time", "symbol", "mark_price"]]], ignore_index=True
    )
    settlement = tail.copy()
    settlement["funding_time"] = terminal
    settlement["settlement_time"] = terminal
    settlement["funding_rate"] = 0.0
    funding = pd.concat(
        [funding, settlement.loc[:, funding.columns.intersection(settlement.columns)]],
        ignore_index=True,
    ).drop_duplicates(subset=["symbol", "funding_time"], keep="first")

    labels = monthly_regime_labels(bars, membership, policy=regimes) if regimes else {}
    return Snapshot(
        bars=bars,
        funding=funding,
        mark_prices=marks,
        membership=membership,
        contract_metadata=metadata,
        manifest_sha256="research-approximate",
        window_start=pd.Timestamp(bars["open_time"].min()),
        window_end=terminal,
        sealed=False,
        regime_labels=labels,
    )
