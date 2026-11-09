"""Download the raw data used in the paper into data/raw/.

Sources (all public, no key needed):
  * FRED (Federal Reserve Bank of St. Louis): daily H.10 exchange rates, the AFE
    dollar index, VIX, S&P 500, Nikkei 225, and OECD short-term interest rates.
  * CFTC Public Reporting Environment: Commitments of Traders, legacy
    futures-only report, Japanese yen (CME contract code 097741).
  * Yahoo Finance (via the yfinance package): daily adjusted closes for the
    62 Tokyo-listed stocks in data/firm_universe.csv and the TOPIX ETF (1306.T).

Run from the repository root:   python src/fetch_data.py
"""
import io
import os
import time

import pandas as pd
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")

FRED_DAILY = [
    # value of foreign currency per US dollar (DEX..US) or US dollars per unit (DEXUS..)
    "DEXJPUS", "DEXSZUS", "DEXMXUS", "DEXBZUS", "DEXUSEU", "DEXUSUK", "DEXCAUS",
    "DEXUSAL", "DEXUSNZ", "DEXSDUS", "DEXNOUS", "DEXKOUS", "DEXSFUS", "DEXINUS",
    # broad dollar index against advanced foreign economies
    "DTWEXAFEGS",
    # markets
    "VIXCLS", "SP500", "NIKKEI225",
    # US two-year Treasury yield
    "DGS2",
]
FRED_RATES = [  # OECD 3-month interbank rates; immediate (call) rates for BRL and INR
    "IR3TIB01JPM156N", "IR3TIB01CHM156N", "IR3TIB01SEM156N", "IR3TIB01NOM156N",
    "IR3TIB01AUM156N", "IR3TIB01NZM156N", "IR3TIB01KRM156N", "IR3TIB01ZAM156N",
    "IR3TIB01MXM156N", "IR3TIB01EZM156N", "IR3TIB01GBM156N", "IR3TIB01CAM156N",
    "IR3TIB01USM156N", "IRSTCI01BRM156N", "IRSTCI01INM156N",
]
FRED_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={id}&cosd={start}&coed={end}"
CFTC_URL = ("https://publicreporting.cftc.gov/resource/6dca-aqww.json"
            "?$select=report_date_as_yyyy_mm_dd,noncomm_positions_long_all,"
            "noncomm_positions_short_all,open_interest_all"
            "&$where=cftc_contract_market_code='097741'"
            "&$order=report_date_as_yyyy_mm_dd&$limit=5000")


def fred(series_id, start="1990-01-01", end="2024-12-31"):
    out = os.path.join(RAW, "fred", f"{series_id}.csv")
    if os.path.exists(out):
        return
    r = requests.get(FRED_URL.format(id=series_id, start=start, end=end), timeout=60)
    r.raise_for_status()
    with open(out, "w") as f:
        f.write(r.text)
    time.sleep(0.5)


def cftc():
    out = os.path.join(RAW, "cftc_jpy_legacy.csv")
    if os.path.exists(out):
        return
    r = requests.get(CFTC_URL, timeout=60)
    r.raise_for_status()
    df = pd.DataFrame(r.json())
    df = df.rename(columns={
        "report_date_as_yyyy_mm_dd": "report_date",
        "noncomm_positions_long_all": "noncomm_long",
        "noncomm_positions_short_all": "noncomm_short",
        "open_interest_all": "open_interest",
    })
    df["report_date"] = df["report_date"].str[:10]
    for c in ["noncomm_long", "noncomm_short", "open_interest"]:
        df[c] = df[c].astype(int)
    df["net"] = df["noncomm_long"] - df["noncomm_short"]
    df.to_csv(out, index=False)


def yahoo():
    import yfinance as yf
    uni = pd.read_csv(os.path.join(ROOT, "data", "firm_universe.csv"), dtype={"code": str})
    tickers = [f"{c}.T" for c in uni["code"]] + ["1306.T"]
    for t in tickers:
        out = os.path.join(RAW, "yahoo", f"{t}.csv")
        if os.path.exists(out):
            continue
        h = yf.Ticker(t).history(start="2024-01-01", end="2024-09-01", auto_adjust=False)
        if h.empty:
            print("  no data for", t)
            continue
        d = pd.DataFrame({"date": h.index.tz_localize(None).strftime("%Y-%m-%d"),
                          "adjclose": h["Adj Close"].values})
        d.to_csv(out, index=False)
        time.sleep(0.3)


if __name__ == "__main__":
    for sub in ["fred", "yahoo"]:
        os.makedirs(os.path.join(RAW, sub), exist_ok=True)
    print("FRED daily series ...")
    for s in FRED_DAILY:
        fred(s)
    print("FRED interest rates ...")
    for s in FRED_RATES:
        fred(s, start="2024-04-01", end="2024-07-31")
    print("CFTC ...")
    cftc()
    print("Yahoo Finance ...")
    yahoo()
    print("Done. Raw files are in data/raw/.")
