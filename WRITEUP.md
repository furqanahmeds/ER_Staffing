# ER Staffing Simulation: A Systems Engineering Approach

**Author:** Furqan Ahmed | Texas A&M ISEN | Systems Engineering focus

## Summary

This project models emergency room patient flow as a system with defined
requirements, identifies the primary capacity bottleneck through
simulation, and recommends a staffing configuration that meets all
wait-time requirements — including under a demand surge — at the lowest
additional cost. Baseline staffing produced 90th-percentile wait times
exceeding 21 hours; the recommended configuration reduces this to under
2 minutes at roughly 34% higher weighted staffing cost, driven primarily
by a treatment-bay capacity increase rather than uniform headcount growth.

This is the core deliverable. The sections below walk through the
process that produced it, following a systems engineering methodology:
architecture, requirements, model, verification & validation (V&V),
trade-space study, and recommendation.

---

## 1. System Architecture

The ER is modeled as a system of three resource subsystems that a
patient flows through sequentially, with staffing levels as the
controllable input:

```
                    +-------------------+
  Patient arrivals  |   Staffing levels  |  (control input,
  (by acuity level) |  (nurses/bays/docs)|   varied in trade study)
        |            +-------------------+
        v                      |
  [ Triage (nurse) ] --------> [ Treatment bay (priority queue) ] --> [ Physician ] --> Disposition
                                                                                          (discharge/admit)
```

- **Triage:** every patient is assessed by a nurse on arrival.
- **Treatment bay:** a priority-queued resource — higher-acuity (more
  urgent) patients are seen first, regardless of arrival order.
- **Physician:** holds a shorter "contact time" within the bay stay
  (assessment/direction of care), not the full treatment duration —
  see modeling decisions below.
- **Disposition:** patients exit the modeled system on discharge.
  Admissions (patients whose care continues beyond the ED) are treated
  as a separate downstream system, out of scope — see Section 3.

## 2. Requirements

| ID | Requirement |
|---|---|
| REQ-1 | 90% of patients triaged within 10 minutes of arrival |
| REQ-2 | Acuity-tiered treatment SLA (90% of patients seen within target, by triage level): Level 1 — 20 min, Level 2 — 40 min, Level 3 — 75 min, Level 4 — 150 min |
| REQ-3 | No patient waits more than 240 minutes (4 hrs) for treatment, regardless of acuity |
| REQ-4 | System maintains REQ-1–3 under a +20% demand surge |

REQ-2/REQ-3 targets are anchored to published NHAMCS median wait times
by triage level (CDC, most recent complete triage-level breakdown,
2010–2011 data — see Section 3 for the caveat on data currency).

**Revision note:** REQ-2/3 originally used a single uniform 2-hour wait
ceiling for all patients. This was revised after early testing showed a
flat ceiling doesn't reflect real ED triage practice, where wait-time
tolerance is acuity-dependent. The tiered version above is more clinically
realistic and is the version tested throughout this report.

## 3. Data Sources & Modeling Decisions

Two data sources were used, each for a different purpose, following a
decision made explicitly after diagnosing limitations in the raw data:

| Source | Used for | Why |
|---|---|---|
| **Synthea** (synthetic patient generator) | Arrival timing shape (hour-of-day pattern) | Real, plausible hourly variation; not usable for absolute volume or acuity mix (see below) |
| **NHAMCS** (CDC national ED survey) | Acuity mix, service-time distributions, arrival volume benchmark | Real national aggregate data; used to compensate for Synthea's small-sample and data-structure limitations |

**Reproducibility:** Synthea commit `2b0a55bab0ab9ae22204320c80f5880ceb8925aa`, random seed `12345`, population size 5,000.

Four data issues were found and resolved during development, each
handled with a documented, defensible decision rather than a silent fix:

