# MN4 Phase B — REVEAL INSTRUCTIONS (each pair reads before revealing)

Phase A is complete: 10 constructions are frozen. You are now authorized for **Phase B** — reveal
YOUR frozen construction on the sealed 2-year holdout. This **OVERRIDES** your Phase-A "IS-only,
zero holdout reads" instruction: you MAY now read the holdout window for this one authorized reveal.

## THE REVEAL — sacred discipline (read twice)
- **Window:** `[2024-07-01, 2026-07-01)`. Holdout ONLY. **Do NOT read past 2026-07-01** (that is
  Stage-3 data — untouchable).
- **Construction:** your **FROZEN byte-exact Phase-A construction** — identical code, features,
  weights, gates. NO changes. NO re-gating. NO threshold adjustment. NO re-fitting. Re-run the
  same object over the holdout window.
- **One look:** this is the SINGLE authorized holdout read for your construction. Whatever the
  numbers are, they STAND. No re-runs, no "let me try a variant," no post-hoc fixes.
- **Token:** spend your `MN4-NN` token by writing a per-token marker file
  `data/mn4_reveal/spend_MN4-NN.json` = `{"token":"MN4-NN","window":"[2024-07-01,2026-07-01)",`
  `"idea":"<your idea name>","result":"PASS|FAIL","holdout_sharpe_2x":<num>,"holdout_maxdd":<num>}`.
  **Do NOT edit the shared `REVEAL-LEDGER.md` directly** — the orchestrator consolidates all 10
  markers into the ledger atomically after the reveals (avoids concurrent-write races). Your
  authorization to read the holdout is this orchestrator directive + the user's Phase-B mandate.

## SCORE vs YOUR FROZEN GATES
Score the holdout against the **SAME gates you pre-registered in Phase A** (the principle-anchored
thresholds in your `briefs-portfolio-mn4/IDEA-NN.md`). Report each gate: realized holdout value vs
threshold vs PASS/FAIL. The verdict is mechanical: **PASS → your construction survives → Stage-3
(paper-trade) eligible**; **FAIL → your construction is closed** (no rescue, no second reveal).

## DELIVERABLE: `diary-portfolio-mn4/REVEAL-NN.md`
Header (construction one-liner + the authorization note + model = Opus 4.8) + the holdout
scorecard:
- Sharpe 1× and 2×-GT, maxDD, annualized return + vol
- **Per-half path:** 2024-H2 / 2025-H1 / 2025-H2 / 2026-H1 (net)
- **Regime buckets:** CRASH / MANIA / CHOP net + β_BTC per bucket
- Realized rolling β_BTC / β_ETH; turnover; cost coverage (2×-GT vs 1×)
- Gate-by-gate verdict table (holdout value vs frozen threshold vs PASS/FAIL)
- **HONEST generalization read:** compare holdout to your IS numbers explicitly — did the edge
  hold, decay, or invert? Did the crash-robustness (if you claimed it) survive? One paragraph,
  no spin.

## REPORT BACK (final message to orchestrator)
The holdout headline (Sharpe 1×/2×-GT, maxDD, β_BTC + crash-bucket β, crash-regime net), the
verdict (PASS/FAIL), whether it generalized (hold vs decay vs invert vs your IS numbers), and the
spend-marker path. **Honest numbers — a FAIL on unseen data is the methodology working, not a
disappointment.**

*— Orchestrator, MN4 Phase B, 2026-07-12. Reveal all 10; one look each; then the Critic reviews
the tournament. The 2-year holdout is being spent here — irreversibly — by user mandate.*
