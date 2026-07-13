"""
Day 5 (final): Arrival rate decision.

FINDING:
Synthea's 5,000-patient population, even restricted to the most recent
year, produces only ~2.24 arrivals/day -- unusably low, because Synthea
generates each patient's full life history and 5,000 patients is a small
population base relative to a real hospital's ED catchment area.

DECISION:
Same pattern as the Day 3 acuity-mix decision -- use an external,
documented benchmark for the volume Synthea can't reliably provide:

  - Target arrival rate: 150 patients/day, representing a mid-size ED.
    Grounded in the national ED visit rate of 47 visits per 100 people/year
    (NHAMCS 2022 national summary), scaled to a mid-size hospital
    catchment population.
  - Synthea's hour-of-day distribution is retained as-is -- this shape
    (evening peaks, midday bump) is a real, usable pattern independent
    of the population-size problem that affects the absolute rate.

This is a documented scope decision: the simulation represents a
mid-size ED scenario, not a specific real hospital's actual volume.
State this plainly in the write-up's data caveats section.
"""

import pandas as pd
import json

ed = pd.read_csv("data/ed_encounters_with_acuity.csv")
ed["START"] = pd.to_datetime(ed["START"])

# ---- Hourly shape from Synthea (kept as-is, this part is valid) ----
ed["hour"] = ed["START"].dt.hour
hourly_counts = ed["hour"].value_counts().sort_index()
hourly_fraction = (hourly_counts / hourly_counts.sum()).to_dict()

# ---- Documented target volume (external benchmark, not from Synthea) ----
TARGET_ARRIVALS_PER_DAY = 150

arrival_config = {
    "avg_arrivals_per_day": TARGET_ARRIVALS_PER_DAY,
    "hourly_fraction": {str(h): round(hourly_fraction.get(h, 0), 4) for h in range(24)},
    "source": "Target volume (150/day) is a documented assumption representing "
              "a mid-size ED, grounded in NHAMCS 2022 national ED visit rate "
              "(47 per 100 people/year). Synthea's population was too small "
              "(5000 patients, ~2.24 recent-year arrivals/day) to provide a "
              "realistic absolute rate directly. Hourly distribution shape "
              "is retained from Synthea as it remains valid independent of "
              "population size.",
}

with open("data/arrival_rate.json", "w") as f:
    json.dump(arrival_config, f, indent=2)

print(f"Target arrivals/day: {TARGET_ARRIVALS_PER_DAY}")
print("\nHourly fraction distribution:")
for h in range(24):
    frac = hourly_fraction.get(h, 0)
    approx_arrivals = frac * TARGET_ARRIVALS_PER_DAY
    print(f"  {h:02d}:00  {frac:.4f}  (~{approx_arrivals:.1f} patients/hr)")

print("\nSaved to data/arrival_rate.json")
