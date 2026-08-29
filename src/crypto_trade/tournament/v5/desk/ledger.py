"""Append-invariant ledgers: a row is written once and never revised.

Six months of forward paper produces exactly one thing -- an unedited record. Everything else about
these desks is reconstructible; the record is not. So the ledger's only real job is to make a
rewrite *fail* rather than succeed quietly.

:func:`append_rows` re-reads what is already on disk and compares every overlapping row field by
field. If a value that was published before comes back different, it raises
:class:`AppendInvarianceError` naming the key, the column and both values, and **writes nothing**.
That is deliberately louder than repairing the row: a silent correction leaves a record that looks
consistent and is not, and a difference between what was published and what the evaluator now
produces is the single most informative event this system can observe.

The exception is evidence. Do not delete the ledger to clear it.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


class AppendInvarianceError(RuntimeError):
    """A row already on disk came back different. Nothing was written."""


def read_ledger(path: str | Path) -> pd.DataFrame:
    resolved = Path(path)
    if not resolved.is_file():
        return pd.DataFrame()
    return pd.read_parquet(resolved)


def append_rows(path: str | Path, rows: pd.DataFrame, *, key: str) -> int:
    """Append only genuinely new rows; refuse if an existing one changed.

    Returns the number of rows added. Compares on ``key`` -- the decision boundary for a returns
    ledger -- because a boundary is the unit the desk publishes and re-publishing one is exactly
    the event this guards against.
    """

    resolved = Path(path)
    if rows.empty:
        return 0
    incoming = rows.sort_values(key).reset_index(drop=True)
    existing = read_ledger(resolved)

    if not existing.empty:
        overlap = incoming[incoming[key].isin(set(existing[key]))]
        if not overlap.empty:
            prior = existing.set_index(key)
            fresh = overlap.set_index(key)
            shared = [c for c in fresh.columns if c in prior.columns]
            for boundary in fresh.index:
                for column in shared:
                    before, after = prior.loc[boundary, column], fresh.loc[boundary, column]
                    same = (
                        bool(pd.isna(before) and pd.isna(after))
                        or (
                            abs(float(before) - float(after)) <= 1e-12
                            if isinstance(before, (int, float)) and not isinstance(before, bool)
                            else before == after
                        )
                    )
                    if not same:
                        raise AppendInvarianceError(
                            f"{resolved.name}: row {boundary} column {column} was published as "
                            f"{before!r} and now evaluates to {after!r}; nothing written"
                        )

    added = incoming[~incoming[key].isin(set(existing[key]))] if not existing.empty else incoming
    if added.empty:
        return 0
    combined = pd.concat([existing, added], ignore_index=True).sort_values(key)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    combined.reset_index(drop=True).to_parquet(resolved)
    return int(len(added))


__all__ = ["AppendInvarianceError", "append_rows", "read_ledger"]
