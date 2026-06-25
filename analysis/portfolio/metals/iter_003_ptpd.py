"""metals-portfolio EXPLORATION-003 — platinum-vs-palladium REVERSION SLEEVE (3rd sleeve).

The book is now THREE orthogonal sleeves:
  1. iter-001 ANCHOR     — long-biased gold-led trend.
  2. iter-002 OVERLAY    — dollar-neutral gold-defensive dispersion (the 0.5· dispersion arm).
  3. THIS sleeve         — dollar-neutral platinum-vs-palladium ratio REVERSION.

Mechanism / why it is orthogonal: platinum and palladium have DIVERGING fundamentals — palladium
is bled by EV substitution (autocatalyst demand collapsing), platinum is lifted by hydrogen / diesel
demand — yet the iter-002 dispersion lumps BOTH into the single short "industrials" basket. Their
log price-ratio `log(XPT/XPD)` MEAN-REVERTS (variance ratio < 1; unlike the gold/silver ratio that
TRENDED). So we FADE the ratio: when platinum is rich vs palladium (z > 0) we short platinum / long
palladium, and vice-versa — a dollar-neutral relative-value pair that earns on convergence.

THIN-N CAVEAT (pre-registered, reported honestly — NOT hidden): platinum & palladium Dukascopy
depth starts 2022-01-03, so this sleeve carries weight only from 2022+ → ~33 effective months of IS
history (2022-01 .. 2025-03 cutoff). Every standalone / contribution metric for this sleeve is a
THIN-N estimate. The headline reporting therefore ALWAYS splits a 2022+ IS sub-window alongside the
full-IS number, and the verdict classification is gated on a `PROMISING-THIN-N` outcome to avoid
over-claiming.

Combination is PARITY-CORRECT (identical to iter-002): each arm's RAW book is gross-normalised, then
summed at the raw-weight level with a mixing weight, then a SINGLE `net_from_raw` does the lag /
cost / vol-target. No post-trade netting, no double-counting of cost.

IN-SAMPLE-ONLY reporting. OOS (>= OOS_CUTOFF) is HIDDEN and never printed; no `reveal_oos`.
"""

from __future__ import annotations

import iter_001_trend as it  # noqa: E402  (anchor; build_raw is the parity-correct raw book)
import iter_002_mn_overlay as ov  # noqa: E402  (gross_norm + mn_dispersion_raw — the 0.5· arm)
import numpy as np
import pandas as pd
from universe_metals import (
    LO0,
    OOS_CUTOFF,
    VOL_WIN,
    load_metals,
    maxdd,
    msharpe,
    net_from_raw,
    panels,
    turnover,
)

# ── Center config (the registered candidate) ─────────────────────────────────────────────
Z_WIN = 126  # 42d z-score window on the log(XPT/XPD) ratio (≈ the conservative center)
BETA = 0.25  # mixing weight of the pt-pd reversion sleeve on top of the iter-002 combined book
ALPHA_DISP = 0.5  # the iter-002 dispersion mixing weight — UNCHANGED from iter-002
PT = "XPTUSDT"
PD = "XPDUSDT"
PTPD = (PT, PD)
ERA_2022 = pd.Timestamp("2022-01-01")  # the 2022+ IS sub-window boundary (where pt/pd live)

# Machine-readable promotion guard (Critic Caveat). The pre-registered era-split FALSIFIER tripped
# (standalone sleeve Sharpe 2022-23 = -0.13 → 2024-cutoff = +0.72, sign-inverts): the edge lives in
# the recent, OOS-adjacent half of an already ~33-month window. Classification = PROMISING-THIN-N.
# Any baseline-builder MUST refuse to promote this sleeve while PROMOTABLE is False. Lift ONLY after
# pt/pd history reaches ~60+ months OR a CONFIRMATION clears the era-split falsifier + a variance-
# ratio bootstrap CI excluding 0.5 on the full pt/pd history.
PROMOTABLE = False

# ── Robustness sweep grid (reporting only — NOT for cell selection) ──────────────────────
SWEEP_ZWIN = (84, 126, 189)  # 28d / 42d / 63d z-score windows
SWEEP_BETA = (0.20, 0.35, 0.50)


