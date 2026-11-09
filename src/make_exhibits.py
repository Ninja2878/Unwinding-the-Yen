"""Draw Exhibits 1-6 of the paper into exhibits/.

Run from the repository root:   python src/make_exhibits.py
Exhibit 1 uses data/fred_data_2024.csv; Exhibits 2-5 use the files in results/
(written by src/analysis.py); Exhibit 6 is a diagram.
"""
import os

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Patch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES, EXH = os.path.join(ROOT, "results"), os.path.join(ROOT, "exhibits")
os.makedirs(EXH, exist_ok=True)

INK, INK2, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#8a8984", "#e4e3df", "#ffffff"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": INK2,
    "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "axes.spines.top": False, "axes.spines.right": False,
})


def title(fig, text, source):
    fig.suptitle(text, x=0.02, ha="left", fontsize=10.5, color=INK, fontweight="bold")
    fig.text(0.02, 0.008, source, fontsize=7, color=INK2, va="bottom")


def save(fig, name):
    fig.savefig(os.path.join(EXH, name), dpi=220, facecolor=SURF)
    plt.close(fig)


# ---------------------------------------------------------------- Exhibit 1
def exhibit1():
    df = pd.read_csv(os.path.join(ROOT, "data", "fred_data_2024.csv"), parse_dates=["date"]).set_index("date")
    fx = pd.DataFrame({"JPY": 1 / df["DEXJPUS"], "CHF": 1 / df["DEXSZUS"],
                       "MXN": 1 / df["DEXMXUS"], "BRL": 1 / df["DEXBZUS"]}).dropna()
    r = np.log(fx).diff()
    carry = ((r["MXN"] + r["BRL"]) / 2 - (r["JPY"] + r["CHF"]) / 2).loc["2024-07-01":]
    base = "2024-06-28"
    yen = 100 * (np.log(fx["JPY"]) - np.log(fx.loc[base, "JPY"])).loc["2024-06-28":"2024-08-16"]
    car = 100 * carry.cumsum().reindex(yen.index).fillna(0)
    nk = df["NIKKEI225"].dropna()
    nk = 100 * (np.log(nk) - np.log(nk.loc[base])).loc["2024-06-28":"2024-08-16"]
    vix = df["VIXCLS"].dropna().loc["2024-06-28":"2024-08-16"]

    fig, (a1, a2) = plt.subplots(2, 1, figsize=(6.5, 5.6), sharex=True, facecolor=SURF,
                                 gridspec_kw={"height_ratios": [1.6, 1]})
    for ax in (a1, a2):
        ax.axvspan(pd.Timestamp("2024-07-30 12:00"), pd.Timestamp("2024-08-05 12:00"),
                   color=GRID, alpha=0.7, lw=0)
        ax.grid(axis="y", color=GRID, lw=0.8)
    a1.plot(yen.index, yen, color=BLUE, lw=2, label="Yen against US dollar")
    a1.plot(car.index, car, color=ORANGE, lw=2, label="Carry portfolio (long MXN, BRL; short JPY, CHF)")
    a1.plot(nk.index, nk, color=INK2, lw=1.6, ls=(0, (4, 2)), label="Nikkei 225")
    a1.axhline(0, color=INK2, lw=0.8)
    a1.set_ylabel("Cumulative change since 28 June (%)")
    a1.legend(frameon=False, fontsize=7.8, loc="lower left")
    a2.plot(vix.index, vix, color=BLUE, lw=2)
    a2.scatter(vix.index, vix, color=BLUE, s=9, zorder=3)
    a2.set_ylabel("VIX (close)")
    a1.set_ylim(-25, 17)
    marks = [("2024-07-11", "Japanese \nintervention ", "right"), ("2024-07-31", "BoJ \nhike ", "right"),
             ("2024-08-02", " US\n payrolls", "left")]
    for d, lab, ha in marks:
        for ax in (a1, a2):
            ax.axvline(pd.Timestamp(d), color=INK2, lw=0.7, ls=(0, (2, 2)))
        a1.text(pd.Timestamp(d), 16.6, lab, fontsize=7, color=INK2, ha=ha, va="top")
    a2.text(pd.Timestamp("2024-08-02 12:00"), 11.5, "event window", fontsize=7,
            color=INK2, ha="center", va="bottom")
    a2.set_ylim(10, 41)
    a2.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    a2.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO))
    title(fig, "Exhibit 1. The yen and the carry trade moved first; volatility followed",
          "Source: FRED (DEXJPUS, DEXSZUS, DEXMXUS, DEXBZUS, NIKKEI225, VIXCLS); author's calculations.\n"
          "Shaded: event window, 31 Jul - 5 Aug 2024. Dotted lines: the intervention, BoJ and payroll dates.")
    fig.tight_layout(rect=(0, 0.05, 1, 0.96))
    save(fig, "Exhibit 1 - sequencing.png")


