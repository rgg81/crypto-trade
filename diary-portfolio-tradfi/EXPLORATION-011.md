# EXPLORATION-011 — Long-term-reversal (value-proxy) sleeve + SEC-EDGAR fundamentals (iter-011)

**Date:** 2026-07-01 (multi-factor pivot; user bar = ≥0.5 Sharpe + positive every year)
**Status:** LTR sleeve **KEPT** (net +0.28→+0.33); EDGAR value/quality **BUILT but negative-EV here**. OOS HIDDEN.
**Commits:** `7ee597f8` (LTR) + `abd5ec37` (SEC-EDGAR pipeline)

## iter-011 = MOM + 0.5·LTR (3y-1y long-term reversal, De Bondt-Thaler value proxy)
| | net | bull | bear | chop | maxDD | +years |
|--|-----|------|------|------|-------|--------|
| iter-006 (mom) | +0.28 | +0.30 | −0.24 | +0.51 | −29% | 10/16 |
| **iter-011 (mom+LTR)** | **+0.33** | +0.26 | **+0.35** | +0.60 | −49% | **11/16** |
| iter-011 + VIX | +0.30 | | | | −45% | 12/16 |

LTR is **genuinely orthogonal** (mom↔LTR corr +0.01 / −0.12 in bad years) and **fixed all 3 momentum-crash
years** (2013 −1.28→+0.46, 2016 −0.56→+1.02, 2023 −0.09→+0.37); bear flipped positive. **Still misses 2017 &
2019** (low-dispersion melt-ups — structural for a market-neutral book) + 2010 (LTR 3y warm-up). Cost: maxDD
−49% (VIX tames to −45%). KEEP (accretive multi-factor step, not a promote). Leak PASS, 55/55 green.

## SEC-EDGAR PIT fundamentals (value + quality) — built, PIT-clean, but NEGATIVE-EV on this universe
Pipeline `ingest_edgar.py` + `features_fundamental.py`: SEC companyfacts, **PIT by FILING date** (test proves
AAPL FY2006 book equity invisible before its 2009 filing — no look-ahead). 56/69 usable (13 foreign-IFRS ADRs
/ dual-class tag gaps → NaN→0). **VALUE (book/price) IS −0.34** (best in bear +1.46 / 2022 growth-crash +1.60
— economically correct), **QUALITY (gross-profitability) IS −0.09**. Both orthogonal (corr <0.15) BUT
negative-EV AND negative in momentum's bad years → **do NOT rescue them** (MOM+VALUE −0.71). Reason: **2010-25
mega-cap-GROWTH universe = a historic value drought.** The pipeline is validated (correct regime/year signs);
value/quality need a universe with a real value cross-section, which the tradeable 69 lack.

## Verdict / next
Progress: **net +0.33, 11-12/16 years** — ~⅔ to the 0.5 bar. The 69 tradeable names are a homogeneous
mega-cap-growth cohort with little factor spread → value/quality/BAB/low-vol can't be harvested within them.
**iter-012 = BROAD-UNIVERSE test** (the pivotal one): do the price factors (mom/LTR/BAB/low-vol/size) + the
EDGAR value/quality work on a broad US universe with real cross-sectional diversity, and can a multi-factor
book reach 0.5 + positive-all-years there? Then: how much is realizable within the tradeable 69 (hybrid), and
the controlled directional sleeve for the 2017/2019 no-dispersion years.
