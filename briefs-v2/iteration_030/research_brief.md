# Iteration v2/030 Research Brief

**Type**: EXPLOITATION (engineering prerequisite only)
**Track**: v2 — enforcing new seed concentration rule
**Parent baseline**: iter-v2/029 (forced reset)
**Date**: 2026-04-15
**Researcher**: QR
**Branch**: `iteration-v2/030` on `quant-research`

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    ← FIXED. NEVER CHANGES.
```

## Motivation

iter-v2/029 merged as a one-time forced baseline reset. The new Seed
Concentration Check rule (skill commit `0e5ac3a`) requires auditing
per-seed per-symbol OOS PnL share across ALL 10 seeds, not just the
primary seed. Until now, the runner only saved primary-seed reports,
so the rule could not be enforced.

**iter-v2/030 is a pure engineering prerequisite iter**: it adds
per-seed concentration tracking to `run_baseline_v2.py` and produces
the first full per-seed audit in v2's history. No algorithmic changes.

The actual concentration fix is deferred to iter-v2/031+, where the
data from iter-030 will drive the fix design. Without the per-seed
data, any fix we design now is guessing about what the distribution
actually looks like.

## Hypothesis

**Per-seed concentration will reveal one of three patterns**:

1. **Structural** — most seeds concentrate on XRP > 50%. Would mean
   XRP's profitable OOS signals are fundamentally more abundant than
   other symbols; fix requires structural changes (drop XRP, add
   symbols, equal-weight allocation, or confidence_threshold cap).
2. **Bimodal** — some seeds concentrate on XRP, others distribute
   evenly. Would mean Optuna's hyperparameter search occasionally
   locks onto XRP's sweet spot; fix is Optuna range constraints or
   seed averaging.
3. **Seed-specific** — only primary seed 42 concentrates; most seeds
   distribute normally. Would mean the problem is smaller than it
   looks and a minor tweak (different primary seed, wider Optuna
   search) fixes it.

Best guess based on iter-028 and iter-029 primary seeds: **pattern 1
or 2**. iter-028 primary was 73% XRP, iter-029 primary was 61% XRP
with only 15 trials. The direction of travel suggests structural.

## Changes vs iter-029

| File | Change |
|---|---|
| `run_baseline_v2.py:52` | ITERATION_LABEL `v2-029` → `v2-030` |
| `run_baseline_v2.py:~255` | Add `per_seed_concentration` list |
| `run_baseline_v2.py:~310` | Compute per-symbol OOS share per seed |
| `run_baseline_v2.py:~360` | Print concentration audit table |
| `run_baseline_v2.py:~375` | Save `seed_concentration.json` |

**No backtest logic changes.** Same symbols, same features, same
risk gates, same 15 Optuna trials, same 10 seeds as iter-029.

## Section 6: Risk Management Design

No risk-layer changes. The same 7 active gates from iter-019-029.

### Pre-registered failure-mode prediction

The iter-030 run will produce **the same primary seed 42 metrics as
iter-029** (OOS monthly +1.28, XRP concentration 60.86%), because
the underlying backtest is unchanged. The new per-seed concentration
table will show the distribution for the other 9 seeds.

**Most likely outcome**: pattern 1 (structural) — mean per-seed
max-share will be in the 50-65% range, and 7-10 of 10 seeds will
fail the 50% rule. Fewer than 3 seeds will pass the 40% inner rule.

**If this prediction holds**, iter-031 will need a structural fix:
- Remove XRP from V2_MODELS (try 3-symbol DOGE+SOL+NEAR)
- Add a 5th symbol (AVAX, ADA, or MATIC) to dilute
- Apply a post-hoc per-symbol return cap (less clean, but simple)

**If the prediction is wrong** (pattern 2 or 3), the fix is smaller
— seed-specific tuning or Optuna constraint.

## Success criteria

iter-v2/030 is an engineering-prerequisite iter. It is NOT expected
to MERGE (cannot beat iter-029 which is the frozen baseline; also
cannot alter backtest output since no algorithmic change).

### Engineering success (non-gating)

- [ ] Runner produces `seed_concentration.json` with 10 entries
- [ ] SEED CONCENTRATION AUDIT table prints to stdout
- [ ] Audit contains max-share, max-symbol, pass/fail for all 10 seeds
- [ ] Primary seed 42 result matches iter-029 exactly (no algorithmic drift)
- [ ] The mean per-seed max-share is reported

### Research success (non-gating)

- [ ] Diary contains the full per-seed concentration table
- [ ] Diary identifies which of the 3 patterns the distribution matches
- [ ] Diary proposes a specific concentration fix for iter-031 based
      on the revealed pattern

## Exploration/Exploitation classification

**Exploitation**: no new features, symbols, or risk primitives.
Pure engineering iteration. The 70/30 rule (70 exploration / 30
exploitation) argues for a structural change — but the prerequisite
must come first.

Next exploration iter after this will be iter-031 (structural fix
based on iter-030 data).