# ---------------------------------------------------------------- Exhibit 2
def exhibit2():
    t = pd.read_csv(os.path.join(RES, "benchmark_top_episodes.csv"))
    t = t[(t["series"] == "Carry portfolio (loss)") & (t["ranking"] == "top_z")].head(10)
    t = t.iloc[::-1]
    labels = [pd.Timestamp(e).strftime("%b %Y") for e in t["end"]]
    col = [ORANGE if e == "2024-08-05" else BLUE for e in t["end"]]
    fig, ax = plt.subplots(figsize=(6.5, 3.9), facecolor=SURF)
    y = np.arange(len(t))
    ax.barh(y, t["z"], color=col, height=0.62)
    for yi, (z, r) in enumerate(zip(t["z"], t["ret_pct"])):
        ax.text(z + 0.12, yi, f"{z:.1f}  (loss {r:.1f}%)", va="center", fontsize=7.8, color=INK)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, color=INK)
    ax.set_xlabel("Four-day loss in units of its trailing 250-day volatility")
    ax.set_xlim(0, t["z"].max() + 2.6)
    ax.grid(axis="x", color=GRID, lw=0.8)
    title(fig, "Exhibit 2. The ten largest carry crashes since 1999, scaled by volatility",
          "Separate episodes (window end dates at least 20 days apart). Carry portfolio as in Exhibit 1. "
          "Source: FRED; author's calculations.")
    fig.tight_layout(rect=(0, 0.04, 1, 0.95))
    save(fig, "Exhibit 2 - historical benchmark.png")


# ---------------------------------------------------------------- Exhibit 3
def exhibit3():
    c = pd.read_csv(os.path.join(RES, "cross_section.csv"))
    c = c[c["sample"] == "F factor, 11 floating currencies"]
    x, y = c["rate_pct"].values, c["CAR_pct"].values
    b, a = np.polyfit(x, y, 1)
    fig, ax = plt.subplots(figsize=(6.5, 3.9), facecolor=SURF)
    xx = np.linspace(-0.3, 12, 50)
    ax.plot(xx, a + b * xx, color=INK2, lw=1, ls=(0, (4, 2)))
    ax.scatter(x, y, s=34, color=BLUE, zorder=3)
    nudge = {"AUD": (-6, -10), "NOK": (6, 2), "KRW": (-6, 8), "SEK": (6, 4), "NZD": (6, 2),
             "INR": (6, 2), "ZAR": (6, 2), "BRL": (6, 3), "MXN": (-6, -10), "JPY": (6, 0),
             "CHF": (6, 0)}
    for cur, xi, yi in zip(c["currency"], x, y):
        dx, dy = nudge.get(cur, (6, 2))
        ax.annotate(cur, (xi, yi), xytext=(dx, dy), textcoords="offset points", fontsize=8,
                    color=INK, ha="left" if dx > 0 else "right")
    ax.axhline(0, color=INK2, lw=0.8)
    ax.set_xlabel("Three-month interest rate, July 2024 (%)")
    ax.set_ylabel("Abnormal return, 31 Jul - 5 Aug (%)")
    ax.grid(color=GRID, lw=0.8)
    ax.text(11.8, a + b * 11.8 + 1.0, f"slope {b:.2f}", fontsize=7.8, color=INK2, ha="right")
    title(fig, "Exhibit 3. The higher a currency's interest rate, the more it fell",
          "Abnormal returns against the US dollar from the factor model (Section 4.1). Rates: OECD via FRED "
          "(call rate for BRL, INR).")
    fig.tight_layout(rect=(0, 0.04, 1, 0.95))
    save(fig, "Exhibit 3 - cross-section.png")


