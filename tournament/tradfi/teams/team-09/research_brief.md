# team-09 — research brief — t09-short-max-lottery-v1

Family (APPROVED in registry.jsonl): **Skewness / lottery premium (short MAX)** — short names
with recent extreme daily-return spikes, long the boring low-MAX end.

Status: PRE-REGISTRATION written 2026-07-17 BEFORE any experiment was run (ledger: every
experiment line in `experiments.jsonl` is appended before its result is read). A "FINAL SPEC"
section is appended at the end after the experiment program completes; the pre-registration
sections below are immutable.

---

## 1. Economic mechanism

Retail investors overpay for lottery-like payoffs: names that recently printed extreme single-day
gains attract attention-driven buying, get bid above fair value, and subsequently underperform
(Bali–Cakici–Whitelaw "MAX effect"). The effect is strongest exactly in retail-selected,
attention-concentrated universes — and the Binance TradFi stock-perp list (~65 names) is
retail-selected by construction: it exists because these are the tickers retail wants leveraged
exposure to. The mirror leg: "boring" low-MAX names carry no lottery premium and earn it back.

Why it can survive costs here: the signal is a trailing-window extreme statistic — it changes
slowly (an extreme day enters the window once and stays for L days), so a rank book on it has
structurally low daily turnover, which is what 6 bps/side at daily cadence demands.

Known risk to the classic direction (pre-registered, per coordinator prior): in THIS universe the
high-MAX end may contain structural compounders (mega-momentum tech / crypto-adjacent names)
whose spikes are informative rather than lottery noise. The registry already shows the
52-week-high-anchor family tripping its falsifier here with sign inversion. We therefore treat
DIRECTION as the first hypothesis to test, and the falsifier below kills the family honestly if
the classic short-lottery direction has no edge anywhere in the design space.

## 2. Signal definition (design space)

Let `close` be the close panel (dates × tickers, ragged starts, never forward-filled).

- Daily return: `r[t] = close[t]/close[t-1] − 1` (strict; NaN propagates, no padding).
- **MAX(k, L)[i,t]** = mean of the `k` largest daily returns of name `i` over the trailing `L`
  trading days ending at `t` (inclusive). Windows with fewer than
  `min_obs = max(15, ceil(0.6·L))` valid returns → NaN (flat).
- **SMAX(k, L)** = MAX(k, L) / σ(L), σ(L) = std of daily returns over the same window (same
  min_obs). Separates jumpiness from the generic vol level (family-fidelity control: the book
  must not be low-vol-in-disguise).
- Cross-sectional transform: per day, rank valid signals (`method=average`);
  centered score `c = (rank − (n+1)/2) / n` ∈ (−0.5, +0.5), row-sum 0.
- Raw weight: `w = −c` (short high-MAX, long low-MAX). Rows with `n < 10` valid names → all-flat.
- Optional sector demean (aux `sector_map`): subtract the sector row-mean of the signal before
  ranking; sectors with < 3 valid names that day fall back to the global row mean.
- Optional turnover control: EMA-smooth the weight panel, halflife `h` days (past-only).
- Engine owns everything else (gross=1, |w_i|≤0.10, |net|≤0.25, shift(1), costs, vol-target).

Parameter ranges (pre-registered): `L ∈ {21, 42, 63}`, `k ∈ {1, 3, 5}`, vol-adjust ∈ {raw, SMAX},
sector-demean ∈ {off, on}, `h ∈ {0, 5, 10}`. VIX is NOT used (no regime gating in this family).

## 3. Experiment program (target ≤ 16 material experiments, hard family budget 40)

- **Stage A — direction & horizon** (raw MAX, no demean, no smoothing):
  exp-001 (k=1, L=21, classic), exp-002 (k=5, L=21), exp-003 (k=5, L=63).
