"""Tables and charts from data/clean/s206_transactions.csv.gz. Amounts are obligations in current U.S. dollars."""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
TAB, FIG = ROOT / "output" / "tables", ROOT / "figures"
TAB.mkdir(parents=True, exist_ok=True); FIG.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(ROOT / "data" / "clean" / "s206_transactions.csv.gz", dtype=str, low_memory=False)
df["obligation_usd"] = df["obligation_usd"].astype(float)
df["fiscal_year"] = df["fiscal_year"].astype(int)
df["where"] = df["pop_country_code"].map(lambda c: "United States" if c == "USA" else ("Unknown" if pd.isna(c) else "Outside the United States"))
df["parent"] = df["recipient_parent_name"].fillna(df["recipient_name"])
M = 1e6


def by(cols, data=df):
    return data.groupby(cols)["obligation_usd"].sum().div(M).round(2)


# 1. By fiscal year, inside and outside the United States.
fy = by(["fiscal_year", "where"]).unstack(fill_value=0)
fy["Total"] = fy.sum(axis=1)
fy.columns.name = None
fy.to_csv(TAB / "by_fiscal_year_musd.csv")

# 2. Countries outside the United States, all years.
abroad = df[df["where"] == "Outside the United States"]
ctry = by(["pop_country_name"], abroad).sort_values(ascending=False).rename("obligations_musd_fy2008_2026")
ctry.to_csv(TAB / "by_country_outside_us_musd.csv")

# 3. Iraq and Afghanistan by fiscal year (for comparison with the contractor census).
ia = by(["fiscal_year", "pop_country_name"], abroad[abroad["pop_country_name"].isin(["IRAQ", "AFGHANISTAN"])]).unstack(fill_value=0)
ia = ia.reindex(range(2008, 2027), fill_value=0)
ia.columns.name = None
ia.to_csv(TAB / "iraq_afghanistan_by_fiscal_year_musd.csv")

# 4. Agencies.
ag = by(["awarding_agency", "awarding_subagency"]).sort_values(ascending=False).rename("obligations_musd_fy2008_2026")
ag.to_csv(TAB / "by_agency_musd.csv")
top_sub = ag.groupby(level=1).sum().nlargest(8).index
ag_fy = by(["fiscal_year", "awarding_subagency"], df[df["awarding_subagency"].isin(top_sub)]).unstack(fill_value=0)
ag_fy.columns.name = None
ag_fy.to_csv(TAB / "top_subagencies_by_fiscal_year_musd.csv")

# 5. Companies (parent company where reported).
co = df.groupby("parent").agg(obligations_musd=("obligation_usd", lambda s: round(s.sum() / M, 2)),
                              awards=("award_key", "nunique")).sort_values("obligations_musd", ascending=False)
co.head(50).to_csv(TAB / "top50_companies_musd.csv")
co_ab = abroad.groupby("parent").agg(obligations_musd=("obligation_usd", lambda s: round(s.sum() / M, 2)),
                                     awards=("award_key", "nunique")).sort_values("obligations_musd", ascending=False)
co_ab.head(25).to_csv(TAB / "top25_companies_outside_us_musd.csv")

# Figure 1: total by fiscal year, split inside / outside the United States.
fig, ax = plt.subplots(figsize=(7.5, 3.8))
years = fy.index
ax.bar(years, fy.get("United States", 0) / 1000, color="0.35", label="Work in the United States")
ax.bar(years, fy.get("Outside the United States", 0) / 1000, bottom=fy.get("United States", 0) / 1000,
       color="0.75", label="Work outside the United States")
ax.set_ylabel("Obligations (billion US$, current)")
ax.set_xticks(list(years)[::2])
ax.legend(frameon=False, fontsize=8)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout(); fig.savefig(FIG / "guard_contracts_by_year.png", dpi=200)

# Figure 2: top countries outside the United States.
top = ctry.head(12).sort_values()
fig, ax = plt.subplots(figsize=(7, 4))
ax.barh([c.title() for c in top.index], top.values / 1000, color="0.35")
ax.set_xlabel("Obligations FY2008-FY2026 (billion US$, current)")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout(); fig.savefig(FIG / "top_countries_outside_us.png", dpi=200)

pd.set_option("display.width", 200)
print(fy.round(0).to_string())
print(ctry.head(12).round(0).to_string())
print(ia.round(1).to_string())
print(ag.head(12).round(0).to_string())
print(ag_fy.round(0).tail(4).T.to_string())
print(co.head(15).to_string())
print(co_ab.head(10).to_string())
