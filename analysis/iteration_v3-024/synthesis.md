# iter-v3/024 — BTC Funding EDA Synthesis

## Decision Summary

| Gate | Threshold | Observed | PASS? |
|------|-----------|----------|-------|
| Coverage IS window per symbol | >= 80.0% | see coverage CSV | True |
| Max \|IC\| vs 13 V3_FEATURE_COLUMNS (HARD) | < 0.7 | 0.1921 | True |
| Max \|IC\| vs 13 V3_FEATURE_COLUMNS (BRIEF target) | < 0.5 | 0.1921 | True |
| ADF p-value < 0.05 per symbol | structural stationarity | see adf CSV | True |
| Max \|rank-IC\| vs forward returns | >= 0.02 (predictive signal) | 0.0474 | True |

## Per-symbol max |IC| vs 13 V3_FEATURE_COLUMNS

- BCHUSDT: max |IC| = 0.1779
- LDOUSDT: max |IC| = 0.1921
- TRXUSDT: max |IC| = 0.1779

## Files

- analysis/iteration_v3-024/btc_funding_eda_coverage.csv
- analysis/iteration_v3-024/btc_funding_eda_distribution.csv
- analysis/iteration_v3-024/btc_funding_eda_correlation.csv
- analysis/iteration_v3-024/btc_funding_eda_rankic.csv
- analysis/iteration_v3-024/btc_funding_eda_adf.csv

## Verdict

GO — all 5 EDA gates pass; structurally vetted candidate.
