# Methodology Deep Reference

Twenty methodologies a quant ML researcher must internalize. Each entry: definition, bias addressed, formula/algorithm, implementation gotcha, when NOT to use, authoritative reference.

This is the canonical methodology reference for the `quant-researcher` agent. The main agent file's Methodology Cheatsheet (Section 4) is a 1-2-line summary of each entry; this file is the deep version.

---

## 1. Combinatorial Purged Cross-Validation (CPCV)

**Definition:** Splits T blocks into all C(N,k) train/test combinations; purges training labels overlapping test windows; applies post-test embargo.

**Bias addressed:** Leakage from event-driven labels that span multiple bars; single-path bias of standard walk-forward.

**Algorithm:** For N groups with k test groups, you get φ = C(N,k) × (k/N) backtest paths. The gap (purge window) must equal the maximum label horizon h on **both** sides of the test boundary. Embargo δ ≈ 1% of T (López de Prado convention).

**Gotcha:** For triple-barrier labels with vertical-barrier T_v=24 bars, gap must be ≥24 bars on **both** sides — not just leading. Truncating gap to test-leading edge alone leaks future returns into training. With multi-symbol pooled models, gap = max_h × n_symbols × bars_per_horizon.

**When NOT to use:** Labels are point-in-time (single-bar returns, daily forecasts on daily bars) — overhead unjustified; standard purged k-fold suffices.

**Reference:** López de Prado, *Advances in Financial Machine Learning* (2018), Ch. 7 & 12.

---

## 2. Deflated Sharpe Ratio (DSR)

**Definition:** Sharpe-significance test correcting for N trials, non-normal returns, and finite sample size.

**Bias addressed:** Selection bias — best of N trials produces inflated Sharpe even under the null hypothesis of zero edge.

**Formula:**
```
DSR = Z[(SR̂ − SR_0)·√(T−1) / √(1 − γ̂₃·SR̂ + ((γ̂₄−1)/4)·SR̂²)]
```
where:
- SR_0 = √V[{SR_n}] · ((1−γ)·Z⁻¹(1−1/N) + γ·Z⁻¹(1−1/(Ne)))
- γ ≈ 0.5772 (Euler–Mascheroni)
- γ̂₃ = sample skewness, γ̂₄ = sample kurtosis
- Z⁻¹ = inverse standard-normal CDF

Reject the null at DSR > 0.95.

**Gotcha:** N is *effective independent trials*, not raw hyperparameter combos. Correlated configs collapse N — compute N_eff via PCA on trial returns (count eigenvalues capturing 95% variance).

**When NOT to use:** You ran exactly one prespecified strategy (no selection occurred). DSR is meaningless when N=1.

**Reference:** Bailey & López de Prado (2014), *Journal of Portfolio Management* 40(5).

---

## 3. Probability of Backtest Overfitting (PBO)

**Definition:** The probability that the IS-optimal configuration underperforms the OOS median.

**Bias addressed:** Overfit configs rank high IS but mean-revert OOS — naive backtest selection guarantees the chosen strategy is overfit.

**Algorithm (Combinatorially Symmetric CV / CSCV):** Split T×N matrix of returns (T time, N strategies) into S even submatrices. For each of C(S, S/2) train/test splits, compute:
```
λ = log(ω/(1−ω))   where ω = OOS-rank of IS-best / (N+1)
PBO = P[λ < 0]
```

**Threshold:**
- PBO > 0.5 → strategy is curve-fit (no better than random selection)
- Production deploys typically demand PBO < 0.2

**Gotcha:** N = number of *configurations tested*, including those discarded mid-research. Failing to log abandoned configs underestimates PBO. Symmetric splitting is essential — non-symmetric splits bias the rank distribution.

**When NOT to use:** N < ~20. Distribution of λ too sparse to be informative.

**Reference:** Bailey, Borwein, López de Prado, Zhu (2017), *Journal of Computational Finance* 20(4).

---

## 4. Triple-Barrier Labeling

**Definition:** Label = sign of first barrier hit among {upper profit-take, lower stop-loss, vertical timeout}.

**Bias addressed:** Fixed-horizon returns ignore path; binary direction labels lose magnitude information; barriers respect realistic exit conditions.

**Algorithm:**
- Profit-take: PT = +k_up · σ_t
- Stop-loss: SL = −k_dn · σ_t
- Vertical (timeout): T_v = N bars
- σ_t = rolling vol forecast (must be past-only)
- Label ∈ {−1, 0, +1} = {SL hit, T_v expiry, PT hit}

