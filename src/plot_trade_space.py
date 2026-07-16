"""
Days 10-12: Trade-space visualization.

Plots weighted staffing cost against 90th-percentile wait time across
all searched configurations, colored by whether they meet all
requirements. This is the core trade-space chart for the write-up.
"""

import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("data/trade_space_results.csv")

fig, ax = plt.subplots(figsize=(9, 6))

passing = df[df["all_requirements_pass"]]
failing = df[~df["all_requirements_pass"]]

ax.scatter(failing["cost"], failing["p90_wait_min"], c="#d94f4f", alpha=0.6,
           label="Fails one or more requirements", s=50)
ax.scatter(passing["cost"], passing["p90_wait_min"], c="#2f9e44", alpha=0.8,
           label="Meets all requirements (REQ-1 to REQ-3)", s=70, edgecolors="black")

# Highlight the recommended (cheapest fully-passing) configuration
if len(passing) > 0:
    best = passing.sort_values("cost").iloc[0]
    ax.scatter([best["cost"]], [best["p90_wait_min"]], c="gold", s=200,
               edgecolors="black", zorder=5, marker="*",
               label=f"Recommended: {int(best['triage_nurses'])} nurses, "
                     f"{int(best['treatment_bays'])} bays, "
                     f"{int(best['physicians'])} physicians")

ax.axhline(y=75, color="gray", linestyle="--", linewidth=1, alpha=0.5,
           label="Acuity-3 REQ-2 target (75 min)")

ax.set_xlabel("Weighted staffing cost (relative units)")
ax.set_ylabel("90th percentile wait time (minutes)")
ax.set_title("ER Staffing Trade-Space: Cost vs. Wait Time Performance")
ax.legend(loc="upper right", fontsize=9)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("data/trade_space_chart.png", dpi=150)
print("Saved chart to data/trade_space_chart.png")

# ---- Also print a compact summary table for the write-up ----
print("\n=== All fully-passing configurations, sorted by cost ===")
cols = ["triage_nurses", "treatment_bays", "physicians", "cost", "p90_wait_min"]
print(passing[cols].sort_values("cost").to_string(index=False))