def ptpd_raw(close: pd.DataFrame, z_win: int = Z_WIN) -> pd.DataFrame:
    """Dollar-neutral platinum-vs-palladium ratio reversion → SIGNED raw weight book.

    Mechanics (exactly the QR spec):
      lr      = log(XPT / XPD)                                  (causal — only same-bar closes)
      z       = (lr - mean_{z_win}(lr)) / std_{z_win}(lr), clipped to [-2.5, +2.5]
      sig_pt  = -sign(z)                                        (FADE: pt rich z>0 -> short pt)
      raw[PT] =  sig_pt / rvol[PT] ; raw[PD] = -sig_pt / rvol[PD]  (inverse-vol sized)
    then DEMEANED across the {PT, PD} pair so the deployed book is EXACTLY dollar-neutral
    (raw[PT] + raw[PD] = 0 every bar). The sleeve is NONZERO only in XPT / XPD; all other
    metals carry 0 weight (column-isolation).

    Leak-safe: the rolling mean/std and `rvol` use only past/present closes; the downstream
    `net_from_raw` lags the whole book by one candle, so a signal decided at close[t] is
    deployed at open[t+1]. Before the first valid z (first `z_win` bars of pt/pd history), z is
    NaN → sig is NaN → the sleeve is 0 (warmup-clean, no fabricated pre-history exposure).
    """
    rvol = close.pct_change().rolling(VOL_WIN).std()  # 28d realized vol for inverse-vol sizing
    elig = close.notna()  # PIT eligibility — pt/pd carry weight only once they have price history

    lr = np.log(close[PT] / close[PD])  # causal log price-ratio
    mu = lr.rolling(z_win).mean()
    sd = lr.rolling(z_win).std()
    z = ((lr - mu) / sd).clip(-2.5, 2.5)  # NaN during warmup / when either leg is missing
    sig_pt = -np.sign(z)  # FADE the ratio: pt rich (z>0) -> short pt / long pd

    raw = pd.DataFrame(0.0, index=close.index, columns=close.columns)
    raw[PT] = (sig_pt / rvol[PT]).where(elig[PT] & rvol[PT].notna(), 0.0)
    raw[PD] = (-sig_pt / rvol[PD]).where(elig[PD] & rvol[PD].notna(), 0.0)
    pair = raw[[PT, PD]]
    raw[[PT, PD]] = pair.sub(pair.mean(axis=1), axis=0)  # demean the pair → exact dollar-neutrality
    return raw.fillna(0.0)


def build_sleeve(
    coins: dict[str, pd.DataFrame], z_win: int = Z_WIN
) -> tuple[pd.Series, pd.DataFrame]:
    """Standalone pt-pd reversion sleeve → (vol-targeted net, book) via the leak-safe core."""
    pan = panels(coins)
    return net_from_raw(ptpd_raw(pan["close"], z_win), pan["ret_fwd"])


def build_combined3(
    coins: dict[str, pd.DataFrame],
    beta: float = BETA,
    z_win: int = Z_WIN,
    alpha_disp: float = ALPHA_DISP,
) -> tuple[pd.Series, pd.DataFrame]:
    """Parity-correct 3-sleeve book: gn(anchor) + alpha_disp*gn(disp) + beta*gn(ptpd) → ONE net.

    The `gn(anchor) + alpha_disp·gn(dispersion)` head is BIT-IDENTICAL to iter-002's combined book
    (alpha_disp defaults to iter-002's 0.5); the pt-pd sleeve is appended at the raw-weight level
    so the whole book passes through a SINGLE `net_from_raw` (lag / cost / vol-target) — no
    post-trade netting, parity-correct against a single-strategy run of the blended book.
    """
    pan = panels(coins)
    close, ret_fwd = pan["close"], pan["ret_fwd"]
    gn = ov.gross_norm
    raw_combined = (
        gn(it.build_raw(coins))
        + alpha_disp * gn(ov.mn_dispersion_raw(close))
        + beta * gn(ptpd_raw(close, z_win))
    )
    return net_from_raw(raw_combined, ret_fwd)


# ── reporting helpers (IS-only) ──────────────────────────────────────────────────────────
def _is_slice(net: pd.Series, *, since: pd.Timestamp | None = None) -> pd.Series:
    """IS-window slice (< OOS_CUTOFF), optionally restricted to t >= `since` (2022+ sub-window)."""
    s = net[net.index < OOS_CUTOFF]
    return s[s.index >= since] if since is not None else s


def _sharpe_dd(net: pd.Series, *, since: pd.Timestamp | None = None) -> tuple[float, float]:
    """(IS Sharpe, IS maxDD%) over the IS window, optionally restricted to the 2022+ sub-window."""
    s = _is_slice(net, since=since)
    sr = msharpe(s, LO0, OOS_CUTOFF)
    dd = maxdd(s) * 100 if len(s) else float("nan")
    return sr, dd