**Gotcha:** σ_t MUST be computed using only past data (e.g., EWMA on prior returns). Using sample std over the labeling window is **look-ahead** and inflates Sharpe ~2x. Trend-following needs k_up = k_dn; mean-reversion benefits from asymmetric barriers (smaller k_dn, larger k_up).

**When NOT to use:** Strategy holds to a fixed deterministic horizon (e.g., month-end rebalance) — use directional return at horizon instead.

**Reference:** López de Prado, AFML, Ch. 3.

---

## 5. Meta-Labeling

**Definition:** Primary model predicts direction (side); secondary binary classifier predicts whether to take the trade and how much.

**Bias addressed:** Conflating direction skill with execution/sizing skill; primary precision/recall locked at one threshold.

**Algorithm:**
1. Train M1 (direction model) → side ŝ ∈ {−1, +1}
2. Construct meta-labels: y_meta = 1 if M1 was right (post-triple-barrier outcome agrees with ŝ), else 0
3. Train M2 (binary classifier) on (features ∪ ŝ) → P(M1 correct)
4. Bet size ∝ P(correct) − 0.5

**Gotcha:** Meta-labels are only defined where M1 *traded*. You cannot meta-label `0`-decisions. M2 is trained on M1's filtered subset; it must be tested on the same filter (no out-of-distribution evaluation on samples where M1 abstained).

**When NOT to use:** M1 is already calibrated and well-sized — meta-labeling adds variance without payoff.

**Reference:** López de Prado, AFML, Ch. 3.

---

## 6. Fractional Differentiation

**Definition:** Difference series by real d ∈ (0, 1) preserving long memory while achieving stationarity.

**Bias addressed:** Integer differencing (returns) erases all level memory; raw prices are non-stationary so models extrapolate badly.

**Algorithm:**
```
(1−L)^d x_t = Σ ω_k · x_{t−k}
ω_k = ω_{k−1} · (−(d−k+1)/k)
```
Choose d* = min{d : ADF(diff_d(x)) < critical_value(95%)}. Typically d* ∈ [0.3, 0.6].

**Gotcha:** Use *fixed-width window* (FFD), not expanding — expanding window introduces non-stationarity in the weights themselves. Truncate weights at |ω_k| < τ (e.g., 1e-5).

**When NOT to use:** Already-stationary features (RSI, z-scores, log-returns) — d=0 is correct.

**Reference:** López de Prado, AFML, Ch. 5; Hosking (1981), "Fractional Differencing."

---

## 7. Sample Weighting by Uniqueness / Concurrency

**Definition:** Reweight training samples by 1 / number of overlapping label horizons at that bar.

**Bias addressed:** Overlapping labels (e.g., triple-barrier holding 1–24 bars) violate IID assumption; concurrent labels triple-count the same return shock.

**Formula:**
```
c_t = #{i : t ∈ [t_i, t_i + h_i]}
ū_i = (1 / (t_i + h_i − t_i)) · Σ_{t ∈ label} 1/c_t
weight w_i ∝ ū_i
```
Sequential bootstrap (López de Prado AFML Ch. 4) extends this for resampling.

**Gotcha:** CV purging is a separate concern — both must apply. Forgetting weights inflates apparent feature importance for any feature concentrated in clustered events (e.g., volatility-spike features fire only during clusters).

**When NOT to use:** Labels are non-overlapping by construction (per-bar returns, daily forecasts on daily bars).

**Reference:** López de Prado, AFML, Ch. 4.

---

## 8. Hierarchical Risk Parity (HRP)

**Definition:** Cluster-based portfolio weights using only correlation distances — no covariance matrix inversion.

**Bias addressed:** Markowitz instability — small noise in Σ produces wild weight swings (condition number explodes when N ≈ T).

**Algorithm:**
1. Distance d_ij = √(0.5 · (1 − ρ_ij))
2. Hierarchical agglomerative clustering → linkage matrix
3. Quasi-diagonalize Σ via cluster ordering
4. Recursive bisection: at each split, allocate inverse-variance between two cluster halves

**Gotcha:** Linkage method matters (`single` vs `ward`). Single linkage is the LdP default but is vulnerable to chaining; `ward` is more stable for small N. Distance metric must satisfy triangle inequality.

**When NOT to use:** N is small (≤5) and Σ is well-conditioned — full mean-variance is fine and provides cleaner closed-form solutions.

**Reference:** López de Prado (2016), *Journal of Portfolio Management* 42(4).

---

## 9. Multiple Testing Correction

**Definition:** Adjust significance threshold when conducting M independent tests.

