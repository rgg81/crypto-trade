# Top-12 V2

This is a fresh, strategy-blind, twelve-team tournament over the causal weekly Top-12 native-
crypto universe. The authoritative contract is `../../TOURNAMENT-CHARTER-TOP12-V2.md`; numerical
policy is in `config.toml`.

```text
development IS (2020-08-03..2023-06-30)
  -> one qualified nominee per lane
  -> sealed confirmation (2023-07-01..2024-06-30)
  -> at most four finalists
  -> sealed historical OOS (2024-07-01..2026-06-30)
  -> atomic result release
```

Non-negotiable rules:

- prior-strategy and cross-team blindness;
- organizer-side collision and prior-OOS-family exclusion without disclosure;
- sixteen accepted trials maximum, thirteen minimum before nomination or retirement;
- trials 9-13 reserved for the five-point local neighborhood;
- every gate conjunctive, with no forced finalist or winner;
- one sealed observation, no repair or retry, in confirmation and historical OOS;
- serial result commands pinned to at most two CPUs.

Organizer commands should use the pinned environment:

```bash
env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  taskset -c 0,1 uv run --frozen python scripts/top12_v2_tournament.py validate --pre-activation
env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  taskset -c 0,1 uv run --frozen python scripts/top12_v2_tournament.py activate
env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  taskset -c 0,1 uv run --frozen python scripts/top12_v2_tournament.py is-run team-01 \
  tournament/top12-v2/teams/team-01/candidates/<candidate-id>/strategy.py \
  --purpose "preregistered evidence cell"
```

After thirteen trials, use `nominate` or `retire`. Once all lanes resolve, `close-is` performs the
sealed confirmation and freezes finalists. `historical-release` consumes and atomically publishes
the two-year OOS.
