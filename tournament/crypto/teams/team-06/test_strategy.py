"""team-06 strategy tests - leak-proofing self-checks for build_raw_weights.

Covers the research_brief.md QE SPEC 10 mandate:
  * future-corruption: mangling klines AND the aux ratio panels strictly AFTER a cut leaves
    the weights at or before the cut bit-identical (the pipeline is strictly trailing / past-only);
  * determinism: identical inputs -> bit-identical weights (no unseeded randomness / clock);
plus structural checks (centered-rank range, eligibility masking, widening safety).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

import strategy

STEP_MS = 8 * 60 * 60 * 1000
GRID_ORIGIN_MS = 1_577_836_800_000  # 2020-01-01 00:00 UTC, 8h grid origin
PANELS = (
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


def _make_inputs(n_rows=260, n_syms=8, n_extra_inelig=0, seed=0):
    """Synthetic 8h panels. ls_accounts is a positive per-coin random walk around ~100
    (mimicking the 8h ratio-of-sums magnitude); klines are irrelevant to the strategy but
    are present so the future-corruption check can mangle them too."""
    rng = np.random.default_rng(seed)
    idx = pd.to_datetime(
        np.arange(n_rows, dtype=np.int64) * STEP_MS + GRID_ORIGIN_MS, unit="ms"
    )
    syms = [f"C{i:02d}USDT" for i in range(n_syms)]
    inelig_syms = [f"Z{i:02d}USDT" for i in range(n_extra_inelig)]
    all_syms = syms + inelig_syms

    pn = {
        name: pd.DataFrame(
            rng.uniform(1.0, 100.0, size=(n_rows, len(all_syms))), index=idx, columns=all_syms
        )
        for name in PANELS
    }

    base = rng.uniform(80.0, 120.0, size=n_syms)
    walk = np.cumsum(rng.normal(0.0, 2.0, size=(n_rows, n_syms)), axis=0)
    ls_core = np.abs(base + walk) + 1.0
    ls = pd.DataFrame(ls_core, index=idx, columns=syms)
    for s in inelig_syms:  # extra columns carry NO ratio history (all NaN)
        ls[s] = np.nan
    ls = ls[all_syms]

    elig = pd.DataFrame(True, index=idx, columns=syms)
    for s in inelig_syms:
        elig[s] = False
    elig = elig[all_syms]

    aux = {"ls_accounts": ls, "eligibility": elig, "seed": 12345}
    return pn, aux, idx


def test_determinism():
    pn, aux, _ = _make_inputs()
    w1 = strategy.build_raw_weights(pn, aux)
    w2 = strategy.build_raw_weights(pn, aux)
    pd.testing.assert_frame_equal(w1, w2, check_exact=True)


def test_future_corruption_past_only():
    pn, aux, idx = _make_inputs()
    w_full = strategy.build_raw_weights(pn, aux)

    cut = idx[180]
    after = idx > cut

    # mangle klines strictly AFTER the cut (prices *7+5, everything else *3+1)
    pn2 = {k: v.copy() for k, v in pn.items()}
    for k in pn2:
        pn2[k].loc[after] = pn2[k].loc[after] * 7.0 + 5.0

    # mangle the ratio aux panel and INVERT eligibility strictly AFTER the cut
    aux2 = dict(aux)
    ls2 = aux["ls_accounts"].copy()
    ls2.loc[after] = ls2.loc[after] * 3.0 + 1.0
    elig2 = aux["eligibility"].copy()
    elig2.loc[after] = ~elig2.loc[after]
    aux2["ls_accounts"] = ls2
    aux2["eligibility"] = elig2

    w_corr = strategy.build_raw_weights(pn2, aux2)

    pd.testing.assert_frame_equal(
        w_full[w_full.index <= cut], w_corr[w_corr.index <= cut], check_exact=True
    )


def test_centered_rank_range_and_eligibility():
    pn, aux, _ = _make_inputs(n_extra_inelig=3)
    w = strategy.build_raw_weights(pn, aux)

    # never-eligible columns must be flat (NaN) everywhere
    assert w[["Z00USDT", "Z01USDT", "Z02USDT"]].isna().all().all()

    vals = w.to_numpy()
    finite = vals[np.isfinite(vals)]
    assert finite.size > 0
    assert np.nanmax(np.abs(finite)) < 0.5 + 1e-9  # centered rank strictly inside [-0.5, 0.5]

    # rows with an active cross-section sum to ~0 (centered rank is dollar-balanced)
    row_sums = w.sum(axis=1, skipna=True)
    active = w.notna().sum(axis=1) > 1
    assert np.allclose(row_sums[active].to_numpy(), 0.0, atol=1e-9)


def test_widening_safe():
    pn, aux, _ = _make_inputs(n_extra_inelig=5)
    w = strategy.build_raw_weights(pn, aux)
    assert isinstance(w, pd.DataFrame)
    assert list(w.columns) == list(aux["ls_accounts"].columns)


def test_pre_warmup_flat():
    pn, aux, idx = _make_inputs()
    w = strategy.build_raw_weights(pn, aux)
    # before min_periods (45 obs, first valid z at position 44) rolling z is undefined
    # -> whole book flat. Check strictly inside the warmup band (positions 0..39).
    early = w[w.index < idx[40]]
    assert early.isna().all().all()