**Bias addressed:** P(at least one false positive | M tests at α=0.05) = 1 − 0.95^M ≈ 0.99 at M=100.

**Formulas:**
- **Bonferroni:** α' = α / M (FWER control, conservative)
- **Benjamini–Hochberg FDR:** Rank p-values; reject p_(k) ≤ k · α / M (FDR control, more powerful)
- **Bailey-LdP Sharpe haircut:**
  ```
  SR_threshold = SR_naive · √(1 + (γ−1) · log M / √log log M)
  ```

**Gotcha:** M = trials *attempted*, not retained. Researchers' "I only tried 5" is rarely true — count grid points, prior projects, papers' citing factors. For Sharpe, 100 trials at T=252 require observed SR ≈ 1.2 to clear DSR (vs 0.5 naive).

**When NOT to use:** Single hypothesis declared in advance and pre-registered.

**Reference:** Benjamini & Hochberg (1995); Harvey, Liu, Zhu (2016) "...and the Cross-Section of Expected Returns," *RFS* 29(1).

---

## 10. Walk-Forward Analysis

**Definition:** Sequentially refit on past, evaluate on next out-of-sample window.

**Bias addressed:** Single-path bias — only one realized OOS sequence; CPCV is the multi-path generalization.

**Variants:**
- **Anchored / expanding:** train on [0, t], test on (t, t+h]
- **Rolling:** train on [t−w, t], test on (t, t+h]

**Gotcha:** Rolling window discards regime memory — fails on slow-changing factors. Expanding accumulates regime contamination — fails after regime breaks. For low-frequency strategies (daily+, including 8h crypto), expanding usually wins because parameter stability dominates regime cost.

**When NOT to use:** Concept drift is rapid (HFT order-book features) — CPCV better, or rolling with short w.

**Reference:** Pardo (2008), *The Evaluation and Optimization of Trading Strategies*; LdP AFML Ch. 11.

---

## 11. Combinatorial Symmetric Cross-Validation (CSCV)

**Definition:** Symmetric splitting algorithm underlying PBO computation.

**Bias addressed:** Asymmetric splits in vanilla CV bias the rank distribution of "best" config.

**Algorithm:** Split returns matrix into S equal time-blocks (S even, typically 16). For each of C(S, S/2) selections, half = train, half = test. Track IS-rank vs OOS-rank of each strategy. Symmetry guarantees train and test have identical statistical structure under H0.

**Gotcha:** S too small → too few combinations (S=8 gives 70 paths, noisy PBO); S too large → blocks too short to estimate meaningful Sharpe per block. S=16 is standard.

**When NOT to use:** You're not computing PBO. For OOS estimation alone, CPCV is more direct.

**Reference:** Bailey, Borwein, LdP, Zhu (2017).

---

## 12. Feature Importance — MDI, MDA, SFI

**Definition:**
- **MDI** (Mean Decrease Impurity) = in-tree impurity reduction averaged across the forest
- **MDA** (Mean Decrease Accuracy) = OOS accuracy drop after permuting one feature
- **SFI** (Single Feature Importance) = OOS performance of a model trained on feature j alone

**Bias addressed:** MDI is in-sample, biased toward high-cardinality features, and **catastrophically misleading with correlated features** — splits importance arbitrarily across the cluster, so neither member appears important.

**Algorithm (MDA):** Compute baseline OOS score; permute feature j across the test set; loss in score = importance_j. SFI: train model on feature j alone, score OOS.

**Gotcha:** Always cluster features by correlation (e.g., agglomerative clustering on |ρ|) and report cluster-level importance, not feature-level. MDA on a CV split must apply CPCV purging or it leaks.

**When NOT to use:** Features are uncorrelated and you want speed → MDI is fine.

**Reference:** LdP AFML Ch. 8; Strobl et al. (2007), "Bias in random forest variable importance measures."

---

## 13. Structural Breaks Detection

**Definition:** Tests for parameter discontinuities in time-series models.

**Bias addressed:** Models trained across regime breaks fit a chimera of two distributions; backtest looks fine in-sample because both regimes are represented.

**Tests:**
- **Chow** (known break date): F = ((SSR_pooled − SSR_1 − SSR_2) / k) / ((SSR_1+SSR_2) / (T−2k))
- **CUSUM:** cumulative recursive residuals; alarm on boundary cross
- **Bai-Perron:** multiple unknown breaks via dynamic programming
- **SADF (LdP):** supremum ADF for bubble detection

