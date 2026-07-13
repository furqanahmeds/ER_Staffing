"""
Day 5-6: Complete SimPy model -- entities, resources, arrival process,
and a baseline simulation run.

Structure matches the system architecture diagram:
  Patient arrivals -> Triage -> Treatment bay -> Physician -> Disposition

Data inputs (all derived/calibrated in Days 1-5):
  data/arrival_mix.json              -- acuity mix (NHAMCS-derived)
  data/arrival_rate.json             -- daily volume + hourly shape
  data/service_time_distributions.json -- wait/treatment lognormal params
"""

import simpy
import numpy as np
import json
import pandas as pd

RANDOM_SEED = 12345

# ---- Load calibrated data ----
with open("data/arrival_mix.json") as f:
    ARRIVAL_MIX = json.load(f)  # {"1": 15.0, "2": 27.0, "3": 42.5, "4": 15.5}

with open("data/arrival_rate.json") as f:
    ARRIVAL_RATE = json.load(f)  # avg_arrivals_per_day, hourly_fraction

with open("data/service_time_distributions.json") as f:
    SERVICE_TIMES = json.load(f)  # lognormal params by acuity level

ACUITY_LEVELS = [int(k) for k in ARRIVAL_MIX.keys()]
ACUITY_WEIGHTS = [ARRIVAL_MIX[str(a)] for a in ACUITY_LEVELS]

# ---- Staffing configuration (the control variable, varied in Days 10-12) ----
STAFFING = {
    "triage_nurses": 2,
    "treatment_bays": 8,
    "physicians": 3,
}

SIM_DURATION_MIN = 60 * 24 * 7  # simulate one full week


class ERSystem:
    """Wraps the SimPy resources so staffing configs can be swapped
    without rewriting the patient flow logic."""

    def __init__(self, env, staffing=STAFFING):
        self.env = env
        self.triage_nurse = simpy.Resource(env, capacity=staffing["triage_nurses"])
        self.treatment_bay = simpy.PriorityResource(env, capacity=staffing["treatment_bays"])
        self.physician = simpy.Resource(env, capacity=staffing["physicians"])


def patient(env, patient_id, acuity, er: ERSystem, rng, results: list):
    """One patient's journey through the ER, recording timestamps at
    each stage to compute wait times and total time-in-system."""

    arrival_time = env.now
    record = {"patient_id": patient_id, "acuity": acuity, "arrival_time": arrival_time}

    # ---- Triage ----
    with er.triage_nurse.request() as req:
        yield req
        record["triage_start"] = env.now
        triage_duration = max(1, rng.lognormal(mean=1.6, sigma=0.4))  # ~5 min median
        yield env.timeout(triage_duration)
        record["triage_end"] = env.now

    # ---- Treatment bay (priority by acuity: lower number = seen first) ----
    with er.treatment_bay.request(priority=acuity) as req:
        yield req
        record["bay_start"] = env.now
        record["wait_time_min"] = record["bay_start"] - record["triage_end"]

        # ---- Physician ----
        with er.physician.request() as phys_req:
            yield phys_req
            record["physician_start"] = env.now

            treat_params = SERVICE_TIMES[str(acuity)]["treatment_time_lognormal"]
            treatment_min = max(5, rng.lognormal(
                mean=treat_params["mu"], sigma=treat_params["sigma"]
            ))
            yield env.timeout(treatment_min)
            record["treatment_time_min"] = treatment_min

    record["departure_time"] = env.now
    record["total_time_min"] = record["departure_time"] - arrival_time
    results.append(record)


def arrival_process(env, er: ERSystem, rng, results: list):
    """Generates patients over time, using the hourly-weighted arrival
    rate and NHAMCS acuity mix. Interarrival times are exponential
    (standard Poisson arrival assumption), scaled by the current hour's
    fraction of daily volume."""

    patient_id = 0
    avg_per_day = ARRIVAL_RATE["avg_arrivals_per_day"]
    hourly_fraction = ARRIVAL_RATE["hourly_fraction"]

    while True:
        current_hour = int((env.now // 60) % 24)
        hour_frac = hourly_fraction[str(current_hour)]

        # Expected arrivals in this hour, converted to a per-minute rate
        expected_per_hour = avg_per_day * hour_frac
        rate_per_min = max(expected_per_hour / 60, 0.001)  # avoid div-by-zero

        interarrival = rng.exponential(1 / rate_per_min)
        yield env.timeout(interarrival)

        patient_id += 1
        acuity = rng.choice(ACUITY_LEVELS, p=np.array(ACUITY_WEIGHTS) / sum(ACUITY_WEIGHTS))
        env.process(patient(env, patient_id, int(acuity), er, rng, results))


def run_simulation(staffing=STAFFING, sim_duration=SIM_DURATION_MIN, seed=RANDOM_SEED):
    rng = np.random.default_rng(seed)
    env = simpy.Environment()
    er = ERSystem(env, staffing=staffing)
    results = []

    env.process(arrival_process(env, er, rng, results))
    env.run(until=sim_duration)

    return pd.DataFrame(results)


if __name__ == "__main__":
    df = run_simulation()

    print(f"Simulated {SIM_DURATION_MIN / (60*24):.0f} days, {len(df)} patients processed")
    print(f"\n=== Summary statistics ===")
    print(f"Average wait time (triage -> bay): {df['wait_time_min'].mean():.1f} min")
    print(f"90th percentile wait time: {df['wait_time_min'].quantile(0.9):.1f} min")
    print(f"Average total time in system: {df['total_time_min'].mean():.1f} min")

    print(f"\n=== Wait time by acuity level ===")
    print(df.groupby("acuity")["wait_time_min"].agg(["mean", "median",
          lambda x: x.quantile(0.9), "count"]).rename(
          columns={"<lambda_0>": "p90"}))

    df.to_csv("data/simulation_results_baseline.csv", index=False)
    print("\nSaved to data/simulation_results_baseline.csv")