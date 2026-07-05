"""
Day 3: NHAMCS Calibration

Purpose:
1. Compare Synthea's derived acuity-level mix against published NHAMCS
   national benchmarks (validation check).
2. Derive lognormal distribution parameters for wait time and treatment
   time by acuity level, anchored to NHAMCS median values, since Synthea's
   own LOS field is contaminated by inpatient admission time (see Day 2
   diagnostic finding).

IMPORTANT MODELING ASSUMPTION:
NHAMCS publishes MEDIAN wait/treatment times by triage level, but not
full distribution shapes in the publicly available summary tables used
here. To build a SimPy-usable distribution, we assume a lognormal shape
(standard for right-skewed service-time data in queuing literature) and
choose a dispersion parameter (sigma) representative of typical ED
variability. This is a documented assumption, not a directly observed
NHAMCS statistic -- flag this explicitly in the write-up.

Sources:
- CDC NCHS QuickStats, NHAMCS 2010-2011 (median wait/treatment by triage level)
- Horeczko et al., "A Method for Grouping ED Visits by Severity and Complexity"
  (NHAMCS-ESI derived wait/LOS by level)
"""

import pandas as pd
import numpy as np
import json

# ---- Load Synthea-derived data ----
ed = pd.read_csv("data/ed_encounters_with_acuity.csv")

# ---- Synthea acuity mix (your data) ----
synthea_mix = ed["ACUITY"].value_counts(normalize=True).sort_index() * 100
print("=== Synthea acuity-level mix (%) ===")
print(synthea_mix.round(1))

# ---- NHAMCS target benchmarks ----
# Note: NHAMCS uses a 5-level scale (1=immediate ... 5=nonurgent).
# Synthea's keyword-based mapping only produced levels 1-4 in your data
# (no encounters classified as level 5 / nonurgent), which makes sense
# since true "emergency" class encounters skew toward higher acuity.
# We therefore compare only across levels 1-4 and note the absence of
# level 5 as an expected artifact of filtering to ENCOUNTERCLASS='emergency'.

nhamcs_target_mix_pct = {
    1: 15.0,   # immediate - interpolated estimate, see write-up caveat
    2: 27.0,   # emergent  - interpolated estimate
    3: 42.5,   # urgent    - directly reported (Horeczko et al.)
    4: 15.5,   # semiurgent - interpolated estimate
}

nhamcs_median_wait_min = {
    1: 13,
    2: 16,
    3: 20,
    4: 22,
}

nhamcs_median_treatment_min = {
    1: 200,
    2: 130,
    3: 100,
    4: 90,
}

# ---- Comparison table ----
print("\n=== Synthea vs NHAMCS acuity mix comparison ===")
comparison = pd.DataFrame({
    "synthea_pct": synthea_mix.round(1),
    "nhamcs_target_pct": pd.Series(nhamcs_target_mix_pct),
})
comparison["diff"] = (comparison["synthea_pct"] - comparison["nhamcs_target_pct"]).round(1)
print(comparison)

# ---- Derive lognormal distribution parameters ----
# For a lognormal distribution, median = exp(mu) --> mu = ln(median)
# Sigma (dispersion) is assumed based on typical ED wait/treatment time
# variability reported in queuing/health-ops literature. Higher acuity
# levels tend to have MORE variable treatment times (wider range of
# interventions), so sigma increases slightly as acuity increases (1=worst).

ASSUMED_SIGMA_WAIT = {1: 0.7, 2: 0.65, 3: 0.6, 4: 0.55}
ASSUMED_SIGMA_TREATMENT = {1: 0.9, 2: 0.75, 3: 0.6, 4: 0.5}

distribution_params = {}
for level in [1, 2, 3, 4]:
    wait_median = nhamcs_median_wait_min[level]
    treat_median = nhamcs_median_treatment_min[level]

    distribution_params[level] = {
        "wait_time_lognormal": {
            "mu": round(np.log(wait_median), 4),
            "sigma": ASSUMED_SIGMA_WAIT[level],
            "median_min": wait_median,
        },
        "treatment_time_lognormal": {
            "mu": round(np.log(treat_median), 4),
            "sigma": ASSUMED_SIGMA_TREATMENT[level],
            "median_min": treat_median,
        },
    }

print("\n=== Derived distribution parameters (for SimPy model) ===")
print(json.dumps(distribution_params, indent=2))

# ---- Save for use in the SimPy model ----
with open("data/service_time_distributions.json", "w") as f:
    json.dump(distribution_params, f, indent=2)

print("\nSaved to data/service_time_distributions.json")

# ---- Quick sanity check: sample from distributions ----
print("\n=== Sanity check: 5 sampled treatment times per acuity level ===")
rng = np.random.default_rng(seed=12345)  # same seed for reproducibility
for level in [1, 2, 3, 4]:
    params = distribution_params[level]["treatment_time_lognormal"]
    samples = rng.lognormal(mean=params["mu"], sigma=params["sigma"], size=5)
    print(f"Acuity {level}: {np.round(samples, 1)} (target median: {params['median_min']})")