**Gotcha:** Crypto regime breaks are almost continuous (BTC dominance shifts, leverage cycles). Detection rarely actionable in real-time — by the time CUSUM fires, the regime has already shifted. Use as a *retrospective filter* on training data, not a live trading signal.

**When NOT to use:** Sample is short (<200 obs) — power is too low to detect anything.

**Reference:** Andrews (1993); LdP AFML Ch. 17.

---

## 14. Triple-Fitness (Held-Out OOS Protocol)

**Definition:** Three disjoint splits — train, validation (hyperparameter tuning), final test (researcher has *never* seen).

**Bias addressed:** Researcher degrees of freedom — every glance at OOS leaks bias into the next decision.

**Protocol:**
1. Lock final test window before any analysis
2. Run final evaluation exactly *once*
3. If it fails, the strategy is discarded — not retuned
4. Pre-register configs

**Gotcha:** Most researchers fail this — they tweak after seeing OOS. The honest mitigation is *adversarial review*: a colleague holds the test set and runs the final eval; researcher cannot trigger reruns.

**When NOT to use:** You have <2 years of data — the final test window steals too much training mass; use CPCV/DSR instead.

**Reference:** Harvey & Liu (2014); LdP AFML Ch. 11–12.

---

## 15. Kelly Criterion / Fractional Kelly

**Definition:** Bet fraction maximizing E[log(wealth)].

**Bias addressed:** Linear position sizing leaves geometric growth on the table; full Kelly over-bets when edge is uncertain.

**Formula:**
- Discrete: f* = p − q/b = (bp − q) / b, where p = win prob, q = 1 − p, b = win/loss ratio
- Continuous (Gaussian returns): f* = μ / σ² ≈ Sharpe / σ
- Half-Kelly: f = 0.5 · f* → ~75% of max growth, ~50% drawdown

**Gotcha:** μ and σ are *estimates with error*. If true f* = 0.10 but you estimate 0.20, full Kelly bets twice the optimum and drawdowns balloon. Sharpe estimation error has σ_SR ≈ √(1/T) → fractional Kelly is robustness, not preference.

**When NOT to use:** Returns have heavy tails or skew you can't characterize — log-utility breaks down; cap at quarter-Kelly or use vol-targeting instead.

**Reference:** Kelly (1956); Thorp (2006), "The Kelly Criterion in Blackjack..."; MacLean, Thorp, Ziemba (2010), *The Kelly Capital Growth Investment Criterion*.

---

## 16. Variance Targeting / Vol Scaling

**Definition:** Scale position size by σ_target / σ̂_t to maintain constant ex-ante portfolio volatility.

**Bias addressed:** Fixed notional positions inherit market vol regime — equity curve dominated by vol clusters.

**Formula:**
```
w_t = σ_target / σ̂_t
σ̂_t = ex-ante forecast (EWMA λ=0.94, GARCH, or rolling realized)
σ_target_annual = σ_target_daily · √252
```

**Gotcha:** Ex-post vol scaling (using σ over the test window) is forward-looking — a backtest favorite that vanishes live. **Always use lagged vol forecast.** Also: vol scaling improves Sharpe for momentum (negative vol-Sharpe correlation in trend strategies) but hurts mean-reversion.

**When NOT to use:** Short time series where σ̂ is noisier than position itself — vol scaling adds variance.

**Reference:** Moreira & Muir (2017), "Volatility-Managed Portfolios," *Journal of Finance*.

---

## 17. Information Coefficient (IC) Decay

**Definition:** IC = corr(forecast, realized return) across cross-section, computed at each forward horizon h.

**Bias addressed:** Reporting IC at one horizon hides whether signal is fleeting or persistent — turnover/cost analysis breaks without decay info.

**Algorithm:**
- IC(h) = mean over time of cross-sectional Spearman ρ between f_t and r_{t→t+h}
- Half-life h* = horizon where IC(h*) = 0.5 · IC(0)
- Fit decay = IC(0) · exp(−h / τ); τ = decay constant

**Gotcha:** Daily Spearman IC has σ_IC ≈ 1/√N_cross — for N=20 names, single-day IC is noise (±0.22 just from sampling). Report rolling IC over time and ICIR = mean(IC) / std(IC). IC > 0.05 sustained is institutional-grade.

**When NOT to use:** Sparse cross-section (N < 10) or single-asset signals — use direct return-based stats.

**Reference:** Grinold & Kahn (2000), *Active Portfolio Management*, Ch. 4.

---

## 18. Look-Ahead / Time-Travel Bias

**Definition:** Using information unavailable at decision time t in a feature, label, or evaluation at t.

**Bias addressed:** Classic — produces nonexistent edge in backtest.

