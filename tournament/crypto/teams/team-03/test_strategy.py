"""team-03 leak-proofing + contract tests for strategy.build_raw_weights.

Runnable with `uv run pytest tournament/crypto/teams/team-03/test_strategy.py -q`.

NOTE: this file is STATICALLY SCANNED by the tournament harness (every *.py under the team
dir must pass the import whitelist). So it imports ONLY numpy/pandas/math + the local
`strategy` module — no pytest, no sys/pathlib, no file reads. Tests are plain assert
functions; pytest collects them by the `test_` prefix without needing `import pytest`.

Assertions (QE SPEC §10): (a) future corruption of klines AND aux rows > t leaves weights at
rows <= t bit-identical; (b) determinism across two calls; (c) widening with junk synthetic
columns neither crashes nor changes the original columns' weights; (d) an all-NaN close panel
yields all-zero weights; (e) output index/columns equal pn["close"]'s. Plus a truncated-replay
check (rows <= cut unchanged when the panel is cut at the tail).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

import strategy

STEP_MS = 8 * 60 * 60 * 1000
TEAM_PANELS = (
    "open",
    "high",
    "low",
    "close",
    "volume",
    "quote_volume",
    "trades",
    "taker_buy_volume",
    "taker_buy_quote_volume",
)


def _make_inputs(seed: int = 7, n_rows: int = 500, n_syms: int = 12):
    """Build a synthetic (pn, aux) pair with positive prices and a full eligibility mask.

    Deterministic (seeded numpy RNG) — this is TEST-INPUT construction, not strategy
    randomness. Enough rows to clear the beta/formation warmup so post-warmup weights are
    non-trivial (the leak-proofing tests are only meaningful on non-zero rows).
    """
    rng = np.random.default_rng(seed)
    idx = pd.to_datetime(
        np.arange(n_rows, dtype=np.int64) * STEP_MS
        + pd.Timestamp("2020-01-01").value // 1_000_000 * 1_000_000,
        unit="ms",
    )
    syms = [f"C{i:02d}USDT" for i in range(n_syms)]

    rets = rng.normal(0.0, 0.02, size=(n_rows, n_syms))
    close = 100.0 * np.exp(np.cumsum(rets, axis=0))
    close_df = pd.DataFrame(close, index=idx, columns=syms)

    pn = {}
    pn["close"] = close_df
    pn["open"] = close_df.shift(1).fillna(close_df.iloc[0])
    pn["high"] = close_df * 1.01
    pn["low"] = close_df * 0.99
    vol = pd.DataFrame(rng.uniform(1e3, 1e5, size=(n_rows, n_syms)), index=idx, columns=syms)
    pn["volume"] = vol
    pn["quote_volume"] = vol * close_df
    pn["trades"] = pd.DataFrame(
        rng.uniform(50, 500, size=(n_rows, n_syms)), index=idx, columns=syms
    )
    pn["taker_buy_volume"] = vol * 0.5
    pn["taker_buy_quote_volume"] = vol * close_df * 0.5

    # Every listed symbol eligible on every candle -> breadth well above the factor floor.
    elig = pd.DataFrame(True, index=idx, columns=syms)
    funding = pd.DataFrame(
        rng.normal(0.0, 1e-4, size=(n_rows, n_syms)), index=idx, columns=syms
    )
    oi = pd.DataFrame(rng.uniform(1e6, 1e7, size=(n_rows, n_syms)), index=idx, columns=syms)
    aux = {"eligibility": elig, "funding": funding, "oi": oi, "seed": 12345}
    return pn, aux


def _frames_bit_equal(a: pd.DataFrame, b: pd.DataFrame) -> bool:
    """Bit-exact frame equality (NaNs in matching positions count as equal)."""
    return a.shape == b.shape and list(a.columns) == list(b.columns) and a.equals(b)


# ------------------------------------------------------------------ (e) contract ----------------
def test_output_index_and_columns_match_close():
    pn, aux = _make_inputs()
    w = strategy.build_raw_weights(pn, aux)
    assert isinstance(w, pd.DataFrame)
    assert w.index.equals(pn["close"].index)
    assert list(w.columns) == list(pn["close"].columns)


# ------------------------------------------------------------------ (b) determinism -------------
def test_determinism_two_calls_bit_identical():
    pn, aux = _make_inputs()
    w1 = strategy.build_raw_weights(pn, aux)
    w2 = strategy.build_raw_weights(pn, aux)
    assert _frames_bit_equal(w1, w2)


# ------------------------------------------------------------------ zero-sum / caps sanity ------
def test_rows_are_dollar_neutral_before_smoothing_tail():
    """Centered rank => each fully-populated row of the pre-smoothing book sums to ~0. After
    the EMA the row sum is a decaying blend but must still be numerically tiny (no directional
    tilt injected by the strategy)."""
    pn, aux = _make_inputs()
    w = strategy.build_raw_weights(pn, aux)
    active = w.abs().sum(axis=1) > 0
    assert active.any()
    assert w[active].sum(axis=1).abs().max() < 1e-9


# ------------------------------------------------------------------ (b/leak) truncated replay ---
def test_truncated_replay_rows_before_cut_unchanged():
    pn, aux = _make_inputs()
    w_full = strategy.build_raw_weights(pn, aux)
    cut_pos = 360
    pn_t = {k: v.iloc[: cut_pos + 1].copy() for k, v in pn.items()}
    aux_t = {
        "eligibility": aux["eligibility"].iloc[: cut_pos + 1].copy(),
        "funding": aux["funding"].iloc[: cut_pos + 1].copy(),
        "oi": aux["oi"].iloc[: cut_pos + 1].copy(),
        "seed": aux["seed"],
    }
    w_t = strategy.build_raw_weights(pn_t, aux_t)
    a = w_full.iloc[: cut_pos + 1]
    assert _frames_bit_equal(a, w_t)


# ------------------------------------------------------------------ (a) future corruption -------
def test_future_corruption_leaves_past_weights_bit_identical():
    """Mangle EVERY row strictly after the cut in BOTH a kline panel (close) and aux
    (eligibility inverted, funding mangled); weights at rows <= cut must be bit-unchanged."""
    pn, aux = _make_inputs()
    w_full = strategy.build_raw_weights(pn, aux)

    cut_pos = 360
    n = len(pn["close"].index)
    post = np.arange(cut_pos + 1, n)

    pn_c = {k: v.copy() for k, v in pn.items()}
    # klines: prices *7+5, volumes *3+1 on the post-cut rows.
    for f in ("open", "high", "low", "close"):
        pn_c[f].iloc[post] = pn_c[f].iloc[post] * 7.0 + 5.0
    for f in ("volume", "quote_volume", "trades", "taker_buy_volume", "taker_buy_quote_volume"):
        pn_c[f].iloc[post] = pn_c[f].iloc[post] * 3.0 + 1.0

    elig_c = aux["eligibility"].copy()
    elig_c.iloc[post] = ~elig_c.iloc[post].astype(bool)  # eligibility inverted after cut
    fund_c = aux["funding"].copy()
    fund_c.iloc[post] = fund_c.iloc[post] * 3.0 + 1e-4
    oi_c = aux["oi"].copy()
    oi_c.iloc[post] = oi_c.iloc[post] * 3.0 + 1.0
    aux_c = {"eligibility": elig_c, "funding": fund_c, "oi": oi_c, "seed": aux["seed"]}

    w_c = strategy.build_raw_weights(pn_c, aux_c)
    a = w_full.iloc[: cut_pos + 1]
    b = w_c.iloc[: cut_pos + 1]
    assert _frames_bit_equal(a, b)


# ------------------------------------------------------------------ (c) widening ----------------
def _widen(pn, aux, junk, junk_seed):
    """Append `junk` synthetic (never-eligible) columns filled with seeded random prices."""
    rng = np.random.default_rng(junk_seed)
    idx = pn["close"].index
    n = len(idx)
    pn_w = {}
    for k, v in pn.items():
        add = pd.DataFrame(
            rng.uniform(1.0, 100.0, size=(n, len(junk))), index=idx, columns=junk
        )
        pn_w[k] = pd.concat([v, add], axis=1)
    # Eligibility does NOT list the junk columns -> reindex fills them False (never eligible).
    aux_w = {k: v for k, v in aux.items()}
    return pn_w, aux_w


def test_widening_no_crash_and_original_weights_unchanged():
    """The sealed out-of-sample panel WILL carry coins the IS panel didn't. Appending
    never-eligible junk columns must not crash, must return a DataFrame, must leave the junk
    columns flat, and must NOT materially change the original columns' weights.

    Note: the original columns match to floating-point tolerance rather than bit-for-bit,
    because the dollar-neutral centering mean `rk.mean(axis=1)` is reduced across the now-wider
    row (junk masked to NaN); numpy's row reduction over 17 vs 12 slots differs by <=1 ULP.
    That is information-free summation-order noise, NOT a leak — the stronger invariant below
    proves junk CONTENT cannot influence the originals at all. The engine scores each window on
    its own fixed column set, never bit-comparing across widths, so this never affects scoring
    or reproduction.
    """
    pn, aux = _make_inputs()
    w_full = strategy.build_raw_weights(pn, aux)
    orig_cols = list(pn["close"].columns)
    junk = [f"ZZWIDE{i:02d}USDT" for i in range(5)]

    pn_w, aux_w = _widen(pn, aux, junk, junk_seed=99)
    w_w = strategy.build_raw_weights(pn_w, aux_w)
    assert isinstance(w_w, pd.DataFrame)
    assert list(w_w.columns) == list(pn_w["close"].columns)
    # Junk (never-eligible) columns must be EXACTLY flat.
    assert float(w_w[junk].abs().to_numpy().max()) == 0.0
    # Original columns unchanged up to summation-order ULP noise (no material change).
    delta = float((w_full[orig_cols] - w_w[orig_cols]).abs().to_numpy().max())
    assert delta < 1e-12


def test_widening_junk_content_cannot_leak_into_originals():
    """Strong anti-leak invariant: two widenings that differ ONLY in the junk columns' VALUES
    produce BIT-IDENTICAL original-column weights. Proves synthetic-column data can never flow
    into the tradable book (the narrow->wide ULP offset is a constant, junk-independent)."""
    pn, aux = _make_inputs()
    orig_cols = list(pn["close"].columns)
    junk = [f"ZZWIDE{i:02d}USDT" for i in range(5)]

    pn_a, aux_a = _widen(pn, aux, junk, junk_seed=111)
    pn_b, aux_b = _widen(pn, aux, junk, junk_seed=222)
    w_a = strategy.build_raw_weights(pn_a, aux_a)
    w_b = strategy.build_raw_weights(pn_b, aux_b)
    assert _frames_bit_equal(w_a[orig_cols], w_b[orig_cols])


# ------------------------------------------------------------------ (d) all-NaN close -----------
def test_all_nan_close_yields_all_zero_weights():
    pn, aux = _make_inputs()
    pn_n = {k: v.copy() for k, v in pn.items()}
    pn_n["close"] = pd.DataFrame(
        np.nan, index=pn["close"].index, columns=pn["close"].columns
    )
    w = strategy.build_raw_weights(pn_n, aux)
    assert isinstance(w, pd.DataFrame)
    assert w.index.equals(pn["close"].index)
    assert list(w.columns) == list(pn["close"].columns)
    assert float(np.nanmax(np.abs(w.to_numpy()))) == 0.0
    assert not np.isnan(w.to_numpy()).any()


# ------------------------------------------------------------------ NaN-tolerant close ----------
def test_partial_nan_close_column_does_not_crash():
    """A dead/delisted name (NaN closes on a tail block) must not crash and must stay flat
    where it is NaN-scored; other names keep trading."""
    pn, aux = _make_inputs()
    pn_n = {k: v.copy() for k, v in pn.items()}
    dead = pn_n["close"].columns[0]
    pn_n["close"].iloc[300:, pn_n["close"].columns.get_loc(dead)] = np.nan
    w = strategy.build_raw_weights(pn_n, aux)
    assert isinstance(w, pd.DataFrame)
    assert not np.isnan(w.to_numpy()).any()  # fillna(0.0) => no NaN escapes


def _run_all():
    fns = [
        test_output_index_and_columns_match_close,
        test_determinism_two_calls_bit_identical,
        test_rows_are_dollar_neutral_before_smoothing_tail,
        test_truncated_replay_rows_before_cut_unchanged,
        test_future_corruption_leaves_past_weights_bit_identical,
        test_widening_no_crash_and_original_weights_unchanged,
        test_widening_junk_content_cannot_leak_into_originals,
        test_all_nan_close_yields_all_zero_weights,
        test_partial_nan_close_column_does_not_crash,
    ]
    for fn in fns:
        fn()
        print(f"PASS {fn.__name__}")


if __name__ == "__main__":
    _run_all()
