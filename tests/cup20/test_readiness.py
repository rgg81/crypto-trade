"""The pre-start readiness gate, and the two ways it could pass while proving nothing.

The gate's whole value is that it exercises the real pipeline on the real data, so the mutation
that matters is not "it raises when it should" -- it is **vacuity**. A reference strategy that
quietly stopped trading would still drive every stage to completion: ``generate_targets`` would
emit a frame of zeros, the evaluator would return a flat book, every floor would fail without
anything raising, and the script would print ``READINESS PASSED`` having proved that an empty book
can be scored. Nothing in the script itself can notice that. These tests are what does.

The second half pins the mark-coverage stage at its own boundary: it must NAME the symbol, because
the entire reason it exists is that the alternative -- discovering the same fact as a stack trace
from inside the evaluator, forty minutes into a team's first backtest -- is what happened.
"""

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from crypto_trade.cup20.config import IS_END, load_config
from crypto_trade.cup20.metrics import is_folds
from crypto_trade.cup20.scored_metrics import (
    ASSEMBLED_METRIC_KEYS,
    MetricProvenance,
    ScoredVector,
)
from crypto_trade.cup20.snapshot import Snapshot
from crypto_trade.tournament.protocol import DecisionContext

_SPEC = importlib.util.spec_from_file_location(
    "cup20_readiness", Path(__file__).resolve().parents[2] / "scripts" / "cup20_readiness.py"
)
readiness = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(readiness)

MONDAY = pd.Timestamp("2021-01-04T00:00:00Z")


def _context(decision_time, symbols, gradients):
    """A past-only context in which each symbol's close rises by its own constant gradient."""
    times = pd.date_range(
        end=decision_time, periods=readiness.REFERENCE_LOOKBACK_BARS + 1, freq="8h"
    )
    bars = {
        symbol: pd.DataFrame(
            {
                "open_time": times,
                "close": 100.0 * (1.0 + gradient) ** np.arange(len(times)),
            }
        )
        for symbol, gradient in zip(symbols, gradients, strict=True)
    }
    return DecisionContext(
        decision_time=decision_time,
        bars=bars,
        funding=pd.DataFrame(),
        auxiliary={},
        eligible_symbols=list(symbols),
    )


def _twelve():
    symbols = [f"S{index:02d}USDT" for index in range(12)]
    gradients = [0.001 * (index + 1) for index in range(12)]  # S00 worst, S11 best
    return symbols, gradients


def test_the_reference_load_actually_trades_both_sides():
    """Kills the mutation that makes this whole gate vacuous: a reference book that stops trading.

    A strategy returning ``None`` or ``{}`` everywhere drives every pipeline stage to completion
    without raising, so ``READINESS PASSED`` would then mean only that an empty book can be scored.
    """
    symbols, gradients = _twelve()
    weights = readiness.WeeklyCrossSectionalReversal().target_weights(
        _context(MONDAY, symbols, gradients), seed=1
    )
    assert weights is not None and weights, "the reference load emitted no book at all"
    longs = {symbol for symbol, weight in weights.items() if weight > 0}
    shorts = {symbol for symbol, weight in weights.items() if weight < 0}
    assert len(longs) == readiness.REFERENCE_SLEEVE
    assert len(shorts) == readiness.REFERENCE_SLEEVE
    assert sum(abs(weight) for weight in weights.values()) == pytest.approx(1.0)
    # Reversal, not momentum: the weakest five are bought and the strongest five sold. Asserting
    # the direction is what keeps this from passing on a book that trades both sides at random.
    assert longs == set(symbols[:5])
    assert shorts == set(symbols[-5:])


def test_the_reference_load_holds_between_weekly_rebalances():
    """Kills the mutation: rebalancing at every 8h boundary, which pins the run against the
    participation cap and tests the caps instead of the pipeline."""
    symbols, gradients = _twelve()
    strategy = readiness.WeeklyCrossSectionalReversal()
    for offset in (8, 16):
        held = strategy.target_weights(
            _context(MONDAY + pd.Timedelta(hours=offset), symbols, gradients), seed=1
        )
        assert held is None, f"the reference load rebalanced {offset}h after its weekly boundary"
    tuesday = strategy.target_weights(
        _context(MONDAY + pd.Timedelta(days=1), symbols, gradients), seed=1
    )
    assert tuesday is None


