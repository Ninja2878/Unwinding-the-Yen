"""All statistical results reported in 'Unwinding the Yen'.

Run from the repository root after `python src/fetch_data.py`:

    python src/analysis.py

Each test writes a small results file to results/. The numbers in the paper are
copied from those files. Conventions throughout:

  * Returns are daily log returns, in per cent where reported.
  * A currency's return is the change in its value against the US dollar,
    so a positive number means the currency strengthened.
  * Estimation window: 2 January - 28 June 2024.
    Event window: 31 July, 1, 2 and 5 August 2024 (four trading days).
"""
import math
import os

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
OUT = os.path.join(ROOT, "results")

EST = ("2024-01-02", "2024-06-28")
EVENT = ["2024-07-31", "2024-08-01", "2024-08-02", "2024-08-05"]

# FRED id, sign: +1 if quoted in US dollars per unit of the currency, -1 if quoted
# in units of the currency per US dollar (so the currency's value is 1/x).
FX = {
    "JPY": ("DEXJPUS", -1), "CHF": ("DEXSZUS", -1), "MXN": ("DEXMXUS", -1),
    "BRL": ("DEXBZUS", -1), "EUR": ("DEXUSEU", +1), "GBP": ("DEXUSUK", +1),
    "CAD": ("DEXCAUS", -1), "AUD": ("DEXUSAL", +1), "NZD": ("DEXUSNZ", +1),
    "SEK": ("DEXSDUS", -1), "NOK": ("DEXNOUS", -1), "KRW": ("DEXKOUS", -1),
    "ZAR": ("DEXSFUS", -1), "INR": ("DEXINUS", -1),
    # AFE dollar index: dollars' value against advanced economies, so invert
    "AFE": ("DTWEXAFEGS", -1),
}


# ----------------------------------------------------------------- helpers
def fred(series_id):
    path = os.path.join(RAW, "fred", f"{series_id}.csv")
    df = pd.read_csv(path)
    df.columns = ["date", "value"]
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df.dropna().set_index("date")["value"].sort_index()


def log_returns(level, sign=+1):
    """Log returns between consecutive available observations."""
    return sign * np.log(level).diff().dropna()


def ols(X, y, robust=False):
    """OLS with classical (or HC1 robust) standard errors."""
    X, y = np.asarray(X, float), np.asarray(y, float)
    n, k = X.shape
    XtX_inv = np.linalg.inv(X.T @ X)
    b = XtX_inv @ X.T @ y
    e = y - X @ b
    if robust:
        meat = (X * e[:, None] ** 2).T @ X
        V = XtX_inv @ meat @ XtX_inv * n / (n - k)
    else:
        V = XtX_inv * (e @ e) / (n - k)
    se = np.sqrt(np.diag(V))
    r2 = 1 - (e @ e) / ((y - y.mean()) @ (y - y.mean()))
    return {"b": b, "se": se, "t": b / se, "r2": r2, "resid": e,
            "s": math.sqrt((e @ e) / (n - k)), "n": n}


def p_two_sided(z):
    return math.erfc(abs(z) / math.sqrt(2))


def load_fx():
    R = {c: log_returns(fred(i), s) for c, (i, s) in FX.items()}
    trio = pd.concat([R["EUR"], R["GBP"], R["CAD"]], axis=1).dropna()
    R["F"] = trio.mean(axis=1)          # dollar factor: average of EUR, GBP, CAD
    four = pd.concat([R["MXN"], R["BRL"], R["JPY"], R["CHF"]], axis=1).dropna()
    four.columns = ["MXN", "BRL", "JPY", "CHF"]
    R["CARRY"] = (four["MXN"] + four["BRL"]) / 2 - (four["JPY"] + four["CHF"]) / 2
    return R


# ----------------------------------------------------- 1. factor-model event study
def factor_event_study(y, factor):
    d = pd.concat([y, factor], axis=1, keys=["y", "f"]).dropna()
    est = d.loc[EST[0]:EST[1]]
    fit = ols(np.column_stack([np.ones(len(est)), est["f"]]), est["y"])
    a, b = fit["b"]
    ev = d.loc[d.index.isin(EVENT)]
    car = (ev["y"] - a - b * ev["f"]).sum()
    z = car / (fit["s"] * math.sqrt(len(ev)))
    return {"CAR_pct": 100 * car, "z": z, "p": p_two_sided(z), "beta": b,
            "R2": fit["r2"], "days": len(ev)}


