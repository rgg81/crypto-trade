"""team-08 leak-proofing + correctness checks (QE SPEC A8 mandated set).

Self-contained: builds synthetic panels with numpy/pandas (no evaluator import, no data
read), so the whole file passes the tournament static scan. Run:

    uv run pytest tournament/crypto/teams/team-08/test_strategy.py -q
"""

from __future__ import annotations

import numpy as np
import pandas as pd

import strategy

STEP_MS = 8 * 60 * 60 * 1000
N_ROWS = 220
N_SYMS = 12
SEED = 20260718


def _panels(n_rows=N_ROWS, n_syms=N_SYMS, seed=SEED):
    """Synthetic (pn, aux) with a rising, noisy OI ledger so the gate admits real breadth."""
    rng = np.random.default_rng(seed)
    idx = pd.to_datetime(np.arange(n_rows, dtype=np.int64) * STEP_MS, unit="ms")
    cols = [f"SYM{i:02d}USDT" for i in range(n_syms)]

    close = pd.DataFrame(
        100.0 * np.exp(np.cumsum(rng.normal(0.0, 0.02, size=(n_rows, n_syms)), axis=0)),
        index=idx,
        columns=cols,
    )
    # positive OI with a mild upward drift + noise -> mix of confirmed / unconfirmed names
    drift = np.linspace(0.0, 0.6, n_rows)[:, None]
    oi = pd.DataFrame(
        1.0e6 * np.exp(drift + np.cumsum(rng.normal(0.0, 0.03, size=(n_rows, n_syms)), axis=0)),
        index=idx,
        columns=cols,
    )
    elig = pd.DataFrame(True, index=idx, columns=cols)

    pn = {"close": close}
    aux = {"eligibility": elig, "oi": oi, "seed": seed}
    return pn, aux


def test_determinism():
    """Two calls on identical inputs emit bit-identical weights."""
    pn, aux = _panels()
    w1 = strategy.build_raw_weights(pn, aux)
    w2 = strategy.build_raw_weights(pn, aux)
    pd.testing.assert_frame_equal(w1, w2, check_exact=True)


def test_no_nans_and_nonzero_activity():
    """Sanity: output is NaN-free and actually trades (else the leak tests are vacuous)."""
    pn, aux = _panels()
    w = strategy.build_raw_weights(pn, aux)
    assert isinstance(w, pd.DataFrame)
    assert np.isfinite(w.to_numpy()).all()
    active = w.abs().sum(axis=1) > 0
    assert int(active.sum()) > 20  # many candles carry a book


def test_future_corruption():
    """Mangle klines AND OI AND eligibility strictly AFTER a cut; weights <= cut unchanged."""
    pn, aux = _panels()
    w_full = strategy.build_raw_weights(pn, aux)

    cut_pos = N_ROWS - 15
    cut_time = pn["close"].index[cut_pos]
    after = pn["close"].index > cut_time

    close_c = pn["close"].copy()
    close_c.loc[after] = close_c.loc[after] * 7.0 + 5.0          # prices mangled
    oi_c = aux["oi"].copy()
    oi_c.loc[after] = oi_c.loc[after] * 3.0 + 1.0                # OI mangled
    elig_c = aux["eligibility"].copy()
    elig_c.loc[after] = ~elig_c.loc[after]                       # eligibility inverted

    pn_c = {"close": close_c}
    aux_c = {"eligibility": elig_c, "oi": oi_c, "seed": SEED}
    w_c = strategy.build_raw_weights(pn_c, aux_c)

    le = w_full.index <= cut_time
    pd.testing.assert_frame_equal(w_full[le], w_c[le], check_exact=True)


def test_samebar_before_unchanged():
    """Perturb only candle t*'s close + OI; weights STRICTLY BEFORE t* are unchanged."""
    pn, aux = _panels()
    w_full = strategy.build_raw_weights(pn, aux)

    tpos = int(N_ROWS * 0.7)
    tstar = pn["close"].index[tpos]

    close_p = pn["close"].copy()
    close_p.loc[tstar] = close_p.loc[tstar] * 1.001
    oi_p = aux["oi"].copy()
    oi_p.loc[tstar] = oi_p.loc[tstar] * 1.001

    pn_p = {"close": close_p}
    aux_p = {"eligibility": aux["eligibility"], "oi": oi_p, "seed": SEED}
    w_p = strategy.build_raw_weights(pn_p, aux_p)

    lt = w_full.index < tstar
    pd.testing.assert_frame_equal(w_full[lt], w_p[lt], check_exact=True)


def test_widening():
    """Extra synthetic never-eligible column: no crash, original columns' weights unchanged."""
    pn, aux = _panels()
    w_base = strategy.build_raw_weights(pn, aux)

    idx = pn["close"].index
    extra = pd.Series(50.0 * np.exp(np.cumsum(np.full(len(idx), 0.001))), index=idx)
    close_w = pn["close"].copy()
    close_w["ZZWIDE00USDT"] = extra                              # OI / elig lack this name

    pn_w = {"close": close_w}
    w_w = strategy.build_raw_weights(pn_w, aux)

    assert isinstance(w_w, pd.DataFrame)
    assert "ZZWIDE00USDT" in w_w.columns
    assert float(w_w["ZZWIDE00USDT"].abs().sum()) == 0.0        # unseen name stays flat
    pd.testing.assert_frame_equal(w_base, w_w[w_base.columns], check_exact=True)


def test_all_nan_oi():
    """All-NaN OI: no exception, every weight zero (no ledger -> no confirmation -> flat)."""
    pn, aux = _panels()
    aux_nan = {
        "eligibility": aux["eligibility"],
        "oi": aux["oi"] * np.nan,
        "seed": SEED,
    }
    w = strategy.build_raw_weights(pn, aux_nan)
    assert isinstance(w, pd.DataFrame)
    assert np.isfinite(w.to_numpy()).all()
    assert float(w.abs().to_numpy().sum()) == 0.0


def test_nonpositive_oi_flat():
    """Non-positive OI is treated as missing -> those names never enter the book."""
    pn, aux = _panels()
    oi_bad = aux["oi"].copy()
    oi_bad.iloc[:, 0] = -1.0                                     # one name has invalid OI
    aux_bad = {"eligibility": aux["eligibility"], "oi": oi_bad, "seed": SEED}
    w = strategy.build_raw_weights(pn, aux_bad)
    assert float(w.iloc[:, 0].abs().sum()) == 0.0
