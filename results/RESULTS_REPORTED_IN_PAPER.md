# Numbers reported in the essay (FRED, CFTC and Yahoo Finance data downloaded 9 Nov 2026)
## Factor model (y = a + b F, F = mean EUR,GBP,CAD vs USD; est 2 Jan-28 Jun 2024; event 31 Jul-5 Aug)
JPY +6.57 z7.32 (b .96 R2 .29) | CHF +3.54 z5.73 | MXN -3.51 z-2.36 p.018 | BRL -1.64 z-1.45 p.147 | CARRY -7.63 z-5.98 | AUD -1.33 z-2.34
AFE factor: JPY 5.06/6.55, CHF 2.29/4.24, MXN -4.43/-2.96, BRL -2.76/-2.45, CARRY -7.27/-5.72; EUR-only: JPY 5.83/6.35, CHF 2.78/4.44
## Historical benchmark (rolling 4-day log-return sums; vol-scaled z uses trailing 250-day sd)
JPY since 1990: event +6.57%, 8th largest of 8780 overlapping windows (top 0.09%); 4th largest non-overlapping episode (after Oct-1998 13.97, Oct-2008 9.37, Jun-1998 8.71); vol-scaled z 5.9, 5th non-overlapping (1998-10 7.2, 1998-06 6.2, 2020-03 6.0, 1995-03 6.0)
CARRY since Feb 1999: loss 7.67%, 8th largest non-overlapping (2008-10 20.72, 2020-03 10.25, 2008-12 8.77, 2002-08 8.52, 2015-01 8.37, 2015-08 7.86, 2009-01 7.73); vol-scaled z 5.6, 4th non-overlapping (2008-10 10.3, 2020-03 7.5, 2015-01 6.4); raw top 0.23%
CHF since 1990: +3.73%, 22nd non-overlapping raw; vol-scaled 4.4 6th
## VIX anomaly (daily, Nov 2016-Dec 2024, n=2048 ex 5 Aug): dlogVIX = -0.49 -3.73 r -1.87 min(r,0); R2 .50; se 5.56
5 Aug: S&P -3.04%, VIX close 23.39->38.57 (+15.18pt, +50.0 log pts); predicted +16.5; residual 6.0 se; 5th largest positive residual (2018-02-05 9.7, 2024-12-18 7.0, 2020-03-24 6.1, 2021-01-27 6.1). 31 days with S&P -2.5..-3.5%: median dlogVIX 14.1, max 55.4
## Sequencing
11-30 Jul (before event window): JPY +5.08%, carry -8.23%, F -0.66%; VIX max 18.46 (close). Japan MoF intervened 11 Jul (JPY 3.168trn) and 12 Jul (JPY 2.367trn), Reuters 7 Nov 2024. BoJ hike 31 Jul.
## Cross-section (11 floating non-factor currencies; 3m interbank rate Jul 2024, OECD via FRED IR3TIB01; BRL, INR policy/call rate IRSTCI01)
CAR = 4.09 - 0.690 i; t -5.29 (OLS, n 11); R2 .76; Spearman -.91. Excl JPY,CHF: slope -0.43, t -3.60, n 9, Spearman -.83. AFE factor incl EUR GBP CAD (n 14): slope -0.633 t -4.52 Spearman -.77
Placebo: slope for every rolling 4-day window 2023-24 (n 497, same betas): event window most negative (rank 1/497); median 0.02; next: 2024-06-04 -0.53, 2023-03-15 -0.49
rates: JPY .166 CHF 1.193 SEK 3.585 NOK 4.76 AUD 4.46 NZD 5.55 KRW 3.54 ZAR 8.45 INR 6.75 MXN 11.40 BRL 10.50 (USD 5.31)
## CFTC (legacy futures-only, JPY 097741, 1986-2026)
2 Jul 2024 net -184,223 (-52.7% OI): 2nd largest net short since 1986 (record -188,077 on 26 Jun 2007), 0.1 pct; by %OI larger in Dec 2013 (-60.1%). Net 30 Jul -73,460; 6 Aug -11,354; 13 Aug +23,104
Exploratory (weekly 1993-2023, n 1618): max 4-day yen gain in next 20 days = 1.98 + 0.0065*(net%OI) + 0.033*(trailing 20d yen ret); t 4.51 (non-overlapping n 405: 0.0073 t 2.44) => more net SHORT predicts SMALLER spikes; quintiles mean max4d 1.77 (most short) ... 2.19 (most long); 9 Jul 2024 report: fitted max 4-day gain 1.56% (non-overlapping coefficients) vs actual 6.57%; R2 of full regression 0.027
## Firm level (62 large Tokyo stocks; Yahoo adj close; betas: r = a + b TOPIX(1306) + c yen_t + d yen_t-1, Jan-Jun 2024; event Tokyo 31 Jul-5 Aug, log %)
TOPIX ETF -19.56, Nikkei -20.27
Exporters (30): -22.89 (mb 1.11, yb -0.26), rebound 6 Aug +10.76
Domestic (27): -15.18 (mb .75, yb +.18), rebound +7.10
Financials (5): -30.05 (mb 1.17), rebound +8.27
Dummies: EXP -7.71 (t -4.18), FIN -14.87 (t -5.93) vs DOM; R2 .35 (HC1)
Betas: ret = -8.17 -12.32 mb (t -4.99) +3.72 yb (t 1.98); R2 .36
Both: EXP -3.29 (t -1.69), FIN -10.59 (t -4.96), mb -9.06, yb 2.63 (t 1.29); R2 .47
Beta-implied (mb*-19.56 + yb*6.6): EXP -23.37, DOM -13.41, FIN -22.82
## Table 1 full (CAR % / z): F | AFE | EUR only
JPY 6.57/7.32 | 5.06/6.55 | 5.83/6.35
CHF 3.54/5.73 | 2.29/4.24 | 2.78/4.44
AUD -1.33/-2.34 (p .019) | -3.09/-5.99 | -2.44/-3.71
MXN -3.51/-2.36 (p .018) | -4.43/-2.96 | -4.15/-2.76
BRL -1.64/-1.45 (p .147) | -2.76/-2.45 | -2.38/-2.08
CARRY -7.63/-5.98 | -7.27/-5.72 | -7.57/-5.93
F currencies' raw event-window move: +0.36%
## CFTC extras
Share of weeks followed by a >3% four-day yen rise: most-short quintile 13.0%, most-long quintile 22.8%
Dec 2013 (-60.1% of OI): largest four-day yen rise in following 60 trading days 2.03%
## Reversal and rate repricing
Cross-sectional slope of abnormal returns on rates, 6-9 Aug 2024: +0.432 (corr 0.86); JPY -1.53, MXN +3.30. 6 Aug alone: +0.138
US 2-year Treasury yield: 4.35 (30 Jul) -> 3.89 (5 Aug), -0.46 points; x 2 years = ~0.9% implied yen move (~1.1% if Japanese 2y yields rose 0.1)
