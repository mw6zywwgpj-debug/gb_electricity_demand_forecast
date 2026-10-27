#!/usr/bin/env python3
"""Recalculate the saved forecast comparison and draw two simple figures.

This does not retrain the models or fetch any external market data.
"""
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)

d = pd.read_csv(DATA / "matched_forecasts.csv")
b = pd.read_csv(DATA / "december_experiments.csv")
required = ["Date", "Settlement_Period", "actual_MW", "temporal_MW", "memory_MW", "neso_MW"]
assert all(c in d.columns for c in required), "Missing prediction columns"
assert len(d) == 5848 and d.Date.nunique() == 122, "Unexpected sample coverage"
assert not d.duplicated(["Date", "Settlement_Period"]).any(), "Duplicate periods"

names = {"temporal_MW": "Multi-scale temporal", "memory_MW": "Condition-matched memory", "neso_MW": "NESO forecast"}
d["month"] = d["Date"].str.slice(0, 7)
mae = pd.DataFrame(index=sorted(d.month.unique()))
for col, name in names.items():
    d[name] = (d[col] - d.actual_MW).abs()
    mae[name] = d.groupby("month")[name].mean()
    print(f"{name:27s}  pooled MAE = {d[name].mean():7.1f} MW")
assert abs(d["temporal_MW"].sub(d.actual_MW).abs().mean()-802.36363) < .1
assert abs(d["memory_MW"].sub(d.actual_MW).abs().mean()-790.86047) < .1
assert abs(d["neso_MW"].sub(d.actual_MW).abs().mean()-740.17254) < .1
assert abs(b.loc[b.approach=='Multi-scale temporal','mae_MW'].iloc[0] - mae.loc['2025-12','Multi-scale temporal']) < .1
assert abs(b.loc[b.approach=='Condition-matched memory','mae_MW'].iloc[0] - mae.loc['2025-12','Condition-matched memory']) < .1

plt.rcParams.update({"font.size": 10, "savefig.dpi": 170})
fig, ax = plt.subplots(figsize=(9, 4.5))
labels = b.approach.to_list()
values = b.mae_MW.to_list()
colors = ["#a8afb5"]*5 + ["#466b83", "#688b87", "#424b55"]
y = list(range(len(labels)))
ax.barh(y, values, color=colors, height=.66)
ax.set_yticks(y, labels)
ax.invert_yaxis()
ax.set_xlim(0, max(values)*1.15)
ax.set_xlabel("Mean absolute error (MW) · lower is better")
ax.set_title("December 2025: exploring the forecasting approaches", loc="left", fontsize=12)
for yi, val in zip(y,values): ax.text(val+20, yi, f"{val:,.0f}", va="center", fontsize=9)
ax.spines[['top','right','left']].set_visible(False)
ax.tick_params(axis='y',length=0)
ax.grid(axis='x',alpha=.13)
ax.set_axisbelow(True)
fig.tight_layout()
fig.savefig(FIG/'01_december_progression.png',bbox_inches='tight')
plt.close(fig)

fig, ax = plt.subplots(figsize=(8.6, 4.5))
xs = list(range(len(mae)))
for name, color, mark in [("Multi-scale temporal", "#466b83", "o"),
                          ("Condition-matched memory", "#688b87", "s"),
                          ("NESO forecast", "#424b55", "^")]:
    ax.plot(xs, mae[name], marker=mark, linewidth=2, markersize=5, label=name, color=color)
ax.set_xticks(xs,["Dec 2025", "Apr 2026", "Jun 2026", "Aug 2026"])
ax.set_ylabel("MAE (MW) · lower is better")
ax.set_title("Same settlement periods: monthly forecast errors", loc="left", fontsize=12)
ax.spines[['top','right']].set_visible(False)
ax.grid(axis='y',alpha=.18)
ax.legend(frameon=False,loc='upper left',fontsize=9)
fig.tight_layout()
fig.savefig(FIG/'02_matched_months.png',bbox_inches='tight')
plt.close(fig)
print('Figures written to figures/.')
