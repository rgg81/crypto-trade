"""Tests for the track-aware refresh dispatch added in Task 4.

`refresh_features_by_track` accepts a list of (symbols, features_dir, track)
tuples and routes each group through the right features module
(``crypto_trade.features.run_features`` for v1,
 ``crypto_trade.features_v2.run_features_v2`` for v2).
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from crypto_trade.live.data_pipeline import refresh_features_by_track


def test_refresh_features_dispatches_v1_only():
    groups = [(("BTCUSDT", "ETHUSDT"), Path("data/features"), "v1")]
    with patch("crypto_trade.features.run_features") as v1_run, \
         patch("crypto_trade.features_v2.run_features_v2") as v2_run, \
         patch("crypto_trade.features.list_groups", return_value=["all"]):
        refresh_features_by_track(
            groups, interval="8h", data_dir="data", feature_groups=("all",)
        )
        assert v1_run.call_count == 1
        assert v2_run.call_count == 0
        assert set(v1_run.call_args.kwargs["symbols"]) == {"BTCUSDT", "ETHUSDT"}
        assert v1_run.call_args.kwargs["output_dir"] == "data/features"


def test_refresh_features_dispatches_v2_only():
    groups = [(("DOGEUSDT", "SOLUSDT"), Path("data/features_v2"), "v2")]
    with patch("crypto_trade.features.run_features") as v1_run, \
         patch("crypto_trade.features_v2.run_features_v2") as v2_run, \
         patch("crypto_trade.features_v2.list_groups", return_value=["all"]):
        refresh_features_by_track(
            groups, interval="8h", data_dir="data", feature_groups=("all",)
        )
        assert v2_run.call_count == 1
        assert v1_run.call_count == 0
        assert set(v2_run.call_args.kwargs["symbols"]) == {"DOGEUSDT", "SOLUSDT"}
        assert v2_run.call_args.kwargs["output_dir"] == "data/features_v2"


def test_refresh_features_dispatches_combined():
    """A combined groups list dispatches v1 + v2 each to its own module exactly once."""
    groups = [
        (("BTCUSDT", "ETHUSDT"), Path("data/features"), "v1"),
        (("DOGEUSDT", "SOLUSDT"), Path("data/features_v2"), "v2"),
    ]
    with patch("crypto_trade.features.run_features") as v1_run, \
         patch("crypto_trade.features_v2.run_features_v2") as v2_run, \
         patch("crypto_trade.features.list_groups", return_value=["all"]), \
         patch("crypto_trade.features_v2.list_groups", return_value=["all"]):
        refresh_features_by_track(
            groups, interval="8h", data_dir="data", feature_groups=("all",)
        )
        assert v1_run.call_count == 1
        assert v2_run.call_count == 1


def test_refresh_features_unknown_track_raises():
    groups = [(("BTCUSDT",), Path("data/features"), "vX")]
    with pytest.raises(ValueError, match="unknown track"):
        refresh_features_by_track(
            groups, interval="8h", data_dir="data", feature_groups=("all",)
        )
