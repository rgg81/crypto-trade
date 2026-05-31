# Skill v1 — Bundle Discipline Rules (Draft for Insertion)

**Status**: Draft authored 2026-05-31 by QR after user veto of an unintended-design bundle (iter-v1/038 candidate). The bundle composed BASELINE_V1 + iter-v1/036 with overlapping coins (LINK, DOT), assigned ad-hoc weights, and produced backtest results that cannot be replayed live (a single account cannot hold two simultaneous positions in the same symbol from two models).

This draft codifies three new rules in skill text ready for direct insertion into `.claude/commands/quant-iteration-v1.md`. Each rule is self-contained, cites existing skill structure, includes a concrete example, and specifies the enforcement mechanism.

---

## Rule 1 — Backtest-Live Parity (HARD GATE, ENFORCED)

### Skill text (ready-to-insert)

```markdown
### Backtest-Live Parity — Bundle Composition Constraint (HARD GATE)

Every bundle composition method MUST produce IDENTICAL trade decisions in backtest
and live. This rule was IMPLICIT in v1 prior to 2026-05-31; it is now EXPLICIT and
HARD.

**Decision rule**: a bundle's per-(symbol, candle) action MUST be a deterministic
function of:
- Each component's signal at the SAME timestamp t (same-time-snapshot only)
- Each component's INTERNAL position-size weight (frozen pre-Phase-6, see Rule 3)
- Static bundle configuration (universe assignment, dispatch rule)

Aggregation rules that depend on POST-TRADE information BLOCK. Examples of forbidden
constructs:
- Summing realized PnL of simultaneously-open positions across two models that both
  trade the same symbol (post-trade aggregate; not replayable tick-by-tick)
- "Net" exposure of two models in the same symbol netted into one Binance order
  (requires intra-tick reconciliation that `live/engine.py:_tick` does not implement)
- Any rule referencing future bars relative to the decision candle

**Enforcement**: Critic Check 15 (NEW, v1-only). The Critic verifies the bundle's
decision rule is implementable at `live/engine.py:_tick` using only same-time-snapshot
per-component signals + each component's own internal weight. If the bundle would
require the engine to take a position a single Binance account cannot hold (long+long
in same symbol from two models, conflicting long/short, etc.), the verdict is
BLOCK-FINAL with reason `BUNDLE-PARITY-VIOLATION`.

The Critic runs Check 15 in Phase 7.5 for `CONFIRMATION-PORTFOLIO` iterations only;
EXPLORATION single-component iterations are exempt (single component is trivially
live-replayable).
```

### Concrete example

VIOLATION: A bundle that composes `BASELINE_V1` (which trades LINK in Model C) with `iter-v1/036` (which also trades LINK in a new specialist) and aggregates by "sum PnL of both open LINK positions". A single Binance account cannot hold two independent LINK positions; the backtest's "sum" cannot be replayed.

VALID: A bundle that partitions the universe so each coin is owned by exactly one component (see Rule 2), then dispatches the (symbol, candle) decision to that owner. Each owner runs its own internal sizing weight. Result is one signal per (symbol, candle), trivially replayable.

### Enforcement mechanism

- **Agent**: Critic (Phase 7.5)
- **Check**: NEW Critic Check 15 — Backtest-Live Parity
- **Trigger**: every iteration with TYPE = `CONFIRMATION-PORTFOLIO`
- **Verdict on fail**: `BLOCK-FINAL` with reason `BUNDLE-PARITY-VIOLATION`
- **Diary line added**: `- Check 15 (Backtest-Live Parity): PASS / FAIL  (CONFIRMATION-PORTFOLIO-only)`

### Backtest-live parity implication

If Check 15 PASSES, the bundle is provably implementable in `live/engine.py:_tick` with no logic gap — every backtest trade has a one-to-one live counterpart.

---

## Rule 2 — No Coin Overlap Across Bundle Models (NEW, HARD)

### Skill text (ready-to-insert)

