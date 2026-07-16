
# ER Staffing 
A discrete-event simulation of ER patient flow, built to explore staffing 
trade-offs under demand constraints. Applies a systems engineering approach: 
formal requirements, architecture modeling, and verification/validation.
## Project Status

Days 1–7 of a 14-day build complete: data pipeline, calibration, system
architecture, baseline SimPy model, and bottleneck analysis are done.
Trade-space staffing exploration (Days 10–12) and final write-up
(Days 13–14) are in progress.

## Data Validation & Modeling Decisions

This project surfaced several real data-quality issues during
development, each resolved with a documented modeling decision rather
than silently patched:

- **Synthea LOS contamination:** Synthea's encounter-level length-of-stay
  field conflates ED time with downstream inpatient admission time,
  making it unusable directly as a service-time distribution. Resolved
  by using NHAMCS published median wait/treatment times instead.
- **Acuity mapping bug:** an early keyword-based acuity classifier
  defaulted ~60% of encounters to a single acuity level due to
  incomplete keyword coverage. Diagnosed and fixed by expanding keyword
  coverage based on the actual unmatched diagnosis text found in the data.
- **Residual acuity-mix mismatch:** even after the fix, Synthea's
  acuity distribution still diverged meaningfully from NHAMCS national
  benchmarks. Decision: NHAMCS's published acuity mix drives the
  simulation's patient arrivals; Synthea provides arrival timing/volume
  shape and validated the plausibility of service-time assumptions.
- **Arrival volume scaling:** Synthea's small synthetic population
  (5,000 patients) produced an unusably low recent-year arrival rate
  (~2.24/day). Decision: use a documented target of 150 arrivals/day
  (a mid-size ED benchmark, grounded in the national NHAMCS ED visit
  rate), while retaining Synthea's real hourly arrival-timing shape.
- **Physician vs. bay occupancy modeling:** treatment time (from NHAMCS)
  reflects total ED length of stay, not exclusive physician contact
  time. Modeled physicians as holding a shorter contact-time portion
  (~20% of total treatment time, a documented assumption) while the
  bay remains occupied for the full duration — this reflects realistic
  ED workflow and avoids overstating physician demand.

All of these are documented as explicit, defensible modeling
assumptions rather than claims of ground-truth accuracy. See
`src/diagnose_los.py`, `src/diagnose_acuity_mapping.py`,
`src/calibrate_nhamcs.py`, and `src/finalize_arrival_mix.py` for the
full diagnostic trail.

## Baseline Results (Day 7)
Baseline staffing (2 triage nurses, 16 treatment bays, 4 physicians)
was checked against the formal requirements below.

| Requirement | Result | Status |
|---|---|---|
| REQ-1: 90% triaged within 10 min | 100.0% | PASS |
| REQ-2: Acuity 1 seen within 20 min (90% target) | 69.8% | FAIL |
| REQ-2: Acuity 2 seen within 40 min (90% target) | 69.4% | FAIL |
| REQ-2: Acuity 3 seen within 75 min (90% target) | 13.7% | FAIL |
| REQ-2: Acuity 4 seen within 150 min (90% target) | 100.0%* | FAIL (see note) |
| REQ-3: No patient waits >240 min, any acuity | 38.6% exceeded | FAIL |
| REQ-4: Holds under +20% surge | Not yet tested | TBD |

*Acuity 4's apparent 100% pass is a data artifact, not a real pass:
because acuity 4 is lowest-priority in the treatment bay queue, almost
none of these patients complete their full journey within the
simulated week — the few that do are a biased, faster-than-typical
subset. This is a right-censoring effect, not evidence the requirement
is met; if anything it indicates acuity 4 patients are the most
underserved group in the baseline.

**Resource utilization:**

| Resource | Capacity | Utilization |
|---|---|---|
| Triage nurses | 2 | 26.8% |
| Treatment bays | 16 | 91.5% |
| Physicians | 4 | 75.0% |

**Finding:** treatment bay capacity is the primary system bottleneck,
driving the REQ-2/REQ-3 failures above. Physician capacity is a
secondary constraint. Triage nurse capacity is substantially
over-provisioned relative to demand, suggesting a reallocation
opportunity to explore in the trade-space phase rather than simply
adding headcount everywhere.

## Surge Test (Day 8) — REQ-4
Baseline staffing (2 nurses, 16 bays, 4 physicians) was re-run at +20%
demand to test REQ-4.

| Requirement | Baseline | +20% Surge |
|---|---|---|
| REQ-1: Triage within 10 min | ✅ 100% | ✅ 100% |
| REQ-2: Acuity 1 within 20 min | ❌ 69.8% | ❌ 75.3% |
| REQ-2: Acuity 2 within 40 min | ❌ 69.4% | ❌ 69.1% |
| REQ-2: Acuity 3 within 75 min | ❌ 13.7% | ❌ 0.0% |
| REQ-2: Acuity 4 within 150 min | ⚠️ 100%* | ⚠️ fully censored* |
| REQ-3: No wait over 4 hrs | ❌ 38.6% exceeded | ❌ 37.5% exceeded |
|

## Requirements
- **REQ-1:** 90% of patients triaged within 10 minutes of arrival.
- **REQ-2 (acuity-tiered treatment SLA):** 90% of patients seen by a
  physician within the following targets, anchored to NHAMCS median
  wait times by triage level:
  - Level 1 (immediate): 20 minutes
  - Level 2 (emergent): 40 minutes
  - Level 3 (urgent): 75 minutes
  - Level 4 (semiurgent): 150 minutes
- **REQ-3:** No patient waits more than 4 hours (240 minutes) for
  treatment, regardless of acuity level. This is a hard outer ceiling,
  distinct from the primary SLA in REQ-2.
- **REQ-4:** The system maintains REQ-1 through REQ-3 under a +20%
  demand surge above baseline arrival volume.

*Note: REQ-2/REQ-3 were revised from an earlier uniform 2-hour wait
target after baseline testing showed a single ceiling doesn't reflect
real ED triage practice — see write-up for the full rationale.*

## Status
Work in progress — Day 1 of build.

## Data Sources
- Synthea (synthetic patient data) — version/seed TBD
- NHAMCS (CDC aggregate ED benchmarks)

## Reproducibility
- Synthea commit: 2b0a55bab0ab9ae22204320c80f5880ceb8925aa
- Random seed: 12345
- Population size: 5000
- Generated: July 2026