def run_event_studies(R):
    rows = []
    names = ["JPY", "CHF", "MXN", "BRL", "AUD", "NZD", "SEK", "NOK", "KRW", "ZAR",
             "INR", "CARRY"]
    for fac_name, fac in [("F (EUR,GBP,CAD)", R["F"]), ("AFE index", R["AFE"]),
                          ("EUR only", R["EUR"])]:
        for c in names:
            r = factor_event_study(R[c], fac)
            rows.append({"factor": fac_name, "series": c, **r})
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUT, "factor_event_study.csv"), index=False, float_format="%.4f")
    return df


# ------------------------------------------------ 2. historical benchmarking
def benchmark(r, start, sign, end_date="2024-08-05", gap_days=20):
    r = r.loc[start:"2024-12-31"]
    dates, x = r.index.tolist(), r.values
    rows = []
    for i in range(len(x) - 3):
        s = x[i:i + 4].sum()
        z = np.nan
        if i >= 250:
            past = x[i - 250:i]
            z = (s - 4 * past.mean()) / (past.std(ddof=1) * 2)
        rows.append((dates[i + 3], sign * 100 * s, sign * z))
    W = pd.DataFrame(rows, columns=["end", "ret_pct", "z"])
    ev = W[W["end"] == end_date].iloc[0]

    def episodes(key):
        """Greedy list of separate episodes: windows sorted by size, each kept only if
        it ends more than `gap_days` calendar days from every episode already kept.
        Also returns the event's episode rank: the number of episodes kept by the time
        the event window is reached in the sorted list."""
        s = W.dropna(subset=[key]).sort_values(key, ascending=False)
        ends = pd.to_datetime(s["end"]).values
        kept, rank = [], None
        for j, t in enumerate(ends):
            if all(abs((t - k) / np.timedelta64(1, "D")) > gap_days for k in ends[kept]):
                kept.append(j)
            if rank is None and s["end"].iloc[j] == end_date:
                rank = len(kept)
            if rank is not None and len(kept) >= 10:
                break
        return s.iloc[kept].reset_index(drop=True), rank

    (raw_ep, raw_rank), (z_ep, z_rank) = episodes("ret_pct"), episodes("z")
    return {
        "windows": len(W), "event_ret_pct": ev["ret_pct"], "event_z": ev["z"],
        "rank_raw_overlapping": int((W["ret_pct"] > ev["ret_pct"]).sum() + 1),
        "rank_raw_episodes": raw_rank,
        "rank_z_episodes": z_rank,
        "top_raw": raw_ep.head(10), "top_z": z_ep.head(10),
    }


