# team-06 provenance — t06-sector-pairs-coint-v1

## What was read (Phase 1 + Phase 2)

Authorized tournament documents:
- tournament/tradfi/CHARTER.md, config.toml, FAMILY-MENU.md, registry.jsonl
- tournament/tradfi/teams/team-06/ (own tree only)
- Evaluator source: analysis/portfolio/tradfi/tournament/{engine.py, constants.py} and a
  targeted grep of metric-helper signatures in analysis/portfolio/tradfi/core_tradfi.py
  (approved substrate module). holdout.py NOT read. MANIFEST.sha256.json NOT read.

Data access: EXCLUSIVELY `tournament.engine.load_is_panels()` / `te.team_view(pn)` /
`te.run_is(raw, pn)` from scratch scripts inside tournament/tradfi/teams/team-06/, run from the
worktree root. No direct reads of tournament/tradfi/data_is/ files, no data/ store access,
no network access, no ret_fwd use in signal construction.

## What was imported in scratch code

numpy, pandas, stdlib (sys, json, math, itertools, time), tournament.engine (te).
No scipy needed to date. No statsmodels (DF t-stat implemented from first principles via OLS).

## Independence statement

All design decisions derive from: the tournament documents above, the evaluator interface, and
public-domain quant knowledge (Engle-Granger cointegration, Gatev distance pairs, standard
z-score band trading). No contact or information exchange with any other team; no access to any
other team's directory; no incumbent-book files (BASELINE_TRADFI.md, reports-tradfi/,
diary-portfolio-tradfi/, iter_*.py, splice/live modules) were read at any point by this agent.
The prior Phase-1 registration work (residual momentum, low-vol/BAB — both vetoed) used no data.

## Pivot disclosure (t06-vix-regime-books-v1, reg-024)

After the accepted falsification of the pairs family, the single documented pivot was
exercised to family #7 (VIX-conditional regime books), pre-approved by the orchestrator.
Pivot research used the same access path (te.load_is_panels / te.team_view / te.run_is from
out/scratch/scratch_vixbooks.py) and only `close` + `aux['vix']` as inputs. The two
unconditional inner books (12-1 momentum, short-horizon reversal) were run ONLY as disclosed
fidelity-reference diagnostics (exp-025/026); the submitted mechanism is the regime-conditional
book switch, and the fidelity falsifier (brief §P4.2) required the composite to beat both
references by >= +0.10 Sharpe (achieved: +0.25). aux['seed'] is unused — the strategy is
deterministic with no randomness. Ledger closed at the 40-line hard cap.

## Phase-2 outcome disclosure (retired pairs family)

The family was falsified (research_brief.md §8, is_report.md). One sign-flip forensic
(exp-022) was run as a DISCLOSED diagnostic to characterize the spread process (divergence
direction also negative); it was never a tradable candidate and no pivot family was researched
without registration. Scratch code lives in out/scratch/scratch_pairs.py; all evaluator outputs
in out/scratch_results.jsonl. No strategy.py was written.

## Ledger discipline

Every experiments.jsonl line is appended BEFORE its result is read; batch lines are appended
before the batch script runs. reg-001/reg-002 = registration events. Census/diagnostic lines
are logged with type "diagnostic" and count against the hard cap conservatively.

## Phase-2 QE implementation notes (strategy.py)

Implemented strictly from the frozen QR spec (research_brief.md §P7, COMBO B / exp-038). No
hidden research choices: every parameter is a fixed module constant taken verbatim from the spec
(PCT_WIN=504, MIN_PCT_OBS=252, HI=0.85, LO=0.70, MOM_SKIP=21, MOM_FORM=252, REV_WIN=10, WINS=3.0,
MIN_NAMES=10, EMA_HL=3.0). The three internal helpers mirror the QR scratch engine
(out/scratch/scratch_vixbooks.py) operation-for-operation so the evaluation reproduces the
scratch results bit-for-bit rather than merely approximately:
- `_vix_state`: trailing-percentile VIX state with a start-anchored hysteresis loop (initial
  calm; stressed once pct >= 0.85, calm once pct <= 0.70, carry otherwise). Percentile window is
  trailing and row-anchored; the state loop iterates from row 0 — pure causal, truncation-safe.
- `_xz_book`: strictly row-wise cross-sectional z -> winsorize(±3) -> re-demean -> (negate for
  reversal) -> min-names gate -> row gross-normalise -> fillna(0.0). No cross-row information.
- `build_raw_weights`: momentum book (close.shift(21)/close.shift(252)-1), reversal book
  (close/close.shift(10)-1, negated), regime blend (1-s)*w_mom + s*w_rev, then causal EMA(hl=3).

Inputs used: ONLY `pn['close']` and `aux['vix']`. No sector_map, no volume, no OHLC beyond close,
no ret_fwd, no aux['seed'] (strategy is deterministic — no randomness). Returns RAW signed
weights only; the engine owns gross-normalisation, the 0.10/0.25 caps, the .shift(1) decision
lag, taker costs, and vol-targeting (none pre-applied by the strategy).

Imports in strategy.py: numpy, pandas only. Imports in test_strategy.py: numpy, pandas, and the
local `strategy` module only (kept inside the static-scan whitelist — no pytest, no evaluator
imports); tests run on self-contained synthetic panels with no file reads.

Verification (all green):
- `pytest tournament/tradfi/teams/team-06/test_strategy.py` — 7 passed (determinism,
  future-corruption <= cut invariance, truncated-replay <= cut invariance, same-bar strict-before
  invariance, regime-state truncation-safety + both-regimes-exercised, output shape/finiteness,
  books-exercised guard against vacuous leak tests).
- `cli.py team-run --team team-06` — Sharpe +0.7388 @1× / +0.6393 @2×, maxDD −0.2298 / −0.2336,
  ann. turnover 18.13×, breadth 22/27, total return +3.443 / +2.547, regime (bull/bear/chop)
  +0.63/+0.41/+1.28 @1×. Matches exp-038 / exp-040 exactly.
- `cli.py audit --team team-06` — PASS (scan, determinism, truncation, corruption, same-bar all
  ok; 0 violations; 11 truncation cuts).

Files authored by the QE, all under tournament/tradfi/teams/team-06/: strategy.py, test_strategy.py.
No shared tournament files, evaluator package, or other-team directories were modified.
