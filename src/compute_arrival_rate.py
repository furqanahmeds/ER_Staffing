"""
Day 5: Derive arrival rate and hour-of-day arrival pattern from Synthea's
ED encounter timestamps. This is the "arrival timing" half of the Day 3
decision (NHAMCS drives acuity mix, Synthea drives arrival timing/volume).
"""

import pandas as pd
import json

ed = pd.read_csv("data/ed_encounters_with_acuity.csv")
ed["START"] = pd.to_datetime(ed["START"])

# ---- Overall average arrivals per day ----
date_range_days = (ed["START"].max() - ed["START"].min()).days
avg_arrivals_per_day = len(ed) / date_range_days
print(f"Date range: {date_range_days} days")
print(f"Total ED encounters: {len(ed)}")
print(f"Average arrivals/day: {avg_arrivals_per_day:.2f}")

# ---- Hour-of-day distribution (captures realistic surge patterns) ----
ed["hour"] = ed["START"].dt.hour
hourly_counts = ed["hour"].value_counts().sort_index()
hourly_fraction = (hourly_counts / hourly_counts.sum()).to_dict()

print("\nHour-of-day arrival distribution (fraction of daily volume):")
for hour in range(24):
    frac = hourly_fraction.get(hour, 0)
    print(f"  {hour:02d}:00  {frac:.4f}  {'#' * int(frac * 200)}")

# ---- Save for use in the SimPy arrival process ----
arrival_config = {
    "avg_arrivals_per_day": round(avg_arrivals_per_day, 2),
    "hourly_fraction": {str(h): round(hourly_fraction.get(h, 0), 4) for h in range(24)},
}

with open("data/arrival_rate.json", "w") as f:
    json.dump(arrival_config, f, indent=2)

print("\nSaved to data/arrival_rate.json")
