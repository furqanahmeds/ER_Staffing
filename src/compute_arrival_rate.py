"""
Day 5 (fixed): Synthea generates each patient's full life history, so
encounters span ~100+ years -- averaging total encounters over that whole
span badly understates a realistic daily arrival rate. Fix: compute the
rate using only the most recent 365 days of simulated time, which better
approximates a "current state" snapshot of the population.
"""

import pandas as pd
import json

ed = pd.read_csv("data/ed_encounters_with_acuity.csv")
ed["START"] = pd.to_datetime(ed["START"])

# ---- Restrict to the most recent year of simulated time ----
most_recent = ed["START"].max()
one_year_ago = most_recent - pd.Timedelta(days=365)
recent = ed[ed["START"] >= one_year_ago].copy()

print(f"Most recent encounter date: {most_recent.date()}")
print(f"Encounters in most recent year: {len(recent)} (out of {len(ed)} total)")

avg_arrivals_per_day = len(recent) / 365
print(f"Average arrivals/day (recent year only): {avg_arrivals_per_day:.2f}")

# ---- Hour-of-day distribution (use full dataset -- shape is stable
#      regardless of time window, more data = smoother pattern) ----
ed["hour"] = ed["START"].dt.hour
hourly_counts = ed["hour"].value_counts().sort_index()
hourly_fraction = (hourly_counts / hourly_counts.sum()).to_dict()

# ---- Sanity flag ----
# A population of 5,000 synthetic patients is far smaller than a real
# hospital's ED catchment area, so this recent-year rate will likely
# still be lower than a real mid-size ED (typically 100-200 arrivals/day).
# Document this explicitly: this simulation reflects a small ED or a
# scaled-down scenario, not a claim about a specific real hospital's
# actual volume.

arrival_config = {
    "avg_arrivals_per_day": round(avg_arrivals_per_day, 2),
    "hourly_fraction": {str(h): round(hourly_fraction.get(h, 0), 4) for h in range(24)},
    "note": "Rate computed from most recent 365 days of Synthea's 5000-patient "
            "population. Small population size means this reflects a "
            "small/scaled-down ED scenario, not a specific real hospital.",
}

with open("data/arrival_rate.json", "w") as f:
    json.dump(arrival_config, f, indent=2)

print("\nSaved to data/arrival_rate.json")