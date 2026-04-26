"""Tests for the v1/v2 features CLI flag (Task 13)."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from crypto_trade.main import build_parser


def test_features_track_flag_defaults_to_v1():
    parser = build_parser()
    args = parser.parse_args(["features", "--symbols", "BTCUSDT", "--interval", "8h"])
    assert args.track == "v1"


def test_features_track_flag_accepts_v2():
    parser = build_parser()
    args = parser.parse_args(
        ["features", "--symbols", "DOGEUSDT", "--interval", "8h", "--track", "v2"]
    )
    assert args.track == "v2"


def test_cmd_features_v2_dispatches_to_features_v2():
    """When --track v2 is given, _cmd_features routes through crypto_trade.features_v2.run_features_v2."""
    from crypto_trade.config import Settings
    from crypto_trade.main import _cmd_features

    settings = Settings(binance_api_key="", binance_api_secret="")
    parser = build_parser()
    args = parser.parse_args(
        [
            "features",
            "--symbols", "DOGEUSDT,SOLUSDT",
            "--interval", "8h",
            "--format", "parquet",
            "--track", "v2",
        ]
    )
    with patch("crypto_trade.features_v2.run_features_v2", return_value=[]) as v2_run, \
         patch("crypto_trade.features_v2.list_groups", return_value=["all"]), \
         patch("crypto_trade.features.run_features") as v1_run:
        _cmd_features(args, settings)
        assert v2_run.call_count == 1
        assert v1_run.call_count == 0
        assert set(v2_run.call_args.kwargs["symbols"]) == {"DOGEUSDT", "SOLUSDT"}
        # Output_dir defaults to data/features_v2 when --output is not given and track==v2
        assert v2_run.call_args.kwargs["output_dir"].endswith("features_v2")


def test_cmd_features_v1_dispatches_to_features():
    from crypto_trade.config import Settings
    from crypto_trade.main import _cmd_features

    settings = Settings(binance_api_key="", binance_api_secret="")
    parser = build_parser()
    args = parser.parse_args(
        [
            "features",
            "--symbols", "BTCUSDT",
            "--interval", "8h",
            "--format", "parquet",
        ]
    )
    with patch("crypto_trade.features.run_features", return_value=[]) as v1_run, \
         patch("crypto_trade.features.list_groups", return_value=["all"]), \
         patch("crypto_trade.features_v2.run_features_v2") as v2_run:
        _cmd_features(args, settings)
        assert v1_run.call_count == 1
        assert v2_run.call_count == 0
        assert v1_run.call_args.kwargs["output_dir"].endswith("features")


def test_features_list_track_v2_lists_v2_groups(capsys):
    """`features --list --track v2` prints v2 groups, not v1."""
    from crypto_trade.config import Settings
    from crypto_trade.main import _cmd_features

    settings = Settings(binance_api_key="", binance_api_secret="")
    parser = build_parser()
    args = parser.parse_args(["features", "--list", "--track", "v2"])

    with patch(
        "crypto_trade.features_v2.list_groups", return_value=["regime", "tail_risk"]
    ):
        _cmd_features(args, settings)
    out = capsys.readouterr().out
    assert "v2 feature groups" in out
    assert "regime" in out
    assert "tail_risk" in out
