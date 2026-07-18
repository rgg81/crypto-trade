from __future__ import annotations

import pandas as pd
import pytest

from crypto_trade.tournament import top40_amendment_0003_stage_stitch as stage_stitch
from crypto_trade.tournament import top40_amendment_0003_stitched as parent


def _series(start: pd.Timestamp, end: pd.Timestamp, value: float) -> pd.Series:
    index = pd.date_range(start, end, freq="1D")
    return pd.Series(value, index=index, name="net_return")


def test_stage_concat_uses_immutable_train_and_only_scored_validation() -> None:
    train = _series(
        parent.TRAIN_START,
        parent.VALIDATION_START - pd.Timedelta(days=1),
        0.01,
    )
    validation_replay = _series(parent.TRAIN_START, parent.PUBLIC_END, -0.02)
    stitched = stage_stitch._stage_concat(train, validation_replay)
    assert (stitched.loc[: parent.VALIDATION_START - pd.Timedelta(days=1)] == 0.01).all()
    assert (stitched.loc[parent.VALIDATION_START :] == -0.02).all()


def test_stage_concat_does_not_require_unscored_prefix_equality() -> None:
    train = _series(
        parent.TRAIN_START,
        parent.VALIDATION_START - pd.Timedelta(days=1),
        0.03,
    )
    validation_replay = _series(parent.TRAIN_START, parent.PUBLIC_END, -0.04)
    stitched = stage_stitch._stage_concat(train, validation_replay)
    assert stitched.loc[parent.TRAIN_START] == 0.03
    assert stitched.loc[parent.VALIDATION_START] == -0.04


def test_stage_concat_has_exact_gap_free_public_grid() -> None:
    train = _series(
        parent.TRAIN_START,
        parent.VALIDATION_START - pd.Timedelta(days=1),
        0.0,
    )
    validation_replay = _series(parent.TRAIN_START, parent.PUBLIC_END, 0.0)
    stitched = stage_stitch._stage_concat(train, validation_replay)
    assert stitched.index.equals(pd.date_range(parent.TRAIN_START, parent.PUBLIC_END, freq="1D"))
    assert not stitched.index.has_duplicates


def test_stage_concat_rejects_incomplete_train_grid() -> None:
    train = _series(
        parent.TRAIN_START + pd.Timedelta(days=1),
        parent.VALIDATION_START - pd.Timedelta(days=1),
        0.0,
    )
    validation_replay = _series(parent.TRAIN_START, parent.PUBLIC_END, 0.0)
    with pytest.raises(stage_stitch.StageStitchAddendumError):
        stage_stitch._stage_concat(train, validation_replay)


def test_stage_concat_rejects_incomplete_validation_replay_grid() -> None:
    train = _series(
        parent.TRAIN_START,
        parent.VALIDATION_START - pd.Timedelta(days=1),
        0.0,
    )
    validation_replay = _series(
        parent.TRAIN_START, parent.PUBLIC_END - pd.Timedelta(days=1), 0.0
    )
    with pytest.raises(stage_stitch.StageStitchAddendumError):
        stage_stitch._stage_concat(train, validation_replay)


def test_addendum_canonical_hash_is_order_independent() -> None:
    assert stage_stitch._sha256(
        stage_stitch._canonical({"b": 2, "a": 1})
    ) == stage_stitch._sha256(stage_stitch._canonical({"a": 1, "b": 2}))
