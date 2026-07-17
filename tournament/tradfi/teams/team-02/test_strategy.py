"""team-02 team-owned tests for strategy.build_raw_weights.

Static-scan constraint (harness.scan_sources runs over EVERY team .py): this file may
import ONLY the harness-whitelisted roots (numpy, pandas, ...) plus the team-local
`strategy` module. It therefore does NOT import pytest / sys / pathlib / tournament — it
builds self-contained synthetic panels and relies on bare `assert` + `test_*` collection.

Covered (research_brief.md PART D.6):
  (a) future-bar corruption self-check — mangle bars strictly AFTER a cut; weights at/before
      the cut must be bit-identical (past-only property).
  (b) determinism — two calls on identical inputs give a bit-identical frame.
  (c) NaN-close day forces a NaN weight for that name (no EWM bridging a missing bar).
  (d) output index/columns == pn['close'] index/columns.
  (e) unused-aux honesty — runs with aux['vix']=None (and no seed used at all).
Plus a truncated-replay equivalence check mirroring the mechanical harness.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from strategy import build_raw_weights

_N_ROWS = 500
_TICKERS = [f"AAA{i:02d}USDT" for i in range(12)]


def _make_panels(n_rows: int = _N_ROWS, seed: int = 0) -> dict[str, pd.DataFrame]:
    """Synthetic positive OHLCV panels (dates x tickers), DatetimeIndex, no NaNs.

    Prices are seeded geometric random walks so `high >= close >= low` and everything is
    strictly positive (mirrors the frozen snapshot's ragged-but-positive bars minus the
    ragged starts, which are exercised separately by the NaN-close test)."""
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2016-01-04", periods=n_rows)
    close = {}
    high = {}
    low = {}
    open_ = {}
    vol = {}
    for t in _TICKERS:
        rets = rng.normal(0.0003, 0.02, size=n_rows)
        c = 100.0 * np.cumprod(1.0 + rets)
        span = np.abs(rng.normal(0.0, 0.01, size=n_rows)) * c
        close[t] = c
        high[t] = c + span
        low[t] = np.maximum(c - span, 0.01)
        open_[t] = c * (1.0 + rng.normal(0.0, 0.005, size=n_rows))
        vol[t] = rng.uniform(1e5, 1e6, size=n_rows)
    return {
        "open": pd.DataFrame(open_, index=idx),
        "high": pd.DataFrame(high, index=idx),
        "low": pd.DataFrame(low, index=idx),
        "close": pd.DataFrame(close, index=idx),
        "volume": pd.DataFrame(vol, index=idx),
    }


def _aux(seed: int = 20260717) -> dict:
    return {"vix": None, "sector_map": {t: "Tech" for t in _TICKERS}, "seed": seed}


def _corrupt_after(pn: dict[str, pd.DataFrame], cut_pos: int) -> dict[str, pd.DataFrame]:
    """Mangle every bar STRICTLY AFTER `cut_pos` (prices*7+5, volume*3+1) — mirrors the
    mechanical future-corruption harness. Positivity is preserved so math never NaNs out."""
    out: dict[str, pd.DataFrame] = {}
    for field, df in pn.items():
        d = df.copy()
        block = d.iloc[cut_pos + 1 :]
        if field == "volume":
            d.iloc[cut_pos + 1 :] = block * 3.0 + 1.0
        else:
            d.iloc[cut_pos + 1 :] = block * 7.0 + 5.0
        out[field] = d
    return out


# --------------------------------------------------------------------------- (d) labels ---------
def test_output_index_and_columns_match_close():
    pn = _make_panels()
    raw = build_raw_weights(pn, _aux())
    assert isinstance(raw, pd.DataFrame)
    assert list(raw.index) == list(pn["close"].index)
    assert list(raw.columns) == list(pn["close"].columns)


# --------------------------------------------------------------------------- (b) determinism ----
def test_determinism_two_calls_identical():
    pn = _make_panels()
    raw1 = build_raw_weights(pn, _aux())
    raw2 = build_raw_weights(pn, _aux())
    assert raw1.equals(raw2)


def test_seed_value_does_not_change_output():
    # aux['seed'] is unused: two different seeds must give bit-identical books.
    pn = _make_panels()
    a = build_raw_weights(pn, _aux(seed=1))
    b = build_raw_weights(pn, _aux(seed=999_999))
    assert a.equals(b)


# --------------------------------------------------------------------------- (a) future corrupt -
def test_future_corruption_leaves_past_weights_bit_identical():
    pn = _make_panels()
    raw_full = build_raw_weights(pn, _aux())
    for cut_pos in (200, 350, _N_ROWS - 2):
        pn_c = _corrupt_after(pn, cut_pos)
        raw_c = build_raw_weights(pn_c, _aux())
        a = raw_full.iloc[: cut_pos + 1]
        b = raw_c.iloc[: cut_pos + 1]
        assert a.equals(b), f"future corruption changed weights at/before cut_pos={cut_pos}"


def test_truncated_replay_equivalence():
    # Re-run on data truncated at a cut; weights <= cut must be bit-identical (no full-sample
    # state, no panel-length-derived behavior).
    pn = _make_panels()
    raw_full = build_raw_weights(pn, _aux())
    for cut_pos in (260, 400):
        pn_t = {f: df.iloc[: cut_pos + 1].copy() for f, df in pn.items()}
        raw_t = build_raw_weights(pn_t, _aux())
        a = raw_full.iloc[: cut_pos + 1]
        assert raw_t.equals(a), f"truncated replay diverged at cut_pos={cut_pos}"


# --------------------------------------------------------------------------- (c) NaN close -------
def test_nan_close_forces_flat_no_ewm_bridge():
    pn = _make_panels()
    raw_ref = build_raw_weights(pn, _aux())
    t_pos, name = 360, _TICKERS[3]
    # Precondition: normally this cell is a live (non-NaN) position.
    assert not pd.isna(raw_ref.iloc[t_pos][name])

    pn_gap = {f: df.copy() for f, df in pn.items()}
    pn_gap["close"].iloc[t_pos, pn_gap["close"].columns.get_loc(name)] = np.nan
    raw_gap = build_raw_weights(pn_gap, _aux())
    # No bar at t -> flat at t for that name; EWM must not bridge a missing current bar.
    assert pd.isna(raw_gap.iloc[t_pos][name])


# --------------------------------------------------------------------------- (e) unused aux ------
def test_runs_with_vix_none_and_missing_optional_aux():
    pn = _make_panels()
    # aux['vix'] is None (as the evaluator passes when VIX is absent); strategy must not touch it.
    raw = build_raw_weights(pn, {"vix": None, "sector_map": {}, "seed": 7})
    assert raw.shape == pn["close"].shape
    # After warm-up the book carries live (finite) positions on most names.
    tail = raw.iloc[-1]
    assert tail.notna().sum() >= 5


# --------------------------------------------------------------------------- neutrality sanity ---
def test_centered_book_is_near_dollar_neutral_pre_engine():
    # The centered rank is exactly dollar-neutral; after the (linear) EWM the row net stays
    # tiny. This is a sanity check on the transform order, not an engine assertion.
    pn = _make_panels()
    raw = build_raw_weights(pn, _aux())
    row = raw.iloc[-1].dropna()
    assert abs(float(row.sum())) < 0.05 * float(row.abs().sum() + 1e-12)
