# Team 07 two-tape incumbent port provenance

This directory is a new Top-40 V3 port of the audited V2 candidate. It is not a
byte-identical copy: the required runtime seed changed from `20260801` to
`20260718`, and the V2 organizer score-hook import was replaced by the adjacent
exact identity hook. The two-tape durability signal, active variant, schedule,
portfolio construction, parameters, and no-control risk policy are otherwise
preserved.

V2 lineage:

- Commit: `be5bd81b68b8da424b1e8aae531183446eeaa555`
- Candidate: `t07-two-tape-rank-durability-v1-base`
- Family: `t07-two-tape-rank-durability-v1`
- `strategy.py` SHA-256: `bb5b45c3c0de5846463bc8b3164a5921a319ee5a17663ad93b3b6cc7e2224506`
- `candidate_variant.py` SHA-256: `7aaed418826d38667e44ff26bdd73a4658bb329b02e0f379ab46218cdc8f80c8`
- `frozen_config.json` SHA-256: `10859e9a405ecccccab3712eb0db362f060a8cc0e8fbc473817c029ac3b40bb5`
- `risk_policy.json` SHA-256: `d3b918f600f2b548b6a2c8dc44a3077b7b34d8c911ecc6e9c776eada8ad77b6c`
- V2 source-bundle SHA-256: `119981c805c575a42b7fb2bf36885e4c2310311e848871cb5676a3eea887439b`
- V2 executable-source manifest: `tournament/top40-v2/teams/team-07/score-adapters/t07-two-tape-rank-durability-v1-base.executable-source-manifest.json`

The V2 result is calibration evidence only. This incumbent receives no V3 pass,
qualification, or nomination by inheritance and must use Team 07's ordinary
journal, trial, and probe budget.
