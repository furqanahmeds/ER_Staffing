"""
Sets the arrival rate the simulation uses.

Ran into a problem here: Synthea's 5,000-patient population, even
limited to the most recent year of encounters, only works out to about
2.24 arrivals/day. Synthea generates each patient's entire life history,
so 5,000 patients spread across decades ends up being way too small a
base to produce a realistic single-ED volume.

Same fix as the acuity-mix issue -- pull the volume from an external
benchmark instead of trying to force Synthea to produce it:

  - Target rate: 150 patients/day, roughly a mid-size ED. Based this on
    the national ED visit rate (47 visits per 100 people/year, NHAMCS
    2022) scaled to a mid-size hospital's catchment population.
  - Kept Synthea's hour-of-day shape as-is, since that part (evening
    peaks, midday bump) looks realistic and isn't affected by the
    population-size problem -- that's specific to the absolute count.

So to be clear: this represents a plausible mid-size ED, not the actual
volume of any real hospital. That's a scope choice, not a hidden gap.
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
    "source": "Target volume (150/day) represents a mid-size ED, based on the "
              "NHAMCS 2022 national ED visit rate (47 per 100 people/year). "
              "Synthea's population was too small "
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
