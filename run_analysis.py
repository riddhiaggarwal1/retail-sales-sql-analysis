"""Build the SQLite database, run every .sql query and save results.

Usage:  python run_analysis.py

Outputs
  retail.db        the database (rebuilt on every run)
  <query>.csv      one result table per SQL file
  *.png            charts
"""
import sqlite3
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).parent
DATA = SQL = RESULTS = ROOT          # all files sit in one folder
TABLES = ["customers", "products", "orders", "order_items"]

BLUE, INK, MUTED, GRID = "#2a78d6", "#0b0b0b", "#898781", "#e1e0d9"
plt.rcParams.update({
    "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb",
    "savefig.facecolor": "#fcfcfb", "font.size": 10,
    "text.color": INK, "axes.labelcolor": "#52514e",
    "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.edgecolor": "#c3c2b7", "axes.spines.top": False,
    "axes.spines.right": False, "axes.spines.left": False,
    "axes.titlelocation": "left", "axes.titleweight": "bold",
    "axes.titlesize": 12, "axes.titlepad": 14,
})


def build_database(con):
    con.executescript((SQL / "00_schema.sql").read_text(encoding="utf-8"))
    for table in TABLES:
        pd.read_csv(DATA / f"{table}.csv").to_sql(
            table, con, if_exists="append", index=False)
    con.commit()


def run_queries(con):
    results = {}
    for path in sorted(SQL.glob("*.sql")):
        if path.name.startswith("00_"):
            continue
        df = pd.read_sql_query(path.read_text(encoding="utf-8"), con)
        df.to_csv(RESULTS / f"{path.stem}.csv", index=False)
        results[path.stem] = df
        print(f"\n=== {path.name} ===")
        print(df.to_string(index=False))
    return results


def save(fig, name):
    fig.tight_layout()
    fig.savefig(RESULTS / name, dpi=160)
    plt.close(fig)


def chart_monthly_revenue(df):
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(df["order_month"], df["revenue"] / 1000, color=BLUE, lw=2)
    ax.set_title("Monthly net revenue (EUR thousand)")
    ax.set_ylim(0)
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.tick_params(length=0)
    ax.set_xticks(range(0, len(df), 3))
    peak = df["revenue"].idxmax()
    ax.annotate(f"{df['order_month'][peak]}: {df['revenue'][peak] / 1000:.0f}k",
                (peak, df["revenue"][peak] / 1000), xytext=(-8, 4),
                textcoords="offset points", ha="right", color="#52514e")
    save(fig, "monthly_revenue.png")


def barh(df, label, value, title, name, fmt="{:.1f}"):
    df = df.sort_values(value)
    fig, ax = plt.subplots(figsize=(7, 0.5 * len(df) + 1.2))
    bars = ax.barh(df[label].astype(str), df[value], color=BLUE, height=0.6)
    ax.bar_label(bars, labels=[fmt.format(v) for v in df[value]],
                 padding=4, color="#52514e")
    ax.set_title(title)
    ax.xaxis.set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.tick_params(length=0, labelcolor="#52514e")
    ax.set_xlim(0, df[value].max() * 1.15)
    save(fig, name)


def chart_cohorts(df):
    grid = df.pivot(index="cohort", columns="quarters_since_first_order",
                    values="retention_pct")
    later = grid.drop(columns=0)          # quarter 0 is always 100 %
    for y in range(len(later)):           # no repeat buyers in an observed quarter = 0 %
        seen = len(later) - 1 - y
        later.iloc[y, :seen] = later.iloc[y, :seen].fillna(0)
    fig, ax = plt.subplots(figsize=(8, 4.2))
    im = ax.imshow(later, cmap="Blues", vmin=0, vmax=later.max().max() * 1.6,
                   aspect="auto")
    ax.set_xticks(range(later.shape[1]), later.columns)
    ax.set_yticks(range(len(later)),
                  [f"{c}  (n={int(n)})" for c, n in
                   df[df["quarters_since_first_order"] == 0][["cohort", "cohort_size"]].values])
    for y in range(later.shape[0]):
        for x in range(later.shape[1]):
            v = later.iat[y, x]
            if pd.notna(v):
                ax.text(x, y, f"{v:.0f}%", ha="center", va="center", color=INK, fontsize=9)
    ax.set_title("Customers ordering again, by quarter of first order")
    ax.set_xlabel("Quarters since first order")
    ax.tick_params(length=0, labelcolor="#52514e")
    for s in ax.spines.values():
        s.set_visible(False)
    save(fig, "cohort_retention.png")


def main():
    RESULTS.mkdir(exist_ok=True)
    db = ROOT / "retail.db"
    db.unlink(missing_ok=True)
    with sqlite3.connect(db) as con:
        build_database(con)
        r = run_queries(con)
    chart_monthly_revenue(r["01_monthly_revenue"])
    barh(r["02_category_performance"], "category", "return_rate_pct",
         "Return rate by category (% of units)", "return_rate_by_category.png", "{:.1f}%")
    barh(r["03_channel_performance"], "channel", "revenue_per_signup",
         "Net revenue per signup by acquisition channel (EUR)",
         "revenue_per_signup_by_channel.png", "{:.0f}")
    barh(r["05_rfm_segments"], "segment", "revenue_share_pct",
         "Share of net revenue by customer segment", "revenue_by_segment.png", "{:.1f}%")
    chart_cohorts(r["04_cohort_retention"])
    print("\nDone. Result tables (CSV) and charts (PNG) written.")


if __name__ == "__main__":
    main()
