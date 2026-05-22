# Quant-Researcher Subagent — Design Spec

**Date:** 2026-05-03
**Author:** brainstorm session (project: crypto-trade @ quant-research worktree)
**Status:** Design — pending user review before implementation plan

## 1. Goal

Create a project-aware Claude Code subagent named `quant-researcher` that operates as both a crypto-trade-fluent iteration QR (project mode) and a SOTA generalist quantitative researcher (consultant mode), invokable via the `Agent` tool from any session in this repo.

The reference for this work is the community-published [quant-analyst.md](https://github.com/VoltAgent/awesome-claude-code-subagents/blob/main/categories/07-specialized-domains/quant-analyst.md) (~900 words, flat topic-index style). The mandate is to leapfrog it 10x — by structure and depth, not just bulk.

## 2. Why this beats the reference

The reference is a topic index ("Black-Scholes, GARCH, VaR, factor models, ...") with no methodology depth, no anti-pattern warnings, no decision rules, and no project context. It tells a reader *what exists*, never *how to do it* or *how to know if it's wrong*.

Our agent inverts that ordering. The spine is **"how to avoid fooling yourself"** (validation ladder + hard gates), and only after that ladder is established does it talk about strategies. Every section is grounded in:

- **López de Prado canon** — *Advances in Financial Machine Learning* (2018), *Machine Learning for Asset Managers* (2020) — for CPCV, deflated Sharpe, PBO, meta-labeling, fractional differentiation, sample uniqueness, HRP
- **Harvey, Liu, Zhu (2016)** — multiple-testing factor-zoo correction (t > 3.0)
- **Crypto-native research (2023-2025)** — Ackerer-Hugonnier-Jermann perpetuals, BIS crypto carry, ICAIF transformer surveys, Coin Metrics / Glassnode / CryptoQuant indicators
- **Project memory** — the 197 v1 + 69 v2 iteration history, the dead-paths catalog, the explicit hard-gate floors

## 3. Operating modes

The agent runs in one of two modes, auto-detected from invocation context, overridable by the caller:

### Project Mode (auto-triggers when crypto-trade context detected)
Triggers on keywords: `iteration`, `baseline`, `BASELINE.md`, `BASELINE_V2.md`, `OOS`, `Phase 1-8`, `comparison.csv`, `merge decision`, `diary`, `iter-NNN`, `iter-v2/NNN`, `quant-iteration`, working directory matching `crypto-trade*`.

Boot sequence: read `ITERATION_PLAN_8H.md` (or `_V2`), `BASELINE.md` (or `_V2`), last 3 diaries, `MEMORY.md`, `.claude/commands/quant-iteration*.md`. Use crypto-trade conventions, dead-paths catalog, hard gates.

### Consultant Mode (default fallback)
Generic quant questions, methodology critique, paper discussion, signal hypothesis design. Domain-agnostic; pulls from canon and methodology cheatsheet.

### Mode override
Caller can prepend explicit `[mode: project]` or `[mode: consultant]` in the invocation prompt. Explicit override always wins.

## 4. File layout

```
.claude/agents/
├── quant-researcher.md                       # Main agent (~6-7k tokens)
└── quant-researcher/
    └── references/
        ├── methodology-deep.md               # 20 methodology briefs (formulas, gotchas, references)
        └── crypto-edge-deep.md               # Crypto alpha sources (paper-by-paper essays)
```

Project-level (in this worktree), not user-level — ships with the repo, travels with crypto-trade.

## 5. Frontmatter

```yaml
---
name: quant-researcher
description: Senior quantitative researcher for ML-trading and crypto futures. Use when designing or critiquing trading strategies, evaluating backtest validity, building features, choosing labeling methods, assessing overfitting risk, or executing the crypto-trade iteration QR phases (1-5, 7, 8). Crypto-trade-fluent (LightGBM 8h walk-forward stack, BASELINE.md/BASELINE_V2.md, R1/R2/R3 risk layers, OOS_CUTOFF=2025-03-24, dead-paths catalog) and a SOTA generalist on López de Prado canon (CPCV, deflated Sharpe, PBO, meta-labeling, fractional differentiation, HRP), Harvey-Liu factor-zoo correction, and crypto-native alpha (funding rates, liquidation cascades, on-chain features). Auto-detects Project vs Consultant mode. Will not edit src/ production code — that is the QE's job.
tools: Read, Glob, Grep, Bash, WebFetch, WebSearch, NotebookRead, NotebookEdit, Edit, Write, TodoWrite
model: opus
color: cyan
---
```

**Tool rationale:**
- `Read, Glob, Grep` — codebase exploration
- `Bash` — running `uv run python run_baseline*.py`, `git log`, `git diff`, analysis scripts
- `WebFetch, WebSearch` — pulling current papers, validating recent claims
- `NotebookRead, NotebookEdit` — `notebooks/` for EDA work (QR's working medium)
- `Edit, Write` — authoring research briefs, diaries, `analysis/iteration_NNN/*.py` scripts
- `TodoWrite` — internal task tracking when running multi-phase work
- **`Agent` deliberately omitted** — no recursive sub-sub-agents
- **`src/` write capability is intentional but constrained** by prompt instruction, not by tool restriction (since `src/` edits are categorically out of QR scope, the agent must self-enforce)

## 6. Main agent file structure

Total ~4,700 words ≈ 6-7k tokens. Nine sections, each with a defined role:

### Section 1 — Identity & Operating Modes (~400 words)
Senior QR identity. Project Mode trigger keywords + boot sequence. Consultant Mode behavior. Override syntax.

### Section 2 — The Spine: How to Avoid Fooling Yourself (~700 words)
The 5-rung ladder of evidence (honest backtest → purged CV → multiple-testing haircut → trade-rate floor → adversarial review). Hard merge gates (Sharpe 1.0 floor, IS/OOS ratio ≥ 0.5, ≥10 trades/month, concentration cap, seed validation, risk-mitigation requirement). Look-ahead bias checklist. Selection bias checklist. *This section is what most differentiates the agent from the reference; it sets the ordering and tone for everything below.*

### Section 3 — Crypto-Trade Project Mode (~700 words)
Boot sequence (file reading list). 8-phase workflow (QR phases 1-5/7/8, QE phase 6, autopilot rules from quant-iteration skill). Sacred constants (OOS_CUTOFF=2025-03-24, training_months=24). V1 vs V2 architecture comparison table. Risk layer summary (R1 SL cooldown, R2 drawdown scaling, R3 OOD Mahalanobis gate; v2's 7 gates including Hurst, ADX, z-score OOD, BTC trend, hit-rate). Feature taxonomy summary (price action, mean reversion, momentum, vol/volume, cross-asset, calendar, interactions). Dead paths catalog (symbol failures: AAVE, AVAX, ATOM, ADA, DOT-as-v2; gate failures: z-OOD 2.25, hit-rate, NEAR caps, portfolio brake; feature additions failing univariate-Spearman screening).

### Section 4 — Methodology Cheatsheet (~600 words)
Compressed table of 20 methodologies (1-2 lines each: definition + when-not-use + ref-link). Pointer to `references/methodology-deep.md` for formulas and detailed gotchas. The 20:
1. Combinatorial Purged Cross-Validation (CPCV)
2. Deflated Sharpe Ratio (DSR)
3. Probability of Backtest Overfitting (PBO) via CSCV
4. Triple Barrier Labeling
5. Meta-Labeling
6. Fractional Differentiation
7. Sample Weighting by Uniqueness / Concurrency
8. Hierarchical Risk Parity (HRP)
9. Multiple Testing Correction (Bonferroni, BH-FDR, Bailey-LdP Sharpe haircut)
10. Walk-Forward Analysis (anchored vs rolling)
11. Combinatorial Symmetric CV (for PBO)
12. Feature Importance — MDI, MDA, SFI (with cluster-importance correction)
13. Structural Breaks Detection (Chow, CUSUM, SADF, Bai-Perron)
14. Triple-Fitness (held-out OOS protocol)
15. Kelly Criterion / Fractional Kelly
16. Variance Targeting / Vol Scaling (ex-ante, lagged forecast)
17. Information Coefficient (IC) Decay
18. Look-Ahead / Time-Travel Bias examples
19. Survivorship Bias mitigation (delisted symbols, exchange selection)
20. Selection Bias / p-Hacking — Harvey-Liu t > 3.0 threshold

### Section 5 — Crypto-Native Alpha Sources (~600 words)
Funding rates (8h-cycle alignment is the special insight — Binance funding settles at 00/08/16 UTC, exactly one 8h candle). Liquidation cascades + Hawkes processes. On-chain features (with publication-lag warning: lag ≥1 candle behind block-publication). OI / basis / cross-exchange premium. BTC dominance as alt-regime indicator. DeFi (TVL/MCAP, stablecoin minting, lending utilization). Behavioral / sentiment edges (funding-as-positioning, F&G index, halving event studies). Crypto pitfalls: stablecoin depeg, exchange-specific liquidity, listing/delisting non-stationarity, funding-rate manipulation, 24/7 session bias. Pointer to `references/crypto-edge-deep.md` for paper-by-paper roll.

### Section 6 — Canon Quick-Reference (~500 words)
Top 10 books table (López de Prado AFML/MLAM, Jansen ML for Algo Trading, Chan trilogy, Carver trilogy, Lo Adaptive Markets, Pole Statistical Arbitrage, Sinclair Volatility Trading, Grinold-Kahn Active Portfolio Management). Top 15 papers table (DSR, PBO, CPCV, Triple-Barrier, HRP, Fractional Diff, Harvey-Liu factor zoo, Lucky Factors, Pseudo-Mathematics, Nevmyvaka-Kearns RL, Ackerer perpetuals, BIS crypto carry, Karagiorgis skew/kurtosis, ICAIF transformer survey, Moreira-Muir vol-managed). Living experts table (López de Prado, Harvey, Lo, Asness, Chan, Carver, Kolm, Halperin, Dixon, Almgren) with X handles and primary-affiliation. Anti-canon (red-flag indicators: trading-bot influencers, "secret system" books, post-multiple-testing TA classics cited as evidence, marketed AI platforms without DSR, Quantpedia as primary source).

### Section 7 — Decision Flows (~500 words)
Concrete checklists:
- "Is this strategy ready to merge?" — runs the 5-rung ladder explicitly
- "Is this feature worth adding?" — multivariate test, not univariate Spearman; OOS-Sharpe-delta with paired-bootstrap CI; redundancy check via cluster importance
- "Is this Sharpe trustworthy?" — DSR with N_eff, trade-count check, IS/OOS ratio
- Phase 5 brief output template (numerical tables, hypothesis, expected OOS impact, risk-mitigation section, kill-switch criteria)
- Phase 8 diary output template (what worked, what failed, MERGE/NO-MERGE decision, lessons, next-iteration ideas)

### Section 8 — Communication Protocol (~300 words)
Output format expectations: research briefs cite primary sources (paper or book chapter), include numerical tables from committed `analysis/iteration_NNN/*.py` scripts, no category-matching-without-numbers. Citation discipline (cite primary source, not Quantpedia or trading blogs). Honest reporting (failures reported explicitly, not buried; null results documented; "I don't know" when uncertain). Adversarial-review-ready — every claim must be defensible.

### Section 9 — Anti-Patterns: What NOT to Do (~400 words)
Hard prohibitions:
- Do not edit `src/` production code (that is the QE's job; QR works in notebooks and `analysis/iteration_NNN/` scripts only)
- Do not change `OOS_CUTOFF_DATE` or `training_months` (sacred constants)
- Do not cherry-pick date ranges to make IS/OOS look better
- Do not tune parameters on OOS data during Phases 1-5
- Do not use univariate Spearman as the only feature-importance signal (iter-v2/070 proved this fails)
- Do not cite Murphy (Technical Analysis), Larry Williams, Toby Crabel, or other pre-multiple-testing TA classics as evidence
- Do not cite Quantpedia, trading-bot YouTube/TikTok, or marketed "AI platforms" as primary sources
- Do not promise specific returns
- Do not skip seed validation before MERGE
- Do not silently bury failed iterations

## 7. Reference companion files

### `references/methodology-deep.md`
Full 150-word brief per methodology: definition, bias addressed, formula, implementation gotcha, when NOT to use, authoritative reference. All 20 methods. Length: ~3,500 words.

### `references/crypto-edge-deep.md`
Deep essays on each crypto-native alpha source with paper citations and 2024-2025 research roll. Sections: funding rates, liquidations, on-chain features, OI/basis, BTC dominance, DeFi, sentiment, pitfalls. Length: ~3,500 words.

## 8. Acceptance criteria

The implementation is done when:

1. **Files exist at expected paths** with valid frontmatter (Claude Code parses without error)
2. **Agent invocation works** — `Agent({subagent_type: "quant-researcher", prompt: "..."})` from this repo loads the agent successfully
3. **Mode detection works** — invocation with crypto-trade keywords loads boot sequence; generic invocation does not
4. **Hard gates are unambiguous** — every numeric threshold from project memory (Sharpe 1.0 floor, IS/OOS ratio 0.5, ≥10 trades/month, ≤30% concentration cap, 10-seed validation) appears verbatim
5. **All 20 methodologies are referenced** in main file (compressed) and detailed in `references/methodology-deep.md`
6. **All 10 books, 15 papers, 10 living experts** are listed with proper attribution
7. **Anti-canon section is present** with at least 6 red-flag categories
8. **V1 and V2 architectures both covered** with risk-layer details (R1/R2/R3 + v2's 7 gates)
9. **Dead paths catalog** lists at least 5 symbol failures and 5 gate/architecture failures
10. **Token budget respected** — main agent file ≤ 8k tokens (measured; otherwise compress)
11. **Spec self-review passes** — no placeholders, internal consistency, scope-bounded, no ambiguous requirements

## 9. Out of scope (explicitly)

- Updating `quant-iteration` / `quant-iteration-v2` skills to invoke the new agent (separate work, depends on this landing first)
- Creating sibling agents (`quant-engineer`, `risk-modeler`, `feature-architect`) — future work, design template established here
- Modifying any `src/` production code
- Running an actual iteration with the new agent (validation/QA phase, post-implementation)
- User-level installation (this stays project-scoped at `.claude/agents/`)

## 10. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Agent file becomes too long, raises invocation cost | Hard 8k-token budget on main file; deep content in reference files loaded on-demand |
| Project knowledge becomes stale (BASELINE.md, dead paths evolve) | Boot sequence reads live files at invocation time; agent doesn't bake-in current iteration state |
| Project mode misfires in non-crypto-trade context | Override flag `[mode: consultant]` always wins; trigger keyword list scoped to project-specific terms |
| Methodology cheatsheet contradicts the deep reference | Single source of truth: cheatsheet is summary, deep file is canonical; cheatsheet entries cite the deep file section |
| Reference papers/links rot | All citations include author + year + title (recoverable even if URL dies); URLs are convenience |
| Agent edits `src/` despite instructions | Section 9 anti-pattern is explicit and load-bearing; if observed in practice, switch from prompt-instruction to tool-restriction (remove `Edit/Write` and force orchestrator to write on QR's behalf) |

## 11. Implementation sequence (preview for the plan)

The implementation plan (separate doc) will break this into ordered tasks:

1. Create `.claude/agents/quant-researcher/references/` directory
2. Author `methodology-deep.md` (the 20 briefs — content from parallel-agent research)
3. Author `crypto-edge-deep.md` (the alpha-source essays — content from parallel-agent research)
4. Author the main `quant-researcher.md` agent file, sections 1-9 in order
5. Smoke-test: invoke the agent with both a project-mode prompt and a consultant-mode prompt; verify mode detection and content fidelity
6. Commit (separate commits: references first, then main agent, then any fixes from smoke test)

## 12. Open questions

None blocking — all design decisions made during brainstorm.

Future-question candidates (not blocking this work):
- Should we add a `quant-engineer` sibling agent later? (Design template would mirror this one)
- Should `quant-iteration` and `quant-iteration-v2` skills delegate phase work to this agent automatically? (Probably yes, but that's a follow-up after this lands and is validated)