```markdown
### Bundle Universe Partition — No Coin Overlap (HARD)

In a bundle, NO single coin may appear in the universe of two or more component
models. Each coin is owned by EXACTLY ONE model. Bundles are SYMBOL-PARTITIONED
federations of specialists.

This rule is what makes Rule 1 (Backtest-Live Parity) trivially achievable: with
universe disjointness, the per-(symbol, candle) decision is unambiguously one
model's call — there is no aggregation, no netting, no inter-model arbitration.

**Brief Section 11 (Bundle Composition) MUST list per-component universes and assert
pairwise disjointness explicitly**:

```markdown
### Universe Partition
- Component A (iter-v1/NNN-a): {BTCUSDT, ETHUSDT}
- Component B (iter-v1/NNN-b): {LINKUSDT, DOTUSDT}
- Component C (iter-v1/NNN-c): {LTCUSDT}
- Pairwise disjoint: YES  (A ∩ B = A ∩ C = B ∩ C = {})
- Union: {BTCUSDT, ETHUSDT, LINKUSDT, LTCUSDT, DOTUSDT}
```

If a candidate component's universe overlaps an existing component, the QR MUST
either (a) drop the overlapped coin from one of the components (rerun the smaller
component without that coin and document the resulting metrics in the catalog),
or (b) drop the candidate component from the bundle.

**Enforcement**: Critic Check 16 (NEW, v1-only). The Critic computes pairwise
universe intersections across all bundle components from brief Section 11. Any
non-empty intersection → BLOCK-FINAL with reason `BUNDLE-UNIVERSE-OVERLAP`.
```

### Concrete example

VIOLATION: `bundle = {BASELINE_V1 (BTC+ETH+LINK+LTC+DOT cohorts), iter-v1/036 (LINK+DOT specialist)}`. LINK appears in both; DOT appears in both. Check 16 BLOCKS.

VALID: `bundle = {baseline_pool_A (BTC+ETH), iter-v1/036 (LINK+DOT), baseline_D (LTC)}`. Disjoint universes. Check 16 PASSES.

Re-composition under Rule 2: to admit `iter-v1/036`, the QR removes LINK and DOT from `BASELINE_V1`'s active universe in this bundle (the underlying baseline doesn't change — its baseline-level metrics still anchor the broader catalog — but in THIS bundle the baseline-pool components for LINK and DOT are dropped in favor of `iter-v1/036`). Brief Section 11 documents the re-composition and runs the per-pool component substitution test.

### Enforcement mechanism

- **Agent**: Critic (Phase 7.5)
- **Check**: NEW Critic Check 16 — Universe Disjointness
- **Trigger**: every iteration with TYPE = `CONFIRMATION-PORTFOLIO`
- **Verdict on fail**: `BLOCK-FINAL` with reason `BUNDLE-UNIVERSE-OVERLAP`
- **Phase 5.5 pre-check** (optional, recommended): the Phase 5.5 Engineer also reads Section 11 and BLOCKS early if overlap is declared, saving Phase 6 compute.
- **Diary line added**: `- Check 16 (Universe Disjointness): PASS / FAIL  (CONFIRMATION-PORTFOLIO-only)`

### Backtest-live parity implication

Universe disjointness makes the bundle's decision rule a pure function of `(symbol, t) → owning_component.signal_at(symbol, t)`, which is trivially the same in backtest and live — there is no aggregation step that could differ between regimes.

---

## Rule 3 — Bundle Weights Are IS-Only Computed by QR (NEW, METHODOLOGY)

### Skill text (ready-to-insert)