def run_benchmarks(R):
    lines, tops = [], []
    for name, series, start, sign in [("Yen", R["JPY"], "1990-01-01", +1),
                                      ("Swiss franc", R["CHF"], "1990-01-01", +1),
                                      ("Carry portfolio (loss)", R["CARRY"], "1999-02-01", -1)]:
        b = benchmark(series, start, sign)
        lines.append(f"{name} from {start}: 4-day move {b['event_ret_pct']:.2f}%, vol-scaled z "
                     f"{b['event_z']:.2f}; rank {b['rank_raw_overlapping']} of {b['windows']} "
                     f"overlapping windows; rank {b['rank_raw_episodes']} among separate episodes "
                     f"(raw), {b['rank_z_episodes']} (vol-scaled)")
        for kind in ["top_raw", "top_z"]:
            t = b[kind].copy()
            t.insert(0, "ranking", kind)
            t.insert(0, "series", name)
            tops.append(t)
    pd.concat(tops).to_csv(os.path.join(OUT, "benchmark_top_episodes.csv"), index=False,
                           float_format="%.3f")
    with open(os.path.join(OUT, "benchmark_summary.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    return lines


# --------------------------------------------------------- 3. the VIX anomaly
def run_vix():
    V, S = fred("VIXCLS"), fred("SP500").loc["2016-11-07":"2024-12-31"]
    d = pd.concat([S, V], axis=1, keys=["S", "V"]).dropna()
    df = pd.DataFrame({"r": 100 * np.log(d["S"]).diff(),
                       "dv": 100 * np.log(d["V"]).diff()}).dropna()
    X = lambda q: np.column_stack([np.ones(len(q)), q["r"], np.minimum(q["r"], 0)])
    est = df.drop(index="2024-08-05")
    fit = ols(X(est), est["dv"])
    ev = df.loc[["2024-08-05"]]
    pred = float((X(ev) @ fit["b"])[0])
    resid_z = (float(ev["dv"].iloc[0]) - pred) / fit["s"]
    all_res = (df["dv"] - X(df) @ fit["b"]) / fit["s"]
    rank = int((all_res > all_res.loc["2024-08-05"]).sum() + 1)
    text = (f"n={fit['n']} days ({df.index[0]} to {df.index[-1]}, excl. 5 Aug 2024)\n"
            f"dlogVIX = {fit['b'][0]:.3f} + {fit['b'][1]:.3f} r + {fit['b'][2]:.3f} min(r,0); "
            f"R2 {fit['r2']:.3f}; residual sd {fit['s']:.2f}\n"
            f"5 Aug 2024: S&P {float(ev['r'].iloc[0]):.2f}%, VIX log change "
            f"{float(ev['dv'].iloc[0]):.1f}, predicted {pred:.1f}, residual {resid_z:.1f} sd, "
            f"rank {rank} of {len(df)}\n")
    with open(os.path.join(OUT, "vix_regression.txt"), "w") as f:
        f.write(text)
    return text


# ------------------------------------------ 4. cross-section and placebo
FLOATERS = ["JPY", "CHF", "SEK", "NOK", "AUD", "NZD", "KRW", "ZAR", "INR", "MXN", "BRL"]


def spearman(x, y):
    return pd.Series(x).rank().corr(pd.Series(y).rank())


def run_cross_section(R):
    rates = pd.read_csv(os.path.join(ROOT, "data", "rates_jul2024.csv")).set_index("currency")["rate_pct"]
    out = []

    def cs(cur, factor, label):
        cars = [factor_event_study(R[c], factor)["CAR_pct"] for c in cur]
        x = rates.loc[cur].values
        fit = ols(np.column_stack([np.ones(len(x)), x]), cars)
        out.append(f"{label}: n={len(cur)}, slope {fit['b'][1]:.3f} (t {fit['t'][1]:.2f}), "
                   f"intercept {fit['b'][0]:.2f}, R2 {fit['r2']:.2f}, Spearman {spearman(x, cars):.2f}")
        return pd.DataFrame({"currency": cur, "rate_pct": x, "CAR_pct": cars, "sample": label})

    t1 = cs(FLOATERS, R["F"], "F factor, 11 floating currencies")
    cs([c for c in FLOATERS if c not in ("JPY", "CHF")], R["F"], "F factor, excl. JPY and CHF")
    cs(FLOATERS + ["EUR", "GBP", "CAD"], R["AFE"], "AFE factor, 14 currencies")

    # placebo: the same slope for every 4-day window in 2023-24, same betas
    ab = {}
    for c in FLOATERS:
        d = pd.concat([R[c], R["F"]], axis=1, keys=["y", "f"]).dropna().loc[EST[0]:EST[1]]
        fit = ols(np.column_stack([np.ones(len(d)), d["f"]]), d["y"])
        ab[c] = fit["b"]
    panel = pd.concat([R[c] for c in FLOATERS] + [R["F"]], axis=1,
                      keys=FLOATERS + ["F"]).dropna().loc["2023-01-01":"2024-12-31"]
    abn = pd.DataFrame({c: panel[c] - ab[c][0] - ab[c][1] * panel["F"] for c in FLOATERS})
    x = rates.loc[FLOATERS].values
    slopes = []
    for i in range(len(abn) - 3):
        y = 100 * abn.iloc[i:i + 4].sum().values
        slopes.append((abn.index[i + 3], np.polyfit(x, y, 1)[0]))
    sl = pd.DataFrame(slopes, columns=["end", "slope"]).sort_values("slope")
    ev_rank = int(sl.reset_index(drop=True).index[sl["end"].values == "2024-08-05"][0] + 1)
    out.append(f"Placebo: event-window slope ranks {ev_rank} (most negative = 1) of {len(sl)} "
               f"rolling 4-day windows in 2023-24; median slope {sl['slope'].median():.3f}; "
               f"lowest: " + ", ".join(f"{e} {s:.2f}" for e, s in sl.head(5).values))
    t1.to_csv(os.path.join(OUT, "cross_section.csv"), index=False, float_format="%.3f")
    with open(os.path.join(OUT, "cross_section.txt"), "w") as f:
        f.write("\n".join(out) + "\n")
    return out


# ------------------------------------------------------------ 5. CFTC positioning
def run_cftc(R):
    c = pd.read_csv(os.path.join(RAW, "cftc_jpy_legacy.csv"))
    c["share"] = c["net"] / c["open_interest"]
    m = c[(c["report_date"] >= "1993-01-01") & (c["report_date"] <= "2024-12-31")].copy()
    m["month"] = m["report_date"].str[:7]
    m.groupby("month").last()[["report_date", "net"]].to_csv(
        os.path.join(OUT, "cftc_monthly.csv"))
    pre = c[c["report_date"] <= "2024-07-30"]
    lines = ["Five most negative net positions (contracts) to 30 Jul 2024:"]
    for _, r in pre.nsmallest(5, "net").iterrows():
        lines.append(f"  {r['report_date']} {r['net']:,} ({100 * r['share']:.1f}% of open interest)")
    lines.append("Five most negative net positions as a share of open interest:")
    for _, r in pre.nsmallest(5, "share").iterrows():
        lines.append(f"  {r['report_date']} {100 * r['share']:.1f}% ({r['net']:,})")

    # Exploratory: does visible positioning predict the size of the next yen spike?
    J = R["JPY"]
    jd, jv = J.index.tolist(), J.values
    rows = []
    for _, r in c[(c["report_date"] >= "1993-01-01") & (c["report_date"] <= "2023-12-31")].iterrows():
        i = next((k for k, d in enumerate(jd) if d > r["report_date"]), None)
        if i is None or i + 20 > len(jv) or i - 21 < 0:
            continue
        window = jv[i:i + 20]
        max4 = max(window[k:k + 4].sum() for k in range(17))
        past20 = jv[i - 20:i].sum()
        rows.append((r["report_date"], 100 * r["share"], 100 * past20, 100 * max4))
    D = pd.DataFrame(rows, columns=["date", "net_share_pct", "past20_pct", "max4d_next20_pct"])
    X = lambda q: np.column_stack([np.ones(len(q)), q["net_share_pct"], q["past20_pct"]])
    full = ols(X(D), D["max4d_next20_pct"])
    sub = D.iloc[::4]
    non = ols(X(sub), sub["max4d_next20_pct"])
    D["quintile"] = pd.qcut(D["net_share_pct"], 5, labels=[1, 2, 3, 4, 5])
    q = D.groupby("quintile", observed=True).agg(
        n=("max4d_next20_pct", "size"),
        mean_max4d=("max4d_next20_pct", "mean"),
        share_above_3pct=("max4d_next20_pct", lambda s: 100 * (s > 3).mean()))
    # fitted and actual values for the 9 July 2024 report (the last report before the
    # yen began to rise sharply on 11 July)
    ref = c[c["report_date"] == "2024-07-09"].iloc[0]
    i = next(k for k, d in enumerate(jd) if d > "2024-07-09")
    past = 100 * jv[i - 20:i].sum()
    fitted = non["b"][0] + non["b"][1] * 100 * ref["share"] + non["b"][2] * past
    actual = 100 * max(jv[i + k:i + k + 4].sum() for k in range(17))
    lines += [
        "",
        f"Exploratory regression, weekly 1993-2023 (n={full['n']}): max 4-day yen gain in next "
        f"20 trading days on net position (% of OI) and past 20-day yen return",
        f"  all weeks: slope on positioning {full['b'][1]:.4f} (t {full['t'][1]:.2f}), R2 {full['r2']:.3f}",
        f"  every 4th week (n={non['n']}): slope {non['b'][1]:.4f} (t {non['t'][1]:.2f})",
        f"  9 Jul 2024 report: fitted {fitted:.2f}%, actual {actual:.2f}%",
        q.round(2).to_string(),
    ]
    with open(os.path.join(OUT, "cftc_positioning.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    return lines


# --------------------------------------------------------------- 6. firm level
def run_firms():
    uni = pd.read_csv(os.path.join(ROOT, "data", "firm_universe.csv"), dtype={"code": str})
    def px(t):
        d = pd.read_csv(os.path.join(RAW, "yahoo", f"{t}.csv")).set_index("date")["adjclose"]
        return np.log(d.dropna()).diff().dropna()
    mkt = px("1306.T")
    # yen return (value of yen) from the FRED noon New York rate; for a Tokyo trading
    # day t use the same-day and the previous New York observation, because Tokyo
    # closes before New York noon.
    yen = log_returns(fred("DEXJPUS"), -1).loc["2023-12-01":"2024-08-31"]
    ny = yen.index.tolist()
    def prev_ny(d):
        p = [x for x in ny if x < d]
        return yen[p[-1]] if p else np.nan
    Y = pd.DataFrame({"yc": [yen.get(d, np.nan) for d in mkt.index],
                      "yl": [prev_ny(d) for d in mkt.index]}, index=mkt.index)
    rows = []
    for _, u in uni.iterrows():
        r = px(f"{u['code']}.T")
        d = pd.concat([r, mkt, Y], axis=1, keys=["r", "m", "Y"]).dropna()
        d.columns = ["r", "m", "yc", "yl"]
        est = d.loc["2024-01-04":EST[1]]
        fit = ols(np.column_stack([np.ones(len(est)), est["m"], est["yc"], est["yl"]]), est["r"])
        ev = 100 * r[r.index.isin(EVENT)].sum()
        rows.append({"code": u["code"], "name": u["name"], "group": u["group"],
                     "market_beta": fit["b"][1], "yen_beta": fit["b"][2] + fit["b"][3],
                     "event_ret_pct": ev, "aug6_ret_pct": 100 * r.get("2024-08-06", np.nan)})
    F = pd.DataFrame(rows)
    F.to_csv(os.path.join(OUT, "firm_level.csv"), index=False, float_format="%.3f")
    m_ev = 100 * mkt[mkt.index.isin(EVENT)].sum()
    g = F.groupby("group")[["event_ret_pct", "aug6_ret_pct", "market_beta", "yen_beta"]].mean()
    exp, fin = (F["group"] == "EXP").astype(float), (F["group"] == "FIN").astype(float)
    one = np.ones(len(F))
    m1 = ols(np.column_stack([one, exp, fin]), F["event_ret_pct"], robust=True)
    m2 = ols(np.column_stack([one, F["market_beta"], F["yen_beta"]]), F["event_ret_pct"], robust=True)
    m3 = ols(np.column_stack([one, F["market_beta"], F["yen_beta"], exp, fin]),
             F["event_ret_pct"], robust=True)
    fmt = lambda m, names: ", ".join(f"{n} {b:.2f} (t {t:.2f})" for n, b, t in zip(names, m["b"], m["t"])) + f"; R2 {m['r2']:.2f}"
    lines = [f"TOPIX ETF (1306.T) event-window return: {m_ev:.2f}%", g.round(2).to_string(), "",
             "Cross-sectional OLS, HC1 robust t-statistics (domestic firms are the base group):",
             "  groups only:   " + fmt(m1, ["const", "EXP", "FIN"]),
             "  betas only:    " + fmt(m2, ["const", "mkt beta", "yen beta"]),
             "  both:          " + fmt(m3, ["const", "mkt beta", "yen beta", "EXP", "FIN"])]
    with open(os.path.join(OUT, "firm_level.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    return lines


# ------------------------------------------- 7. reversal and rate repricing
def run_reversal_and_rates(R):
    rates = pd.read_csv(os.path.join(ROOT, "data", "rates_jul2024.csv")).set_index("currency")["rate_pct"]
    x = rates.loc[FLOATERS].values

    def slope(days):
        ys = []
        for c in FLOATERS:
            d = pd.concat([R[c], R["F"]], axis=1, keys=["y", "f"]).dropna()
            est = d.loc[EST[0]:EST[1]]
            a, b = ols(np.column_stack([np.ones(len(est)), est["f"]]), est["y"])["b"]
            ev = d.loc[d.index.isin(days)]
            ys.append(100 * (ev["y"] - a - b * ev["f"]).sum())
        return np.polyfit(x, ys, 1)[0]

    rev = slope(["2024-08-06", "2024-08-07", "2024-08-08", "2024-08-09"])
    y2 = fred("DGS2")
    d2 = y2.loc["2024-08-05"] - y2.loc["2024-07-30"]
    lines = [f"Cross-sectional slope of abnormal returns on rates, 6-9 Aug 2024: {rev:.3f} "
             f"(event window: {slope(EVENT):.3f})",
             f"US 2-year yield change 30 Jul -> 5 Aug 2024: {d2:.2f} points; implied yen move "
             f"over a 2-year horizon: {-2 * d2:.2f}%"]
    with open(os.path.join(OUT, "reversal_and_rates.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    return lines


# ------------------------------- 8. identification checks added in Draft 4
def run_identification(R):
    """Risk-controlled cross-section, permutation test, non-overlapping placebo,
    rate-repricing bound and positioning robustness."""
    rates = pd.read_csv(os.path.join(ROOT, "data", "rates_jul2024.csv")).set_index("currency")["rate_pct"]
    x = rates.loc[FLOATERS].values
    sp = log_returns(fred("SP500"))
    vix = log_returns(fred("VIXCLS"))
    REV = ["2024-08-06", "2024-08-07", "2024-08-08", "2024-08-09"]
    rows = []
    for c in FLOATERS:
        d = pd.concat([R[c], R["F"], sp, vix], axis=1, keys=["y", "f", "sp", "vix"]).dropna()
        est = d.loc[EST[0]:EST[1]]
        one = np.ones(len(est))
        a, b = ols(np.column_stack([one, est["f"]]), est["y"])["b"]
        b_sp = ols(np.column_stack([one, est["f"], est["sp"]]), est["y"])["b"][2]
        b_vix = ols(np.column_stack([one, est["f"], est["vix"]]), est["y"])["b"][2]
        dd = pd.concat([R[c], R["F"]], axis=1, keys=["y", "f"]).dropna()
        car = lambda days: 100 * (dd.loc[dd.index.isin(days), "y"] - a - b * dd.loc[dd.index.isin(days), "f"]).sum()
        rows.append({"currency": c, "rate": rates[c], "beta_sp": b_sp, "beta_vix": b_vix,
                     "car": car(EVENT), "rev": car(REV)})
    T = pd.DataFrame(rows)
    T.to_csv(os.path.join(OUT, "cross_section_risk_controls.csv"), index=False, float_format="%.5f")
    one = np.ones(len(T))
    lines = []
    for lab, col in [("Event window", "car"), ("Reversal 6-9 Aug", "rev")]:
        for name, X in [("rate only", [one, T["rate"]]), ("rate + S&P beta", [one, T["rate"], T["beta_sp"]]),
                        ("rate + VIX beta", [one, T["rate"], T["beta_vix"]])]:
            f = ols(np.column_stack(X), T[col])
            lines.append(f"{lab}, {name}: rate slope {f['b'][1]:.3f} (t {f['t'][1]:.2f})"
                         + (f", risk beta t {f['t'][2]:.2f}" if len(X) == 3 else "") + f", R2 {f['r2']:.2f}")
    # permutation test
    rng = np.random.default_rng(12345)
    def slope(xx, yy):
        return np.polyfit(xx, yy, 1)[0]
    for lab, sub in [("11 currencies", T), ("excl. JPY and CHF", T[~T["currency"].isin(["JPY", "CHF"])])]:
        obs = slope(sub["rate"].values, sub["car"].values)
        perms = np.array([slope(rng.permutation(sub["rate"].values), sub["car"].values) for _ in range(100000)])
        lines.append(f"Permutation test ({lab}): observed slope {obs:.3f}; share of 100,000 shuffles "
                     f"at least as negative {np.mean(perms <= obs):.5f}")
    # non-overlapping placebo, blocks aligned on the event window
    ab = {}
    for c in FLOATERS:
        d = pd.concat([R[c], R["F"]], axis=1, keys=["y", "f"]).dropna().loc[EST[0]:EST[1]]
        ab[c] = ols(np.column_stack([np.ones(len(d)), d["f"]]), d["y"])["b"]
    panel = pd.concat([R[c] for c in FLOATERS] + [R["F"]], axis=1,
                      keys=FLOATERS + ["F"]).dropna().loc["2023-01-01":"2024-12-31"]
    abn = pd.DataFrame({c: panel[c] - ab[c][0] - ab[c][1] * panel["F"] for c in FLOATERS})
    start = abn.index.get_loc("2024-07-31") % 4
    blocks = [(abn.index[i + 3], slope(x, 100 * abn.iloc[i:i + 4].sum().values))
              for i in range(start, len(abn) - 3, 4)]
    bl = sorted(blocks, key=lambda t: t[1])
    rank = [e for e, _ in bl].index("2024-08-05") + 1
    lines.append(f"Non-overlapping placebo: event window ranks {rank} of {len(bl)}")
    # rate-repricing bound: change in US-Japan spread x maturity, 30 Jul -> 5 Aug 2024
    j = pd.read_csv(os.path.join(RAW, "jgb_yields.csv"), skiprows=1, na_values="-")
    j["Date"] = pd.to_datetime(j["Date"], errors="coerce").dt.strftime("%Y-%m-%d")
    j = j.dropna(subset=["Date"]).set_index("Date")
    for d0, d1 in [("2024-07-30", "2024-08-05"), ("2024-07-10", "2024-07-30")]:
        for us, jp, n in [("DGS1", "1Y", 1), ("DGS2", "2Y", 2), ("DGS5", "5Y", 5)]:
            u = fred(us)
            du = u.loc[d1] - u.loc[d0]
            dj = float(j.loc[d1, jp]) - float(j.loc[d0, jp])
            lines.append(f"{d0} -> {d1}, {n}-year: US {du:+.2f}, Japan {dj:+.3f}, spread {du - dj:+.3f}; "
                         f"implied yen move {-(du - dj) * n:.2f}% (US only: {-du * n:.2f}%)")
    with open(os.path.join(OUT, "identification_checks.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    return lines


def run_positioning_robustness(R):
    c = pd.read_csv(os.path.join(RAW, "cftc_jpy_legacy.csv"))
    c["share"] = 100 * c["net"] / c["open_interest"]
    J = R["JPY"]
    jd, jv = J.index.tolist(), J.values
    lines = []
    for H in (10, 20, 40):
        rows = []
        for _, r in c[(c["report_date"] >= "1993-01-01") & (c["report_date"] <= "2023-12-31")].iterrows():
            i = next((k for k, d in enumerate(jd) if d > r["report_date"]), None)
            if i is None or i + H > len(jv) or i - 21 < 0:
                continue
            m4 = 100 * max(jv[i + k:i + k + 4].sum() for k in range(H - 3))
            rows.append((r["share"], m4))
        D = pd.DataFrame(rows, columns=["share", "m4"]).sort_values("share")
        q = len(D) // 5
        for thr in (2, 3, 4):
            lo, hi = (D["m4"].iloc[:q] > thr).mean(), (D["m4"].iloc[-q:] > thr).mean()
            lines.append(f"Horizon {H} days, threshold {thr}%: spike frequency after most-short fifth "
                         f"{100 * lo:.1f}%, after most-long fifth {100 * hi:.1f}%")
    with open(os.path.join(OUT, "positioning_robustness.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    return lines


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    R = load_fx()
    es = run_event_studies(R)
    print(es[es["factor"] == "F (EUR,GBP,CAD)"].round(3).to_string(index=False))
    print("\n".join(run_benchmarks(R)))
    print(run_vix())
    print("\n".join(run_cross_section(R)))
    print("\n".join(run_cftc(R)))
    print("\n".join(run_firms()))
    print("\n".join(run_reversal_and_rates(R)))
    print("\n".join(run_identification(R)))
    print("\n".join(run_positioning_robustness(R)))