# ---------------------------------------------------------------- Exhibit 4
def exhibit4():
    f = pd.read_csv(os.path.join(RES, "firm_level.csv"), dtype={"code": str})
    MKT, YEN = -19.56, 6.57   # event-window TOPIX ETF and yen returns (%)
    f["implied"] = f["market_beta"] * MKT + f["yen_beta"] * YEN
    g = f.groupby("group")[["event_ret_pct", "implied"]].mean().loc[["DOM", "EXP", "FIN"]]
    n = f.groupby("group").size().loc[["DOM", "EXP", "FIN"]]
    names = [f"Domestic-facing\n({n['DOM']} firms)", f"Exporters\n({n['EXP']} firms)",
             f"Banks and insurers\n({n['FIN']} firms)"]
    fig, ax = plt.subplots(figsize=(6.5, 3.7), facecolor=SURF)
    xs = np.arange(3)
    w = 0.36
    b1 = ax.bar(xs - w / 2, g["event_ret_pct"], w, color=BLUE, label="Actual")
    b2 = ax.bar(xs + w / 2, g["implied"], w, color=MUTED, label="Implied by pre-event betas")
    for bars in (b1, b2):
        for rect in bars:
            v = rect.get_height()
            ax.text(rect.get_x() + rect.get_width() / 2, v - 0.6, f"{v:.1f}", ha="center",
                    va="top", fontsize=8, color=INK)
    ax.set_xticks(xs)
    ax.set_xticklabels(names, color=INK)
    ax.axhline(0, color=INK2, lw=0.8)
    ax.set_ylabel("Return, 31 Jul - 5 Aug (%)")
    ax.set_ylim(min(g.min()) - 4, 2)
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.legend(frameon=False, fontsize=8, loc="lower left")
    title(fig, "Exhibit 4. Domestically oriented firms also fell 15 per cent",
          "Mean log returns of 62 large Tokyo-listed firms. Implied = market beta x TOPIX move + yen beta x yen move,\n"
          "with betas estimated over Jan-Jun 2024. Source: Yahoo Finance, FRED; author's calculations.")
    fig.tight_layout(rect=(0, 0.07, 1, 0.95))
    save(fig, "Exhibit 4 - firm level.png")


# ---------------------------------------------------------------- Exhibit 5
def exhibit5():
    m = pd.read_csv(os.path.join(RES, "cftc_monthly.csv"))
    m["t"] = pd.to_datetime(m["month"] + "-15")
    fig, ax = plt.subplots(figsize=(6.5, 3.4), facecolor=SURF)
    ax.fill_between(m["t"], m["net"] / 1000, 0, where=m["net"] < 0, color=BLUE, alpha=0.85, lw=0)
    ax.fill_between(m["t"], m["net"] / 1000, 0, where=m["net"] >= 0, color=MUTED, alpha=0.7, lw=0)
    ax.axhline(0, color=INK2, lw=0.8)
    for d, lab, ha in [("2007-06-15", "Jun 2007: -188,077 ", "right"), ("2024-06-15", "Jul 2024: -184,223 ", "right")]:
        ax.annotate(lab, (pd.Timestamp(d), -176), xytext=(-2, 0), textcoords="offset points",
                    fontsize=7.5, color=INK, ha=ha, va="center")
    ax.set_ylim(-200, 90)
    ax.set_ylabel("Net position (thousand contracts)")
    ax.grid(axis="y", color=GRID, lw=0.8)
    title(fig, "Exhibit 5. Visible speculative short positions in the yen, 1993-2024",
          "Net non-commercial positions in CME yen futures, last report of each month (labels give weekly peaks).\n"
          "Source: CFTC Commitments of Traders, legacy futures-only report, contract 097741.")
    fig.tight_layout(rect=(0, 0.07, 1, 0.95))
    save(fig, "Exhibit 5 - CFTC history.png")