def _year_breakdown_is(net: pd.Series) -> dict[int, float]:
    """Per-year IS net% (sum of per-candle net within the IS window, in percent)."""
    s = _is_slice(net)
    return {int(y): round(v * 100, 1) for y, v in s.groupby(s.index.year).sum().items()}


def _monthly_2022(net: pd.Series) -> pd.Series:
    """Monthly-summed net over the 2022+ IS sub-window (for sleeve↔book correlation)."""
    s = _is_slice(net, since=ERA_2022)
    return s.groupby(s.index.to_period("M")).sum()


def main() -> None:
    coins = load_metals()
    print(f"EXPLORATION-003: platinum-vs-palladium REVERSION SLEEVE — {len(coins)} metals")
    print(f"  universe {tuple(coins)}  (IN-SAMPLE ONLY — OOS hidden until CONFIRMATION)")
    print("  THIN-N: pt/pd exist 2022+ only (~33 effective IS months) — reported honestly\n")

    # ── 1. REFERENCE: iter-002 combined (anchor + dispersion), unchanged head ─────────────
    net_ref, w_ref = ov.build_combined(coins)
    sr_ref_full, dd_ref_full = _sharpe_dd(net_ref)
    sr_ref_2022, dd_ref_2022 = _sharpe_dd(net_ref, since=ERA_2022)
    print("[1] REFERENCE  iter-002 combined (anchor + 0.5·dispersion)  — the bar to beat")
    print(
        f"  iter-002                 full-IS_Sharpe={sr_ref_full:+.3f}  2022+_Sharpe="
        f"{sr_ref_2022:+.3f}  maxDD_full={dd_ref_full:6.1f}%  maxDD_2022={dd_ref_2022:6.1f}%"
    )
    print("      (spec: full-IS +0.514 / 2022+ +0.745)\n")

    # ── 2. 3-SLEEVE CENTER (Z_WIN=126, BETA=0.25) ─────────────────────────────────────────
    net_c, w_c = build_combined3(coins, BETA, Z_WIN)
    sr_c_full, dd_c_full = _sharpe_dd(net_c)
    sr_c_2022, dd_c_2022 = _sharpe_dd(net_c, since=ERA_2022)
    tnov_c = turnover(w_c, LO0, OOS_CUTOFF)
    # sleeve correlation to the iter-002 reference book (2022+ monthly)
    book_m = _monthly_2022(net_c)
    ref_m = _monthly_2022(net_ref)
    common = book_m.index.intersection(ref_m.index)
    corr_to_ref = float(book_m.loc[common].corr(ref_m.loc[common]))
    print(f"[2] 3-SLEEVE CENTER  (Z_WIN={Z_WIN}, BETA={BETA}, dispersion α={ALPHA_DISP} unchanged)")
    print(
        f"  3-sleeve                 full-IS_Sharpe={sr_c_full:+.3f}  2022+_Sharpe="
        f"{sr_c_2022:+.3f}  maxDD_full={dd_c_full:6.1f}%  maxDD_2022={dd_c_2022:6.1f}%"
    )
    print(
        f"      turnover/candle={tnov_c:.4f}   3-sleeve↔iter-002 book corr (2022+ monthly)="
        f"{corr_to_ref:+.3f}"
    )
    print(f"      IS net%/yr = {_year_breakdown_is(net_c)}\n")

    # ── 3. STANDALONE pt-pd sleeve (2022+ only — it has no pre-2022 history) ──────────────
    net_s, w_s = build_sleeve(coins, Z_WIN)
    sr_s_2022, dd_s_2022 = _sharpe_dd(net_s, since=ERA_2022)
    tnov_s = turnover(w_s, ERA_2022, OOS_CUTOFF)
    # standalone sleeve correlation to the iter-002 book (2022+ monthly)
    sleeve_m = _monthly_2022(net_s)
    common_s = sleeve_m.index.intersection(ref_m.index)
    corr_sleeve = float(sleeve_m.loc[common_s].corr(ref_m.loc[common_s]))
    print("[3] STANDALONE pt-pd sleeve  (2022+ only — pt/pd have no pre-2022 history)")
    print(
        f"  ptpd-sleeve              2022+_Sharpe={sr_s_2022:+.3f}  maxDD_2022={dd_s_2022:6.1f}%  "
        f"turnover/candle={tnov_s:.4f}"
    )
    print(f"      standalone-sleeve↔iter-002 book corr (2022+ monthly)={corr_sleeve:+.3f}")
    print(f"      IS net%/yr = {_year_breakdown_is(net_s)}\n")

    # ── 4. ROBUSTNESS sweep (REPORT ALL CELLS — no best-cell selection) ──────────────────
    print(
        f"[4] ROBUSTNESS sweep  Z_WIN{list(SWEEP_ZWIN)} × BETA{list(SWEEP_BETA)}  "
        f"({len(SWEEP_ZWIN) * len(SWEEP_BETA)} cells)  — 3-sleeve full-IS / 2022+ Sharpe per cell"
    )
    print(f"      lifts-both bar: full-IS > {sr_ref_full:+.3f} AND 2022+ > {sr_ref_2022:+.3f}")
    lift_both = 0
    n_cells = 0
    for zw in SWEEP_ZWIN:
        cells = []
        for b in SWEEP_BETA:
            net_sw, _ = build_combined3(coins, b, zw)
            srf, _ = _sharpe_dd(net_sw)
            sr22, _ = _sharpe_dd(net_sw, since=ERA_2022)
            n_cells += 1
            both = srf > sr_ref_full and sr22 > sr_ref_2022
            lift_both += int(both)
            mark = "*" if both else " "
            cells.append(f"B{b:<4}full={srf:+.3f}/2022={sr22:+.3f}{mark}")
        print(f"  Z{zw:<4}  " + "  ".join(cells))
    print(f"  summary: {lift_both}/{n_cells} cells lift BOTH vs iter-002 (* = lifts both)\n")

    # ── 5. FALSIFIER — 2-fold era split of the standalone sleeve ──────────────────────────
    fold = pd.Timestamp("2024-01-01")  # split the thin 2022+ history in two halves
    s_22 = _is_slice(net_s, since=ERA_2022)
    sr_early = msharpe(s_22[s_22.index < fold], LO0, OOS_CUTOFF)  # 2022-2023
    sr_late = msharpe(s_22[s_22.index >= fold], LO0, OOS_CUTOFF)  # 2024 .. cutoff
    invert = (sr_early > 0) != (sr_late > 0)
    print("[5] FALSIFIER  2-fold era split of standalone sleeve  (lift must NOT invert)")
    print(f"  2022-2023      Sharpe={sr_early:+.3f}")
    print(f"  2024-cutoff    Sharpe={sr_late:+.3f}")
    print(f"  sign-inverts={invert}  (TRUE => FALSIFIER tripped => PROMISING-THIN-N)\n")

    # ── 6. INTEGRITY asserts (PASS/FAIL) ──────────────────────────────────────────────────
    print("[6] INTEGRITY asserts")
    raw_full = ptpd_raw(panels(coins)["close"], Z_WIN)
    # (a) dollar-neutrality of the pt-pd raw pair: max|XPT + XPD weight| < 1e-9
    dn = float(raw_full[[PT, PD]].sum(axis=1).abs().max())
    a_dn = dn < 1e-9
    print(f"  (a) dollar-neutral pt-pd raw   max|XPT+XPD| = {dn:.2e}  < 1e-9 : {_pf(a_dn)}")
    # (b) column-isolation: sleeve nonzero only in XPT / XPD
    others = [c for c in raw_full.columns if c not in PTPD]
    max_other = float(raw_full[others].abs().max().max()) if others else 0.0
    a_iso = max_other < 1e-12
    print(f"  (b) column-isolation       max|other-metal weight| = {max_other:.2e} : {_pf(a_iso)}")
    # (c) warmup-clean: sleeve net = 0 before the first valid (non-NaN) z
    close = panels(coins)["close"]
    lr = np.log(close[PT] / close[PD])
    z = (lr - lr.rolling(Z_WIN).mean()) / lr.rolling(Z_WIN).std()
    first_valid = z.first_valid_index()
    pre = net_s[net_s.index < first_valid] if first_valid is not None else net_s.iloc[:0]
    max_pre = float(pre.abs().max()) if len(pre) else 0.0
    a_warm = max_pre < 1e-12
    print(
        f"  (c) warmup-clean              first valid z @ {first_valid}  "
        f"max|net before| = {max_pre:.2e} : {_pf(a_warm)}"
    )


def _pf(ok: bool) -> str:
    """PASS/FAIL stamp for an integrity assert."""
    return "PASS" if ok else "FAIL"


if __name__ == "__main__":
    main()