```markdown
### Bundle Weights — IS-Only Derivation, Pre-Registered (METHODOLOGY)

Bundle weights (per-component position-size scaling, capital allocation factors, or
any other multiplicative weight applied to a component's signal) MUST be derived
from IS-only data by the QR during Phase 5 brief authoring. Weights are
PRE-REGISTERED in brief Section 11 BEFORE Phase 6 backtest launches. NO OOS
metrics may appear in the derivation chain.

**Derivation must be a deterministic function** of IS metrics. Acceptable methods
(examples; QR documents the chosen one):
1. EQUAL weights — `w_i = 1 / N` for N components
2. IS-Sharpe-proportional — `w_i = SR_IS_i / Σ SR_IS_j` (clipped at 0)
3. IS-inverse-variance — `w_i ∝ 1 / σ_IS_i` (risk parity in volatility space)
4. IS-risk-parity — allocate so each component contributes equal IS portfolio risk
5. QR-documented choice — any other derivation, fully specified, IS-only

**Mandatory artifact**: `analysis/iteration_v1-NNN/weight_calibration.py` (or
equivalent) that:
- Reads ONLY IS-window data (every loaded timestamp satisfies `close_time <
  OOS_CUTOFF_MS`)
- Computes the weights deterministically (no random seeds without explicit seeding)
- Writes `analysis/iteration_v1-NNN/bundle_weights.csv` with columns
  `[component_id, weight, derivation_method, is_window_start, is_window_end]`
- Is COMMITTED before Phase 6.0 Critic pre-flight

Brief Section 11 quotes the computed weights verbatim from `bundle_weights.csv`
and cites the script path.

**Enforcement**: Critic Check 17 (NEW, v1-only). The Critic:
1. Confirms `analysis/iteration_v1-NNN/weight_calibration.py` exists and is committed
2. Greps the script for any reference to OOS data (`OOS_CUTOFF`, `>=
   OOS_CUTOFF_MS`, `oos_window`, `out_of_sample`, hard-coded post-2025-03-24 dates
   used for FILTERING IN rather than filtering OUT) — any forward-pointing
   reference → BLOCK-FINAL
3. Confirms `bundle_weights.csv` matches brief Section 11
4. Confirms each loaded data source in the script respects the IS-window cutoff

Any failure → BLOCK-FINAL with reason `BUNDLE-WEIGHT-OOS-LEAK`.
```

### Concrete example

VIOLATION: A `weight_calibration.py` that reads `reports-v1/iteration_v1-036/out_of_sample/trades.csv` to compute "post-2025-03-24 Sharpe" for each component, then assigns weights proportional to OOS Sharpe. This leaks OOS into the IS-only derivation — Check 17 BLOCKS.

VALID: A `weight_calibration.py` that loads `reports-v1/iteration_v1-036/in_sample/trades.csv` only, computes IS Sharpe per component over the full IS window, and writes:

```csv
component_id,weight,derivation_method,is_window_start,is_window_end
baseline_pool_A,0.35,is_sharpe_proportional,2021-03-24,2025-03-24
iter-v1/036,0.45,is_sharpe_proportional,2021-03-24,2025-03-24
baseline_D,0.20,is_sharpe_proportional,2021-03-24,2025-03-24
```

Brief Section 11 quotes the table verbatim and points the reader to the script. Check 17 PASSES.

### Enforcement mechanism

- **Agent**: Critic (Phase 7.5)
- **Check**: NEW Critic Check 17 — Bundle Weight IS-Only Provenance
- **Trigger**: every iteration with TYPE = `CONFIRMATION-PORTFOLIO`
- **Verdict on fail**: `BLOCK-FINAL` with reason `BUNDLE-WEIGHT-OOS-LEAK`
- **Phase 5.5 pre-check**: Engineer verifies `weight_calibration.py` and `bundle_weights.csv` exist and Section 11 cites them. Missing → BLOCK at Phase 5.5.
- **Diary line added**: `- Check 17 (Bundle Weight IS-Only Provenance): PASS / FAIL  (CONFIRMATION-PORTFOLIO-only)`

### Backtest-live parity implication

Because weights are frozen from IS-only data BEFORE the OOS window is touched, the same weight vector is used in IS evaluation, OOS evaluation, and live deployment — there is no path by which OOS performance could re-tune the weights. This eliminates the most subtle leakage vector in ensemble construction (LdP AFML Ch. 11 — "the meta-model must be calibrated before OOS").

---

## Proposed Insertion Points in `.claude/commands/quant-iteration-v1.md`

### Insertion 1 — Phase 7.5 Critic Check 15/16/17 definitions

**File**: `.claude/commands/quant-iteration-v1.md`
**Insert after**: the existing "Check 14 — Axis Family Validation" definition (around line 846, the section that introduces v1-only checks)
**New subsection**: "Checks 15, 16, 17 — Bundle Discipline (v1-only, CONFIRMATION-PORTFOLIO-only)"
**Content**: copy the "Skill text (ready-to-insert)" blocks from Rules 1, 2, 3 above.

### Insertion 2 — Phase 7.5 dispatch prompt update

