# team-09 — provenance & independence statement

Updated 2026-07-17, end of Part-II design phase (t09-jump-momentum-v1 final spec issued;
Part-I family t09-short-max-lottery-v1 falsified — both records in is_report.md).

## What was read

Charter-authorized only:
- `tournament/tradfi/CHARTER.md`, `tournament/tradfi/config.toml`,
  `tournament/tradfi/FAMILY-MENU.md`, `tournament/tradfi/registry.jsonl`
- `tournament/tradfi/teams/team-09/` (own tree only)
- Evaluator source: `analysis/portfolio/tradfi/tournament/engine.py`, `constants.py`
  (holdout.py NOT opened)
- Approved substrate module source: `analysis/portfolio/tradfi/core_tradfi.py`
  (metric semantics: msharpe, regime tags, vol-target, turnover)
- `.claude/agents/tradfi-tournament-qr.md` (role definition)

NOT read (clean-room): `data/` (raw store), `data_live_tradfi/`, `data/funding_rates/`,
`diary-portfolio-tradfi/`, `BASELINE_TRADFI.md`, `reports-tradfi/`,
`analysis/portfolio/tradfi/iter_*.py`, `oos_forensic.py`, `splice_loader.py`,
`reconcile_basis_tradfi.py`, `live_tradfi.py`, `live_weights_tradfi.py`,
`analysis/portfolio/tradfi/tournament/holdout.py`, `tournament/tradfi/MANIFEST.sha256.json`,
`tournament/tradfi/results/`, `tournament/tradfi/critic/`, any other team's directory,
`tournament/tradfi/RUNBOOK.md` (not on the authorized list). No network access of any kind.

## How market data was accessed

Exclusively `tournament.engine.load_is_panels()` (manifest-verified frozen IS snapshot) from
the scratch script `out/scratch/scratch_max_lab.py`, run from the worktree root. Signals were
built from `team_view(pn)` (OHLCV; only `close` used) + `aux` (`sector_map`, `vix`);
`pn['ret_fwd']` was passed only to `te.run_is` for scoring and never entered signal
construction. Every reported number is a `te.run_is` output archived in `out/*_metrics.json`.

## Imports in team scratch code

stdlib (`sys`, `json`, `math`), `numpy` (incl. `sliding_window_view`), `pandas`,
`tournament.engine`. No file I/O of market data, no subprocesses, no network.

## Disclosures

1. **Lab defect (exp-001)**: first run used `sig.notna().count(axis=1)` (column count, not
   valid-signal count) as the rank-centering denominator → long-tilted book (breadth 32/16).
   Disclosed in the ledger, result marked INVALID, rerun as exp-001b after the one-line fix.
   The defective artifact `out/exp-001_metrics.json` is retained for audit.
2. **Design-space extension (Amendment 1)**: E1/E2 arms were added AFTER Stage A–D results,
   pre-registered in research_brief.md §7 with a stricter falsifier BEFORE either ran
   (ledger order: exp-001b..008 → amendment → exp-009/010).
3. **Sign-flip provenance (exp-008)**: one pre-registered reversed-sign DIAGNOSTIC was run
   for the falsification record (+0.542 @1×). It was not refined, extended, or treated as a
   candidate: the reversed direction is outside the registered family. If the orchestrator
   grants a pivot toward it, this disclosure is the audit trail (team-02 precedent).
4. **Unspent cells**: smoothing (h ∈ {5,10}), plateau neighbors, E2 p=0.70, and the gated-σ
   control were not run; each exclusion is justified by explicit arithmetic bounds in
   is_report.md rather than silence.

## Part II additions (t09-jump-momentum-v1, approved pivot)

- Registry re-read to confirm the pivot approval line (authorized artifact).
- New scratch lab `out/scratch/scratch_jump_lab.py`: same evaluator-only data path; uses
  `team_view(pn)['close']` ONLY. `aux['vix']` is never read (family bound: no regime
  switching); `aux['sector_map']` reachable only via the sector-demean option, which was
  dropped unrun by a pre-registered rule — the FINAL SPEC uses no aux at all.
- Provenance chain for the pivot: exp-008 (Part I pre-registered diagnostic) → registry
  approval with Critic-scrutiny flag → P0 replication exp-011 reproduced exp-008's evaluator
  output exactly before any refinement ran.
- Pre-registration order preserved: research_brief.md PART II (§II.1–II.7) was written to
  disk before exp-011's ledger line; the 3-cell P4 extension (exp-023/024/025) was ledgered
  with rationale before running; §II.8 (final spec) was written after P5.
- Part II unspent cells: sector-demean and tercile variants (dropped by the pre-registered
  two-consecutive-degrades rule); (5,21,h10)-type corner cells outside any selection
  neighborhood. No number in is_report.md comes from anywhere but `out/*_metrics.json`.

## Part III — QE implementation (2026-07-17, distinct agent from the QR)

- Read only: `tournament/tradfi/CHARTER.md`, `config.toml`, own `teams/team-09/` tree
  (`BOOTSTRAP.md`, `research_brief.md` incl. §II.8, `out/scratch/scratch_jump_lab.py`,
  `out/exp-026_metrics.json`), and the evaluator interfaces implemented against
  (`analysis/portfolio/tradfi/tournament/engine.py`, `harness.py`, `protocol.py`, `cli.py`,
  `leaderboard.py`). Clean-room list honoured: no `data/`, no `holdout.py`, no `results/`,
  no `critic/`, no other team's tree, no `MANIFEST.sha256.json`. No network, no subprocess
  from strategy/test code.
- `strategy.py` implements §II.8 verbatim with the config inlined (`k=3, L=42, d=0,
  smooth_hl=10`); it is an exact numerical transcription of `scratch_jump_lab.build_raw`
  restricted to that config (same `sliding_window_view` + `np.partition` top-k, same
  `min_obs=26`, same centered-rank `c=(rank-(n+1)/2)/n`, same `w=+c`, same n<10 flat rule,
  same `ewm(halflife=10, min_periods=1)`). Reads `pn['close']` ONLY; `aux` is never touched
  (vix/sector_map/seed unused — the strategy carries no randomness and no regime logic).
- Imports in `strategy.py`: `math`, `numpy` (incl. `numpy.lib.stride_tricks.sliding_window_view`),
  `pandas`. Imports in `test_strategy.py`: `numpy`, `pandas`, local `strategy` (NO pytest —
  bare `test_*` asserts, so the file passes the audit static-import whitelist too).
- Verification (all green): `pytest test_strategy.py` 8/8 (incl. a future-corruption self-check
  that mangles bars strictly after a cut and asserts at/before-cut weights byte-identical, a
  same-bar strict-past check, and a determinism check); `cli.py team-run` reproduces
  `out/exp-026_metrics.json` bit-for-bit; `cli.py audit` PASS on all five checks.
- No hidden research choices were made: §II.8 fully specified the algorithm and every parameter;
  zero ambiguities were bounced. The engine's gross-normalise / 0.10 + 0.25 caps / shift(1) /
  cost / vol-target stages were left untouched (the raw book emits signed weights only).

## Independence statement

No cross-team communication occurred. No other team's directory, the critic/results trees,
or any holdout-bearing path was read. All conclusions derive from the frozen IS snapshot via
the evaluator, the authorized tournament documents, and the registry (a shared, authorized
artifact). The registry's public entries (e.g. team-02's pivot precedent) informed process
expectations only, not signal design.