# ---------------------------------------------------------------- Exhibit 6
def exhibit6():
    fig, ax = plt.subplots(figsize=(6.5, 5.6), facecolor=SURF)
    ax.set_xlim(0, 10); ax.set_ylim(0, 8.6); ax.axis("off")
    boxes = [
        (5.0, 6.55, "1. Yen strengthens\n(cost of yen funding rises)"),
        (8.15, 4.4, "2. Losses on short-yen\npositions; margin calls"),
        (6.95, 1.55, "3. Forced sales of the\nassets the yen funded\n(equities, high-yield FX)"),
        (3.05, 1.55, "4. Asset prices fall,\nvolatility jumps"),
        (1.85, 4.4, "5. Volatility-based risk\nlimits cut exposure;\nyen bought back to close"),
    ]
    W, H = 2.95, 1.15
    centres = []
    for x, y, t in boxes:
        ax.add_patch(FancyBboxPatch((x - W / 2, y - H / 2), W, H,
                     boxstyle="round,pad=0.02,rounding_size=0.12", fc="#f3f6fb", ec=BLUE, lw=1.4))
        ax.text(x, y, t, ha="center", va="center", fontsize=8.6, color=INK)
        centres.append((x, y))

    def edge(p, q):
        (x1, y1), (x2, y2) = p, q
        dx, dy = x2 - x1, y2 - y1
        s = min((W / 2 + 0.08) / abs(dx) if dx else 1e9, (H / 2 + 0.08) / abs(dy) if dy else 1e9)
        return x1 + dx * s, y1 + dy * s

    for i in range(5):
        p, q = centres[i], centres[(i + 1) % 5]
        ax.add_patch(FancyArrowPatch(edge(p, q), edge(q, p), arrowstyle="-|>", mutation_scale=14,
                     lw=1.6, color=INK2, connectionstyle="arc3,rad=-0.18"))
    ax.text(5.0, 4.1, "Self-reinforcing\nunwind", ha="center", va="center", fontsize=9.5,
            color=INK2, style="italic")
    ax.add_patch(FancyBboxPatch((0.15, 7.45), 3.2, 0.9, boxstyle="round,pad=0.02,rounding_size=0.12",
                 fc=SURF, ec=ORANGE, lw=1.4))
    ax.text(1.75, 7.9, "Triggers: intervention (11-12 Jul),\nBoJ hike (31 Jul), payrolls (2 Aug)",
            ha="center", va="center", fontsize=8.0, color=INK)
    ax.add_patch(FancyArrowPatch((3.25, 7.75), (3.55, 7.0), arrowstyle="-|>", mutation_scale=13,
                 lw=1.4, color=ORANGE))
    ax.add_patch(FancyBboxPatch((6.2, 7.45), 3.65, 0.9, boxstyle="round,pad=0.02,rounding_size=0.12",
                 fc=SURF, ec=INK2, lw=1.0, ls=(0, (3, 2))))
    ax.text(8.025, 7.9, "Amplifiers: crowded positions,\nthin August liquidity, poor visibility",
            ha="center", va="center", fontsize=8.0, color=INK)
    title(fig, "Exhibit 6. How a modest shock became a large one",
          "Source: author, drawing on Brunnermeier and Pedersen (2009), Adrian and Shin (2010) and BIS (2024b).")
    fig.tight_layout(rect=(0, 0.03, 1, 0.96))
    save(fig, "Exhibit 6 - feedback loop.png")


if __name__ == "__main__":
    for f in (exhibit1, exhibit2, exhibit3, exhibit4, exhibit5, exhibit6):
        f()
    print("Exhibits written to", EXH)
