# team-05 · Top-40 V2

Status: `FAMILY_REGISTERED_CORE_V2_INFRA_FAILED_A8_REPLACEMENT_NOT_REGISTERED`

Family: `team05-causal-residual-trend-reversal-v1`  
Base: `team05-crtr-base-v1`

The controlling tournament entrypoint is now
`scripts/top40_v2_tournament_runtime_preload_v7.py` at SHA-256
`8a4ada10176d2606df3f358fc188e21b45153ad9a7270f36908736f03322a3a9`. Its active integration
freeze is commit `c8b917ca49306d5200a4e08848e73ff6f5a18bf3`, SHA-256
`6f77a146e7b414eabd20c5cc9321a95493bb98116dde07ef79d9eb009b6a6f51`. The dispatcher retains
the active Amendment 0006 pure-crypto audit: only certified native crypto coins/tokens may enter;
stablecoins, equities/TradFi, indexes, metals, commodities, and other non-crypto contracts remain
ineligible even if Binance lists a perpetual contract for them.

The family was registered through the organizer lifecycle at `2026-07-16T16:32:53Z`;
`families.jsonl` has that one accepted row. The later v2 core run failed before strategy
initialization at the A5 protocol import boundary and produced no model metric or artifact; its
registration and terminal row remain immutable in `experiments.jsonl`. Frozen A8 commit
`f6003ae687d5a6bf665abb001715b01ea8b10abb` (SHA-256
`08bf194c9ade1f66bf38012210ad8604df61ca467cdad00bd3957aa679ea9bdd`) authorizes one unchanged
replacement. Start with `HANDOFF.md`; do not register `team05-crtr-core-v2-infra-r1` or evaluate until every
prospective Team05 placeholder is materialized, the complete executable-source manifest and
independent semantic review are first-added in the required order, organizer verification passes,
and the A8-bound replacement registration is accepted into the organizer journal.