def test_a_universe_too_thin_for_both_sides_asks_to_be_flat_rather_than_holding():
    """``{}`` and ``None`` are different instructions and the difference is load-bearing: ``None``
    would carry the previous week's book forward into a cross-section that can no longer support
    it, which is a position nobody asked for."""
    symbols, gradients = _twelve()
    thin = readiness.WeeklyCrossSectionalReversal().target_weights(
        _context(MONDAY, symbols[:9], gradients[:9]), seed=1
    )
    assert thin == {}


def test_a_symbol_without_enough_history_is_skipped_rather_than_priced_off_a_short_window():
    symbols, gradients = _twelve()
    context = _context(MONDAY, symbols, gradients)
    short = dict(context.bars)
    short["S00USDT"] = short["S00USDT"].iloc[-3:]
    truncated = DecisionContext(
        decision_time=MONDAY,
        bars=short,
        funding=context.funding,
        auxiliary={},
        eligible_symbols=list(symbols),
    )
    weights = readiness.WeeklyCrossSectionalReversal().target_weights(truncated, seed=1)
    assert "S00USDT" not in weights, "a symbol with three bars was ranked against symbols with 22"
    assert len(weights) == 2 * readiness.REFERENCE_SLEEVE


# --- the mark-coverage stage, at its own boundary


def _snapshot(*, mark_symbols=("AUSDT", "BUSDT")):
    times = pd.date_range("2021-01-04T00:00:00Z", periods=9, freq="8h")
    symbols = ("AUSDT", "BUSDT")
    bars = pd.concat(
        [
            pd.DataFrame({"open_time": times, "symbol": symbol, "open": 100.0, "close": 100.0})
            for symbol in symbols
        ],
        ignore_index=True,
    )
    marks = pd.concat(
        [
            pd.DataFrame({"mark_time": times, "symbol": symbol, "mark_price": 100.0})
            for symbol in mark_symbols
        ],
        ignore_index=True,
    )
    membership = pd.DataFrame(
        {
            "reconstitution_time": [times[0]] * len(symbols),
            "symbol": list(symbols),
            "liquidity_rank": [1, 2],
            "trailing_quote_volume": [1e9, 1e8],
        }
    )
    return Snapshot(bars, pd.DataFrame(), marks, membership, pd.DataFrame(), manifest_sha256="t")


def test_the_mark_coverage_stage_passes_a_fully_marked_snapshot():
    assert readiness.check_mark_coverage(_snapshot()) == 2


def test_the_mark_coverage_stage_names_the_symbol_and_the_first_boundary():
    """Kills the mutation: failing with a bare exit code, or with the count alone.

    The organiser has to know WHICH symbol to look at; the alternative to naming it is the raise
    that this gate exists to pre-empt, which arrives from inside the evaluator and names only the
    boundary it happened to reach first.
    """
    with pytest.raises(SystemExit) as failure:
        readiness.check_mark_coverage(_snapshot(mark_symbols=("AUSDT",)))
    message = str(failure.value)
    assert "BUSDT" in message
    assert "9 (boundary, symbol) pairs" in message
    assert "2021-01-04 00:00:00+00:00" in message


def test_the_adjudication_call_matches_the_scoring_stack_it_calls():
    """Kills the mutation this script actually shipped with: a missing keyword argument.

    The pre-flight's last stage runs seven minutes after its first, so a signature drift between
    the script and `adjudicate_candidate` surfaces at the worst possible moment -- after the whole
    evaluation, on the day the organiser is trying to dispatch teams. This pins the call against
    the real frozen config with a synthetic vector, in milliseconds.

    The vector's VALUES are arbitrary; only its shape and provenance are load-bearing here, and
    `adjudicate_candidate` refuses a bare mapping outright, so a vector without provenance would
    not reach the signature at all.
    """
    raw = load_config(Path("tournament/cup20/config.toml")).raw
    is_start = pd.Timestamp("2020-08-17T00:00:00Z")
    scored = ScoredVector(
        dict.fromkeys(ASSEMBLED_METRIC_KEYS, 0.5),
        MetricProvenance(
            stage="in_sample",
            window_start=is_start,
            window_end=IS_END,
            folds=is_folds(is_start, IS_END),
        ),
    )
    verdict = readiness.adjudicate(scored, raw)
    assert verdict.team_id == "reference"
    assert set(verdict.gates.checks) >= {"net_sharpe", "max_drawdown", "trade_count"}
    # The in-sample drawdown floor, not the holdout's rebased 0.25: a readiness run that scored
    # the reference book against section 8's scale would report a verdict nobody asked for.
    assert float(raw["floors"]["max_drawdown"]) == 0.20