**File**: `.claude/commands/quant-iteration-v1.md`
**Line**: ~1448 (the Phase 7.5 orchestrator dispatch `prompt:` string)
**Edit**: append `+ Check 15 (Backtest-Live Parity) + Check 16 (Universe Disjointness) + Check 17 (Bundle Weight IS-Only Provenance) [last three CONFIRMATION-PORTFOLIO-only]` to the checks list.

### Insertion 3 — Phase 8 diary template

**File**: `.claude/commands/quant-iteration-v1.md`
**Line**: ~1349 (Critic Review Summary block in the diary template)
**Edit**: add three new lines after "Check 14":
```
- Check 15 (Backtest-Live Parity): PASS / FAIL  (CONFIRMATION-PORTFOLIO-only)
- Check 16 (Universe Disjointness): PASS / FAIL  (CONFIRMATION-PORTFOLIO-only)
- Check 17 (Bundle Weight IS-Only Provenance): PASS / FAIL  (CONFIRMATION-PORTFOLIO-only)
```
Also extend the OVERALL enumeration to include `BUNDLE-PARITY-VIOLATION | BUNDLE-UNIVERSE-OVERLAP | BUNDLE-WEIGHT-OOS-LEAK` as BLOCK-FINAL reasons.

### Insertion 4 — Brief Section 11 template

**File**: `.claude/commands/quant-iteration-v1.md`
**Line**: ~1298–1310 (the "Section 11 — Bundle Composition" template block)
**Edit**: add four required sub-blocks AFTER the existing bullets:
1. **Universe Partition** (per-component universes + pairwise-disjoint assertion + union)
2. **Backtest-Live Parity Statement** (one-paragraph proof that the bundle's decision rule is replayable at `live/engine.py:_tick`)
3. **Weight Derivation** (method + script path + bundle_weights.csv quote + assertion "IS-only, no OOS dependency")
4. **Re-Composition Note** (if a component coin is dropped to satisfy Rule 2: which component, which coin, where the dropped-coin metrics are documented in the catalog)

### Insertion 5 — Phase 5.5 gate

**File**: `.claude/commands/quant-iteration-v1.md`
**Line**: ~655–658 (CONFIRMATION cadence verification block)
**Edit**: add three pre-checks for TYPE = `CONFIRMATION-PORTFOLIO`:
- Brief Section 11 includes Universe Partition with `Pairwise disjoint: YES`. BLOCK if NO or missing.
- Brief Section 11 includes Weight Derivation with committed `analysis/iteration_v1-NNN/weight_calibration.py` + `bundle_weights.csv`. BLOCK if missing.
- Brief Section 11 includes Backtest-Live Parity Statement. BLOCK if missing.

This is intentional redundancy with Critic Checks 15/16/17 — Phase 5.5 catches missing-section cases (cheap), Phase 7.5 catches deeper-substantive-violation cases (expensive, semantic).

### Insertion 6 — Anti-Pattern catalog (A14, A15, A16)

**File**: `.claude/commands/quant-iteration-v1.md`
**Section**: anti-pattern A1-A13 catalog (referenced at line 722)
**Add**:
- **A14 — Cross-Model Symbol Overlap In Bundle**: any CONFIRMATION-PORTFOLIO brief where Section 11 enumerates two components that share at least one coin in their universes. Static scan during Phase 6.0 mini-Check 13.
- **A15 — Bundle Weight Computed Post-OOS**: any commit to `analysis/iteration_v1-NNN/` that touches `weight_calibration.py` AFTER the first commit to `reports-v1/iteration_v1-NNN/out_of_sample/`. Static scan during Phase 6.0.
- **A16 — Bundle Aggregation Requires Post-Trade Information**: any brief Section 11 method description containing phrases like "sum of realized PnL", "net position across models", "ex-post correlation-adjusted weight". Static scan during Phase 6.0.

---

## Versioning Note

These rules become effective for iter-v1/038 (the iteration that triggered the veto) and forward. Prior CONFIRMATION-PORTFOLIO iterations (if any exist in catalog) are GRANDFATHERED but flagged in `briefs-v1/exploration_catalog.md` with a column `bundle_discipline_pre_2026_05_31: TRUE`. They are NOT bundles of record going forward — any future bundle composition decision starts from a re-curated catalog under the new rules.