1. **Synthea's length-of-stay field conflates ED time with inpatient
   admission time.** A single encounter's START/STOP timestamps span
   the entire hospital stay, not just ED treatment — verified by
   inspecting outlier encounters (up to 962 hours), which corresponded
   to admission-coded diagnoses (sepsis, overdose, etc.). *Resolution:*
   NHAMCS published median wait/treatment times are used for service-time
   distributions instead of Synthea's raw LOS field.

2. **Acuity classification bug.** An initial keyword-based mapping from
   diagnosis text to a 1–4 acuity scale defaulted ~60% of encounters to
   a single level because the keyword list had incomplete coverage.
   Diagnosed by inspecting the actual unmatched diagnosis text (e.g.,
   "cerebrovascular accident" wasn't recognized as a stroke synonym).
   *Resolution:* keyword coverage expanded based on the real unmatched
   terms found in the data, reducing unclassified encounters from ~60%
   to ~25% (the remainder had no reason code at all).

3. **Residual acuity-mix mismatch.** Even after the fix, Synthea's
   acuity distribution (2.8% / 26.3% / 59.4% / 11.5% across levels 1–4)
   still diverged materially from NHAMCS's national target (15% / 27% /
   42.5% / 15.5%). Rather than continuing to tune keywords to force a
   match — which would cross from data validation into fitting the data
   to a predetermined answer — the decision was made to use NHAMCS's
   published mix directly to drive simulated patient arrivals.

4. **Arrival volume too low to be usable.** Synthea's small synthetic
   population (5,000 patients, spanning full synthetic lifespans)
   produced a recent-year arrival rate of ~2.24 patients/day — far below
   any real single-facility ED. *Resolution:* a documented target of 150
   arrivals/day (a mid-size ED benchmark grounded in the national NHAMCS
   ED visit rate) was used for volume, while retaining Synthea's real
   hourly arrival-timing shape.

**Additional modeling assumption:** physicians are modeled as holding a
resource for only ~20% of the total treatment duration (a documented
estimate, not directly observed data), reflecting that a physician's
active contact time with a patient is shorter than the patient's total
bay occupancy (which includes nursing care, monitoring, and tests).
Without this distinction, the model overstated physician demand and
produced an artificially unstable system.

**Caveats carried into every result below:** Synthea data is synthetic,
not real patient records. NHAMCS triage-level benchmarks are from
2010–2011 survey data with documented imputation for ~19.5% of records.
This project demonstrates a systems engineering methodology applied to
a representative problem — it is not a validated operational
recommendation for any specific real facility.

## 4. Baseline Verification

Baseline staffing (2 triage nurses, 16 treatment bays, 4 physicians —
sized from initial queuing-theory estimates) was tested against REQ-1–3:

| Requirement | Result | Status |
|---|---|---|
| REQ-1: 90% triaged within 10 min | 100.0% | Pass |
| REQ-2: Acuity 1 within 20 min | 69.8% | Fail |
| REQ-2: Acuity 2 within 40 min | 69.4% | Fail |
| REQ-2: Acuity 3 within 75 min | 13.7% | Fail |
| REQ-2: Acuity 4 within 150 min | 100.0%* | Fail (see note) |
| REQ-3: No wait over 240 min | 38.6% exceeded | Fail |

*Acuity 4's apparent 100% pass is a statistical artifact (right-censoring),
not a real pass: because acuity 4 is lowest-priority in the treatment
queue, almost no level-4 patients complete their full journey within the
simulated week — the few that do are a small, faster-than-typical biased
sample. This indicates acuity 4 patients are likely the most underserved
group, not the best-served.

**Resource utilization:**

| Resource | Capacity | Utilization |
|---|---|---|
| Triage nurses | 2 | 26.8% |
| Treatment bays | 16 | **91.5%** |
| Physicians | 4 | 75.0% |

**Root cause:** treatment bay capacity is the binding constraint,
running near the utilization threshold where queuing delay grows
sharply nonlinear. Triage capacity is substantially over-provisioned —
a reallocation opportunity, not just a case for adding more of
everything.

## 5. Surge Test (REQ-4)

Baseline staffing was re-run at +20% arrival volume:

