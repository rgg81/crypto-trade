"""team-06 strategy tests — leak-proofing self-checks on synthetic panels.

Imports are restricted to the static-scan whitelist (numpy, pandas) plus the local
``strategy`` module, so this file passes ``harness.scan_sources`` unchanged. Tests are
plain ``test_*`` functions using bare ``assert`` (no ``pytest`` import). Everything runs on
synthetic in-memory panels; no snapshot, no evaluator, no file reads.

Coverage:
  * determinism            — two fresh calls on identical inputs are bit-identical.
  * future-corruption      — mangling every bar strictly AFTER a cut leaves weights <= cut
                             bit-identical (the harness's own check-4 property).
  * truncated-replay       — running on data truncated at a cut leaves weights <= cut
                             bit-identical (the harness's own check-3 property).
  * same-bar               — perturbing close[t*] only leaves weights STRICTLY BEFORE t*
                             unchanged (close[t*] is legitimately available at t*).
  * regime state machine   — the hysteresis state is start-anchored and truncation-safe, and
                             both regime books are actually exercised on the fixture.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

import strategy as strat


# ------------------------------------------------------------------ fixtures --------------------
def _synthetic(n_rows: int = 900, n_names: int = 16, seed: int = 424242):
    """Positive-price random-walk panel + a spiky VIX series that trips both regimes."""
    idx = pd.bdate_range("2013-01-01", periods=n_rows)
    rng = np.random.default_rng(seed)
    names = [f"SYN{i:02d}USDT" for i in range(n_names)]

    rets = rng.normal(0.0003, 0.02, size=(n_rows, n_names))
    prices = 100.0 * np.exp(np.cumsum(rets, axis=0))
    close = pd.DataFrame(prices, index=idx, columns=names)

    # VIX: a calm baseline with a couple of engineered stress spikes so the trailing
    # percentile crosses both the HI (0.85) and LO (0.70) hysteresis thresholds.
    base = 15.0 + 3.0 * np.abs(rng.normal(0.0, 1.0, size=n_rows))
    for lo, hi in ((300, 340), (600, 650)):
        base[lo:hi] += np.linspace(0.0, 45.0, hi - lo)
    vix = pd.Series(base, index=idx)

    pn = {"close": close}
    aux = {"vix": vix, "sector_map": {c: "Tech" for c in names}, "seed": strat.MIN_PCT_OBS}
    return pn, aux, idx


def _corrupt_after(pn: dict, aux: dict, cut: pd.Timestamp):
    """Mangle every bar STRICTLY AFTER the cut (positive-preserving, mirrors the harness)."""
    close = pn["close"].copy()
    vix = aux["vix"].copy()
    cmask = close.index > cut
    close.loc[cmask] = close.loc[cmask] * 7.0 + 5.0
    vmask = vix.index > cut
    vix.loc[vmask] = vix.loc[vmask] * 2.0 + 3.0
    new_pn = {"close": close}
    new_aux = {**aux, "vix": vix}
    return new_pn, new_aux


def _truncate(pn: dict, aux: dict, cut: pd.Timestamp):
    close = pn["close"][pn["close"].index <= cut].copy()
    vix = aux["vix"][aux["vix"].index <= cut].copy()
    return {"close": close}, {**aux, "vix": vix}


def _le(df: pd.DataFrame, cut: pd.Timestamp) -> pd.DataFrame:
    return df[df.index <= cut]


def _lt(df: pd.DataFrame, cut: pd.Timestamp) -> pd.DataFrame:
    return df[df.index < cut]


# ------------------------------------------------------------------ tests -----------------------
def test_determinism():
    pn, aux, _ = _synthetic()
    a = strat.build_raw_weights(pn, aux)
    b = strat.build_raw_weights(pn, aux)
    pd.testing.assert_frame_equal(a, b, check_exact=True)


def test_output_shape_and_finiteness():
    pn, aux, idx = _synthetic()
    w = strat.build_raw_weights(pn, aux)
    assert list(w.index) == list(idx)
    assert list(w.columns) == list(pn["close"].columns)
    # Step-5 gross-normalise + fillna(0.0) => no NaN/inf cells anywhere.
    assert np.isfinite(w.to_numpy()).all()


def test_books_are_exercised():
    """The fixture must produce non-trivial, two-sided weights (else the leak tests are vacuous)."""
    pn, aux, _ = _synthetic()
    w = strat.build_raw_weights(pn, aux)
    active = w.abs().sum(axis=1) > 0
    assert active.sum() > 200
    # Both a long and a short leg appear on the active book (cross-sectional demeaning).
    act = w[active]
    assert (act > 1e-12).any(axis=1).mean() > 0.9
    assert (act < -1e-12).any(axis=1).mean() > 0.9


def test_regime_state_both_regimes_and_truncation_safe():
    """The VIX state machine visits both regimes and is start-anchored / truncation-safe."""
    pn, aux, idx = _synthetic()
    close = pn["close"]
    s_full = strat._vix_state(aux["vix"], close.index)
    assert (s_full == 0.0).any() and (s_full == 1.0).any()  # both regimes reached

    cut = idx[700]
    _, aux_t = _truncate(pn, aux, cut)
    s_trunc = strat._vix_state(aux_t["vix"], close.index[close.index <= cut])
    pd.testing.assert_series_equal(s_trunc, s_full[s_full.index <= cut], check_exact=True)


def test_future_corruption_before_cut_unchanged():
    """Check-4 property: mangling bars strictly after the cut cannot move weights <= cut."""
    pn, aux, idx = _synthetic()
    w_full = strat.build_raw_weights(pn, aux)
    for cut in (idx[400], idx[620], idx[800]):
        pn_c, aux_c = _corrupt_after(pn, aux, cut)
        w_c = strat.build_raw_weights(pn_c, aux_c)
        pd.testing.assert_frame_equal(_le(w_c, cut), _le(w_full, cut), check_exact=True)
        # The corruption must actually change SOMETHING after the cut (guards a vacuous pass).
        assert not _le(w_c, idx[-1]).equals(_le(w_full, idx[-1]))


def test_truncated_replay_before_cut_unchanged():
    """Check-3 property: truncating the panel at the cut cannot move weights <= cut."""
    pn, aux, idx = _synthetic()
    w_full = strat.build_raw_weights(pn, aux)
    for cut in (idx[500], idx[700], idx[-2]):
        pn_t, aux_t = _truncate(pn, aux, cut)
        w_t = strat.build_raw_weights(pn_t, aux_t)
        pd.testing.assert_frame_equal(_le(w_t, cut), _le(w_full, cut), check_exact=True)


def test_same_bar_perturbation_before_tstar_unchanged():
    """Check-5 property: perturbing close[t*] only leaves weights STRICTLY BEFORE t* unchanged."""
    pn, aux, idx = _synthetic()
    w_full = strat.build_raw_weights(pn, aux)
    t_star = idx[int(len(idx) * 0.7)]
    close = pn["close"].copy()
    close.loc[t_star] = close.loc[t_star] * 1.001
    w_p = strat.build_raw_weights({"close": close}, aux)
    pd.testing.assert_frame_equal(_lt(w_p, t_star), _lt(w_full, t_star), check_exact=True)


def _main() -> None:
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"ok  {name}")


if __name__ == "__main__":
    _main()