- **Stage B — vol-scaled**: exp-004 (SMAX k=5 L=21), exp-005 (SMAX k=1 L=21).
- **Stage C — family-fidelity control**: exp-006 σ-only rank book (short high-vol) at L=21 —
  DIAGNOSTIC ONLY, never a submission candidate (low-vol is another team's family); verifies
  MAX adds information beyond vol.
- **Stage D — refinement of the Stage-A/B leader**: exp-007 sector-demean ON;
  exp-008 h=5; exp-009 h=10.
- **Stage E — plateau neighbors** around the champion (±1 step in L and k): 2–3 experiments.
- **Stage F — final confirmation** of the exact QE spec (numbers for is_report.md).
- **Contingency (pre-registered)**: if ALL of Stage A+B post negative Sharpe @1×, run ONE
  reversed-sign diagnostic for the record (documented as diagnostic, not a candidate), then
  invoke the falsifier: honest pivot to a then-free family or DNF. No sign-flip laundering.

Every experiment logs BOTH cost tiers (1× and 2×) from `te.run_is`.

## 4. Falsifier (pre-registered)

The family is DEAD if, across the full design space above, no configuration achieves ALL of:
net IS Sharpe @1× ≥ +0.30, net IS Sharpe @2× > 0, median names/side ≥ 5, and at least one
parameter neighbor (±1 step in L or k) also ≥ 0 (no isolated peaks). Additional kill: if the
σ-only control (exp-006) matches or beats the best MAX book AND the MAX book's weights correlate
with the σ book > 0.9 (cross-sectional, time-averaged), the "lottery" framing is dead here
(it would be a low-vol book in disguise) and we do not submit it under this family.

## 5. Selection rule (pre-registered)

Among configs passing the falsifier gates: choose the one whose WORST neighbor (±1 step in L, k)
has the highest Sharpe @1× (plateau-centered choice, not peak-chasing). Ties: lower annual
turnover, then better bear-regime Sharpe from the fixed regime scorecard.

## 6. Expected regime behavior (pre-registered)

- **Bull**: headwind for the short leg (lottery names rip in risk-on); expect the weakest
  scorecard cell. The long boring leg cushions.
- **Bear/panic**: tailwind — lottery names crash hardest (high beta + crowding unwind);
  expect the best cell.
- **Chop**: mildly positive — spikes mean-revert without a trend to pay the shorts.
- Net behavior should look defensive / negatively skew-exposed-in-reverse; if instead the book
  bleeds in bears, the mechanism is not what we think it is and that feeds the honesty check.

---

## 7. AMENDMENT 1 — pre-registered design-space EXTENSION (written 2026-07-17, AFTER
## Stages A–D results, BEFORE any extension experiment ran — elevated overfit risk, so the
## extension falsifier below is stricter than the original)

Status of the original space at amendment time (ledger exp-001b..exp-007): every classic-
direction candidate cell posted net IS Sharpe @1× between −0.86 and −1.13; the σ-only control
(exp-006, −0.92) sits on top of the raw-MAX cells and vol-stripped SMAX is worse — the
unconditional book is dominated by an anti-compounder / short-high-vol bleed in bull regimes.
Cost arithmetic kills the untested smoothing/neighbor cells without running them: the 1×→2×
Sharpe delta is ≈ 0.2 at turnover ≈ 27, so even ZERO trading cost leaves the book at ≈ −0.7.
The one pre-registered regime prediction that came TRUE in every raw-MAX cell: bear-regime
Sharpe +1.07..+1.46 (§6 said bear = tailwind). The lottery-unwind premium exists here — it is
harvestable only when stress is priced, and swamped by compounder drift the rest of the time.

Two within-family extension arms (both keep the registered direction: short high-MAX, long
boring; both use only `close` + aux `vix`):

- **E1 — long-boring half book**: long leg = low-MAX half of the centered-rank book
  (`max(−c, 0)`); short leg = the SAME total gross spread equally across ALL valid names
  (an equal-weight basket hedge). Economically: harvest the boring premium without a
  concentrated short in structural compounders. Signal params fixed at the Stage-A leader
  (k=5, L=63); one plateau neighbor (k=5, L=21) IF the first cell passes.
- **E2 — VIX-stress-gated classic book**: the full classic rank book (k=5, L=63) held ONLY
  when VIX close > its trailing 252-day p-quantile (threshold `.shift(1)`, past-only;
  min_periods 126; gate value compared is the same-day VIX close, known at decision time);
  flat otherwise. p ∈ {0.80, 0.70} (two cells). Economically: the short-lottery premium is a
  crisis-unwind premium; hold the book only when stress is priced.
- **E2 fidelity control** (only if an E2 cell passes): the SAME gate on the σ-only book. The
  gated MAX book must beat the gated σ book at 1×, else the family claim is hollow
  (low-vol-in-disguise) and E2 is dead by §4's fidelity clause.

**Extension falsifier (stricter than §4)**: an extension cell is a submission candidate ONLY if
net IS Sharpe @1× ≥ +0.40 AND @2× ≥ +0.20 AND median names/side ≥ 5 AND its pre-named neighbor
cell (E1: L=21 twin; E2: the other p) is ≥ 0 AND (for E2) it beats the gated-σ control. If no
extension cell passes, the family is FALSIFIED in full and we recommend documented pivot or DNF
— no further extensions, no sign flips.

Budget note at amendment: 10 ledger lines used (2 registration, 7 valid experiments, 1
invalidated by a lab defect). Extensions add ≤ 5 more.

---

## 8. FINAL — FAMILY FALSIFIED (2026-07-17). No QE specification is issued.

Verdict per the pre-registered falsifiers (§4 original space, §7 extension space):
**t09-short-max-lottery-v1 is DEAD in this universe.** Every candidate cell is far below the
+0.30 (original) / +0.40 (extension) floors; full numbers in `is_report.md` (all from
`te.run_is` artifacts in `out/`).

- Classic direction, all candidate cells (exp-001b..exp-007): net IS Sharpe @1× in
  [−1.13, −0.86]; @2× in [−1.73, −0.94]. Sector-demean and vol-scaling (SMAX) do not change
  the sign; SMAX is the worst end and additionally destroys the bear tailwind.
- Cost is NOT the cause: 1×→2× Sharpe delta ≈ 0.1–0.2 at turnover ≈ 11–35, so the zero-cost
  gross book is still ≈ −0.7. The untested smoothing/neighbor cells are dead by this
  arithmetic (documented instead of spent).
- Extension E1 (long-boring vs equal-weight basket): −0.73 — the "boring premium" long leg is
  itself negative here; both legs of the registered mechanism fail independently.
- Extension E2 (VIX-stress gate p80): −0.52 with bear cell +0.01 — the gate holds the
  short-lottery book through the post-trough reflex rally (VIX stays elevated past the fixed
  bear-window troughs) and gives back the crash alpha. p70 is bounded by the (−0.52, −0.86)
  sandwich and was not spent. Gated-σ control moot (no E2 cell passed).
- Mechanism autopsy: the σ-only control (exp-006, −0.92) sits ON the raw-MAX cells → the
  unconditional MAX book here is mostly a short-high-vol book, and the vol-stripped jump
  component (SMAX) is worse than that. The one confirmed pre-registered prediction is the
  regime fingerprint (bear +1.07..+1.46 in every raw cell): the lottery-unwind premium exists
  ONLY inside crash windows and is not reachable by a causal VIX gate.
- Universe interpretation (consistent with the sign-structure diagnostic exp-008, +0.54 @1×,
  bull +1.05 / bear −1.56): this retail-selected perp universe PAYS short-horizon
  jump-chasing (attention momentum on compounders) and punishes shorting it. That diagnostic
  is sign-flip provenance, fully disclosed — it is NOT a submission candidate under this
  family and was not refined further (family discipline).

**Recommendation to the orchestrator** (decision is theirs; team-02 precedent applies):
1. Preferred: ONE documented pivot to a then-free family. If a short-horizon
   attention/jump-momentum family (the disclosed sign-flip direction, distinct from t04's
   12-1 cross-sectional momentum, t10's per-name trend, and the RESERVED bear-gated TSMOM)
   is judged registrable, exp-008 provenance transfers with it for Critic audit. Otherwise a
   free menu family (e.g. #7 VIX-conditional regime books, #13 intra-sector lead-lag).
2. Honorable alternative: DNF with this negative-result bundle standing for audit.

Ledger state at close of design phase: 13 lines = 2 registrations + 10 experiment runs
(1 invalidated by a disclosed lab defect, rerun as exp-001b) + this phase used no further
budget. Material-experiment budget consumed: 10 of 40.

---
---

# PART II — t09-jump-momentum-v1 (documented pivot, APPROVED in registry.jsonl)

## II.0 Status and provenance

Pivot approved 2026-07-17 (one pivot now SPENT). Provenance: the pre-registered reversed-sign
diagnostic exp-008 (+0.542 @1× / +0.344 @2×, maxDD −0.333, turnover 27.4, breadth 24/24,
bull +1.05 / bear −1.56 / chop +0.00) — disclosed at falsification time, never refined before
this approval. This PART II pre-registration is written BEFORE any Part-II experiment ran;
ledger order proves it (exp-011 line postdates this section's commit to disk).

## II.1 Mechanism

Short-horizon jump/attention continuation: names that just printed extreme single-day returns
attract retail attention and leveraged perp flow, and in a retail-selected perp universe that
flow CONTINUES over the following weeks rather than mean-reverting. Long the recent-jump end
of the cross-section, short the boring end. This is the empirically-paid direction in this
universe (Part I autopsy: every short-lottery cell bled in bulls with the exact mirror
fingerprint; team-02's long-horizon anchor book failed while short-horizon jumpiness paid).

## II.2 Family boundaries (Critic-checked; all respected by construction)

- Lookbacks are SHORT-horizon only: L ≤ 42 trading days (≤ 2 months). NO 12-1 formation
  windows (t04's family).
- Signal is a CROSS-SECTIONAL rank of a jump statistic — never the sign of a per-name k-month
  return (t10's family).
- NO beta/market residualization, no medium-horizon momentum (t01's family).
- Returns are close-to-close ONLY — no overnight/intraday decomposition (t07's family).
- NO VIX use of any kind, no regime switching (t06's family). `aux['vix']` is not read.

## II.3 Signal definition (design space, pre-registered)

- `r[t] = close[t]/close[t-1] − 1` (strict NaN, no padding).
- **JUMP(k, L)[i,t]** = mean of the `k` largest daily returns of name `i` over the trailing
  `L` days ending at `t − d` (skip parameter `d` for 1-day-reversal avoidance).
  Validity: `min_obs = max(min(15, L−2), ceil(0.6·L))` valid returns, else NaN → flat
  (reduces to Part I's formula at L ∈ {21, 42}; keeps the anchor replication exact).
- Optional vol adjustment: JUMP/σ(L), σ = same-window std (same min_obs).
- Cross-sectional transform: centered rank `c = (rank − (n+1)/2)/n`; raw weight `w = +c`
  (long high-jump, short boring). Rows with n < 10 valid names → flat. Optional variants:
  sector-demean before rank; tercile concentration (+1 top third / −1 bottom third / 0 mid).
- Turnover control (FIRST-CLASS, cost axis is existential at 6 bps/side): EMA on the weight
  panel, halflife `h ∈ {0, 3, 5, 10}` days.
- Parameter ranges: `L ∈ {10, 21, 42}`, `k ∈ {1, 3, 5}`, `d ∈ {0, 1}`, vol-adj ∈ {off, on},
  sector-demean ∈ {off, on}, concentration ∈ {rank, tercile}.

## II.4 Experiment program (target ≤ 13 runs; 27 ledger lines of headroom)

- **P0 anchor replication**: exp-011 = (k=1, L=21, d=0, h=0) in the NEW lab — must reproduce
  exp-008's evaluator numbers exactly (pristine sign-flip chain; the old lab's `sign=−1` and
  the new lab's `w=+c` are algebraically identical).
- **P1 horizon/width grid** (h=0): exp-012 (k=1, L=10), exp-013 (k=1, L=42),
  exp-014 (k=3, L=21), exp-015 (k=5, L=21).
- **P2 smoothing on the P1 leader**: h ∈ {3, 5, 10} (3 runs).
- **P3 single-cell variants on the leader(+best h)**: skip d=1; vol-adj ON; sector-demean ON
  (run in that order; drop remaining P3 cells if two consecutive degrade the leader).
- **P4 plateau completion**: any ±1-step neighbor of the selected spec not yet run (≤ 2).
- **P5 final confirmation** of the exact QE spec (the is_report numbers).

## II.5 Falsifier (pre-registered)

The pivot family is DEAD (→ DNF; no second pivot exists) if no cell achieves ALL of:
net IS Sharpe @1× ≥ +0.40, @2× ≥ +0.20, median names/side ≥ 5, and at least one ±1-step
neighbor (in L, k, or h) with Sharpe @1× ≥ 0. Additional honesty tripwire: if the P0
replication fails to reproduce exp-008, STOP — the provenance chain is broken and the Critic
is notified before anything else runs.

## II.6 Selection rule (pre-registered)

Among cells passing II.5: maximize the MINIMUM @1× Sharpe over the cell and all its run
±1-step neighbors (plateau-centered, never the peak). Ties: higher @2× Sharpe, then lower
annual turnover. The chosen cell is then confirmed as P5 and becomes the QE spec verbatim.

## II.7 Expected regime behavior (pre-registered)

Bull: strongly positive (attention flow chases jumps). Bear: negative — this book carries
crash/unwind exposure (anchor: bear −1.56); accepted and disclosed, the engine vol-target is
the only mitigation (VIX gating is out of family bounds). Chop: ~flat. Deployment posture:
bull-harvester with disclosed crash risk; the holdout verdict rides on regime mix.

---

## II.8 FINAL SPEC — the QE specification (COMPLETE; nothing is left to the QE's judgment)

Selected by the pre-registered rule II.6 over the completed neighborhood (see is_report.md
Part II): **JUMP(k=3, L=42), linear centered rank, EMA halflife 10** — the plateau center,
not the peak. Confirmed by P5 (exp-026 bit-identical to exp-021).

**Evaluator numbers (out/exp-026_metrics.json): net IS Sharpe +0.727 @1× / +0.689 @2×,
maxDD −0.333, annual turnover 6.0, breadth 24/24 median names L/S, 174 months.**
Neighborhood (all @1×): (1,42,h10) +0.706 · (5,42,h10) +0.725 · (3,21,h10) +0.682 ·
(3,42,h5) +0.732 — worst neighbor +0.682. Every II.5 gate passed.

### Exact algorithm for `build_raw_weights(pn, aux)`

Inputs used: `pn['close']` ONLY. `aux` is NOT used (`vix` never read — family bound;
`sector_map` unused; `seed` irrelevant — the strategy is fully deterministic).
Derive tickers/dates from the panel at runtime; hard-code nothing.

1. `r = close / close.shift(1) - 1` — strict NaN propagation, no padding, no fill.
2. `JUMP[i, t]` = mean of the **3 largest** values of `r[i]` over the trailing **42 rows**
   `t-41 .. t` inclusive. Validity: count of non-NaN `r` in the window; if `< 26`
   (`min_obs = max(min(15, L-2), ceil(0.6*L)) = 26`), `JUMP = NaN`.
   (Reference: NaN→−inf, `np.partition` top-3 over sliding windows; any −inf in the top-3
   is impossible when validity ≥ 26.) Rows `t < 41` (window incomplete): NaN.
3. Cross-sectional transform per day `t`:
   `rank = JUMP.rank(axis=1, method="average")` (ascending, NaN excluded);
   `n[t]` = count of non-NaN `JUMP[·, t]`;
   `c = (rank - (n+1)/2) / n` — centered rank in (−0.5, +0.5), row-sum ≈ 0.
4. `w_pre = +c` (LONG high-jump, short boring — the family direction).
   Rows with `n < 10` → entire row set to 0. All remaining NaN → 0.
5. `w = w_pre.ewm(halflife=10, min_periods=1).mean()` — pandas EMA down the rows (days),
   applied to the FULL panel including the zero rows (warmup zeros enter the EMA; do not
   skip or mask rows).
6. Return `w` (index × columns of the input panel). The engine owns everything downstream.

No skip parameter (d=0; exp-019 showed the d-axis inert), no vol adjustment (exp-020
degrades), no sector demean (dropped by the pre-registered two-consecutive-degrades rule),
no tercile book, no VIX, no volume/open/high/low, no randomness.

### Acceptance criteria for the QE implementation

- `te.run_is` metrics at 1× and 2× must equal `out/exp-026_metrics.json` EXACTLY (the
  reference implementation is `out/scratch/scratch_jump_lab.py` with config
  `{"k":3, "L":42, "d":0, "smooth_hl":10}`; exp-026 ≡ exp-021 proved determinism).
- Harness: all `cli.py audit` checks must pass (pure function of inputs; no file I/O,
  no network, no subprocess in `strategy.py`).

### Known weaknesses (disclosed for the record, no further design responses permitted)

- Bear-regime Sharpe −1.40 (crash/unwind exposure). Accepted: mitigation via regime
  switching is out of family bounds; the engine vol-target is the only defense.
- The book is bull-loaded (+1.06 bull / +0.54 chop); Stage-2 holdout outcome rides on the
  2024-07 → 2026-06 regime mix. This is a property of the mechanism, not a defect.

### Deviation log (for Critic audit)

- Part II ran 16 experiments vs the pre-registered target "≤ 13": +3 P4-extension cells
  (exp-023/024/025), ledgered with rationale BEFORE running — the alternative was selecting
  (3,42,h10) on an under-scrutinized single-neighbor min (a peak-chasing loophole in II.6).
  The extension is conservative (adds scrutiny to the winner); hard budget unaffected
  (29 of 40 ledger lines used, incl. 2 registrations and 1 invalidated Part-I run).