| Requirement | Baseline | +20% Surge |
|---|---|---|
| REQ-1 | 100% | 100% |
| REQ-2 Acuity 1 | 69.8% | 75.3% |
| REQ-2 Acuity 2 | 69.4% | 69.1% |
| REQ-2 Acuity 3 | 13.7% | **0.0%** |
| REQ-2 Acuity 4 | 100%* | fully censored* |
| REQ-3 | 38.6% exceeded | 37.5% exceeded |
| **REQ-4 (overall)** | — | **Fail** |

Because baseline bay capacity was already near saturation, the surge did
not increase completed patient throughput (both runs completed a similar
patient count) — it lengthened queues instead. The system is
capacity-limited, not demand-limited: additional demand on top of an
already-saturated system worsens outcomes for the lowest-priority
patients disproportionately (acuity 3 collapsed from 13.7% to 0% meeting
target). Baseline staffing has effectively zero slack to absorb a surge.

## 6. Trade-Space Exploration

75 staffing configurations were evaluated (2–3 triage nurses, 16–24
treatment bays, 4–8 physicians), each scored against REQ-1–3 and a
weighted staffing cost (physicians weighted 4x, nurses 1.5x, bays 1x —
a documented relative-cost assumption, not real wage data, reflecting
physicians' higher labor cost relative to nurses and bays being closer
to a capital/space cost than an hourly labor cost).

**10 of 75 configurations met all requirements.** Every passing
configuration used 22 or 24 treatment bays — confirming bay capacity as
the binding constraint identified in Section 4. Above that bay-capacity
floor, nurse and physician counts traded off more flexibly.

**Recommended configuration:** 2 triage nurses, 24 treatment bays, 5
physicians — the cheapest fully-passing configuration found.

| Metric | Baseline | Recommended | Change |
|---|---|---|---|
| Triage nurses | 2 | 2 | — |
| Treatment bays | 16 | 24 | +8 |
| Physicians | 4 | 5 | +1 |
| Weighted cost | 35.0 | 47.0 | +34% |
| 90th percentile wait | 1,265 min (~21 hrs) | 1.8 min | −99.9% |
| All requirements pass | No | Yes | — |

See `data/trade_space_chart.png` for the full cost-vs-performance
frontier across all 75 configurations.

## 7. Recommendation

Increase treatment bay capacity from 16 to 24 and add one physician (4→5),
keeping triage nursing unchanged at 2. This is a targeted capacity
investment (~34% higher weighted staffing cost than baseline) rather
than uniform headcount growth, and it fully resolves the wait-time
requirement failures identified in the baseline — including under a
20% demand surge, which the baseline configuration could not absorb at all.

The dramatic wait-time reduction (21+ hours to under 2 minutes) reflects
how severely undersized the baseline configuration was relative to
modeled demand, not an unusually large intervention — the recommended
configuration is the *cheapest* option in the search grid that meets
every requirement, not the most aggressive one.

## 8. Limitations & Future Work

- Synthetic (Synthea) and aggregate national (NHAMCS) data stand in for
  a real facility's patient population; a production deployment would
  need validation against a specific hospital's actual patient mix and
  historical volumes.
- The physician contact-time fraction (20%) and cost weights are
  documented estimates, not measured values — sensitivity analysis on
  these assumptions is a natural next step.
- A follow-on cost model — staffing cost per shift-hour vs. the
  estimated cost of SLA violations (patient harm risk, reputational
  cost, left-without-being-seen rates) — would turn this from a
  technical exercise into a full business-decision tool.

## Repository

Code, data, and full diagnostic trail: https://github.com/furqanahmeds/ER_Staffing

Key scripts: `src/build_acuity_mapping.py`, `src/diagnose_los.py`,
`src/calibrate_nhamcs.py`, `src/finalize_arrival_mix.py`,
`src/simpy_model_skeleton.py`, `src/check_requirements.py`,
`src/stress_test.py`, `src/trade_space_search.py`,
`src/trade_space_chart.py`
