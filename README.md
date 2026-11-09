# Unwinding the Yen

Replication files for the essay *Unwinding the Yen: What the August 2024 Carry Trade Collapse Reveals About Global Leverage*.

The essay tests whether the market turmoil of 31 July to 5 August 2024 was a forced unwinding of yen-funded carry trades, using public data only:

| Test | Section | Output in `results/` |
|---|---|---|
| Factor-model event study (14 currencies, three dollar factors) | 4.1-4.2, Table 1 | `factor_event_study.csv` |
| Historical benchmarking since 1990 (yen, franc) and 1999 (carry portfolio) | 4.2, Exhibit 2 | `benchmark_summary.txt`, `benchmark_top_episodes.csv` |
| Cross-section of currencies against interest rates, with placebo | 4.3, Exhibit 3 | `cross_section.txt`, `cross_section.csv` |
| VIX response to the S&P 500, 2016-2024 | 4.4 | `vix_regression.txt` |
| 62 Japanese firms: exporters, domestic firms, financials | 4.5, Exhibit 4 | `firm_level.txt`, `firm_level.csv` |
| CFTC yen positioning since 1986 and an exploratory early-warning test | 4.6, 5.2, Exhibit 5 | `cftc_positioning.txt`, `cftc_monthly.csv` |

`results/RESULTS_REPORTED_IN_PAPER.md` lists every number quoted in the essay.

## How to reproduce

You need Python 3.10 or later and an internet connection.

```bash
pip install -r requirements.txt
python src/fetch_data.py      # downloads raw data into data/raw/ (about 2 minutes)
python src/analysis.py        # recomputes every statistic and writes results/
python src/make_exhibits.py   # redraws Exhibits 1-6 into exhibits/
```

## Data

All data are public and were downloaded on 9 November 2026.

* **FRED** (Federal Reserve Bank of St. Louis): Federal Reserve H.10 noon New York exchange rates, the dollar index against advanced foreign economies (DTWEXAFEGS), VIX, S&P 500, Nikkei 225 and OECD short-term interest rates.
* **CFTC** Commitments of Traders, legacy futures-only report, Japanese yen (CME contract 097741).
* **Yahoo Finance** daily adjusted closes for the 62 firms in `data/firm_universe.csv` and the TOPIX ETF (1306.T).

Small files used directly are committed in `data/`: the 2024 daily series behind Exhibit 1, the 2024 CFTC positions, the July 2024 interest rates and the firm list.

## Conventions

* Every exchange rate is converted to the currency's value in US dollars, so a positive return is an appreciation (see Table 2 in the essay).
* Returns are daily log returns. Estimation window: 2 January to 28 June 2024. Event window: 31 July, 1, 2 and 5 August 2024.
* Carry portfolio: long Mexican peso and Brazilian real, short yen and Swiss franc, equal weights, spot returns only.

## Notes

The statistics were first computed during drafting with an independent implementation of the same methods, and the Python code here reproduces them. Small differences in the last decimal place can arise if a data provider revises a series, and Yahoo Finance's adjusted prices can change after later corporate actions.

## Licence

MIT. See `LICENSE`.
