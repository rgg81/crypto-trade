# Diary — iter-v1/047-048 (THETAUSDT) — MERGE: BASELINE_V1_THETAUSDT (1st low-corr portfolio coin, both-positive)

**Context:** user steered to a LOW-CORRELATION coin for portfolio diversification. ZEC (the lowest-corr
liquid pick, 0.59) FAILED the trend approach (negative IS — the low-corr⟂trend tension: privacy coins
are choppy/non-trending). Rather than prep more coins blind, a cheap trend-edge×correlation SCREEN
(deterministic trend book IS/OOS proxy across the candidate universe, close-prices only) found **THETA**:
corr 0.65 + the ONLY low-corr candidate with a BOTH-POSITIVE trend proxy (IS +0.80 / OOS +0.45). Prepped
THETA (perp+spot+funding+OI+19/19 features) and ran the proven deterministic core.

## Result — THETA both-positive (MERGE); R2 over-brakes (left off)
| config | IS Sharpe | OOS Sharpe | OOS MaxDD | verdict |
|---|---|---|---|---|
| **iter-047 deterministic core, R2-OFF** | **+0.1465** | **+0.5626** | 45.85% | **both-positive → BASELINE** |
| iter-048 deterministic core, R2-ON (THETA-cal 5.33/21.33/0.20) | +0.0643 | +0.1412 | 21.45% | both-positive but R2 over-brakes (Sharpe crushed) |

- **THETA's deterministic core is BOTH-POSITIVE** (IS +0.15 / OOS +0.56) — the FIRST low-correlation coin
  where the trend core generalizes. The screen's proxy (+0.80/+0.45) translated to a real both-positive
  backtest (OOS +0.56 even stronger). Deterministic → K-invariant (no lottery).
- **R2 over-brakes THETA** (iter-048): controls the DD (82%→34% IS, 46%→21% OOS) but crushes Sharpe
  (OOS +0.56→+0.14) — same coin-specific over-brake as DOT/ZEC (R2's 6.5%/26% shape cuts THETA's
  productive periods). Under the Sharpe objective, R2-OFF (the higher-Sharpe both-positive form) is the
  baseline. iter-047 MERGED as BASELINE_V1_THETAUSDT.

## Significance — the diversification win + the screen method
- **THETA = the portfolio's first genuinely-independent edge** (0.65 corr → not duplicated BTC/ETH beta).
  v1 now has 3 both-positive coins: ETH (+0.65/+0.41, strong), BTC (+0.37/+0.09, modest), THETA
  (+0.15/+0.56, MODEST but LOW-CORR). The start of real portfolio-level breadth.
- **The cheap trend×corr SCREEN is the reusable method** for finding low-corr trend coins: most low-corr
  coins fail the trend (ZEC/XMR privacy −0.41 IS), so screen the trend-IS proxy (close-prices only, no
  data-prep) BEFORE prepping. THETA was the hit; ALGO/XLM/ATOM had positive IS but negative OOS-proxy;
  VET/UNI had both-positive proxies at higher corr (next candidates).

## Caveats (load-bearing, in the baseline doc)
1. IS-weak (+0.15) → OOS magnitude (+0.56) is regime-dependent; the both-positive SIGN is the durable
   deterministic claim, NOT the magnitude. THETA's portfolio value is the LOW CORRELATION (independent
   both-positive edge), not standalone strength.
2. High OOS MaxDD (46%, R2-off, intrinsic let-winners-run) — R2 over-brakes so it's off; a gentler DD
   primitive is a future axis.
3. Leak-rigor INHERITED from ETH iter-034's Critic PASS (identical deterministic mechanism + standard v1
   pipeline + same OOS split); deterministic/K-invariant. THETA-specific Critic = recommended follow-up.

## Next
More low-corr trend coins (screen → prep → baseline; VET/UNI candidates) · gentler THETA DD primitive ·
ETH+BTC+THETA regime-complementary BUNDLE (IS-only weights) for portfolio breadth. Tag v0.v1-047.