**Concrete examples:**
1. **Centered moving averages** (uses future bars)
2. **Z-score using full-sample mean/std** (sample stats include future)
3. **Resampling with `closed='left'` but joining on bar-close timestamp** (off-by-one)
4. **Volatility for triple-barrier σ_t computed over the labeling window** (the labels know their own vol)
5. **Survivor-screened universes** (the screen is future-conditional)
6. **Rebased-to-100 plots starting at any post-data-end date**
7. **On-chain features without publication-lag** (block time ≠ knowable time)

**Gotcha:** Any pandas `.rolling().mean().shift(0)` is suspect — should be `.shift(1)` for trade decision. Always ask "could I have computed this feature using only data with timestamp < t?"

**When NOT to use:** Never. Always test by replaying historical data tick-by-tick or bar-by-bar.

**Reference:** LdP AFML Ch. 7; Bailey et al. (2014), "Pseudo-Mathematics and Financial Charlatanism," *Notices of AMS*.

---

## 19. Survivorship Bias

**Definition:** Universe restricted to assets that survived to end-of-sample, omitting delisted/defunct assets.

**Bias addressed:** Inflates returns (survivors > random), deflates vol, kills tail risk. In crypto: ~30% of 2021's top-100 are now <1% of original cap — your "BTC, ETH, SOL" universe is post-hoc.

**Mitigation:** Rebuild universe at each rebalance from *that-date's* listing. Binance's `delisted/` archive on data.binance.vision contains the dead. Backfill price = NaN after delist date; do not exclude from universe pre-delist.

**Gotcha:** Crypto-specific — exchange listings come and go faster than equity. Coins delisted from Binance may continue trading elsewhere; using only Binance data understates true universe and *adds* survivorship via exchange selection.

**When NOT to use:** No reason not to control for it; absence of mitigation is itself a methodology error.

**Reference:** Brown, Goetzmann, Ibbotson, Ross (1992), "Survivorship Bias in Performance Studies," *Review of Financial Studies*; Elton, Gruber, Blake (1996).

---

## 20. Selection Bias / p-Hacking — Harvey & Liu Threshold

**Definition:** Reporting only successful strategies after silent multiple testing.

**Bias addressed:** Published factor zoo has ~400 "significant" factors; most are noise.

**Threshold:** Harvey, Liu, Zhu (2016) — adjusting for ~315 published candidates and unpublished trials, a new factor needs **t-stat > 3.0** (not the traditional 2.0). Equivalent OOS Sharpe (10 yrs daily) ≈ 0.95 vs naive 0.63.

**Implementation:** Compute Bonferroni adjustment t_threshold = Φ⁻¹(1 − 0.025 / M); BH-FDR for power. For factors with credible economic story, M can be smaller than literal trial count if pre-registration is credible.

**Gotcha:** "I had a story first, then tested it" is rarely true — researchers iterate. Pre-registration logs are the only honest evidence. In iterative research, bake in a 2x trial inflation factor.

**When NOT to use:** Single hypothesis derived from non-data theory (rare).

**Reference:** Harvey, Liu, Zhu (2016), *Review of Financial Studies* 29(1); Harvey & Liu (2020), "False (and Missed) Discoveries in Financial Economics."

---

## Tier-2 Methodologies (Mention Only)

Worth knowing exist but not fully detailed here:

- **De-noising correlation matrices** (Marchenko-Pastur clipping for principal-component-based covariance regularization)
- **Bagged classifier ensembles** for label uncertainty
- **Hurst exponent** for trend persistence regime detection
- **Bekaert-Hodrick small-sample SR test** (heavy tails)
- **Reality Check / Superior Predictive Ability test** (White 2000; Hansen 2005) — alternatives to DSR for strategy-set comparison
- **Conformal prediction** for calibrated forecast intervals
- **SHAP values** for model interpretability (with multicollinearity caveat from §12)

---

## Cross-References

- Methodology #1, #11 → cited in main agent §2 (Spine — rung 2)
- Methodology #2, #3, #9, #20 → cited in main agent §2 (Spine — rung 3)
- Methodology #14 → cited in main agent §2 (Spine — rung 5)
- Methodology #4, #5, #7 → cited in main agent §3 (Project Mode, labeling)
- Methodology #12 → cited in main agent §3 (Feature importance) and §7 (Decision flow: feature selection)
- Methodology #15, #16 → cited in main agent §3 (Risk layers R2)
- Methodology #18, #19 → cited in main agent §2 (Spine — rung 1) and §9 (Anti-patterns)
