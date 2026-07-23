"""
Day 10-12: Trade-space visualization.

Reads data/trade_space_results.csv (produced by trade_space_search.py)
and produces the core trade-space chart: staffing cost vs. p90 wait
time, with pass/fail on all requirements marked. This is the chart
that ties the trade-space study together for the write-up.
"""

import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("data/trade_space_results.csv")

fig, ax = plt.subplots(figsize=(9, 6))

passing = df[df["all_requirements_pass"]]
failing = df[~df["all_requirements_pass"]]

ax.scatter(failing["cost"], failing["p90_wait_min"],
           c="#c0392b", alpha=0.5, label="Fails one or more requirements", s=50)
ax.scatter(passing["cost"], passing["p90_wait_min"],
           c="#27ae60", alpha=0.9, label="Meets all requirements (REQ-1/2/3)", s=70,
           edgecolors="black", linewidths=0.5)

# Highlight the baseline configuration (2 nurses, 16 bays, 4 physicians)
baseline = df[(df["triage_nurses"] == 2) & (df["treatment_bays"] == 16) & (df["physicians"] == 4)]
if len(baseline) > 0:
    ax.scatter(baseline["cost"], baseline["p90_wait_min"],
               marker="*", s=400, c="orange", edgecolors="black", linewidths=1,
               label="Baseline (2 nurses / 16 bays / 4 physicians)", zorder=5)

# Highlight the recommended cheapest fully-passing configuration
if len(passing) > 0:
    recommended = passing.sort_values("cost").iloc[[0]]
    ax.scatter(recommended["cost"], recommended["p90_wait_min"],
               marker="D", s=200, c="blue", edgecolors="black", linewidths=1,
               label=f"Recommended ({int(recommended['triage_nurses'].iloc[0])}N / "
                     f"{int(recommended['treatment_bays'].iloc[0])}B / "
                     f"{int(recommended['physicians'].iloc[0])}P)", zorder=5)

ax.set_xlabel("Weighted staffing cost (nurses x1.5 + bays x1.0 + physicians x4.0)")
ax.set_ylabel("90th percentile wait time (minutes)")
ax.set_title("ER Staffing Trade-Space: Cost vs. Wait-Time Performance")
ax.legend(loc="upper right", fontsize=9)
ax.grid(alpha=0.3)

plt.tight_layout()
plt.savefig("data/trade_space_chart.png", dpi=150)
print("Saved chart to data/trade_space_chart.png")

# Also print a quick summary table of the passing frontier, sorted by cost
if len(passing) > 0:
    print("\n=== Configurations meeting all requirements (sorted by cost) ===")
    print(passing.sort_values("cost")[
        ["triage_nurses", "treatment_bays", "physicians", "cost",
         "p90_wait_min", "avg_wait_min"]
    ].to_string(index=False))
