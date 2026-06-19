"""Tests for the canonical broad cross-sectional carry strategy (analysis/broad_carry.py).

Foundation verification (user: solid foundation, no errors; reproduce real scenarios):
  - DOLLAR-NEUTRAL: every active rebalance has sum(weights) == 0 (equal $ long and short).
  - NO-LOOKAHEAD: a weight at t depends only on funding <= t; future rows can't change it.
  - CARRY DIRECTION + INCOME: with constant prices and distinct constant funding, the book SHORTS
    the highest-funding coins / LONGS the lowest, and collects POSITIVE funding; price P&L == 0.
"""

from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "analysis"))
import broad_carry as bc  # noqa: E402


def _synth_universe(n_coins=8, n_rows=60, prices_constant=True):
    """N coins on a shared 8h grid; coin i has constant funding i*0.001 (distinct ranks)."""
    ot = np.arange(n_rows, dtype=np.int64) * (8 * 60 * 60 * 1000) + 1_600_000_000_000
    rng = np.random.default_rng(0)
    coins = {}
    for i in range(n_coins):
        if prices_constant:
            px = np.full(n_rows, 100.0)
        else:
            px = 100 * np.cumprod(1 + rng.normal(0, 0.01, n_rows))
        coins[f"C{i}USDT"] = pd.DataFrame(
            {"open": px, "close": px, "funding_rate": np.full(n_rows, i * 0.001),
             "quote_volume": 1e9},
            index=ot,
        )
    return coins


def test_dollar_neutral():
    coins = _synth_universe()
    _, w = bc.build_book(coins, m_fund=3, frac=0.25)
    active = w.abs().sum(axis=1) > 0
    assert active.any(), "expected some active rebalances"
    assert np.allclose(w[active].sum(axis=1), 0.0, atol=1e-12), "book is not dollar-neutral"


def test_no_lookahead():
    coins = _synth_universe(prices_constant=False)
    _, w_clean = bc.build_book(coins, m_fund=3, frac=0.25)
    k = 40
    corrupt = {s: d.copy() for s, d in coins.items()}
    for s in corrupt:
        corrupt[s].iloc[k:, :] = 1e9  # garbage in the entire future, all columns
    _, w_corrupt = bc.build_book(corrupt, m_fund=3, frac=0.25)
    assert np.allclose(w_clean.to_numpy()[:k], w_corrupt.to_numpy()[:k], equal_nan=True), \
        "look-ahead: a past weight changed when future data was corrupted"


def test_carry_direction_and_income():
    """Constant prices + distinct funding => short highest-funding, long lowest, funding > 0."""
    coins = _synth_universe(n_coins=8, prices_constant=True)
    book, w = bc.build_book(coins, m_fund=3, frac=0.25)
    assert np.allclose(book["price"], 0.0, atol=1e-12), "price P&L must be 0 with constant prices"
    # highest-funding coin (C7) is short (negative weight); lowest (C0) is long (positive)
    active = w.abs().sum(axis=1) > 0
    last = w[active].iloc[-1]
    assert last["C7USDT"] < 0, "highest-funding coin must be SHORT"
    assert last["C0USDT"] > 0, "lowest-funding coin must be LONG"
    # funding income strictly positive (collect the spread), no turnover after steady state
    assert (book["funding"][active] > 0).all(), "carry must collect positive funding income"


def test_build_book_returns_aligned_weights():
    coins = _synth_universe()
    book, w = bc.build_book(coins, m_fund=3, frac=0.25)
    assert len(book) == len(w), "book and weights must share the row index"
    assert (book.index == w.index).all(), "book and weights index must match"
