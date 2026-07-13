"""
Day 7: Check baseline simulation results against formal requirements.

REQ-1: 90% of patients triaged within 10 min of arrival
REQ-2: Acuity-tiered treatment SLA (90% seen within target, by level)
REQ-3: No patient waits more than 240 min (4 hrs) for treatment, any acuity
REQ-4: System maintains REQ-1-3 under +20% demand surge (checked separately,
       requires a second simulation run -- see stress_test.py, not yet built)
"""

import pandas as pd

df = pd.read_csv("data/simulation_results_baseline.csv")

WARMUP_MIN = 60 * 24
steady = df[df["arrival_time"] >= WARMUP_MIN].copy()

REQ2_TARGETS_MIN = {1: 20, 2: 40, 3: 75, 4: 150}
REQ3_CEILING_MIN = 240

print("=== REQ-1: 90% triaged within 10 min ===")
steady["triage_duration_min"] = steady["triage_start"].sub(steady["arrival_time"])
# Note: triage duration itself isn't in current CSV columns explicitly as
# "time to START triage" -- using triage_start - arrival_time as the
# wait-to-begin-triage metric, which is what REQ-1 is actually about.
triage_wait = steady["triage_start"] - steady["arrival_time"]
pct_within_10 = (triage_wait <= 10).mean() * 100
print(f"% triaged within 10 min: {pct_within_10:.1f}%  "
      f"({'PASS' if pct_within_10 >= 90 else 'FAIL'})")

print("\n=== REQ-2: Acuity-tiered treatment SLA (90% seen within target) ===")
for acuity, target in REQ2_TARGETS_MIN.items():
    subset = steady[steady["acuity"] == acuity]["wait_time_min"]
    if len(subset) == 0:
        print(f"Acuity {acuity}: no completed patients in steady-state window "
              f"(likely still queued -- see censoring note in write-up)")
        continue
    pct_within = (subset <= target).mean() * 100
    status = "PASS" if pct_within >= 90 else "FAIL"
    print(f"Acuity {acuity} (target {target} min): {pct_within:.1f}% within target  ({status})")

print("\n=== REQ-3: No patient waits more than 240 min, any acuity ===")
over_ceiling = (steady["wait_time_min"] > REQ3_CEILING_MIN).sum()
pct_over = over_ceiling / len(steady) * 100
print(f"Patients exceeding 240 min wait: {over_ceiling} ({pct_over:.1f}%)  "
      f"({'PASS' if over_ceiling == 0 else 'FAIL'})")

print("\n=== REQ-4: Not yet checked -- requires a +20% surge simulation run ===")
