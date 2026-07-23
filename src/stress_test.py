"""
Surge test for REQ-4 -- reruns the baseline staffing configuration at
+20% demand and checks whether REQ-1 through REQ-3 still hold. This is
the robustness check: does the system have any slack, or is it already
maxed out?
"""

import simpy
import numpy as np
import json
import pandas as pd

RANDOM_SEED = 12345

with open("data/arrival_mix.json") as f:
    ARRIVAL_MIX = json.load(f)
with open("data/arrival_rate.json") as f:
    ARRIVAL_RATE = json.load(f)
with open("data/service_time_distributions.json") as f:
    SERVICE_TIMES = json.load(f)

ACUITY_LEVELS = [int(k) for k in ARRIVAL_MIX.keys()]
ACUITY_WEIGHTS = [ARRIVAL_MIX[str(a)] for a in ACUITY_LEVELS]

STAFFING = {"triage_nurses": 2, "treatment_bays": 16, "physicians": 4}
PHYSICIAN_CONTACT_FRACTION = 0.2
SIM_DURATION_MIN = 60 * 24 * 7
WARMUP_MIN = 60 * 24

SURGE_MULTIPLIER = 1.2  # REQ-4: +20% demand
REQ2_TARGETS_MIN = {1: 20, 2: 40, 3: 75, 4: 150}
REQ3_CEILING_MIN = 240


class ERSystem:
    def __init__(self, env, staffing=STAFFING):
        self.env = env
        self.triage_nurse = simpy.Resource(env, capacity=staffing["triage_nurses"])
        self.treatment_bay = simpy.PriorityResource(env, capacity=staffing["treatment_bays"])
        self.physician = simpy.Resource(env, capacity=staffing["physicians"])


def patient(env, patient_id, acuity, er: ERSystem, rng, results: list):
    arrival_time = env.now
    record = {"patient_id": patient_id, "acuity": acuity, "arrival_time": arrival_time}

    with er.triage_nurse.request() as req:
        yield req
        record["triage_start"] = env.now
        triage_duration = max(1, rng.lognormal(mean=1.6, sigma=0.4))
        yield env.timeout(triage_duration)
        record["triage_end"] = env.now

    with er.treatment_bay.request(priority=acuity) as req:
        yield req
        record["bay_start"] = env.now
        record["wait_time_min"] = record["bay_start"] - record["triage_end"]

        treat_params = SERVICE_TIMES[str(acuity)]["treatment_time_lognormal"]
        treatment_min = max(5, rng.lognormal(mean=treat_params["mu"], sigma=treat_params["sigma"]))
        record["treatment_time_min"] = treatment_min
        physician_contact_min = max(2, treatment_min * PHYSICIAN_CONTACT_FRACTION)

        with er.physician.request() as phys_req:
            yield phys_req
            record["physician_start"] = env.now
            yield env.timeout(physician_contact_min)

        remaining_bay_min = treatment_min - physician_contact_min
        if remaining_bay_min > 0:
            yield env.timeout(remaining_bay_min)

    record["departure_time"] = env.now
    record["total_time_min"] = record["departure_time"] - arrival_time
    results.append(record)


def arrival_process(env, er: ERSystem, rng, results: list, surge_multiplier=1.0):
    patient_id = 0
    avg_per_day = ARRIVAL_RATE["avg_arrivals_per_day"] * surge_multiplier
    hourly_fraction = ARRIVAL_RATE["hourly_fraction"]

    while True:
        current_hour = int((env.now // 60) % 24)
        hour_frac = hourly_fraction[str(current_hour)]
        expected_per_hour = avg_per_day * hour_frac
        rate_per_min = max(expected_per_hour / 60, 0.001)
        interarrival = rng.exponential(1 / rate_per_min)
        yield env.timeout(interarrival)

        patient_id += 1
        acuity = rng.choice(ACUITY_LEVELS, p=np.array(ACUITY_WEIGHTS) / sum(ACUITY_WEIGHTS))
        env.process(patient(env, patient_id, int(acuity), er, rng, results))


def run_simulation(staffing=STAFFING, surge_multiplier=1.0, sim_duration=SIM_DURATION_MIN, seed=RANDOM_SEED):
    rng = np.random.default_rng(seed)
    env = simpy.Environment()
    er = ERSystem(env, staffing=staffing)
    results = []
    env.process(arrival_process(env, er, rng, results, surge_multiplier=surge_multiplier))
    env.run(until=sim_duration)
    return pd.DataFrame(results)


def check_requirements(df, label=""):
    steady = df[df["arrival_time"] >= WARMUP_MIN].copy()

    print(f"\n=== {label} ===")
    print(f"Patients completed (steady-state): {len(steady)}")

    triage_wait = steady["triage_start"] - steady["arrival_time"]
    pct_req1 = (triage_wait <= 10).mean() * 100
    print(f"REQ-1 (90% triaged <=10 min): {pct_req1:.1f}%  "
          f"({'PASS' if pct_req1 >= 90 else 'FAIL'})")

    for acuity, target in REQ2_TARGETS_MIN.items():
        subset = steady[steady["acuity"] == acuity]["wait_time_min"]
        if len(subset) == 0:
            print(f"REQ-2 Acuity {acuity}: no completed patients (censored)")
            continue
        pct = (subset <= target).mean() * 100
        print(f"REQ-2 Acuity {acuity} (<={target} min, 90% target): {pct:.1f}%  "
              f"({'PASS' if pct >= 90 else 'FAIL'})")

    over = (steady["wait_time_min"] > REQ3_CEILING_MIN).sum()
    pct_over = over / len(steady) * 100 if len(steady) else 0
    print(f"REQ-3 (no wait >240 min): {over} exceeded ({pct_over:.1f}%)  "
          f"({'PASS' if over == 0 else 'FAIL'})")


if __name__ == "__main__":
    baseline_df = run_simulation(surge_multiplier=1.0)
    check_requirements(baseline_df, label="Baseline (normal demand)")

    surge_df = run_simulation(surge_multiplier=SURGE_MULTIPLIER)
    check_requirements(surge_df, label=f"REQ-4 Surge Test (+{int((SURGE_MULTIPLIER-1)*100)}% demand)")

    surge_df.to_csv("data/simulation_results_surge.csv", index=False)
    print("\nSaved surge results to data/simulation_results_surge.csv")
