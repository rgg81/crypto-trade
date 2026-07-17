"""team-01 strategy tests — leak-proofing self-checks on a synthetic panel.

These run under the audit static scan too, so imports are limited to numpy / pandas / the
team-local `strategy` module (no sys/os/pathlib). The synthetic panel is deterministic
(seeded RNG) and large enough (450 bars, 12 names, 3 sectors) to clear the strategy's
~294-bar eligibility burn-in, so the corruption/truncation cuts land on ACTIVE weights.

Covered:
  * future-corruption : mangle every bar strictly AFTER a cut -> weights <= cut unchanged
  * truncated-replay  : drop every bar after a cut -> weights <= cut bit-identical
  * determinism       : two fresh calls on identical inputs -> bit-identical
  * same-bar          : perturb close[t*] only -> weights STRICTLY BEFORE t* unchanged
  * close-only        : mangling open/high/low/volume never changes weights
  * dollar-neutral    : each active row is net-zero (longs$ == shorts$)
"""

from __future__ import annotations

import numpy as np
import pandas as pd

import strategy as st

N_BARS = 450
TICKERS = [f"S{i:02d}" for i in range(12)]
SECTORS = {t: ["Alpha", "Beta", "Gamma"][i % 3] for i, t in enumerate(TICKERS)}


def _synth_panel(seed: int = 7) -> tuple[dict, dict]:
    """Deterministic positive OHLCV random walk (dates x tickers) + aux."""
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2015-01-01", periods=N_BARS)
    steps = rng.normal(0.0005, 0.02, size=(N_BARS, len(TICKERS)))
    close = pd.DataFrame(100.0 * np.exp(np.cumsum(steps, axis=0)), index=idx, columns=TICKERS)
    openp = close.shift(1).fillna(close.iloc[0])
    high = np.maximum(openp, close) * 1.005
    low = np.minimum(openp, close) * 0.995
    vol = pd.DataFrame(
        rng.uniform(1e4, 1e6, size=(N_BARS, len(TICKERS))), index=idx, columns=TICKERS
    )
    pn = {"open": openp, "high": high, "low": low, "close": close, "volume": vol}
    aux = {"vix": pd.Series(20.0, index=idx), "sector_map": dict(SECTORS), "seed": 20260717}
    return pn, aux


def _corrupt_after(pn: dict, cut_i: int) -> dict:
    """Mangle every bar strictly after index `cut_i` (prices x7+5, volume x3+1)."""
    out = {}
    for k, df in pn.items():
        d = df.copy()
        mask = np.arange(len(d)) > cut_i
        if k == "volume":
            d.iloc[mask] = d.iloc[mask] * 3.0 + 1.0
        else:
            d.iloc[mask] = d.iloc[mask] * 7.0 + 5.0
        out[k] = d
    return out


def test_determinism():
    pn, aux = _synth_panel()
    w1 = st.build_raw_weights(pn, aux)
    w2 = st.build_raw_weights(pn, aux)
    pd.testing.assert_frame_equal(w1, w2, check_exact=True)


def test_future_corruption_leaves_past_weights_unchanged():
    pn, aux = _synth_panel()
    w_full = st.build_raw_weights(pn, aux)
    cut_i = 400  # past the ~294-bar eligibility burn-in -> active weights at the cut
    w_corrupt = st.build_raw_weights(_corrupt_after(pn, cut_i), aux)
    # weights AT and BEFORE the cut must be bit-identical despite mangled future bars
    pd.testing.assert_frame_equal(
        w_full.iloc[: cut_i + 1], w_corrupt.iloc[: cut_i + 1], check_exact=True
    )
    # sanity: the cut actually lands on a non-trivial (active) book
    assert w_full.iloc[cut_i].abs().sum() > 0.0


def test_truncated_replay_matches_full():
    pn, aux = _synth_panel()
    w_full = st.build_raw_weights(pn, aux)
    cut_i = 380
    pn_trunc = {k: df.iloc[: cut_i + 1].copy() for k, df in pn.items()}
    aux_trunc = dict(aux, vix=aux["vix"].iloc[: cut_i + 1])
    w_trunc = st.build_raw_weights(pn_trunc, aux_trunc)
    pd.testing.assert_frame_equal(
        w_full.iloc[: cut_i + 1], w_trunc.iloc[: cut_i + 1], check_exact=True
    )


def test_same_bar_perturbation_leaves_strictly_prior_unchanged():
    pn, aux = _synth_panel()
    w_full = st.build_raw_weights(pn, aux)
    t_star = 300
    pn_p = {k: df.copy() for k, df in pn.items()}
    pn_p["close"].iloc[t_star] = pn_p["close"].iloc[t_star] * 1.001
    w_p = st.build_raw_weights(pn_p, aux)
    # rows STRICTLY BEFORE t* must be unchanged (close[t*] is available to the t* decision)
    pd.testing.assert_frame_equal(w_full.iloc[:t_star], w_p.iloc[:t_star], check_exact=True)


def test_only_close_is_used():
    pn, aux = _synth_panel()
    w_full = st.build_raw_weights(pn, aux)
    pn_mangled = {k: df.copy() for k, df in pn.items()}
    for k in ("open", "high", "low", "volume"):
        pn_mangled[k] = pn_mangled[k] * 9.0 + 3.0
    w_mangled = st.build_raw_weights(pn_mangled, aux)
    pd.testing.assert_frame_equal(w_full, w_mangled, check_exact=True)


def test_active_rows_are_dollar_neutral():
    pn, aux = _synth_panel()
    w = st.build_raw_weights(pn, aux)
    active = w.abs().sum(axis=1) > 1e-12
    net = w[active].sum(axis=1).abs()
    assert float(net.max()) < 1e-9
